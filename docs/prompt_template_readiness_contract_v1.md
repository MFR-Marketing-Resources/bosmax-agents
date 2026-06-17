# BOSMAX Prompt Template Readiness Contract v1

## Purpose

Defines the complete operator-facing template surface for BOSMAX video and batch
prompt generation. Proves the ecosystem has auditable coverage for:

- A. Single prompt / single block
- B. Multiple prompts / multiple blocks
- C. Batch single-block
- D. Batch multi-block

---

## A. Video Single-Block Templates

### Required Coverage

| workflow | silo | copywriting_mode | registry_writeback | expected route_status |
|---|---|---|---|---|
| BOSMAX_SERUM_STEALTH | STEALTH | AUTO_RESOLVE / COPY_FIXED / COPY_ROTATE | not applicable | REGISTERED_PRODUCT |
| MWCB_DIRECT | DIRECT | AUTO_RESOLVE / COPY_FIXED / COPY_ROTATE | not applicable | REGISTERED_PRODUCT |
| ON_THE_FLY_SESSION_ONLY | — | SESSION_ONLY_GENERATE | FORBIDDEN | ON_THE_FLY |

### Template field contract (per template)

| Field | Required | Description |
|---|---|---|
| `product_workflow` | YES | Workflow identifier |
| `platform` | YES | TikTok / Shopee / Lazada / Meta |
| `mode` | YES | A / B / C |
| `engine` | YES | From ENGINE CONSTRAINT TABLE |
| `duration` | YES | Must match engine allowed_durations |
| `language` | YES | BM / EN |
| `silo` | YES | STEALTH / DIRECT / (none for OTF) |
| `compliance` | YES | LOW / HIGH / REVIEW_ONLY / RED |
| `copywriting_mode` | YES | AUTO_RESOLVE / COPY_FIXED / COPY_ROTATE / SESSION_ONLY_GENERATE |
| `copywriting_id` | conditional | Required for COPY_FIXED; range/list for COPY_ROTATE; `none` for OTF |
| `avatar_context_id` | conditional | Required for registered products; optional for OTF |
| `registry_writeback` | OTF only | FORBIDDEN — hard contract, no other value accepted |
| `expected_route_status` | YES | REGISTERED_PRODUCT / ON_THE_FLY / BLOCKED_REVIEW_ONLY |

### Fail-closed rules (single-block)

- BOSMAX_SERUM_STEALTH MUST use `BOSMAX_MALE_STEALTH_POOL_001`
- MWCB_DIRECT MUST use `MWCB_TRAD_REMEDY_POOL_001`
- Pool cross-contamination raises ExporterError
- ON_THE_FLY registry_writeback must be FORBIDDEN — any other value raises ExporterError
- Hook / USP / CTA fields MUST NOT appear in beginner-facing template surface

### Reference

Sample files: `samples/notion/video_single_block_templates.yaml`

---

## B. Video Multi-Block Templates

### Required Coverage

| engine | total_duration | block_plan | execution_mode |
|---|---|---|---|
| VEO_3_1_LITE | 16s | [8, 8] | CLIP_CHAIN |
| VEO_3_1_LITE | 24s | [8, 8, 8] | CLIP_CHAIN |
| GROK | 16s | [10, 6] | EXTENSION |
| GROK | 20s | [10, 10] | EXTENSION |
| GOOGLE_FLOW (8s chain) | 16s | [8, 8] | FLOW_EXTEND_UI |
| GOOGLE_FLOW (8s chain) | 24s | [8, 8, 8] | FLOW_EXTEND_UI |
| GOOGLE_FLOW (10s extend) | 10s | [10] | FLOW_EXTEND_10S |
| GOOGLE_FLOW (10s extend) | 18s | [10, 8] | FLOW_EXTEND_10S |
| GOOGLE_FLOW (10s extend) | 20s | [10, 10] | FLOW_EXTEND_10S |
| GOOGLE_FLOW (10s extend) | 30s | [10, 10, 10] | FLOW_EXTEND_10S |
| GOOGLE_FLOW (10s extend) | 40s | [10, 10, 10, 10] | FLOW_EXTEND_10S |
| GOOGLE_FLOW (10s extend) | 50s | [10, 10, 10, 10, 10] | FLOW_EXTEND_10S |
| GOOGLE_FLOW (10s extend) | 60s | [10, 10, 10, 10, 10, 10] | FLOW_EXTEND_10S |

