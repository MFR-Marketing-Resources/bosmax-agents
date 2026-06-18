# BOSMAX Agent Role Inventory
# Version: v1.2
# Authority: BOSMAX Systems Architecture
# Status: ACTIVE — docs-only contract
# Last updated: 2026-06-17
# Changelog v1.1: Added Unit 13 — Final Output Agent (PR #30A)
# Changelog v1.2: Inventory reconcile — backfilled Unit 14 (Dialogue WPS Enforcer)
#                 and Unit 15 (Notion Row Intake Adapter), which existed as skill
#                 files but were unnumbered; added Unit 16 (Market-Angle
#                 Intelligence). Unit count updated 14 → 17.

---

## IMPORTANT: AGENT NATURE

All 17 units listed below are **Claude Code prompt-level skill personas**.
They are `.md` instruction files. They are NOT autonomous runtime processes, NOT deployed containers,
and NOT background services. They execute within a human-initiated Claude Code session only.

---

## UNIT 00 — BOSMAX Orchestrator

| Field | Value |
|-------|-------|
| **File** | `.claude/CLAUDE.md` |
| **Role** | Master orchestrator and command centre for all BOSMAX sessions |
| **Category** | Orchestrator |
| **Trigger** | Loaded automatically at the start of every Claude Code session in this working directory |
| **Inputs** | User requirement, uploaded images/video, Notion raw seed (pasted by operator), session state variables |
| **Outputs** | WORK ORDER dispatched to specialist skill; PRE-FLIGHT validation result; terminal state declaration |
| **Upstream** | User / operator |
| **Downstream** | All specialist skills (Units 01–12); compliance gate (Unit 10) as final terminal |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Version** | Snapshot-driven via `.claude/BOSMAX_CURRENT_STATE.md` (current snapshot v11.11) |
| **Key responsibilities** | VISUAL INTAKE GATE, PRE-FLIGHT PROTOCOL (Steps 0–5), STORYBOARD GATE (video), route determination (A/B/C/D/REG/BULK), WORK ORDER issuance, terminal state enforcement |

---

## UNIT 01 — Requirement Analyst

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-requirement-analyst.md` |
| **Role** | Pre-dispatch intelligence layer — extracts explicit + implicit requirements before route dispatch |
| **Category** | Pre-dispatch intelligence |
| **Trigger** | Appointed by orchestrator when user requirement is ambiguous, new product is detected, or MINI-INTAKE WIZARD is needed |
| **Inputs** | Raw user request, session state, uploaded visuals (if any) |
| **Outputs** | WORK ORDER (structured requirement brief) or BLOCKER (with specific missing input declared) |
| **Upstream** | BOSMAX Orchestrator |
| **Downstream** | BOSMAX Orchestrator (returns WORK ORDER for route dispatch) |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Key responsibilities** | LAYER 0 visual scan, LAYER 1 explicit requirement extraction, LAYER 2 implicit requirement detection (13 IMPLICITs), MINI-INTAKE WIZARD for new products/avatars |
| **Hard rule** | Issues WORK ORDERs only. Does NOT generate content. Does NOT route directly to specialist skills. |

---

## UNIT 02 — Product Intelligence

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-product-intelligence.md` |
| **Role** | Product data resolver — mandatory STEP 0 appointment when any product is mentioned |
| **Category** | Pre-dispatch intelligence |
| **Trigger** | Appointed by orchestrator at PRE-FLIGHT STEP 0 when request mentions a product name, brand, or product code |
| **Inputs** | Product name / brand / product code from user request or visual scan |
| **Outputs** | `product_record` (populated), `scale_anchor_descriptor` (per variant), `copywriting data` (hook, USP 1-3, CTA), `product_copy_router` classification |
| **Upstream** | BOSMAX Orchestrator (STEP 0) |
| **Downstream** | All generation routes — product_record injected before route dispatch |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Lookup hierarchy** | TIER 1: `products/*.yaml` (BOSMAX Registry); TIER 2: FASTMOSS xlsx (manual reference); TIER 3: MINI-INTAKE WIZARD (ask user) |
| **Hard rule** | If platform = TikTok and `scale_anchor_descriptor` is null: WARN and block route dispatch until resolved |

---

