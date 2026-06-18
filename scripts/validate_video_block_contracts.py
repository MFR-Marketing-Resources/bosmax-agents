from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from video_block_plan import (
    CONTRACT_PATH,
    DIALOGUE_BUDGET_PATH,
    build_plan,
    compute_block_durations,
    load_registry_bundle,
)
from video_storyboard_builder import StoryboardError, build_storyboard  # type: ignore[import]
from video_template_parser import build_canonical_template  # type: ignore[import]

ROOT = Path(__file__).resolve().parents[1]
HANDOFF_DOC_PATH = ROOT / "BOSMAX_NOTION_MULTI_BLOCK_VIDEO_HANDOFF_v1.md"
DECISION_DOC_PATH = ROOT / "BOSMAX_VEO31_FLOW_CONTRACT_DECISION_v1.md"

FLOW_READY_STATUS = "READY_REVIEWED_FLOW_EXTEND"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def validate_registry_shape() -> dict[str, Any]:
    require(CONTRACT_PATH.exists(), f"Missing video contract registry: {CONTRACT_PATH}")
    require(DIALOGUE_BUDGET_PATH.exists(), f"Missing dialogue budget registry: {DIALOGUE_BUDGET_PATH}")
    require(HANDOFF_DOC_PATH.exists(), f"Missing multi-block handoff doc: {HANDOFF_DOC_PATH}")
    require(DECISION_DOC_PATH.exists(), f"Missing VEO/Flow decision record: {DECISION_DOC_PATH}")

    registry = load_yaml(CONTRACT_PATH)
    engines = registry.get("engines")
    require(isinstance(engines, dict) and engines, "video_engine_duration_contracts.yaml has no engines map")

    for engine_id in ("GROK", "VEO_3_1", "VEO_3_1_LITE", "GOOGLE_FLOW"):
        require(engine_id in engines, f"Registry missing required engine entry: {engine_id}")

    return engines


def validate_grok_contract(engines: dict[str, Any]) -> list[str]:
    grok = engines["GROK"]
    require(grok.get("authority_status") == "VERIFIED", "GROK must remain VERIFIED")
    require(grok.get("notion_execution_status") == "READY", "GROK notion_execution_status must remain READY")

    valid_blocks = [int(value) for value in grok.get("valid_block_durations_seconds", [])]
    require(valid_blocks == [6, 10], f"GROK valid block durations drifted: {valid_blocks}")

    expected_plans = {
        12: [6, 6],
        16: [10, 6],
        20: [10, 10],
        30: [10, 10, 10],
    }
    checks: list[str] = []
    for duration, expected_blocks in expected_plans.items():
        plan = build_plan("GROK", duration)
        actual_blocks = [int(item) for item in plan["block_durations_seconds"]]
        require(actual_blocks == expected_blocks, f"GROK {duration}s plan mismatch: expected {expected_blocks}, got {actual_blocks}")
        require(plan["block_count"] == len(expected_blocks), f"GROK {duration}s block_count mismatch")
        require(all(block in (6, 10) for block in actual_blocks), f"GROK {duration}s contains invalid block duration")
        for block in plan["blocks"]:
            block_index = int(block["block_index"])
            if block_index < plan["block_count"]:
                require(block["bridge_out_required"] is True, f"GROK {duration}s block {block_index} missing bridge-out requirement")
            if block_index > 1:
                require(block["bridge_in_required"] is True, f"GROK {duration}s block {block_index} missing bridge-in requirement")
                resume = block.get("speech_resume_window_seconds") or {}
                require(resume.get("min") == 0.5 and resume.get("max") == 1.0, f"GROK {duration}s block {block_index} resume window drifted")
            budget = block.get("dialogue_budget")
            require(isinstance(budget, dict), f"GROK {duration}s block {block_index} missing per-block budget")
        checks.append(f"GROK {duration}s -> {'+'.join(str(item) for item in actual_blocks)}")
    return checks


