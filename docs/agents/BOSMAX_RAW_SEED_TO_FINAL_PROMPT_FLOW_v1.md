# BOSMAX Raw Seed to Final Prompt Flow
# Version: v1
# Authority: BOSMAX Systems Architecture
# Status: ACTIVE — docs-only contract
# Last updated: 2026-06-08

---

## 1. DEFINITIONS

### What is a Raw Seed?

A raw seed is an **unstructured creative starting point** for a piece of content. It is operator-generated and may include:

- A brief description of the product angle or creative idea
- A hook concept or emotional premise
- A rough scene description
- A reference to a persona or avatar
- A platform target and rough format intent

A raw seed is **not a prompt**. It has not been expanded, polished, or validated. It may contain incomplete fields, informal language, or contradictions. Raw seeds are stored in Notion for operator reference.

**Examples of raw seeds:**
```
"Bosmax Serum 5ml — tunjuk mak muda pakai dalam lift, nampak glowing, TikTok 10s"
"MWCB — wanita professional bekerja, serum pagi, office background, Shopee banner"
"Coffee product — UGC style, lepas bangun pagi, 15s GROK, BM dialog"
```

### What is a Final Prompt?

A final prompt is a **deployment-ready, compliance-passed instruction** delivered to the operator for direct copy-paste into an image or video generator. It has been:

- Expanded from the raw seed by specialist BOSMAX skills
- Validated against product_record (product truth, scale anchor, compliance class)
- Audited by bosmax-compliance-gate (VERIFICATION PASSED)
- Formatted for the specific engine (GROK, VEO_3_1_LITE, KLING_3_0, NANO_BANANA_PRO, etc.)

A final prompt is **not a seed**. It cannot be treated as a raw creative idea — it is the terminal output of the BOSMAX system and is ready to be submitted directly to the image/video generator.

**Key rule: Final prompts do not go back into Notion as source of truth.**
Final prompts may be saved in Notion for operator reference only. They are never used as inputs to another generation pass without being re-processed through BOSMAX.

---

## 2. NOTION'S ROLE IN THIS FLOW

```
NOTION STORES:                          NOTION DOES NOT STORE:
  ✅ Raw creative seeds                   ❌ Final expanded prompts (as source of truth)
  ✅ Product/copy reference data          ❌ QA audit results (compliance gate output)
  ✅ Avatar reference notes               ❌ System SOP rules
  ✅ Template card references             ❌ Engine configuration data
  ✅ Operator workflow notes              ❌ Registry data (products/*.yaml is authority)
```

Notion is the operator's **input scratchpad and output reference viewer**. The BOSMAX repo is the system truth.

---

## 3. END-TO-END FLOW

### Master Flow (all routes)

