"""
BOSMAX Batch Video Prompt Exporter v1.

Resolves a batch input YAML into CSV / Markdown / JSONL prompt rows using
existing resolver_runtime contracts.  Does not modify any resolver internals.

Supported workflows:
  BOSMAX_SERUM_STEALTH       — registered STEALTH product, BOSMAX Serum
  MWCB_DIRECT                — registered DIRECT product, Minyak Warisan Cap Burung
  ON_THE_FLY_SESSION_ONLY    — session-only; registry_writeback FORBIDDEN

Copywriting selection modes:
  AUTO_RESOLVE (+ copywriting_id)          → COPY_FIXED behaviour
  AUTO_RESOLVE (+ copywriting_id_range)    → COPY_ROTATE behaviour
  AUTO_RESOLVE (+ copywriting_id_list)     → COPY_ROTATE behaviour
  SESSION_ONLY_GENERATE                    → no copywriting ID; ON_THE_FLY only

Avatar rotation:
  Uses resolver_runtime.resolve_avatar_pool() — no pool logic re-implemented here.
"""
from __future__ import annotations

import csv
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "batch_prompts"

# ---------------------------------------------------------------------------
# Workflow registry — maps workflow name to product / silo metadata.
# Do NOT add new registry structures here; mirror what's in the YAML registries.
# ---------------------------------------------------------------------------

WORKFLOW_REGISTRY: dict[str, dict[str, Any]] = {
    "BOSMAX_SERUM_STEALTH": {
        "product_id": "BOSMAX_SERUM",
        "product_name": "BOSMAX Serum",
        "silo": "STEALTH",
        "product_family": "FAMILY_MALE_EXT_SENSITIVE_OIL",
        "allowed_pool_ids": {"BOSMAX_MALE_STEALTH_POOL_001"},
        "route_status": "REGISTERED_PRODUCT",
    },
    "MWCB_DIRECT": {
        "product_id": "CAP_BURUNG_MINYAK",
        "product_name": "Minyak Warisan Cap Burung",
        "silo": "DIRECT",
        "product_family": "FAMILY_TRADITIONAL_REMEDY_OIL",
        "allowed_pool_ids": {"MWCB_TRAD_REMEDY_POOL_001"},
        "route_status": "REGISTERED_PRODUCT",
    },
    "ON_THE_FLY_SESSION_ONLY": {
        "product_id": None,
        "product_name": None,
        "silo": None,
        "product_family": None,
        "allowed_pool_ids": set(),
        "route_status": "ON_THE_FLY",
    },
}

OUTPUT_COLUMNS: list[str] = [
    "prompt_id",
    "row_index",
    "product_workflow",
    "product_id",
    "product_name",
    "copywriting_id",
    "avatar_context_id",
    "avatar_pool_id",
    "engine",
    "duration",
    "platform",
    "language",
    "route_status",
    "final_prompt_text",
]

PARENT_OUTPUT_COLUMNS: list[str] = [
    # Verified compiler-owned parent spine (no parent_row_id — template_id is the key).
    "template_id",
    "template_name",
    "product_lane",
    "engine",
    "mode",
    "duration",
    "block_mode",
    "block_count",
    "block_plan",
    "prompt_execution_mode",
    "raw_prompt_seed",
    "master_storyline",
    "master_storyboard",
    "final_prompt_text",
    "qa_status",
    "production_ready",
    "export_ready",
    "notion_ready",
    # Copywriting landbank traceability metadata (parent registry only).
    "copywriting_landbank_row_id",
    "commercial_angle_id",
    "commercial_angle_name",
    "hook",
    "body_copy",
    "cta",
    "risk_class",
    "claim_class",
    "platform",
    "pilot_batch",
]

CHILD_OUTPUT_COLUMNS: list[str] = [
    "child_row_id",
    "parent_template_id",
    "block_id",
    "block_duration",
    "narrative_function",
    "visual_action",
    "dialogue_or_copy",
    "wps_budget",
    "start_state",
    "end_state",
    "continuity_anchor",
    "final_prompt_block_text",
    "qa_status",
]

