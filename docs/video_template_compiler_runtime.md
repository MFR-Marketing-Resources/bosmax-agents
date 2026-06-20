# Video Template Compiler Runtime

## Purpose

`video_template_compiler_runtime` is the governed BOSMAX runtime lane for:

- template parsing and normalization
- master storyboard generation
- deterministic block-script generation
- engine-specific prompt compilation
- QA validation
- Notion-ready parent/child export

This lane does not authorize production prompt generation at scale.  
`100-row Notion generation remains blocked until 10-row pilot passes.`

## Pipeline

1. `scripts/video_template_parser.py`
   - accepts YAML, JSON, or key:value text
   - normalizes product lane, engine, mode, duration, execution mode, and block plan
   - preserves `raw_prompt_seed` as a separate export surface
2. `scripts/video_storyboard_builder.py`
   - validates BOSMAX planner math against `scripts/video_block_plan.py`
   - builds `master_storyline`, `master_storyboard`, continuity locks, and `block_script_json`
3. `scripts/video_prompt_compiler.py`
   - compiles block scripts into engine-adapted final prompt text plus structured `prompt_sets[]`
   - emits `output_mode`, `prompt_set_count`, and one complete 9-section prompt per block
   - blocks unsafe claims, internal marker leakage, missing multi-block continuity, collapsed multi-block output, and WPS overflow
4. `scripts/build_batch_video_prompts.py`
   - exports compiled parent/child Notion-ready rows while preserving the legacy batch exporter contract

## Supported Runtime Surface

- Single block:
  - `GROK` 6s and 10s
  - `VEO_3_1` 4s, 6s, 8s
  - `VEO_3_1_LITE` 8s
  - `GOOGLE_FLOW` 8s via `FLOW_EXTEND_UI`; 10s via `FLOW_EXTEND_10S`
- Multi-block:
  - `GROK` `[10,6]`, `[10,10]`, `[6,6]`, `[6,6,6]`, `[10,10,10]`
  - `VEO_3_1` `[8,8]`, `[8,8,8]`, and longer BOSMAX clip-chain arrays
  - `VEO_3_1_LITE` `[8,8]`, `[8,8,8]`, and longer BOSMAX clip-chain arrays
  - `GOOGLE_FLOW` 8s chain (`FLOW_EXTEND_UI`): `[8,8]`, `[8,8,8]`, and longer 8s arrays
  - `GOOGLE_FLOW` 10s extend (`FLOW_EXTEND_10S`): `[10,8]` (18s), `[10,10]` (20s),
    `[10,10,10]` (30s), `[10,10,10,10]` (40s), `[10,10,10,10,10]` (50s),
    `[10,10,10,10,10,10]` (60s)

## Unsupported Plans

- `[4,4,4,4]` is explicitly blocked in this lane.
- Any declared block plan that diverges from `scripts/video_block_plan.py` fails closed.

## Multi-Prompt Set Law

Whenever `block_count > 1`, the compiler must emit:

- `output_mode = MULTI_PROMPT_SET`
- `prompt_set_count = block_count`
- `prompt_sets.length = block_count`
- one complete 9-section prompt set per block

The compiler must fail closed if a multi-block runtime collapses into one
combined prompt surface, hides split timing inside a single prompt, or drifts
GROK 16s away from `[10,6]` or GOOGLE_FLOW 16s away from `[8,8]`.

For Google Flow continuation sets, the compiled prompt must spell out:

- `Previous clip final second state: ...`
- `Continue from that exact state into ...`
- `Continuity seam instruction: ...`

and it must keep product position / label / scale, avatar identity / wardrobe /
pose, scene / lighting / camera direction, and commercial chronology locked
across the seam.

## Mode Semantics

`mode` (compiler seed-authoring style) is distinct from `intake_mode` (operator
asset-intake pattern). Do not conflate them.

- `FRAMES`
  - visual-seed-first commercial framing
  - dialogue stays concise and camera continuity is explicit
- `INGREDIENTS`
  - seed/material list orientation
  - compiler still emits runtime-safe final prompt surfaces
- `HYBRID`
  - combines visual framing and structured ingredient cues
  - useful for clip-chain proof arcs where both scene and product behavior must stay locked

## Intake Mode Semantics

`intake_mode` is the optional operator-facing asset-intake pattern. Input
aliases normalize to canonical values:

- `PRODUCT_ONLY` (alias `HYBRID`) — product image only; avatar from pool /
  description; scene, action, and dialogue described in the raw template.
