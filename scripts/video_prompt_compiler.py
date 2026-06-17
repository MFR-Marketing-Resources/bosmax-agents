from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from video_storyboard_builder import StoryboardError, build_storyboard  # type: ignore[import]
from video_template_parser import build_canonical_template, load_input  # type: ignore[import]

MARKER_PATTERNS = [
    r"CTX_",
    r"CAM_",
    r"CLASS_",
    r"SCRIPT_",
    r"DNA_",
    r"ANCHOR_",
    r"\bTRG\b",
    r"TEMP_",
    r"SCENE_",
    r"BLOCK_",
    r"INTERVAL_",
    r"REF_",
    r"IMG_",
    r"VID_",
    r"AUDIO_",
    r"GEN_",
    r"RENDER_",
]

UNSAFE_CLAIM_PATTERNS = [
    (r"\bcure\b|\bpenawar\b|\bsembuh\b", "medical cure claim"),
    (r"\bguaranteed\b|\bjamin\b", "guaranteed result claim"),
    (r"\berectile\b|\blibido\b|\bsexual performance\b", "sexual-performance claim"),
    (r"\bapply directly to penis\b|\bsapu terus pada zakar\b", "risky direct-body-use instruction"),
]

ENGINE_ADAPTERS = {
    "GROK": "GROK_EXTENSION_V1",
    "GOOGLE_FLOW": "FLOW_EXTEND_UI_V1",
    "VEO_3_1": "VEO_CLIP_CHAIN_V1",
    "VEO_3_1_LITE": "VEO_CLIP_CHAIN_V1",
}


class CompilerError(RuntimeError):
    """Raised when the prompt compiler is blocked by governance or QA."""


def _load_template(path: Path) -> dict[str, Any]:
    payload = load_input(path)
    if "identity" in payload and "duration" in payload and "storyboard" in payload:
        return payload
    return build_storyboard(build_canonical_template(payload, path))


def _word_count(text: str) -> int:
    return len([token for token in text.split() if token.strip()])


def _collect_text_surfaces(template: dict[str, Any]) -> list[str]:
    texts = [
        str(template["input"].get("raw_prompt_seed", "")),
        str(template["parsed"].get("hook", "")),
        str(template["parsed"].get("body", "")),
        str(template["parsed"].get("cta", "")),
        str(template["storyboard"].get("master_storyline", "")),
        str(template["storyboard"].get("master_storyboard", "")),
    ]
    for block in template["storyboard"].get("block_script_json", []):
        texts.extend([
            str(block.get("block_visual_action", "")),
            str(block.get("block_dialogue_or_copy", "")),
            str(block.get("block_start_state", "")),
            str(block.get("block_end_state", "")),
            str(block.get("block_continuity_anchor", "")),
        ])
    return [text for text in texts if text]


def _scan_marker_leakage(texts: list[str]) -> list[str]:
    findings: list[str] = []
    for text in texts:
        for pattern in MARKER_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                findings.append(f"marker leakage detected: {pattern} in '{text[:120]}'")
    return findings


def _scan_unsafe_claims(texts: list[str], forbidden_claims: list[str]) -> list[str]:
    findings: list[str] = []
    combined = "\n".join(texts)
    for pattern, label in UNSAFE_CLAIM_PATTERNS:
        if re.search(pattern, combined, flags=re.IGNORECASE):
            findings.append(f"unsafe claim blocked: {label}")
    for claim in forbidden_claims:
        if claim and claim.lower() in combined.lower():
            findings.append(f"forbidden claim phrase blocked: {claim}")
    return findings


def _validate_storyboard_presence(template: dict[str, Any]) -> list[str]:
    storyboard = template["storyboard"]
    duration = template["duration"]
    findings: list[str] = []
    if duration["block_mode"] == "MULTI_BLOCK":
        if not storyboard.get("master_storyboard"):
            findings.append("multi-block runtime missing master_storyboard")
        if not storyboard.get("master_storyline"):
            findings.append("multi-block runtime missing master_storyline")
        if not storyboard.get("character_continuity_lock"):
            findings.append("multi-block runtime missing character_continuity_lock")
        if not storyboard.get("product_continuity_lock"):
            findings.append("multi-block runtime missing product_continuity_lock")
        if not storyboard.get("setting_camera_lock"):
            findings.append("multi-block runtime missing setting_camera_lock")
    return findings


