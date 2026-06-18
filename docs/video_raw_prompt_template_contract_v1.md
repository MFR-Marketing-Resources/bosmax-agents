# BOSMAX Video Raw Prompt Template Contract v1

```
Status:    ACTIVE — repo contract (source of truth)
Version:   v1.0
Scope:     Operator-facing raw video prompt templates -> parser-ready seeds ->
           final prompt set surfaces via the video_template_compiler_runtime
Authority: registries/video_engine_duration_contracts.yaml (engine/duration),
           registries/video_template_schema.yaml (canonical record),
           registries/dialogue_budget_corridor.yaml (dialogue budget),
           docs/video_source_mode_contract_v1.md (source/intake modes)
```

---

## A. Purpose

This contract defines how an operator sends a **raw / very raw / rough** video
prompt request to BOSMAX Agents, and how that request is normalized into a
parser-ready seed and then polished into a detailed final prompt surface.

The operator declares **intent** (engine, duration, intake mode, product /
avatar / action / dialogue / safety detail). BOSMAX derives the deterministic
mechanics (lane, block plan, per-block dialogue budget, storyboard, continuity)
and the compiler produces the final prompt. The operator never hand-authors the
mechanical layers.

This doc is the **source of truth**. Notion templates and any operator UI are
downstream surfaces and must be generated only after this repo contract passes.

---

## B. Layer separation (do not collapse these)

1. **User-facing raw prompt template** — operator copy-paste. Contains engine,
   duration, intake_mode, product / avatar / action / dialogue / safety detail.
   Does **not** contain `final_prompt_text` and does **not** contain manually
   written child block prompts. Lives under `samples/video_raw_prompt_templates/`.
2. **Runtime canonical record** — parser / storyboard / compiler generated.
   Contains normalized engine / duration / intake_mode / block plan / storyboard
   / QA. Shape defined by `registries/video_template_schema.yaml`.
3. **Block registry / child rows** — compiler / exporter generated **only**.
   Never hand-authored by the operator.
4. **Final prompt surface** — compiler / Claude Cowork generated. Single-block
   runs emit one complete 9-section prompt. Multi-block runs emit a
   `MULTI_PROMPT_SET` container with one complete 9-section prompt per block.
   This is **not** the raw template.

---

## C. Required fields (every raw template)

| Field | Meaning |
|---|---|
| `engine` | `GROK` \| `GOOGLE_FLOW` \| `VEO_3_1` \| `VEO_3_1_LITE` |
| `duration` | Total seconds (e.g. `16s`). Must be valid for the engine/lane. |
| `intake_mode` | `HYBRID`/`PRODUCT_ONLY`, `FRAMES`/`READY_FRAME`, `INGREDIENTS`/`ASSET_SET` |
| `product_lane` | Canonical product lane (e.g. `BOSMAX`) |
| dialogue intent | `dialogue_seed` (spoken intent) and/or `hook`/`body`/`cta` spoken lines |
| mode truth lock | mode-appropriate truth (see N): product truth / frame truth / asset role map |

`platform` and `language` are strongly recommended (default `TikTok` / `Malay`).

## D. Optional fields

`product_input`, `avatar_source`, `avatar_brief`, `action_seed`,
`continuation_action_seed`, `visual_seed`, `scale_lock`, `safety_guardrails`,
`forbidden_claims`, `style_scene_limit`, `avatar_reference_lock`,
`commercial_angle_id`, `pilot_batch`. These enrich the seed; absence does not
block compilation.

## E. System-derived fields (operator must NOT supply)

- `block_plan` — derived from engine + duration (see H).
- `prompt_execution_mode` / lane — derived (e.g. Google Flow `FLOW_EXTEND_UI`
  vs `FLOW_EXTEND_10S`).
- `block_mode`, `block_count`, per-block `dialogue_budget`, storyboard,
  continuity locks, `output_mode`, `prompt_set_count`, `prompt_sets`,
  `final_prompt_text`, `final_prompt_blocks`, QA verdict.

## F. Forbidden manual fields

The operator must never hand-author any of:
`block_plan` (except a deliberate negative test), `output_mode`,
`prompt_set_count`, `prompt_sets`, `final_prompt_text`, `final_prompt_blocks`,
`final_prompt_block_text`, `final_block_prompt_text`, `block_script_json`, or
child block rows. These belong to the runtime / compiler / exporter only.

---

## G. intake_mode mapping

| Operator alias | Canonical `intake_mode` | Internal source mode | Uploaded assets |
|---|---|---|---|
| `HYBRID` | `PRODUCT_ONLY` | `HYBRID_PRODUCT_ANCHOR_MODE` | product image only |
| `FRAMES` | `READY_FRAME` | `READY_FRAME_MODE` | one finished frame |
| `INGREDIENTS` | `ASSET_SET` | `REFERENCE_SET_MODE` | role-mapped image set |

