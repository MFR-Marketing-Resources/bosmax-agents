# BOSMAX Video Raw Prompt Templates v1.0 — Operator Page

> **Page purpose:** This is the **operator surface** for sending raw / very raw / rough
> video prompt requests to BOSMAX Agents. You provide **engine + duration + intake_mode +
> creative details**; the runtime derives everything mechanical (block plan, per-block
> dialogue budget, storyboard, continuity) and the compiler writes the final 9-section /
> Google Flow prompt. You never hand-author the mechanical layers.

---

## 1. Status Box

| Field | Value |
|---|---|
| **Status** | ACTIVE OPERATOR PAGE |
| **Source of Truth** | `docs/video_raw_prompt_template_contract_v1.md` |
| **Contract version** | v1.0 |
| **Last repo validation** | PR #59 merged (squash `5f477fc`) |
| **Notion role** | copy-paste operator surface only |

- The **repo contract is the source of truth.** Notion is only a copy-paste surface.
- Operators provide `engine` + `duration` + `intake_mode` + creative details.
- The **runtime derives `block_plan`** — never hand-author it.
- Operators must **not** hand-author `final_prompt_text` or child block prompts.
- **Dialogue is spoken by default.** **CTA is spoken by default.**
- **Section 9 defaults `NO_OVERLAY`.** Text overlay only if explicitly requested.

---

## 2. Quick Decision Guide

| If the user uploads… | Use intake_mode | What it means |
|---|---|---|
| **Product image only** (no person) | `HYBRID` → `PRODUCT_ONLY` | Product image is the truth source. Avatar comes from the BOSMAX avatar pool / a description. Scene, action, and dialogue are described in the raw prompt. |
| **One finished image** (avatar + product + scene already in it) | `FRAMES` → `READY_FRAME` | The uploaded frame is the visual truth. System **continues / animates** from it. Do **not** rebuild avatar / product / scene / wardrobe / lighting / grip / scale. Action + dialogue are continuation only. |
| **Separate images** (product + avatar + optional scene/style) | `INGREDIENTS` → `ASSET_SET` | Role-mapped image set. Product-truth image outranks avatar and style. Style/scene image controls mood/environment only — never identity. |

---

## 3. Engine Duration Cheat Sheet

**GROK** (blocks are **6s / 10s only** — GROK never uses 8s):

| Duration | Block plan |
|---|---|
| 6s | `[6]` |
| 10s | `[10]` |
| 16s | `[10,6]` |
| 20s | `[10,10]` |
| 30s | `[10,10,10]` |

**GOOGLE_FLOW** (dual lane — **never uses the GROK `[10,6]` split**):

| Duration | Block plan |
|---|---|
| 8s | `[8]` |
| 16s | `[8,8]` |
| 24s | `[8,8,8]` |
| 10s | `[10]` |
| 18s | `[10,8]` |
| 20s | `[10,10]` |
| 30s | `[10,10,10]` |
| 40s | `[10,10,10,10]` |
| 50s | `[10,10,10,10,10]` |
| 60s | `[10,10,10,10,10,10]` |

> You never type the block plan. The runtime derives it from `engine` + `duration`.

---

## 4. Universal Rules

- ❌ No manual `block_plan`.
- ❌ No manual `final_prompt_text`.
- ❌ No manual child block prompt text.
- ✅ `overlay_allowed` defaults **false**.
- ✅ Section 9 defaults **`NO_OVERLAY`**.
- ✅ Dialogue **required by default** (spoken Malay unless you ask otherwise).
- ✅ **CTA spoken by default.**
- ✅ **Product truth outranks avatar and style** in every mode.
- ✅ For **BOSMAX Serum**, scale must remain **exactly lip balm / chapstick size**.

**BOSMAX Serum product truth lock (reuse verbatim where relevant):**

> BOSMAX Serum 5ML / BOSMAX HERBS Herbal Oil Roll On. Preserve the exact tiny slim
> matte-black cylindrical roll-on bottle, glossy black cap, white BOSMAX HERBS wordmark,
> leaf icon, and "Herbal Oil Roll On" label. The product must remain **exactly lip balm
> size / exactly chapstick size**. Do not enlarge, stretch, relabel, recolor, redesign,
> duplicate, crop, replace, or change the cap/body proportion. It must never look like a
> perfume, spray, supplement, skincare-serum, or tall cosmetic bottle.

---

## 5. Template 01 — HYBRID / PRODUCT_ONLY (GROK 16s)

> Upload the **product image only**. Avatar comes from the avatar pool. Copy the block below.