```
STEP 0: INPUT
  ├─ Operator retrieves raw seed from Notion (or types requirement directly)
  └─ Operator pastes into Claude Code session

STEP 1: VISUAL INTAKE GATE (if image/video uploaded)
  → BOSMAX scans uploaded visuals before any other processing
  → Extracts: avatar DNA from image, product name from label, scene context
  → Sets: avatar_record.source = "USER_UPLOAD" if human detected
  → Visual evidence overrides all text and session memory
  → Declares scan results to operator; asks only if genuinely unclear

STEP 2: PRE-FLIGHT PROTOCOL
  ├─ STEP 0: Product Intelligence Lookup
  │    → TIER 1: products/*.yaml
  │    → TIER 2: FASTMOSS xlsx (manual reference)
  │    → TIER 3: MINI-INTAKE WIZARD (new product only)
  │    → Populates: product_record, scale_anchor_descriptor, copywriting data
  │    → HARD BLOCK: TikTok + scale_anchor_descriptor null → warn + wait
  │
  ├─ STEP 0.5: Market Angle Intelligence (OPT-IN — bosmax-market-angle-intelligence)
  │    → Runs only on angle/research/competitor/landbank/copy-pack triggers,
  │      after STEP 0 product_record is resolved
  │    → TIER 1: loads product_record.angle_taxonomy_file if present (approved wins)
  │    → Competitor research DEFAULT NOT_RUN; source-gated; never fabricated
  │    → Emits: angle_intelligence_pack (overlay_safe_text for poster,
  │      spoken_dialogue_seed for video, forbidden_claims, landbank candidate rows)
  │    → No final creative; no Notion write; never bypasses compliance gate
  │
  ├─ STEP 1: Extract Requirements
  │    → req_platform, req_task_mode, req_engine, req_duration, etc.
  │
  ├─ STEP 2: Validate All Fields
  │    → Platform, engine, duration vs engine max, Mode C prerequisites,
  │      BULK prerequisites, Google Flow image counts
  │
  ├─ STEP 3: Multi-Block Protocol (if duration > engine max)
  │    → MASTER NARRATIVE BRIEF built and presented to operator
  │    → Operator approves before skill dispatch
  │
  ├─ STEP 4: Implicit Requirement Detection
  │    → 13 IMPLICITs detected automatically
  │
  └─ STEP 5: WORK ORDER issued

STEP 3: STORYBOARD GATE (video requests only)
  → Engine selection confirmed
  → Block math resolved
  → per-block WPS budget resolved from registry
  → presentation route resolved
  → storyboard beats allocated by block duration
  → exact dialogue draft written per block
  → dialogue word count audited per block
  → Master storyboard built and presented to operator
  → Only dispatch to script-generator after WPS passes
  → Operator approves before skill dispatch

STEP 4: ROUTE → SPECIALIST SKILL CHAIN
  → (see per-route flow below)

STEP 5: COMPLIANCE GATE
  → bosmax-compliance-gate audits skill output
  → Auto-heal minor issues
  → VERIFICATION PASSED or ABORT

STEP 6: FINAL OUTPUT HANDOFF
  → [Contract defined in BOSMAX_FINAL_OUTPUT_HANDOFF_CONTRACT_v1.md]
  → [Skill file pending PR 30]
  → Final clean prompt delivered to operator

STEP 7: GENERATOR RENDER
  → Operator copies final prompt to image/video generator
  → Generator renders; BOSMAX has no further role
```

---

## 4. PER-ROUTE FLOW

### Image Flow — Route A

```
INPUT: Raw seed / product brief + platform + image_goal
  ↓
bosmax-subject-dna
  → Inputs:  avatar source (USER_UPLOAD or registry persona), product_record
  → Outputs: subject_dna JSON + biometric prose
  ↓
bosmax-scene-engine
  → Inputs:  subject_dna JSON, product_record, platform, image_goal
  → Outputs: English Master Image Prompt + source_image_handoff JSON
  [+ bosmax-commercial-poster-director for SELLING_POSTER requests]
  → Inputs:  product brief, product_record, platform, design intent
  → Outputs: Structured commercial poster prompt
  ↓
bosmax-compliance-gate
  → VERIFICATION PASSED or ABORT
  ↓
[Final Output Handoff — pending PR 30]
  ↓
USER receives final image prompt → pastes into image generator → render
```

**Fail-closed points:**
- `subject_dna` null → scene engine ABORTS
- `product_record` null → orchestrator BLOCKS route dispatch
- `scale_anchor_descriptor` null + TikTok → WARN and HOLD

### Video Flow — Route B (from brief)

```
INPUT: Raw seed / product brief + engine + duration + platform + language
  ↓
PRE-FLIGHT (engine validation, duration vs max, multi-block check)
  ↓
STORYBOARD GATE (engine confirmed, block math, per-block WPS, exact dialogue draft, word count audited, storyboard approved)
  ↓
bosmax-script-generator
  → Inputs:  approved storyboard, block distribution, per-block WPS corridor, presentation route, exact dialogue draft, product_record, avatar_record
  → Outputs: N × full structured video prompt (9-section or Google Flow format)
  ↓
bosmax-compliance-gate
  → VERIFICATION PASSED or ABORT
  ↓
[Final Output Handoff — pending PR 30]
  ↓
USER receives final video prompt(s) → pastes into video generator → render
```

**Fail-closed points:**
- Engine not in ENGINE CONSTRAINT TABLE → ABORT
- Duration not in engine's `allowed_durations` → ABORT
- Storyboard not approved → skill dispatch blocked
- Any dialogue block below corridor minimum or above hard ceiling → dispatch blocked until rewritten and word count audited
- Block N dialogue restarts instead of continuing from Block N-1 → compliance ABORT