## UNIT 03 — Commercial Poster Director

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-commercial-poster-director.md` |
| **Role** | Universal commercial poster prompt elevation engine — converts weak briefs into structured commercial design prompts |
| **Category** | Image prompt specialist |
| **Trigger** | Appointed by orchestrator for ROUTE A poster requests (`image_goal = SELLING_POSTER`) |
| **Inputs** | Product brief, product_record, platform, avatar data, design intent |
| **Outputs** | Structured commercial poster prompt (Full Professional Delivery, Prompt Only, or Variant Pack) |
| **Upstream** | BOSMAX Orchestrator (Route A) |
| **Downstream** | `bosmax-compliance-gate` |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Design contracts** | `docs/design/BOSMAX_COMMERCIAL_POSTER_DESIGN_SKILL_v1.md` (20+ poster mechanics, 15 layout formulas LF-01–LF-15, copy overlay library, product truth lock rules, rejection rules) + `docs/design/BOSMAX_IMAGE_PROMPT_EXPANSION_CONTRACT_v1.md` (12-section full prompt format, expansion rules, Universal Variation Controller) — WIRED in PR 29. |

---

## UNIT 04 — Scene Engine

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-scene-engine.md` |
| **Role** | Mode A image specialist — environment, lighting, camera, and final image prompt assembly |
| **Category** | Image prompt specialist |
| **Trigger** | Appointed by orchestrator at Route A step 2, after `bosmax-subject-dna` returns `subject_dna` JSON |
| **Inputs** | `subject_dna` JSON from bosmax-subject-dna, product_record, platform, image_goal |
| **Outputs** | English Master Image Prompt + `source_image_handoff` JSON (subject_dna + context_environment + lighting_camera) |
| **Upstream** | `bosmax-subject-dna` (Unit 05) |
| **Downstream** | `bosmax-compliance-gate`; `source_image_handoff` then enables Route C for video generation |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Hard rule** | ABORT if `subject_dna` is null or incomplete |
| **Template card schema** | `docs/design/BOSMAX_IMAGE_TEMPLATE_CARD_CONTRACT_v1.md` (28-field schema authority for Mode A image prompt assembly and source_image_handoff outputs, frozen controls, variation axes, product_truth_lock format) — WIRED in PR 29. |

---

## UNIT 05 — Subject DNA

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-subject-dna.md` |
| **Role** | Character visual identity authority — generates the immutable subject_dna JSON for all Mode A image generation |
| **Category** | Image prompt specialist |
| **Trigger** | Appointed by orchestrator at Route A step 1 (before scene engine) |
| **Inputs** | Avatar source (USER_UPLOAD from visual scan, or persona registry: NORA/SARA/RIZAL/AZMAN/etc.), product_record |
| **Outputs** | `subject_dna` JSON block + biometric prose descriptor |
| **Upstream** | BOSMAX Orchestrator (Route A) |
| **Downstream** | `bosmax-scene-engine` (Unit 04) |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Hard rule** | If avatar uploaded via image: extract visual DNA from upload, set `avatar_record.source = "USER_UPLOAD"`. Do NOT substitute registry persona even if operator names one in text. |
| **Does NOT do** | Build scenes, lighting, camera specs, or final prompts — those are scene engine responsibilities |

---

## UNIT 06 — Script Generator

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-script-generator.md` |
| **Role** | Video script specialist — Route B (video from brief) and primary multi-block video prompt engine |
| **Category** | Video prompt specialist |
| **Trigger** | Appointed by orchestrator for Route B (video from brief, no existing image) |
| **Inputs** | Approved storyboard, engine selection, block distribution, WPS budget per block, product_record, avatar_record, platform, language, presentation_route, copy_formula |
| **Outputs** | Full structured video prompt (9-section format or Google Flow block architecture); one prompt per block for multi-block requests |
| **Upstream** | BOSMAX Orchestrator (after storyboard gate approval) |
| **Downstream** | `bosmax-compliance-gate` |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Multi-block rule** | Block N visual start state must match Block N-1 visual end state. Dialogue must continue — no restart between blocks. |

---

