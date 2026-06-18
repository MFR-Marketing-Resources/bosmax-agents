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
    expected_adapter: str,
    expected_mode: str,
    expected_durations: list[int],
) -> None:
    expect(compiled["compiler"]["engine_adapter"] == expected_adapter, f"{name}: engine adapter mismatch")
    compiler = compiled["compiler"]
    prompt_sets = compiler["prompt_sets"]
    final_blocks = compiler["final_prompt_blocks"]
    storyboard_blocks = compiled["storyboard"]["block_script_json"]
    engine = compiled["identity"]["engine"]
    intake_mode = compiled["identity"].get("intake_mode", "")

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
            "previous_clip_final_second_state" in prompt_set,
            f"{name}: set {index} previous_clip_final_second_state field missing",
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
        section_blob = "\n".join(str(section["section_text"]) for section in prompt_set["final_prompt_9_sections"])
        if engine == "GOOGLE_FLOW":
            expect(
                int(prompt_set["wps_budget"]["duration_seconds"]) == expected_durations[index - 1],
                f"{name}: Google Flow set {index} WPS budget duration must equal set duration",
            )
            if index == 1:
                expect(
                    str(prompt_set["previous_clip_final_second_state"]) == "",
                    f"{name}: Google Flow set 1 previous_clip_final_second_state must be empty",
                )
            else:
                expected_previous = str(block_meta["previous_clip_final_second_state"])
                expect(
                    str(prompt_set["previous_clip_final_second_state"]) == expected_previous,
                    f"{name}: Google Flow set {index} previous_clip_final_second_state mismatch",
                )
                expect(
                    f"Previous clip final second state: {expected_previous}" in section_blob,
                    f"{name}: Google Flow set {index} must spell out previous clip final state",
                )
                expect(
                    "Continue from that exact state into" in section_blob,
                    f"{name}: Google Flow set {index} must declare the exact next action",
                )
                expect(
                    "Continuity seam instruction:" in section_blob,
                    f"{name}: Google Flow set {index} must include seam instruction",
                )
                expect(
                    "Do not restart the scene, product intro, avatar identity, lighting, scale, wardrobe, camera style, or commercial arc." in section_blob,
                    f"{name}: Google Flow set {index} must block scene and identity resets",
                )
        if engine == "GOOGLE_FLOW" and intake_mode == "READY_FRAME":
            expect(
                "visual truth" in section_blob.lower(),
                f"{name}: READY_FRAME Flow set {index} must preserve uploaded frame truth",
            )
        if engine == "GOOGLE_FLOW" and intake_mode == "ASSET_SET":
            expect(
                "Asset role map:" in section_blob,
                f"{name}: ASSET_SET Flow set {index} must preserve asset role map",
            )
            expect(
                "Asset hierarchy:" in section_blob,
                f"{name}: ASSET_SET Flow set {index} must preserve asset hierarchy",
            )
        if engine == "GOOGLE_FLOW" and intake_mode == "PRODUCT_ONLY":
            expect(
                "Scale lock:" in section_blob,
                f"{name}: PRODUCT_ONLY Flow set {index} must preserve scale lock",
            )

    forbidden_needles = [
        "VISUAL STORY - FIRST 10 SECONDS",
        "VISUAL STORY - FINAL 6 SECONDS",
        "VISUAL STORY - FIRST 8 SECONDS",
        "VISUAL STORY - FINAL 8 SECONDS",
        "Create one 16-second GROK video prompt",
        "Create one 16-second Google Flow video prompt",
        "one continuous 16s video",
        "one merged 16s prompt",
        "[8,8]",
    ]
    final_prompt_text = str(compiler["final_prompt_text"])
    for needle in forbidden_needles:
        expect(needle not in final_prompt_text, f"{name}: forbidden combined-output pattern absent: {needle}")
    if engine == "GROK":
        for index, prompt_set in enumerate(prompt_sets, start=1):
            expect(
                int(prompt_set["wps_budget"]["duration_seconds"]) == expected_durations[index - 1],
                f"{name}: GROK set {index} WPS budget duration must equal set duration",
            )