def validate_veo_contract(engines: dict[str, Any]) -> list[str]:
    checks: list[str] = []
    veo = engines["VEO_3_1"]
    require(veo.get("authority_status") == "PARTIAL_VERIFIED", "VEO_3_1 must be PARTIAL_VERIFIED")
    require(veo.get("notion_execution_status") == "READY_CLIP_MODE", "VEO_3_1 notion_execution_status must be READY_CLIP_MODE")
    require(veo.get("decision_record") == DECISION_DOC_PATH.name, "VEO_3_1 decision record link missing")
    clip_chain = (veo.get("execution_modes") or {}).get("CLIP_CHAIN") or {}
    require(str(clip_chain.get("status", "")).upper() == "READY", "VEO_3_1.CLIP_CHAIN must be READY")
    expected_plans = {
        16: [8, 8],
        24: [8, 8, 8],
        32: [8, 8, 8, 8],
        40: [8, 8, 8, 8, 8],
        48: [8, 8, 8, 8, 8, 8],
        56: [8, 8, 8, 8, 8, 8, 8],
    }
    for duration, expected_blocks in expected_plans.items():
        plan = build_plan("VEO_3_1", duration)
        actual_blocks = [int(item) for item in plan["block_durations_seconds"]]
        require(plan["status"] == "READY", f"VEO_3_1 {duration}s must resolve READY")
        require(actual_blocks == expected_blocks, f"VEO_3_1 {duration}s mismatch: expected {expected_blocks}, got {actual_blocks}")
        require(plan["requires_frame_bridge"] is True, f"VEO_3_1 {duration}s missing frame bridge requirement")
        require(plan["requires_identity_reanchor"] is True, f"VEO_3_1 {duration}s missing identity re-anchor requirement")
        require(plan["requires_product_reanchor"] is True, f"VEO_3_1 {duration}s missing product re-anchor requirement")
        for block in plan["blocks"][1:]:
            require(block["requires_frame_bridge"] is True, f"VEO_3_1 {duration}s block {block['block_index']} missing frame bridge flag")
            require(block["bridge_in_required"] is True, f"VEO_3_1 {duration}s block {block['block_index']} missing bridge-in")
        checks.append(f"VEO_3_1 {duration}s -> {'+'.join(str(item) for item in actual_blocks)}")

    try:
        build_plan("VEO_3_1", 14)
        fail("VEO_3_1 14s should fail closed")
    except ValueError:
        checks.append("VEO_3_1 invalid 14s rejected")
    return checks


def validate_veo31_lite_contract(engines: dict[str, Any]) -> list[str]:
    checks: list[str] = []
    lite = engines["VEO_3_1_LITE"]
    require(lite.get("authority_status") == "PARTIAL_VERIFIED", "VEO_3_1_LITE must be PARTIAL_VERIFIED")
    require(lite.get("notion_execution_status") == "READY_CLIP_MODE", "VEO_3_1_LITE notion_execution_status must be READY_CLIP_MODE")
    clip_chain = (lite.get("execution_modes") or {}).get("CLIP_CHAIN") or {}
    require(str(clip_chain.get("status", "")).upper() == "READY", "VEO_3_1_LITE.CLIP_CHAIN must be READY")
    require(int(clip_chain.get("actual_render_duration_seconds", 0)) == 7, "VEO_3_1_LITE must declare actual_render_duration_seconds: 7")
    require(int(clip_chain.get("dialogue_budget_actual_render_seconds", 0)) == 7, "VEO_3_1_LITE must declare dialogue_budget_actual_render_seconds: 7")

    bundle = load_registry_bundle()
    seven_s_budget = bundle.budgets.get(("BM", "BRISK_UGC", 7))
    require(isinstance(seven_s_budget, dict), "Dialogue budget corridor missing BM/BRISK_UGC/7s (required for VEO_3_1_LITE)")

    expected_plans = {
        8: [8],
        16: [8, 8],
        24: [8, 8, 8],
        32: [8, 8, 8, 8],
        40: [8, 8, 8, 8, 8],
        48: [8, 8, 8, 8, 8, 8],
        56: [8, 8, 8, 8, 8, 8, 8],
    }
    for duration, expected_blocks in expected_plans.items():
        plan = build_plan("VEO_3_1_LITE", duration)
        actual_blocks = [int(item) for item in plan["block_durations_seconds"]]
        require(plan["status"] == "READY", f"VEO_3_1_LITE {duration}s must resolve READY")
        require(actual_blocks == expected_blocks, f"VEO_3_1_LITE {duration}s mismatch: expected {expected_blocks}, got {actual_blocks}")
        require(plan["requires_frame_bridge"] is True, f"VEO_3_1_LITE {duration}s missing frame bridge requirement")
        require(plan["requires_identity_reanchor"] is True, f"VEO_3_1_LITE {duration}s missing identity re-anchor requirement")
        require(plan["requires_product_reanchor"] is True, f"VEO_3_1_LITE {duration}s missing product re-anchor requirement")
        for block in plan["blocks"]:
            block_budget = block.get("dialogue_budget") or {}
            require(
                int(block_budget.get("duration_seconds", 0)) == 7,
                f"VEO_3_1_LITE {duration}s block {block['block_index']} dialogue_budget must use 7s actual-render corridor, got {block_budget.get('duration_seconds')}",
            )
        for block in plan["blocks"][1:]:
            require(block["requires_frame_bridge"] is True, f"VEO_3_1_LITE {duration}s block {block['block_index']} missing frame bridge flag")
            require(block["bridge_in_required"] is True, f"VEO_3_1_LITE {duration}s block {block['block_index']} missing bridge-in")
        checks.append(f"VEO_3_1_LITE {duration}s -> {'+'.join(str(item) for item in actual_blocks)}")

    try:
        build_plan("VEO_3_1_LITE", 14)
        fail("VEO_3_1_LITE 14s should fail closed")
    except ValueError:
        checks.append("VEO_3_1_LITE invalid 14s rejected")
    return checks


