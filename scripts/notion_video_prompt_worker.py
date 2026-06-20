from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from video_prompt_compiler import compile_template
from video_storyboard_builder import build_storyboard
from video_template_parser import build_canonical_template

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_SOURCE_ID = "537c35a1-fd7a-453a-909b-eeb839b6b979"
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_API_VERSION = "2025-09-03"
WORKER_CONTRACT_VERSION = "BOSMAX_EXT_COMPILER_WORKER_v1.0"

MODE_TO_INTAKE = {
    "HYBRID": "PRODUCT_ONLY",
    "FRAMES": "READY_FRAME",
    "INGREDIENTS": "ASSET_SET",
}


class WorkerError(RuntimeError):
    """Raised when the external compiler worker cannot continue safely."""


class NotionAPIError(WorkerError):
    """Raised when a Notion API call fails."""


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").upper() or "RUN"


def _utc_job_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _join_sentences(parts: list[str]) -> str:
    cleaned: list[str] = []
    for part in parts:
        text = str(part or "").strip()
        if not text:
            continue
        if text[-1] not in ".?!":
            text = f"{text}."
        cleaned.append(text)
    return " ".join(cleaned).strip()


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    token = str(value or "").strip().lower()
    return token in {"true", "yes", "__yes__", "1"}


def _normalize_page_id(value: str) -> str:
    token = str(value or "").strip()
    if not token:
        raise WorkerError("Empty Notion page/data source id.")
    if token.startswith("collection://"):
        token = token.split("collection://", 1)[1]
    match = re.search(r"([0-9a-fA-F]{32}|[0-9a-fA-F]{8}-[0-9a-fA-F-]{27})", token)
    if not match:
        raise WorkerError(f"Could not parse a Notion id from {value!r}")
    raw = match.group(1).replace("-", "")
    return (
        f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-"
        f"{raw[16:20]}-{raw[20:32]}"
    ).lower()