### Video Flow — Route C (image to video)

```
INPUT: source_image_handoff JSON from completed Route A session + engine + duration
  ↓
PRE-FLIGHT (source_image_handoff validation: 3 fields must all be non-null)
  ↓
STORYBOARD GATE
  ↓
bosmax-mode-c-executor
  → Inputs:  source_image_handoff (locked, immutable), engine, storyboard
  → Outputs: Video prompt maintaining visual continuity from source image
  ↓
bosmax-compliance-gate
  → VERIFICATION PASSED or ABORT
  ↓
[Final Output Handoff — pending PR 30]
  ↓
USER receives final video prompt → pastes into video generator → render
```

**Fail-closed points:**
- `source_image_handoff` null → immediate ABORT, inform operator Mode A must complete first
- Any of the 3 handoff fields null → ABORT

### Analysis Flow — Route D

```
INPUT: Uploaded reference image OR video/frames + Route D keywords
  ↓
bosmax-image-analyst OR bosmax-video-analyst
  Phase 1: Deconstruct reference (extract concept DNA from A)
  Phase 2: Product B resolution + compatibility checks
  Phase 3: Synthesis (A→B work order)
  [A→B separation: concept structure from A, product/copy from B only]
  ↓
  → image analyst routes to: bosmax-scene-engine (poster) or bosmax-mode-c-executor (video)
  → video analyst routes to: bosmax-script-generator (with full work order)
  ↓
bosmax-compliance-gate
  → VERIFICATION PASSED or ABORT
  ↓
[Final Output Handoff — pending PR 30]
  ↓
USER receives final prompt → pastes into generator → render
```

**Fail-closed points:**
- No Product B product_record → analyst HOLDS pending product resolution
- Silo incompatibility (A vs B) → auto-adapt with declared change
- SAVAGE_HPAS formula + DIRECT silo product → auto-swap formula

### Batch Flow — Route BULK

```
INPUT: Product brief + batch_goal + output_count + mix specification
  ↓
PRE-FLIGHT (product_record mandatory before bulk opens; batch fields validated)
  ↓
bosmax-bulk-generator
  Step 1: Receive product record
  Step 2: Determine batch type
  Step 3: Build Variant Plan (presented to operator — OPERATOR MUST APPROVE)
  Step 4: [After approval] Expand each row via deterministic single-output path
  ↓
bosmax-compliance-gate (per batch output)
  → VERIFICATION PASSED or ABORT per row
  ↓
[Final Output Handoff — pending PR 30]
  ↓
USER receives batch of final prompts → copy each to generator → render
```

**Fail-closed points:**
- `product_record` null at batch start → redirect to Route REG first
- Variant Plan not approved → no rows expanded
- Output count > 50 → split into chunks, no single-pass override
- Row fails compliance → ABORT that row, continue others, declare failures in batch summary

---

## 5. WHAT NEVER ENTERS THIS FLOW FROM NOTION

The following must NEVER be used as system inputs from Notion:
- Final prompts from previous sessions (re-process through BOSMAX instead)
- QA scores or compliance verdicts (compliance gate re-audits every time)
- Engine configuration overrides (ENGINE CONSTRAINT TABLE in CLAUDE.md is authority)
- Product truth (products/*.yaml is the authority; Notion product notes are informal reference only)

---

## 6. TERMINAL STATES

| State | Trigger | Resolution |
|-------|---------|-----------|
| `VERIFICATION PASSED` | Compliance gate approves all checklist items | Deliver final prompt to operator |
| `ABORT` | Hard block triggered (missing input, failed auto-heal, compliance violation) | State exact reason; operator resolves; session continues or restarts |
| `NEEDS USER CLARIFICATION` | Single targeted question from orchestrator | Operator answers; flow resumes |
| `PENDING STORYBOARD APPROVAL` | Storyboard presented to operator; awaiting response | Operator approves or requests edits; flow resumes |
| `PENDING VARIANT PLAN APPROVAL` | Bulk Variant Plan presented; awaiting response | Operator approves or edits; bulk expansion begins |
