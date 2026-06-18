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
    hook_schema = load_yaml(SCHEMA_DIR / "hook.schema.yaml")
    subhook_schema = load_yaml(SCHEMA_DIR / "subhook.schema.yaml")
    usp_schema = load_yaml(SCHEMA_DIR / "usp.schema.yaml")
    cta_schema = load_yaml(SCHEMA_DIR / "cta.schema.yaml")
    video_matrix_schema = load_yaml(SCHEMA_DIR / "video_copy_matrix.schema.yaml")
    poster_matrix_schema = load_yaml(SCHEMA_DIR / "poster_copy_matrix.schema.yaml")
    notion_rows_schema = load_yaml(SCHEMA_DIR / "notion_production_rows.schema.yaml")
    video_pack_schema = load_yaml(SCHEMA_DIR / "video_prompt_pack.schema.yaml")
    poster_pack_schema = load_yaml(SCHEMA_DIR / "poster_prompt_pack.schema.yaml")

    buyer_csv = PRODUCT_DIR / "buyer_motivations.csv"
    class_csv = PRODUCT_DIR / "motivation_classification.csv"
    angle_csv = PRODUCT_DIR / "angle_bank.csv"
    hook_csv = PRODUCT_DIR / "hook_bank.csv"
    subhook_csv = PRODUCT_DIR / "subhook_bank.csv"
    usp_csv = PRODUCT_DIR / "usp_bank.csv"
    cta_csv = PRODUCT_DIR / "cta_bank.csv"
    video_matrix_csv = PRODUCT_DIR / "video_copy_matrix.csv"
    poster_matrix_csv = PRODUCT_DIR / "poster_copy_matrix.csv"
    notion_rows_csv = PRODUCT_DIR / "notion_production_rows.csv"
    video_pack_csv = PRODUCT_DIR / "video_prompt_pack.csv"
    poster_pack_csv = PRODUCT_DIR / "poster_prompt_pack.csv"

    buyer_rows = load_csv(buyer_csv)
    class_rows = load_csv(class_csv)
    
    angle_rows = []
    if angle_csv.exists():
        angle_rows = load_csv(angle_csv)

    hook_rows = []
    if hook_csv.exists():
        hook_rows = load_csv(hook_csv)

    subhook_rows = []
    if subhook_csv.exists():
        subhook_rows = load_csv(subhook_csv)

    usp_rows = []
    if usp_csv.exists():
        usp_rows = load_csv(usp_csv)

    cta_rows = []
    if cta_csv.exists():
        cta_rows = load_csv(cta_csv)

    video_matrix_rows = []
    if video_matrix_csv.exists():
        video_matrix_rows = load_csv(video_matrix_csv)

    poster_matrix_rows = []
    if poster_matrix_csv.exists():
        poster_matrix_rows = load_csv(poster_matrix_csv)

    notion_rows_rows = []
    if notion_rows_csv.exists():
        notion_rows_rows = load_csv(notion_rows_csv)

    video_pack_rows = []
    if video_pack_csv.exists():
        video_pack_rows = load_csv(video_pack_csv)

    poster_pack_rows = []
    if poster_pack_csv.exists():
        poster_pack_rows = load_csv(poster_pack_csv)

    errors: list[str] = []
    errors.extend(validate_columns(buyer_rows, buyer_schema["required_columns"], buyer_csv.name))
    errors.extend(validate_columns(class_rows, class_schema["required_columns"], class_csv.name))
    
    valid_motivation_ids = {r["buyer_motivation_row_id"] for r in buyer_rows}
    valid_angle_ids = set()

    if angle_csv.exists():
        errors.extend(validate_columns(angle_rows, angle_schema["required_columns"], angle_csv.name))
        errors.extend(validate_unique(angle_rows, "angle_id", angle_csv.name))
        valid_angle_ids = {r["angle_id"] for r in angle_rows}
        
        # Specific fields validation
        for index, row in enumerate(angle_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{angle_csv.name}:{index}: invalid product_id `{pid}` (must be `MWTCB_25ML`)")
                
            for col in ["motivation_id", "angle_name", "commercial_trigger", "visual_scene", "why_it_can_sell"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{angle_csv.name}:{index}: empty required field `{col}`")
                    
            m_id = (row.get("motivation_id") or "").strip()
            if m_id and m_id not in valid_motivation_ids:
                errors.append(f"{angle_csv.name}:{index}: unknown motivation_id `{m_id}`")
    else:
        errors.append(f"Missing required output file: {angle_csv.name}")

    # Hook validation
    if hook_csv.exists():
        errors.extend(validate_columns(hook_rows, hook_schema["required_columns"], hook_csv.name))
        errors.extend(validate_unique(hook_rows, "hook_id", hook_csv.name))
        valid_hook_ids = {r["hook_id"] for r in hook_rows}
        
        for index, row in enumerate(hook_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{hook_csv.name}:{index}: invalid product_id `{pid}`")
            
            # Non-empty checks
            for col in ["hook_text", "boldness_level", "angle_id", "motivation_id"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{hook_csv.name}:{index}: empty required field `{col}`")
            
            # Cross-ref checks
            a_id = (row.get("angle_id") or "").strip()
            m_id = (row.get("motivation_id") or "").strip()
            if a_id and a_id not in valid_angle_ids:
                errors.append(f"{hook_csv.name}:{index}: unknown angle_id `{a_id}`")
            if m_id and m_id not in valid_motivation_ids:
                errors.append(f"{hook_csv.name}:{index}: unknown motivation_id `{m_id}`")
    else:
        errors.append(f"Missing hook file: {hook_csv.name}")

    # Subhook validation
    if subhook_csv.exists():
        errors.extend(validate_columns(subhook_rows, subhook_schema["required_columns"], subhook_csv.name))
        errors.extend(validate_unique(subhook_rows, "subhook_id", subhook_csv.name))
        
        for index, row in enumerate(subhook_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{subhook_csv.name}:{index}: invalid product_id `{pid}`")
            
            # Non-empty checks
            for col in ["subhook_text", "boldness_level", "hook_id", "angle_id", "motivation_id"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{subhook_csv.name}:{index}: empty required field `{col}`")
            
            # Cross-ref checks
            h_id = (row.get("hook_id") or "").strip()
            a_id = (row.get("angle_id") or "").strip()
            m_id = (row.get("motivation_id") or "").strip()
            if hook_csv.exists() and h_id and h_id not in valid_hook_ids:
                errors.append(f"{subhook_csv.name}:{index}: unknown hook_id `{h_id}`")
            if a_id and a_id not in valid_angle_ids:
                errors.append(f"{subhook_csv.name}:{index}: unknown angle_id `{a_id}`")
            if m_id and m_id not in valid_motivation_ids:
                errors.append(f"{subhook_csv.name}:{index}: unknown motivation_id `{m_id}`")
    else:
        errors.append(f"Missing subhook file: {subhook_csv.name}")

    # USP validation
    if usp_csv.exists():
        errors.extend(validate_columns(usp_rows, usp_schema["required_columns"], usp_csv.name))
        errors.extend(validate_unique(usp_rows, "usp_id", usp_csv.name))
        
        for index, row in enumerate(usp_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{usp_csv.name}:{index}: invalid product_id `{pid}`")
            
            # Non-empty checks
            for col in ["usp_text", "proof_type", "angle_id", "motivation_id"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{usp_csv.name}:{index}: empty required field `{col}`")
            
            # Cross-ref checks
            a_id = (row.get("angle_id") or "").strip()
            m_id = (row.get("motivation_id") or "").strip()
            if a_id and a_id not in valid_angle_ids:
                errors.append(f"{usp_csv.name}:{index}: unknown angle_id `{a_id}`")
            if m_id and m_id not in valid_motivation_ids:
                errors.append(f"{usp_csv.name}:{index}: unknown motivation_id `{m_id}`")
    else:
        errors.append(f"Missing USP file: {usp_csv.name}")

    # CTA validation
    if cta_csv.exists():
        errors.extend(validate_columns(cta_rows, cta_schema["required_columns"], cta_csv.name))
        errors.extend(validate_unique(cta_rows, "cta_id", cta_csv.name))
        
        for index, row in enumerate(cta_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{cta_csv.name}:{index}: invalid product_id `{pid}`")
            
            # Non-empty checks
            for col in ["cta_text", "boldness_level", "angle_id", "motivation_id"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{cta_csv.name}:{index}: empty required field `{col}`")
            
            # Cross-ref checks
            a_id = (row.get("angle_id") or "").strip()
            m_id = (row.get("motivation_id") or "").strip()
            if a_id and a_id not in valid_angle_ids:
                errors.append(f"{cta_csv.name}:{index}: unknown angle_id `{a_id}`")
            if m_id and m_id not in valid_motivation_ids:
                errors.append(f"{cta_csv.name}:{index}: unknown motivation_id `{m_id}`")
    else:
        errors.append(f"Missing CTA file: {cta_csv.name}")

    # Video Matrix validation
    if video_matrix_csv.exists():
        errors.extend(validate_columns(video_matrix_rows, video_matrix_schema["required_columns"], video_matrix_csv.name))
        errors.extend(validate_unique(video_matrix_rows, "video_matrix_id", video_matrix_csv.name))
        
        valid_mot_ids = {r["buyer_motivation_row_id"] for r in buyer_rows}
        valid_ang_ids = {r["angle_id"] for r in angle_rows} if angle_csv.exists() else set()
        valid_hk_ids = {r["hook_id"] for r in hook_rows} if hook_csv.exists() else set()
        valid_shk_ids = {r["subhook_id"] for r in subhook_rows} if subhook_csv.exists() else set()
        valid_u_ids = {r["usp_id"] for r in usp_rows} if usp_csv.exists() else set()
        valid_c_ids = {r["cta_id"] for r in cta_rows} if cta_csv.exists() else set()

        for index, row in enumerate(video_matrix_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{video_matrix_csv.name}:{index}: invalid product_id `{pid}`")
            
            # Non-empty checks
            for col in video_matrix_schema["required_columns"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{video_matrix_csv.name}:{index}: empty required field `{col}`")
            
            # Cross-ref checks
            mot = (row.get("motivation_id") or "").strip()
            ang = (row.get("angle_id") or "").strip()
            hk = (row.get("hook_id") or "").strip()
            shk = (row.get("subhook_id") or "").strip()
            u = (row.get("usp_id") or "").strip()
            c = (row.get("cta_id") or "").strip()
            
            if mot and mot not in valid_mot_ids:
                errors.append(f"{video_matrix_csv.name}:{index}: unknown motivation_id `{mot}`")
            if ang and ang not in valid_ang_ids:
                errors.append(f"{video_matrix_csv.name}:{index}: unknown angle_id `{ang}`")
            if hk and hk not in valid_hk_ids:
                errors.append(f"{video_matrix_csv.name}:{index}: unknown hook_id `{hk}`")
            if shk and shk not in valid_shk_ids:
                errors.append(f"{video_matrix_csv.name}:{index}: unknown subhook_id `{shk}`")
            if u and u not in valid_u_ids:
                errors.append(f"{video_matrix_csv.name}:{index}: unknown usp_id `{u}`")
            if c and c not in valid_c_ids:
                errors.append(f"{video_matrix_csv.name}:{index}: unknown cta_id `{c}`")
                
            # Tolerance and review
            tol = (row.get("raw_claim_tolerance") or "").strip()
            rev = (row.get("production_review_required") or "").strip()
            if tol not in ["LOW", "MEDIUM", "HIGH"]:
                errors.append(f"{video_matrix_csv.name}:{index}: invalid raw_claim_tolerance `{tol}`")
            if rev not in ["YES", "NO"]:
                errors.append(f"{video_matrix_csv.name}:{index}: invalid production_review_required `{rev}`")
    else:
        errors.append(f"Missing required output file: {video_matrix_csv.name}")

    # Poster Matrix validation
    if poster_matrix_csv.exists():
        errors.extend(validate_columns(poster_matrix_rows, poster_matrix_schema["required_columns"], poster_matrix_csv.name))
        errors.extend(validate_unique(poster_matrix_rows, "poster_matrix_id", poster_matrix_csv.name))
        
        valid_mot_ids = {r["buyer_motivation_row_id"] for r in buyer_rows}
        valid_ang_ids = {r["angle_id"] for r in angle_rows} if angle_csv.exists() else set()
        valid_hk_ids = {r["hook_id"] for r in hook_rows} if hook_csv.exists() else set()
        valid_shk_ids = {r["subhook_id"] for r in subhook_rows} if subhook_csv.exists() else set()
        valid_u_ids = {r["usp_id"] for r in usp_rows} if usp_csv.exists() else set()
        valid_c_ids = {r["cta_id"] for r in cta_rows} if cta_csv.exists() else set()

        for index, row in enumerate(poster_matrix_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{poster_matrix_csv.name}:{index}: invalid product_id `{pid}`")
            
            # Non-empty checks
            for col in poster_matrix_schema["required_columns"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{poster_matrix_csv.name}:{index}: empty required field `{col}`")
            
            # Cross-ref checks
            mot = (row.get("motivation_id") or "").strip()
            ang = (row.get("angle_id") or "").strip()
            hk = (row.get("hook_id") or "").strip()
            shk = (row.get("subhook_id") or "").strip()
            u = (row.get("usp_id") or "").strip()
            c = (row.get("cta_id") or "").strip()
            
            if mot and mot not in valid_mot_ids:
                errors.append(f"{poster_matrix_csv.name}:{index}: unknown motivation_id `{mot}`")
            if ang and ang not in valid_ang_ids:
                errors.append(f"{poster_matrix_csv.name}:{index}: unknown angle_id `{ang}`")
            if hk and hk not in valid_hk_ids:
                errors.append(f"{poster_matrix_csv.name}:{index}: unknown hook_id `{hk}`")
            if shk and shk not in valid_shk_ids:
                errors.append(f"{poster_matrix_csv.name}:{index}: unknown subhook_id `{shk}`")
            if u and u not in valid_u_ids:
                errors.append(f"{poster_matrix_csv.name}:{index}: unknown usp_id `{u}`")
            if c and c not in valid_c_ids:
                errors.append(f"{poster_matrix_csv.name}:{index}: unknown cta_id `{c}`")
                
            # Tolerance and review
            tol = (row.get("raw_claim_tolerance") or "").strip()
            rev = (row.get("production_review_required") or "").strip()
            if tol not in ["LOW", "MEDIUM", "HIGH"]:
                errors.append(f"{poster_matrix_csv.name}:{index}: invalid raw_claim_tolerance `{tol}`")
            if rev not in ["YES", "NO"]:
                errors.append(f"{poster_matrix_csv.name}:{index}: invalid production_review_required `{rev}`")
    else:
        errors.append(f"Missing required output file: {poster_matrix_csv.name}")

    # Notion Production Rows validation
    if notion_rows_csv.exists():
        errors.extend(validate_columns(notion_rows_rows, notion_rows_schema["required_columns"], notion_rows_csv.name))
        errors.extend(validate_unique(notion_rows_rows, "notion_row_id", notion_rows_csv.name))

        # Explicit canonical self-contained column check (no joins permitted)
        nr_headers = set(notion_rows_rows[0].keys()) if notion_rows_rows else set()
        NOTION_REQUIRED_DIRECT_COLS = [
            "headline_or_hook", "subheadline_or_subhook", "usp_text", "cta_text",
            "angle_name", "primary_bucket", "secondary_bucket", "angle_family",
            "buyer_stage", "persona_fit", "boldness_level", "usage_context",
            "sales_mechanism", "format_family", "platform_surface_fit",
            "creative_output_type", "prompt_pack_id", "raw_claim_tolerance",
            "production_review_required", "operator_edit_required",
            "recommended_view", "priority_score", "production_notes",
            "source_batch", "row_status",
        ]
        for col in NOTION_REQUIRED_DIRECT_COLS:
            if col not in nr_headers:
                errors.append(f"{notion_rows_csv.name}: MISSING required direct canonical column `{col}` — notion_production_rows must be self-contained")

        valid_video_matrix_ids = {r["video_matrix_id"] for r in video_matrix_rows} if video_matrix_csv.exists() else set()
        valid_poster_matrix_ids = {r["poster_matrix_id"] for r in poster_matrix_rows} if poster_matrix_csv.exists() else set()
        valid_video_pack_ids = {r["video_prompt_pack_id"] for r in video_pack_rows} if video_pack_csv.exists() else set()
        valid_poster_pack_ids = {r["poster_prompt_pack_id"] for r in poster_pack_rows} if poster_pack_csv.exists() else set()

        for index, row in enumerate(notion_rows_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{notion_rows_csv.name}:{index}: invalid product_id `{pid}` (must be `MWTCB_25ML`)")

            for col in notion_rows_schema["required_columns"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{notion_rows_csv.name}:{index}: empty required field `{col}`")

            prod_type = (row.get("production_type") or "").strip()
            if prod_type not in ["video", "poster"]:
                errors.append(f"{notion_rows_csv.name}:{index}: invalid production_type `{prod_type}` (must be video or poster)")

            tol = (row.get("raw_claim_tolerance") or "").strip()
            if tol not in ["LOW", "MEDIUM", "HIGH"]:
                errors.append(f"{notion_rows_csv.name}:{index}: invalid raw_claim_tolerance `{tol}`")

            rev = (row.get("production_review_required") or "").strip()
            if rev not in ["YES", "NO"]:
                errors.append(f"{notion_rows_csv.name}:{index}: invalid production_review_required `{rev}`")

            oper = (row.get("operator_edit_required") or "").strip()
            if oper not in ["YES", "OPTIONAL", "NO"]:
                errors.append(f"{notion_rows_csv.name}:{index}: invalid operator_edit_required `{oper}`")

            # Cross-ref: source_matrix_id against appropriate matrix
            src_id = (row.get("source_matrix_id") or "").strip()
            if prod_type == "video" and src_id and src_id not in valid_video_matrix_ids:
                errors.append(f"{notion_rows_csv.name}:{index}: unknown video source_matrix_id `{src_id}`")
            if prod_type == "poster" and src_id and src_id not in valid_poster_matrix_ids:
                errors.append(f"{notion_rows_csv.name}:{index}: unknown poster source_matrix_id `{src_id}`")

            # Cross-ref: prompt_pack_id against appropriate prompt pack
            pack_id = (row.get("prompt_pack_id") or "").strip()
            if prod_type == "video" and pack_id and pack_id not in valid_video_pack_ids:
                errors.append(f"{notion_rows_csv.name}:{index}: unknown video prompt_pack_id `{pack_id}`")
            if prod_type == "poster" and pack_id and pack_id not in valid_poster_pack_ids:
                errors.append(f"{notion_rows_csv.name}:{index}: unknown poster prompt_pack_id `{pack_id}`")
    else:
        errors.append(f"Missing required output file: {notion_rows_csv.name}")

    # Video Prompt Pack validation
    if video_pack_csv.exists():
        errors.extend(validate_columns(video_pack_rows, video_pack_schema["required_columns"], video_pack_csv.name))
        errors.extend(validate_unique(video_pack_rows, "video_prompt_pack_id", video_pack_csv.name))

        # Explicit canonical self-contained column check
        vpp_headers = set(video_pack_rows[0].keys()) if video_pack_rows else set()
        VPP_REQUIRED_DIRECT_COLS = [
            "hook_text", "video_format", "raw_claim_tolerance",
            "production_review_required", "operator_edit_required", "next_adapter_stage",
            "subhook_text", "usp_text", "cta_text", "scene_direction", "opening_visual",
            "product_role", "proof_visual", "cta_delivery",
            "product_truth_lock", "visual_guardrails", "dialogue_guardrails",
            "overlay_guidance", "engine_neutral_prompt_brief", "negative_prompt_rules",
            "recommended_engine_family", "prompt_pack_status",
        ]
        for col in VPP_REQUIRED_DIRECT_COLS:
            if col not in vpp_headers:
                errors.append(f"{video_pack_csv.name}: MISSING required direct canonical column `{col}` — video_prompt_pack must be self-contained")

        valid_video_matrix_ids_pack = {r["video_matrix_id"] for r in video_matrix_rows} if video_matrix_csv.exists() else set()
        for index, row in enumerate(video_pack_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{video_pack_csv.name}:{index}: invalid product_id `{pid}`")
            for col in video_pack_schema["required_columns"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{video_pack_csv.name}:{index}: empty required field `{col}`")
            vid_mat_id = (row.get("video_matrix_id") or "").strip()
            if vid_mat_id and vid_mat_id not in valid_video_matrix_ids_pack:
                errors.append(f"{video_pack_csv.name}:{index}: unknown video_matrix_id `{vid_mat_id}`")
    else:
        errors.append(f"Missing required output file: {video_pack_csv.name}")

    # Poster Prompt Pack validation
    if poster_pack_csv.exists():
        errors.extend(validate_columns(poster_pack_rows, poster_pack_schema["required_columns"], poster_pack_csv.name))
        errors.extend(validate_unique(poster_pack_rows, "poster_prompt_pack_id", poster_pack_csv.name))

        # Explicit canonical self-contained column check
        ppp_headers = set(poster_pack_rows[0].keys()) if poster_pack_rows else set()
        PPP_REQUIRED_DIRECT_COLS = [
            "headline_text", "poster_format", "raw_claim_tolerance",
            "production_review_required", "operator_edit_required", "next_adapter_stage",
            "subheadline_text", "usp_chip_1", "usp_chip_2", "usp_chip_3", "cta_text",
            "poster_visual_direction", "product_position", "background_direction",
            "prop_cues", "overlay_hierarchy",
            "product_truth_lock", "visual_guardrails", "overlay_guardrails",
            "engine_neutral_prompt_brief", "negative_prompt_rules",
            "recommended_design_family", "prompt_pack_status",
        ]
        for col in PPP_REQUIRED_DIRECT_COLS:
            if col not in ppp_headers:
                errors.append(f"{poster_pack_csv.name}: MISSING required direct canonical column `{col}` — poster_prompt_pack must be self-contained")

        valid_poster_matrix_ids_pack = {r["poster_matrix_id"] for r in poster_matrix_rows} if poster_matrix_csv.exists() else set()
        for index, row in enumerate(poster_pack_rows, start=2):
            pid = (row.get("product_id") or "").strip()
            if pid != "MWTCB_25ML":
                errors.append(f"{poster_pack_csv.name}:{index}: invalid product_id `{pid}`")
            for col in poster_pack_schema["required_columns"]:
                if (row.get(col) or "").strip() == "":
                    errors.append(f"{poster_pack_csv.name}:{index}: empty required field `{col}`")
            post_mat_id = (row.get("poster_matrix_id") or "").strip()
            if post_mat_id and post_mat_id not in valid_poster_matrix_ids_pack:
                errors.append(f"{poster_pack_csv.name}:{index}: unknown poster_matrix_id `{post_mat_id}`")
    else:
        errors.append(f"Missing required output file: {poster_pack_csv.name}")

    errors.extend(validate_unique(buyer_rows, "buyer_motivation_row_id", buyer_csv.name))
    errors.extend(validate_unique(class_rows, "motivation_classification_row_id", class_csv.name))
    errors.extend(validate_non_empty(buyer_rows, buyer_schema["required_columns"], buyer_csv.name))
    errors.extend(validate_non_empty(class_rows, class_schema["required_columns"], class_csv.name))
    errors.extend(validate_cross_refs(buyer_rows, class_rows))

    csvs_to_test = [buyer_csv, class_csv]
    for csv_file in [angle_csv, hook_csv, subhook_csv, usp_csv, cta_csv, video_matrix_csv, poster_matrix_csv,
                     notion_rows_csv, video_pack_csv, poster_pack_csv]:
        if csv_file.exists():
            csvs_to_test.append(csv_file)
        
    pandas_errors, pandas_status = validate_pandas_read(csvs_to_test, args.require_pandas)
    errors.extend(pandas_errors)

    print("Copywriting Landbank Validation Summary")
    print(f"- buyer_motivations.csv rows: {len(buyer_rows)}")
    print(f"- motivation_classification.csv rows: {len(class_rows)}")
    print(f"- angle_bank.csv rows: {len(angle_rows) if angle_csv.exists() else 0}")
    print(f"- hook_bank.csv rows: {len(hook_rows) if hook_csv.exists() else 0}")
    print(f"- subhook_bank.csv rows: {len(subhook_rows) if subhook_csv.exists() else 0}")
    print(f"- usp_bank.csv rows: {len(usp_rows) if usp_csv.exists() else 0}")
    print(f"- cta_bank.csv rows: {len(cta_rows) if cta_csv.exists() else 0}")
    print(f"- video_copy_matrix.csv rows: {len(video_matrix_rows) if video_matrix_csv.exists() else 0}")
    print(f"- poster_copy_matrix.csv rows: {len(poster_matrix_rows) if poster_matrix_csv.exists() else 0}")
    print(f"- notion_production_rows.csv rows: {len(notion_rows_rows) if notion_rows_csv.exists() else 0}")
    print(f"- video_prompt_pack.csv rows: {len(video_pack_rows) if video_pack_csv.exists() else 0}")
    print(f"- poster_prompt_pack.csv rows: {len(poster_pack_rows) if poster_pack_csv.exists() else 0}")
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