### Template field contract (per multi-block template)

| Field | Required | Description |
|---|---|---|
| `execution_mode` | YES | CLIP_CHAIN (VEO) / EXTENSION (GROK) |
| `total_duration` | YES | Total seconds across all blocks |
| `block_plan` | YES | Array of per-block durations (e.g. [8, 8]) |
| `block_count` | YES | Count of blocks |
| `block_index` | YES | 1-based index per block record |
| `block_role` | YES | HOOK / BODY / RELIEF / CTA / SINGLE |
| `bridge_out_required` | YES | true for all non-final blocks |
| `bridge_in_required` | YES | true for all non-first blocks |
| `identity_reanchor_required` | YES | true for VEO/GOOGLE_FLOW non-first blocks |
| `product_reanchor_required` | YES | true for VEO/GOOGLE_FLOW non-first blocks |
| `previous_clip_final_second_state` | GOOGLE_FLOW only | Required for FLOW_EXTEND_UI non-first blocks |
| `child_prompt_output_rule` | YES | Declares how child block prompts are emitted |

### GROK-specific multi-block rules

- GROK valid block durations: 6s and 10s ONLY
- GROK speech resume window: 0.5s–1.0s after seam
- GROK bridge-out on non-final blocks: required
- GROK bridge-in on non-first blocks: required
- GROK blocks must not contain internal labels (Block 1, Block 2) in operator-facing text
- GROK blocks must not re-introduce avatar or restart greeting
- Default BOSMAX GROK distributions:
  - 12s → [6, 6]
  - 16s → [10, 6]
  - 18s → [6, 6, 6]
  - 20s → [10, 10]
  - 30s → [10, 10, 10]

### VEO_3_1_LITE multi-block rules

- VEO_3_1_LITE max per block: 8s
- API declares 8s but actual render = 7s → dialogue budget uses 7s corridor
- requires_frame_bridge: true for all non-first blocks
- requires_identity_reanchor: true
- requires_product_reanchor: true
- bridge_in_required: true for all non-first blocks

### Google Flow dual-lane rules

Google Flow now runs two deterministic lanes. They never mix inside a single
render.

- `FLOW_EXTEND_UI` — 8s chain: 8s = [8], 16s = [8, 8], 24s = [8, 8, 8]
  (plus longer 8s arrays). 16s stays [8, 8].
- `FLOW_EXTEND_10S` — 10s extend lane: 10s = [10], 18s = [10, 8],
  20s = [10, 10], 30s = [10, 10, 10], 40s = [10, 10, 10, 10],
  50s = [10, 10, 10, 10, 10], 60s = [10, 10, 10, 10, 10, 10].
- 18s is the only 10s-lane plan that carries a single 8s tail ([10, 8]).
- 40s is valid in both lanes; the registry `default_total_lane` override routes
  auto-derived 40s to the 10s extend lane ([10, 10, 10, 10]). The 8s-chain 40s
  ([8, 8, 8, 8, 8]) remains reachable only by explicitly selecting
  `FLOW_EXTEND_UI`.
- Google Flow must NEVER use the GROK [10, 6] split.
- GROK must NEVER use an 8s block (GROK blocks are 6s or 10s only).
- The operator never writes `execution_mode` or `block_plan`; the runtime
  derives the lane and block plan from engine + duration.

### Child prompt output rule

Each multi-block plan produces N separate structured prompts:
- Block 1: generated from zero, no bridge-in
- Block 2+: `[CONTINUES FROM BLOCK N-1]` declared at top
- Visual start state of block N = visual end state of block N-1 (LOCKED)
- Dialogue is continuous — no restart between blocks
- Each block emits `BLOCK [X] OF [N]` declaration in Section 8
- Section 9 (overlay) of each block: `NO_OVERLAY` only

