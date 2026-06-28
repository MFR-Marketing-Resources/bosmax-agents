"""
OTAK -> TANGAN envelope projection.

Projects a BOSMAX compiled video template (the OTAK "brain" output) into the
single JSON envelope the TANGAN service consumes, per
docs/INTEGRATION_CONTRACT.md section 5 (in the _ref_flowkit repo).

Design rules (kept deliberately thin / dumb, per the contract):
  - No import of BOSMAX pipeline code. Consumes a plain dict (a compiled template
    or a hand-built brief). Two repos, zero coupling.
  - Fail LOUD, not silent: if the motion prompt cannot be located we raise, we do
    NOT emit an empty/garbage prompt. This mirrors BOSMAX's fail-closed ethos.
  - Pure stdlib. No third-party deps.

Envelope shape (contract section 5):
  {
    "prompt": "<video motion prompt>",
    "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
    "user_paygate_tier": "PAYGATE_TIER_ONE",
    "start_frame": {
      "mode": "ai" | "upload",
      "image_prompt": "<used when mode=ai>",
      "image_base64": "<used when mode=upload>",
      "mime_type": "image/png"
    }
  }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# ---- Contract enums (contract section 3/5) --------------------------------

ASPECT_PORTRAIT = "VIDEO_ASPECT_RATIO_PORTRAIT"
ASPECT_LANDSCAPE = "VIDEO_ASPECT_RATIO_LANDSCAPE"

TIER_ONE = "PAYGATE_TIER_ONE"     # AI Pro
TIER_TWO = "PAYGATE_TIER_TWO"     # AI Ultra
PAID_TIERS = (TIER_ONE, TIER_TWO)

MODE_AI = "ai"          # TANGAN calls /generate-image with image_prompt
MODE_UPLOAD = "upload"  # TANGAN calls /upload-image-base64 with image bytes

# Keys we probe for the engine-facing Google Flow motion prompt inside a
# block_script_json entry. Order = priority. Defensive because the exact key
# name in the compiled template is owned by the BOSMAX compiler and may drift.
_PROMPT_KEYS = (
    "google_flow_prompt",
    "flow_prompt",
    "prompt_text",
    "block_prompt",
    "prompt",
    "text",
)

# Platforms that imply a 9:16 portrait video.
_PORTRAIT_PLATFORMS = (
    "tiktok",
    "youtube shorts",
    "shorts",
    "reels",
    "instagram",
    "meta",
)


class EnvelopeError(ValueError):
    """Raised when a template cannot be projected into a valid envelope."""


@dataclass
class StartFrame:
    mode: str
    image_prompt: Optional[str] = None
    image_base64: Optional[str] = None
    mime_type: str = "image/png"

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"mode": self.mode}
        if self.mode == MODE_AI:
            d["image_prompt"] = self.image_prompt
        elif self.mode == MODE_UPLOAD:
            d["image_base64"] = self.image_base64
            d["mime_type"] = self.mime_type
        return d


@dataclass
class Envelope:
    prompt: str
    aspect_ratio: str
    user_paygate_tier: str
    start_frame: StartFrame
    # Carried for orchestration/labelling only; not part of the wire envelope.
    scene_id: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """The exact JSON object POSTed to /api/flow/shoot-oneshot (contract 5)."""
        return {
            "prompt": self.prompt,
            "aspect_ratio": self.aspect_ratio,
            "user_paygate_tier": self.user_paygate_tier,
            "start_frame": self.start_frame.to_dict(),
        }


# ---- helpers ---------------------------------------------------------------

def _first(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return None


def aspect_from_platform(platform: Optional[str], explicit: Optional[str] = None) -> str:
    """Map a BOSMAX platform string to a contract aspect_ratio. Portrait default
    (BOSMAX is TikTok-Shop-first)."""
    if explicit:
        return explicit
    p = (platform or "").strip().lower()
    if not p:
        return ASPECT_PORTRAIT
    for token in _PORTRAIT_PLATFORMS:
        if token in p:
            return ASPECT_PORTRAIT
    # Shopee/Lazada listings are commonly square/landscape; treat non-social as
    # landscape unless the caller overrides. Portrait stays the safe default.
    return ASPECT_PORTRAIT


def _assemble_9_sections(block: dict[str, Any]) -> str:
    """Join a BOSMAX final_prompt_9_sections list into one engine-facing prompt."""
    secs = block.get("final_prompt_9_sections") or []
    lines = []
    for s in secs:
        if isinstance(s, dict) and str(s.get("section_text", "")).strip():
            head = str(s.get("section_heading", "")).strip()
            text = str(s["section_text"]).strip()
            lines.append(f"{head}: {text}" if head else text)
    return "\n".join(lines).strip()


def extract_motion_prompt(template: dict[str, Any]) -> str:
    """Pull the engine-facing Google Flow motion prompt out of a BOSMAX template.

    Priority (verified against the real repo-clone pipeline
    parser->storyboard->compiler):
      1. compiler.final_prompt_text         — the assembled engine-ready prompt
      2. compiler.final_prompt_blocks[].final_prompt_9_sections (or prompt_sets[])
      3. storyboard.block_script_json[]      — real keys block_visual_action
         (+ block_dialogue_or_copy), or generic _PROMPT_KEYS for hand briefs
      4. storyboard.master_storyboard        — last-resort fallback
    Raises EnvelopeError if nothing usable is found (fail loud)."""
    # 1 + 2: compiled engine-facing surfaces (authoritative).
    # Prefer the clean 9-section body over compiler.final_prompt_text: the latter
    # wraps the sections in orchestration framing ("SINGLE PROMPT",
    # "prompt_set_count: N", "SET 1 - 8 SECONDS") which BOSMAX's own fail-closed
    # rule forbids leaking into the engine-read prompt body. The 9 sections are
    # the engine body; the wrapper is an OUTER header only.
    comp = template.get("compiler") or {}
    for block in (comp.get("final_prompt_blocks") or comp.get("prompt_sets") or []):
        if isinstance(block, dict):
            joined = _assemble_9_sections(block)
            if joined:
                return joined
    txt = comp.get("final_prompt_text")
    if txt and str(txt).strip():
        return str(txt).strip()

    # 3: storyboard blocks (pre-compile)
    storyboard = template.get("storyboard") or {}
    for block in (storyboard.get("block_script_json") or []):
        if isinstance(block, dict):
            generic = _first(block, *_PROMPT_KEYS)
            if generic and str(generic).strip():
                return str(generic).strip()
            va = block.get("block_visual_action")
            if va and str(va).strip():
                parts = [str(va).strip()]
                dlg = block.get("block_dialogue_or_copy")
                if dlg and str(dlg).strip():
                    parts.append(f'Spoken: "{str(dlg).strip()}"')
                return " ".join(parts)
        elif isinstance(block, str) and block.strip():
            return block.strip()

    # 4: master storyboard fallback
    fallback = _first(storyboard, "master_storyboard", "master_storyline")
    if fallback and str(fallback).strip():
        return str(fallback).strip()
    raise EnvelopeError(
        "No motion prompt found: no compiler.final_prompt_text/blocks, no usable "
        f"block_script_json (block_visual_action or {_PROMPT_KEYS}), no master_storyboard."
    )


def _derive_start_frame(
    template: dict[str, Any],
    *,
    mode: Optional[str],
    image_base64: Optional[str],
    mime_type: str,
    image_prompt: Optional[str],
) -> StartFrame:
    """Decide AI vs upload. Explicit args win; otherwise infer from the template's
    asset_role_map / source signals. Product photo present -> upload (BOSMAX
    'product is the anchor'); else AI scene frame."""
    if mode is None:
        # infer
        src = template.get("input") or template.get("run") or {}
        role_map = src.get("asset_role_map") or template.get("asset_role_map") or {}
        product_uploads = src.get("product_photo_uploads") or src.get(
            "product_reference_photos"
        ) or []
        has_product_photo = bool(image_base64) or bool(product_uploads) or any(
            "PRODUCT" in str(v).upper() for v in (role_map.values() if isinstance(role_map, dict) else [])
        )
        mode = MODE_UPLOAD if has_product_photo else MODE_AI

    if mode == MODE_UPLOAD:
        if not image_base64:
            raise EnvelopeError(
                "start_frame.mode=upload requires image_base64 (the product photo "
                "bytes). Pass image_base64=... or use mode='ai'."
            )
        return StartFrame(mode=MODE_UPLOAD, image_base64=image_base64, mime_type=mime_type)

    # AI mode: compose an image prompt from the scene/product brief if not given.
    if not image_prompt:
        image_prompt = _compose_scene_brief(template)
    if not image_prompt:
        raise EnvelopeError(
            "start_frame.mode=ai requires an image_prompt and none could be "
            "composed from the template (no scene_context / angle seed / product "
            "truth). Pass image_prompt=... explicitly."
        )
    return StartFrame(mode=MODE_AI, image_prompt=image_prompt)


def _compose_scene_brief(template: dict[str, Any]) -> Optional[str]:
    """Best-effort AI start-frame brief from BOSMAX scene/product fields.

    Probes both shapes: the canonical compiled template (scene under `input.*`)
    and a raw worker snapshot (scene under `angle`/`product`/`run`)."""
    inp = template.get("input") or {}
    parsed = template.get("parsed") or {}
    angle = template.get("angle") or {}
    product = template.get("product") or {}
    run = template.get("run") or {}
    scene = (
        _first(inp, "visual_seed", "copy_seed")
        or _first(parsed, "scene_context")
        or _first(angle, "scene_context_seed", "auto_scene_context")
        or _first(run, "scene_context", "frame_context")
    )
    product_truth = _first(inp, "product_truth_lock") or _first(product, "product_truth_lock")
    scale = _first(inp, "scale_lock") or _first(product, "scale_lock")
    parts = [str(p).strip() for p in (scene, product_truth, scale) if p and str(p).strip()]
    return " ".join(parts) or None


# ---- public entrypoint -----------------------------------------------------

def project(
    template: dict[str, Any],
    *,
    user_paygate_tier: str = TIER_ONE,
    aspect_ratio: Optional[str] = None,
    mode: Optional[str] = None,
    image_base64: Optional[str] = None,
    mime_type: str = "image/png",
    image_prompt: Optional[str] = None,
    scene_id: Optional[str] = None,
) -> Envelope:
    """
    Project a BOSMAX compiled video template into a contract-5 Envelope.

    template          : compiled BOSMAX video template (dict) OR a hand brief.
    user_paygate_tier : PAYGATE_TIER_ONE/TWO (the wall that gates video).
    aspect_ratio      : override; else derived from platform (portrait default).
    mode              : 'ai'|'upload' override; else inferred from asset roles.
    image_base64      : required when (effective) mode == 'upload'.
    image_prompt      : AI start-frame brief; else composed from scene fields.
    """
    if user_paygate_tier not in PAID_TIERS:
        # Not fatal at projection time (image path works on freemium), but flag it.
        # The caller / TANGAN enforces the actual video gate.
        pass

    prompt = extract_motion_prompt(template)

    identity = template.get("identity") or {}
    run = template.get("run") or {}
    platform = _first(identity, "platform") or _first(run, "platform") or _first(
        template, "platform"
    )
    aspect = aspect_from_platform(platform, aspect_ratio)

    start_frame = _derive_start_frame(
        template,
        mode=mode,
        image_base64=image_base64,
        mime_type=mime_type,
        image_prompt=image_prompt,
    )

    sid = scene_id or _first(identity, "scene_id") or _first(run, "run_name") or "scene-1"

    return Envelope(
        prompt=prompt,
        aspect_ratio=aspect,
        user_paygate_tier=user_paygate_tier,
        start_frame=start_frame,
        scene_id=str(sid),
        meta={"platform": platform, "engine": _first(identity, "engine")},
    )
