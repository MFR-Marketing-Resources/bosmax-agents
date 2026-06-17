from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from video_template_parser import (  # type: ignore[import]
    build_canonical_template,
    load_input,
    load_schema,
    parse_block_plan,
)
from video_storyboard_builder import StoryboardError, build_storyboard  # type: ignore[import]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def expect(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def get_path(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for token in path.split("."):
        if not isinstance(current, dict) or token not in current:
            return None
        current = current[token]
    return current


def validate_schema_metadata() -> None:
    schema = load_schema()
    expect(schema.get("module_lane") == "video_template_compiler_runtime", "Schema module_lane mismatch")
    expect("required_paths" in schema and schema["required_paths"], "Schema required_paths missing")
    expect([6] in schema.get("supported_block_plans", []), "Schema missing [6] support")
    expect([8, 8] in schema.get("supported_block_plans", []), "Schema missing [8,8] support")
    expect([4, 4, 4, 4] in schema.get("unsupported_block_plans", []), "Schema missing unsupported [4,4,4,4]")
    print("PASS: schema metadata")


def validate_fixture(path: Path) -> None:
    template = build_canonical_template(load_input(path), path)
    for required_path in load_schema().get("required_paths", []):
        expect(get_path(template, required_path) is not None, f"{path.name}: required path missing: {required_path}")
    print(f"PASS: canonical parse {path.name}")


def validate_storyboard_success(path: Path) -> None:
    template = build_canonical_template(load_input(path), path)
    built = build_storyboard(template)
    block_plan = built["duration"]["block_plan"]
    block_count = built["duration"]["block_count"]
    expect(len(block_plan) == block_count, f"{path.name}: block_count does not match block_plan")
    expect(len(built["storyboard"]["block_script_json"]) == block_count, f"{path.name}: block_script count mismatch")
    print(f"PASS: storyboard build {path.name}")


def validate_key_value_and_json_support() -> None:
    raw_txt = ROOT / "tests" / "video_template_compiler" / "raw_seed_key_value.txt"
    json_fixture = ROOT / "tests" / "video_template_compiler" / "bosmax_grok_frames_single_6s.json"
    txt_template = build_canonical_template(load_input(raw_txt), raw_txt)
    json_template = build_canonical_template(load_input(json_fixture), json_fixture)
    expect(txt_template["identity"]["engine"] == "GROK", "Key:value parser failed to normalize engine")
    expect(json_template["duration"]["block_plan"] == [6], "JSON fixture block plan mismatch")
    print("PASS: text/json parser support")


def validate_unsupported_plan_fails() -> None:
    invalid_path = ROOT / "samples" / "video_template_compiler" / "unsupported_block_plan_4x4x4x4.yaml"
    template = build_canonical_template(load_input(invalid_path), invalid_path)
    plan = parse_block_plan(template["duration"]["block_plan"])
    expect(plan == [4, 4, 4, 4], "Unsupported plan fixture did not retain declared block plan")
    try:
        build_storyboard(template)
    except StoryboardError:
        print("PASS: unsupported [4,4,4,4] blocked")
        return
    fail("Unsupported [4,4,4,4] block plan should fail closed")


def main() -> None:
    validate_schema_metadata()
    validate_key_value_and_json_support()

    fixture_dir = ROOT / "samples" / "video_template_compiler"
    success_fixtures = [
        fixture_dir / "bosmax_grok_frames_single_6s.yaml",
        fixture_dir / "bosmax_flow_frames_multi_8x8.yaml",
        fixture_dir / "bosmax_hybrid_multi_8x8.yaml",
        fixture_dir / "mwtcb_product_demo_single_6s.yaml",
    ]
    for fixture in success_fixtures:
        validate_fixture(fixture)
        validate_storyboard_success(fixture)

    validate_unsupported_plan_fails()
    print("PASS: validate_video_template_schema")


if __name__ == "__main__":
    main()
