from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from video_prompt_compiler import compile_template  # type: ignore[import]
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


def validate_valid_compiles() -> None:
    fixtures = {
        "bosmax_grok_frames_single_6s.yaml": "GROK_EXTENSION_V1",
        "bosmax_flow_frames_multi_8x8.yaml": "FLOW_EXTEND_UI_V1",
        "bosmax_hybrid_multi_8x8.yaml": "VEO_CLIP_CHAIN_V1",
        "mwtcb_product_demo_single_6s.yaml": "GROK_EXTENSION_V1",
        # Google Flow 10s extend lane (FLOW_EXTEND_10S) + GROK 16s [10,6]
        "bosmax_flow_extend_10s_single_10s.yaml": "FLOW_EXTEND_UI_V1",
        "bosmax_flow_extend_18s_10_8.yaml": "FLOW_EXTEND_UI_V1",
        "bosmax_flow_extend_20s_10_10.yaml": "FLOW_EXTEND_UI_V1",
        "bosmax_grok_extend_16s_10_6.yaml": "GROK_EXTENSION_V1",
    }
    fixture_dir = ROOT / "samples" / "video_template_compiler"
    for name, adapter in fixtures.items():
        compiled = compile_fixture(fixture_dir / name)
        expect(compiled["compiler"]["engine_adapter"] == adapter, f"{name}: engine adapter mismatch")
        expect(bool(compiled["compiler"]["final_prompt_text"]), f"{name}: final_prompt_text missing")
        expect(len(compiled["compiler"]["final_prompt_blocks"]) == compiled["duration"]["block_count"], f"{name}: final_prompt_blocks count mismatch")
        expect(compiled["compiler"]["prompt_surface_status"] == "COMPILED", f"{name}: prompt surface should be COMPILED")
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


def main() -> None:
    validate_valid_compiles()
    validate_fail_fixtures()
    print("PASS: validate_video_prompt_compiler")


if __name__ == "__main__":
    main()