```yaml
engine: GROK
duration: 16s
intake_mode: HYBRID            # normalizes to PRODUCT_ONLY
platform: TikTok
language: Malay
product_lane: BOSMAX

# product truth (HYBRID: the uploaded product image is the truth source)
product_input: "Uploaded product image only: BOSMAX Serum 5ML roll-on (no avatar uploaded)."
product_truth_ref: products/BOSMAX_SERUM.yaml
product_truth_lock: >
  BOSMAX Serum 5ML / BOSMAX HERBS Herbal Oil Roll On. Preserve the exact tiny
  slim matte-black cylindrical roll-on bottle, glossy black cap, white BOSMAX
  HERBS wordmark, leaf icon, and "Herbal Oil Roll On" label. Do not enlarge,
  stretch, relabel, recolor, redesign, duplicate, crop, replace, or change the
  cap/body proportion. Never render it as a perfume, spray, supplement,
  skincare-serum, or tall cosmetic bottle.
scale_lock: "EXACTLY lip balm size / EXACTLY chapstick size; fits into fingers naturally."

# avatar (HYBRID: not uploaded; assembled from pool / description)
avatar_source: AVATAR_POOL
avatar_brief: "Malaysian adult presenter from the approved avatar pool, natural UGC look, one-hand product hold; BOSMAX selects the exact persona."

# action + dialogue (spoken Malay; CTA spoken; dialogue required by default)
action_seed: "Presenter speaks to camera, opens cap, quick roll-on motion, pockets the product."
dialogue_seed: "Hook (pain) -> friction (bulky products) -> relief (compact roll-on) -> spoken CTA. Per-block budget respected for GROK 16s [10,6]."
hook: "Tengah hari rasa panas, badan tak selesa sepanjang hari kan?"
body: "Produk lain besar menyusahkan, berat, tak muat poket bila keluar rumah, susah nak bawa ke mana-mana setiap masa. BOSMAX roll-on kecil macam lip balm, sapu sekali terus lega."
cta: "Tap tengok harga sekarang, boss."
visual_seed: "Brisk handheld UGC framing, product in palm, quick cap-open motion, label readable."

# safety / overlay
overlay_allowed: false         # Section 9 defaults NO_OVERLAY
safety_guardrails: "No medical cure / guaranteed-result / sexual-performance claims; no risky direct-body-use instructions."
forbidden_claims:
  - menyembuhkan penyakit
# block_plan: NOT supplied — runtime derives GROK 16s = [10,6]
# final_prompt_text: NEVER supplied here — the compiler writes it
```

---

## 6. Template 02 — FRAMES / READY_FRAME (GROK 16s)

> Upload **one finished image** (avatar + product + scene already in it). The system
> continues / animates the frame. **⚠️ Do not rebuild avatar / product / scene / wardrobe
> / lighting / grip / scale** — describe continuation only, in general specialist wording.

```yaml
engine: GROK
duration: 16s
intake_mode: FRAMES            # normalizes to READY_FRAME
platform: TikTok
language: Malay
product_lane: BOSMAX

# visual truth = the uploaded finished frame (do NOT rebuild)
ready_frame_input: "One uploaded finished frame already containing avatar + product + scene."
visual_authority: USER_UPLOAD
frame_truth_lock: >
  The uploaded finished frame is the single visual truth source. Lock identity,
  wardrobe, pose, product position, grip, label orientation, product scale,
  scene, and lighting from the frame. Motion-delta only. Do NOT rebuild the
  avatar, product, scene, wardrobe, lighting, grip, or product scale from
  scratch. Read the product name and scale from the frame; do not invent a
  different product or rescale it.
product_truth_ref: products/BOSMAX_SERUM.yaml

# continuation action + dialogue (continuation only; spoken Malay)
continuation_action_seed: "Hold the product naturally, slight tilt, small natural hand movement, natural expression while speaking. No new scene setup."
dialogue_seed: "Continue from a natural opening line; relief (practical/easy); spoken CTA. Per-block budget respected for GROK 16s [10,6]."
hook: "Tengah hari rasa panas, badan tak selesa sepanjang hari kan?"
body: "Produk lain besar menyusahkan, berat, tak muat poket bila keluar rumah, susah nak bawa ke mana-mana setiap masa. BOSMAX roll-on kecil macam lip balm, sapu sekali terus lega."
cta: "Tap tengok harga sekarang, boss."
visual_seed: "Continue from the uploaded frame; brisk UGC energy; keep identity, product position, and label readable as in the frame."

# safety / overlay
overlay_allowed: false         # Section 9 defaults NO_OVERLAY
safety_guardrails: "No medical cure / guaranteed-result / sexual-performance claims; no risky direct-body-use instructions."
forbidden_claims:
  - menyembuhkan penyakit
# block_plan: NOT supplied — runtime derives GROK 16s = [10,6]
# final_prompt_text: NEVER supplied here — the compiler writes it
```

