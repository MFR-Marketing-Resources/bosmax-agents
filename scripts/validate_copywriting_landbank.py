from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = REPO_ROOT / "data" / "copywriting_landbank"
PRODUCT_DIR = BASE_DIR / "products" / "mwtcb"
SCHEMA_DIR = BASE_DIR / "schema"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_columns(rows: list[dict[str, str]], required_columns: list[str], file_label: str) -> list[str]:
    errors: list[str] = []
    if not rows:
        errors.append(f"{file_label}: no data rows found")
        return errors
    header = set(rows[0].keys())
    missing = [column for column in required_columns if column not in header]
    if missing:
        errors.append(f"{file_label}: missing required columns: {', '.join(missing)}")
    return errors


def validate_unique(rows: list[dict[str, str]], key_name: str, file_label: str) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        value = (row.get(key_name) or "").strip()
        if not value:
            errors.append(f"{file_label}:{index}: empty key field `{key_name}`")
            continue
        if value in seen:
            errors.append(f"{file_label}:{index}: duplicate key `{key_name}` = {value}")
        seen.add(value)
    return errors


def validate_non_empty(rows: list[dict[str, str]], required_columns: list[str], file_label: str) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=2):
        for column in required_columns:
            if (row.get(column) or "").strip() == "":
                errors.append(f"{file_label}:{index}: empty required field `{column}`")
    return errors


def validate_cross_refs(
    buyer_rows: list[dict[str, str]],
    class_rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    buyer_ids = {row["buyer_motivation_row_id"] for row in buyer_rows}
    buyer_keys = {row["motivation_batch_key"] for row in buyer_rows}
    for index, row in enumerate(class_rows, start=2):
        buyer_ref = (row.get("buyer_motivation_row_id") or "").strip()
        batch_key = (row.get("motivation_batch_key") or "").strip()
        if buyer_ref and buyer_ref not in buyer_ids:
            errors.append(
                f"motivation_classification.csv:{index}: unknown buyer_motivation_row_id `{buyer_ref}`"
            )
        if batch_key and batch_key not in buyer_keys:
            errors.append(
                f"motivation_classification.csv:{index}: unknown motivation_batch_key `{batch_key}`"
            )
    return errors


def validate_pandas_read(paths: list[Path], require_pandas: bool) -> tuple[list[str], str]:
    spec = importlib.util.find_spec("pandas")
    if spec is None:
        if require_pandas:
            return ["pandas is not installed; cannot satisfy --require-pandas"], "missing"
        return [], "skipped"
    import pandas as pd  # type: ignore

    errors: list[str] = []
    for path in paths:
        try:
            df = pd.read_csv(path)
            if df.empty:
                errors.append(f"{path.name}: pandas read succeeded but dataframe is empty")
        except Exception as exc:  # pragma: no cover - terminal validation path
            errors.append(f"{path.name}: pandas read failed: {exc}")
    return errors, "passed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-pandas",
        action="store_true",
        help="Fail if pandas is unavailable or cannot read the canonical CSVs.",
    )
    args = parser.parse_args()

    buyer_schema = load_yaml(SCHEMA_DIR / "buyer_motivation.schema.yaml")
    class_schema = load_yaml(SCHEMA_DIR / "motivation_classification.schema.yaml")
    angle_schema = load_yaml(SCHEMA_DIR / "angle.schema.yaml")

    buyer_csv = PRODUCT_DIR / "buyer_motivations.csv"
    class_csv = PRODUCT_DIR / "motivation_classification.csv"
    angle_csv = PRODUCT_DIR / "angle_bank.csv"

    buyer_rows = load_csv(buyer_csv)
    class_rows = load_csv(class_csv)
    
    angle_rows = []
    if angle_csv.exists():
        angle_rows = load_csv(angle_csv)

    errors: list[str] = []
    errors.extend(validate_columns(buyer_rows, buyer_schema["required_columns"], buyer_csv.name))
    errors.extend(validate_columns(class_rows, class_schema["required_columns"], class_csv.name))
    
    if angle_csv.exists():
        errors.extend(validate_columns(angle_rows, angle_schema["required_columns"], angle_csv.name))
        errors.extend(validate_unique(angle_rows, "angle_id", angle_csv.name))
        
        # Specific fields validation
        for index, row in enumerate(angle_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{angle_csv.name}:{index}: invalid product_id `{pid}` (must be `MWTCB_25ML`)")
                
            for col in ["motivation_id", "angle_name", "commercial_trigger", "visual_scene", "why_it_can_sell"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{angle_csv.name}:{index}: empty required field `{col}`")
                    
            # Check cross-ref for motivation_id
            m_id = (row.get("motivation_id") or "").strip()
            valid_motivation_ids = {r["buyer_motivation_row_id"] for r in buyer_rows}
            if m_id and m_id not in valid_motivation_ids:
                errors.append(f"{angle_csv.name}:{index}: unknown motivation_id `{m_id}`")
    else:
        errors.append(f"Missing required output file: {angle_csv.name}")

    errors.extend(validate_unique(buyer_rows, "buyer_motivation_row_id", buyer_csv.name))
    errors.extend(validate_unique(class_rows, "motivation_classification_row_id", class_csv.name))
    errors.extend(validate_non_empty(buyer_rows, buyer_schema["required_columns"], buyer_csv.name))
    errors.extend(validate_non_empty(class_rows, class_schema["required_columns"], class_csv.name))
    errors.extend(validate_cross_refs(buyer_rows, class_rows))

    csvs_to_test = [buyer_csv, class_csv]
    if angle_csv.exists():
        csvs_to_test.append(angle_csv)
        
    pandas_errors, pandas_status = validate_pandas_read(csvs_to_test, args.require_pandas)
    errors.extend(pandas_errors)

    print("Copywriting Landbank Validation Summary")
    print(f"- buyer_motivations.csv rows: {len(buyer_rows)}")
    print(f"- motivation_classification.csv rows: {len(class_rows)}")
    print(f"- angle_bank.csv rows: {len(angle_rows) if angle_csv.exists() else 0}")
    print(f"- pandas_read: {pandas_status}")
    print(f"- product_dir: {PRODUCT_DIR}")

    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