`intake_mode` is distinct from the compiler `mode` enum (`FRAMES`/`INGREDIENTS`/
`HYBRID` seed-authoring style) — they never collide. An unrecognized
`intake_mode` is rejected (fail-closed); an empty value is allowed (optional).

---

## H. Engine-duration derivation rules

The runtime derives `block_plan` deterministically (authority:
`registries/video_engine_duration_contracts.yaml`).

**GROK** (blocks 6s/10s only; never 8s; never `[8,8]`):
`6=[6]`, `10=[10]`, `12=[6,6]`, `16=[10,6]`, `18=[6,6,6]`, `20=[10,10]`, `30=[10,10,10]`.

**GOOGLE_FLOW — dual lane (never mixed in one render):**
- `FLOW_EXTEND_UI` (8s chain): `8=[8]`, `16=[8,8]`, `24=[8,8,8]`.
- `FLOW_EXTEND_10S` (10s extend): `10=[10]`, `18=[10,8]`, `20=[10,10]`,
  `30=[10,10,10]`, `40=[10,10,10,10]`, `50=[10×5]`, `60=[10×6]`.
- 16s stays `[8,8]`; 18s is `[10,8]`; Google Flow never uses the GROK `[10,6]`
  split. 40s auto-derives to the 10s lane; the 8s-chain 40s is reachable only by
  explicitly selecting `FLOW_EXTEND_UI`.

**VEO_3_1 / VEO_3_1_LITE:** clip-chain 8s blocks (`16=[8,8]`, `24=[8,8,8]`…).

A declared `block_plan` that diverges from the deterministic plan fails closed
(`StoryboardError`).

## H1. Multi-block output law

If the derived `block_plan` contains more than one block, the final output must
be `MULTI_PROMPT_SET`.

- Each block exports as its own complete 9-section prompt set.
- `prompt_set_count == len(block_plan)`.
- `prompt_sets.length == len(block_plan)`.
- Each prompt set exposes:
  - `set_index`
  - `set_duration`
  - `set_role`
  - `block_source`
  - `continuation_from_previous_set`
  - `wps_budget`
  - `dialogue_word_count`
  - `safe_max_words`
  - `dialogue_budget_status`
  - `final_prompt_9_sections`
- Continuation sets must continue directly from the previous set and must not
  restart the scene, product intro, avatar identity, lighting, scale, wardrobe,
  camera style, or commercial arc.
- The runtime must never collapse multiple blocks into one combined 9-section
  prompt.

Required examples:

- GROK 16s -> `SET 1 = 10s` + `SET 2 = 6s`
- GOOGLE_FLOW 16s (`FLOW_EXTEND_UI`) -> `SET 1 = 8s` + `SET 2 = 8s`
- GROK 20s -> `SET 1 = 10s` + `SET 2 = 10s`
- GROK 30s -> `SET 1 = 10s` + `SET 2 = 10s` + `SET 3 = 10s`
- GOOGLE_FLOW 24s (`FLOW_EXTEND_UI`) -> `SET 1 = 8s` + `SET 2 = 8s` + `SET 3 = 8s`
- GOOGLE_FLOW 20s (`FLOW_EXTEND_10S`) -> `SET 1 = 10s` + `SET 2 = 10s`

For Google Flow continuation sets, the compiler must make the seam explicit:

- `previous_clip_final_second_state` must be surfaced in the prompt set payload
- the prompt text must literally state `Previous clip final second state: ...`
- the prompt text must literally state `Continue from that exact state into ...`
- the seam must lock product position / label / scale, avatar identity /
  wardrobe / pose, scene / lighting / camera direction, and the next action
- vague shorthand such as `continue naturally` or `from last frame` is not sufficient

---

## I. Dialogue law

- `dialogue_required` defaults **YES** for commercial video.
- Dialogue is spoken **Malay** unless the operator requests otherwise.
- The **CTA is spoken** by default.
- Hook / body / CTA are **never** auto-converted into on-screen text.
- Per-block dialogue budgets are authoritative (e.g. GROK 16s `[10,6]`:
  block 1 ≈ 26–28 words, block 2 ≈ 15–16 words). The raw template provides
  dialogue **intent/seed**; the compiler / script-generator writes and budgets
  the final per-block spoken lines.
- For GROK 16s `[10,6]`, block 1 uses the 10s budget and block 2 uses the 6s
  budget. The runtime must never budget the dialogue as one 16s spoken block.

## J. Overlay law

