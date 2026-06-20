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
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_API_VERSION = "2025-09-03"
WORKER_CONTRACT_VERSION = "BOSMAX_EXT_COMPILER_WORKER_v1.0"

BACKEND_RUNS_DATA_SOURCE_ID = "537c35a1-fd7a-453a-909b-eeb839b6b979"
LEGACY_REQUESTS_DATA_SOURCE_ID = "b9ea23b2-82f9-4256-b1cd-89d53c9157ac"
LEGACY_FRONTEND_DATA_SOURCE_ID = "2cccc189-74e6-4ef2-a1d1-4ac4c8e1d5f7"
HYBRID_OPERATOR_DATA_SOURCE_ID = "a47a36cc-ca74-40f7-88d3-2bd9ad67987d"
FRAMES_OPERATOR_DATA_SOURCE_ID = "e87788b4-1c0e-45df-91b4-4a8869a56c73"
INGREDIENTS_OPERATOR_DATA_SOURCE_ID = "e179ea64-9691-4802-bbb6-cf896284a709"
ASSET_ROLE_MAP_AUTHORITY_DATA_SOURCE_ID = "e97ff5ec-508a-4c1e-8302-50cf10a45953"

DEFAULT_OPERATOR_DATA_SOURCE_IDS = (
    HYBRID_OPERATOR_DATA_SOURCE_ID,
    FRAMES_OPERATOR_DATA_SOURCE_ID,
    INGREDIENTS_OPERATOR_DATA_SOURCE_ID,
)

MODE_TO_INTAKE = {
    "HYBRID": "PRODUCT_ONLY",
    "FRAMES": "READY_FRAME",
    "INGREDIENTS": "ASSET_SET",
}

OPERATOR_SOURCE_PROFILES = {
    HYBRID_OPERATOR_DATA_SOURCE_ID: {
        "name": "BOSMAX HYBRID Operator Intake",
        "mode": "HYBRID",
        "request_status_sent": "In progress",
        "request_status_success": "Done",
        "request_status_error": "Not started",
    },
    FRAMES_OPERATOR_DATA_SOURCE_ID: {
        "name": "BOSMAX FRAMES Operator Intake",
        "mode": "FRAMES",
        "request_status_sent": "In progress",
        "request_status_success": "Done",
        "request_status_error": "Not started",
    },
    INGREDIENTS_OPERATOR_DATA_SOURCE_ID: {
        "name": "BOSMAX INGREDIENTS Operator Intake",
        "mode": "INGREDIENTS",
        "request_status_sent": "In progress",
        "request_status_success": "Done",
        "request_status_error": "Not started",
    },
}
BACKEND_ONLY_SOURCE_NAMES = {
    BACKEND_RUNS_DATA_SOURCE_ID: "BOSMAX_VIDEO_PROMPT_RUNS",
    LEGACY_REQUESTS_DATA_SOURCE_ID: "BOSMAX Video Prompt Requests",
    LEGACY_FRONTEND_DATA_SOURCE_ID: "BOSMAX Video Operator Front-End",
}

OUTPUT_PROMPT_FIELD_ALIASES = (
    "Compiler Payload / RAW Prompt",
    "RAW_PROMPT_COMPILED",
)
FINAL_OUTPUT_FIELD_ALIASES = (
    "Output From Compiler",
    "FINAL_OUTPUT_9_SECTION",
    "Final Output 9 Section",
)
VALIDATION_NOTES_FIELD_ALIASES = (
    "QA Notes",
    "Compiler Output Notes",
)
REQUEST_STATUS_FIELD_ALIASES = (
    "Request Status",
    "Prompt Status",
)


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
    if prop_type == "files":
        files: list[dict[str, str]] = []
        for item in prop.get("files") or []:
            if not isinstance(item, dict):
                continue
            file_type = str(item.get("type") or "")
            target = item.get(file_type) or {}
            if not isinstance(target, dict):
                target = {}
            files.append(
                {
                    "name": str(item.get("name") or ""),
                    "type": file_type,
                    "url": str(target.get("url") or ""),
                }
            )
        return files
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


def _build_option_property(value: str | None, prop_type: str) -> dict[str, Any]:
    normalized_type = str(prop_type or "").strip().lower()
    if normalized_type == "status":
        if not value:
            return {"status": None}
        return {"status": {"name": value}}
    return _build_select_property(value)


def _page_property_names(page: dict[str, Any]) -> set[str]:
    props = page.get("properties") or {}
    if not isinstance(props, dict):
        return set()
    return {str(key) for key in props}


def _page_property_types(page: dict[str, Any]) -> dict[str, str]:
    props = page.get("properties") or {}
    if not isinstance(props, dict):
        return {}
    result: dict[str, str] = {}
    for key, value in props.items():
        if isinstance(value, dict):
            result[str(key)] = str(value.get("type") or "")
    return result


