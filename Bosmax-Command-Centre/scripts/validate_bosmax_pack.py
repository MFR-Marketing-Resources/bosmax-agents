from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import openpyxl
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_PACK = PROJECT_ROOT / "knowledge-pack"

EXPECTED_FILES = {
    "Bosmax Custom Instruction.txt": KNOWLEDGE_PACK / "custom-instruction" / "Bosmax Custom Instruction.txt",
    "AVATAR_POOL_NORMALIZED.csv": KNOWLEDGE_PACK / "avatars" / "AVATAR_POOL_NORMALIZED.csv",
    "UNIVERSAL_PRODUCT_SCHEMA.json": KNOWLEDGE_PACK / "schemas" / "UNIVERSAL_PRODUCT_SCHEMA.json",
    "VIDEO_PROMPT_COMPILER_TEMPLATES.yaml": KNOWLEDGE_PACK / "templates" / "VIDEO_PROMPT_COMPILER_TEMPLATES.yaml",
    "COPYWRITING_FRAMEWORK_UNIVERSAL.yaml": KNOWLEDGE_PACK / "templates" / "COPYWRITING_FRAMEWORK_UNIVERSAL.yaml",
    "COPYWRITING_MASTER_BOSMAX.xlsx": KNOWLEDGE_PACK / "copywriting" / "COPYWRITING_MASTER_BOSMAX.xlsx",
    "COPYWRITING_MASTER_MWTCB_REPAIRED.xlsx": KNOWLEDGE_PACK / "copywriting" / "COPYWRITING_MASTER_MWTCB_REPAIRED.xlsx",
    "WPS_Blocking_Template_REPAIRED.xlsx": KNOWLEDGE_PACK / "wps" / "WPS_Blocking_Template_REPAIRED.xlsx",
    "hybrid_frames_ingredients_9_section_video_prompt_report_CORRECTED.md": KNOWLEDGE_PACK / "reports" / "hybrid_frames_ingredients_9_section_video_prompt_report_CORRECTED.md",
    "BOSMAX_FINAL_11_FILE_MANIFEST.csv": KNOWLEDGE_PACK / "manifests" / "BOSMAX_FINAL_11_FILE_MANIFEST.csv",
}

YAML_FILES = [
    "VIDEO_PROMPT_COMPILER_TEMPLATES.yaml",
    "COPYWRITING_FRAMEWORK_UNIVERSAL.yaml",
]
CSV_FILES = [
    "AVATAR_POOL_NORMALIZED.csv",
    "BOSMAX_FINAL_11_FILE_MANIFEST.csv",
]
XLSX_FILES = [
    "COPYWRITING_MASTER_BOSMAX.xlsx",
    "COPYWRITING_MASTER_MWTCB_REPAIRED.xlsx",
    "WPS_Blocking_Template_REPAIRED.xlsx",
]


def sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    errors: list[str] = []
    hashes: dict[str, str] = {}

    print(f"PROJECT_ROOT: {PROJECT_ROOT}")

    print("== FILE INVENTORY ==")
    for name, path in EXPECTED_FILES.items():
        if not path.exists():
            errors.append(f"MISSING: {name} -> {path}")
            print(f"MISSING: {name} -> {path}")
            continue
        size = path.stat().st_size
        digest = sha256_for(path)
        hashes[name] = digest
        print(f"{name} | bytes={size} | sha256={digest}")

    print("== JSON VALIDATION ==")
    json_name = "UNIVERSAL_PRODUCT_SCHEMA.json"
    if json_name in hashes:
        try:
            with EXPECTED_FILES[json_name].open("r", encoding="utf-8") as handle:
                json.load(handle)
            print(f"OK: {json_name}")
        except Exception as exc:
            errors.append(f"JSON_PARSE_FAIL: {json_name}: {exc}")
            print(f"FAIL: {json_name}: {exc}")

    print("== YAML VALIDATION ==")
    for name in YAML_FILES:
        if name not in hashes:
            continue
        try:
            with EXPECTED_FILES[name].open("r", encoding="utf-8") as handle:
                yaml.safe_load(handle)
            print(f"OK: {name}")
        except Exception as exc:
            errors.append(f"YAML_PARSE_FAIL: {name}: {exc}")
            print(f"FAIL: {name}: {exc}")

    print("== CSV VALIDATION ==")
    for name in CSV_FILES:
        if name not in hashes:
            continue
        try:
            with EXPECTED_FILES[name].open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle)
                rows = sum(1 for _ in reader)
            print(f"OK: {name} | rows={rows}")
        except Exception as exc:
            errors.append(f"CSV_PARSE_FAIL: {name}: {exc}")
            print(f"FAIL: {name}: {exc}")

    print("== XLSX VALIDATION ==")
    for name in XLSX_FILES:
        if name not in hashes:
            continue
        try:
            workbook = openpyxl.load_workbook(EXPECTED_FILES[name], read_only=True, data_only=True)
            sheets = workbook.sheetnames
            print(f"OK: {name} | sheets={', '.join(sheets)}")
            workbook.close()
        except Exception as exc:
            errors.append(f"XLSX_OPEN_FAIL: {name}: {exc}")
            print(f"FAIL: {name}: {exc}")

    print("== MANIFEST HASH CHECK ==")
    manifest_name = "BOSMAX_FINAL_11_FILE_MANIFEST.csv"
    if manifest_name in hashes:
        try:
            with EXPECTED_FILES[manifest_name].open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            for row in rows:
                file_name = row["File"]
                manifest_sha = row["SHA256"].strip().upper()
                if manifest_sha == "SELF_REFERENCE_NOT_HASHED":
                    print(f"SKIP: {file_name} | manifest marks self-reference")
                    continue
                actual_sha = hashes.get(file_name)
                if actual_sha is None:
                    message = f"HASH_COMPARE_SKIPPED_MISSING_FILE: {file_name}"
                    errors.append(message)
                    print(f"FAIL: {message}")
                    continue
                if actual_sha != manifest_sha:
                    message = (
                        f"HASH_MISMATCH: {file_name} | manifest={manifest_sha} | actual={actual_sha}"
                    )
                    errors.append(message)
                    print(f"FAIL: {message}")
                else:
                    print(f"OK: {file_name} | manifest hash matches")
        except Exception as exc:
            errors.append(f"MANIFEST_READ_FAIL: {exc}")
            print(f"FAIL: MANIFEST_READ_FAIL: {exc}")

    print("== PACKAGE COUNT NOTE ==")
    manifest_rows = 0
    if manifest_name in hashes:
        with EXPECTED_FILES[manifest_name].open("r", encoding="utf-8-sig", newline="") as handle:
            manifest_rows = sum(1 for _ in csv.DictReader(handle))
    retained_file_count = len([path for path in EXPECTED_FILES.values() if path.exists()])
    print(
        "NOTE: manifest filename says 11; manifest content rows="
        f"{manifest_rows}; current retained canonical file count={retained_file_count}"
    )

    print("== MACRO STATUS ==")
    print("NOT VERIFIED: Excel macro execution was not run.")

    if errors:
        print("== RESULT ==")
        print("FAIL")
        for error in errors:
            print(error)
        return 1

    print("== RESULT ==")
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
