"""
BOSMAX Prompt Template Readiness Validator v1.2.

Checks that all required sample files exist and contain the correct coverage
for the readiness closure layer:
  A. Video single-block (BOSMAX, MWCB, ON_THE_FLY)
  B. Video multi-block (VEO_LITE 16/24, GROK 16/20)
  C. Batch single-block (BOSMAX, MWCB, ON_THE_FLY)
  D. Batch multi-block (declares child block output shape)
  E. Field alias map (CopyPack ID -> copywriting_id)
  F. Forbidden fields absent from beginner-facing templates
  G. (CHECK 15) Duration values in templates are within engine allowed durations
  H. (CHECK 16) sum(block_plan) == total_duration for multi-block templates

Changelog v1.2:
  - CHECK 15 multi-block path: replaced raw int(block_dur) with _parse_seconds()
    so string-format durations ("8s") produce a clean fail() instead of ValueError.
  - CHECK 16 added: cross-validates sum(block_plan) against total_duration to
    catch block-plan math mismatches that CHECK 15 alone cannot detect.
  - registries/video_engine_duration_contracts.yaml: removed duplicate
    valid_block_durations_seconds key from GROK section (normalisation only,
    no functional change — duplicate value was identical).

Scope decisions recorded (not patched):
  - KLING_3_0: registry status READY but no sample templates exist.
    Decision point: add KLING_3_0 single-block templates in a dedicated future PR.
  - GOOGLE_FLOW: registry status PARTIAL_VERIFIED, no templates. Correct —
    do not add until Vertex proof lane is confirmed.

Exit code 0 = all checks passed.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]

SAMPLES_NOTION = ROOT / "samples" / "notion"
DOCS = ROOT / "docs"
REGISTRIES = ROOT / "registries"
ENGINE_REGISTRY = REGISTRIES / "video_engine_duration_contracts.yaml"

SINGLE_BLOCK_FILE = SAMPLES_NOTION / "video_single_block_templates.yaml"
MULTI_BLOCK_FILE = SAMPLES_NOTION / "video_multi_block_templates.yaml"
BATCH_SINGLE_FILE = SAMPLES_NOTION / "batch_single_block_templates.yaml"
BATCH_MULTI_FILE = SAMPLES_NOTION / "batch_multi_block_templates.yaml"
READINESS_CONTRACT = DOCS / "prompt_template_readiness_contract_v1.md"
MULTIBLOCK_CONTRACT = DOCS / "batch_multiblock_output_contract_v1.md"

FORBIDDEN_FIELDS = {"hook", "usp", "usp_1", "usp_2", "usp_3", "cta"}
FORBIDDEN_LABELS = {"hook", "usp 1", "usp 2", "usp 3", "cta", "usp"}

_failures: list[str] = []


def fail(msg: str) -> None:
    _failures.append(msg)
    print(f"FAIL: {msg}")


def check(condition: bool, msg: str) -> None:
    if condition:
        print(f"PASS: {msg}")
    else:
        fail(msg)


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _has_forbidden_fields(data: Any, context: str = "") -> bool:
    """Recursively check that forbidden fields are absent."""
    if isinstance(data, dict):
        for key in data:
            key_lower = str(key).lower().strip()
            if key_lower in FORBIDDEN_FIELDS or key_lower in FORBIDDEN_LABELS:
                fail(f"Forbidden field '{key}' found in {context}")
                return True
            if _has_forbidden_fields(data[key], context=f"{context}.{key}"):
                return True
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if _has_forbidden_fields(item, context=f"{context}[{i}]"):
                return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1 — Required sample files exist
# ─────────────────────────────────────────────────────────────────────────────

def check_files_exist() -> None:
    for path in [
        SINGLE_BLOCK_FILE,
        MULTI_BLOCK_FILE,
        BATCH_SINGLE_FILE,
        BATCH_MULTI_FILE,
        READINESS_CONTRACT,
        MULTIBLOCK_CONTRACT,
    ]:
        check(path.exists(), f"Required file exists: {path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2 — Video single-block has BOSMAX, MWCB, ON_THE_FLY
# ─────────────────────────────────────────────────────────────────────────────

def check_single_block_coverage() -> None:
    data = load_yaml(SINGLE_BLOCK_FILE)
    templates = data.get("templates") or []
    workflows = {str(t.get("product_workflow", "")).upper() for t in templates}
    check("BOSMAX_SERUM_STEALTH" in workflows,
          "video_single_block has BOSMAX_SERUM_STEALTH template")
    check("MWCB_DIRECT" in workflows,
          "video_single_block has MWCB_DIRECT template")
    check("ON_THE_FLY_SESSION_ONLY" in workflows,
          "video_single_block has ON_THE_FLY_SESSION_ONLY template")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3 — Video multi-block has VEO_LITE 16/24 and GROK 16/20
# ─────────────────────────────────────────────────────────────────────────────

def check_multi_block_coverage() -> None:
    data = load_yaml(MULTI_BLOCK_FILE)
    templates = data.get("templates") or []

    def find(engine: str, total_s: str) -> bool:
        return any(
            str(t.get("engine", "")).upper() == engine.upper()
            and str(t.get("total_duration", "")) == total_s
            for t in templates
        )

    check(find("VEO_3_1_LITE", "16s"),
          "video_multi_block has VEO_3_1_LITE 16s template")
    check(find("VEO_3_1_LITE", "24s"),
          "video_multi_block has VEO_3_1_LITE 24s template")
    check(find("GROK", "16s"),
          "video_multi_block has GROK 16s template")
    check(find("GROK", "20s"),
          "video_multi_block has GROK 20s template")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4 — Batch single-block has BOSMAX, MWCB, ON_THE_FLY
# ─────────────────────────────────────────────────────────────────────────────

def check_batch_single_block_coverage() -> None:
    data = load_yaml(BATCH_SINGLE_FILE)
    templates = data.get("batch_templates") or []
    workflows = {str(t.get("product_workflow", "")).upper() for t in templates}
    check("BOSMAX_SERUM_STEALTH" in workflows,
          "batch_single_block has BOSMAX_SERUM_STEALTH template")
    check("MWCB_DIRECT" in workflows,
          "batch_single_block has MWCB_DIRECT template")
    check("ON_THE_FLY_SESSION_ONLY" in workflows,
          "batch_single_block has ON_THE_FLY_SESSION_ONLY template")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5 — Batch multi-block declares child block output shape
# ─────────────────────────────────────────────────────────────────────────────

def check_batch_multi_block_shape() -> None:
    data = load_yaml(BATCH_MULTI_FILE)
    status = str(data.get("implementation_status", "")).upper()
    check("CONTRACT_READY" in status or "IMPLEMENTED" in status,
          "batch_multi_block declares CONTRACT_READY or IMPLEMENTED implementation_status")

    templates = data.get("templates") or []
    check(len(templates) > 0,
          "batch_multi_block has at least one template")

    for t in templates:
        tid = t.get("template_id", "?")
        contracts = t.get("block_contracts") or []
        check(len(contracts) >= 2,
              f"batch_multi_block template {tid} has >= 2 block_contracts")

        for bc in contracts:
            bidx = bc.get("block_index", "?")
            prefix = f"batch_multi_block template {tid} block {bidx}"
            check("bridge_in_required" in bc,
                  f"{prefix} declares bridge_in_required")
            check("bridge_out_required" in bc,
                  f"{prefix} declares bridge_out_required")
            check("identity_reanchor_required" in bc,
                  f"{prefix} declares identity_reanchor_required")
            check("product_reanchor_required" in bc,
                  f"{prefix} declares product_reanchor_required")

        # Validate child row math
        batch_count = t.get("batch_count", 0)
        block_count = t.get("block_count", 0)
        exp_parent = t.get("expected_parent_rows", None)
        exp_child = t.get("expected_child_block_rows", None)
        if batch_count and block_count:
            if exp_parent is not None:
                check(int(exp_parent) == int(batch_count),
                      f"batch_multi_block template {tid} expected_parent_rows == batch_count")
            if exp_child is not None:
                check(int(exp_child) == int(batch_count) * int(block_count),
                      f"batch_multi_block template {tid} expected_child_block_rows == batch_count × block_count")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6 — Field alias map exists and includes CopyPack ID -> copywriting_id
# ─────────────────────────────────────────────────────────────────────────────

def check_field_alias_map() -> None:
    content = READINESS_CONTRACT.read_text(encoding="utf-8")
    check("CopyPack ID" in content and "copywriting_id" in content,
          "readiness contract contains CopyPack ID -> copywriting_id alias mapping")
    check("avatar_pool_id" in content,
          "readiness contract contains avatar_pool_id alias")
    check("registry_writeback" in content,
          "readiness contract declares registry_writeback field")
    check("FORBIDDEN" in content,
          "readiness contract declares registry_writeback FORBIDDEN rule")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7 — Manual Hook / USP / CTA absent from beginner-facing templates
# ─────────────────────────────────────────────────────────────────────────────

def check_no_forbidden_fields() -> None:
    for path in [SINGLE_BLOCK_FILE, BATCH_SINGLE_FILE, BATCH_MULTI_FILE]:
        data = load_yaml(path)
        had = _has_forbidden_fields(data, context=path.name)
        if not had:
            print(f"PASS: No forbidden fields (hook/USP/CTA) in {path.name}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8 — ON_THE_FLY has SESSION_ONLY_GENERATE
# ─────────────────────────────────────────────────────────────────────────────

def check_on_the_fly_session_only_generate() -> None:
    for path, key in [
        (SINGLE_BLOCK_FILE, "templates"),
        (BATCH_SINGLE_FILE, "batch_templates"),
    ]:
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            if str(t.get("product_workflow", "")).upper() == "ON_THE_FLY_SESSION_ONLY":
                check(
                    str(t.get("copywriting_mode", "")).upper() == "SESSION_ONLY_GENERATE",
                    f"{path.name}: ON_THE_FLY template has copywriting_mode=SESSION_ONLY_GENERATE",
                )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9 — ON_THE_FLY has registry_writeback: FORBIDDEN
# ─────────────────────────────────────────────────────────────────────────────

def check_on_the_fly_registry_writeback_forbidden() -> None:
    for path, key in [
        (SINGLE_BLOCK_FILE, "templates"),
        (BATCH_SINGLE_FILE, "batch_templates"),
    ]:
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            if str(t.get("product_workflow", "")).upper() == "ON_THE_FLY_SESSION_ONLY":
                check(
                    str(t.get("registry_writeback", "")).upper() == "FORBIDDEN",
                    f"{path.name}: ON_THE_FLY template has registry_writeback=FORBIDDEN",
                )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 10 — Registered products use approved workflows only
# ─────────────────────────────────────────────────────────────────────────────

APPROVED_REGISTERED_WORKFLOWS = {"BOSMAX_SERUM_STEALTH", "MWCB_DIRECT"}
APPROVED_OTF_WORKFLOWS = {"ON_THE_FLY_SESSION_ONLY"}


def check_approved_workflows() -> None:
    all_approved = APPROVED_REGISTERED_WORKFLOWS | APPROVED_OTF_WORKFLOWS
    for path, key in [
        (SINGLE_BLOCK_FILE, "templates"),
        (BATCH_SINGLE_FILE, "batch_templates"),
        (BATCH_MULTI_FILE, "templates"),
    ]:
        if not path.exists():
            continue
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            wf = str(t.get("product_workflow", "")).upper()
            if wf:
                check(
                    wf in all_approved,
                    f"{path.name}: workflow '{wf}' is in approved workflow list",
                )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 11 — MWCB uses MWCB_TRAD_REMEDY_POOL_001
# ─────────────────────────────────────────────────────────────────────────────

def check_mwcb_pool() -> None:
    for path, key in [
        (SINGLE_BLOCK_FILE, "templates"),
        (BATCH_SINGLE_FILE, "batch_templates"),
        (BATCH_MULTI_FILE, "templates"),
    ]:
        if not path.exists():
            continue
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            if str(t.get("product_workflow", "")).upper() == "MWCB_DIRECT":
                pool = str(t.get("avatar_pool_id", ""))
                check(
                    pool == "MWCB_TRAD_REMEDY_POOL_001",
                    f"{path.name}: MWCB_DIRECT template uses MWCB_TRAD_REMEDY_POOL_001 (got '{pool}')",
                )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 12 — BOSMAX uses BOSMAX_MALE_STEALTH_POOL_001
# ─────────────────────────────────────────────────────────────────────────────

def check_bosmax_pool() -> None:
    for path, key in [
        (SINGLE_BLOCK_FILE, "templates"),
        (BATCH_SINGLE_FILE, "batch_templates"),
        (BATCH_MULTI_FILE, "templates"),
    ]:
        if not path.exists():
            continue
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            if str(t.get("product_workflow", "")).upper() == "BOSMAX_SERUM_STEALTH":
                pool = str(t.get("avatar_pool_id", ""))
                check(
                    pool == "BOSMAX_MALE_STEALTH_POOL_001",
                    f"{path.name}: BOSMAX_SERUM_STEALTH template uses BOSMAX_MALE_STEALTH_POOL_001 (got '{pool}')",
                )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 13 — Multi-block examples include bridge-in/out fields
# ─────────────────────────────────────────────────────────────────────────────

def check_multi_block_bridge_fields() -> None:
    for path, key in [
        (MULTI_BLOCK_FILE, "templates"),
        (BATCH_MULTI_FILE, "templates"),
    ]:
        if not path.exists():
            continue
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            tid = t.get("template_id", "?")
            blocks = t.get("blocks") or t.get("block_contracts") or []
            for b in blocks:
                bidx = b.get("block_index", "?")
                prefix = f"{path.name} template {tid} block {bidx}"
                check("bridge_in_required" in b,
                      f"{prefix} has bridge_in_required")
                check("bridge_out_required" in b,
                      f"{prefix} has bridge_out_required")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 14 — Multi-block examples include identity/product reanchor fields
# ─────────────────────────────────────────────────────────────────────────────

def check_multi_block_reanchor_fields() -> None:
    for path, key in [
        (MULTI_BLOCK_FILE, "templates"),
        (BATCH_MULTI_FILE, "templates"),
    ]:
        if not path.exists():
            continue
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            tid = t.get("template_id", "?")
            blocks = t.get("blocks") or t.get("block_contracts") or []
            for b in blocks:
                bidx = b.get("block_index", "?")
                prefix = f"{path.name} template {tid} block {bidx}"
                check("identity_reanchor_required" in b,
                      f"{prefix} has identity_reanchor_required")
                check("product_reanchor_required" in b,
                      f"{prefix} has product_reanchor_required")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 15 — Template duration values are within engine allowed durations
# ─────────────────────────────────────────────────────────────────────────────

def _parse_seconds(value: Any) -> int | None:
    """Parse a duration value like '10s' or 10 into an integer seconds."""
    if value is None:
        return None
    s = str(value).strip().lower().rstrip("s")
    try:
        return int(s)
    except ValueError:
        return None


def _engine_allowed_durations(engine_data: dict) -> list[int]:
    """Extract top-level valid_block_durations_seconds; fall back to nested CLIP_CHAIN."""
    top_level = engine_data.get("valid_block_durations_seconds")
    if top_level:
        return [int(x) for x in top_level]
    # Fallback: try execution_modes → first mode → single_clip_durations_seconds
    modes = engine_data.get("execution_modes", {})
    for mode_data in modes.values():
        single = mode_data.get("single_clip_durations_seconds")
        if single:
            return [int(x) for x in single]
    return []


def check_template_durations_vs_engine() -> None:
    """CHECK 15: Every duration declared in single-block and multi-block templates
    must appear in the engine's valid_block_durations_seconds list."""
    if not ENGINE_REGISTRY.exists():
        fail(f"CHECK 15: engine registry not found: {ENGINE_REGISTRY.relative_to(ROOT)}")
        return

    engine_reg = load_yaml(ENGINE_REGISTRY)
    engines = engine_reg.get("engines", {})

    # Single-block templates: check `duration` field
    for path, key in [
        (SINGLE_BLOCK_FILE, "templates"),
        (BATCH_SINGLE_FILE, "batch_templates"),
    ]:
        if not path.exists():
            continue
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            tid = t.get("template_id", "?")
            engine_id = str(t.get("engine", "")).upper()
            raw_dur = t.get("duration")
            if not engine_id or raw_dur is None:
                continue
            dur_s = _parse_seconds(raw_dur)
            if dur_s is None:
                fail(f"{path.name} template {tid}: cannot parse duration '{raw_dur}'")
                continue
            engine_data = engines.get(engine_id)
            if engine_data is None:
                fail(f"{path.name} template {tid}: engine '{engine_id}' not found in registry")
                continue
            allowed = _engine_allowed_durations(engine_data)
            if not allowed:
                # Registry has no duration list for this engine — skip (not a template defect)
                print(f"SKIP: {path.name} template {tid}: no allowed durations in registry for {engine_id}")
                continue
            check(
                dur_s in allowed,
                f"{path.name} template {tid}: duration {dur_s}s in engine {engine_id} allowed list {allowed}",
            )

    # Multi-block templates: check each value in `block_plan`
    for path, key in [
        (MULTI_BLOCK_FILE, "templates"),
        (BATCH_MULTI_FILE, "templates"),
    ]:
        if not path.exists():
            continue
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            tid = t.get("template_id", "?")
            engine_id = str(t.get("engine", "")).upper()
            block_plan = t.get("block_plan") or []
            if not engine_id or not block_plan:
                continue
            engine_data = engines.get(engine_id)
            if engine_data is None:
                fail(f"{path.name} template {tid}: engine '{engine_id}' not found in registry")
                continue
            allowed = _engine_allowed_durations(engine_data)
            if not allowed:
                print(f"SKIP: {path.name} template {tid}: no allowed durations in registry for {engine_id}")
                continue
            for block_dur in block_plan:
                dur_s = _parse_seconds(block_dur)
                if dur_s is None:
                    fail(
                        f"{path.name} template {tid}: cannot parse block_plan"
                        f" duration '{block_dur}' — expected int or 'Ns' string"
                    )
                    continue
                check(
                    dur_s in allowed,
                    f"{path.name} template {tid}: block_plan duration {dur_s}s in engine {engine_id} allowed list {allowed}",
                )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 16 — sum(block_plan) == total_duration for multi-block templates
