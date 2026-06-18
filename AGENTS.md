# BOSMAX Codex Bridge — AGENTS.md

## Authority

This file is a Codex bridge only.

Canonical BOSMAX orchestrator authority lives in:
- `.claude/CLAUDE.md`

If this file conflicts with `.claude/CLAUDE.md`, the canonical winner is always:
- `.claude/CLAUDE.md`

## Live Repo Truth Map

Use these surfaces as the live deterministic path for BOSMAX work:
- Orchestrator and route logic: `.claude/CLAUDE.md`
- Specialist execution skills: `.claude/skills/`
- Video prompt quality gate (4 defects, deterministic check before Notion): `BOSMAX_VIDEO_PROMPT_QUALITY_GATE_HANDOFF_v1.md` + `scripts/validate_final_video_prompt_text.py`
- Product registry and scale anchors: `products/*.yaml`
- Product schema contract: `products/_SCHEMA.yaml`
- Dialogue authority for sensitive products: `SCRIPT_REGISTRY_UNIFIED.md` + `SCRIPT_VARIANT_LIBRARY.md`
- Session memory and authority trail: `.claude/BOSMAX-LOG.md`
- Prompt framework rules still consumed by live skills: `Prompt_Framework_v1_STRICT.yaml`
- Platform, model-behaviour, and visual strict layers: `Platform_Specs_v1_STRICT.yaml`, `Model_Behaviour_v1_STRICT.yaml`, `Visual_Language_v1_STRICT.yaml`

## Non-Canonical Files

The following files are not canonical truth sources:
- `BOSMAX_ANALYSIS_REPORT_v1.md`
- `BOSMAX_CONFLICT_REGISTER_v1.md`
- `CODEX_REPAIR_PROMPT_v1.md`

Treat them as audit artifacts, working notes, or decision-support documents only.
Do not promote their contents into live authority unless the repo is explicitly patched to do so.

## Fail-Closed Rules

- Do not duplicate engine constraints in this file.
- Do not resolve engine conflicts from audit artifacts alone.
- Do not treat dormant tiers as live runtime authority unless a live skill or `.claude/CLAUDE.md` explicitly consumes them.
- Before patching BOSMAX logic, check the real live path rather than assuming every top-level spec file is active.

## Execution Posture For Codex

- Read `.claude/CLAUDE.md` first for BOSMAX routing, engine rules, and route semantics.
- Read `.claude/BOSMAX-LOG.md` for recent authority changes before patching.
- When a product is mentioned, treat `products/*.yaml` as Tier 1 truth.
- When a sensitive product uses script-registry dialogue authority, keep `products/*.yaml` as product truth and `SCRIPT_REGISTRY_UNIFIED.md` + `SCRIPT_VARIANT_LIBRARY.md` as dialogue truth.

## Intent Of This Bridge

This file exists to:
- eliminate stale duplicated orchestrator text
- remove corrupted content drift
- point Codex and adjacent agents to the single canonical BOSMAX brain

Do not expand this file back into a second full orchestrator copy unless the architect explicitly requests dual-surface maintenance.