---

## 7. Template 03 — INGREDIENTS / ASSET_SET (GROK 16s)

> Upload **separate images** with a role map. Product-truth image is highest authority.

```yaml
engine: GROK
duration: 16s
intake_mode: INGREDIENTS       # normalizes to ASSET_SET
platform: TikTok
language: Malay
product_lane: BOSMAX

# asset role map (product truth outranks avatar and style)
asset_role_map:
  image_1: PRODUCT_REFERENCE     # product truth (highest authority)
  image_2: AVATAR_REFERENCE      # identity / wardrobe / pose
  image_3: STYLE_SCENE_REFERENCE # optional: mood / environment only
asset_hierarchy: "PRODUCT_TRUTH > AVATAR_IDENTITY > STYLE_SCENE"
product_truth_ref: products/BOSMAX_SERUM.yaml
product_truth_lock: >
  BOSMAX Serum 5ML / BOSMAX HERBS Herbal Oil Roll On. Preserve the exact tiny
  slim matte-black cylindrical roll-on bottle, glossy black cap, white BOSMAX
  HERBS wordmark, leaf icon, and "Herbal Oil Roll On" label. Do not enlarge,
  stretch, relabel, recolor, redesign, duplicate, crop, replace, or change the
  cap/body proportion. Never render it as a perfume, spray, supplement,
  skincare-serum, or tall cosmetic bottle.
scale_lock: "EXACTLY lip balm size / EXACTLY chapstick size; fits into fingers naturally."
avatar_reference_lock: "Use image_2 for identity / wardrobe / pose generally; uploaded avatar overrides any registry persona."
style_scene_limit: "image_3 influences mood / environment / lighting only; it must never override product identity or avatar identity."

# action + dialogue (spoken Malay; CTA spoken)
action_seed: "Avatar interacts naturally with the product, performs the requested motion, speaks to camera."
dialogue_seed: "Hook (pain) -> friction -> relief (product) -> spoken CTA. Per-block budget respected for GROK 16s [10,6]."
hook: "Tengah hari rasa panas, badan tak selesa sepanjang hari kan?"
body: "Produk lain besar menyusahkan, berat, tak muat poket bila keluar rumah, susah nak bawa ke mana-mana setiap masa. BOSMAX roll-on kecil macam lip balm, sapu sekali terus lega."
cta: "Tap tengok harga sekarang, boss."
visual_seed: "Asset-set UGC cadence; product truth from product reference; avatar interacts naturally; label readable."

# safety / overlay
overlay_allowed: false         # Section 9 defaults NO_OVERLAY
safety_guardrails: "No medical cure / guaranteed-result / sexual-performance claims; no risky direct-body-use instructions."
forbidden_claims:
  - menyembuhkan penyakit
# block_plan: NOT supplied — runtime derives GROK 16s = [10,6]
# final_prompt_text: NEVER supplied here — the compiler writes it
```

---

## 8. Optional Google Flow Templates

### 8a. HYBRID / PRODUCT_ONLY — GOOGLE_FLOW 20s (`20s -> [10,10]`)

```yaml
engine: GOOGLE_FLOW
duration: 20s
intake_mode: HYBRID            # normalizes to PRODUCT_ONLY
platform: TikTok
language: Malay
product_lane: BOSMAX
product_input: "Uploaded product image only: BOSMAX Serum 5ML roll-on (no avatar uploaded)."
product_truth_ref: products/BOSMAX_SERUM.yaml
product_truth_lock: "BOSMAX Serum 5ML roll-on — preserve exact tiny slim matte-black bottle, glossy black cap, white BOSMAX HERBS wordmark, leaf icon, 'Herbal Oil Roll On' label; never a perfume/spray/serum bottle."
scale_lock: "EXACTLY lip balm size / EXACTLY chapstick size."
avatar_source: AVATAR_POOL
avatar_brief: "Malaysian adult presenter, natural UGC look; BOSMAX selects persona."
action_seed: "Two continuous 10s beats: cap-open + roll-on in beat one, pocket + CTA in beat two."
dialogue_seed: "Hook (pain) -> friction -> relief -> spoken CTA, spread across two 10s extend blocks."
hook: "Tengah hari rasa lesu, badan tak bermaya, susah nak fokus?"
body: "Banyak produk besar menyusahkan, tak muat poket bila keluar. BOSMAX roll-on ni kecil, ringan, sapu sekali terus rasa segar. Senang bawa pergi mana-mana."
cta: "Tap tengok harga sekarang, boss."
overlay_allowed: false
safety_guardrails: "No medical cure / guaranteed-result / sexual-performance claims."
# block_plan: NOT supplied — runtime derives GOOGLE_FLOW 20s = [10,10] (FLOW_EXTEND_10S; never [10,6])
# final_prompt_text: NEVER supplied here
```