- `READY_FRAME` (alias `FRAMES`) — one finished frame (avatar + product + scene);
  continue / animate the frame; action and dialogue continuation only; no scene
  rebuild.
- `ASSET_SET` (alias `INGREDIENTS`) — multiple role-mapped images; product truth
  outranks avatar and style.

The operator supplies engine + duration + intake_mode (plus creative detail);
the runtime derives `block_plan`. Operators never hand-author `block_plan`,
child block rows, or `final_prompt_text`.

## Engine Notes

- `GROK`
  - extension-first seam logic
  - no greeting reset on extension blocks
  - continuity must resume within the BOSMAX seam window
- `GOOGLE_FLOW`
  - dual deterministic lanes that never mix in one render:
    - `FLOW_EXTEND_UI` (8s chain): 8, 16=[8,8], 24=[8,8,8]
    - `FLOW_EXTEND_10S` (10s extend): 10, 18=[10,8], 20=[10,10], 30/40/50/60 repeated 10s
  - lane is auto-derived from duration; 40s is overlap-resolved to the 10s lane
    via the registry `default_total_lane` override
  - must never use the GROK [10,6] split
  - chronological continuation only
  - previous-clip-final-second state must be explicit for non-first blocks
  - avoid vague shorthand such as “same as last frame”
- `VEO_3_1` / `VEO_3_1_LITE`
  - clip-chain continuity
  - preserve identity, packaging scale, label readability, and scene family block-to-block

## QA Gates

Compilation fails when any of the following appear:

- cure or medical-treatment claims
- guaranteed-result claims
- sexual-performance claims
- risky direct-body-use instructions
- internal markers such as `CTX_`, `DNA_`, `BLOCK_`, `SCENE_`, `IMG_`, `VID_`
- internal orchestration / budget scaffolding inside the engine-facing prompt body —
  `key=value` tokens (`output_mode=`, `block_source=`, `dialogue_word_count=`,
  `safe_max_words=`, `dialogue_budget_status=`, `target_min_words=`, `target_max_words=`)
  or set-sequencing narration (`Runtime plan`, `Do not compile as one`,
  `Do not use two equal`, `multi-prompt sequence`)
- an English / internal storyboard label code-switched into a BM spoken line
  (for example `family shelf`, `shelf cue`, `b-roll`)
- missing multi-block `master_storyboard`
- dialogue word count above block `safe_max_words` (overfill)
- dialogue word count below block `minimum_words` (underfill) — this BLOCKS readiness
  (`REWRITE_REQUIRED`); underfilled dialogue opens dead air the model fills with
  hallucinated drift/glitch, so it is no longer a non-blocking warning
- multi-block output presented as a single prompt instead of `MULTI_PROMPT_SET`
- overlay / subtitle / on-screen-text instructions in seed or storyboard surfaces
  when `parsed.overlay_allowed` is not explicitly set (Section 9 defaults to NO_OVERLAY)

Warnings (non-blocking) are emitted for target-range-miss dialogue (within
`[minimum_words, safe_max_words]` but outside `[target_min_words, target_max_words]`)
and when `presenter_route` was defaulted rather than set explicitly.

## Presenter Route (lip-sync vs voiceover)

`presenter_route` decides whether a speaking video renders an on-camera presenter
(lip-sync applies) or a faceless product clip with voiceover (no mouth, lip-sync
N/A). It is distinct from `intake_mode`: a `PRODUCT_ONLY` intake can still render a
presenter because the avatar comes from pool / description.

- `PRESENTER_FULL` — on-camera presenter speaks every line straight to camera with
  frame-accurate lip-sync.
- `PRESENTER_HYBRID` — presenter speaks to camera with lip-sync; product-hero
  cutaways keep the same line as tightly synced voice.
- `PRODUCT_ONLY_VO` — faceless product-only visuals with voiceover narration;
  lip-sync is not applicable.

A dialogue video with no `presenter_route` set defaults to `PRESENTER_HYBRID`
(lip-sync) and emits a warning. A faceless voiceover clip must opt in with
`PRODUCT_ONLY_VO` explicitly — the runtime never silently turns a speaking video
into a faceless voiceover.

## Notion Export Contract

Compiled exports produce:

- parent rows
  - `template_id`
  - `template_name`
  - `product_lane`
  - `engine`
  - `mode`
  - `duration`
  - `block_mode`
  - `block_count`
  - `block_plan`
  - `output_mode`
  - `prompt_set_count`
  - `raw_prompt_seed`
  - `master_storyline`
  - `master_storyboard`
  - `final_prompt_text`
  - `qa_status`
  - `production_ready`
  - `notion_ready`
  - `copywriting_landbank_row_id`
  - `commercial_angle_id`
  - `commercial_angle_name`
  - `hook`
  - `body_copy`
  - `cta`
  - `risk_class`
  - `claim_class`
  - `platform`
  - `pilot_batch`

  The parent CSV uses `template_id` as the import key; the legacy
  `parent_row_id` duplicate column is no longer emitted. The first 18 fields
  are the compiler-owned spine; the trailing 10 are copywriting landbank
  traceability metadata (blank when the input seed does not supply them). The
  child CSV is unchanged.
- child rows
  - `parent_template_id`
  - `block_id`
  - `block_duration`
  - `set_role`
  - `continuation_from_previous_set`
  - `narrative_function`
  - `visual_action`
  - `dialogue_or_copy`
  - `wps_budget`
  - `safe_max_words`
  - `dialogue_budget_status`
  - `start_state`
  - `end_state`
  - `continuity_anchor`
  - `final_prompt_block_text`
  - `qa_status`

## External Compiler Worker Contract

`scripts/notion_video_prompt_worker.py` is the governed bridge between the live
Notion operator rows and this runtime lane.

It owns exactly three responsibilities:

1. read one READY row or a READY queue from `BOSMAX_VIDEO_PROMPT_RUNS`
2. resolve the selected authority relations
   - `Product`
   - `Engine Rule`
   - `Angle`
   - `Avatar AI` (optional)
   - exactly one copy pack lane
3. compile and write back:
   - `RAW_PROMPT_COMPILED`
   - `FINAL_OUTPUT_9_SECTION`
   - compiler status / QA fields

### Live queue entry rule

The worker only accepts rows when all of the following are true:

- `Compiler Method = EXTERNAL_COMPILER`
- `Output Reactivity = SYSTEM_WRITTEN_OUTPUT`
- `Compiler Output Status = READY_TO_COMPILE`
- authority relations are selected; manual fallback fields are empty

Mode-specific gates:

- `HYBRID`
  - `Product Reference Provided = true`
- `FRAMES`
  - `Frame Provided = true`
- `INGREDIENTS`
  - `Product Reference Provided = true`
  - `Asset Roles Verified = true`
  - if `Avatar AI` is selected, `Avatar Reference Provided = true`

### Writeback ownership

The worker writes:

- `Compiler Contract Version = BOSMAX_EXT_COMPILER_WORKER_v1.0`
- `Compiler Job ID`
- `Compiler Input Snapshot`
- `RAW_PROMPT_COMPILED`
- `FINAL_OUTPUT_9_SECTION`
- `Compiler Output Notes`
- `Compiler Error`
- `Compiler Output Status`
- `Prompt Status`
- `COMPILER_QA_STATUS`

State mapping:

- compile start
  - `Compiler Output Status = SENT_TO_COMPILER`
  - `Prompt Status = Sent to Compiler`
- compile success with no QA warnings
  - `Compiler Output Status = QA_PASSED`
  - `Prompt Status = Final Received`
  - `COMPILER_QA_STATUS = PASSED`
- compile success with warnings but no hard QA errors
  - `Compiler Output Status = COMPILED`
  - `Prompt Status = Final Received`
  - `COMPILER_QA_STATUS = REVIEW`
- blocked / failed
  - `Compiler Output Status = BLOCKED` or `QA_FAILED`
  - `Prompt Status = Failed`
  - `COMPILER_QA_STATUS = FAILED`

### Runtime commands

Single offline snapshot proof:

```bash
python scripts/notion_video_prompt_worker.py ^
  --snapshot tests/video_template_compiler/notion_worker_snapshot_bosmax.json
```

Single live row:

```bash
set NOTION_API_TOKEN=secret_xxx
python scripts/notion_video_prompt_worker.py --run-page-id <page-id>
```

READY queue sweep:

```bash
set NOTION_API_TOKEN=secret_xxx
python scripts/notion_video_prompt_worker.py ^
  --data-source-id 537c35a1-fd7a-453a-909b-eeb839b6b979 ^
  --page-size 10
```

## Validators

Run these from repo root:

```bash
python scripts/validate_video_template_schema.py
python scripts/validate_video_prompt_compiler.py
python scripts/validate_video_template_export_readiness.py
python scripts/validate_notion_video_prompt_worker.py
```

Recommended repo-wide evidence checks:

```bash
npx tsx scripts/mandor-check.ts
npx @biomejs/biome check .
npx dependency-cruiser . --no-config --output-type err
```
