from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from notion_video_prompt_worker import WORKER_CONTRACT_VERSION, compile_snapshot  # noqa: E402


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    snapshot_path = ROOT / "tests" / "video_template_compiler" / "notion_worker_snapshot_bosmax.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    result = compile_snapshot(snapshot)

    payload = result["worker_payload"]
    compiled = result["compiled_template"]
    compiler = compiled["compiler"]
    qa = compiled["qa"]
    raw_prompt = result["raw_prompt_compiled"]
    final_output = result["final_output_9_section"]

    require(result["contract_version"] == WORKER_CONTRACT_VERSION, "Worker contract version drifted.")
    require(payload["mode"] == "HYBRID", "Sample payload mode must stay HYBRID.")
    require(payload["intake_mode"] == "PRODUCT_ONLY", "HYBRID must normalize to PRODUCT_ONLY.")
    require(payload["engine"] == "GROK", "Engine rule did not normalize to GROK.")
    require(payload["product_lane"] == "BOSMAX", "Product lane did not normalize to BOSMAX.")
    require("products/BOSMAX_SERUM.yaml" in raw_prompt, "RAW_PROMPT_COMPILED lost product truth reference.")
    require("Luar panas" in raw_prompt, "RAW_PROMPT_COMPILED lost the selected hook.")
    require("Tap tengok harga sekarang" in raw_prompt, "RAW_PROMPT_COMPILED lost CTA.")
    require(compiler["output_mode"] == "MULTI_PROMPT_SET", "GROK 16s sample must compile to MULTI_PROMPT_SET.")
    require(int(compiler["prompt_set_count"]) == 2, "GROK 16s sample must compile to two prompt sets.")
    require("MULTI-PROMPT SET" in final_output, "FINAL_OUTPUT_9_SECTION must declare MULTI-PROMPT SET.")
    require("SECTION 9 - NO_OVERLAY" in final_output, "FINAL_OUTPUT_9_SECTION lost Section 9 NO_OVERLAY.")
    require(not qa["qa_errors"], f"Worker introduced hard QA errors: {qa['qa_errors']!r}")
    require(bool(qa["notion_ready"]), "Compiled sample is not notion_ready.")

    print("VALIDATION PASSED")
    print(f"worker_contract ok: {WORKER_CONTRACT_VERSION}")
    print(f"sample_snapshot ok: {snapshot_path.name}")
    print(f"output_mode ok: {compiler['output_mode']}")
    print(f"prompt_set_count ok: {compiler['prompt_set_count']}")
    print(f"qa_status ok: {qa['qa_status']}")


if __name__ == "__main__":
    main()