def _validate_word_budgets(template: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for block in template["storyboard"].get("block_script_json", []):
        dialogue = str(block.get("block_dialogue_or_copy", ""))
        words = _word_count(dialogue)
        budget = block.get("block_wps_budget") or {}
        minimum_words = int(budget.get("minimum_words", 0))
        target_min = int(budget.get("target_min_words", 0))
        target_max = int(budget.get("target_max_words", 0))
        safe_max = int(budget.get("safe_max_words", 0))
        block_id = str(block.get("block_id", "UNKNOWN_BLOCK"))

        if safe_max and words > safe_max:
            errors.append(f"{block_id} exceeds safe_max_words {safe_max} with {words} words")
        elif target_max and words > target_max:
            warnings.append(f"{block_id} exceeds target_max_words {target_max} with {words} words")
        if minimum_words and words < minimum_words:
            warnings.append(f"{block_id} is underfilled: {words} words < minimum_words {minimum_words}")
        elif target_min and words < target_min:
            warnings.append(f"{block_id} is below target_min_words {target_min} with {words} words")
    return errors, warnings


def _build_block_prompt(template: dict[str, Any], block: dict[str, Any], total_blocks: int) -> str:
    identity = template["identity"]
    storyboard = template["storyboard"]
    is_first = int(block["block_index"]) == 1
    lines = [
        f"Engine adapter: {ENGINE_ADAPTERS[identity['engine']]}",
        f"Product lane: {identity['product_lane']}",
        f"Platform: {identity['platform']}",
        f"Mode: {identity['mode']}",
        f"Master storyline: {storyboard['master_storyline']}",
        f"Master storyboard: {storyboard['master_storyboard']}",
        f"Character continuity lock: {storyboard['character_continuity_lock']}",
        f"Product continuity lock: {storyboard['product_continuity_lock']}",
        f"Setting/camera lock: {storyboard['setting_camera_lock']}",
        f"Block duration: {block['block_duration']}s",
        f"Narrative function: {block['block_narrative_function']}",
        f"Visual action: {block['block_visual_action']}",
        f"Dialogue or copy: {block['block_dialogue_or_copy']}",
        f"Start state: {block['block_start_state']}",
        f"End state target: {block['block_end_state']}",
        f"Continuity anchor: {block['block_continuity_anchor']}",
    ]

    if identity["engine"] == "GROK":
        if not is_first:
            lines.extend([
                "Resume inside 0.5-1.0 seconds from the previous spoken seam.",
                "Do not restart greeting or re-introduce the presenter.",
            ])
        lines.append("Keep product truth repeated naturally without medical or sexual-performance claims.")
    elif identity["engine"] == "GOOGLE_FLOW":
        if not is_first:
            lines.append(
                f"Previous clip final second state: {block.get('previous_clip_final_second_state', '')}"
            )
        lines.extend([
            "Keep chronology literal and continuation-ready for Flow Extend UI.",
            "Do not depend on vague 'from last frame' shorthand; spell out continuity explicitly.",
        ])
    else:
        lines.extend([
            "Keep Veo clip-chain continuity strict across identity, product label, packaging scale, and scene framing.",
            "Use a passable last frame for the next clip without resetting the commercial arc.",
        ])

    if int(block["block_index"]) == total_blocks:
        lines.append("Close with a clear CTA-ready hero state and no overlay text.")
    return "\n".join(lines)


def compile_template(template: dict[str, Any]) -> dict[str, Any]:
    if not template.get("storyboard", {}).get("block_script_json"):
        try:
            template = build_storyboard(template)
        except StoryboardError as exc:
            raise CompilerError(str(exc)) from exc

    errors = _validate_storyboard_presence(template)
    budget_errors, budget_warnings = _validate_word_budgets(template)
    texts = _collect_text_surfaces(template)
    errors.extend(_scan_marker_leakage(texts))
    errors.extend(_scan_unsafe_claims(texts, template["parsed"].get("forbidden_claims", [])))
    warnings = list(template["qa"].get("qa_warnings", []))
    warnings.extend(budget_warnings)

    blocks = template["storyboard"].get("block_script_json", [])
    final_prompt_blocks: list[dict[str, Any]] = []
    for block in blocks:
        final_prompt_blocks.append(
            {
                "block_id": block["block_id"],
                "block_index": block["block_index"],
                "final_prompt_block_text": _build_block_prompt(template, block, len(blocks)),
                "qa_status": "FAIL" if errors else "PASS",
            }
        )

    template["compiler"]["engine_adapter"] = ENGINE_ADAPTERS[template["identity"]["engine"]]
    template["compiler"]["compiler_version"] = "video_template_compiler_runtime@1.0.0"
    template["compiler"]["final_prompt_blocks"] = final_prompt_blocks
    template["compiler"]["final_prompt_text"] = "\n\n".join(
        block["final_prompt_block_text"] for block in final_prompt_blocks
    )
    template["compiler"]["compiler_errors"] = errors + budget_errors
    template["compiler"]["compiler_warnings"] = warnings

    all_errors = template["compiler"]["compiler_errors"]
    template["compiler"]["prompt_surface_status"] = "BLOCKED" if all_errors else "COMPILED"
    template["qa"]["qa_errors"] = all_errors
    template["qa"]["qa_warnings"] = warnings
    template["qa"]["qa_status"] = "FAIL" if all_errors else ("WARN" if warnings else "PASS")
    template["qa"]["production_ready"] = not all_errors
    template["qa"]["export_ready"] = not all_errors and bool(final_prompt_blocks)
    template["qa"]["notion_ready"] = not all_errors and bool(final_prompt_blocks)
    template["qa"]["generated_by"] = "scripts/video_prompt_compiler.py"
    return template


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile BOSMAX video storyboard payloads into engine-specific prompt surfaces."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--format", choices=("json", "yaml"), default="json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    template = _load_template(Path(args.input))
    compiled = compile_template(template)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() in {".yaml", ".yml"} or args.format == "yaml":
            output_path.write_text(
                yaml.safe_dump(compiled, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
        else:
            output_path.write_text(
                json.dumps(compiled, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        print(output_path)
        return

    if args.format == "yaml":
        print(yaml.safe_dump(compiled, sort_keys=False, allow_unicode=True))
        return
    print(json.dumps(compiled, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
