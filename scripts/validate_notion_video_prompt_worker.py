from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from notion_video_prompt_worker import (  # noqa: E402
    FRAMES_OPERATOR_DATA_SOURCE_ID,
    HYBRID_OPERATOR_DATA_SOURCE_ID,
    INGREDIENTS_OPERATOR_DATA_SOURCE_ID,
    WORKER_CONTRACT_VERSION,
    _normalize_page_id,
    _resolve_writeback_field_map,
    compile_snapshot,
    validate_snapshot,
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_contains(text: str, needle: str, message: str) -> None:
    require(needle in text, message)


def load_snapshot(name: str) -> dict:
    path = ROOT / "tests" / "video_template_compiler" / f"notion_worker_snapshot_{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def assert_schema_exclusivity(snapshot: dict, *, required: set[str], forbidden: set[str], expected_ds: str) -> None:
    available = set(snapshot["run"]["available_fields"])
    for field_name in required:
        require(field_name in available, f"{snapshot['run']['mode']} missing required operator field: {field_name}")
    for field_name in forbidden:
        require(field_name not in available, f"{snapshot['run']['mode']} leaked foreign-mode field: {field_name}")
    require(
        snapshot["run"]["data_source_id"] == expected_ds,
        f"{snapshot['run']['mode']} data source drifted.",
    )


def assert_fail_closed(snapshot: dict, expected_error_fragment: str) -> None:
    errors, _warnings = validate_snapshot(snapshot)
    require(errors, f"Expected fail-closed validation error containing {expected_error_fragment!r}")
    error_blob = " | ".join(errors)
    require(
        expected_error_fragment in error_blob,
        f"Expected error fragment {expected_error_fragment!r}, got {error_blob!r}",
    )
    try:
        compile_snapshot(snapshot)
    except Exception as exc:  # noqa: BLE001
        require(
            expected_error_fragment in str(exc),
            f"Expected compile failure containing {expected_error_fragment!r}, got {exc!r}",
        )
        return
    fail(f"compile_snapshot unexpectedly passed for missing asset case: {expected_error_fragment!r}")


def assert_docs() -> None:
    docs = {
        "tests/video_template_compiler/README.md": (
            "backend database export is invalid for operators",
            "Compiler Payload / RAW Prompt",
            "Output From Compiler",
            "BOSMAX HYBRID Operator Intake",
            "BOSMAX FRAMES Operator Intake",
            "BOSMAX INGREDIENTS Operator Intake",
        ),
        "tests/video_template_compiler/notion_worker_test_report.md": (
            "Exporting backend Notion pages is not an operator workflow.",
            "Exporting `Compiler Payload / RAW Prompt` and `Output From Compiler` is the correct operator workflow.",
        ),
        "docs/video_template_compiler_runtime.md": (
            "BOSMAX Video Prompt Requests",
            "BOSMAX_VIDEO_PROMPT_RUNS",
            "BACKEND / ADMIN ONLY / DO NOT USE AS OPERATOR UI",
            "The only operator-facing databases are:",
        ),
        "README.md": (
            "Mode-specific Notion operator intake is the only approved UI for the video prompt worker.",
            "Do not use backend databases/pages as operator UI or export source.",
        ),
    }
    for relative_path, needles in docs.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            require_contains(text, needle, f"{relative_path} lost required worker governance text: {needle!r}")


def main() -> None:
    hybrid = load_snapshot("bosmax")
    frames = load_snapshot("frames")
    ingredients = load_snapshot("ingredients")

    assert_schema_exclusivity(
        hybrid,
        required={
            "Product Photo Upload",
            "Avatar Source",
            "Avatar Ai",
            "Scene Context",
            "Compiler Payload / RAW Prompt",
            "Output From Compiler",
            "QA Notes",
            "Request Status",
        },
        forbidden={
            "Completed Frame Upload",
            "Motion Delta",
            "Frame Context",
            "Product Reference Photo",
            "Avatar Reference Photo",
            "Style Scene Reference Photo",
            "Asset Role Map",
            "style_scene_source",
        },
        expected_ds=HYBRID_OPERATOR_DATA_SOURCE_ID,
    )
    assert_schema_exclusivity(
        frames,
        required={
            "Completed Frame Upload",
            "Motion Delta",
            "Frame Context",
            "Compiler Payload / RAW Prompt",
            "Output From Compiler",
            "QA Notes",
            "Request Status",
        },
        forbidden={
            "Product Photo Upload",
            "Avatar Source",
            "Avatar Ai",
            "Product Reference Photo",
            "Avatar Reference Photo",
            "Style Scene Reference Photo",
            "Asset Role Map",
            "style_scene_source",
            "Scene Context",
        },
        expected_ds=FRAMES_OPERATOR_DATA_SOURCE_ID,
    )
    assert_schema_exclusivity(
        ingredients,
        required={
            "Product Reference Photo",
            "Avatar Reference Photo",
            "Style Scene Reference Photo",
            "Asset Role Map",
            "style_scene_source",
            "Scene Context",
            "Compiler Payload / RAW Prompt",
            "Output From Compiler",
            "QA Notes",
            "Request Status",
        },
        forbidden={
            "Product Photo Upload",
            "Avatar Source",
            "Avatar Ai",
            "Completed Frame Upload",
            "Motion Delta",
            "Frame Context",
        },
        expected_ds=INGREDIENTS_OPERATOR_DATA_SOURCE_ID,
    )

    samples = [
        {
            "name": "HYBRID",
            "snapshot": hybrid,
            "expected_intake_mode": "PRODUCT_ONLY",
            "required_raw_snippets": [
                "product_truth_ref: products/BOSMAX_SERUM.yaml",
                "target_language: Malay",
                "scene_context:",
            ],
            "forbidden_raw_snippets": [
                "ready_frame_input:",
                "asset_role_map:",
            ],
        },
        {
            "name": "FRAMES",
            "snapshot": frames,
            "expected_intake_mode": "READY_FRAME",
            "required_raw_snippets": [
                "ready_frame_input:",
                "frame_truth_lock:",
                "completed_frame_assets:",
            ],
            "forbidden_raw_snippets": [
                "asset_role_map:",
                "style_scene_reference_assets:",
            ],
        },
        {
            "name": "INGREDIENTS",
            "snapshot": ingredients,
            "expected_intake_mode": "ASSET_SET",
            "required_raw_snippets": [
                "asset_role_map:",
                "avatar_reference_assets:",
                "style_scene_reference_assets:",
                "style_scene_limit:",
            ],
            "forbidden_raw_snippets": [
                "ready_frame_input:",
            ],
        },
    ]

    for sample in samples:
        result = compile_snapshot(sample["snapshot"])
        payload = result["worker_payload"]
        compiled = result["compiled_template"]
        compiler = compiled["compiler"]
        qa = compiled["qa"]
        raw_prompt = result["raw_prompt_compiled"]
        final_output = result["final_output_9_section"]

        require(result["contract_version"] == WORKER_CONTRACT_VERSION, "Worker contract version drifted.")
        require(payload["mode"] == sample["name"], f"{sample['name']} payload mode drifted.")
        require(payload["intake_mode"] == sample["expected_intake_mode"], f"{sample['name']} intake mode drifted.")
        require(payload["engine"] == "GROK", f"{sample['name']} engine rule did not normalize to GROK.")
        require(payload["duration"] == "16s", f"{sample['name']} duration drifted.")
        require(bool(payload["product_truth_ref"]), f"{sample['name']} lost product_truth_ref.")
        require(bool(payload["hook"]), f"{sample['name']} lost hook.")
        require(bool(payload["body"]), f"{sample['name']} lost body.")
        require(bool(payload["cta"]), f"{sample['name']} lost CTA.")
        require(compiler["output_mode"] == "MULTI_PROMPT_SET", f"{sample['name']} must compile to MULTI_PROMPT_SET.")
        require(int(compiler["prompt_set_count"]) == 2, f"{sample['name']} GROK 16s sample must compile to two prompt sets.")
        require(not qa["qa_errors"], f"{sample['name']} introduced hard QA errors: {qa['qa_errors']!r}")
        require(bool(qa["notion_ready"]), f"{sample['name']} compiled sample is not notion_ready.")

        for snippet in sample["required_raw_snippets"]:
            require_contains(raw_prompt, snippet, f"{sample['name']} raw prompt lost required snippet: {snippet!r}")
        for snippet in sample["forbidden_raw_snippets"]:
            require(snippet not in raw_prompt, f"{sample['name']} raw prompt leaked wrong-mode snippet: {snippet!r}")

        require_contains(final_output, "MULTI-PROMPT SET", f"{sample['name']} final output lost MULTI-PROMPT SET.")
        require_contains(final_output, "SECTION 9 - NO_OVERLAY", f"{sample['name']} final output lost NO_OVERLAY.")

        print(f"sample ok: {sample['name']}")
        print(f"intake_mode ok: {payload['intake_mode']}")
        print(f"output_mode ok: {compiler['output_mode']}")

    missing_hybrid_asset = copy.deepcopy(hybrid)
    missing_hybrid_asset["run"]["product_photo_uploads"] = []
    assert_fail_closed(missing_hybrid_asset, "HYBRID intake requires Product Photo Upload.")

    missing_frame_asset = copy.deepcopy(frames)
    missing_frame_asset["run"]["completed_frame_uploads"] = []
    assert_fail_closed(missing_frame_asset, "FRAMES intake requires Completed Frame Upload.")

    missing_ingredient_asset = copy.deepcopy(ingredients)
    missing_ingredient_asset["run"]["asset_role_map_relation_ids"] = []
    missing_ingredient_asset["asset_role_map"] = {}
    assert_fail_closed(missing_ingredient_asset, "INGREDIENTS intake requires exactly one Asset Role Map relation.")

    missing_style_scene = copy.deepcopy(ingredients)
    missing_style_scene["run"]["style_scene_reference_photos"] = []
    assert_fail_closed(
        missing_style_scene,
        "INGREDIENTS intake requires Style Scene Reference Photo for the selected Asset Role Map.",
    )

    alias_field_map = _resolve_writeback_field_map(
        {
            "Compiler Payload / RAW Prompt",
            "Output From Compiler",
            "QA Notes",
            "Request Status",
        }
    )
    require(
        alias_field_map == {
            "raw_prompt_field": "Compiler Payload / RAW Prompt",
            "final_output_field": "Output From Compiler",
            "qa_notes_field": "QA Notes",
            "request_status_field": "Request Status",
        },
        "Alias field resolution drifted for the operator-facing property names.",
    )
    require(
        _normalize_page_id("https://app.notion.com/p/3854775af48a81c896ecf999a53e5f5c")
        == "3854775a-f48a-81c8-96ec-f999a53e5f5c",
        "Row URL parsing drifted.",
    )

    assert_docs()

    print("worker_contract ok:", WORKER_CONTRACT_VERSION)
    print("alias_writeback ok")
    print("row_url_parse ok")
    print("docs_governance ok")
    print("VALIDATION PASSED")


if __name__ == "__main__":
    main()