_REVIEW_ONLY_COMPLIANCE_CLASSES = frozenset({"HIGH", "REVIEW_ONLY", "RED"})
_REVIEW_ONLY_KEYWORDS = frozenset({
    "baby", "bayi", "maternity", "pregnancy", "pregnant", "hamil",
    "supplement", "supplemen", "vitamin", "medical", "medicine",
    "ubat", "penawar", "cure", "sembuh", "merawat", "disease",
    "diagnosis", "clinic", "clinical", "prescription",
    "sexual wellness", "intimate", "erectile", "libido",
    "fertility", "adult", "restricted",
})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ExporterError(RuntimeError):
    """Raised for any validation or resolution failure inside the exporter."""


# ---------------------------------------------------------------------------
# Copywriting sequence builders
# ---------------------------------------------------------------------------

def _parse_copywriting_id_range(range_str: str) -> list[str]:
    """Expand 'PREFIX_CP_0001..PREFIX_CP_0003' to a list of IDs."""
    if ".." not in range_str:
        raise ExporterError(
            f"Invalid copywriting_id_range: {range_str!r}. "
            "Expected 'START_CP_ID..END_CP_ID'."
        )
    start_id, end_id = range_str.split("..", 1)
    start_id, end_id = start_id.strip(), end_id.strip()
    m_start = re.match(r"^(.+_CP_)(\d+)$", start_id)
    m_end = re.match(r"^(.+_CP_)(\d+)$", end_id)
    if not m_start or not m_end:
        raise ExporterError(
            f"copywriting_id_range IDs must match PREFIX_CP_NNNN. "
            f"Got: {start_id!r}, {end_id!r}."
        )
    if m_start.group(1) != m_end.group(1):
        raise ExporterError(
            f"copywriting_id_range prefix mismatch: "
            f"{m_start.group(1)!r} vs {m_end.group(1)!r}."
        )
    prefix = m_start.group(1)
    start_n, end_n = int(m_start.group(2)), int(m_end.group(2))
    if start_n > end_n:
        raise ExporterError(
            f"copywriting_id_range start {start_n} > end {end_n}."
        )
    width = len(m_start.group(2))
    return [f"{prefix}{str(n).zfill(width)}" for n in range(start_n, end_n + 1)]


def _build_copywriting_sequence(batch_input: dict[str, Any], batch_count: int) -> list[str]:
    """Return a list of copywriting_id strings, one per row."""
    mode = str(batch_input.get("copywriting_mode") or "").upper().strip()

    if mode == "SESSION_ONLY_GENERATE":
        return ["none"] * batch_count

    if mode not in ("AUTO_RESOLVE", "COPY_FIXED", "COPY_ROTATE"):
        raise ExporterError(
            f"Unknown copywriting_mode: {mode!r}. "
            "Expected AUTO_RESOLVE, COPY_FIXED, COPY_ROTATE, or SESSION_ONLY_GENERATE."
        )

    range_str = str(batch_input.get("copywriting_id_range") or "").strip()
    id_list_raw = batch_input.get("copywriting_id_list")
    single_id = str(batch_input.get("copywriting_id") or "").strip()

    # COPY_ROTATE via range
    if range_str:
        ids = _parse_copywriting_id_range(range_str)
        if not ids:
            raise ExporterError("copywriting_id_range produced an empty ID list.")
        return [ids[i % len(ids)] for i in range(batch_count)]

    # COPY_ROTATE via explicit list
    if id_list_raw and mode in ("AUTO_RESOLVE", "COPY_ROTATE"):
        ids = [str(item).strip() for item in id_list_raw if str(item or "").strip()]
        if not ids:
            raise ExporterError("copywriting_id_list is empty.")
        return [ids[i % len(ids)] for i in range(batch_count)]

    # COPY_FIXED / AUTO_RESOLVE with a single ID
    if single_id and single_id.lower() != "none":
        return [single_id] * batch_count

    raise ExporterError(
        "copywriting_mode AUTO_RESOLVE/COPY_FIXED requires a non-empty copywriting_id. "
        "For rotation, supply copywriting_id_range or copywriting_id_list."
    )


# ---------------------------------------------------------------------------
# Cross-validation guards — fail closed before touching the resolver
# ---------------------------------------------------------------------------

