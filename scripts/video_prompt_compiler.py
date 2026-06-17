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

# Section 9 defaults to NO_OVERLAY. Overlay/subtitle/on-screen-text instructions
# must not leak into the seed/storyboard surfaces unless the operator explicitly
# opted in (parsed.overlay_allowed). Hook/body/CTA must stay spoken, never
# auto-converted to on-screen copy.
OVERLAY_PATTERNS = [
    r"\boverlay\b",
    r"text overlay",
    r"on-?screen text",
    r"on-?screen copy",
    r"on-?screen caption",
    r"\bsubtitle",
    r"\blower[- ]?third",
    r"\bcaption\b",
    r"\bsari kata\b",
    r"teks atas skrin",
    r"teks pada skrin",
]

ENGINE_ADAPTERS = {
    "GROK": "GROK_EXTENSION_V1",
    "GOOGLE_FLOW": "FLOW_EXTEND_UI_V1",
    "VEO_3_1": "VEO_CLIP_CHAIN_V1",
    "VEO_3_1_LITE": "VEO_CLIP_CHAIN_V1",
}

MULTI_BLOCK_COLLAPSE_PATTERNS = [
    r"Create one 16-second GROK video prompt",
    r"one continuous 16s video",
    r"VISUAL STORY\s*[-:]\s*FIRST 10 SECONDS",
    r"VISUAL STORY\s*[-:]\s*FINAL 6 SECONDS",
]

PROMPT_SET_SECTION_HEADINGS = [
    "ROLE & OBJECTIVE",
    "PRODUCT TRUTH LOCK",
    "CONTINUITY & STATE LOCK",
    "VISUAL STORY",
    "SHOT & CAMERA RULES",
    "SPOKEN DIALOGUE",
    "WPS & DIALOGUE BUDGET",
    "CTA & END FRAME",
    "NO_OVERLAY",
]


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


def _scan_overlay_leakage(texts: list[str], overlay_allowed: bool) -> list[str]:
    if overlay_allowed:
        return []
    findings: list[str] = []
    for text in texts:
        for pattern in OVERLAY_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                findings.append(
                    f"overlay leakage blocked (Section 9 defaults to NO_OVERLAY): "
                    f"{pattern} in '{text[:120]}'"
                )
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


def _compute_dialogue_budget_status(words: int, budget: dict[str, Any]) -> str:
    minimum_words = int(budget.get("minimum_words", 0))
    target_min = int(budget.get("target_min_words", 0))
    target_max = int(budget.get("target_max_words", 0))
    safe_max = int(budget.get("safe_max_words", 0))
    if safe_max and words > safe_max:
        return "FAIL"
    if minimum_words and words < minimum_words:
        return "WARN"
    if target_min and words < target_min:
        return "WARN"
    if target_max and words > target_max:
        return "WARN"
    return "PASS"


def _build_engine_rules(identity: dict[str, Any], block: dict[str, Any], is_first: bool) -> str:
    lines: list[str] = []
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
    return " ".join(line for line in lines if line).strip()


