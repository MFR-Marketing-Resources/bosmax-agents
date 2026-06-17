from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from video_prompt_compiler import (  # type: ignore[import]
    compile_template,
    validate_compiled_prompt_structure,
)
from video_storyboard_builder import build_storyboard  # type: ignore[import]
from video_template_parser import build_canonical_template, load_input  # type: ignore[import]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def expect(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def compile_fixture(path: Path) -> dict:
    payload = load_input(path)
    if "identity" in payload and "storyboard" in payload:
        template = payload
    else:
        template = build_storyboard(build_canonical_template(payload, path))
    return compile_template(template)


def expect_prompt_set_contract(
    compiled: dict[str, Any],
    name: str,
    *,
    expected_mode: str,
    expected_durations: list[int],
) -> None:
    compiler = compiled["compiler"]
    prompt_sets = compiler["prompt_sets"]
    final_blocks = compiler["final_prompt_blocks"]
    storyboard_blocks = compiled["storyboard"]["block_script_json"]

    expect(compiler["output_mode"] == expected_mode, f"{name}: output_mode should be {expected_mode}")
    expect(int(compiler["prompt_set_count"]) == len(expected_durations), f"{name}: prompt_set_count mismatch")
    expect(len(prompt_sets) == len(expected_durations), f"{name}: prompt_sets count mismatch")
    expect(len(final_blocks) == len(expected_durations), f"{name}: final_prompt_blocks count mismatch")

    continuation_flags = [False] + [True] * (len(expected_durations) - 1)
    for index, prompt_set in enumerate(prompt_sets, start=1):
        block_meta = storyboard_blocks[index - 1]
        expect(int(prompt_set["set_index"]) == index, f"{name}: set {index} index mismatch")
        expect(int(prompt_set["set_duration"]) == expected_durations[index - 1], f"{name}: set {index} duration mismatch")
        expect(prompt_set["set_role"] == block_meta["block_narrative_function"], f"{name}: set {index} role mismatch")
        expect(prompt_set["block_source"] == block_meta["block_id"], f"{name}: set {index} block_source mismatch")
        expect(
            bool(prompt_set["continuation_from_previous_set"]) is continuation_flags[index - 1],
            f"{name}: set {index} continuation flag mismatch",
        )
        expect(
            isinstance(prompt_set["final_prompt_9_sections"], list) and len(prompt_set["final_prompt_9_sections"]) == 9,
            f"{name}: set {index} must contain exactly 9 sections",
        )
        expect(
            [int(section["section_index"]) for section in prompt_set["final_prompt_9_sections"]] == list(range(1, 10)),
            f"{name}: set {index} section indexes must run 1..9",
        )
        expect(
            int(prompt_set["dialogue_word_count"]) == int(block_meta["block_dialogue_word_count"]),
            f"{name}: set {index} dialogue_word_count mismatch",
        )
        expect(
            int(prompt_set["safe_max_words"]) == int(prompt_set["wps_budget"]["safe_max_words"]),
            f"{name}: set {index} safe_max_words mismatch",
        )
        expect(
            0 < int(prompt_set["wps_budget"]["duration_seconds"]) <= expected_durations[index - 1],
            f"{name}: set {index} WPS budget duration must stay inside the block duration",
        )
        expect(
            prompt_set["dialogue_budget_status"] in {"PASS", "WARN"},
            f"{name}: set {index} dialogue_budget_status must be PASS/WARN",
        )
        section_9 = prompt_set["final_prompt_9_sections"][8]
        expect(
            "NO_OVERLAY" in str(section_9["section_text"]),
            f"{name}: set {index} section 9 must preserve NO_OVERLAY",
        )

    forbidden_needles = [
        "VISUAL STORY - FIRST 10 SECONDS",
        "VISUAL STORY - FINAL 6 SECONDS",
        "Create one 16-second GROK video prompt",
        "one continuous 16s video",
        "[8,8]",
    ]
    final_prompt_text = str(compiler["final_prompt_text"])
    for needle in forbidden_needles:
        expect(needle not in final_prompt_text, f"{name}: forbidden combined-output pattern absent: {needle}")
    if compiled["identity"]["engine"] == "GROK":
        for index, prompt_set in enumerate(prompt_sets, start=1):
            expect(
                int(prompt_set["wps_budget"]["duration_seconds"]) == expected_durations[index - 1],
                f"{name}: GROK set {index} WPS budget duration must equal set duration",
            )