def _as_json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _read_yaml_or_json(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
    else:
        data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise WorkerError(f"Snapshot must resolve to a mapping: {path}")
    return data


def _extract_plain_text(nodes: list[dict[str, Any]]) -> str:
    return "".join(str(node.get("plain_text") or "") for node in nodes)


def _extract_property_value(prop: dict[str, Any]) -> Any:
    prop_type = prop.get("type")
    if prop_type == "title":
        return _extract_plain_text(prop.get("title") or [])
    if prop_type == "rich_text":
        return _extract_plain_text(prop.get("rich_text") or [])
    if prop_type == "select":
        selected = prop.get("select") or {}
        return str(selected.get("name") or "")
    if prop_type == "multi_select":
        return [str(item.get("name") or "") for item in (prop.get("multi_select") or [])]
    if prop_type == "status":
        selected = prop.get("status") or {}
        return str(selected.get("name") or "")
    if prop_type == "checkbox":
        return bool(prop.get("checkbox"))
    if prop_type == "number":
        return prop.get("number")
    if prop_type == "url":
        return str(prop.get("url") or "")
    if prop_type == "relation":
        return [_normalize_page_id(item.get("id") or "") for item in (prop.get("relation") or [])]
    if prop_type == "formula":
        formula = prop.get("formula") or {}
        formula_type = formula.get("type")
        return formula.get(formula_type)
    if prop_type == "rollup":
        rollup = prop.get("rollup") or {}
        rollup_type = rollup.get("type")
        value = rollup.get(rollup_type)
        if rollup_type == "array":
            items: list[Any] = []
            for item in value or []:
                if isinstance(item, dict) and "type" in item:
                    items.append(_extract_property_value(item))
                else:
                    items.append(item)
            return items
        return value
    return prop.get(prop_type)


def _get_prop(page: dict[str, Any], name: str, default: Any = "") -> Any:
    prop = (page.get("properties") or {}).get(name)
    if not isinstance(prop, dict):
        return default
    value = _extract_property_value(prop)
    return default if value in (None, "") else value


def _title_from_page(page: dict[str, Any]) -> str:
    for prop in (page.get("properties") or {}).values():
        if isinstance(prop, dict) and prop.get("type") == "title":
            return str(_extract_property_value(prop) or "")
    return ""


def _single_relation_id(page: dict[str, Any], prop_name: str, *, required: bool) -> str:
    relation_ids = _get_prop(page, prop_name, default=[])
    if not isinstance(relation_ids, list):
        relation_ids = []
    if not relation_ids and not required:
        return ""
    if len(relation_ids) != 1:
        raise WorkerError(
            f"Property {prop_name!r} must contain exactly one relation id, got {relation_ids!r}"
        )
    return str(relation_ids[0])


def _build_text_property(value: str) -> dict[str, Any]:
    text = str(value or "")
    if not text.strip():
        return {"rich_text": []}
    chunks = [text[index:index + 1800] for index in range(0, len(text), 1800)]
    return {
        "rich_text": [
            {"type": "text", "text": {"content": chunk}}
            for chunk in chunks
        ]
    }


def _build_select_property(value: str | None) -> dict[str, Any]:
    if not value:
        return {"select": None}
    return {"select": {"name": value}}


class NotionClient:
    def __init__(self, token: str) -> None:
        self.token = token.strip()
        if not self.token:
            raise WorkerError("NOTION_API_TOKEN is empty.")

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{NOTION_API_BASE}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query, doseq=True)}"
        payload = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json",
        }
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise NotionAPIError(f"Notion API {method} {path} failed: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise NotionAPIError(f"Notion API {method} {path} failed: {exc.reason}") from exc
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise NotionAPIError(f"Unexpected Notion API payload for {method} {path}: {type(data)!r}")
        return data

    def retrieve_page(self, page_id: str) -> dict[str, Any]:
        return self._request("GET", f"/pages/{_normalize_page_id(page_id)}")

    def query_ready_rows(self, data_source_id: str, *, page_size: int) -> list[dict[str, Any]]:
        response = self._request(
            "POST",
            f"/data_sources/{_normalize_page_id(data_source_id)}/query",
            body={
                "page_size": page_size,
                "filter": {
                    "and": [
                        {"property": "Compiler Method", "select": {"equals": "EXTERNAL_COMPILER"}},
                        {"property": "Compiler Output Status", "select": {"equals": "READY_TO_COMPILE"}},
                        {"property": "Output Reactivity", "select": {"equals": "SYSTEM_WRITTEN_OUTPUT"}},
                    ]
                },
            },
        )
        results = response.get("results") or []
        if not isinstance(results, list):
            raise NotionAPIError("Unexpected query response: results is not a list")
        return [item for item in results if isinstance(item, dict)]

    def update_page_properties(self, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/pages/{_normalize_page_id(page_id)}",
            body={"properties": properties},
        )


def _extract_run_snapshot(run_page: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_id": _normalize_page_id(str(run_page.get("id") or "")),
        "run_name": str(_get_prop(run_page, "Run Name", default=_title_from_page(run_page)) or ""),
        "mode": str(_get_prop(run_page, "Mode") or ""),
        "platform": str(_get_prop(run_page, "Platform", default="TikTok") or "TikTok"),
        "target_language": str(_get_prop(run_page, "Target Language", default="Malay") or "Malay"),
        "overlay_allowed": bool(_get_prop(run_page, "Overlay Allowed", default=False)),
        "product_reference_provided": bool(_get_prop(run_page, "Product Reference Provided", default=False)),
        "frame_provided": bool(_get_prop(run_page, "Frame Provided", default=False)),
        "avatar_reference_provided": bool(_get_prop(run_page, "Avatar Reference Provided", default=False)),
        "style_reference_provided": bool(_get_prop(run_page, "Style Reference Provided", default=False)),
        "asset_roles_verified": bool(_get_prop(run_page, "Asset Roles Verified", default=False)),
        "uploaded_asset_notes": str(_get_prop(run_page, "Uploaded Asset Notes") or ""),
        "scene_context_override": str(_get_prop(run_page, "Scene Context Override") or ""),
        "safety_override": str(_get_prop(run_page, "Safety Override") or ""),
        "asset_role_map_text": str(_get_prop(run_page, "Asset Role Map") or ""),
        "compiler_method": str(_get_prop(run_page, "Compiler Method") or ""),
        "compiler_output_status": str(_get_prop(run_page, "Compiler Output Status") or ""),
        "prompt_status": str(_get_prop(run_page, "Prompt Status") or ""),
        "operator_use": str(_get_prop(run_page, "Operator Use") or ""),
        "output_reactivity": str(_get_prop(run_page, "Output Reactivity") or ""),
        "manual_product_route": str(_get_prop(run_page, "MANUAL_product_route") or ""),
        "manual_engine_rule": str(_get_prop(run_page, "MANUAL_engine_rule") or ""),
        "manual_angle_id": str(_get_prop(run_page, "MANUAL_angle_id") or ""),
    }


def _extract_product_snapshot(page: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_id": _normalize_page_id(str(page.get("id") or "")),
        "title": str(_get_prop(page, "Product", default=_title_from_page(page)) or ""),
        "product_id": str(_get_prop(page, "product_id") or ""),
        "product_name_full": str(_get_prop(page, "product_name_full") or ""),
        "product_truth_ref": str(_get_prop(page, "product_truth_ref") or ""),
        "product_truth_lock": str(_get_prop(page, "product_truth_lock") or ""),
        "scale_lock": str(_get_prop(page, "scale_lock") or ""),
        "safety_notes": str(_get_prop(page, "safety_notes") or ""),
        "cta_text_default": str(_get_prop(page, "cta_text_default") or ""),
        "status": str(_get_prop(page, "status") or ""),
        "product_lane": str(_get_prop(page, "product_lane") or ""),
    }


def _extract_engine_snapshot(page: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_id": _normalize_page_id(str(page.get("id") or "")),
        "title": str(_get_prop(page, "Rule", default=_title_from_page(page)) or ""),
        "engine": str(_get_prop(page, "engine") or ""),
        "duration_seconds": _get_prop(page, "duration_seconds"),
        "block_plan_reference": str(_get_prop(page, "block_plan_reference") or ""),
        "block_rule_label": str(_get_prop(page, "block_rule_label") or ""),
        "compile_output_type": str(_get_prop(page, "compile_output_type") or ""),
        "continuation_rule": str(_get_prop(page, "continuation_rule") or ""),
        "final_cta_rule": str(_get_prop(page, "final_cta_rule") or ""),
        "target_language_default": str(_get_prop(page, "target_language_default") or ""),
        "status": str(_get_prop(page, "status") or ""),
    }


def _extract_angle_snapshot(page: dict[str, Any]) -> dict[str, Any]:
    usage_tags = _get_prop(page, "usage_tags", default=[])
    mode_fit = _get_prop(page, "mode_fit", default=[])
    return {
        "page_id": _normalize_page_id(str(page.get("id") or "")),
        "title": str(_get_prop(page, "Angle", default=_title_from_page(page)) or ""),
        "angle_id": str(_get_prop(page, "angle_id") or ""),
        "product_id": str(_get_prop(page, "product_id") or ""),
        "scene_context_seed": str(_get_prop(page, "scene_context_seed") or ""),
        "auto_scene_context": str(_get_prop(page, "AUTO_scene_context") or ""),
        "commercial_family": str(_get_prop(page, "commercial_family") or ""),
        "usage_tags": usage_tags if isinstance(usage_tags, list) else [str(usage_tags)],
        "mode_fit": mode_fit if isinstance(mode_fit, list) else [str(mode_fit)],
        "visual_risk_notes": str(_get_prop(page, "visual_risk_notes") or ""),
        "status": str(_get_prop(page, "status") or ""),
    }


def _extract_avatar_snapshot(page: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_id": _normalize_page_id(str(page.get("id") or "")),
        "title": str(_get_prop(page, "Name", default=_title_from_page(page)) or ""),
        "avatar_code": str(_get_prop(page, "AvatarCode") or ""),
        "prompt_v1": str(_get_prop(page, "PromptV1") or ""),
        "character_name": str(_get_prop(page, "CharacterName") or ""),
        "environment": str(_get_prop(page, "Environment") or ""),
        "wardrobe": str(_get_prop(page, "Wardrobe") or ""),
        "lighting": str(_get_prop(page, "Lighting") or ""),
        "expression": str(_get_prop(page, "Expression") or ""),
        "usage_tags": str(_get_prop(page, "usage_tags") or ""),
    }


def _extract_copy_pack_snapshot(page: dict[str, Any], lane: str) -> dict[str, Any]:
    return {
        "page_id": _normalize_page_id(str(page.get("id") or "")),
        "lane": lane,
        "title": str(_get_prop(page, "Name", default=_title_from_page(page)) or ""),
        "product_id": str(_get_prop(page, "product_id") or ""),
        "angle_id": str(_get_prop(page, "angle_id") or ""),
        "hook": str(_get_prop(page, "hook") or ""),
        "subhook": str(_get_prop(page, "subhook") or ""),
        "usp1": str(_get_prop(page, "usp1") or ""),
        "usp2": str(_get_prop(page, "usp2") or ""),
        "usp3": str(_get_prop(page, "usp3") or ""),
        "cta": str(_get_prop(page, "cta") or ""),
        "usage_tags": str(_get_prop(page, "usage_tags") or ""),
        "status": str(_get_prop(page, "status") or ""),
    }


def build_live_snapshot(client: NotionClient, run_page_id: str) -> dict[str, Any]:
    run_page = client.retrieve_page(run_page_id)
    product_id = _single_relation_id(run_page, "Product", required=True)
    engine_rule_id = _single_relation_id(run_page, "Engine Rule", required=True)
    angle_id = _single_relation_id(run_page, "Angle", required=True)
    avatar_id = _single_relation_id(run_page, "Avatar AI", required=False)
    copy_bosmax_id = _single_relation_id(run_page, "Copy Pack BOSMAX", required=False)
    copy_mwtcb_id = _single_relation_id(run_page, "Copy Pack MWTCB", required=False)
    if bool(copy_bosmax_id) == bool(copy_mwtcb_id):
        raise WorkerError(
            "Exactly one copy pack relation must be selected across 'Copy Pack BOSMAX' and 'Copy Pack MWTCB'."
        )

    product_page = client.retrieve_page(product_id)
    engine_rule_page = client.retrieve_page(engine_rule_id)
    angle_page = client.retrieve_page(angle_id)
    avatar_page = client.retrieve_page(avatar_id) if avatar_id else None
    copy_pack_page = client.retrieve_page(copy_bosmax_id or copy_mwtcb_id)

    snapshot = {
        "run": _extract_run_snapshot(run_page),
        "product": _extract_product_snapshot(product_page),
        "engine_rule": _extract_engine_snapshot(engine_rule_page),
        "angle": _extract_angle_snapshot(angle_page),
        "avatar": _extract_avatar_snapshot(avatar_page) if avatar_page else {},
        "copy_pack": _extract_copy_pack_snapshot(
            copy_pack_page,
            lane="BOSMAX" if copy_bosmax_id else "MWTCB",
        ),
    }
    return snapshot


def _normalize_product_lane(product: dict[str, Any]) -> str:
    token = " ".join(
        [
            str(product.get("product_id") or ""),
            str(product.get("title") or ""),
            str(product.get("product_name_full") or ""),
        ]
    ).upper()
    if "BOSMAX" in token:
        return "BOSMAX"
    if "MWTCB" in token or "MINYAK" in token or "CAP_BURUNG" in token:
        return "MINYAK_WARISAN_TOK"
    raise WorkerError(f"Unsupported product lane for external compiler worker: {token!r}")


def _normalize_engine(engine_rule: dict[str, Any]) -> str:
    engine = str(engine_rule.get("engine") or "").strip().upper().replace(" ", "_")
    if engine == "GOOGLE_FLOW":
        return "GOOGLE_FLOW"
    if engine == "GROK":
        return "GROK"
    raise WorkerError(f"Unsupported engine for external compiler worker: {engine!r}")


def _parse_asset_role_map(run: dict[str, Any], mode: str) -> dict[str, str]:
    text = str(run.get("asset_role_map_text") or "").strip()
    if text:
        parsed = yaml.safe_load(text)
        if not isinstance(parsed, dict):
            raise WorkerError("Asset Role Map must parse to a mapping when provided.")
        return {str(key): str(value) for key, value in parsed.items()}
    if mode != "INGREDIENTS":
        return {}
    return {
        "image_1": "PRODUCT_REFERENCE",
        "image_2": "AVATAR_REFERENCE",
        "image_3": "STYLE_SCENE_REFERENCE",
    }


def _build_avatar_brief(snapshot: dict[str, Any]) -> str:
    avatar = snapshot.get("avatar") or {}
    prompt_v1 = str(avatar.get("prompt_v1") or "").strip()
    if prompt_v1:
        return prompt_v1
    parts = [
        str(avatar.get("character_name") or "").strip(),
        str(avatar.get("environment") or "").strip(),
        str(avatar.get("wardrobe") or "").strip(),
        str(avatar.get("expression") or "").strip(),
    ]
    return _join_sentences(parts)


def _build_visual_seed(snapshot: dict[str, Any]) -> str:
    run = snapshot["run"]
    angle = snapshot["angle"]
    avatar = snapshot.get("avatar") or {}
    parts = [
        str(run.get("scene_context_override") or "").strip(),
        str(angle.get("auto_scene_context") or "").strip(),
        str(angle.get("scene_context_seed") or "").strip(),
        str(avatar.get("environment") or "").strip(),
        str(run.get("uploaded_asset_notes") or "").strip(),
        str(angle.get("visual_risk_notes") or "").strip(),
    ]
    deduped: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if not part:
            continue
        key = part.lower()
        if key in seen:
            continue
        deduped.append(part)
        seen.add(key)
    return _join_sentences(deduped)


def _build_body(copy_pack: dict[str, Any]) -> str:
    return _join_sentences(
        [
            str(copy_pack.get("subhook") or ""),
            str(copy_pack.get("usp1") or ""),
            str(copy_pack.get("usp2") or ""),
            str(copy_pack.get("usp3") or ""),
        ]
    )


def _build_compliance_notes(snapshot: dict[str, Any]) -> str:
    run = snapshot["run"]
    product = snapshot["product"]
    angle = snapshot["angle"]
    engine_rule = snapshot["engine_rule"]
    return _join_sentences(
        [
            str(product.get("safety_notes") or ""),
            str(angle.get("visual_risk_notes") or ""),
            str(run.get("safety_override") or ""),
            str(engine_rule.get("continuation_rule") or ""),
        ]
    )


def validate_snapshot(snapshot: dict[str, Any], *, force: bool = False) -> tuple[list[str], list[str]]:
    run = snapshot["run"]
    product = snapshot["product"]
    engine_rule = snapshot["engine_rule"]
    angle = snapshot["angle"]
    copy_pack = snapshot["copy_pack"]
    mode = str(run.get("mode") or "").strip().upper()

    errors: list[str] = []
    warnings: list[str] = []

    if str(run.get("compiler_method") or "") != "EXTERNAL_COMPILER":
        errors.append("Compiler Method must be EXTERNAL_COMPILER.")
    if str(run.get("output_reactivity") or "") != "SYSTEM_WRITTEN_OUTPUT":
        errors.append("Output Reactivity must be SYSTEM_WRITTEN_OUTPUT.")
    if not force and str(run.get("compiler_output_status") or "") != "READY_TO_COMPILE":
        errors.append("Compiler Output Status must be READY_TO_COMPILE unless --force is used.")
    if not force and str(run.get("prompt_status") or "") not in {"Ready", "Sent to Compiler"}:
        errors.append("Prompt Status must be Ready unless --force is used.")
    if any(str(run.get(key) or "").strip() for key in ("manual_product_route", "manual_engine_rule", "manual_angle_id")):
        errors.append("Manual fallback fields are populated; external compiler lane requires authority relations only.")
    if mode not in MODE_TO_INTAKE:
        errors.append(f"Unsupported run mode: {mode!r}")

    if not str(product.get("product_id") or "").strip():
        errors.append("Product authority row is missing product_id.")
    if not str(product.get("product_truth_ref") or "").strip() and not str(product.get("product_truth_lock") or "").strip():
        errors.append("Product authority row must supply product_truth_ref or product_truth_lock.")
    if not str(engine_rule.get("engine") or "").strip():
        errors.append("Engine Rule row is missing engine.")
    if not engine_rule.get("duration_seconds"):
        errors.append("Engine Rule row is missing duration_seconds.")
    if str(engine_rule.get("compile_output_type") or "") == "BLOCKED_UNTIL_LANE":
        errors.append("Engine Rule row is blocked for compile_output_type.")
    if not str(angle.get("angle_id") or "").strip():
        errors.append("Angle authority row is missing angle_id.")
    if not str(angle.get("auto_scene_context") or angle.get("scene_context_seed") or "").strip():
        errors.append("Angle authority row is missing scene context.")
    if not str(copy_pack.get("hook") or "").strip():
        errors.append("Copy pack row is missing hook.")
    if not str(copy_pack.get("cta") or "").strip():
        warnings.append("Copy pack row is missing cta; worker will fall back to the product default CTA when available.")
    if not _build_body(copy_pack):
        errors.append("Copy pack row is missing body material (subhook/usp1/usp2/usp3).")

    product_id = str(product.get("product_id") or "").strip()
    if product_id and str(angle.get("product_id") or "").strip() and str(angle.get("product_id")) != product_id:
        errors.append("Angle authority product_id does not match Product authority product_id.")
    if product_id and str(copy_pack.get("product_id") or "").strip() and str(copy_pack.get("product_id")) != product_id:
        errors.append("Copy pack product_id does not match Product authority product_id.")
    if str(copy_pack.get("angle_id") or "").strip() and str(copy_pack.get("angle_id")) != str(angle.get("angle_id") or ""):
        errors.append("Copy pack angle_id does not match the selected Angle row.")

    if str(product.get("status") or "").lower() not in {"", "approved"}:
        warnings.append(f"Product authority status is {product.get('status')!r}, not approved.")
    if str(angle.get("status") or "").lower() not in {"", "approved"}:
        warnings.append(f"Angle authority status is {angle.get('status')!r}, not approved.")
    if str(engine_rule.get("status") or "").lower() not in {"", "approved"}:
        warnings.append(f"Engine Rule status is {engine_rule.get('status')!r}, not approved.")
    if str(copy_pack.get("status") or "").lower() not in {"", "approved"}:
        warnings.append(f"Copy pack status is {copy_pack.get('status')!r}, not approved.")

    mode_fit = [str(item).upper() for item in (angle.get("mode_fit") or []) if str(item).strip()]
    if mode_fit and mode not in mode_fit:
        warnings.append(f"Angle mode_fit {mode_fit!r} does not explicitly include run mode {mode!r}.")

    if mode == "HYBRID" and not _coerce_bool(run.get("product_reference_provided")):
        errors.append("HYBRID runs require Product Reference Provided = true.")
    if mode == "FRAMES" and not _coerce_bool(run.get("frame_provided")):
        errors.append("FRAMES runs require Frame Provided = true.")
    if mode == "INGREDIENTS":
        if not _coerce_bool(run.get("product_reference_provided")):
            errors.append("INGREDIENTS runs require Product Reference Provided = true.")
        if not _coerce_bool(run.get("asset_roles_verified")):
            errors.append("INGREDIENTS runs require Asset Roles Verified = true.")
        if snapshot.get("avatar") and not _coerce_bool(run.get("avatar_reference_provided")):
            errors.append("INGREDIENTS runs with Avatar AI selected require Avatar Reference Provided = true.")

    return errors, warnings


def build_worker_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    run = snapshot["run"]
    product = snapshot["product"]
    engine_rule = snapshot["engine_rule"]
    angle = snapshot["angle"]
    avatar = snapshot.get("avatar") or {}
    copy_pack = snapshot["copy_pack"]
    mode = str(run.get("mode") or "").strip().upper()
    product_lane = _normalize_product_lane(product)
    engine = _normalize_engine(engine_rule)
    duration_seconds = int(engine_rule.get("duration_seconds") or 0)
    duration = f"{duration_seconds}s"
    asset_role_map = _parse_asset_role_map(run, mode)
    copy_cta = str(copy_pack.get("cta") or product.get("cta_text_default") or "").strip()
    hook = str(copy_pack.get("hook") or "").strip()
    body = _build_body(copy_pack)
    visual_seed = _build_visual_seed(snapshot)
    avatar_brief = _build_avatar_brief(snapshot)

    payload: dict[str, Any] = {
        "template_id": f"NOTION_{_slug(str(run.get('run_name') or 'RUN'))}_{str(run.get('page_id') or '')[:8].upper()}",
        "template_name": str(run.get("run_name") or "Notion Video Prompt Run").strip(),
        "source_angle_id": str(angle.get("angle_id") or "").strip(),
        "copypack_id": str(copy_pack.get("page_id") or "").strip(),
        "product_lane": product_lane,
        "platform": str(run.get("platform") or "TikTok").strip() or "TikTok",
        "engine": engine,
        "mode": mode,
        "intake_mode": MODE_TO_INTAKE[mode],
        "presenter_route": "PRESENTER_HYBRID",
        "commercial_angle_id": str(angle.get("angle_id") or "").strip(),
        "commercial_angle_name": str(angle.get("title") or "").strip(),
        "duration": duration,
        "hook": hook,
        "body": body,
        "cta": copy_cta,
        "raw_prompt_seed": " ".join(part for part in [hook, body, copy_cta] if part).strip(),
        "visual_seed": visual_seed,
        "product_truth_ref": str(product.get("product_truth_ref") or "").strip(),
        "product_truth_lock": str(product.get("product_truth_lock") or "").strip(),
        "scale_lock": str(product.get("scale_lock") or "").strip(),
        "product_input": f"Selected approved product authority row for {product.get('product_name_full') or product.get('title')}.",
        "avatar_source": "NOTION_AVATAR_AI" if avatar else "AVATAR_POOL",
        "avatar_brief": avatar_brief,
        "compliance_notes": _build_compliance_notes(snapshot),
        "overlay_allowed": bool(run.get("overlay_allowed")),
        "risk_class": "LOW",
        "claim_class": "STANDARD",
    }

    if mode == "FRAMES":
        payload["ready_frame_input"] = (
            str(run.get("uploaded_asset_notes") or "").strip()
            or "One uploaded finished frame already contains the presenter, product, and scene."
        )
        payload["frame_truth_lock"] = (
            "The uploaded finished frame is the visual truth. Lock identity, wardrobe, pose, "
            "product position, label orientation, scale, scene, and lighting from that frame. "
            "Motion-delta only; do not rebuild the scene from zero."
        )
        payload["visual_authority"] = "USER_UPLOAD"
    elif mode == "INGREDIENTS":
        payload["asset_role_map"] = asset_role_map
        payload["asset_hierarchy"] = "PRODUCT_TRUTH > AVATAR_IDENTITY > STYLE_SCENE"
        payload["avatar_reference_lock"] = (
            "Use the selected avatar reference as identity truth; do not drift identity, "
            "wardrobe, expression, or age."
            if avatar
            else ""
        )
        payload["style_scene_limit"] = (
            "Uploaded style/scene references may influence mood, environment, and lighting only; "
            "they must never override product truth or avatar identity."
        )

    return payload


def render_raw_prompt_compiled(payload: dict[str, Any]) -> str:
    ordered: dict[str, Any] = {}
    for key in (
        "engine",
        "duration",
        "intake_mode",
        "platform",
        "product_lane",
        "product_input",
        "product_truth_ref",
        "product_truth_lock",
        "scale_lock",
        "avatar_source",
        "avatar_brief",
        "ready_frame_input",
        "frame_truth_lock",
        "asset_role_map",
        "asset_hierarchy",
        "avatar_reference_lock",
        "style_scene_limit",
        "visual_seed",
        "hook",
        "body",
        "cta",
        "overlay_allowed",
        "compliance_notes",
    ):
        value = payload.get(key)
        if value in (None, "", {}, []):
            continue
        ordered[key] = value
    return yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True).strip()