def _build_prompt_set_sections(
    template: dict[str, Any],
    block: dict[str, Any],
    total_blocks: int,
) -> tuple[list[dict[str, Any]], str, int]:
    identity = template["identity"]
    is_first = int(block["block_index"]) == 1
    is_final = int(block["block_index"]) == total_blocks
    storyboard = template["storyboard"]
    dialogue = str(block.get("block_dialogue_or_copy", ""))
    dialogue_words = _word_count(dialogue)
    wps_budget = dict(block.get("block_wps_budget") or {})
    safe_max_words = int(wps_budget.get("safe_max_words", 0))
    dialogue_budget_status = _compute_dialogue_budget_status(dialogue_words, wps_budget)
    cta = str(template["parsed"].get("cta", "")).strip()
    continuation_text = (
        "Continue directly from the previous prompt set. Do not restart the scene, product intro, avatar identity, lighting, scale, wardrobe, camera style, or commercial arc."
        if not is_first
        else "This is the opening prompt set. Establish the scene cleanly without implying any prior unseen clip."
    )
    cta_text = (
        f"Deliver the spoken CTA naturally: {cta} End frame: {block['block_end_state']}"
        if is_final
        else f"No CTA yet unless the operator explicitly overrides it. End frame: {block['block_end_state']} Carry the commercial tension into Set {int(block['block_index']) + 1}."
    )
    overlay_text = (
        "NO_OVERLAY. No visual text layer of any kind. Spoken hook/body/CTA must remain spoken and never be converted into visual copy."
        if not template["parsed"].get("overlay_allowed", False)
        else "Overlay is operator-enabled. Keep any text minimal and never cover the product label, avatar identity, or visual truth."
    )
    budget_line = (
        f"dialogue_word_count={dialogue_words}; safe_max_words={safe_max_words}; "
        f"dialogue_budget_status={dialogue_budget_status}; "
        f"language={wps_budget.get('language', '')}; pace_class={wps_budget.get('pace_class', '')}; "
        f"target_min_words={wps_budget.get('target_min_words', 0)}; "
        f"target_max_words={wps_budget.get('target_max_words', 0)}."
    )
    sections = [
        {
            "section_index": 1,
            "section_heading": PROMPT_SET_SECTION_HEADINGS[0],
            "section_text": (
                f"Set {block['block_index']} of {total_blocks}. Build a complete {block['block_duration']}-second "
                f"{identity['engine']} prompt for the {block['block_narrative_function']} beat. "
                f"output_mode={'MULTI_PROMPT_SET' if total_blocks > 1 else 'SINGLE_PROMPT'}. "
                f"block_source={block['block_id']}."
            ),
        },
        {
            "section_index": 2,
            "section_heading": PROMPT_SET_SECTION_HEADINGS[1],
            "section_text": storyboard["product_continuity_lock"],
        },
        {
            "section_index": 3,
            "section_heading": PROMPT_SET_SECTION_HEADINGS[2],
            "section_text": (
                f"{continuation_text} Character continuity: {storyboard['character_continuity_lock']} "
                f"Setting/camera continuity: {storyboard['setting_camera_lock']} "
                f"Start state: {block['block_start_state']} Continuity anchor: {block['block_continuity_anchor']}"
            ),
        },
        {
            "section_index": 4,
            "section_heading": PROMPT_SET_SECTION_HEADINGS[3],
            "section_text": (
                f"Visual action: {block['block_visual_action']} "
                f"Narrative function: {block['block_narrative_function']}."
            ),
        },
        {
            "section_index": 5,
            "section_heading": PROMPT_SET_SECTION_HEADINGS[4],
            "section_text": _build_engine_rules(identity, block, is_first),
        },
        {
            "section_index": 6,
            "section_heading": PROMPT_SET_SECTION_HEADINGS[5],
            "section_text": f"Spoken dialogue only: {dialogue}",
        },
        {
            "section_index": 7,
            "section_heading": PROMPT_SET_SECTION_HEADINGS[6],
            "section_text": budget_line,
        },
        {
            "section_index": 8,
            "section_heading": PROMPT_SET_SECTION_HEADINGS[7],
            "section_text": cta_text,
        },
        {
            "section_index": 9,
            "section_heading": PROMPT_SET_SECTION_HEADINGS[8],
            "section_text": overlay_text,
        },
    ]
    prompt_set_header = f"SET {block['block_index']} - {block['block_duration']} SECONDS"
    return sections, dialogue_budget_status, safe_max_words


def _render_prompt_set_text(prompt_set: dict[str, Any]) -> str:
    lines = [f"SET {prompt_set['set_index']} - {prompt_set['set_duration']} SECONDS"]
    for section in prompt_set["final_prompt_9_sections"]:
        lines.append(f"SECTION {section['section_index']} - {section['section_heading']}")
        lines.append(str(section["section_text"]))
    return "\n".join(lines)


