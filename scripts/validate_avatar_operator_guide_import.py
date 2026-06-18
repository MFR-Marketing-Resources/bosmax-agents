"""
validate_avatar_operator_guide_import.py
BOSMAX Avatar Operator Guide Import Validator
14-point validation for AVATAR_OPERATOR_GUIDE_IMPORT_v1.csv

Usage:
    python scripts/validate_avatar_operator_guide_import.py
"""

import csv
import re
import sys
from pathlib import Path

# Force UTF-8 stdout so emoji status markers (✅/⚠️/❌/⛔) do not crash on
# Windows consoles defaulting to cp1252. Guarded for streams lacking reconfigure.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (ValueError, OSError):
        pass

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

CSV_PATH = Path(__file__).parent.parent / "outputs" / "notion_import" / "AVATAR_OPERATOR_GUIDE_IMPORT_v1.csv"

REQUIRED_COLUMNS_ORDERED = [
    "Avatar Context ID",
    "Display Name",
    "Persona Label",
    "Gender",
    "Age Range",
    "Product Fit",
    "Silo",
    "Scene Label",
    "Scene Summary",
    "Mannequin Label",
    "Pose Summary",
    "Wardrobe Style",
    "Best For",
    "Content Type",
    "Use Case",
    "Do",
    "Do Not",
    "Safe Usage Notes",
    "Status",
    "Source Registry",
    "Source Version",
]

FORBIDDEN_COLUMNS = [
    "prompt_fragment_source",
    "internal_notes",
    "compatible_physics_classes",
]

# Plain string fragments — exact substring match
FORBIDDEN_TEXT_FRAGMENTS_PLAIN = [
    "prompt_fragment_source",
    "internal_notes",
    "avatars/",
    "yaml::",
    "::prompt_fragment",
]

# Regex fragments — require word-boundary-aware matching.
# "MAN_" is a mannequin ID prefix (e.g. MAN_STEALTH_CLOSE_HOLD_001).
# It must NOT be preceded by a letter (to exclude persona wardrobe refs
# like AZMAN_CASUAL_01 where "MAN_" appears inside the persona name).
# "CTX_" is a scene context ID prefix — same word-boundary rule.
FORBIDDEN_TEXT_FRAGMENTS_REGEX = [
    (r"(?<![A-Za-z])MAN_[A-Z]", "MAN_<mannequin_id>"),
    (r"(?<![A-Za-z])CTX_[A-Z]", "CTX_<context_id>"),
]

EXPECTED_IDS = [
    "BOSMAX_AVP_0001",
    "BOSMAX_AVP_0002",
    "BOSMAX_AVP_0003",
    "BOSMAX_AVP_0004",
    "BOSMAX_AVP_0005",
    "BOSMAX_AVP_0006",
    "BOSMAX_AVP_0007",
    "BOSMAX_AVP_0008",
    "MWCB_DIRECT_AVP_0001",
    "MWCB_DIRECT_AVP_0002",
]

EXPECTED_TOTAL_ROWS = 10
EXPECTED_BOSMAX_ROWS = 8
EXPECTED_MWCB_ROWS = 2
EXPECTED_SOURCE_REGISTRY = "avatar_context_rotation.yaml"


# ──────────────────────────────────────────────────────────────────────────────
# VALIDATOR
# ──────────────────────────────────────────────────────────────────────────────