## UNIT 07 — Mode C Executor

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-mode-c-executor.md` |
| **Role** | Image-to-video specialist — Route C, derives video prompt from existing Mode A image |
| **Category** | Video prompt specialist |
| **Trigger** | Appointed by orchestrator for Route C (`reference_mode = BOSMAX_IMAGE_HANDOFF`) |
| **Inputs** | `source_image_handoff` JSON (must have `subject_dna`, `context_environment`, `lighting_camera` all non-null); video engine, duration, storyboard |
| **Outputs** | Video prompt structured to maintain visual continuity from the source image |
| **Upstream** | BOSMAX Orchestrator (Route C); `source_image_handoff` produced by bosmax-scene-engine |
| **Downstream** | `bosmax-compliance-gate` |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Hard rule** | ABORT immediately if `source_image_handoff` is null or any of the 3 required fields is null. Do not proceed with partial handoff. |

---

## UNIT 08 — Image Analyst

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-image-analyst.md` |
| **Role** | Route D specialist — reverse engineers uploaded reference images to extract concept DNA for Product B generation |
| **Category** | Analysis / reverse engineering |
| **Trigger** | Appointed by orchestrator when user uploads image + uses keywords: `analisa`, `analisis`, `reverse`, `tiru konsep`, `copy konsep`, `buat macam ni` |
| **Inputs** | Uploaded reference image (Product/Concept A), Product B identity (from product_record), platform |
| **Outputs** | A→B synthesis work order: Subject DNA extracted from A, Product DNA replaced with B, Visual Composition DNA, Hook Pattern, compatibility check results |
| **Upstream** | BOSMAX Orchestrator (Route D) |
| **Downstream** | `bosmax-scene-engine` (for poster) or `bosmax-mode-c-executor` (for video) |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **A→B separation rule** | Concept DNA (visual/structure) borrowed from A. Content DNA (product/copy) replaced entirely with Product B. No brand identity, product name, or copy from A appears in B output. |
| **3-phase structure** | Phase 1: Deconstruct A. Phase 2: Product B Resolution + Compatibility Checks. Phase 3: Synthesis. |

---

## UNIT 09 — Video Analyst

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-video-analyst.md` |
| **Role** | Route D specialist — reverse engineers uploaded reference videos or frames to extract concept DNA for Product B video generation |
| **Category** | Analysis / reverse engineering |
| **Trigger** | Appointed by orchestrator when user uploads video/frames + uses Route D keywords |
| **Inputs** | Uploaded reference video or frames (Product/Concept A), Product B identity, platform, engine selection |
| **Outputs** | A→B video work order: Avatar DNA, Scene DNA, Camera DNA, Script DNA (hook pattern, formula, dialogue skeleton as abstraction), Audio DNA, compatibility check results |
| **Upstream** | BOSMAX Orchestrator (Route D) |
| **Downstream** | `bosmax-script-generator` (with full video work order) |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **A→B separation rule** | Same as image analyst: concept structure borrowed, product/copy identity fully replaced |
| **Formula compatibility** | Check 4 (video-specific): SAVAGE_HPAS formula restrictions enforced; auto-swap if Product B silo incompatible |

---

## UNIT 10 — Compliance Gate

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-compliance-gate.md` |
| **Role** | Fail-closed final quality auditor — terminal step for ALL routes |
| **Category** | QA / compliance |
| **Trigger** | Appointed by orchestrator as the mandatory final step after any specialist skill completes |
| **Inputs** | Output from any specialist skill; product_record; platform; session state |
| **Outputs** | `VERIFICATION PASSED` (output cleared for delivery to user) or `ABORT` (with exact reason declared) |
| **Upstream** | Any specialist skill (Units 03–09, 11, 12) |
| **Downstream** | User (via final output handoff layer — contract defined, skill file pending PR 30) |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Auto-heal registry** | 20+ auto-healable issues: gate resolves minor issues internally without aborting |
| **Hard blocks** | Missing mandatory inputs, failed auto-heal attempts — these always trigger ABORT |
| **Poster QA rubric** | `docs/design/BOSMAX_POSTER_QA_RUBRIC_v1.md` (10 scoring dimensions, 82/100 overall pass gate, 12 hard gates HG-01–HG-12, 15 auto-reject conditions, CBTC definition and detection) — WIRED into Mode A Poster QA Audit section in PR 29. |
| **Key rule** | NEVER output to user without VERIFICATION PASSED. NEVER ABORT for issues in the auto-heal registry. |

---