def _guard_pool_silo_compatibility(
    workflow_meta: dict[str, Any], avatar_pool_id: str
) -> None:
    """Fail if the requested pool is not in this workflow's allowed set."""
    from resolver_runtime import normalize_key  # noqa: PLC0415

    pool_key = normalize_key(avatar_pool_id)
    allowed_keys = {normalize_key(p) for p in workflow_meta.get("allowed_pool_ids", set())}
    if allowed_keys and pool_key not in allowed_keys:
        raise ExporterError(
            f"Avatar pool '{avatar_pool_id}' is not allowed for workflow silo "
            f"'{workflow_meta.get('silo', '?')}'. "
            f"Allowed pools: {sorted(workflow_meta.get('allowed_pool_ids', set()))}."
        )


def _guard_on_the_fly_writeback(batch_input: dict[str, Any]) -> None:
    """Fail if ON_THE_FLY batch tries to enable registry writeback."""
    writeback = str(batch_input.get("registry_writeback") or "").upper().strip()
    if writeback and writeback != "FORBIDDEN":
        raise ExporterError(
            f"ON_THE_FLY_SESSION_ONLY registry_writeback must be FORBIDDEN, "
            f"got: {writeback!r}."
        )


def _classify_on_the_fly_intake(
    product_intake: dict[str, Any],
) -> tuple[bool, str]:
    """Return (is_blocked, reason).  Blocked rows become BLOCKED_REVIEW_ONLY."""
    compliance = str(product_intake.get("compliance_class") or "").upper().strip()
    if compliance in _REVIEW_ONLY_COMPLIANCE_CLASSES:
        return True, f"compliance_class={compliance}"
    combined = (
        str(product_intake.get("product_name") or "").lower()
        + " "
        + str(product_intake.get("category") or "").lower()
    )
    matched = [kw for kw in _REVIEW_ONLY_KEYWORDS if kw in combined]
    if matched:
        return True, f"review_only_keywords={matched}"
    return False, ""


# ---------------------------------------------------------------------------
# Prompt text builders — produce the final_prompt_text cell value
# ---------------------------------------------------------------------------

def _build_registered_prompt_text(
    batch_input: dict[str, Any],
    workflow_meta: dict[str, Any],
    copy_pack: dict[str, Any],
    avatar_pack: dict[str, Any],
) -> str:
    lines = [
        "[BATCH_PROMPT_ROW]",
        f"workflow: {batch_input.get('product_workflow', '')}",
        f"product_id: {workflow_meta['product_id']}",
        f"product_name: {workflow_meta['product_name']}",
        f"platform: {batch_input.get('platform', '')}",
        f"engine: {batch_input.get('engine', '')}",
        f"duration: {batch_input.get('duration', '')}",
        f"language: {batch_input.get('language', '')}",
        f"copywriting_id: {copy_pack.get('copywriting_id', '')}",
        f"copy_formula: {copy_pack.get('submode_formula', '')}",
        f"copy_hook: {copy_pack.get('hook', '')}",
        f"copy_cta: {copy_pack.get('cta', '')}",
        f"compliance: {copy_pack.get('compliance', '')}",
        f"avatar_context_id: {avatar_pack.get('avatar_context_id', '')}",
        f"avatar_display_name: {avatar_pack.get('display_name', '')}",
        f"avatar_persona: {avatar_pack.get('persona_label', '')}",
        f"avatar_scene: {avatar_pack.get('scene_label', '')}",
        f"avatar_mannequin: {avatar_pack.get('mannequin_label', '')}",
        f"avatar_wardrobe: {avatar_pack.get('wardrobe_id', '')}",
        "[/BATCH_PROMPT_ROW]",
    ]
    return "\n".join(lines)


