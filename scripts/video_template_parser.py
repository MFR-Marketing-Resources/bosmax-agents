from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "registries" / "video_template_schema.yaml"

ENGINE_ALIASES = {
    "GROK": "GROK",
    "GOOGLE_FLOW": "GOOGLE_FLOW",
    "FLOW": "GOOGLE_FLOW",
    "VEO": "VEO_3_1",
    "VEO_3_1": "VEO_3_1",
    "VEO31": "VEO_3_1",
    "VEO_3_1_LITE": "VEO_3_1_LITE",
    "VEO31LITE": "VEO_3_1_LITE",
}

MODE_ALIASES = {
    "FRAMES": "FRAMES",
    "FRAME": "FRAMES",
    "INGREDIENTS": "INGREDIENTS",
    "INGREDIENT": "INGREDIENTS",
    "HYBRID": "HYBRID",
}

PRODUCT_ALIASES = {
    "BOSMAX": "BOSMAX",
    "BOSMAX_SERUM": "BOSMAX",
    "MINYAK_WARISAN_TOK": "MINYAK_WARISAN_TOK",
    "MINYAK WARISAN TOK": "MINYAK_WARISAN_TOK",
    "MINYAK_WARISAN_CAP_BURUNG": "MINYAK_WARISAN_TOK",
    "CAP_BURUNG_MINYAK": "MINYAK_WARISAN_TOK",
    "MWTCB": "MINYAK_WARISAN_TOK",
    "MULTI_PRODUCT": "MULTI_PRODUCT",
    "ON_THE_FLY": "ON_THE_FLY",
}

EXECUTION_MODE_BY_ENGINE = {
    "GROK": "EXTENSION",
    "GOOGLE_FLOW": "FLOW_EXTEND_UI",
    "VEO_3_1": "CLIP_CHAIN",
    "VEO_3_1_LITE": "CLIP_CHAIN",
}


class ParserError(RuntimeError):
    """Raised when a template cannot be normalized safely."""


def load_schema() -> dict[str, Any]:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8")) or {}


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_")
    return slug.upper() or "VIDEO_TEMPLATE"