def _build_snapshot_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_page_id": snapshot["run"].get("page_id"),
        "product_page_id": snapshot["product"].get("page_id"),
        "engine_rule_page_id": snapshot["engine_rule"].get("page_id"),
        "angle_page_id": snapshot["angle"].get("page_id"),
        "avatar_page_id": (snapshot.get("avatar") or {}).get("page_id", ""),
        "copy_pack_page_id": snapshot["copy_pack"].get("page_id"),
        "copy_pack_lane": snapshot["copy_pack"].get("lane"),
        "mode": snapshot["run"].get("mode"),
        "engine": snapshot["engine_rule"].get("engine"),
        "duration_seconds": snapshot["engine_rule"].get("duration_seconds"),
    }


def compile_snapshot(snapshot: dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    errors, warnings = validate_snapshot(snapshot, force=force)
    if errors:
        raise WorkerError(" | ".join(errors))

    payload = build_worker_payload(snapshot)
    raw_prompt_compiled = render_raw_prompt_compiled(payload)
    compiled = build_canonical_template(payload)
    compiled = build_storyboard(compiled)
    compiled = compile_template(compiled)

    qa = compiled.get("qa") or {}
    compiler = compiled.get("compiler") or {}
    qa_errors = [str(item) for item in (qa.get("qa_errors") or [])]
    qa_warnings = [str(item) for item in (qa.get("qa_warnings") or [])]
    if warnings:
        qa_warnings = [*warnings, *qa_warnings]
        qa["qa_warnings"] = qa_warnings

    if qa_errors:
        compiler_output_status = "QA_FAILED"
        prompt_status = "Failed"
        compiler_qa_status = "FAILED"
    elif qa_warnings:
        compiler_output_status = "COMPILED"
        prompt_status = "Final Received"
        compiler_qa_status = "REVIEW"
    else:
        compiler_output_status = "QA_PASSED"
        prompt_status = "Final Received"
        compiler_qa_status = "PASSED"

    notes = " | ".join(
        part
        for part in [
            f"output_mode={compiler.get('output_mode') or ''}",
            f"prompt_set_count={compiler.get('prompt_set_count') or 0}",
            f"qa_status={qa.get('qa_status') or ''}",
            f"block_plan={','.join(str(item) for item in (compiled.get('duration') or {}).get('block_plan') or [])}",
            "" if not qa_warnings else f"warnings={len(qa_warnings)}",
        ]
        if part
    )

    job_id = f"{_utc_job_stamp()}-{str(snapshot['run'].get('page_id') or '')[:8]}"
    result = {
        "job_id": job_id,
        "contract_version": WORKER_CONTRACT_VERSION,
        "snapshot": snapshot,
        "snapshot_summary": _build_snapshot_summary(snapshot),
        "worker_payload": payload,
        "raw_prompt_compiled": raw_prompt_compiled,
        "final_output_9_section": str(compiler.get("final_prompt_text") or ""),
        "compiled_template": compiled,
        "writeback_properties": {
            "Compiler Contract Version": WORKER_CONTRACT_VERSION,
            "Compiler Job ID": job_id,
            "Compiler Input Snapshot": _as_json_text(_build_snapshot_summary(snapshot)),
            "RAW_PROMPT_COMPILED": raw_prompt_compiled,
            "FINAL_OUTPUT_9_SECTION": str(compiler.get("final_prompt_text") or ""),
            "Compiler Output Notes": notes,
            "Compiler Error": "",
            "Compiler Output Status": compiler_output_status,
            "Prompt Status": prompt_status,
            "COMPILER_QA_STATUS": compiler_qa_status,
        },
    }
    return result


def write_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".yaml", ".yml"}:
        path.write_text(yaml.safe_dump(result, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


def update_run_as_sent(client: NotionClient, run_page_id: str, *, job_id: str) -> None:
    client.update_page_properties(
        run_page_id,
        {
            "Compiler Job ID": _build_text_property(job_id),
            "Compiler Error": _build_text_property(""),
            "Compiler Output Notes": _build_text_property("External compiler worker picked up this row."),
            "Compiler Output Status": _build_select_property("SENT_TO_COMPILER"),
            "Prompt Status": _build_select_property("Sent to Compiler"),
            "COMPILER_QA_STATUS": _build_select_property("NOT_SENT"),
        },
    )


def update_run_with_result(client: NotionClient, run_page_id: str, result: dict[str, Any]) -> None:
    props = result["writeback_properties"]
    client.update_page_properties(
        run_page_id,
        {
            "Compiler Contract Version": _build_text_property(str(props["Compiler Contract Version"])),
            "Compiler Job ID": _build_text_property(str(props["Compiler Job ID"])),
            "Compiler Input Snapshot": _build_text_property(str(props["Compiler Input Snapshot"])),
            "RAW_PROMPT_COMPILED": _build_text_property(str(props["RAW_PROMPT_COMPILED"])),
            "FINAL_OUTPUT_9_SECTION": _build_text_property(str(props["FINAL_OUTPUT_9_SECTION"])),
            "Compiler Output Notes": _build_text_property(str(props["Compiler Output Notes"])),
            "Compiler Error": _build_text_property(str(props["Compiler Error"])),
            "Compiler Output Status": _build_select_property(str(props["Compiler Output Status"])),
            "Prompt Status": _build_select_property(str(props["Prompt Status"])),
            "COMPILER_QA_STATUS": _build_select_property(str(props["COMPILER_QA_STATUS"])),
        },
    )


def update_run_with_error(client: NotionClient, run_page_id: str, *, message: str, job_id: str) -> None:
    client.update_page_properties(
        run_page_id,
        {
            "Compiler Contract Version": _build_text_property(WORKER_CONTRACT_VERSION),
            "Compiler Job ID": _build_text_property(job_id),
            "Compiler Error": _build_text_property(message),
            "Compiler Output Notes": _build_text_property("External compiler worker blocked this row before final output writeback."),
            "Compiler Output Status": _build_select_property("BLOCKED"),
            "Prompt Status": _build_select_property("Failed"),
            "COMPILER_QA_STATUS": _build_select_property("FAILED"),
        },
    )


def process_snapshot_path(snapshot_path: Path, *, output_path: Path | None, force: bool) -> dict[str, Any]:
    snapshot = _read_yaml_or_json(snapshot_path)
    result = compile_snapshot(snapshot, force=force)
    if output_path:
        write_result(output_path, result)
    return result


def process_live_run(
    client: NotionClient,
    run_page_id: str,
    *,
    output_dir: Path | None,
    dry_run: bool,
    force: bool,
) -> dict[str, Any]:
    snapshot = build_live_snapshot(client, run_page_id)
    job_id = f"{_utc_job_stamp()}-{str(snapshot['run'].get('page_id') or '')[:8]}"
    if not dry_run:
        update_run_as_sent(client, run_page_id, job_id=job_id)

    try:
        result = compile_snapshot(snapshot, force=force)
    except Exception as exc:
        if not dry_run:
            update_run_with_error(client, run_page_id, message=str(exc), job_id=job_id)
        raise

    if output_dir:
        output_path = output_dir / f"{result['job_id']}.json"
        write_result(output_path, result)
    if not dry_run:
        update_run_with_result(client, run_page_id, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve BOSMAX Notion video prompt runs into RAW_PROMPT_COMPILED and FINAL_OUTPUT_9_SECTION."
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--snapshot", help="Local YAML/JSON worker snapshot file.")
    source_group.add_argument("--run-page-id", help="Single Notion run page id to compile and write back.")
    source_group.add_argument("--data-source-id", help="Notion data source id to sweep for READY_TO_COMPILE rows.")
    parser.add_argument("--output", help="Single output file path for --snapshot runs.")
    parser.add_argument("--output-dir", help="Optional directory for per-run JSON artifacts.")
    parser.add_argument("--page-size", type=int, default=10, help="Max READY rows to query in one sweep.")
    parser.add_argument("--dry-run", action="store_true", help="Compile without writing back to Notion.")
    parser.add_argument("--force", action="store_true", help="Bypass READY status checks.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else None
    output_path = Path(args.output) if args.output else None

    if args.snapshot:
        result = process_snapshot_path(Path(args.snapshot), output_path=output_path, force=args.force)
        print(json.dumps({
            "job_id": result["job_id"],
            "contract_version": result["contract_version"],
            "qa_status": result["compiled_template"]["qa"]["qa_status"],
            "compiler_output_status": result["writeback_properties"]["Compiler Output Status"],
            "prompt_status": result["writeback_properties"]["Prompt Status"],
        }, ensure_ascii=False, indent=2))
        return

    token = os.environ.get("NOTION_API_TOKEN", "").strip()
    if not token:
        raise WorkerError("NOTION_API_TOKEN is required for live Notion runs.")
    client = NotionClient(token)

    if args.run_page_id:
        result = process_live_run(
            client,
            args.run_page_id,
            output_dir=output_dir,
            dry_run=args.dry_run,
            force=args.force,
        )
        print(json.dumps({
            "run_page_id": _normalize_page_id(args.run_page_id),
            "job_id": result["job_id"],
            "qa_status": result["compiled_template"]["qa"]["qa_status"],
            "compiler_output_status": result["writeback_properties"]["Compiler Output Status"],
            "prompt_status": result["writeback_properties"]["Prompt Status"],
        }, ensure_ascii=False, indent=2))
        return

    data_source_id = args.data_source_id or DEFAULT_DATA_SOURCE_ID
    ready_rows = client.query_ready_rows(data_source_id, page_size=max(1, args.page_size))
    processed: list[dict[str, Any]] = []
    for row in ready_rows:
        run_page_id = _normalize_page_id(str(row.get("id") or ""))
        result = process_live_run(
            client,
            run_page_id,
            output_dir=output_dir,
            dry_run=args.dry_run,
            force=args.force,
        )
        processed.append(
            {
                "run_page_id": run_page_id,
                "job_id": result["job_id"],
                "qa_status": result["compiled_template"]["qa"]["qa_status"],
                "compiler_output_status": result["writeback_properties"]["Compiler Output Status"],
            }
        )

    print(json.dumps({
        "data_source_id": _normalize_page_id(data_source_id),
        "processed_count": len(processed),
        "processed": processed,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