def _render_final_prompt_text(output_mode: str, prompt_sets: list[dict[str, Any]]) -> str:
    header = "MULTI-PROMPT SET" if output_mode == "MULTI_PROMPT_SET" else "SINGLE PROMPT"
    lines = [header, f"prompt_set_count: {len(prompt_sets)}"]
    for prompt_set in prompt_sets:
        lines.append("")
        lines.append(_render_prompt_set_text(prompt_set))
    return "\n".join(lines).strip()


def validate_compiled_prompt_structure(template: dict[str, Any]) -> list[str]:
    compiler = template.get("compiler") or {}
    duration = template.get("duration") or {}
    storyboard = template.get("storyboard") or {}
    block_plan = [int(item) for item in (duration.get("block_plan") or [])]
    block_count = int(duration.get("block_count") or len(block_plan) or 0)
    output_mode = str(compiler.get("output_mode") or "")
    prompt_set_count = int(compiler.get("prompt_set_count") or 0)
    prompt_sets = compiler.get("prompt_sets") or []
    final_prompt_blocks = compiler.get("final_prompt_blocks") or []
    final_prompt_text = str(compiler.get("final_prompt_text") or "")
    overlay_allowed = bool(template.get("parsed", {}).get("overlay_allowed", False))
    findings: list[str] = []

    if block_count <= 1:
        if output_mode != "SINGLE_PROMPT":
            findings.append("single-block output must use SINGLE_PROMPT")
        if prompt_set_count != 1:
            findings.append("single-block output must expose prompt_set_count=1")
    else:
        if output_mode != "MULTI_PROMPT_SET":
            findings.append("multi-block output must use MULTI_PROMPT_SET")
        if prompt_set_count != block_count:
            findings.append("multi-block output prompt_set_count must equal block_count")
        if "MULTI-PROMPT SET" not in final_prompt_text:
            findings.append("multi-block final_prompt_text must declare MULTI-PROMPT SET")

    if len(prompt_sets) != block_count:
        findings.append("prompt_sets length must match block_count")
    if len(final_prompt_blocks) != block_count:
        findings.append("final_prompt_blocks length must match block_count")

    block_map = {
        str(item.get("block_id")): item
        for item in (storyboard.get("block_script_json") or [])
    }

    for index, prompt_set in enumerate(prompt_sets, start=1):
        expected_duration = block_plan[index - 1] if index - 1 < len(block_plan) else None
        sections = prompt_set.get("final_prompt_9_sections") or []
        if int(prompt_set.get("set_index") or 0) != index:
            findings.append(f"prompt_set {index} set_index mismatch")
        if expected_duration is not None and int(prompt_set.get("set_duration") or 0) != expected_duration:
            findings.append(f"prompt_set {index} set_duration mismatch")
        if bool(prompt_set.get("continuation_from_previous_set")) != (index > 1):
            findings.append(f"prompt_set {index} continuation flag mismatch")
        if not isinstance(sections, list) or len(sections) != 9:
            findings.append(f"prompt_set {index} must contain exactly 9 sections")
        else:
            section_indexes = [int(section.get("section_index") or 0) for section in sections]
            if section_indexes != list(range(1, 10)):
                findings.append(f"prompt_set {index} section indexes must run 1..9")
            if not overlay_allowed and "NO_OVERLAY" not in str(sections[8].get("section_text") or ""):
                findings.append(f"prompt_set {index} section 9 must preserve NO_OVERLAY")

        block_source = str(prompt_set.get("block_source") or "")
        block_meta = block_map.get(block_source)
        if not block_meta:
            findings.append(f"prompt_set {index} block_source missing from storyboard")
            continue
        wps_budget = prompt_set.get("wps_budget") or {}
        budget_duration = int(wps_budget.get("duration_seconds") or 0)
        set_duration = int(prompt_set.get("set_duration") or 0)
        total_duration = int(duration.get("duration_seconds") or 0)
        if budget_duration <= 0 or budget_duration > set_duration:
            findings.append(f"prompt_set {index} WPS budget duration must stay within the block duration")
        if block_count > 1 and budget_duration == total_duration:
            findings.append(f"prompt_set {index} WPS budget duration must not use the total multi-block duration")
        expected_words = int(block_meta.get("block_dialogue_word_count") or 0)
        if int(prompt_set.get("dialogue_word_count") or 0) != expected_words:
            findings.append(f"prompt_set {index} dialogue_word_count mismatch")
        safe_max_words = int(wps_budget.get("safe_max_words") or 0)
        if int(prompt_set.get("safe_max_words") or 0) != safe_max_words:
            findings.append(f"prompt_set {index} safe_max_words mismatch")
        if str(prompt_set.get("dialogue_budget_status") or "") == "FAIL":
            findings.append(f"prompt_set {index} dialogue budget failed safe_max_words")

    if template.get("identity", {}).get("engine") == "GROK" and int(duration.get("duration_seconds") or 0) == 16:
        if block_plan != [10, 6]:
            findings.append("GROK 16s must derive [10,6]")
        if block_plan == [8, 8]:
            findings.append("GROK 16s must never use [8,8]")

    surfaces = [final_prompt_text]
    surfaces.extend(str(block.get("final_prompt_block_text") or "") for block in final_prompt_blocks)
    for surface in surfaces:
        for pattern in MULTI_BLOCK_COLLAPSE_PATTERNS:
            if re.search(pattern, surface, flags=re.IGNORECASE):
                findings.append(f"forbidden multi-block collapse pattern: {pattern}")

    return findings


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
    errors.extend(
        _scan_overlay_leakage(texts, bool(template["parsed"].get("overlay_allowed", False)))
    )
    warnings = list(template["qa"].get("qa_warnings", []))
    warnings.extend(budget_warnings)

    blocks = template["storyboard"].get("block_script_json", [])
    prompt_sets: list[dict[str, Any]] = []
    final_prompt_blocks: list[dict[str, Any]] = []
    for block in blocks:
        sections, dialogue_budget_status, safe_max_words = _build_prompt_set_sections(
            template,
            block,
            len(blocks),
        )
        prompt_set = {
            "set_index": block["block_index"],
            "set_duration": block["block_duration"],
            "set_role": block["block_narrative_function"],
            "block_source": block["block_id"],
            "continuation_from_previous_set": int(block["block_index"]) > 1,
            "wps_budget": dict(block.get("block_wps_budget") or {}),
            "dialogue_word_count": block.get("block_dialogue_word_count", 0),
            "safe_max_words": safe_max_words,
            "dialogue_budget_status": dialogue_budget_status,
            "final_prompt_9_sections": sections,
        }
        prompt_set_text = _render_prompt_set_text(prompt_set)
        prompt_sets.append(prompt_set)
        final_prompt_blocks.append(
            {
                "block_id": block["block_id"],
                "block_index": block["block_index"],
                "block_duration": block["block_duration"],
                "set_role": block["block_narrative_function"],
                "continuation_from_previous_set": int(block["block_index"]) > 1,
                "dialogue_word_count": block.get("block_dialogue_word_count", 0),
                "safe_max_words": safe_max_words,
                "dialogue_budget_status": dialogue_budget_status,
                "final_prompt_9_sections": sections,
                "final_prompt_block_text": prompt_set_text,
                "qa_status": "FAIL" if (errors or dialogue_budget_status == "FAIL") else ("WARN" if dialogue_budget_status == "WARN" else "PASS"),
            }
        )

    template["compiler"]["engine_adapter"] = ENGINE_ADAPTERS[template["identity"]["engine"]]
    template["compiler"]["compiler_version"] = "video_template_compiler_runtime@1.0.0"
    template["compiler"]["output_mode"] = "MULTI_PROMPT_SET" if len(blocks) > 1 else "SINGLE_PROMPT"
    template["compiler"]["prompt_set_count"] = len(prompt_sets)
    template["compiler"]["prompt_sets"] = prompt_sets
    template["compiler"]["final_prompt_blocks"] = final_prompt_blocks
    template["compiler"]["final_prompt_text"] = _render_final_prompt_text(
        template["compiler"]["output_mode"],
        prompt_sets,
    )
    structure_errors = validate_compiled_prompt_structure(template)
    template["compiler"]["compiler_errors"] = errors + budget_errors + structure_errors
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