def validate_flow_contract(engines: dict[str, Any]) -> list[str]:
    flow = engines["GOOGLE_FLOW"]
    require(flow.get("authority_status") == "PARTIAL_VERIFIED", "GOOGLE_FLOW must be PARTIAL_VERIFIED")
    require(flow.get("notion_execution_status") == FLOW_READY_STATUS, f"GOOGLE_FLOW notion_execution_status must be {FLOW_READY_STATUS}")
    require(flow.get("decision_record") == DECISION_DOC_PATH.name, "GOOGLE_FLOW decision record link missing")
    require(flow.get("shared_copywriting_avatar_resolver_payload") is True, "GOOGLE_FLOW must declare shared copywriting/avatar resolver payload")

    aliases = {str(key).upper(): str(value).upper() for key, value in (flow.get("execution_mode_aliases") or {}).items()}
    require(aliases.get("FLOW_EXTEND") == "FLOW_EXTEND_UI", "GOOGLE_FLOW FLOW_EXTEND alias must resolve to FLOW_EXTEND_UI")

    execution_modes = flow.get("execution_modes") or {}
    ui_mode = execution_modes.get("FLOW_EXTEND_UI") or {}
    vertex_mode = execution_modes.get("FLOW_EXTEND_VERTEX") or {}
    require(str(ui_mode.get("status", "")).upper() == FLOW_READY_STATUS, f"FLOW_EXTEND_UI must be {FLOW_READY_STATUS}")
    require(str(vertex_mode.get("status", "")).upper() == "NEEDS_REVIEW", "FLOW_EXTEND_VERTEX must remain NEEDS_REVIEW")

    expected_ui_plans = {
        8: [8],
        16: [8, 8],
        24: [8, 8, 8],
        32: [8, 8, 8, 8],
        40: [8, 8, 8, 8, 8],
        48: [8, 8, 8, 8, 8, 8],
        56: [8, 8, 8, 8, 8, 8, 8],
    }
    checks: list[str] = []
    for duration, expected_blocks in expected_ui_plans.items():
        plan = build_plan("GOOGLE_FLOW", duration, execution_mode="FLOW_EXTEND_UI")
        actual_blocks = [int(item) for item in plan["block_durations_seconds"]]
        require(plan["status"] == "READY", f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s must resolve READY")
        require(actual_blocks == expected_blocks, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s mismatch: expected {expected_blocks}, got {actual_blocks}")
        require(plan["execution_mode"] == "FLOW_EXTEND_UI", f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s execution_mode drifted")
        require(plan["shared_copywriting_avatar_resolver_payload"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s lost shared copy/avatar payload flag")
        require(plan["requires_previous_clip_final_second"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s must require previous clip final second state")
        require(plan["requires_identity_reanchor"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s missing identity re-anchor requirement")
        require(plan["requires_product_reanchor"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s missing product re-anchor requirement")
        require(plan["wps_budget_mode"] == ("PER_BLOCK" if len(expected_blocks) > 1 else "SINGLE_BLOCK"), f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s WPS mode drifted")
        if len(expected_blocks) > 1:
            require(
                plan["runtime_proof_fields_pending"] == ["previous_clip_final_second_state"],
                f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s must surface pending previous_clip_final_second_state runtime proof",
            )
        for block in plan["blocks"]:
            block_index = int(block["block_index"])
            require(int(block["dialogue_budget_duration_seconds"]) == 8, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block {block_index} must use 8s WPS corridor")
            require(block["requires_identity_reanchor"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block {block_index} missing identity re-anchor")
            require(block["requires_product_reanchor"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block {block_index} missing product re-anchor")
            if block_index == 1:
                require(block["bridge_in_required"] is False, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block 1 must not require bridge-in")
                require(block["requires_previous_clip_final_second"] is False, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block 1 must not require previous clip final second")
            else:
                require(block["bridge_in_required"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block {block_index} missing bridge-in")
                require(block["requires_previous_clip_final_second"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block {block_index} missing previous clip final second requirement")
                require(block["requires_frame_bridge"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block {block_index} missing frame bridge")
                require(block["continuity_goal_required"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block {block_index} missing continuity goal requirement")
            if block_index < len(expected_blocks):
                require(block["bridge_out_required"] is True, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s block {block_index} missing bridge-out")
            else:
                require(block["bridge_out_required"] is False, f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s final block must not require bridge-out")
        checks.append(f"GOOGLE_FLOW FLOW_EXTEND_UI {duration}s -> {'+'.join(str(item) for item in actual_blocks)}")

    alias_plan = build_plan("GOOGLE_FLOW", 16, execution_mode="FLOW_EXTEND")
    require(alias_plan["execution_mode"] == "FLOW_EXTEND_UI", "Deprecated FLOW_EXTEND alias must normalize to FLOW_EXTEND_UI")
    require(alias_plan["block_durations_seconds"] == [8, 8], "Deprecated FLOW_EXTEND alias drifted from FLOW_EXTEND_UI 16s math")
    checks.append("GOOGLE_FLOW FLOW_EXTEND alias -> FLOW_EXTEND_UI")

    vertex_plan = build_plan("GOOGLE_FLOW", 14, execution_mode="FLOW_EXTEND_VERTEX")
    require(vertex_plan["status"] == "NEEDS_REVIEW", "GOOGLE_FLOW FLOW_EXTEND_VERTEX 14s must remain NEEDS_REVIEW")
    require(vertex_plan["block_durations_seconds"] == [7, 7], "GOOGLE_FLOW FLOW_EXTEND_VERTEX 14s must resolve to [7, 7]")
    require(vertex_plan["requires_previous_clip_final_second"] is True, "GOOGLE_FLOW FLOW_EXTEND_VERTEX must require previous clip final second")
    reason = str(vertex_plan.get("reason", "")).lower()
    require("vertex" in reason and "proof" in reason, "GOOGLE_FLOW FLOW_EXTEND_VERTEX reason must explain missing dedicated Vertex proof")
    checks.append("GOOGLE_FLOW FLOW_EXTEND_VERTEX 14s -> 7+7 (NEEDS_REVIEW)")

    try:
        build_plan("GOOGLE_FLOW", 14, execution_mode="FLOW_EXTEND_UI")
        fail("GOOGLE_FLOW FLOW_EXTEND_UI 14s should fail closed")
    except ValueError:
        checks.append("GOOGLE_FLOW FLOW_EXTEND_UI invalid 14s rejected")

    return checks


def validate_flow_10s_contract(engines: dict[str, Any]) -> list[str]:
    """Google Flow 10s extend lane (FLOW_EXTEND_10S) — new dual-lane addition."""
    flow = engines["GOOGLE_FLOW"]
    execution_modes = flow.get("execution_modes") or {}
    ten = execution_modes.get("FLOW_EXTEND_10S") or {}
    require(
        str(ten.get("status", "")).upper() == FLOW_READY_STATUS,
        f"FLOW_EXTEND_10S must be {FLOW_READY_STATUS}",
    )

    expected_plans = {
        10: [10],
        18: [10, 8],
        20: [10, 10],
        30: [10, 10, 10],
        40: [10, 10, 10, 10],
        50: [10, 10, 10, 10, 10],
        60: [10, 10, 10, 10, 10, 10],
    }
    checks: list[str] = []
    for duration, expected_blocks in expected_plans.items():
        plan = build_plan("GOOGLE_FLOW", duration, execution_mode="FLOW_EXTEND_10S")
        actual_blocks = [int(item) for item in plan["block_durations_seconds"]]
        require(plan["status"] == "READY", f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s must resolve READY")
        require(actual_blocks == expected_blocks, f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s mismatch: expected {expected_blocks}, got {actual_blocks}")
        require(all(block in (8, 10) for block in actual_blocks), f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s contains invalid block duration (only 8/10 allowed)")
        require(actual_blocks.count(8) <= 1, f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s must not chain more than one 8s tail")
        require(6 not in actual_blocks, f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s must never use a 6s GROK block")
        require(plan["requires_previous_clip_final_second"] is True, f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s must require previous clip final second")
        require(plan["requires_identity_reanchor"] is True, f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s missing identity re-anchor")
        require(plan["requires_product_reanchor"] is True, f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s missing product re-anchor")
        for block in plan["blocks"][1:]:
            require(block["bridge_in_required"] is True, f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s block {block['block_index']} missing bridge-in")
            require(block["requires_previous_clip_final_second"] is True, f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s block {block['block_index']} missing previous clip final second")
        # Operator writes only engine+duration: the lane must auto-derive to 10s extend.
        default_plan = build_plan("GOOGLE_FLOW", duration)
        require(default_plan["execution_mode"] == "FLOW_EXTEND_10S", f"GOOGLE_FLOW {duration}s default lane must resolve to FLOW_EXTEND_10S")
        require([int(item) for item in default_plan["block_durations_seconds"]] == expected_blocks, f"GOOGLE_FLOW {duration}s default plan mismatch")
        checks.append(f"GOOGLE_FLOW FLOW_EXTEND_10S {duration}s -> {'+'.join(str(item) for item in actual_blocks)}")

    # The 8s chain must keep auto-deriving to FLOW_EXTEND_UI for its own durations.
    for duration, expected_blocks in {8: [8], 16: [8, 8], 24: [8, 8, 8]}.items():
        default_plan = build_plan("GOOGLE_FLOW", duration)
        require(default_plan["execution_mode"] == "FLOW_EXTEND_UI", f"GOOGLE_FLOW {duration}s default lane must stay FLOW_EXTEND_UI")
        require([int(item) for item in default_plan["block_durations_seconds"]] == expected_blocks, f"GOOGLE_FLOW {duration}s 8s-chain default mismatch")
        checks.append(f"GOOGLE_FLOW default {duration}s -> FLOW_EXTEND_UI {expected_blocks}")

    # 38s is COMPUTED, not hand-listed: proves the auto-chainer derives a split
    # for a duration the registry never enumerated.
    ten_table = ten.get("default_total_to_blocks") or {}
    require(38 not in ten_table, "FLOW_EXTEND_10S 38s must be COMPUTED, not hand-listed in default_total_to_blocks")
    plan_38 = build_plan("GOOGLE_FLOW", 38)
    require(plan_38["execution_mode"] == "FLOW_EXTEND_10S", "GOOGLE_FLOW 38s must auto-resolve to FLOW_EXTEND_10S")
    require([int(item) for item in plan_38["block_durations_seconds"]] == [10, 10, 10, 8], "GOOGLE_FLOW 38s must compute [10,10,10,8]")
    require(plan_38["block_durations_seconds"].count(8) == 1, "GOOGLE_FLOW 38s must use exactly one 8s tail")
    require(sum(plan_38["block_durations_seconds"]) == 38, "GOOGLE_FLOW 38s block sum must equal 38")
    checks.append("GOOGLE_FLOW computed 38s -> FLOW_EXTEND_10S [10,10,10,8]")
    return checks


def validate_block_math_reproduces_tables(engines: dict[str, Any]) -> list[str]:
    """Invariant: where both a curated default_total_to_blocks AND block_math
    exist, the computed chain must equal the curated chain for every tabled
    total. This guarantees the table and the computer never drift apart."""
    checks: list[str] = []

    def check_contract(label: str, contract: dict[str, Any]) -> None:
        math_cfg = contract.get("block_math")
        table = contract.get("default_total_to_blocks") or {}
        if not math_cfg or not table:
            return
        primary = int(math_cfg["primary_block_seconds"])
        tail = math_cfg.get("tail_block_seconds")
        tail_max = math_cfg.get("tail_max_count")
        single = {int(x) for x in contract.get("single_clip_durations_seconds", [])}
        for total, curated in table.items():
            total = int(total)
            curated = [int(x) for x in curated]
            if total in single and curated == [total]:
                continue  # single-clip durations are not chained by block_math
            computed = compute_block_durations(
                total,
                primary,
                int(tail) if tail is not None else None,
                int(tail_max) if tail_max is not None else None,
            )
            require(
                computed == curated,
                f"{label} {total}s: block_math computed {computed} != curated {curated}",
            )
        checks.append(f"{label}: block_math reproduces {len(table)} curated split(s)")

    for engine_id, contract in engines.items():
        if "execution_modes" in contract:
            for mode_name, mode_contract in (contract.get("execution_modes") or {}).items():
                check_contract(f"{engine_id}.{mode_name}", mode_contract)
        else:
            check_contract(engine_id, contract)
    return checks


def validate_duration_lane_negatives() -> list[str]:
    """Negative tests: cross-engine block plans must fail closed.

    GROK must never use an 8s block; Google Flow must never use the GROK [10,6]
    split; declared block plans that diverge from the deterministic plan must
    raise StoryboardError instead of compiling.
    """
    checks: list[str] = []
    grok16 = [int(item) for item in build_plan("GROK", 16)["block_durations_seconds"]]
    require(grok16 == [10, 6], f"GROK 16s must remain [10,6], got {grok16}")
    require(8 not in grok16, "GROK 16s must never contain an 8s block")
    flow16 = [int(item) for item in build_plan("GOOGLE_FLOW", 16)["block_durations_seconds"]]
    require(flow16 == [8, 8], f"GOOGLE_FLOW 16s must remain [8,8], got {flow16}")
    require(flow16 != [10, 6], "GOOGLE_FLOW 16s must never be the GROK [10,6] split")
    checks.append("planner guards: GROK16=[10,6] (no 8s), FLOW16=[8,8] (no [10,6])")

    bad_plans = [
        ("GROK 16s [8,8]", "GROK", "16s", [8, 8]),
        ("GOOGLE_FLOW 16s [10,6]", "GOOGLE_FLOW", "16s", [10, 6]),
        ("GOOGLE_FLOW 18s [8,10]", "GOOGLE_FLOW", "18s", [8, 10]),
        ("GOOGLE_FLOW 20s [8,8,4]", "GOOGLE_FLOW", "20s", [8, 8, 4]),
    ]
    for label, engine, duration, declared in bad_plans:
        payload = {
            "template_name": "negative-contract-fixture",
            "product_lane": "BOSMAX",
            "platform": "TikTok",
            "engine": engine,
            "duration": duration,
            "block_plan": declared,
            "hook": "Hook line satu",
            "body": "Body line dua tiga empat lima",
            "cta": "Tap tengok harga",
        }
        template = build_canonical_template(payload, None)
        try:
            build_storyboard(template)
            fail(f"{label} must fail closed (declared plan != deterministic plan)")
        except StoryboardError:
            checks.append(f"{label} rejected (fail-closed)")
    return checks


def validate_dialogue_budget_coverage() -> list[str]:
    bundle = load_registry_bundle()
    expected = [6, 7, 8, 10, 12, 16, 18, 20, 24, 30, 32, 38, 40, 48, 50, 56, 60]
    checks: list[str] = []
    for duration in expected:
        budget = bundle.budgets.get(("BM", "BRISK_UGC", duration))
        require(isinstance(budget, dict), f"Dialogue budget corridor missing BM/BRISK_UGC/{duration}s")
        chain = [
            int(budget["minimum_words"]),
            int(budget["target_min_words"]),
            int(budget["target_max_words"]),
            int(budget["safe_max_words"]),
            int(budget["hard_ceiling_words"]),
        ]
        require(chain == sorted(chain), f"Dialogue budget monotonicity failed for {duration}s: {chain}")
        checks.append(f"budget {duration}s ok")
    return checks


def main() -> None:
    engines = validate_registry_shape()
    grok_checks = validate_grok_contract(engines)
    veo_checks = validate_veo_contract(engines)
    veo_lite_checks = validate_veo31_lite_contract(engines)
    flow_checks = validate_flow_contract(engines)
    flow_10s_checks = validate_flow_10s_contract(engines)
    block_math_checks = validate_block_math_reproduces_tables(engines)
    negative_checks = validate_duration_lane_negatives()
    budget_checks = validate_dialogue_budget_coverage()

    print("VALIDATION PASSED")
    print(f"Video Contract Registry: {CONTRACT_PATH}")
    print(f"Dialogue Budget Registry: {DIALOGUE_BUDGET_PATH}")
    print(f"Handoff Doc: {HANDOFF_DOC_PATH}")
    print(f"Decision Record: {DECISION_DOC_PATH}")
    for item in (
        grok_checks
        + veo_checks
        + veo_lite_checks
        + flow_checks
        + flow_10s_checks
        + block_math_checks
        + negative_checks
        + budget_checks
    ):
        print(item)


if __name__ == "__main__":
    main()
