from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from notion_video_prompt_worker import (  # noqa: E402
    WORKER_CONTRACT_VERSION,
    _normalize_page_id,
    _resolve_writeback_field_map,
    compile_snapshot,
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    samples = [
        {
            "name": "HYBRID",
            "path": ROOT / "tests" / "video_template_compiler" / "notion_worker_snapshot_bosmax.json",
            "expected_intake_mode": "PRODUCT_ONLY",
            "required_raw_snippets": [
                "products/BOSMAX_SERUM.yaml",
                "Luar panas",
                "Tap tengok harga sekarang",
                "intake_mode: PRODUCT_ONLY",
            ],
            "required_final_snippets": [
                "MULTI-PROMPT SET",
                "SECTION 9 - NO_OVERLAY",
            ],
        },
        {
            "name": "FRAMES",
            "path": ROOT / "tests" / "video_template_compiler" / "notion_worker_snapshot_frames.json",
            "expected_intake_mode": "READY_FRAME",
            "required_raw_snippets": [
                "ready_frame_input:",
                "frame_truth_lock:",
                "Completed anchor frame provided.",
            ],
            "required_final_snippets": [
                "SET 1 - 10 SECONDS",
                "SET 2 - 6 SECONDS",
            ],
        },
        {
            "name": "INGREDIENTS",
            "path": ROOT / "tests" / "video_template_compiler" / "notion_worker_snapshot_ingredients.json",
            "expected_intake_mode": "ASSET_SET",
            "required_raw_snippets": [
                "asset_role_map:",
                "avatar_reference_lock:",
                "style_scene_limit:",
            ],
            "required_final_snippets": [
                "SET 1 - 10 SECONDS",
                "SET 2 - 6 SECONDS",
            ],
        },
    ]

    for sample in samples:
        snapshot = json.loads(sample["path"].read_text(encoding="utf-8"))
        result = compile_snapshot(snapshot)
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
        require(payload["product_lane"] == "BOSMAX", f"{sample['name']} product lane did not normalize to BOSMAX.")
        require(compiler["output_mode"] == "MULTI_PROMPT_SET", f"{sample['name']} must compile to MULTI_PROMPT_SET.")
        require(int(compiler["prompt_set_count"]) == 2, f"{sample['name']} GROK 16s sample must compile to two prompt sets.")
        require(not qa["qa_errors"], f"{sample['name']} introduced hard QA errors: {qa['qa_errors']!r}")
        require(bool(qa["notion_ready"]), f"{sample['name']} compiled sample is not notion_ready.")

        for snippet in sample["required_raw_snippets"]:
            require(snippet in raw_prompt, f"{sample['name']} RAW_PROMPT_COMPILED lost required snippet: {snippet!r}")
        for snippet in sample["required_final_snippets"]:
            require(snippet in final_output, f"{sample['name']} FINAL_OUTPUT_9_SECTION lost required snippet: {snippet!r}")

        print(f"sample ok: {sample['path'].name}")
        print(f"mode ok: {sample['name']}")
        print(f"intake_mode ok: {payload['intake_mode']}")
        print(f"output_mode ok: {compiler['output_mode']}")
        print(f"prompt_set_count ok: {compiler['prompt_set_count']}")
        print(f"qa_status ok: {qa['qa_status']}")

    alias_field_map = _resolve_writeback_field_map(
        {
            "Compiler Payload / RAW Prompt",
            "Final Output 9 Section",
            "QA Notes",
            "Request Status",
        }
    )
    require(
        alias_field_map == {
            "raw_prompt_field": "Compiler Payload / RAW Prompt",
            "final_output_field": "Final Output 9 Section",
            "qa_notes_field": "QA Notes",
            "request_status_field": "Request Status",
        },
        "Alias field resolution drifted for the new operator-facing property names.",
    )
    require(
        _normalize_page_id("https://app.notion.com/p/3854775af48a81c896ecf999a53e5f5c") == "3854775a-f48a-81c8-96ec-f999a53e5f5c",
        "Row URL parsing drifted.",
    )

    print("worker_contract ok:", WORKER_CONTRACT_VERSION)
    print("alias_writeback ok")
    print("row_url_parse ok")
    print("VALIDATION PASSED")


if __name__ == "__main__":
    main()