### Reference

Sample files: `samples/notion/video_multi_block_templates.yaml`

---

## C. Batch Single-Block Contract

### Required Coverage

| product_workflow | copywriting_mode | avatar_pool_id | registry_writeback |
|---|---|---|---|
| BOSMAX_SERUM_STEALTH | COPY_FIXED | BOSMAX_MALE_STEALTH_POOL_001 | not applicable |
| BOSMAX_SERUM_STEALTH | COPY_ROTATE | BOSMAX_MALE_STEALTH_POOL_001 | not applicable |
| MWCB_DIRECT | COPY_FIXED | MWCB_TRAD_REMEDY_POOL_001 | not applicable |
| MWCB_DIRECT | COPY_ROTATE | MWCB_TRAD_REMEDY_POOL_001 | not applicable |
| ON_THE_FLY_SESSION_ONLY | SESSION_ONLY_GENERATE | none | FORBIDDEN |

### Exporter output schema (per row)

| Column | Description |
|---|---|
| `prompt_id` | Unique row identifier |
| `row_index` | 1-based integer |
| `product_workflow` | Workflow name |
| `product_id` | Registry product ID or `none` |
| `product_name` | Human-readable name or `none` |
| `copywriting_id` | Resolved ID or `none` |
| `avatar_context_id` | Resolved avatar context ID or `none` |
| `avatar_pool_id` | Pool used or `none` |
| `engine` | Video engine |
| `duration` | Duration string |
| `platform` | Platform |
| `language` | Language |
| `route_status` | REGISTERED_PRODUCT / ON_THE_FLY / BLOCKED_REVIEW_ONLY |
| `final_prompt_text` | Full structured prompt text |

### Reference

Sample files: `samples/notion/batch_single_block_templates.yaml`
Exporter: `scripts/build_batch_video_prompts.py`
Exporter doc: `docs/batch_prompt_exporter_v1.md`

---

## D. Batch Multi-Block Contract

### Implementation status

```
SUPPORTED_CONTRACT_DESIGN / NOT_IMPLEMENTED_IN_EXPORTER_YET
```

The multi-block batch output shape is fully designed and documented here. The
`build_batch_video_prompts.py` exporter currently emits single-block rows only.
Multi-block batch output is CONTRACT_READY but requires a future exporter extension.

### Parent/child row design

For a batch of N videos × M blocks, the output is:

**Parent rows** (one per video):
- `prompt_id`: e.g. `BOSMAX_SERUM_BATCH_0001`
- `block_count`: M
- `total_duration`: total seconds
- `parent_copywriting_id`: resolved for the video
- `parent_avatar_context_id`: resolved for the video

**Child block rows** (M rows per parent = N × M total):
- `block_prompt_id`: e.g. `BOSMAX_SERUM_BATCH_0001_BLK_1`
- `row_index`: parent row index (1-based)
- `block_index`: 1-based block position within the video
- `block_count`: total blocks for this parent
- `block_duration`: duration of this block in seconds
- `total_duration`: total duration for the parent video
- `block_role`: HOOK / BODY / RELIEF / CTA
- `bridge_in_required`: true if block_index > 1
- `bridge_out_required`: true if block_index < block_count
- `identity_reanchor_required`: per engine contract
- `product_reanchor_required`: per engine contract
- `parent_copywriting_id`: inherited from parent
- `parent_avatar_context_id`: inherited from parent
- `final_block_prompt_text`: full structured prompt for this block

### Scale examples

- 20 videos × 2 blocks = 20 parent rows + 40 child block rows
- 20 videos × 3 blocks = 20 parent rows + 60 child block rows

### Reference

Sample files: `samples/notion/batch_multi_block_templates.yaml`

---

## E. Notion Field Alias Contract