def _relation_ids(page: dict[str, Any], prop_name: str) -> list[str]:
    value = _get_prop(page, prop_name, default=[])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _extract_file_refs(page: dict[str, Any], prop_name: str) -> list[str]:
    value = _get_prop(page, prop_name, default=[])
    if not isinstance(value, list):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, dict):
            ref = str(item.get("url") or item.get("name") or "").strip()
        else:
            ref = str(item or "").strip()
        if ref:
            refs.append(ref)
    return refs


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    return [chunk.strip() for chunk in re.split(r"[,|]", text) if chunk.strip()]


def _parent_data_source_id(page: dict[str, Any]) -> str:
    parent = page.get("parent") or {}
    if not isinstance(parent, dict):
        return ""
    parent_type = str(parent.get("type") or "")
    if parent_type == "data_source_id":
        return _normalize_page_id(str(parent.get("data_source_id") or ""))
    if parent_type == "database_id":
        return _normalize_page_id(str(parent.get("database_id") or ""))
    return ""


def _normalize_copy_source(value: Any) -> str:
    token = str(value or "").strip().upper().replace(" ", "_")
    if token in {"BOSMAX", "COPYWRITING_BANK_BOSMAX"}:
        return "BOSMAX"
    if token in {"MWTCB", "COPYWRITING_BANK_MWTCB", "MINYAK_WARISAN_TOK_CAP_BURUNG"}:
        return "MWTCB"
    return ""


def _maybe_retrieve_single_relation_page(
    client: "NotionClient",
    relation_ids: list[str],
) -> dict[str, Any] | None:
    if len(relation_ids) != 1:
        return None
    return client.retrieve_page(relation_ids[0])


def _infer_engine_from_title(title: str) -> str:
    token = str(title or "").upper()
    if "GOOGLE FLOW" in token or "FLOW" in token:
        return "GOOGLE_FLOW"
    if "GROK" in token:
        return "GROK"
    return ""


def _infer_duration_seconds(title: str) -> int | None:
    match = re.search(r"(\d+)\s*S\b", str(title or "").upper())
    if not match:
        return None
    return int(match.group(1))


def _infer_block_plan_reference(engine: str, duration_seconds: int | None) -> str:
    rules = {
        ("GROK", 16): "[10,6]",
        ("GOOGLE_FLOW", 16): "[8,8]",
        ("GOOGLE_FLOW", 40): "[10,10,10,10]",
    }
    return rules.get((str(engine or "").upper(), int(duration_seconds or 0)), "")


def _resolve_field_alias(
    available_fields: set[str],
    aliases: tuple[str, ...],
) -> str:
    for alias in aliases:
        if alias in available_fields:
            return alias
    return ""