## UNIT 11 — Bulk Generator

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-bulk-generator.md` |
| **Role** | Bulk content generation specialist — orchestrates high-volume prompt production from a Variant Plan |
| **Category** | Bulk / scale |
| **Trigger** | Appointed by orchestrator for Route BULK when operator requests 10+ output sets |
| **Inputs** | `product_record` (mandatory — must exist before bulk starts), `batch_goal` (IMAGE_ONLY / VIDEO_ONLY / MIXED), `output_count`, `mix` specification |
| **Outputs** | Variant Plan (pending operator approval) → expanded deterministic prompt rows |
| **Upstream** | BOSMAX Orchestrator (Route BULK) |
| **Downstream** | `bosmax-compliance-gate` (per batch output) |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Hard rule** | Variant Plan MUST be approved by operator before any row is expanded. Each row MUST resolve back to a single-output deterministic path. Maximum 50 outputs per run; split larger batches into chunks. |
| **Key rule** | Do NOT invent new prompt grammar. Do NOT generate before Variant Plan is approved. |

---

## UNIT 12 — Product Registration

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-product-registration.md` |
| **Role** | Product registry specialist — registers new products into the BOSMAX YAML registry for future sessions |
| **Category** | Registry management |
| **Trigger** | Appointed by orchestrator for Route REG, or after content generation when operator elects to permanently register a new product discovered during SANDBOX MODE |
| **Inputs** | Product details from operator (name, brand, variants, scale_anchor_descriptor, copywriting data, compliance class, silo class) |
| **Outputs** | New `products/[product_id].yaml` file (or variant addition to existing file); updated `BOSMAX_CURRENT_STATE.md`; append to `BOSMAX-LOG.md` |
| **Upstream** | BOSMAX Orchestrator (Route REG) or operator election after SANDBOX MODE |
| **Downstream** | Product record available for all future sessions as TIER 1 registry entry |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Key rule** | Registration creates a permanent YAML file. Sandbox mode (TIER 3) is session-only and does NOT create a permanent record unless operator explicitly elects Route REG. |

---

## UNIT 13 — Final Output Agent

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-final-output-agent.md` |
| **Role** | Terminal clean-output formatter — converts compliance-passed internal output into operator-ready final delivery |
| **Category** | Final Output / Handoff |
| **Trigger** | Appointed by orchestrator after `bosmax-compliance-gate` returns any terminal state (VERIFICATION PASSED, ABORT, or VERIFICATION PASSED with gaps) |
| **Inputs** | Compliance verdict from `bosmax-compliance-gate`; approved final prompt or abort reason; declared gaps or warnings (if any) |
| **Outputs** | Clean user-facing final delivery: copy-paste prompt block + QA status line + gaps/warnings if present; OR ABORT declaration with resolution instruction |
| **Upstream** | `bosmax-compliance-gate` (Unit 10) |
| **Downstream** | User / operator |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Source authority** | `docs/agents/BOSMAX_FINAL_OUTPUT_HANDOFF_CONTRACT_v1.md` |
| **Hard rules** | NEVER output draft prompt on ABORT. NEVER expose internal metadata, routing notes, debug JSON, or agent chatter. NEVER write to Notion by default. NEVER claim production-ready unless VERIFICATION PASSED received. |
| **Does NOT do** | Audit content (Compliance Gate's job). Generate creative content. Rewrite prompts. Override Compliance Gate. |

---

## UNIT 14 — Dialogue WPS Enforcer

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-dialogue-wps-enforcer.md` |
| **Role** | Universal pre-output dialogue corridor (WPS) hard gate for spoken-dialogue video |
| **Category** | QA / compliance (video dialogue) |
| **Trigger** | Appointed before final video prompt output whenever `dialogue_required = YES` (all spoken-dialogue engines: GROK, GOOGLE_FLOW, VEO family, KLING_3_0, SEEDANCE_2_0) |
| **Inputs** | engine_id, total_duration_seconds, block_plan, block_duration, language, pace_class, dialogue_required, candidate_dialogue_by_block |
| **Outputs** | `PASS` or `BLOCKED` (internal rewrite up to 3 attempts; no audit scaffolding leaks to the final prompt) |
| **Upstream** | `bosmax-script-generator` / STORYBOARD GATE |
| **Downstream** | Final prompt assembly → `bosmax-compliance-gate` |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Authority** | `registries/dialogue_budget_corridor.yaml` (per-block corridor — sole accept/reject authority); `registries/video_engine_duration_contracts.yaml` |
| **Hard rule** | Compliance scrub runs first (medical / infant-adjacent / stealth) → `BLOCKED` with no rewrite. Per-block corridor wins over total-duration budget. Never leak WPS metadata, counts, or status enums into the final prompt. |
| **Inventory note** | Pre-existing skill file backfilled into the inventory in v1.2 (was previously unnumbered). |

---

