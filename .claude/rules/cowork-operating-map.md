---
paths:
  - ".claude/skills/*.md"
  - "products/*.yaml"
  - "BOSMAX_*_v1.md"
---

# Cowork Operating Map

This rule loads when working on BOSMAX skills, product registry files, or authority files.

## Primary Surfaces

- First read surface: `.claude/BOSMAX_CURRENT_STATE.md`
- Historical audit surface: `.claude/BOSMAX-LOG.md`
- Product authority surface: `products/*.yaml`

## Required Skill Files

The BOSMAX Cowork surface expects these files to exist in `.claude/skills/`:

1. `bosmax-compliance-gate.md`
2. `bosmax-subject-dna.md`
3. `bosmax-scene-engine.md`
4. `bosmax-mode-c-executor.md`
5. `bosmax-script-generator.md`
6. `bosmax-product-registration.md`
7. `bosmax-bulk-generator.md`
8. `bosmax-requirement-analyst.md`
9. `bosmax-product-intelligence.md`
10. `bosmax-image-analyst.md`
11. `bosmax-video-analyst.md`
12. `bosmax-commercial-poster-director.md`
13. `bosmax-notion-row-intake-adapter.md`  ← ADDED v11.10: Notion row → pipeline bridge
14. `bosmax-final-output-agent.md`
15. `bosmax-dialogue-wps-enforcer.md`
16. `bosmax-market-angle-intelligence.md`  ← ADDED v11.11: opt-in STEP 0.5 angle intelligence (Unit 16)

## Template Files — Active

| File | Status | Role |
|---|---|---|
| `templates/poster/03A-P1_PRODUCT_ONLY_COPY_LANDBANK_POSTER.md` | **ACTIVE** | Authoritative assembly format for Minyak Warisan Tok Cap Burung 25ml product-only poster. Defines input contract, product truth lock, 5 inline visual presets, copy injection rules, overlay zone hierarchy, compliance guardrails, negative lock, full prompt assembly format, and QA checklist. Reference when building 03A product-only poster prompts. NOT a template skeleton — it defines the FORMAT standard. |

Sibling templates (not yet built): `03A-P2` (avatar+product), `03A-P3` (copy swap).

## Product Registry Notes

- `products/_SCHEMA.yaml` is the schema reference
- each live product authority sits in its own YAML file
- `scale_anchor_descriptor` remains mandatory per variant
- do not duplicate product truth into orchestration prose

## Pipeline Sequences

```text
Opt-in Market Angle Intelligence (PRE-FLIGHT STEP 0.5) — feeds poster/video/landbank:
User (asks for angle/research/competitor/landbank/copy pack)
  -> BOSMAX [PRE-FLIGHT STEP 0: bosmax-product-intelligence -> product_record]
  -> BOSMAX [PRE-FLIGHT STEP 0.5: bosmax-market-angle-intelligence]
        (loads angle_taxonomy_file as TIER 1; competitor_research default NOT_RUN)
  -> emit angle_intelligence_pack  (intelligence only — NO final creative)
  -> downstream consumption:
       poster route   -> bosmax-commercial-poster-director (overlay_safe_text)
       video route    -> bosmax-script-generator (spoken_dialogue_seed)
       landbank route -> recommended_next_action.notion_landbank_ready_rows
                         (candidate rows only; PR #51 governance is the sole writer)
  -> bosmax-compliance-gate still audits ALL final creative (never bypassed)

NOTE: STEP 0.5 is opt-in only and never sits in the mandatory STEP 0 hot path.
      Approved taxonomy wins over generated packs; REVIEW_ONLY stays REVIEW_ONLY.
      Packs are session_only by default; persisted to registries/angle_packs/<product_id>.yaml
      only on explicit operator promotion after audit.

Full Image Pipeline (Notion Row → SELLING_POSTER):
Notion Row -> BOSMAX [NOTION ROW DETECTION] -> bosmax-notion-row-intake-adapter
          -> BOSMAX [PRE-FLIGHT STEP 0: product lookup with canonical name]
          -> bosmax-subject-dna
          -> bosmax-commercial-poster-director (selected_module_stack)
          -> bosmax-scene-engine [ingests subject_dna + module_stack
                                  + copywriting.subhook + operator_scene_direction]
          -> bosmax-compliance-gate -> bosmax-final-output-agent -> User

NOTE: Notion rows supply: hook, subhook, USP 1/2/3, CTA, Visual Seed, Angle.
      BOSMAX supplies: product truth, image_prompt_locks, compliance, layout, assembly.
      Notion does NOT need to store prompt instructions — only structured copy data.

Full Image Pipeline (VIDEO_SUPPORT):
User -> BOSMAX [PRE-FLIGHT] -> bosmax-subject-dna
     -> bosmax-scene-engine
     -> bosmax-compliance-gate -> bosmax-final-output-agent -> User

Full Image Pipeline (SELLING_POSTER):
User -> BOSMAX [PRE-FLIGHT] -> bosmax-subject-dna
     -> bosmax-commercial-poster-director (selected_module_stack)
     -> bosmax-scene-engine [ingests subject_dna + selected_module_stack]
     -> bosmax-compliance-gate -> bosmax-final-output-agent -> User

NOTE: bosmax-scene-engine must NOT be called for SELLING_POSTER until
selected_module_stack is non-null. ABORT if selected_module_stack is null.

Full Video Pipeline (Mode B, single block):
User -> BOSMAX [PRE-FLIGHT] -> bosmax-script-generator
     -> bosmax-compliance-gate -> bosmax-final-output-agent -> User

Full Video Pipeline (Mode B, multi-block):
User -> BOSMAX [PRE-FLIGHT: MULTI-BLOCK TRIGGERED]
     -> BOSMAX [MASTER NARRATIVE BRIEF -> user approval]
     -> bosmax-script-generator [Block 1..N]
     -> bosmax-compliance-gate
     -> bosmax-final-output-agent -> User

Full Video Pipeline (Mode C):
User -> BOSMAX [PRE-FLIGHT] -> bosmax-mode-c-executor
     -> bosmax-compliance-gate -> bosmax-final-output-agent -> User

Full Product + Bulk Pipeline:
User -> BOSMAX [PRE-FLIGHT] -> bosmax-product-registration
     -> BOSMAX [PRE-FLIGHT] -> bosmax-bulk-generator
     -> bosmax-compliance-gate -> bosmax-final-output-agent -> User
```