def _resolve_writeback_field_map(available_fields: set[str]) -> dict[str, str]:
    return {
        "raw_prompt_field": _resolve_field_alias(available_fields, OUTPUT_PROMPT_FIELD_ALIASES),
        "final_output_field": _resolve_field_alias(available_fields, FINAL_OUTPUT_FIELD_ALIASES),
        "qa_notes_field": _resolve_field_alias(available_fields, VALIDATION_NOTES_FIELD_ALIASES),
        "request_status_field": _resolve_field_alias(available_fields, REQUEST_STATUS_FIELD_ALIASES),
    }


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

    def query_ready_rows(
        self,
        data_source_id: str,
        *,
        page_size: int,
        request_status_property: str,
        request_status_value: str,
    ) -> list[dict[str, Any]]:
        response = self._request(
            "POST",
            f"/data_sources/{_normalize_page_id(data_source_id)}/query",
            body={
                "page_size": page_size,
                "filter": {"property": request_status_property, "status": {"equals": request_status_value}},
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


def _extract_operator_run_snapshot(
    run_page: dict[str, Any],
    *,
    profile: dict[str, Any],
    data_source_id: str,
) -> dict[str, Any]:
    available_fields = _page_property_names(run_page)
    return {
        "page_id": _normalize_page_id(str(run_page.get("id") or "")),
        "data_source_id": data_source_id,
        "data_source_name": str(profile.get("name") or ""),
        "run_name": str(_get_prop(run_page, "Request Name", default=_title_from_page(run_page)) or ""),
        "mode": str(profile.get("mode") or ""),
        "platform": str(_get_prop(run_page, "Platform", default="TikTok Shop Malaysia") or "TikTok Shop Malaysia"),
        "target_language": str(_get_prop(run_page, "Target Language", default="Malay") or "Malay"),
        "overlay_allowed": bool(_get_prop(run_page, "Overlay Allowed", default=False)),
        "avatar_source": str(_get_prop(run_page, "Avatar Source") or ""),
        "copy_source": _normalize_copy_source(_get_prop(run_page, "Copy Source")),
        "copy_source_raw": str(_get_prop(run_page, "Copy Source") or ""),
        "scene_context": str(_get_prop(run_page, "Scene Context") or ""),
        "style_scene_source": str(_get_prop(run_page, "style_scene_source") or ""),
        "motion_delta": str(_get_prop(run_page, "Motion Delta") or ""),
        "frame_context": str(_get_prop(run_page, "Frame Context") or ""),
        "request_status": str(_get_prop(run_page, "Request Status") or ""),
        "product_photo_uploads": _extract_file_refs(run_page, "Product Photo Upload"),
        "completed_frame_uploads": _extract_file_refs(run_page, "Completed Frame Upload"),
        "product_reference_photos": _extract_file_refs(run_page, "Product Reference Photo"),
        "avatar_reference_photos": _extract_file_refs(run_page, "Avatar Reference Photo"),
        "style_scene_reference_photos": _extract_file_refs(run_page, "Style Scene Reference Photo"),
        "available_fields": sorted(available_fields),
        "property_types": _page_property_types(run_page),
        "writeback_field_map": _resolve_writeback_field_map(available_fields),
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
    title = str(_get_prop(page, "Rule", default=_title_from_page(page)) or "")
    engine = str(_get_prop(page, "engine") or "").strip() or _infer_engine_from_title(title)
    duration_seconds = _get_prop(page, "duration_seconds")
    if duration_seconds in (None, ""):
        duration_seconds = _infer_duration_seconds(title)
    duration_int = int(duration_seconds) if duration_seconds not in (None, "") else None
    block_plan_reference = str(_get_prop(page, "block_plan_reference") or "").strip()
    if not block_plan_reference:
        block_plan_reference = _infer_block_plan_reference(engine, duration_int)
    return {
        "page_id": _normalize_page_id(str(page.get("id") or "")),
        "title": title,
        "engine": engine,
        "duration_seconds": duration_int,
        "block_plan_reference": block_plan_reference,
        "block_rule_label": str(_get_prop(page, "block_rule_label") or ""),
        "compile_output_type": str(_get_prop(page, "compile_output_type") or ""),
        "continuation_rule": str(_get_prop(page, "continuation_rule") or ""),
        "final_cta_rule": str(_get_prop(page, "final_cta_rule") or ""),
        "target_language_default": str(_get_prop(page, "target_language_default") or ""),
        "status": str(_get_prop(page, "status") or ""),
    }


def _extract_angle_snapshot(page: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_id": _normalize_page_id(str(page.get("id") or "")),
        "title": str(_get_prop(page, "Angle", default=_title_from_page(page)) or ""),
        "angle_id": str(_get_prop(page, "angle_id") or ""),
        "product_id": str(_get_prop(page, "product_id") or ""),
        "scene_context_seed": str(_get_prop(page, "scene_context_seed") or ""),
        "auto_scene_context": str(_get_prop(page, "AUTO_scene_context") or ""),
        "commercial_family": str(_get_prop(page, "commercial_family") or ""),
        "usage_tags": _normalize_string_list(_get_prop(page, "usage_tags", default=[])),
        "mode_fit": _normalize_string_list(_get_prop(page, "mode_fit", default=[])),
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
        "usage_tags": _normalize_string_list(_get_prop(page, "usage_tags") or ""),
        "commercial_family": str(_get_prop(page, "commercial_family") or ""),
        "scene_context_seed": str(_get_prop(page, "scene_context_seed") or ""),
        "status": str(_get_prop(page, "status") or ""),
    }


def _extract_asset_role_map_snapshot(page: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_id": _normalize_page_id(str(page.get("id") or "")),
        "title": str(_get_prop(page, "Role Map", default=_title_from_page(page)) or ""),
        "map_id": str(_get_prop(page, "map_id") or ""),
        "mode": str(_get_prop(page, "mode") or ""),
        "status": str(_get_prop(page, "status") or ""),
        "minimum_valid_path": str(_get_prop(page, "minimum_valid_path") or ""),
        "product_reference_rule": str(_get_prop(page, "product_reference_rule") or ""),
        "avatar_reference_rule": str(_get_prop(page, "avatar_reference_rule") or ""),
        "style_scene_reference_rule": str(_get_prop(page, "style_scene_reference_rule") or ""),
        "fail_conditions": str(_get_prop(page, "fail_conditions") or ""),
    }


def _build_synthetic_angle_snapshot(run: dict[str, Any], copy_pack: dict[str, Any]) -> dict[str, Any]:
    scene_context = (
        str(run.get("scene_context") or "").strip()
        or str(copy_pack.get("scene_context_seed") or "").strip()
        or str(copy_pack.get("hook") or "").strip()
    )
    return {
        "page_id": "",
        "title": str(copy_pack.get("title") or f"{run['mode']} Operator Scene").strip(),
        "angle_id": str(copy_pack.get("angle_id") or f"{run['mode']}_SCENE_CONTEXT").strip(),
        "product_id": str(copy_pack.get("product_id") or "").strip(),
        "scene_context_seed": scene_context,
        "auto_scene_context": scene_context,
        "commercial_family": str(copy_pack.get("commercial_family") or "").strip(),
        "usage_tags": _normalize_string_list(copy_pack.get("usage_tags") or []),
        "mode_fit": [str(run.get("mode") or "").strip()],
        "visual_risk_notes": "",
        "status": "approved",
    }


def build_live_snapshot(client: NotionClient, run_page_id: str) -> dict[str, Any]:
    run_page = client.retrieve_page(run_page_id)
    data_source_id = _parent_data_source_id(run_page)
    if data_source_id in BACKEND_ONLY_SOURCE_NAMES:
        raise WorkerError(
            f"{BACKEND_ONLY_SOURCE_NAMES[data_source_id]} is BACKEND / ADMIN ONLY / DO NOT USE AS OPERATOR UI."
        )
    profile = OPERATOR_SOURCE_PROFILES.get(data_source_id)
    if not profile:
        raise WorkerError(
            "Live worker only accepts rows from BOSMAX HYBRID Operator Intake, "
            "BOSMAX FRAMES Operator Intake, or BOSMAX INGREDIENTS Operator Intake."
        )

    run_snapshot = _extract_operator_run_snapshot(run_page, profile=profile, data_source_id=data_source_id)
    product_relation_ids = _relation_ids(run_page, "Product")
    engine_relation_ids = _relation_ids(run_page, "Engine + Duration")
    avatar_relation_ids = _relation_ids(run_page, "Avatar Ai")
    bosmax_copy_relation_ids = _relation_ids(run_page, "BOSMAX Copy Set")
    mwtcb_copy_relation_ids = _relation_ids(run_page, "MWTCB Copy Set")
    asset_role_map_relation_ids = _relation_ids(run_page, "Asset Role Map")

    run_snapshot.update(
        {
            "product_relation_ids": product_relation_ids,
            "engine_rule_relation_ids": engine_relation_ids,
            "avatar_relation_ids": avatar_relation_ids,
            "bosmax_copy_relation_ids": bosmax_copy_relation_ids,
            "mwtcb_copy_relation_ids": mwtcb_copy_relation_ids,
            "asset_role_map_relation_ids": asset_role_map_relation_ids,
        }
    )

    product_page = _maybe_retrieve_single_relation_page(client, product_relation_ids)
    engine_rule_page = _maybe_retrieve_single_relation_page(client, engine_relation_ids)
    avatar_page = _maybe_retrieve_single_relation_page(client, avatar_relation_ids)
    copy_lane = "BOSMAX" if len(bosmax_copy_relation_ids) == 1 else "MWTCB"
    copy_page = _maybe_retrieve_single_relation_page(
        client,
        bosmax_copy_relation_ids if len(bosmax_copy_relation_ids) == 1 else mwtcb_copy_relation_ids,
    )
    asset_role_map_page = _maybe_retrieve_single_relation_page(client, asset_role_map_relation_ids)

    product_snapshot = _extract_product_snapshot(product_page) if product_page else {}
    engine_snapshot = _extract_engine_snapshot(engine_rule_page) if engine_rule_page else {}
    avatar_snapshot = _extract_avatar_snapshot(avatar_page) if avatar_page else {}
    copy_pack_snapshot = _extract_copy_pack_snapshot(copy_page, lane=copy_lane) if copy_page else {}
    asset_role_map_snapshot = (
        _extract_asset_role_map_snapshot(asset_role_map_page) if asset_role_map_page else {}
    )

    return {
        "run": run_snapshot,
        "product": product_snapshot,
        "engine_rule": engine_snapshot,
        "angle": _build_synthetic_angle_snapshot(run_snapshot, copy_pack_snapshot),
        "avatar": avatar_snapshot,
        "copy_pack": copy_pack_snapshot,
        "asset_role_map": asset_role_map_snapshot,
    }


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


def _parse_asset_role_map(snapshot: dict[str, Any], mode: str) -> dict[str, str]:
    asset_role_map = snapshot.get("asset_role_map") or {}
    if not asset_role_map:
        return {}
    return {
        "map_id": str(asset_role_map.get("map_id") or ""),
        "minimum_valid_path": str(asset_role_map.get("minimum_valid_path") or ""),
        "product_reference_rule": str(asset_role_map.get("product_reference_rule") or ""),
        "avatar_reference_rule": str(asset_role_map.get("avatar_reference_rule") or ""),
        "style_scene_reference_rule": str(asset_role_map.get("style_scene_reference_rule") or ""),
        "fail_conditions": str(asset_role_map.get("fail_conditions") or ""),
        "mode": mode,
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
        str(run.get("scene_context") or "").strip(),
        str(angle.get("auto_scene_context") or "").strip(),
        str(angle.get("scene_context_seed") or "").strip(),
        str(avatar.get("environment") or "").strip(),
        str(run.get("frame_context") or "").strip(),
        str(run.get("motion_delta") or "").strip(),
        str(run.get("style_scene_source") or "").strip(),
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
    product = snapshot["product"]
    angle = snapshot["angle"]
    engine_rule = snapshot["engine_rule"]
    return _join_sentences(
        [
            str(product.get("safety_notes") or ""),
            str(angle.get("visual_risk_notes") or ""),
            str(engine_rule.get("continuation_rule") or ""),
        ]
    )


def _asset_role_requires_style_scene(asset_role_map: dict[str, Any]) -> bool:
    token = " ".join(
        [
            str(asset_role_map.get("minimum_valid_path") or ""),
            str(asset_role_map.get("style_scene_reference_rule") or ""),
            str(asset_role_map.get("fail_conditions") or ""),
        ]
    ).upper()
    return "STYLE_SCENE" in token


def validate_snapshot(snapshot: dict[str, Any], *, force: bool = False) -> tuple[list[str], list[str]]:
    run = snapshot["run"]
    product = snapshot["product"]
    engine_rule = snapshot["engine_rule"]
    angle = snapshot["angle"]
    copy_pack = snapshot["copy_pack"]
    asset_role_map = snapshot.get("asset_role_map") or {}
    mode = str(run.get("mode") or "").strip().upper()

    errors: list[str] = []
    warnings: list[str] = []

    data_source_id = str(run.get("data_source_id") or "")
    if data_source_id in BACKEND_ONLY_SOURCE_NAMES:
        errors.append(
            f"{BACKEND_ONLY_SOURCE_NAMES[data_source_id]} is BACKEND / ADMIN ONLY / DO NOT USE AS OPERATOR UI."
        )
    if data_source_id not in OPERATOR_SOURCE_PROFILES:
        errors.append("Live worker accepts only the three mode-specific operator intake databases.")
    if mode not in MODE_TO_INTAKE:
        errors.append(f"Unsupported run mode: {mode!r}")
    if not run.get("writeback_field_map", {}).get("raw_prompt_field"):
        errors.append("Operator intake row is missing 'Compiler Payload / RAW Prompt'.")
    if not run.get("writeback_field_map", {}).get("qa_notes_field"):
        errors.append("Operator intake row is missing 'QA Notes'.")
    if not run.get("writeback_field_map", {}).get("request_status_field"):
        errors.append("Operator intake row is missing 'Request Status'.")
    if len(run.get("product_relation_ids") or []) != 1:
        errors.append("Operator intake must select exactly one Product relation.")
    if len(run.get("engine_rule_relation_ids") or []) != 1:
        errors.append("Operator intake must select exactly one Engine + Duration relation.")
    copy_source = str(run.get("copy_source") or "")
    if copy_source not in {"BOSMAX", "MWTCB"}:
        errors.append("Copy Source must be BOSMAX or MWTCB.")
    if copy_source == "BOSMAX" and len(run.get("bosmax_copy_relation_ids") or []) != 1:
        errors.append("Copy Source BOSMAX requires exactly one BOSMAX Copy Set relation.")
    if copy_source == "MWTCB" and len(run.get("mwtcb_copy_relation_ids") or []) != 1:
        errors.append("Copy Source MWTCB requires exactly one MWTCB Copy Set relation.")
    if (len(run.get("bosmax_copy_relation_ids") or []) + len(run.get("mwtcb_copy_relation_ids") or [])) != 1:
        errors.append("Operator intake must select exactly one copy-set relation across BOSMAX Copy Set or MWTCB Copy Set.")

    if not str(product.get("product_id") or "").strip():
        errors.append("Product authority row is missing product_id.")
    if not str(product.get("product_truth_ref") or "").strip() and not str(product.get("product_truth_lock") or "").strip():
        errors.append("Product authority row must supply product_truth_ref or product_truth_lock.")
    if not str(engine_rule.get("engine") or "").strip():
        errors.append("Engine + Duration authority row is missing engine.")
    if not engine_rule.get("duration_seconds"):
        errors.append("Engine + Duration authority row is missing duration_seconds.")
    if str(engine_rule.get("compile_output_type") or "") == "BLOCKED_UNTIL_LANE":
        errors.append("Engine + Duration authority row is blocked for compile_output_type.")
    if not str(angle.get("auto_scene_context") or angle.get("scene_context_seed") or "").strip():
        errors.append("Scene Context is missing from operator intake / copy authority.")
    if not str(copy_pack.get("hook") or "").strip():
        errors.append("Copy pack row is missing hook.")
    if not str(copy_pack.get("cta") or product.get("cta_text_default") or "").strip():
        errors.append("Copy pack row is missing cta and product default CTA is empty.")
    if not _build_body(copy_pack):
        errors.append("Copy pack row is missing body material (subhook/usp1/usp2/usp3).")

    product_id = str(product.get("product_id") or "").strip()
    if product_id and str(copy_pack.get("product_id") or "").strip() and str(copy_pack.get("product_id")) != product_id:
        errors.append("Copy pack product_id does not match Product authority product_id.")

    if str(product.get("status") or "").lower() not in {"", "approved"}:
        warnings.append(f"Product authority status is {product.get('status')!r}, not approved.")
    if str(engine_rule.get("status") or "").lower() not in {"", "approved"}:
        warnings.append(f"Engine + Duration status is {engine_rule.get('status')!r}, not approved.")
    if str(copy_pack.get("status") or "").lower() not in {"", "approved"}:
        warnings.append(f"Copy pack status is {copy_pack.get('status')!r}, not approved.")

    if mode == "HYBRID":
        if len(run.get("product_photo_uploads") or []) < 1:
            errors.append("HYBRID intake requires Product Photo Upload.")
    if mode == "FRAMES":
        if len(run.get("completed_frame_uploads") or []) < 1:
            errors.append("FRAMES intake requires Completed Frame Upload.")
        if not str(run.get("motion_delta") or "").strip():
            errors.append("FRAMES intake requires Motion Delta.")
        if not str(run.get("frame_context") or "").strip():
            errors.append("FRAMES intake requires Frame Context.")
    if mode == "INGREDIENTS":
        if len(run.get("product_reference_photos") or []) < 1:
            errors.append("INGREDIENTS intake requires Product Reference Photo.")
        if len(run.get("avatar_reference_photos") or []) < 1:
            errors.append("INGREDIENTS intake requires Avatar Reference Photo.")
        if len(run.get("asset_role_map_relation_ids") or []) != 1:
            errors.append("INGREDIENTS intake requires exactly one Asset Role Map relation.")
        if asset_role_map and str(asset_role_map.get("mode") or "").upper() not in {"", "INGREDIENTS"}:
            errors.append("Asset Role Map authority row is not marked for INGREDIENTS mode.")
        if _asset_role_requires_style_scene(asset_role_map) and len(run.get("style_scene_reference_photos") or []) < 1:
            errors.append("INGREDIENTS intake requires Style Scene Reference Photo for the selected Asset Role Map.")

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
    asset_role_map = _parse_asset_role_map(snapshot, mode)
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
        "target_language": str(run.get("target_language") or engine_rule.get("target_language_default") or "Malay").strip(),
        "hook": hook,
        "body": body,
        "cta": copy_cta,
        "raw_prompt_seed": " ".join(part for part in [hook, body, copy_cta] if part).strip(),
        "visual_seed": visual_seed,
        "product_truth_ref": str(product.get("product_truth_ref") or "").strip(),
        "product_truth_lock": str(product.get("product_truth_lock") or "").strip(),
        "scale_lock": str(product.get("scale_lock") or "").strip(),
        "product_input": f"Selected approved product authority row for {product.get('product_name_full') or product.get('title')}.",
        "avatar_source": "NOTION_AVATAR_AI" if avatar else (str(run.get("avatar_source") or "").strip() or "AVATAR_POOL"),
        "avatar_brief": avatar_brief,
        "compliance_notes": _build_compliance_notes(snapshot),
        "overlay_allowed": bool(run.get("overlay_allowed")),
        "risk_class": "LOW",
        "claim_class": "STANDARD",
    }

    if mode == "HYBRID":
        payload["product_reference_assets"] = run.get("product_photo_uploads") or []
        payload["scene_context"] = str(run.get("scene_context") or "").strip()
    elif mode == "FRAMES":
        payload["completed_frame_assets"] = run.get("completed_frame_uploads") or []
        payload["ready_frame_input"] = _join_sentences(
            [
                str(run.get("frame_context") or "").strip(),
                str(run.get("motion_delta") or "").strip(),
            ]
        )
        payload["frame_truth_lock"] = (
            "The uploaded finished frame is the visual truth. Lock identity, wardrobe, pose, "
            "product position, label orientation, scale, scene, and lighting from that frame. "
            "Motion-delta only; do not rebuild the scene from zero."
        )
        payload["visual_authority"] = "USER_UPLOAD"
    elif mode == "INGREDIENTS":
        payload["product_reference_assets"] = run.get("product_reference_photos") or []
        payload["avatar_reference_assets"] = run.get("avatar_reference_photos") or []
        payload["style_scene_reference_assets"] = run.get("style_scene_reference_photos") or []
        payload["asset_role_map"] = asset_role_map
        payload["asset_hierarchy"] = "PRODUCT_TRUTH > AVATAR_IDENTITY > STYLE_SCENE"
        payload["avatar_reference_lock"] = (
            "Use the selected avatar reference as identity truth; do not drift identity, "
            "wardrobe, expression, or age."
            if avatar
            else ""
        )
        payload["style_scene_limit"] = (
            f"{str(run.get('style_scene_source') or 'Uploaded style/scene references')} may influence mood, environment, and lighting only; "
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
        "target_language",
        "product_lane",
        "product_input",
        "product_truth_ref",
        "product_truth_lock",
        "scale_lock",
        "avatar_source",
        "avatar_brief",
        "product_reference_assets",
        "completed_frame_assets",
        "avatar_reference_assets",
        "style_scene_reference_assets",
        "scene_context",
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
        "operator_data_source_id": snapshot["run"].get("data_source_id"),
        "operator_data_source_name": snapshot["run"].get("data_source_name"),
        "product_page_id": snapshot["product"].get("page_id"),
        "engine_rule_page_id": snapshot["engine_rule"].get("page_id"),
        "avatar_page_id": (snapshot.get("avatar") or {}).get("page_id", ""),
        "copy_pack_page_id": snapshot["copy_pack"].get("page_id"),
        "copy_pack_lane": snapshot["copy_pack"].get("lane"),
        "asset_role_map_page_id": (snapshot.get("asset_role_map") or {}).get("page_id", ""),
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

    profile = OPERATOR_SOURCE_PROFILES.get(str(snapshot["run"].get("data_source_id") or ""), {})
    if qa_errors:
        compiler_output_status = "QA_FAILED"
        request_status_value = str(profile.get("request_status_error") or "Not started")
    else:
        compiler_output_status = "COMPILED" if qa_warnings else "QA_PASSED"
        request_status_value = str(profile.get("request_status_success") or "Done")

    notes = " | ".join(
        part
        for part in [
            f"output_mode={compiler.get('output_mode') or ''}",
            f"prompt_set_count={compiler.get('prompt_set_count') or 0}",
            f"qa_status={qa.get('qa_status') or ''}",
            f"block_plan={','.join(str(item) for item in (compiled.get('duration') or {}).get('block_plan') or [])}",
            "" if not qa_warnings else f"warnings={len(qa_warnings)}",
            "" if not qa_errors else f"errors={len(qa_errors)}",
        ]
        if part
    )
    if qa_warnings:
        warning_blob = " || ".join(qa_warnings)
        notes = f"{notes} | warnings_detail={warning_blob}" if notes else warning_blob
    if qa_errors:
        error_blob = " || ".join(qa_errors)
        notes = f"{notes} | errors_detail={error_blob}" if notes else error_blob

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
            "raw_prompt": raw_prompt_compiled,
            "final_output": str(compiler.get("final_prompt_text") or ""),
            "qa_notes": notes,
            "request_status": request_status_value,
            "compiler_output_status": compiler_output_status,
        },
        "writeback_field_map": dict(snapshot["run"].get("writeback_field_map") or {}),
        "property_types": dict(snapshot["run"].get("property_types") or {}),
    }
    return result


def write_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".yaml", ".yml"}:
        path.write_text(yaml.safe_dump(result, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


def _set_text_writeback(properties: dict[str, Any], field_name: str, value: str) -> None:
    if field_name:
        properties[field_name] = _build_text_property(value)


def _set_option_writeback(
    properties: dict[str, Any],
    field_name: str,
    value: str,
    property_types: dict[str, Any],
) -> None:
    if field_name:
        properties[field_name] = _build_option_property(value, str(property_types.get(field_name) or ""))


def update_run_as_sent(
    client: NotionClient,
    run_page_id: str,
    *,
    field_map: dict[str, str],
    property_types: dict[str, Any],
    request_status_value: str,
) -> None:
    properties: dict[str, Any] = {}
    _set_text_writeback(properties, field_map.get("qa_notes_field", ""), "External compiler worker picked up this row.")
    _set_option_writeback(
        properties,
        field_map.get("request_status_field", ""),
        request_status_value,
        property_types,
    )
    if properties:
        client.update_page_properties(run_page_id, properties)


def update_run_with_result(client: NotionClient, run_page_id: str, result: dict[str, Any]) -> None:
    props = result["writeback_properties"]
    field_map = result["writeback_field_map"]
    property_types = result.get("property_types") or {}
    properties: dict[str, Any] = {}
    _set_text_writeback(properties, field_map.get("raw_prompt_field", ""), str(props["raw_prompt"]))
    _set_text_writeback(properties, field_map.get("final_output_field", ""), str(props["final_output"]))
    _set_text_writeback(properties, field_map.get("qa_notes_field", ""), str(props["qa_notes"]))
    _set_option_writeback(
        properties,
        field_map.get("request_status_field", ""),
        str(props["request_status"]),
        property_types,
    )
    if properties:
        client.update_page_properties(run_page_id, properties)


def update_run_with_error(
    client: NotionClient,
    run_page_id: str,
    *,
    message: str,
    field_map: dict[str, str],
    property_types: dict[str, Any],
    request_status_value: str,
) -> None:
    properties: dict[str, Any] = {}
    _set_text_writeback(
        properties,
        field_map.get("qa_notes_field", ""),
        f"External compiler worker blocked this row before final output writeback. {message}",
    )
    _set_option_writeback(
        properties,
        field_map.get("request_status_field", ""),
        request_status_value,
        property_types,
    )
    if properties:
        client.update_page_properties(run_page_id, properties)


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
    field_map = dict(snapshot["run"].get("writeback_field_map") or {})
    property_types = dict(snapshot["run"].get("property_types") or {})
    profile = OPERATOR_SOURCE_PROFILES.get(str(snapshot["run"].get("data_source_id") or ""), {})
    if not dry_run:
        update_run_as_sent(
            client,
            run_page_id,
            field_map=field_map,
            property_types=property_types,
            request_status_value=str(profile.get("request_status_sent") or "In progress"),
        )

    try:
        result = compile_snapshot(snapshot, force=force)
    except Exception as exc:
        if not dry_run:
            update_run_with_error(
                client,
                run_page_id,
                message=str(exc),
                field_map=field_map,
                property_types=property_types,
                request_status_value=str(profile.get("request_status_error") or "Not started"),
            )
        raise

    if output_dir:
        output_path = output_dir / f"{result['job_id']}.json"
        write_result(output_path, result)
    if not dry_run:
        update_run_with_result(client, run_page_id, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve BOSMAX operator intake rows into Compiler Payload / RAW Prompt and clean compiler output."
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--snapshot", help="Local YAML/JSON worker snapshot file.")
    source_group.add_argument(
        "--run-page",
        "--run-page-id",
        dest="run_page_id",
        help="Single Notion run page id or full Notion row URL to compile and write back.",
    )
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
            "compiler_output_status": result["writeback_properties"]["compiler_output_status"],
            "request_status": result["writeback_properties"]["request_status"],
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
            "compiler_output_status": result["writeback_properties"]["compiler_output_status"],
            "request_status": result["writeback_properties"]["request_status"],
        }, ensure_ascii=False, indent=2))
        return

    data_source_ids = [
        _normalize_page_id(args.data_source_id)
    ] if args.data_source_id else list(DEFAULT_OPERATOR_DATA_SOURCE_IDS)
    processed: list[dict[str, Any]] = []
    for data_source_id in data_source_ids:
        if data_source_id in BACKEND_ONLY_SOURCE_NAMES:
            raise WorkerError(
                f"{BACKEND_ONLY_SOURCE_NAMES[data_source_id]} is BACKEND / ADMIN ONLY / DO NOT USE AS OPERATOR UI."
            )
        profile = OPERATOR_SOURCE_PROFILES.get(data_source_id)
        if not profile:
            raise WorkerError(
                f"Unsupported operator intake data source: {data_source_id}. "
                "Allowed sources are HYBRID, FRAMES, and INGREDIENTS operator intake databases only."
            )
        ready_rows = client.query_ready_rows(
            data_source_id,
            page_size=max(1, args.page_size),
            request_status_property="Request Status",
            request_status_value=str(profile.get("request_status_error") or "Not started"),
        )
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
                    "operator_data_source_id": data_source_id,
                    "operator_data_source_name": profile["name"],
                    "job_id": result["job_id"],
                    "qa_status": result["compiled_template"]["qa"]["qa_status"],
                    "compiler_output_status": result["writeback_properties"]["compiler_output_status"],
                }
            )

    print(json.dumps({
        "data_source_ids": data_source_ids,
        "processed_count": len(processed),
        "processed": processed,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
