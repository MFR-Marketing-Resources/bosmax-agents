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
   - compiles block scripts into engine-adapted final prompt text
   - blocks unsafe claims, internal marker leakage, missing multi-block continuity, and WPS overflow
4. `scripts/build_batch_video_prompts.py`
   - exports compiled parent/child Notion-ready rows while preserving the legacy batch exporter contract

## Supported Runtime Surface

- Single block:
  - `GROK` 6s and 10s
  - `VEO_3_1` 4s, 6s, 8s
  - `VEO_3_1_LITE` 8s
  - `GOOGLE_FLOW` 8s via `FLOW_EXTEND_UI`
- Multi-block:
  - `GROK` `[10,6]`, `[10,10]`, `[6,6]`, `[6,6,6]`, `[10,10,10]`
  - `VEO_3_1` `[8,8]`, `[8,8,8]`, and longer BOSMAX clip-chain arrays
  - `VEO_3_1_LITE` `[8,8]`, `[8,8,8]`, and longer BOSMAX clip-chain arrays
  - `GOOGLE_FLOW` `[8,8]`, `[8,8,8]`, and longer `FLOW_EXTEND_UI` arrays

## Unsupported Plans

- `[4,4,4,4]` is explicitly blocked in this lane.
- Any declared block plan that diverges from `scripts/video_block_plan.py` fails closed.

## Mode Semantics

- `FRAMES`
  - visual-seed-first commercial framing
  - dialogue stays concise and camera continuity is explicit
- `INGREDIENTS`
  - seed/material list orientation
  - compiler still emits runtime-safe final prompt surfaces
- `HYBRID`
  - combines visual framing and structured ingredient cues
  - useful for clip-chain proof arcs where both scene and product behavior must stay locked

## Engine Notes

- `GROK`
  - extension-first seam logic
  - no greeting reset on extension blocks
  - continuity must resume within the BOSMAX seam window
- `GOOGLE_FLOW`
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
- missing multi-block `master_storyboard`
- dialogue word count above block `safe_max_words`

Warnings are emitted for underfilled or target-range-miss dialogue, but they do not promote a blocked template to ready.

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
  - `narrative_function`
  - `visual_action`
  - `dialogue_or_copy`
  - `wps_budget`
  - `start_state`
  - `end_state`
  - `continuity_anchor`
  - `final_prompt_block_text`
  - `qa_status`

## Validators

Run these from repo root:

```bash
python scripts/validate_video_template_schema.py
python scripts/validate_video_prompt_compiler.py
python scripts/validate_video_template_export_readiness.py
```

Recommended repo-wide evidence checks:

```bash
npx tsx scripts/mandor-check.ts
npx @biomejs/biome check .
npx dependency-cruiser . --no-config --output-type err
```