def run_validation():
    errors = []
    warnings = []
    passed = []

    print("=" * 70)
    print("BOSMAX Avatar Operator Guide Import Validator")
    print("=" * 70)

    # ── CHECK 1: CSV exists ──────────────────────────────────────────────────
    if not CSV_PATH.exists():
        errors.append(f"[CHECK 1] FAIL — CSV not found: {CSV_PATH}")
        print(f"\n[CHECK 1] FAIL — CSV not found: {CSV_PATH}")
        print("\n⛔ VALIDATION ABORTED — CSV missing.")
        sys.exit(1)
    passed.append("[CHECK 1] PASS — CSV exists")

    # Load CSV
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        actual_columns = list(reader.fieldnames) if reader.fieldnames else []

    # Re-read to get fieldnames reliably
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        actual_columns = reader.fieldnames or []
        rows = list(reader)

    # ── CHECK 2: exactly 10 rows ─────────────────────────────────────────────
    if len(rows) == EXPECTED_TOTAL_ROWS:
        passed.append(f"[CHECK 2] PASS — Row count = {len(rows)}")
    else:
        errors.append(f"[CHECK 2] FAIL — Expected {EXPECTED_TOTAL_ROWS} rows, got {len(rows)}")

    # ── CHECK 3: all required columns exist and are in order ─────────────────
    if list(actual_columns) == REQUIRED_COLUMNS_ORDERED:
        passed.append(f"[CHECK 3] PASS — All {len(REQUIRED_COLUMNS_ORDERED)} required columns present in correct order")
    else:
        missing = [c for c in REQUIRED_COLUMNS_ORDERED if c not in actual_columns]
        extra = [c for c in actual_columns if c not in REQUIRED_COLUMNS_ORDERED]
        wrong_order = (set(actual_columns) == set(REQUIRED_COLUMNS_ORDERED)) and (list(actual_columns) != REQUIRED_COLUMNS_ORDERED)
        if missing:
            errors.append(f"[CHECK 3] FAIL — Missing columns: {missing}")
        if extra:
            errors.append(f"[CHECK 3] FAIL — Unexpected extra columns: {extra}")
        if wrong_order:
            errors.append(f"[CHECK 3] FAIL — Columns present but not in required order")

    # ── CHECK 4: BOSMAX rows = 8 ─────────────────────────────────────────────
    bosmax_rows = [r for r in rows if r.get("Avatar Context ID", "").startswith("BOSMAX_")]
    if len(bosmax_rows) == EXPECTED_BOSMAX_ROWS:
        passed.append(f"[CHECK 4] PASS — BOSMAX rows = {len(bosmax_rows)}")
    else:
        errors.append(f"[CHECK 4] FAIL — Expected {EXPECTED_BOSMAX_ROWS} BOSMAX rows, got {len(bosmax_rows)}")

    # ── CHECK 5: MWCB rows = 2 ──────────────────────────────────────────────
    mwcb_rows = [r for r in rows if r.get("Avatar Context ID", "").startswith("MWCB_")]
    if len(mwcb_rows) == EXPECTED_MWCB_ROWS:
        passed.append(f"[CHECK 5] PASS — MWCB rows = {len(mwcb_rows)}")
    else:
        errors.append(f"[CHECK 5] FAIL — Expected {EXPECTED_MWCB_ROWS} MWCB rows, got {len(mwcb_rows)}")

    # ── CHECK 6: no forbidden columns ───────────────────────────────────────
    found_forbidden_cols = [c for c in actual_columns if c in FORBIDDEN_COLUMNS]
    if not found_forbidden_cols:
        passed.append("[CHECK 6] PASS — No forbidden columns present")
    else:
        errors.append(f"[CHECK 6] FAIL — Forbidden columns found: {found_forbidden_cols}")

    # ── CHECK 7: no forbidden text fragments ────────────────────────────────
    fragment_violations = []
    for i, row in enumerate(rows, start=2):  # row 1 = header
        for col, val in row.items():
            cell = val or ""
            # Plain substring checks
            for fragment in FORBIDDEN_TEXT_FRAGMENTS_PLAIN:
                if fragment in cell:
                    fragment_violations.append(
                        f"  Row {i} | Col '{col}' | Fragment: '{fragment}'"
                    )
            # Regex checks (word-boundary aware)
            for pattern, label in FORBIDDEN_TEXT_FRAGMENTS_REGEX:
                if re.search(pattern, cell):
                    fragment_violations.append(
                        f"  Row {i} | Col '{col}' | Fragment: '{label}'"
                    )
    if not fragment_violations:
        passed.append("[CHECK 7] PASS — No forbidden text fragments found")
    else:
        errors.append(f"[CHECK 7] FAIL — Forbidden text fragments found:\n" + "\n".join(fragment_violations))

    # ── CHECK 8: every row has Scene Summary ────────────────────────────────
    missing_scene = [r.get("Avatar Context ID", f"row_{i}") for i, r in enumerate(rows, 2) if not r.get("Scene Summary", "").strip()]
    if not missing_scene:
        passed.append("[CHECK 8] PASS — All rows have Scene Summary")
    else:
        errors.append(f"[CHECK 8] FAIL — Missing Scene Summary in rows: {missing_scene}")

    # ── CHECK 9: every row has Pose Summary ─────────────────────────────────
    missing_pose = [r.get("Avatar Context ID", f"row_{i}") for i, r in enumerate(rows, 2) if not r.get("Pose Summary", "").strip()]
    if not missing_pose:
        passed.append("[CHECK 9] PASS — All rows have Pose Summary")
    else:
        errors.append(f"[CHECK 9] FAIL — Missing Pose Summary in rows: {missing_pose}")

    # ── CHECK 10: every row has Safe Usage Notes ─────────────────────────────
    missing_notes = [r.get("Avatar Context ID", f"row_{i}") for i, r in enumerate(rows, 2) if not r.get("Safe Usage Notes", "").strip()]
    if not missing_notes:
        passed.append("[CHECK 10] PASS — All rows have Safe Usage Notes")
    else:
        errors.append(f"[CHECK 10] FAIL — Missing Safe Usage Notes in rows: {missing_notes}")

    # ── CHECK 11: every row has Status ──────────────────────────────────────
    missing_status = [r.get("Avatar Context ID", f"row_{i}") for i, r in enumerate(rows, 2) if not r.get("Status", "").strip()]
    if not missing_status:
        passed.append("[CHECK 11] PASS — All rows have Status")
    else:
        errors.append(f"[CHECK 11] FAIL — Missing Status in rows: {missing_status}")

    # ── CHECK 12: Source Registry = avatar_context_rotation.yaml ─────────────
    wrong_registry = [r.get("Avatar Context ID", f"row_{i}") for i, r in enumerate(rows, 2) if r.get("Source Registry", "") != EXPECTED_SOURCE_REGISTRY]
    if not wrong_registry:
        passed.append(f"[CHECK 12] PASS — All rows have Source Registry = '{EXPECTED_SOURCE_REGISTRY}'")
    else:
        errors.append(f"[CHECK 12] FAIL — Wrong Source Registry in rows: {wrong_registry}")

    # ── CHECK 13: no duplicate Avatar Context ID ─────────────────────────────
    ids = [r.get("Avatar Context ID", "") for r in rows]
    duplicates = [id_ for id_ in set(ids) if ids.count(id_) > 1]
    if not duplicates:
        passed.append("[CHECK 13] PASS — No duplicate Avatar Context IDs")
    else:
        errors.append(f"[CHECK 13] FAIL — Duplicate Avatar Context IDs: {duplicates}")

    # ── CHECK 14: all expected IDs exist ─────────────────────────────────────
    missing_ids = [id_ for id_ in EXPECTED_IDS if id_ not in ids]
    if not missing_ids:
        passed.append(f"[CHECK 14] PASS — All {len(EXPECTED_IDS)} expected IDs present")
    else:
        errors.append(f"[CHECK 14] FAIL — Missing expected IDs: {missing_ids}")

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    print(f"\nCSV: {CSV_PATH}\n")
    for msg in passed:
        print(f"  ✅ {msg}")
    for msg in warnings:
        print(f"  ⚠️  {msg}")
    for msg in errors:
        print(f"  ❌ {msg}")

    print(f"\n{'─' * 70}")
    print(f"  Checks passed : {len(passed)} / 14")
    print(f"  Warnings      : {len(warnings)}")
    print(f"  Errors        : {len(errors)}")
    print(f"{'─' * 70}")

    if not errors:
        print("\n✅ VALIDATION PASSED — Avatar Operator Guide import is clean.")
        sys.exit(0)
    else:
        print(f"\n⛔ VALIDATION FAILED — {len(errors)} error(s) found. Fix before Notion import.")
        sys.exit(1)


if __name__ == "__main__":
    run_validation()