def validate_valid_compiles() -> None:
    fixtures = {
        "bosmax_grok_frames_single_6s.yaml": ("GROK_EXTENSION_V1", "SINGLE_PROMPT", [6]),
        "bosmax_flow_hybrid_multi_8x8.yaml": ("FLOW_EXTEND_UI_V1", "MULTI_PROMPT_SET", [8, 8]),
        "bosmax_flow_frames_multi_8x8.yaml": ("FLOW_EXTEND_UI_V1", "MULTI_PROMPT_SET", [8, 8]),
        "bosmax_flow_ingredients_multi_8x8.yaml": ("FLOW_EXTEND_UI_V1", "MULTI_PROMPT_SET", [8, 8]),
        "bosmax_hybrid_multi_8x8.yaml": ("VEO_CLIP_CHAIN_V1", "MULTI_PROMPT_SET", [8, 8]),
        "mwtcb_product_demo_single_6s.yaml": ("GROK_EXTENSION_V1", "SINGLE_PROMPT", [6]),
        # Google Flow 10s extend lane (FLOW_EXTEND_10S) + GROK 16s [10,6]
        "bosmax_flow_extend_10s_single_10s.yaml": ("FLOW_EXTEND_10S_V1", "SINGLE_PROMPT", [10]),
        "bosmax_flow_extend_18s_10_8.yaml": ("FLOW_EXTEND_10S_V1", "MULTI_PROMPT_SET", [10, 8]),
        "bosmax_flow_extend_20s_10_10.yaml": ("FLOW_EXTEND_10S_V1", "MULTI_PROMPT_SET", [10, 10]),
        "bosmax_grok_extend_16s_10_6.yaml": ("GROK_EXTENSION_V1", "MULTI_PROMPT_SET", [10, 6]),
    }
    fixture_dir = ROOT / "samples" / "video_template_compiler"
    for name, (adapter, output_mode, durations) in fixtures.items():
        compiled = compile_fixture(fixture_dir / name)
        expect(bool(compiled["compiler"]["final_prompt_text"]), f"{name}: final_prompt_text missing")
        expect(len(compiled["compiler"]["final_prompt_blocks"]) == compiled["duration"]["block_count"], f"{name}: final_prompt_blocks count mismatch")
        expect(compiled["compiler"]["prompt_surface_status"] == "COMPILED", f"{name}: prompt surface should be COMPILED")
        expect_prompt_set_contract(
            compiled,
            name,
            expected_adapter=adapter,
            expected_mode=output_mode,
            expected_durations=durations,
        )
        # Defect A regression: no internal orchestration / WPS budget metadata may
        # leak into the engine-facing prompt body.
        final_text = str(compiled["compiler"]["final_prompt_text"])
        for leak in (
            "output_mode=",
            "block_source=",
            "dialogue_word_count=",
            "safe_max_words=",
            "dialogue_budget_status=",
            "target_min_words=",
            "target_max_words=",
            "Runtime plan",
            "Do not use two equal",
            "Do not compile as one",
        ):
            expect(leak not in final_text, f"{name}: engine-facing prompt leaked internal metadata {leak!r}")
        # Defect D regression: a speaking video must declare a presenter lip-sync
        # route or an explicit voiceover route — never a silent faceless default.
        expect(
            ("lip-sync" in final_text) or ("Voiceover narration" in final_text),
            f"{name}: prompt must declare presenter lip-sync or explicit voiceover route",
        )
        print(f"PASS: compiled {name}")