def _coerce_scalar(value: str) -> Any:
    text = value.strip()
    if not text:
        return ""
    if text.startswith("[") or text.startswith("{"):
        return yaml.safe_load(text)
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _parse_key_value_text(text: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        payload[key.strip()] = _coerce_scalar(value)
    return payload


def load_input(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(raw)
    elif suffix == ".json":
        data = json.loads(raw)
    else:
        data = _parse_key_value_text(raw)
    if not isinstance(data, dict):
        raise ParserError(f"Template input must resolve to a mapping: {path}")
    return data


def _get(payload: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return default


def normalize_engine(value: Any) -> str:
    token = str(value or "").strip().upper()
    token = token.replace("-", "_").replace(" ", "_")
    normalized = ENGINE_ALIASES.get(token)
    if not normalized:
        raise ParserError(f"Unsupported engine: {value!r}")
    return normalized


def normalize_mode(value: Any) -> str:
    token = str(value or "FRAMES").strip().upper()
    normalized = MODE_ALIASES.get(token)
    if not normalized:
        raise ParserError(f"Unsupported template mode: {value!r}")
    return normalized


def normalize_product_lane(value: Any) -> str:
    token = str(value or "ON_THE_FLY").strip().upper().replace("-", "_")
    token = re.sub(r"\s+", "_", token)
    normalized = PRODUCT_ALIASES.get(token)
    if not normalized:
        raise ParserError(f"Unsupported product lane: {value!r}")
    return normalized


def parse_duration_seconds(value: Any) -> int:
    if isinstance(value, int):
        duration = value
    else:
        match = re.search(r"(\d+)", str(value or ""))
        if not match:
            raise ParserError(f"Could not parse duration from {value!r}")
        duration = int(match.group(1))
    if duration <= 0:
        raise ParserError(f"Duration must be positive, got {duration}")
    return duration


def parse_block_plan(value: Any) -> list[int]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        plan = [int(item) for item in value]
    else:
        numbers = re.findall(r"\d+", str(value))
        plan = [int(item) for item in numbers]
    if not plan:
        raise ParserError(f"Block plan is empty or invalid: {value!r}")
    return plan


def derive_execution_mode(engine: str, payload: dict[str, Any]) -> str:
    explicit = str(
        _get(payload, "prompt_execution_mode", "execution_mode", default="")
    ).strip()
    if explicit:
        return explicit.upper().replace("-", "_").replace(" ", "_")
    return EXECUTION_MODE_BY_ENGINE[engine]


def derive_block_plan(
    *,
    engine: str,
    duration_seconds: int,
    execution_mode: str,
) -> list[int]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from video_block_plan import build_plan  # type: ignore[import]

    plan = build_plan(
        engine_id=engine,
        total_duration_seconds=duration_seconds,
        execution_mode=execution_mode,
    )
    return [int(item) for item in plan["block_durations_seconds"]]


def _build_seed_sections(payload: dict[str, Any]) -> tuple[str, str, str, str]:
    hook = str(_get(payload, "hook", "Hook", default="")).strip()
    body = str(_get(payload, "body", "Body", default="")).strip()
    cta = str(_get(payload, "cta", "CTA", default="")).strip()
    raw_prompt_seed = str(
        _get(payload, "raw_prompt_seed", "Raw Prompt Seed", default="")
    ).strip()
    if not raw_prompt_seed:
        raw_prompt_seed = " ".join(part for part in [hook, body, cta] if part)
    if not hook and raw_prompt_seed:
        hook = raw_prompt_seed.split(".")[0].strip()
    return raw_prompt_seed, hook, body, cta


def build_canonical_template(
    payload: dict[str, Any],
    source_path: Path | None = None,
) -> dict[str, Any]:
    schema = load_schema()
    warnings: list[str] = []

    template_name = str(
        _get(payload, "template_name", "template_label", "label", "Template Name", default="")
    ).strip()
    if not template_name:
        template_name = "Video Template Compiler Runtime"
        warnings.append("template_name missing; defaulted to runtime placeholder")

    template_id = str(
        _get(payload, "template_id", "Template ID", default="")
    ).strip()
    if not template_id:
        template_id = _slugify(template_name)
        warnings.append(f"template_id missing; derived as {template_id}")

    engine = normalize_engine(_get(payload, "engine", "Engine"))
    mode = normalize_mode(_get(payload, "mode", "Mode", default="FRAMES"))
    product_lane = normalize_product_lane(
        _get(payload, "product_lane", "product_workflow", "Product Lane", "product_name", default="ON_THE_FLY")
    )
    duration_seconds = parse_duration_seconds(
        _get(payload, "duration", "total_duration", "Duration", "Total Duration")
    )
    execution_mode = derive_execution_mode(engine, payload)
    block_plan = parse_block_plan(_get(payload, "block_plan", "Block Plan", default=[]))
    if not block_plan:
        block_plan = derive_block_plan(
            engine=engine,
            duration_seconds=duration_seconds,
            execution_mode=execution_mode,
        )

    block_count = len(block_plan)
    block_mode = "SINGLE_BLOCK" if block_count == 1 else "MULTI_BLOCK"
    continuity_requirement = "REQUIRED" if block_mode == "MULTI_BLOCK" else "OPTIONAL"

    raw_prompt_seed, hook, body, cta = _build_seed_sections(payload)
    parsed_brief = str(
        _get(payload, "parsed_brief", "summary", "Parsed Brief", default="")
    ).strip()
    if not parsed_brief:
        parsed_brief = " | ".join(part for part in [hook, body, cta] if part)

    template = {
        "schema_version": schema.get("version", 1),
        "template_id": template_id,
        "template_name": template_name,
        "identity": {
            "source_angle_id": str(_get(payload, "source_angle_id", "angle_id", default="")).strip(),
            "copypack_id": str(_get(payload, "copypack_id", "copywriting_id", default="")).strip(),
            "product_lane": product_lane,
            "platform": str(_get(payload, "platform", "Platform", default="TikTok")).strip() or "TikTok",
            "engine": engine,
            "mode": mode,
            "template_category": str(_get(payload, "template_category", default="VIDEO_TEMPLATE_COMPILER")).strip() or "VIDEO_TEMPLATE_COMPILER",
            "output_type": str(_get(payload, "output_type", default="NOTION_READY_VIDEO_PROMPT")).strip() or "NOTION_READY_VIDEO_PROMPT",
        },
        "duration": {
            "duration_seconds": duration_seconds,
            "duration_label": f"{duration_seconds}s",
            "block_mode": block_mode,
            "block_count": block_count,
            "block_plan": block_plan,
            "prompt_execution_mode": execution_mode,
            "continuity_requirement": continuity_requirement,
        },
        "input": {
            "raw_prompt_seed": raw_prompt_seed,
            "source_landbank_row": str(_get(payload, "source_landbank_row", default="")).strip(),
            "visual_seed": str(_get(payload, "visual_seed", "Visual Seed", default="")).strip(),
            "copy_seed": str(_get(payload, "copy_seed", default=raw_prompt_seed)).strip(),
            "overlay_seed": str(_get(payload, "overlay_seed", default="")).strip(),
            "product_truth_ref": str(_get(payload, "product_truth_ref", default="")).strip(),
            "compliance_notes": str(_get(payload, "compliance_notes", default="")).strip(),
        },
        "parsed": {
            "parsed_brief": parsed_brief,
            "hook": hook,
            "body": body,
            "cta": cta,
            "risk_class": str(_get(payload, "risk_class", default="LOW")).strip() or "LOW",
            "claim_class": str(_get(payload, "claim_class", default="STANDARD")).strip() or "STANDARD",
            "forbidden_claims": list(_get(payload, "forbidden_claims", default=[])) if isinstance(_get(payload, "forbidden_claims", default=[]), list) else [],
            "forbidden_visuals": list(_get(payload, "forbidden_visuals", default=[])) if isinstance(_get(payload, "forbidden_visuals", default=[]), list) else [],
        },
        "storyboard": {
            "master_storyline": str(_get(payload, "master_storyline", default="")).strip(),
            "master_storyboard": str(_get(payload, "master_storyboard", default="")).strip(),
            "narrative_arc": list(_get(payload, "narrative_arc", default=[])) if isinstance(_get(payload, "narrative_arc", default=[]), list) else [],
            "character_continuity_lock": str(_get(payload, "character_continuity_lock", default="")).strip(),
            "product_continuity_lock": str(_get(payload, "product_continuity_lock", default="")).strip(),
            "setting_camera_lock": str(_get(payload, "setting_camera_lock", default="")).strip(),
            "block_script_json": list(_get(payload, "block_script_json", default=[])) if isinstance(_get(payload, "block_script_json", default=[]), list) else [],
        },
        "compiler": {
            "engine_adapter": "",
            "compiler_version": "video_template_compiler_runtime@1.0.0",
            "final_prompt_text": "",
            "final_prompt_blocks": [],
            "prompt_surface_status": "DRAFT",
            "compiler_errors": [],
            "compiler_warnings": [],
        },
        "qa": {
            "qa_status": "NOT_RUN",
            "qa_errors": [],
            "qa_warnings": warnings,
            "production_ready": False,
            "export_ready": False,
            "notion_ready": False,
            "source_traceability": {
                "source_path": str(source_path) if source_path else "in_memory",
                "schema_path": str(SCHEMA_PATH),
                "required_paths": schema.get("required_paths", []),
            },
            "generated_at": _utc_now(),
            "generated_by": "scripts/video_template_parser.py",
        },
    }
    return template


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize BOSMAX video template seeds into canonical runtime JSON."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--format", choices=("json", "yaml"), default="json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    payload = load_input(input_path)
    template = build_canonical_template(payload, input_path)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() in {".yaml", ".yml"} or args.format == "yaml":
            output_path.write_text(
                yaml.safe_dump(template, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
        else:
            output_path.write_text(
                json.dumps(template, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        print(output_path)
        return

    if args.format == "yaml":
        print(yaml.safe_dump(template, sort_keys=False, allow_unicode=True))
        return
    print(json.dumps(template, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
