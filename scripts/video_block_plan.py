from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "registries" / "video_engine_duration_contracts.yaml"
DIALOGUE_BUDGET_PATH = ROOT / "registries" / "dialogue_budget_corridor.yaml"


@dataclass(frozen=True)
class RegistryBundle:
    contracts: dict[str, Any]
    budgets: dict[tuple[str, str, int], dict[str, Any]]


def normalize_engine_id(value: str) -> str:
    return value.strip().upper()


def normalize_execution_mode(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().upper()


def is_ready_mode_status(value: str) -> bool:
    normalized = value.strip().upper()
    return normalized in {"READY", "READY_REVIEWED_FLOW_EXTEND"}


def _default_mode_for_duration(
    engine_contract: dict[str, Any], total_duration_seconds: int
) -> str | None:
    """Deterministically pick an execution mode for a duration when none is given.

    Resolution order:
      1. explicit ``default_total_lane`` override for this exact duration
         (used for durations valid in more than one lane, e.g. Google Flow 40s),
      2. the unique READY mode whose valid_total_durations contains the duration,
      3. the engine's declared ``default_execution_mode`` (which then fails closed
         downstream if it does not actually support the duration).
    """
    execution_modes = engine_contract.get("execution_modes") or {}
    overrides = {
        int(key): str(value).upper()
        for key, value in (engine_contract.get("default_total_lane") or {}).items()
    }
    if total_duration_seconds in overrides:
        return overrides[total_duration_seconds]
    ready_candidates: list[str] = []
    for name, mode in execution_modes.items():
        if not is_ready_mode_status(str(mode.get("status", ""))):
            continue
        totals = {int(item) for item in mode.get("valid_total_durations_seconds", [])}
        if total_duration_seconds in totals:
            ready_candidates.append(str(name).upper())
    if len(ready_candidates) == 1:
        return ready_candidates[0]
    return str(engine_contract.get("default_execution_mode", "")).upper() or None


def resolve_execution_mode(
    engine_id: str, total_duration_seconds: int, explicit: str | None = None
) -> str | None:
    """Resolve the concrete execution mode for an engine+duration.

    Returns the alias-normalized mode name for engines that use execution_modes
    (GOOGLE_FLOW, VEO clip-chain). Returns the normalized explicit value (or
    None) for legacy single-lane engines such as GROK that ignore execution_mode.
    """
    bundle = load_registry_bundle()
    engine_contract = bundle.contracts.get("engines", {}).get(engine_id, {})
    if "execution_modes" not in engine_contract:
        return normalize_execution_mode(explicit)
    aliases = {
        str(alias).upper(): str(target).upper()
        for alias, target in (engine_contract.get("execution_mode_aliases") or {}).items()
    }
    explicit_mode = normalize_execution_mode(explicit)
    if explicit_mode:
        return aliases.get(explicit_mode, explicit_mode)
    resolved = _default_mode_for_duration(engine_contract, total_duration_seconds)
    if not resolved:
        return None
    return aliases.get(resolved, resolved)


def load_registry_bundle() -> RegistryBundle:
    contracts = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8")) or {}
    budget_data = yaml.safe_load(DIALOGUE_BUDGET_PATH.read_text(encoding="utf-8")) or {}
    budgets: dict[tuple[str, str, int], dict[str, Any]] = {}
    for item in budget_data.get("corridors", []):
        key = (str(item["language"]).upper(), str(item["pace_class"]).upper(), int(item["duration_seconds"]))
        budgets[key] = item
    return RegistryBundle(contracts=contracts, budgets=budgets)


def get_budget(bundle: RegistryBundle, language: str, pace_class: str, duration_seconds: int) -> dict[str, Any]:
    key = (language.upper(), pace_class.upper(), duration_seconds)
    if key not in bundle.budgets:
        raise ValueError(f"Missing dialogue budget corridor for {language}/{pace_class}/{duration_seconds}s")
    return bundle.budgets[key]


def get_block_map(mode_contract: dict[str, Any]) -> dict[int, list[int]]:
    return {
        int(key): [int(value) for value in values]
        for key, values in (mode_contract.get("default_total_to_blocks") or {}).items()
    }


def compute_block_durations(
    total_duration_seconds: int,
    primary_block_seconds: int,
    tail_block_seconds: int | None = None,
    tail_max_count: int | None = None,
) -> list[int] | None:
    """Deterministically derive a block-chain for a target total.

    The operator only supplies engine + total duration; the chaining math is
    computed here, never hand-specified. Greedy: use as many ``primary`` blocks
    as possible such that the remainder is an exact multiple of the allowed
    ``tail`` block (bounded by ``tail_max_count``), preferring the most primary
    blocks (fewest tails). Returns ``None`` when the total is not representable
    with the engine's block vocabulary — callers fail closed on ``None``.

    This reproduces every curated ``default_total_to_blocks`` entry in the
    registry (verified by validate_video_block_contracts.py), so curated tables
    and computed plans never diverge.
    """
    if total_duration_seconds <= 0 or primary_block_seconds <= 0:
        return None
    max_primary = total_duration_seconds // primary_block_seconds
    for n_primary in range(max_primary, -1, -1):
        remainder = total_duration_seconds - n_primary * primary_block_seconds
        if remainder == 0:
            return [primary_block_seconds] * n_primary if n_primary else None
        if tail_block_seconds and remainder % tail_block_seconds == 0:
            tail_count = remainder // tail_block_seconds
            if tail_max_count is not None and tail_count > tail_max_count:
                continue
            return [primary_block_seconds] * n_primary + [tail_block_seconds] * tail_count
    return None


def _compute_from_block_math(
    contract: dict[str, Any], total_duration_seconds: int
) -> list[int] | None:
    """Resolve a block-chain from a contract's ``block_math`` config, if present."""
    math_cfg = contract.get("block_math")
    if not math_cfg:
        return None
    tail = math_cfg.get("tail_block_seconds")
    tail_max = math_cfg.get("tail_max_count")
    return compute_block_durations(
        total_duration_seconds,
        int(math_cfg["primary_block_seconds"]),
        int(tail) if tail is not None else None,
        int(tail_max) if tail_max is not None else None,
    )


def _synthesize_role_defaults(block_count: int) -> list[dict[str, Any]]:
    """Default copy-arc roles for a computed chain that has no curated
    block_role_defaults entry: HOOK first, CTA last, RELIEF/PROOF in between."""
    if block_count <= 0:
        return []
    if block_count == 1:
        return [
            {
                "block_index": 1,
                "role": "SINGLE_BLOCK",
                "bridge_out_required": False,
                "bridge_in_required": False,
            }
        ]
    rows: list[dict[str, Any]] = []
    for index in range(1, block_count + 1):
        if index == 1:
            role, bridge_out, bridge_in = "HOOK_PAIN_FRICTION", True, False
        elif index == block_count:
            role, bridge_out, bridge_in = "CTA_CLOSE", False, True
        else:
            role, bridge_out, bridge_in = "RELIEF_PROOF_DEVELOPMENT", True, True
        rows.append(
            {
                "block_index": index,
                "role": role,
                "bridge_out_required": bridge_out,
                "bridge_in_required": bridge_in,
            }
        )
    return rows


def _ensure_role_defaults(
    role_defaults: dict[int, list[dict[str, Any]]],
    total_duration_seconds: int,
    block_count: int,
) -> dict[int, list[dict[str, Any]]]:
    """Curated roles win; otherwise synthesize a sensible arc for the chain."""
    if total_duration_seconds in role_defaults or block_count <= 0:
        return role_defaults
    return {
        **role_defaults,
        total_duration_seconds: _synthesize_role_defaults(block_count),
    }


def build_blocks(
    *,
    block_durations: list[int],
    total_duration_seconds: int,
    language: str,
    pace_class: str,
    bundle: RegistryBundle,
    seam_contract: dict[str, Any],
    role_defaults: dict[int, list[dict[str, Any]]],
    budget_duration_override: int | None = None,
) -> list[dict[str, Any]]:
    role_rows = role_defaults.get(total_duration_seconds, [])
    blocks: list[dict[str, Any]] = []
    for index, block_duration in enumerate(block_durations, start=1):
        role_meta = next((item for item in role_rows if int(item["block_index"]) == index), {})
        budget_lookup_duration = budget_duration_override if budget_duration_override is not None else block_duration
        block_budget = get_budget(bundle, language, pace_class, budget_lookup_duration)
        is_non_first = index > 1
        is_non_final = index < len(block_durations)
        require_previous_clip_final_second = bool(seam_contract.get("require_previous_clip_final_second", False) and is_non_first)
        blocks.append(
            {
                "block_index": index,
                "block_duration_seconds": block_duration,
                "block_role": role_meta.get("role", "GENERAL"),
                "requires_seam": is_non_first or is_non_final,
                "bridge_out_required": bool(role_meta.get("bridge_out_required", seam_contract.get("require_bridge_out_on_non_final_blocks", is_non_final) and is_non_final)),
                "bridge_in_required": bool(role_meta.get("bridge_in_required", seam_contract.get("require_bridge_in_on_non_first_blocks", is_non_first) and is_non_first)),
                "speech_resume_window_seconds": seam_contract.get("speech_resume_window_seconds") if is_non_first else None,
                "dialogue_budget": block_budget,
                "dialogue_budget_duration_seconds": int(block_budget["duration_seconds"]),
                "requires_frame_bridge": bool(seam_contract.get("require_frame_bridge", is_non_first) and is_non_first),
                "requires_previous_clip_final_second": require_previous_clip_final_second,
                "requires_identity_reanchor": bool(seam_contract.get("require_identity_reanchor_every_block", False)),
                "requires_product_reanchor": bool(seam_contract.get("require_product_reanchor_every_block", False)),
                "continuity_goal_required": bool(seam_contract.get("continuity_goal")) and is_non_first,
            }
        )
    return blocks


def build_legacy_verified_plan(
    engine_id: str,
    total_duration_seconds: int,
    language: str,
    pace_class: str,
    engine_contract: dict[str, Any],
    bundle: RegistryBundle,
) -> dict[str, Any]:
    totals = {int(item) for item in engine_contract.get("valid_total_durations_seconds", [])}
    if total_duration_seconds not in totals:
        raise ValueError(f"{engine_id} does not allow total duration {total_duration_seconds}s")

    block_map = get_block_map(engine_contract)
    # Curated split wins; otherwise compute it deterministically from block_math.
    block_durations = block_map.get(total_duration_seconds)
    if block_durations is None:
        block_durations = _compute_from_block_math(engine_contract, total_duration_seconds)
    if block_durations is None:
        raise ValueError(
            f"{engine_id} is missing deterministic block math for {total_duration_seconds}s"
        )
    total_budget = get_budget(bundle, language, pace_class, total_duration_seconds)
    role_defaults = {
        int(key): value
        for key, value in (engine_contract.get("block_role_defaults") or {}).items()
    }
    role_defaults = _ensure_role_defaults(role_defaults, total_duration_seconds, len(block_durations))
    seam_contract = engine_contract.get("seam_contract", {})
    blocks = build_blocks(
        block_durations=block_durations,
        total_duration_seconds=total_duration_seconds,
        language=language,
        pace_class=pace_class,
        bundle=bundle,
        seam_contract=seam_contract,
        role_defaults=role_defaults,
    )

    return {
        "engine_id": engine_id,
        "execution_mode": engine_contract.get("execution_mode", "EXTENSION"),
        "authority_status": engine_contract["authority_status"],
        "notion_execution_status": engine_contract["notion_execution_status"],
        "total_duration_seconds": total_duration_seconds,
        "language": language.upper(),
        "pace_class": pace_class.upper(),
        "supports_multi_block": bool(engine_contract.get("supports_multi_block")),
        "block_count": len(block_durations),
        "block_durations_seconds": block_durations,
        "prompt_count": len(block_durations),
        "requires_frame_bridge": bool(seam_contract.get("require_frame_bridge", len(block_durations) > 1)),
        "wps_budget_mode": "PER_BLOCK" if len(block_durations) > 1 else "SINGLE_BLOCK",
        "requires_identity_reanchor": bool(seam_contract.get("require_identity_reanchor_every_block", False)),
        "requires_product_reanchor": bool(seam_contract.get("require_product_reanchor_every_block", False)),
        "requires_previous_clip_final_second": bool(seam_contract.get("require_previous_clip_final_second", False)),
        "status": "READY",
        "reason": "Verified BOSMAX execution contract.",
        "total_dialogue_budget": total_budget,
        "seam_contract": seam_contract,
        "blocks": blocks,
    }


def build_mode_plan(
    engine_id: str,
    total_duration_seconds: int,
    language: str,
    pace_class: str,
    engine_contract: dict[str, Any],
    mode_name: str,
    mode_contract: dict[str, Any],
    bundle: RegistryBundle,
    previous_clip_final_second_state: str | None = None,
) -> dict[str, Any]:
    mode_status = str(mode_contract.get("status", "NEEDS_REVIEW")).upper()
    valid_totals = {int(item) for item in mode_contract.get("valid_total_durations_seconds", [])}
    block_map = get_block_map(mode_contract)
    if valid_totals and total_duration_seconds not in valid_totals:
        raise ValueError(f"{engine_id}.{mode_name} does not allow total duration {total_duration_seconds}s")

    block_durations = block_map.get(total_duration_seconds)
    if block_durations is None:
        single_clip_durations = {int(item) for item in mode_contract.get("single_clip_durations_seconds", [])}
        if total_duration_seconds in single_clip_durations:
            block_durations = [total_duration_seconds]
        else:
            # Curated split absent → compute the chain deterministically.
            block_durations = _compute_from_block_math(mode_contract, total_duration_seconds)
        if block_durations is None:
            if is_ready_mode_status(mode_status):
                raise ValueError(f"{engine_id}.{mode_name} is missing deterministic block math for {total_duration_seconds}s")
            block_durations = []

    seam_contract = mode_contract.get("seam_contract", {})
    role_defaults = {
        int(key): value
        for key, value in (mode_contract.get("block_role_defaults") or {}).items()
    }
    role_defaults = _ensure_role_defaults(role_defaults, total_duration_seconds, len(block_durations))
    raw_budget_override = mode_contract.get("dialogue_budget_actual_render_seconds")
    budget_duration_override = int(raw_budget_override) if raw_budget_override is not None else None
    blocks = build_blocks(
        block_durations=block_durations,
        total_duration_seconds=total_duration_seconds,
        language=language,
        pace_class=pace_class,
        bundle=bundle,
        seam_contract=seam_contract,
        role_defaults=role_defaults,
        budget_duration_override=budget_duration_override,
    ) if block_durations else []

    status = "READY" if is_ready_mode_status(mode_status) else "NEEDS_REVIEW"
    reason = mode_contract.get("reason")
    requires_previous_clip_state = bool(
        seam_contract.get("require_previous_clip_final_second", mode_contract.get("requires_previous_clip_final_second", False))
    )
    if status != "READY" and not reason:
        reason = engine_contract.get("review_reason", "Mode is not production-ready.")

    total_budget = bundle.budgets.get((language.upper(), pace_class.upper(), total_duration_seconds))
    return {
        "engine_id": engine_id,
        "execution_mode": mode_name,
        "authority_status": engine_contract["authority_status"],
        "notion_execution_status": engine_contract["notion_execution_status"],
        "total_duration_seconds": total_duration_seconds,
        "language": language.upper(),
        "pace_class": pace_class.upper(),
        "supports_multi_block": bool(engine_contract.get("supports_multi_block")),
        "block_count": len(block_durations),
        "block_durations_seconds": block_durations,
        "prompt_count": len(block_durations),
        "requires_frame_bridge": bool(seam_contract.get("require_frame_bridge", mode_name == "FLOW_EXTEND" or len(block_durations) > 1)),
        "wps_budget_mode": "PER_BLOCK" if len(block_durations) > 1 else "SINGLE_BLOCK",
        "requires_identity_reanchor": bool(seam_contract.get("require_identity_reanchor_every_block", mode_name == "FLOW_EXTEND")),
        "requires_product_reanchor": bool(seam_contract.get("require_product_reanchor_every_block", mode_name == "FLOW_EXTEND")),
        "requires_previous_clip_final_second": requires_previous_clip_state,
        "status": status,
        "reason": reason,
        "total_dialogue_budget": total_budget,
        "decision_record": engine_contract.get("decision_record"),
        "required_fields": mode_contract.get("required_fields", []),
        "shared_copywriting_avatar_resolver_payload": bool(
            mode_contract.get("shared_copywriting_avatar_resolver_payload", engine_contract.get("shared_copywriting_avatar_resolver_payload", False))
        ),
        "previous_clip_final_second_state": previous_clip_final_second_state,
        "runtime_proof_fields_pending": [
            "previous_clip_final_second_state"
        ] if requires_previous_clip_state and len(block_durations) > 1 and not previous_clip_final_second_state else [],
        "seam_contract": seam_contract,
        "blocks": blocks,
    }


def build_plan(
    engine_id: str,
    total_duration_seconds: int,
    language: str = "BM",
    pace_class: str = "BRISK_UGC",
    execution_mode: str | None = None,
    previous_clip_final_second_state: str | None = None,
) -> dict[str, Any]:
    bundle = load_registry_bundle()
    contracts = bundle.contracts.get("engines", {})
    if engine_id not in contracts:
        raise ValueError(f"Unknown engine_id: {engine_id}")

    engine_contract = contracts[engine_id]
    if "execution_modes" in engine_contract:
        aliases = {
            str(alias).upper(): str(target).upper()
            for alias, target in (engine_contract.get("execution_mode_aliases") or {}).items()
        }
        explicit_mode = normalize_execution_mode(execution_mode)
        if explicit_mode:
            mode_name = aliases.get(explicit_mode, explicit_mode)
        else:
            resolved = _default_mode_for_duration(engine_contract, total_duration_seconds)
            mode_name = aliases.get(resolved, resolved) if resolved else resolved
        if not mode_name:
            raise ValueError(f"{engine_id} is missing default_execution_mode")
        execution_modes = engine_contract.get("execution_modes") or {}
        if mode_name not in execution_modes:
            raise ValueError(f"Unknown execution_mode for {engine_id}: {mode_name}")
        return build_mode_plan(
            engine_id=engine_id,
            total_duration_seconds=total_duration_seconds,
            language=language,
            pace_class=pace_class,
            engine_contract=engine_contract,
            mode_name=mode_name,
            mode_contract=execution_modes[mode_name],
            bundle=bundle,
            previous_clip_final_second_state=previous_clip_final_second_state,
        )

    authority_status = str(engine_contract.get("authority_status", "")).upper()
    if authority_status == "VERIFIED":
        return build_legacy_verified_plan(engine_id, total_duration_seconds, language, pace_class, engine_contract, bundle)
    raise ValueError(f"Unsupported authority_status for {engine_id}: {authority_status}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve BOSMAX engine duration into deterministic block plan")
    parser.add_argument("--engine-id", required=True)
    parser.add_argument("--duration", required=True, type=int)
    parser.add_argument("--language", default="BM")
    parser.add_argument("--pace-class", default="BRISK_UGC")
    parser.add_argument("--execution-mode")
    parser.add_argument("--previous-clip-final-second-state")
    parser.add_argument("--format", choices=("json", "yaml"), default="yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plan = build_plan(
        engine_id=normalize_engine_id(args.engine_id),
        total_duration_seconds=int(args.duration),
        language=args.language,
        pace_class=args.pace_class,
        execution_mode=normalize_execution_mode(args.execution_mode),
        previous_clip_final_second_state=args.previous_clip_final_second_state,
    )
    if args.format == "json":
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return
    print(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    main()