# ─────────────────────────────────────────────────────────────────────────────

def check_block_plan_sum_matches_total_duration() -> None:
    """CHECK 16: For every multi-block template, sum(block_plan) must equal
    the parsed total_duration value.  This catches math mismatches that
    CHECK 15 cannot detect (e.g. total_duration='20s' but block_plan=[8,8])."""
    for path, key in [
        (MULTI_BLOCK_FILE, "templates"),
        (BATCH_MULTI_FILE, "templates"),
    ]:
        if not path.exists():
            continue
        data = load_yaml(path)
        templates = data.get(key) or []
        for t in templates:
            tid = t.get("template_id", "?")
            total_raw = t.get("total_duration")
            block_plan = t.get("block_plan") or []
            if not block_plan or total_raw is None:
                continue
            total_s = _parse_seconds(total_raw)
            if total_s is None:
                fail(
                    f"{path.name} template {tid}: cannot parse total_duration"
                    f" '{total_raw}' — expected int or 'Ns' string"
                )
                continue
            parsed_blocks: list[int] = []
            parse_ok = True
            for b in block_plan:
                bs = _parse_seconds(b)
                if bs is None:
                    fail(
                        f"{path.name} template {tid}: cannot parse block_plan"
                        f" value '{b}' during sum check"
                    )
                    parse_ok = False
                    break
                parsed_blocks.append(bs)
            if not parse_ok:
                continue
            plan_sum = sum(parsed_blocks)
            check(
                plan_sum == total_s,
                f"{path.name} template {tid}: sum(block_plan)={plan_sum}s"
                f" == total_duration={total_s}s",
            )


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 70)
    print("BOSMAX Prompt Template Readiness Validator v1.2")
    print("=" * 70)

    print("\n[CHECK 1] Required sample files exist")
    check_files_exist()

    print("\n[CHECK 2] Video single-block workflow coverage")
    check_single_block_coverage()

    print("\n[CHECK 3] Video multi-block engine/duration coverage")
    check_multi_block_coverage()

    print("\n[CHECK 4] Batch single-block workflow coverage")
    check_batch_single_block_coverage()

    print("\n[CHECK 5] Batch multi-block child block output shape")
    check_batch_multi_block_shape()

    print("\n[CHECK 6] Field alias map (CopyPack ID -> copywriting_id)")
    check_field_alias_map()

    print("\n[CHECK 7] No forbidden fields in beginner-facing templates")
    check_no_forbidden_fields()

    print("\n[CHECK 8] ON_THE_FLY has SESSION_ONLY_GENERATE")
    check_on_the_fly_session_only_generate()

    print("\n[CHECK 9] ON_THE_FLY has registry_writeback: FORBIDDEN")
    check_on_the_fly_registry_writeback_forbidden()

    print("\n[CHECK 10] Registered products use approved workflows only")
    check_approved_workflows()

    print("\n[CHECK 11] MWCB uses MWCB_TRAD_REMEDY_POOL_001")
    check_mwcb_pool()

    print("\n[CHECK 12] BOSMAX uses BOSMAX_MALE_STEALTH_POOL_001")
    check_bosmax_pool()

    print("\n[CHECK 13] Multi-block examples include bridge-in/out fields")
    check_multi_block_bridge_fields()

    print("\n[CHECK 14] Multi-block examples include identity/product reanchor fields")
    check_multi_block_reanchor_fields()

    print("\n[CHECK 15] Template duration values within engine allowed durations")
    check_template_durations_vs_engine()

    print("\n[CHECK 16] sum(block_plan) == total_duration for multi-block templates")
    check_block_plan_sum_matches_total_duration()

    print("\n" + "=" * 70)
    if _failures:
        print(f"VALIDATION FAILED — {len(_failures)} check(s) failed:")
        for f in _failures:
            print(f"  ✗ {f}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED — all readiness checks passed")
    print("=" * 70)


if __name__ == "__main__":
    main()
