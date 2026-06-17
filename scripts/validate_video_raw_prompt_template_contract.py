"""
BOSMAX Video Raw Prompt Template Contract Validator v1.

Validates the operator-facing raw prompt templates under
`samples/video_raw_prompt_templates/` against the contract defined in
`docs/video_raw_prompt_template_contract_v1.md`.

For each raw template this validator confirms:
  1.  All required samples exist (HYBRID / READY_FRAME / ASSET_SET, GROK 16s).
  2.  Valid engine + duration + intake_mode.
  3.  No manually authored block_plan (positive samples derive it).
  4.  Runtime derives the correct deterministic plan (e.g. GROK 16s = [10, 6]).
  5.  intake_mode aliases normalize (HYBRID/FRAMES/INGREDIENTS -> canonical).
  6.  No operator-authored final_prompt_text.
  7.  No operator-authored child block prompt text / block_script_json.
  8.  overlay_allowed defaults false.
  9.  No overlay/subtitle/on-screen-text leakage (file-level + compiler QA).
  10. A spoken dialogue intent is present (dialogue_seed or hook).
  11. Mode-appropriate truth lock present (product truth / frame truth / asset map).
  12. Each sample compiles through parser -> storyboard -> compiler with no QA
      failure (warnings are allowed; hard errors are not).
  13. Output remains sample/test only (templates live under samples/).

Exit code 0 = all checks passed.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from video_block_plan import build_plan  # type: ignore[import]
from video_prompt_compiler import OVERLAY_PATTERNS, compile_template  # type: ignore[import]
from video_storyboard_builder import build_storyboard  # type: ignore[import]
from video_template_parser import (  # type: ignore[import]
    build_canonical_template,
    load_input,
    resolve_overlay_allowed,
)

import re

SAMPLE_DIR = ROOT / "samples" / "video_raw_prompt_templates"

REQUIRED_SAMPLES = [
    "bosmax_hybrid_product_only_grok_16s.yaml",
    "bosmax_ready_frame_grok_16s.yaml",
    "bosmax_asset_set_ingredients_grok_16s.yaml",
]

VALID_ENGINES = {"GROK", "GOOGLE_FLOW", "VEO_3_1", "VEO_3_1_LITE"}
INTAKE_CANON = {
    "HYBRID": "PRODUCT_ONLY",
    "PRODUCT_ONLY": "PRODUCT_ONLY",
    "FRAMES": "READY_FRAME",
    "READY_FRAME": "READY_FRAME",
    "INGREDIENTS": "ASSET_SET",
    "ASSET_SET": "ASSET_SET",
}
FORBIDDEN_MANUAL_KEYS = {
    "final_prompt_text",
    "final_prompt_blocks",
    "final_prompt_block_text",
    "final_block_prompt_text",
    "block_script_json",
    "child_rows",
    "child_block_rows",
}

_failures: list[str] = []


def fail(msg: str) -> None:
    _failures.append(msg)
    print(f"FAIL: {msg}")


def check(cond: bool, msg: str) -> None:
    print(f"PASS: {msg}" if cond else f"FAIL: {msg}")
    if not cond:
        _failures.append(msg)


def _parse_seconds(value: Any) -> int | None:
    if value is None:
        return None
    token = str(value).strip().lower().rstrip("s")
    try:
        return int(token)
    except ValueError:
        return None


def _iter_strings(data: Any):
    if isinstance(data, str):
        yield data
    elif isinstance(data, dict):
        for value in data.values():
            yield from _iter_strings(value)
    elif isinstance(data, list):
        for item in data:
            yield from _iter_strings(item)


def _find_keys(data: Any, names: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if str(key).strip().lower() in names:
                found.append(str(key))
            found.extend(_find_keys(value, names))
    elif isinstance(data, list):
        for item in data:
            found.extend(_find_keys(item, names))
    return found


def validate_sample(path: Path) -> None:
    name = path.name
    raw = load_input(path)

    # 2. valid engine / duration / intake_mode
    engine = str(raw.get("engine", "")).strip().upper().replace("-", "_").replace(" ", "_")
    check(engine in VALID_ENGINES, f"{name}: engine '{engine}' is valid")
    dur = _parse_seconds(raw.get("duration"))
    check(dur is not None and dur > 0, f"{name}: duration parseable ({raw.get('duration')})")
    intake_raw = str(raw.get("intake_mode", raw.get("intake", ""))).strip().upper().replace("-", "_").replace(" ", "_")
    canon = INTAKE_CANON.get(intake_raw)
    check(canon is not None, f"{name}: intake_mode '{raw.get('intake_mode')}' is a valid alias")

    # 3. no manual block_plan in a positive sample
    check("block_plan" not in {str(k).lower() for k in raw}, f"{name}: no manually authored block_plan")

    # 6/7. no operator-authored final / child block text
    leaked_keys = _find_keys(raw, FORBIDDEN_MANUAL_KEYS)
    check(not leaked_keys, f"{name}: no operator-authored final/child prompt fields ({leaked_keys or 'none'})")

    # 8. overlay defaults false
    overlay_allowed = resolve_overlay_allowed(raw)
    check(overlay_allowed is False, f"{name}: overlay_allowed resolves false by default")

    # 9. no overlay leakage in raw text values
    leak_hits = []
    for text in _iter_strings(raw):
        for pattern in OVERLAY_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                leak_hits.append(pattern)
    check(not leak_hits, f"{name}: no overlay/subtitle/on-screen-text leakage in raw fields ({sorted(set(leak_hits)) or 'none'})")

    # 10. spoken dialogue intent present
    has_dialogue = bool(str(raw.get("dialogue_seed", "")).strip() or str(raw.get("hook", "")).strip())
    check(has_dialogue, f"{name}: dialogue intent present (dialogue_seed or hook)")

    # 11. mode-appropriate truth lock
    if canon == "PRODUCT_ONLY":
        ok = bool(raw.get("product_truth_ref") or raw.get("product_truth_lock"))
        check(ok, f"{name}: PRODUCT_ONLY carries product truth (product_truth_ref/lock)")
    elif canon == "READY_FRAME":
        ok = bool(raw.get("frame_truth_lock") or raw.get("ready_frame_input") or raw.get("visual_authority"))
        check(ok, f"{name}: READY_FRAME carries frame truth (frame_truth_lock/ready_frame_input)")
    elif canon == "ASSET_SET":
        ok = bool(raw.get("asset_role_map"))
        check(ok, f"{name}: ASSET_SET carries asset_role_map")

    # 12. compiles through parser -> storyboard -> compiler with no hard QA error
    try:
        compiled = compile_template(build_storyboard(build_canonical_template(raw, path)))
    except Exception as exc:  # noqa: BLE001 - surface any pipeline failure as a contract failure
        fail(f"{name}: pipeline raised {type(exc).__name__}: {exc}")
        return

    qa_errors = compiled["qa"]["qa_errors"]
    check(not qa_errors, f"{name}: compiles with no QA error (status {compiled['qa']['qa_status']})")
    check(
        compiled["compiler"]["prompt_surface_status"] == "COMPILED",
        f"{name}: prompt surface COMPILED",
    )

    # 4. runtime derives the correct deterministic plan
    derived = [int(x) for x in compiled["duration"]["block_plan"]]
    expected = [int(x) for x in build_plan(engine, dur)["block_durations_seconds"]] if dur else []
    check(derived == expected, f"{name}: runtime-derived plan {derived} matches deterministic {expected}")
    if engine == "GROK" and dur == 16:
        check(derived == [10, 6], f"{name}: GROK 16s derives [10,6]")
    if dur is not None:
        check(sum(derived) == dur, f"{name}: sum(block_plan) {sum(derived)} == duration {dur}")

    # 5. intake alias normalized in canonical record
    check(
        compiled["identity"]["intake_mode"] == canon,
        f"{name}: intake_mode normalized to {canon} (got {compiled['identity']['intake_mode']})",
    )

    # 13. sample/test only
    check("samples" in path.parts, f"{name}: lives under samples/ (sample/test only)")


def main() -> None:
    print("=" * 70)
    print("BOSMAX Video Raw Prompt Template Contract Validator v1")
    print("=" * 70)

    check(SAMPLE_DIR.exists(), f"sample dir exists: {SAMPLE_DIR.relative_to(ROOT)}")

    print("\n[CHECK] Required samples exist")
    for req in REQUIRED_SAMPLES:
        check((SAMPLE_DIR / req).exists(), f"required sample exists: {req}")

    samples = sorted(SAMPLE_DIR.glob("*.yaml")) if SAMPLE_DIR.exists() else []
    print(f"\n[CHECK] Validating {len(samples)} raw prompt template(s)")
    for path in samples:
        print(f"\n--- {path.name} ---")
        validate_sample(path)

    print("\n" + "=" * 70)
    if _failures:
        print(f"VALIDATION FAILED — {len(_failures)} check(s) failed:")
        for item in _failures:
            print(f"  x {item}")
        sys.exit(1)
    print("VALIDATION PASSED — all raw prompt template contract checks passed")
    print("=" * 70)


if __name__ == "__main__":
    main()