- `overlay_allowed` defaults **false**; Section 9 defaults `NO_OVERLAY`.
- Text overlay is allowed only when explicitly requested (`overlay_allowed: true`
  or an `overlay_seed`).
- When overlay is not allowed, any overlay / subtitle / caption / lower-third /
  on-screen-text instruction **fails QA** (compiler overlay-leakage gate +
  raw-template file scan).
- When overlay is allowed, it must be bounded and must never cover the product
  label or visual truth.

## K. Product truth and scale-lock law

Product truth outranks avatar and style in every mode. For BOSMAX Serum, embed
this reusable truth lock where relevant:

> BOSMAX Serum 5ML / BOSMAX HERBS Herbal Oil Roll On. Preserve the exact tiny
> slim matte-black cylindrical roll-on bottle, glossy black cap, white BOSMAX
> HERBS wordmark, leaf icon, and "Herbal Oil Roll On" label. The product must
> remain **exactly lip balm size / exactly chapstick size**. Do not enlarge,
> stretch, relabel, recolor, redesign, duplicate, crop, replace, or change the
> cap/body proportion. It must never look like a perfume, spray, supplement,
> skincare-serum, or tall cosmetic bottle.

## L. Avatar handling law

- `PRODUCT_ONLY`: avatar is not uploaded — assembled from the avatar pool or an
  `avatar_brief` description.
- `READY_FRAME`: avatar identity is **locked from the uploaded frame**; do not
  rebuild it.
- `ASSET_SET`: avatar identity comes from the avatar reference image; an uploaded
  avatar overrides any registry persona; style/scene never overrides identity.

## M. Uploaded image description rules

- Describe uploaded assets in **general specialist** terms — the system cannot
  know every uploaded image in advance, so do not over-assert specifics not
  visible.
- `READY_FRAME`: the uploaded frame is the visual truth; describe continuation
  (motion-delta) only.
- `ASSET_SET`: each uploaded image is bound by an explicit role; product-truth
  image is highest authority.

---

## N. Mode-specific raw template requirements

### HYBRID / PRODUCT_ONLY
Product image is the truth source; avatar from pool/description; scene, action,
and dialogue described in the raw prompt. Required:
`engine, duration, intake_mode, product_input, product_truth_lock (or
product_truth_ref), avatar_source, avatar_brief, action_seed, dialogue_seed,
safety_guardrails, overlay_allowed:false`. For BOSMAX Serum 5ML include the K
scale lock (lip balm / chapstick size).

### FRAMES / READY_FRAME
One finished frame (avatar + product + scene) is the visual truth; continue /
animate from it; do not rebuild avatar/product/scene/wardrobe/lighting/grip/
scale. Required:
`engine, duration, intake_mode, ready_frame_input, frame_truth_lock,
continuation_action_seed, dialogue_seed, safety_guardrails,
overlay_allowed:false`. Use general specialist wording.

### INGREDIENTS / ASSET_SET
Multiple uploaded images with a role map; product truth outranks avatar and
style. Default role map: `image_1: PRODUCT_REFERENCE`, `image_2:
AVATAR_REFERENCE`, `image_3: STYLE_SCENE_REFERENCE` (optional). Required:
`engine, duration, intake_mode, asset_role_map, product_truth_lock,
avatar_reference_lock, style_scene_limit, action_seed, dialogue_seed,
safety_guardrails, overlay_allowed:false`.

---

## O. Parser / storyboard / compiler flow

```
raw prompt template (operator)
  -> scripts/video_template_parser.py     (normalize: engine, duration,
                                            intake_mode, lane, derive block_plan,
                                            keep raw_prompt_seed separate)
  -> scripts/video_storyboard_builder.py  (validate declared vs deterministic
                                            plan; master storyboard + continuity
                                            locks + per-block dialogue budget)
  -> scripts/video_prompt_compiler.py     (engine-adapted final prompt surfaces;
                                            QA: unsafe claims, marker leakage,
                                            overlay leakage, multi-block
                                            continuity, per-block WPS)
  -> (export path) parent/child rows       (compiler/exporter only)
```

Raw seed text and compiled final prompt text remain separate export surfaces.

---

## P. Validation requirements

Validator: `scripts/validate_video_raw_prompt_template_contract.py`. It confirms,
for every template under `samples/video_raw_prompt_templates/`:

1. Required samples exist (HYBRID / READY_FRAME / ASSET_SET, GROK 16s).
2. Valid engine + duration + intake_mode.
3. No manually authored `block_plan`.
4. Runtime derives the correct plan (GROK 16s = `[10,6]`; `sum(block_plan)` == duration).
5. intake_mode aliases normalize to canonical values.
6. No operator-authored `final_prompt_text`.
7. No operator-authored child block prompt text / `block_script_json`.
8. `overlay_allowed` defaults false.
9. No overlay / subtitle / on-screen-text leakage (raw scan + compiler QA).
10. Spoken dialogue intent present (`dialogue_seed` or `hook`).
11. Mode-appropriate truth lock present.
12. Compiles through parser -> storyboard -> compiler with no QA failure.
13. Single-block runs emit `output_mode=SINGLE_PROMPT`, `prompt_set_count=1`,
    and exactly one prompt set.
14. Multi-block runs emit `output_mode=MULTI_PROMPT_SET`,
    `prompt_set_count=len(block_plan)`, and one 9-section prompt set per block.
15. GROK 16s HYBRID / READY_FRAME / ASSET_SET samples all compile to two prompt
    sets `[10,6]`, with set 2 marked as a continuation and the CTA in the final
    set.
16. GOOGLE_FLOW 16s HYBRID / READY_FRAME / ASSET_SET samples all compile to two
    prompt sets `[8,8]`, with set 2 carrying explicit previous-clip-final-state
    continuity and per-set WPS budgeting.
17. Validator fails closed if a multi-block output collapses into one combined
    prompt or leaks forbidden phrases such as `FIRST 10 SECONDS`, `FINAL 6
    SECONDS`, `FIRST 8 SECONDS`, `FINAL 8 SECONDS`, `[8,8]` for GROK 16s, or
    `[10,6]` for GOOGLE_FLOW 16s.
18. Output remains sample/test only.

Run alongside the existing suite:

```bash
python scripts/validate_video_block_contracts.py
python scripts/validate_video_template_schema.py
python scripts/validate_prompt_template_readiness.py
python scripts/validate_video_prompt_compiler.py
python scripts/validate_video_template_export_readiness.py
python scripts/validate_video_raw_prompt_template_contract.py
npx tsx scripts/mandor-check.ts
npx @biomejs/biome check .
```

---

## Q. Operator examples

Required GROK 16s samples (operator writes engine + duration + intake_mode +
creative detail; runtime derives `[10,6]`):

- `samples/video_raw_prompt_templates/bosmax_hybrid_product_only_grok_16s.yaml`
- `samples/video_raw_prompt_templates/bosmax_ready_frame_grok_16s.yaml`
- `samples/video_raw_prompt_templates/bosmax_asset_set_ingredients_grok_16s.yaml`

Optional Google Flow 10s-extend lane samples:

- `samples/video_raw_prompt_templates/bosmax_hybrid_product_only_google_flow_16s.yaml` (`16s -> [8,8]`)
- `samples/video_raw_prompt_templates/bosmax_ready_frame_google_flow_16s.yaml` (`16s -> [8,8]`)
- `samples/video_raw_prompt_templates/bosmax_asset_set_ingredients_google_flow_16s.yaml` (`16s -> [8,8]`)
- `samples/video_raw_prompt_templates/bosmax_hybrid_product_only_google_flow_20s.yaml` (`20s -> [10,10]`)
- `samples/video_raw_prompt_templates/bosmax_asset_set_ingredients_google_flow_30s.yaml` (`30s -> [10,10,10]`)

Minimal shape (illustrative):

```yaml
engine: GROK
duration: 16s
intake_mode: HYBRID        # -> PRODUCT_ONLY
platform: TikTok
language: Malay
product_lane: BOSMAX
product_truth_ref: products/BOSMAX_SERUM.yaml
product_truth_lock: "<BOSMAX Serum truth lock — see section K>"
scale_lock: "EXACTLY lip balm size / chapstick size"
avatar_source: AVATAR_POOL
avatar_brief: "Malaysian adult presenter, natural UGC look"
action_seed: "Speak to camera, open cap, quick roll-on, pocket product"
dialogue_seed: "Hook (pain) -> friction -> relief -> spoken CTA"
hook: "..."   # parser-ready spoken Malay
body: "..."
cta: "Tap tengok harga sekarang, boss."
overlay_allowed: false
# block_plan: NOT supplied — runtime derives [10,6]
```

---

## R. Notion future note

- Notion is an **operator surface only**; this repo contract is the **source of
  truth**.
- Notion templates must be generated **only after** this repo contract passes
  validation.
- Notion stores raw seeds for operator reference; it does not store
  `final_prompt_text` as a source of truth and never hand-authors child rows.
- When a downstream Notion field such as `FINAL CLAUDE COPY-PASTE PROMPT`
  mirrors a multi-block runtime, it must declare `MULTI-PROMPT SET` and must
  not claim `one final 9-section prompt`.
- No Notion pages, CSV, production rows, or final production prompts are produced
  by this contract or its validator — sample/test only.