### 8b. INGREDIENTS / ASSET_SET — GOOGLE_FLOW 30s (`30s -> [10,10,10]`)

```yaml
engine: GOOGLE_FLOW
duration: 30s
intake_mode: INGREDIENTS       # normalizes to ASSET_SET
platform: TikTok
language: Malay
product_lane: BOSMAX
asset_role_map:
  image_1: PRODUCT_REFERENCE
  image_2: AVATAR_REFERENCE
  image_3: STYLE_SCENE_REFERENCE   # optional
asset_hierarchy: "PRODUCT_TRUTH > AVATAR_IDENTITY > STYLE_SCENE"
product_truth_ref: products/BOSMAX_SERUM.yaml
product_truth_lock: "BOSMAX Serum 5ML roll-on — preserve exact tiny slim matte-black bottle, glossy black cap, white BOSMAX HERBS wordmark, leaf icon, 'Herbal Oil Roll On' label; never a perfume/spray/serum bottle."
scale_lock: "EXACTLY lip balm size / EXACTLY chapstick size."
avatar_reference_lock: "Use image_2 for identity / wardrobe / pose; uploaded avatar overrides any registry persona."
style_scene_limit: "image_3 controls mood / environment / lighting only; never overrides product or avatar identity."
action_seed: "Three continuous 10s beats: intro + product, proof handling in middle beat, spoken CTA in final beat."
dialogue_seed: "Hook (pain) -> friction -> relief -> proof -> spoken CTA, spread across three 10s extend blocks."
hook: "Tengah hari rasa lesu, badan tak bermaya betul kan?"
body: "Banyak produk lain besar menyusahkan dan tak muat poket. BOSMAX roll-on ni kecil macam lip balm, ringan, senang genggam, sapu sekali terus rasa lega. Simpan dalam beg, kereta, atau poket pun muat."
cta: "Tap tengok harga sekarang."
overlay_allowed: false
safety_guardrails: "No medical cure / guaranteed-result / sexual-performance claims."
# block_plan: NOT supplied — runtime derives GOOGLE_FLOW 30s = [10,10,10]
# final_prompt_text: NEVER supplied here
```

---

## 9. Common Mistakes

- ❌ Do **not** use GROK 8s — GROK blocks are 6s / 10s only.
- ❌ Do **not** write `[8,8]` for GROK 16s — GROK 16s is `[10,6]`.
- ❌ Do **not** write `[10,6]` for Google Flow — Flow never uses the GROK split.
- ❌ Do **not** add text overlay unless explicitly needed (`overlay_allowed` stays false).
- ❌ Do **not** paste a final 9-section prompt into a raw template field.
- ❌ Do **not** use Notion as the source of truth — the repo contract is.
- ❌ Do **not** delete old templates before audit.

---

## 10. Old Template Handling

- **Do not delete old templates immediately.**
- Label old templates as **`DEPRECATED`** / **`ARCHIVE_REFERENCE_ONLY`** if they:
  - use invalid durations / block splits (e.g. GROK `[8,8]`, Flow `[10,6]`),
  - default to overlays / on-screen text, or
  - paste a final prompt into a raw template field.
- Extract useful **creative wording only** if safe (hooks, body, CTA phrasing).
- New operator usage must move to **this v1.0 page**.

---

## 11. Handoff Note

- This file is a **Markdown draft only** — no Notion page was created in this task.
- If Claude Code is low on tokens, stop after creating this page and report the path.
- **ChatGPT / Notion AI** can continue by copying this Markdown into a Notion page.
- Do **not** attempt Notion creation in this task.

---

*Generated from the merged repo contract `docs/video_raw_prompt_template_contract_v1.md`
and the five validated samples under `samples/video_raw_prompt_templates/`. Sample/test
surface only — no CSV, no Notion rows, no production rows, no final production prompts.*