def _build_on_the_fly_prompt_text(
    batch_input: dict[str, Any],
    product_intake: dict[str, Any],
    blocked: bool,
    block_reason: str = "",
) -> str:
    if blocked:
        return f"BLOCKED_REVIEW_ONLY: {block_reason}"
    lines = [
        "[BATCH_PROMPT_ROW]",
        "workflow: ON_THE_FLY_SESSION_ONLY",
        f"product_name: {product_intake.get('product_name', '')}",
        f"platform: {batch_input.get('platform', '')}",
        f"engine: {batch_input.get('engine', '')}",
        f"duration: {batch_input.get('duration', '')}",
        f"language: {batch_input.get('language', '')}",
        "copywriting_id: none",
        "copywriting_mode: SESSION_ONLY_GENERATE",
        "registry_writeback: FORBIDDEN",
        f"category: {product_intake.get('category', '')}",
        f"target_user: {product_intake.get('target_user', '')}",
        f"main_problem_solved: {product_intake.get('main_problem_solved', '')}",
        f"main_benefit: {product_intake.get('main_benefit', '')}",
        f"compliance_class: {product_intake.get('compliance_class', '')}",
        "session_scope: AD_HOC_GENERATED_THIS_SESSION_ONLY",
        "[/BATCH_PROMPT_ROW]",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core batch runners
# ---------------------------------------------------------------------------

def _run_registered_batch(
    batch_input: dict[str, Any],
    workflow_meta: dict[str, Any],
    batch_count: int,
) -> list[dict[str, Any]]:
    from resolver_runtime import ResolverError, resolve_avatar_pool, resolve_copywriting_id  # noqa: PLC0415

    avatar_pool_id = str(batch_input.get("avatar_pool_id") or "").strip()
    if not avatar_pool_id:
        raise ExporterError("avatar_pool_id is required for registered product batch.")
    _guard_pool_silo_compatibility(workflow_meta, avatar_pool_id)

    rotation_rule = str(
        batch_input.get("rotation_rule") or "ROUND_ROBIN_NO_REPEAT"
    ).strip()
    copy_sequence = _build_copywriting_sequence(batch_input, batch_count)

    # Resolve each unique copywriting ID once, cache results.
    resolved_copy_packs: dict[str, dict[str, Any]] = {}
    for cid in dict.fromkeys(copy_sequence):
        try:
            resolved_copy_packs[cid] = resolve_copywriting_id(
                cid,
                expected_template_lane=workflow_meta["silo"],
            )
        except ResolverError as exc:
            raise ExporterError(
                f"Copywriting ID resolution failed for '{cid}': {exc}"
            ) from exc

    # Resolve avatar pool rotation.
    try:
        pool_result = resolve_avatar_pool(
            avatar_pool_id,
            batch_count=batch_count,
            rotation_rule=rotation_rule,
            expected_template_silo=workflow_meta["silo"],
            expected_product_family=workflow_meta.get("product_family"),
        )
    except ResolverError as exc:
        raise ExporterError(
            f"Avatar pool resolution failed for '{avatar_pool_id}': {exc}"
        ) from exc

    rows: list[dict[str, Any]] = []
    for i, (cid, avatar_ctx_id) in enumerate(
        zip(copy_sequence, pool_result["sequence_ids"])
    ):
        copy_pack = resolved_copy_packs[cid]
        avatar_pack = pool_result["sequence"][i]
        rows.append({
            "prompt_id": f"{workflow_meta['product_id']}_BATCH_{i + 1:04d}",
            "row_index": i + 1,
            "product_workflow": str(batch_input.get("product_workflow", "")),
            "product_id": workflow_meta["product_id"],
            "product_name": workflow_meta["product_name"],
            "copywriting_id": cid,
            "avatar_context_id": avatar_ctx_id,
            "avatar_pool_id": avatar_pool_id,
            "engine": str(batch_input.get("engine", "")),
            "duration": str(batch_input.get("duration", "")),
            "platform": str(batch_input.get("platform", "")),
            "language": str(batch_input.get("language", "")),
            "route_status": "REGISTERED_PRODUCT",
            "final_prompt_text": _build_registered_prompt_text(
                batch_input, workflow_meta, copy_pack, avatar_pack
            ),
        })

    return rows


def _run_on_the_fly_batch(
    batch_input: dict[str, Any],
    workflow_meta: dict[str, Any],
    batch_count: int,
) -> list[dict[str, Any]]:
    _guard_on_the_fly_writeback(batch_input)

    product_intake_raw = batch_input.get("product_intake") or {}
    if isinstance(product_intake_raw, list):
        intake_list: list[dict[str, Any]] = list(product_intake_raw[:batch_count])
        if len(intake_list) < batch_count:
            intake_list += [{}] * (batch_count - len(intake_list))
    else:
        intake_list = [dict(product_intake_raw)] * batch_count

    rows: list[dict[str, Any]] = []
    for i, intake in enumerate(intake_list):
        intake_dict = dict(intake) if intake else {}
        blocked, block_reason = _classify_on_the_fly_intake(intake_dict)
        product_name = str(intake_dict.get("product_name") or "SESSION_PRODUCT")
        route_status = "BLOCKED_REVIEW_ONLY" if blocked else "ON_THE_FLY"
        rows.append({
            "prompt_id": f"OTF_SESSION_BATCH_{i + 1:04d}",
            "row_index": i + 1,
            "product_workflow": "ON_THE_FLY_SESSION_ONLY",
            "product_id": "none",
            "product_name": product_name,
            "copywriting_id": "none",
            "avatar_context_id": "none",
            "avatar_pool_id": "none",
            "engine": str(batch_input.get("engine", "")),
            "duration": str(batch_input.get("duration", "")),
            "platform": str(batch_input.get("platform", "")),
            "language": str(batch_input.get("language", "")),
            "route_status": route_status,
            "final_prompt_text": _build_on_the_fly_prompt_text(
                batch_input, intake_dict, blocked, block_reason
            ),
        })

    return rows


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_batch(batch_input: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Resolve a batch input dict into a list of prompt row dicts.

    Each row contains the OUTPUT_COLUMNS fields.
    Raises ExporterError on any validation or resolution failure.
    """
    workflow_name = str(batch_input.get("product_workflow") or "").upper().strip()
    if workflow_name not in WORKFLOW_REGISTRY:
        raise ExporterError(
            f"Unknown product_workflow: {workflow_name!r}. "
            f"Known workflows: {sorted(WORKFLOW_REGISTRY)}."
        )

    workflow_meta = WORKFLOW_REGISTRY[workflow_name]

    raw_count = batch_input.get("batch_count")
    try:
        batch_count = int(raw_count or 0)
    except (TypeError, ValueError) as exc:
        raise ExporterError(
            f"batch_count must be a positive integer, got: {raw_count!r}."
        ) from exc
    if batch_count <= 0:
        raise ExporterError(
            f"batch_count must be > 0, got: {batch_count!r}."
        )

    if workflow_name == "ON_THE_FLY_SESSION_ONLY":
        return _run_on_the_fly_batch(batch_input, workflow_meta, batch_count)
    return _run_registered_batch(batch_input, workflow_meta, batch_count)


# ---------------------------------------------------------------------------
# Export writers
# ---------------------------------------------------------------------------

def _timestamp_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")


def _safe_tag(workflow: str) -> str:
    return re.sub(r"[^A-Z0-9]", "_", workflow.upper())


def export_rows(
    rows: list[dict[str, Any]],
    workflow: str,
    output_dir: Path | None = None,
    stem_override: str | None = None,
) -> dict[str, Path]:
    """
    Write rows to CSV, Markdown, and JSONL files.
    Creates output_dir if it does not exist.
    Returns a dict mapping format name → file path.
    """
    out_dir = output_dir if output_dir is not None else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = _timestamp_utc()
    tag = _safe_tag(workflow)
    stem = stem_override or f"batch_prompts_{tag}_{ts}"
    paths: dict[str, Path] = {}

    # CSV
    csv_path = out_dir / f"{stem}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    paths["csv"] = csv_path

    # JSONL
    jsonl_path = out_dir / f"{stem}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    paths["jsonl"] = jsonl_path

    # Markdown table
    md_path = out_dir / f"{stem}.md"
    with md_path.open("w", encoding="utf-8") as fh:
        fh.write("| " + " | ".join(OUTPUT_COLUMNS) + " |\n")
        fh.write("| " + " | ".join(["---"] * len(OUTPUT_COLUMNS)) + " |\n")
        for row in rows:
            cells: list[str] = []
            for col in OUTPUT_COLUMNS:
                val = str(row.get(col) or "")
                val = val.replace("|", "\\|").replace("\n", " ")
                cells.append(val)
            fh.write("| " + " | ".join(cells) + " |\n")
    paths["md"] = md_path

    return paths


# ---------------------------------------------------------------------------
# Compiler runtime exporter — parent/child Notion-ready rows
# ---------------------------------------------------------------------------

def _json_like_load(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    return yaml.safe_load(raw) or {}


def _looks_like_compiled_template(payload: Any) -> bool:
    return isinstance(payload, dict) and "identity" in payload and "compiler" in payload


def _coerce_compiled_templates(payload: Any) -> list[dict[str, Any]]:
    if _looks_like_compiled_template(payload):
        return [payload]
    if isinstance(payload, dict) and isinstance(payload.get("compiled_templates"), list):
        items = payload["compiled_templates"]
        if all(_looks_like_compiled_template(item) for item in items):
            return list(items)
    if isinstance(payload, list) and all(_looks_like_compiled_template(item) for item in payload):
        return list(payload)
    raise ExporterError("Input is not a compiled video_template_compiler payload.")


def export_compiled_templates(
    compiled_templates: list[dict[str, Any]],
    workflow: str = "VIDEO_TEMPLATE_COMPILER",
    output_dir: Path | None = None,
    stem_override: str | None = None,
) -> dict[str, Path]:
    out_dir = output_dir if output_dir is not None else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = _timestamp_utc()
    tag = _safe_tag(workflow)
    stem = stem_override or f"video_template_compiler_{tag}_{ts}"
    paths: dict[str, Path] = {}

    parent_rows: list[dict[str, Any]] = []
    child_rows: list[dict[str, Any]] = []

    for template in compiled_templates:
        identity = template.get("identity") or {}
        duration = template.get("duration") or {}
        input_block = template.get("input") or {}
        storyboard = template.get("storyboard") or {}
        compiler = template.get("compiler") or {}
        qa = template.get("qa") or {}
        parsed = template.get("parsed") or {}
        template_id = str(template.get("template_id") or "")

        parent_rows.append({
            "template_id": template_id,
            "template_name": str(template.get("template_name") or ""),
            "product_lane": str(identity.get("product_lane") or ""),
            "engine": str(identity.get("engine") or ""),
            "mode": str(identity.get("mode") or ""),
            "duration": str(duration.get("duration_label") or duration.get("duration_seconds") or ""),
            "block_mode": str(duration.get("block_mode") or ""),
            "block_count": int(duration.get("block_count") or 0),
            "block_plan": json.dumps(duration.get("block_plan") or [], ensure_ascii=False),
            "prompt_execution_mode": str(duration.get("prompt_execution_mode") or ""),
            "raw_prompt_seed": str(input_block.get("raw_prompt_seed") or ""),
            "master_storyline": str(storyboard.get("master_storyline") or ""),
            "master_storyboard": str(storyboard.get("master_storyboard") or ""),
            "final_prompt_text": str(compiler.get("final_prompt_text") or ""),
            "qa_status": str(qa.get("qa_status") or ""),
            "production_ready": bool(qa.get("production_ready")),
            "export_ready": bool(qa.get("export_ready")),
            "notion_ready": bool(qa.get("notion_ready")),
            # Copywriting landbank traceability — sourced from the compiled
            # template sections, blank when the input seed did not supply them.
            "copywriting_landbank_row_id": str(input_block.get("source_landbank_row") or ""),
            "commercial_angle_id": str(identity.get("commercial_angle_id") or identity.get("source_angle_id") or ""),
            "commercial_angle_name": str(identity.get("commercial_angle_name") or ""),
            "hook": str(parsed.get("hook") or ""),
            "body_copy": str(parsed.get("body") or ""),
            "cta": str(parsed.get("cta") or ""),
            "risk_class": str(parsed.get("risk_class") or ""),
            "claim_class": str(parsed.get("claim_class") or ""),
            "platform": str(identity.get("platform") or ""),
            "pilot_batch": str(identity.get("pilot_batch") or ""),
        })

        block_map = {
            str(item.get("block_id")): item
            for item in (storyboard.get("block_script_json") or [])
        }
        for compiled_block in compiler.get("final_prompt_blocks") or []:
            block_id = str(compiled_block.get("block_id") or "")
            block_meta = block_map.get(block_id, {})
            child_rows.append({
                "child_row_id": block_id,
                "parent_template_id": template_id,
                "block_id": block_id,
                "block_duration": str(block_meta.get("block_duration") or ""),
                "narrative_function": str(block_meta.get("block_narrative_function") or ""),
                "visual_action": str(block_meta.get("block_visual_action") or ""),
                "dialogue_or_copy": str(block_meta.get("block_dialogue_or_copy") or ""),
                "wps_budget": json.dumps(block_meta.get("block_wps_budget") or {}, ensure_ascii=False),
                "start_state": str(block_meta.get("block_start_state") or ""),
                "end_state": str(block_meta.get("block_end_state") or ""),
                "continuity_anchor": str(block_meta.get("block_continuity_anchor") or ""),
                "final_prompt_block_text": str(compiled_block.get("final_prompt_block_text") or ""),
                "qa_status": str(compiled_block.get("qa_status") or qa.get("qa_status") or ""),
            })

    parent_csv_path = out_dir / f"{stem}_parents.csv"
    with parent_csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=PARENT_OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(parent_rows)
    paths["parent_csv"] = parent_csv_path

    child_csv_path = out_dir / f"{stem}_children.csv"
    with child_csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CHILD_OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(child_rows)
    paths["child_csv"] = child_csv_path

    jsonl_path = out_dir / f"{stem}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in parent_rows:
            fh.write(json.dumps({"row_type": "parent", **row}, ensure_ascii=False) + "\n")
        for row in child_rows:
            fh.write(json.dumps({"row_type": "child", **row}, ensure_ascii=False) + "\n")
    paths["jsonl"] = jsonl_path

    md_path = out_dir / f"{stem}.md"
    with md_path.open("w", encoding="utf-8") as fh:
        fh.write("| " + " | ".join(PARENT_OUTPUT_COLUMNS) + " |\n")
        fh.write("| " + " | ".join(["---"] * len(PARENT_OUTPUT_COLUMNS)) + " |\n")
        for row in parent_rows:
            cells: list[str] = []
            for col in PARENT_OUTPUT_COLUMNS:
                val = str(row.get(col) or "")
                cells.append(val.replace("|", "\\|").replace("\n", " "))
            fh.write("| " + " | ".join(cells) + " |\n")
        fh.write("\n")
        fh.write("| " + " | ".join(CHILD_OUTPUT_COLUMNS) + " |\n")
        fh.write("| " + " | ".join(["---"] * len(CHILD_OUTPUT_COLUMNS)) + " |\n")
        for row in child_rows:
            cells = []
            for col in CHILD_OUTPUT_COLUMNS:
                val = str(row.get(col) or "")
                cells.append(val.replace("|", "\\|").replace("\n", " "))
            fh.write("| " + " | ".join(cells) + " |\n")
    paths["md"] = md_path

    return paths


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse  # noqa: PLC0415

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="BOSMAX Batch Video Prompt Exporter v1 — resolve batch YAML into prompt rows."
    )
    parser.add_argument("input", nargs="?", help="Path to batch input YAML file.")
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help=f"Output folder for generated files (default: {OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve rows but do not write output files.",
    )
    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    batch_input = _json_like_load(input_path)

    if _looks_like_compiled_template(batch_input) or (
        isinstance(batch_input, dict) and "compiled_templates" in batch_input
    ) or isinstance(batch_input, list):
        try:
            templates = _coerce_compiled_templates(batch_input)
        except ExporterError as exc:
            print(f"EXPORT ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

        print(f"Resolved {len(templates)} compiled template(s)  workflow=VIDEO_TEMPLATE_COMPILER")
        if args.dry_run:
            print("  (dry-run: no files written)")
            for template in templates:
                print(
                    f"  [{template.get('template_id', 'UNKNOWN')}]"
                    f" status={template.get('qa', {}).get('qa_status', '')}"
                    f" blocks={template.get('duration', {}).get('block_count', 0)}"
                )
            return

        out_dir = Path(args.output_dir)
        paths = export_compiled_templates(templates, output_dir=out_dir)
        for fmt, path in sorted(paths.items()):
            print(f"  [{fmt.upper():10s}] {path}")
        return

    try:
        rows = run_batch(batch_input)
    except ExporterError as exc:
        print(f"EXPORT ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    workflow = str(batch_input.get("product_workflow", "UNKNOWN"))
    print(f"Resolved {len(rows)} row(s)  workflow={workflow}")

    if args.dry_run:
        print("  (dry-run: no files written)")
        for row in rows:
            print(
                f"  [{row['row_index']:3d}] {row['prompt_id']}"
                f"  copy={row['copywriting_id']}"
                f"  avatar={row['avatar_context_id']}"
                f"  status={row['route_status']}"
            )
        return

    out_dir = Path(args.output_dir)
    paths = export_rows(rows, workflow, out_dir)
    for fmt, path in sorted(paths.items()):
        print(f"  [{fmt.upper():5s}] {path}")


if __name__ == "__main__":
    main()