| Operator-facing Notion label | Repo / Exporter schema field | Notes |
|---|---|---|
| Platform | `platform` | |
| Mode | `mode` | |
| Engine | `engine` | |
| Duration | `duration` | |
| Produk | `product_name` | |
| Product ID | `product_id` | |
| Workflow | `product_workflow` | |
| CopyPack ID | `copywriting_id` | Preferred label |
| Copywriting ID | `copywriting_id` | Legacy alias — tolerated only |
| CopyPack ID Range | `copywriting_id_range` | |
| Copywriting ID Range | `copywriting_id_range` | Legacy alias |
| CopyPack ID List | `copywriting_id_list` | |
| Avatar Context ID | `avatar_context_id` | |
| Avatar Pool ID | `avatar_pool_id` | |
| Batch Count | `batch_count` | |
| Rotation Rule | `rotation_rule` | |
| Copywriting Mode | `copywriting_mode` | |
| Avatar Mode | `avatar_mode` | |
| Compliance | `compliance` | |
| Registry Writeback | `registry_writeback` | ON_THE_FLY only; value must be FORBIDDEN |

### Deprecated aliases

- `Copywriting ID` → tolerated as legacy alias; preferred label is `CopyPack ID`
- `Copywriting ID Range` → tolerated as legacy alias; preferred label is `CopyPack ID Range`

### Forbidden fields (beginner-facing templates)

- `hook` / Hook
- `usp` / USP 1 / USP 2 / USP 3
- `cta` / CTA

These are resolved internally by `resolver_runtime`. They must never appear in
operator-facing batch input YAML or Notion template fields.

---

## F. Raw Prompt Template Contract (intake_mode)

The operator-facing raw template requires only:

- `engine` — GROK, GOOGLE_FLOW, VEO_3_1, VEO_3_1_LITE
- `duration` — e.g. `16s`
- `intake_mode` — one of:
  - `PRODUCT_ONLY` (alias `HYBRID`): product image uploaded; avatar generated
    from the avatar pool / description; scene, action, and dialogue are described
    in the raw template.
  - `READY_FRAME` (alias `FRAMES`): one finished image uploaded (avatar + product
    + scene already exist); the system continues/animates from the frame; action
    and dialogue are continuation only; do not rebuild the scene from scratch.
  - `ASSET_SET` (alias `INGREDIENTS`): multiple uploaded images with an asset role
    map (product-truth image, avatar image, optional scene/style image); product
    truth outranks avatar and style.
- product / avatar / image-role / action / dialogue details.

The operator does NOT write `block_plan` — the runtime derives the lane and
block plan deterministically from engine + duration. The operator does NOT
hand-author child block rows or `final_prompt_text`; those are produced only by
the compiler / export path.

## G. Dialogue & Overlay Law

- `dialogue_required` defaults to YES for commercial video; the CTA is spoken by default.
- Section 9 defaults to `NO_OVERLAY`.
- Hook / body / CTA are never auto-converted into on-screen text.
- Text overlay is allowed only when the operator explicitly opts in
  (`overlay_allowed: true` or an `overlay_seed`). When allowed, overlay must stay
  bounded and must never cover the product label or visual truth.
- The compiler blocks overlay / subtitle / on-screen-text leakage in seed and
  storyboard surfaces whenever overlay is not explicitly allowed.

## Readiness Table

| Surface | Status |
|---|---|
| Video single-block | READY |
| Video multi-block (GROK 16s/20s, VEO_LITE 16s/24s) | READY |
| Video multi-block (GOOGLE_FLOW 8s chain: 16s/24s; 10s extend: 10/18/20/30/40/50/60s) | READY |
| Batch single-block | READY |
| Batch multi-block | IMPLEMENTED_VIA_VIDEO_TEMPLATE_COMPILER_RUNTIME |

---

## References

- `docs/batch_prompt_exporter_v1.md`
- `docs/batch_multiblock_output_contract_v1.md`
- `samples/notion/video_single_block_templates.yaml`
- `samples/notion/video_multi_block_templates.yaml`
- `samples/notion/batch_single_block_templates.yaml`
- `samples/notion/batch_multi_block_templates.yaml`
- `scripts/validate_prompt_template_readiness.py`
- `registries/video_engine_duration_contracts.yaml`
- `scripts/validate_video_block_contracts.py`
