from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_batch_video_prompts import export_compiled_templates  # type: ignore[import]
from video_prompt_compiler import compile_template  # type: ignore[import]
from video_storyboard_builder import build_storyboard  # type: ignore[import]
from video_template_parser import build_canonical_template, load_input  # type: ignore[import]

OUTPUT_DIR = ROOT / "outputs" / "batch_prompts"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def expect(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_compiled_fixture(path: Path) -> dict[str, Any]:
    return compile_template(build_storyboard(build_canonical_template(load_input(path), path)))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    fixture_dir = ROOT / "samples" / "video_template_compiler"
    compiled_templates = [
        load_compiled_fixture(fixture_dir / "bosmax_grok_frames_single_6s.yaml"),
        load_compiled_fixture(fixture_dir / "bosmax_flow_hybrid_multi_8x8.yaml"),
        load_compiled_fixture(fixture_dir / "bosmax_flow_frames_multi_8x8.yaml"),
        load_compiled_fixture(fixture_dir / "bosmax_flow_ingredients_multi_8x8.yaml"),
        load_compiled_fixture(fixture_dir / "bosmax_hybrid_multi_8x8.yaml"),
        load_compiled_fixture(fixture_dir / "mwtcb_product_demo_single_6s.yaml"),
    ]

    paths = export_compiled_templates(
        compiled_templates,
        output_dir=OUTPUT_DIR,
        workflow="VIDEO_TEMPLATE_COMPILER",
        stem_override="video_template_compiler_runtime_validation",
    )
    parent_rows = read_csv_rows(paths["parent_csv"])
    child_rows = read_csv_rows(paths["child_csv"])

    expect(paths["parent_csv"].exists(), "parent_csv not written")
    expect(paths["child_csv"].exists(), "child_csv not written")
    expect(paths["jsonl"].exists(), "jsonl not written")
    expect(paths["md"].exists(), "md not written")

    template_ids = [row["template_id"] for row in parent_rows]
    expect(len(template_ids) == len(set(template_ids)), "duplicate template_id detected in parent export")
    expect(all(row["raw_prompt_seed"] != row["final_prompt_text"] for row in parent_rows), "raw seed and final prompt text must remain separate")
    expect(all(row["qa_status"] for row in parent_rows), "parent rows missing qa_status")
    expect(all(row["notion_ready"] in {"True", "False"} for row in parent_rows), "parent rows missing notion_ready boolean")
    expect(all(row["output_mode"] in {"SINGLE_PROMPT", "MULTI_PROMPT_SET"} for row in parent_rows), "parent rows missing output_mode")
    expect(all(int(row["prompt_set_count"]) >= 1 for row in parent_rows), "parent rows missing prompt_set_count")
    for row in parent_rows:
        block_count = int(row["block_count"])
        prompt_set_count = int(row["prompt_set_count"])
        expect(prompt_set_count == block_count, f"parent row prompt_set_count mismatch for {row['template_id']}")
        if block_count > 1:
            expect("MULTI-PROMPT SET" in row["final_prompt_text"], f"multi-block parent row missing MULTI-PROMPT SET label for {row['template_id']}")
            if row["engine"] == "GOOGLE_FLOW":
                expect("[10,6]" not in row["final_prompt_text"], f"Google Flow export must not leak GROK [10,6] split for {row['template_id']}")

    child_ids = [row["child_row_id"] for row in child_rows]
    expect(len(child_ids) == len(set(child_ids)), "duplicate child_row_id detected")
    parent_map = {row["template_id"]: row for row in parent_rows}
    for row in child_rows:
        expect(row["parent_template_id"] in parent_map, f"child row missing parent linkage: {row}")
        expect(bool(row["final_prompt_block_text"]), f"child row missing final prompt text: {row}")
        expect(row["dialogue_budget_status"] in {"PASS", "WARN", "FAIL"}, f"child row missing dialogue_budget_status: {row}")
        expect(bool(row["set_role"]), f"child row missing set_role: {row}")
        parent = parent_map[row["parent_template_id"]]
        if parent["engine"] == "GOOGLE_FLOW" and row["block_id"].endswith("02"):
            expect("Previous clip final second state:" in row["final_prompt_block_text"], f"Google Flow continuation export missing previous clip final state: {row['block_id']}")

    expected_child_count = sum(template["duration"]["block_count"] for template in compiled_templates)
    expect(len(child_rows) == expected_child_count, "child row count does not match compiled block count")
    print("PASS: validate_video_template_export_readiness")


if __name__ == "__main__":
    main()