def validate_fail_fixtures() -> None:
    fixture_dir = ROOT / "samples" / "video_template_compiler"
    expected_failures = {
        "unsafe_claim_seed.yaml": "unsafe claim blocked",
        "marker_leak_seed.yaml": "marker leakage detected",
        "missing_storyboard_multi.yaml": "multi-block runtime missing master_storyboard",
        "wps_overflow_multi.yaml": "exceeds safe_max_words",
        "overlay_leak_seed.yaml": "overlay leakage blocked",
        # Regression: the "Prompt tercemar" case must block on underfill, not ship.
        "wps_underfill_multi.yaml": "is underfilled",
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


def validate_google_flow_negative_guards() -> None:
    fixture_dir = ROOT / "samples" / "video_template_compiler"
    compiled = compile_fixture(fixture_dir / "bosmax_flow_frames_multi_8x8.yaml")

    collapsed = dict(compiled)
    collapsed["duration"] = dict(compiled["duration"])
    collapsed["compiler"] = dict(compiled["compiler"])
    collapsed["compiler"]["output_mode"] = "SINGLE_PROMPT"
    collapsed["compiler"]["prompt_set_count"] = 1
    collapsed["compiler"]["prompt_sets"] = [dict(compiled["compiler"]["prompt_sets"][0])]
    collapsed["compiler"]["final_prompt_blocks"] = [dict(compiled["compiler"]["final_prompt_blocks"][0])]
    collapsed["compiler"]["final_prompt_text"] = (
        "Create one 16-second Google Flow video prompt. "
        "VISUAL STORY - FIRST 8 SECONDS. "
        "VISUAL STORY - FINAL 8 SECONDS."
    )
    findings = validate_compiled_prompt_structure(collapsed)
    joined = "\n".join(findings)
    expect(findings, "collapsed Flow 16s should produce validator findings")
    expect("multi-block output must use MULTI_PROMPT_SET" in joined, "collapsed Flow 16s must fail output_mode guard")
    expect("forbidden multi-block collapse pattern" in joined, "collapsed Flow 16s must fail forbidden-pattern guard")

    wrong_plan = dict(compiled)
    wrong_plan["duration"] = dict(compiled["duration"])
    wrong_plan["duration"]["block_plan"] = [10, 6]
    findings = validate_compiled_prompt_structure(wrong_plan)
    expect(
        "Google Flow FLOW_EXTEND_UI 16s must derive [8,8]" in "\n".join(findings),
        "Flow 16s [10,6] must fail duration-plan guard",
    )

    missing_state = dict(compiled)
    missing_state["compiler"] = dict(compiled["compiler"])
    missing_prompt_sets = []
    for prompt_set in compiled["compiler"]["prompt_sets"]:
        cloned = dict(prompt_set)
        cloned["final_prompt_9_sections"] = [dict(section) for section in prompt_set["final_prompt_9_sections"]]
        missing_prompt_sets.append(cloned)
    missing_prompt_sets[1]["previous_clip_final_second_state"] = ""
    missing_prompt_sets[1]["final_prompt_9_sections"][2]["section_text"] = missing_prompt_sets[1]["final_prompt_9_sections"][2]["section_text"].replace(
        f"Previous clip final second state: {compiled['compiler']['prompt_sets'][1]['previous_clip_final_second_state']} ",
        "",
    )
    missing_prompt_sets[1]["final_prompt_9_sections"][4]["section_text"] = missing_prompt_sets[1]["final_prompt_9_sections"][4]["section_text"].replace(
        f"Previous clip final second state: {compiled['compiler']['prompt_sets'][1]['previous_clip_final_second_state']} ",
        "",
    )
    missing_state["compiler"]["prompt_sets"] = missing_prompt_sets
    findings = validate_compiled_prompt_structure(missing_state)
    joined = "\n".join(findings)
    expect(
        "Google Flow continuation must expose previous_clip_final_second_state" in joined,
        "Flow continuation without previous clip state must fail",
    )
    print("PASS: Google Flow negative guards")


def main() -> None:
    validate_valid_compiles()
    validate_fail_fixtures()
    validate_collapsed_multi_block_rejected()
    validate_google_flow_negative_guards()
    print("PASS: validate_video_prompt_compiler")


if __name__ == "__main__":
    main()