## UNIT 15 — Notion Row Intake Adapter

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-notion-row-intake-adapter.md` |
| **Role** | Notion Copywriting Landbank row → BOSMAX pipeline bridge; also the append-only delta-CSV governance lane |
| **Category** | Intake / adapter |
| **Trigger** | Front-door detection (before NLU) when input contains 3+ Notion column keys (`Product:` `Mode:` `Angle:` `Hook:` `Subhook:` `USP 1/2/3:` `CTA:` `Visual Seed:` `Output:`), OR a database-growth/append request |
| **Inputs** | Compact Notion row(s) for prompt generation, OR an append/landbank growth request |
| **Outputs** | `notion_row_intake` object for Route A SELLING_POSTER; OR append-mode blocked/delta-CSV guidance with mandatory live-DB proof |
| **Upstream** | BOSMAX Orchestrator front-door (before NLU parsing) |
| **Downstream** | PRE-FLIGHT STEP 0 → Route A SELLING_POSTER flow |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Authority** | `.claude/protocols/notion-csv-append-protocol.md` (PR #51 governance) |
| **Hard rule** | Never treat a row as a final prompt. Enforce canonical product naming, TikTok "Tap" CTA rule, and copy-contamination pre-check. Append jobs require verified live DB state. Never write Notion. |
| **Inventory note** | Pre-existing skill file (added v11.10) backfilled into the inventory in v1.2 (was previously unnumbered). |

---

## UNIT 16 — Market-Angle Intelligence

| Field | Value |
|-------|-------|
| **File** | `.claude/skills/bosmax-market-angle-intelligence.md` |
| **Role** | Opt-in upstream angle intelligence — emits `angle_intelligence_pack` at PRE-FLIGHT STEP 0.5 |
| **Category** | Pre-dispatch intelligence |
| **Trigger** | Opt-in STEP 0.5 (operator asks for angle / market angle / research / competitor / landbank / copy pack / angle bank / hook-subhook-USP-CTA generation), AFTER `product_record` is resolved by Unit 02 |
| **Inputs** | product_record, platform, language, operator_intent, `angle_taxonomy_file`, `competitor_research_policy`, optional operator-supplied competitor source |
| **Outputs** | `angle_intelligence_pack` (source_status, product_context, market_observations, angle_bank, copy_candidates with `overlay_safe_text` + `spoken_dialogue_seed`, forbidden_claims, recommended_next_action) |
| **Upstream** | `bosmax-product-intelligence` (Unit 02, STEP 0) |
| **Downstream** | `bosmax-commercial-poster-director` (overlay_safe_text), `bosmax-script-generator` (spoken_dialogue_seed), PR #51 landbank append (candidate rows only) |
| **Status** | Prompt-level Claude Code persona — NOT autonomous runtime |
| **Authority** | `registries/angle_intelligence_pack.schema.yaml` + `docs/agents/BOSMAX_MARKET_ANGLE_INTELLIGENCE_CONTRACT_v1.md` |
| **Hard rule** | Intelligence only — no final poster prompt, no final video script, no Notion write, no compliance-gate bypass, no product-truth or approved-taxonomy override. Competitor research defaults `NOT_RUN` and is source-gated; never fabricate sources. |

---

## SUMMARY TABLE

| Unit | File | Category | Status |
|------|------|----------|--------|
| 00 | `.claude/CLAUDE.md` | Orchestrator | Prompt-level persona |
| 01 | `bosmax-requirement-analyst.md` | Pre-dispatch intelligence | Prompt-level persona |
| 02 | `bosmax-product-intelligence.md` | Pre-dispatch intelligence | Prompt-level persona |
| 03 | `bosmax-commercial-poster-director.md` | Image prompt specialist | Prompt-level persona |
| 04 | `bosmax-scene-engine.md` | Image prompt specialist | Prompt-level persona |
| 05 | `bosmax-subject-dna.md` | Image prompt specialist | Prompt-level persona |
| 06 | `bosmax-script-generator.md` | Video prompt specialist | Prompt-level persona |
| 07 | `bosmax-mode-c-executor.md` | Video prompt specialist | Prompt-level persona |
| 08 | `bosmax-image-analyst.md` | Analysis / reverse engineering | Prompt-level persona |
| 09 | `bosmax-video-analyst.md` | Analysis / reverse engineering | Prompt-level persona |
| 10 | `bosmax-compliance-gate.md` | QA / compliance | Prompt-level persona |
| 11 | `bosmax-bulk-generator.md` | Bulk / scale | Prompt-level persona |
| 12 | `bosmax-product-registration.md` | Registry management | Prompt-level persona |
| 13 | `bosmax-final-output-agent.md` | Final Output / Handoff | Prompt-level persona |
| 14 | `bosmax-dialogue-wps-enforcer.md` | QA / compliance (video dialogue) | Prompt-level persona |
| 15 | `bosmax-notion-row-intake-adapter.md` | Intake / adapter | Prompt-level persona |
| 16 | `bosmax-market-angle-intelligence.md` | Pre-dispatch intelligence | Prompt-level persona |

**17 units total (Unit 00 orchestrator + Units 01–16 specialist personas). None of the above are autonomous runtime processes. All require a human-initiated Claude Code session.**