def validate_valid_compiles() -> None:
    fixtures = {
        "bosmax_grok_frames_single_6s.yaml": ("GROK_EXTENSION_V1", "SINGLE_PROMPT", [6]),
        "bosmax_flow_frames_multi_8x8.yaml": ("FLOW_EXTEND_UI_V1", "MULTI_PROMPT_SET", [8, 8]),
        "bosmax_hybrid_multi_8x8.yaml": ("VEO_CLIP_CHAIN_V1", "MULTI_PROMPT_SET", [8, 8]),
        "mwtcb_product_demo_single_6s.yaml": ("GROK_EXTENSION_V1", "SINGLE_PROMPT", [6]),
        # Google Flow 10s extend lane (FLOW_EXTEND_10S) + GROK 16s [10,6]
        "bosmax_flow_extend_10s_single_10s.yaml": ("FLOW_EXTEND_UI_V1", "SINGLE_PROMPT", [10]),
        "bosmax_flow_extend_18s_10_8.yaml": ("FLOW_EXTEND_UI_V1", "MULTI_PROMPT_SET", [10, 8]),
        "bosmax_flow_extend_20s_10_10.yaml": ("FLOW_EXTEND_UI_V1", "MULTI_PROMPT_SET", [10, 10]),
        "bosmax_grok_extend_16s_10_6.yaml": ("GROK_EXTENSION_V1", "MULTI_PROMPT_SET", [10, 6]),
    }
    fixture_dir = ROOT / "samples" / "video_template_compiler"
    for name, (adapter, output_mode, durations) in fixtures.items():
        compiled = compile_fixture(fixture_dir / name)
        expect(compiled["compiler"]["engine_adapter"] == adapter, f"{name}: engine adapter mismatch")
        expect(bool(compiled["compiler"]["final_prompt_text"]), f"{name}: final_prompt_text missing")
        expect(len(compiled["compiler"]["final_prompt_blocks"]) == compiled["duration"]["block_count"], f"{name}: final_prompt_blocks count mismatch")
        expect(compiled["compiler"]["prompt_surface_status"] == "COMPILED", f"{name}: prompt surface should be COMPILED")
        expect_prompt_set_contract(compiled, name, expected_mode=output_mode, expected_durations=durations)
        print(f"PASS: compiled {name}")


def validate_fail_fixtures() -> None:
    fixture_dir = ROOT / "samples" / "video_template_compiler"
    expected_failures = {
        "unsafe_claim_seed.yaml": "unsafe claim blocked",
        "marker_leak_seed.yaml": "marker leakage detected",
        "missing_storyboard_multi.yaml": "multi-block runtime missing master_storyboard",
        "wps_overflow_multi.yaml": "exceeds safe_max_words",
        "overlay_leak_seed.yaml": "overlay leakage blocked",
    }
    for name, needle in expected_failures.items():
        compiled = compile_fixture(fixture_dir / name)
        error_blob = "\n".join(compiled["qa"]["qa_errors"])
        expect(compiled["qa"]["qa_status"] == "FAIL", f"{name}: expected FAIL")
        expect(needle in error_blob, f"{name}: expected error containing {needle!r}, got {error_blob!r}")
        print(f"PASS: blocked {name}")


def validate_collapsed_multi_block_rejected() -> None:
    fixture_dir = ROOT / "samples" / "video_template_compiler"
    compiled = compile_fixture(fixture_dir / "bosmax_grok_extend_16s_10_6.yaml")

    compiled["compiler"]["output_mode"] = "SINGLE_PROMPT"
    compiled["compiler"]["prompt_set_count"] = 1
    compiled["compiler"]["prompt_sets"] = compiled["compiler"]["prompt_sets"][:1]
    compiled["compiler"]["final_prompt_blocks"] = compiled["compiler"]["final_prompt_blocks"][:1]
    compiled["compiler"]["final_prompt_text"] = (
        "Create one 16-second GROK video prompt. "
        "VISUAL STORY - FIRST 10 SECONDS. "
        "VISUAL STORY - FINAL 6 SECONDS."
    )

    findings = validate_compiled_prompt_structure(compiled)
    joined = "\n".join(findings)
    expect(findings, "collapsed GROK 16s should produce validator findings")
    expect("multi-block output must use MULTI_PROMPT_SET" in joined, "collapsed GROK 16s must fail output_mode guard")
    expect("forbidden multi-block collapse pattern" in joined, "collapsed GROK 16s must fail forbidden-pattern guard")
    print("PASS: collapsed multi-block output rejected")


def main() -> None:
    validate_valid_compiles()
    validate_fail_fixtures()
    validate_collapsed_multi_block_rejected()
    print("PASS: validate_video_prompt_compiler")


if __name__ == "__main__":
    main()
