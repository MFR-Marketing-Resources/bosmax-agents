# Laporan Rujukan: Raw Prompt → Final Polished 9-Section Video Prompt  
## Hybrid / Frames / Ingredients — BOSMAX Video Source Mode & Multi-Prompt Set Contract

**Status:** Corrected report — v2  
**Purpose:** Dokumen ini menerangkan cara sebenar sistem video menghasilkan final polished prompt berdasarkan tiga bentuk visual intake: **Hybrid**, **Frames**, dan **Ingredients**.  
**Audience:** AI sebelah / prompt compiler / video prompt operator.  
**Output target:** Final prompt yang boleh dihantar ke video engine generator.  
**WPS Authority:** retained WPS profiles inside `WPS_Blocking_Template_REPAIRED.xlsx`  
**Duration Authority:** `WPS_Blocking_Template_REPAIRED.xlsx` — sheet `jadual_durasi`

---

## 0. Executive Summary

Retained package note: only the 9 retained BOSMAX knowledge-pack files are required. Any repo docs, scripts, or external references mentioned below are conceptual or historical references only and are not required attached files.


Dalam sistem BOSMAX video, **Hybrid / Frames / Ingredients ialah source-mode / intake architecture**. Maksudnya: sistem perlu tahu **jenis visual input apa yang user upload**, bagaimana visual tersebut diikat sebagai source of truth, dan bagaimana final polished prompt dibina untuk video engine.

| User-facing term | Canonical intake mode | Internal source mode | Maksud sebenar |
|---|---|---|---|
| **Hybrid** | `PRODUCT_ONLY` | `HYBRID_PRODUCT_ANCHOR_MODE` | User upload **gambar produk sahaja**. Produk jadi visual anchor. Avatar AI datang daripada database/avatar pool atau dibuat on-the-fly berdasarkan description. Scene/action/dialogue digenerate oleh prompt. |
| **Frames** | `READY_FRAME` | `READY_FRAME_MODE` | User upload **satu gambar siap** yang sudah mengandungi produk + avatar/subject + scene. Sistem tidak rebuild scene. Sistem tulis storyline/storyboard berdasarkan frame itu dan animate/continue frame tersebut. |
| **Ingredients** | `ASSET_SET` | `REFERENCE_SET_MODE` | User upload **beberapa gambar berasingan** sebagai bahan binaan: avatar/subject, product/scene, optional background/style/suasana. Sistem wajib buat asset role map dan bina storyline/storyboard daripada gabungan gambar tersebut. |

**Important:**  
Final output prompt bukan "summary". Ia ialah production instruction yang siap untuk engine. Jika runtime memerlukan lebih daripada satu block, final output bukan satu prompt panjang; ia keluar sebagai **MULTI-PROMPT SET**, dan setiap set/block mesti ada **9 section lengkap**.

---

## 1. Repo Evidence Register

| Evidence | Repo file | Key point |
|---|---|---|
| Source-mode authority | `docs/video_source_mode_contract_v1.md` | Defines `HYBRID_PRODUCT_ANCHOR_MODE`, `READY_FRAME_MODE`, `REFERENCE_SET_MODE`, asset role binding, and user-facing picker mapping. |
| Raw prompt template authority | `docs/video_raw_prompt_template_contract_v1.md` | Defines operator raw template, final prompt surface, block plan derivation, multi-block output law, dialogue law, overlay law, and mode-specific requirements. |
| Compiler section headings | `scripts/video_prompt_compiler.py` | Canonical 9 section headings used by compiler. |
| Final handoff contract | `docs/agents/BOSMAX_FINAL_OUTPUT_HANDOFF_CONTRACT_v1.md` | Final delivery must be clean copy-paste prompt blocks; multi-block output delivered as separate blocks. |
| Sample raw templates | `samples/video_raw_prompt_templates/*.yaml` | Shows actual Hybrid / Frames / Ingredients raw input shape for GROK 16s. |
| Duration & block plan | `WPS_Blocking_Template_REPAIRED.xlsx` — sheet `jadual_durasi` | Canonical engine+duration → block array mapping. Authority for all block math in this document. |
| WPS per language | `WPS_Blocking_Template_REPAIRED.xlsx` — sheet `Config` | Retained WPS values (Min/Safe/Max/Ceiling/SweetWPS) used for dialogue budgeting inside the retained package. |

---

## 2. Layer Separation: Raw Prompt vs Final Polished Prompt

### 2.1 Raw Prompt

Raw prompt ialah **operator-facing seed/template**. Ia bukan final prompt untuk engine.

Raw prompt mengandungi:

- `engine`
- `duration`
- `intake_mode`
- `platform`
- `language`
- product / avatar / frame / asset role information
- hook / body / CTA / dialogue seed
- safety guardrails
- overlay setting
- action seed / continuation seed

Raw prompt **tidak boleh** mengandungi:

- manual `block_plan`
- manual child block prompt
- manual `final_prompt_text`
- manual `prompt_sets`
- manual `final_prompt_blocks`
- manual block script JSON

Runtime/agent yang derive benda ini.

---

### 2.2 Runtime Canonical Record

Runtime layer akan normalize raw prompt:

```text
Raw prompt template
→ parser normalize engine, duration, intake_mode
→ runtime derives block plan (dari jadual_durasi)
→ storyboard builder creates storyline, block beats, continuity locks
→ dialogue budget assigned per block (dari WPS table)
→ compiler builds final prompt set(s)
→ compliance / QA checks
→ clean final output handoff
```

Operator tidak perlu tulis block plan. Contoh:

```yaml
engine: GROK
duration: 16s
intake_mode: HYBRID
```

Runtime derive:

```text
GROK 16s = [10,6]
```

---

### 2.3 Final Polished Prompt

Final polished prompt ialah **engine-facing production instruction**.

Ia mesti:

- clean
- copy-paste ready
- tidak bocor internal metadata
- mengikut 9 section
- mengikut block plan
- menjaga product truth
- menjaga avatar/frame/asset role binding
- menjaga continuity
- menjaga dialogue budget per block
- menjaga overlay law
- boleh dihantar terus ke video generator

Final engine-facing prompt body mesti gagal QA jika mengandungi unresolved avatar reference, avatar pool wording, source-mode taxonomy, WPS values, `block_plan`, `prompt_set_count`, debug JSON, atau runtime metadata.

---

## 3. Correct Definition: HYBRID

### 3.1 Maksud HYBRID Sebenar

**Hybrid** bermaksud user upload **gambar produk sahaja**.

Produk itu menjadi **visual anchor**. Sistem kemudian generate final polished prompt berdasarkan:

1. Uploaded product photo / registered product reference
2. Product truth lock
3. Avatar AI yang sudah di-resolve kepada satu description presenter Malaysia dewasa yang konkrit sebelum final prompt dibina
4. Scene/action/storyline yang dibina oleh prompt
5. Hook/body/CTA/dialogue seed
6. Engine + duration rules

Hybrid bukan "multi-input bebas". Hybrid ialah **product-only visual anchor + generated avatar/scene/action**.

---

### 3.2 Hybrid Input Architecture

```text
USER UPLOAD:
- Product photo only

SYSTEM RESOLVES:
- Product truth
- Product scale
- One resolved approved Malaysian adult presenter description
- Scene generated by prompt
- Action generated by prompt
- Dialogue generated/budgeted by runtime (per block)
- Final 9-section prompt
```

---

### 3.3 Hybrid Raw Prompt — Correct Sample

```yaml
template_id: BOSMAX_RAW_HYBRID_PRODUCT_ONLY_GROK_16S
engine: GROK
duration: 16s
intake_mode: HYBRID
platform: TikTok
language: Malay
product_lane: BOSMAX

product_input: "Uploaded product image only: BOSMAX Serum 5ML roll-on. No avatar uploaded."
product_truth_ref: products/BOSMAX_SERUM.yaml
product_truth_lock: >
  BOSMAX Serum 5ML / BOSMAX HERBS Herbal Oil Roll On. Preserve the exact tiny
  slim matte-black cylindrical roll-on bottle, glossy black cap, white BOSMAX
  HERBS wordmark, leaf icon, and "Herbal Oil Roll On" label. Product must remain
  exactly lip balm size / chapstick size.
scale_lock: "EXACTLY lip balm size / EXACTLY chapstick size."

avatar_id: null
avatar_resolution_rule: "If no avatar_id is supplied, resolve one concrete approved Malaysian adult presenter description before final prompt generation."

action_seed: "Presenter speaks to camera, shows compact product, quick pocket/drawer standby cue."
dialogue_seed: "Hook -> practical friction -> compact product relief -> spoken CTA."
hook: "Letak dalam drawer pun kemas."
body: "Kecil, senang standby dekat meja kerja, tak nampak berserabut."
cta: "Tap tengok harga sekarang, boss."

overlay_allowed: false
safety_guardrails: "No medical cure, no guaranteed result, no sexual-performance claim."
# block_plan: intentionally absent — runtime derives GROK 16s = [10, 6]
```

**Important:**  
No `block_plan`. No final prompt. No child blocks. Runtime derives all of that.

---

### 3.4 Hybrid Final Polished Output — What It Should Become

For GROK 16s, final output must become:

```text
MULTI-PROMPT SET
SET 1 - 10 SECONDS
SECTION 1 - ROLE & OBJECTIVE
...
SECTION 9 - NO_OVERLAY

SET 2 - 6 SECONDS
SECTION 1 - ROLE & OBJECTIVE
...
SECTION 9 - NO_OVERLAY
```

Hybrid final prompt must state:

- product image is the anchor
- product truth lock is repeated
- avatar is already resolved into one concrete approved Malaysian adult presenter description
- scene is prompt-generated
- product truth outranks avatar/style
- Set 2 continues from Set 1
- CTA lands in final set
- NO_OVERLAY unless explicitly allowed

---

## 4. Correct Definition: FRAMES

### 4.1 Maksud FRAMES Sebenar

**Frames** bermaksud user upload **gambar siap**.

Gambar siap itu sudah ada:

- product
- avatar / subject AI
- avatar handling product / near product
- scene
- lighting
- framing
- pose / grip / wardrobe / camera angle

Sistem tidak perlu invent avatar baru. Sistem tidak perlu rebuild scene dari kosong. Sistem perlu scan frame, tulis storyline/storyboard berdasarkan frame tersebut, dan generate video prompt untuk animate/continue frame.

Frames = **ready-frame continuation**, bukan product-only prompt.

---

### 4.2 Frames Input Architecture

```text
USER UPLOAD:
- One finished image/frame containing product + avatar/subject + scene

SYSTEM RESOLVES:
- Frame truth
- Product position from frame
- Avatar identity from frame
- Grip/pose/wardrobe from frame
- Lighting/framing from frame
- Motion delta only
- Storyline/storyboard based on the visible frame
- Final 9-section prompt
```

---

### 4.3 Frames Raw Prompt — Correct Sample

```yaml
template_id: BOSMAX_RAW_READY_FRAME_GROK_16S
engine: GROK
duration: 16s
intake_mode: FRAMES
platform: TikTok
language: Malay
product_lane: BOSMAX

ready_frame_input: "One uploaded finished frame already containing avatar + product + scene."
visual_authority: USER_UPLOAD
frame_truth_lock: >
  The uploaded finished frame is the single visual truth source. Lock identity,
  wardrobe, pose, product position, grip, label orientation, product scale,
  scene, and lighting from the frame. Motion-delta only. Do not rebuild avatar,
  product, scene, wardrobe, lighting, grip, or product scale from scratch.

continuation_action_seed: >
  Continue from the uploaded frame. Avatar holds product naturally, slight
  natural hand movement, small expression change, no new scene setup.

dialogue_seed: "Continue from visual frame; practical cue; spoken CTA in final block."
hook: "Yang ni memang senang standby."
body: "Letak dekat drawer, ambil bila perlu, tak nampak serabut."
cta: "Tap tengok harga sekarang, boss."

overlay_allowed: false
safety_guardrails: "No medical cure, no guaranteed result, no sexual-performance claim."
# block_plan: intentionally absent — runtime derives GROK 16s = [10, 6]
```

---

### 4.4 Frames Final Polished Output — What It Should Become

Frames final prompt must not say:

```text
Create a new avatar...
Create a new desk scene...
Design a new product setup...
```

It must say:

```text
The uploaded finished frame is the visual truth. Continue from the frame. Lock avatar
identity, product position, grip, scale, lighting, scene, and camera direction.
Apply only motion-delta action.
```

Frames final output must build the storyline from the uploaded image:

```text
Frame shows avatar + product + scene.
→ Storyline: avatar continues the existing action
→ Motion: small hand/product movement
→ Dialogue: spoken Malay line aligned with visible situation
→ CTA: final block
```

---

## 5. Correct Definition: INGREDIENTS

### 5.1 Maksud INGREDIENTS Sebenar

**Ingredients** bermaksud user upload beberapa gambar sebagai bahan binaan. Ia bukan satu frame siap. Setiap gambar perlu diberi role.

Contoh operator-facing:

```text
image_1 = product reference (product truth — highest authority)
image_2 = avatar/subject
image_3 = optional background/style/suasana
```

**Repo default sample** (dari `bosmax_asset_set_ingredients_grok_16s.yaml`):

```yaml
asset_role_map:
  image_1: PRODUCT_REFERENCE      # product truth — highest authority
  image_2: AVATAR_REFERENCE       # identity / wardrobe / pose
  image_3: STYLE_SCENE_REFERENCE  # optional: mood / environment only
```

**Rule penting:** Nombor gambar tidak menentukan role. Sistem wajib buat `asset_role_map` eksplisit. Yang penting ialah **binding role**, bukan nombor imej.

**Fallback sah untuk 2 gambar sahaja:** Jika hanya product + avatar yang diupload, jangan declare `image_3`. Guna:

```yaml
asset_role_map:
  image_1: PRODUCT_REFERENCE
  image_2: AVATAR_REFERENCE
style_scene_source: SCENE_CONTEXT_ONLY
```

Dalam path ini, environment datang daripada `SCENE_CONTEXT` sahaja. Jika raw prompt masih mengandungi `image_3: STYLE_SCENE_REFERENCE` tetapi imej ketiga tiada atau `NOT PROVIDED`, compiler mesti auto-normalize ke path 2 gambar: buang role style itu dan set `style_scene_source: SCENE_CONTEXT_ONLY`.

---

### 5.2 Ingredients Input Architecture

```text
USER UPLOAD:
- Multiple separate images

POSSIBLE ROLES:
- PRODUCT_REFERENCE
- AVATAR_REFERENCE
- STYLE_SCENE_REFERENCE
- READY_FRAME_PRODUCT_AVATAR
- READY_FRAME_PRODUCT_ONLY
- UNKNOWN_OR_AMBIGUOUS

SYSTEM RESOLVES:
- Asset role map (wajib explicit)
- Product truth hierarchy
- Avatar identity
- Background/style limit
- Storyline based on combined assets
- Final 9-section prompt
```

---

### 5.3 Ingredients Hierarchy

Ingredients mode must obey:

```text
PRODUCT_TRUTH > AVATAR_IDENTITY > STYLE_SCENE
```

Meaning:

- Product image/product truth always wins.
- Uploaded avatar overrides registry avatar.
- Background/style image can influence mood, lighting, surface, and environment only.
- Style/background must never override product identity.
- Ambiguous image roles must be clarified or blocked, not silently guessed.

---

### 5.4 Ingredients Raw Prompt — Correct Sample

```yaml
template_id: BOSMAX_RAW_ASSET_SET_INGREDIENTS_GROK_16S
engine: GROK
duration: 16s
intake_mode: INGREDIENTS
platform: TikTok
language: Malay
product_lane: BOSMAX

asset_role_map:
  image_1: PRODUCT_REFERENCE      # product truth (highest authority)
  image_2: AVATAR_REFERENCE       # identity / wardrobe / pose

asset_hierarchy: "PRODUCT_TRUTH > AVATAR_IDENTITY > STYLE_SCENE"
style_scene_source: SCENE_CONTEXT_ONLY

product_truth_lock: >
  Use the product reference image as product truth. Preserve product shape,
  packaging, cap, label, color, scale, and category. Do not let avatar image
  or background image redesign the product.

avatar_reference_lock: >
  Use image_2 for avatar identity, wardrobe direction, and pose DNA.
  Uploaded avatar overrides any registry persona.

style_scene_limit: >
  No style image is uploaded in this path. Use SCENE_CONTEXT only for mood,
  background, lighting, environment, and surface direction. It must not
  override product identity or avatar identity.

action_seed: "Avatar interacts naturally with the product and speaks to camera."
dialogue_seed: "Hook -> practical friction -> product relief -> spoken CTA."
hook: "Letak dekat meja pun nampak kemas."
body: "Kecil, senang capai, tak makan ruang."
cta: "Tap tengok harga sekarang, boss."

overlay_allowed: false
safety_guardrails: "No medical cure, no guaranteed result, no sexual-performance claim."
# block_plan: intentionally absent — runtime derives GROK 16s = [10, 6]
```

---

### 5.5 Ingredients Final Polished Output — What It Should Become

Ingredients final prompt must state:

- which image controls product truth
- which image controls avatar identity
- which image controls style/background only
- product truth outranks all images
- style image must not redesign product
- avatar image must not override product shape
- storyline/storyboard uses all images within their roles

Final prompt should not say:

```text
Blend all images freely.
Use the nicest image as the main reference.
Let the background reference change the product look.
```

It should say:

```text
Use the asset role map. Product reference (image_1) controls product identity and
scale. Avatar reference (image_2) controls human identity and pose direction.
Style/background reference (image_3) controls mood/environment only.
```

---

## 6. Canonical 9-Section Output Structure

The final polished video prompt must use exactly 9 sections.

Canonical headings (authority: `scripts/video_prompt_compiler.py`):

```text
SECTION 1 - ROLE & OBJECTIVE
SECTION 2 - PRODUCT TRUTH LOCK
SECTION 3 - CONTINUITY & STATE LOCK
SECTION 4 - VISUAL STORY
SECTION 5 - SHOT & CAMERA RULES
SECTION 6 - SPOKEN DIALOGUE
SECTION 7 - VOICE & DELIVERY
SECTION 8 - CTA & END FRAME
SECTION 9 - NO_OVERLAY
```

---

### 6.1 Section 1 — ROLE & OBJECTIVE

Purpose:

- Define engine and duration for this set/block.
- Define commercial role of this block.
- For multi-block: explain whether this is opening segment or continuation segment.
- Do not leak block math or internal runtime metadata inside prompt prose.

Correct:

```text
Build a complete 10-second GROK commercial video for TikTok, covering the opening
product-discovery beat. This is the opening segment of a continuous two-part video;
render only this beat cleanly and let it flow into the next segment.
```

Wrong:

```text
Runtime plan is [10,6]. Do not compile as one 16-second prompt.
output_mode=MULTI_PROMPT_SET.
```

---

### 6.2 Section 2 — PRODUCT TRUTH LOCK

Purpose:

- Lock product identity, shape, label, cap, color, material, scale, category.
- Product truth must repeat in every set/block.
- In Ingredients mode, product truth outranks avatar and style.
- In Frames mode, product must remain as shown in frame.

Correct:

```text
Preserve the exact tiny slim matte-black BOSMAX roll-on bottle, glossy black cap,
white BOSMAX HERBS wordmark, leaf icon, and Herbal Oil Roll On label. Product
remains exactly lip balm size / chapstick size.
```

---

### 6.3 Section 3 — CONTINUITY & STATE LOCK

Purpose:

- Lock continuity state.
- For Hybrid: open from generated scene state and avatar source.
- For Hybrid: embed one resolved concrete presenter description directly; do not mention avatar pool, selection logic, or intake taxonomy.
- For Frames: lock uploaded frame identity/product/scene/pose/grip/lighting.
- For Ingredients: lock asset role map and hierarchy.
- For continuation set: explicitly continue from previous set; do not restart.

Natural engine-facing phrasing:

```text
HYBRID: Use the uploaded product image as the exact product reference. No avatar image is provided. Use this resolved presenter description: [resolved presenter].
FRAMES: Use the uploaded finished frame as the single visual reference. Continue only from the visible frame state.
INGREDIENTS: Use the uploaded references according to the provided asset role map. Product reference controls product truth, avatar reference controls identity, style reference controls environment only.
```

Correct continuation line:

```text
Continue directly from the previous prompt set. Do not restart the scene, product
intro, avatar identity, lighting, scale, wardrobe, camera style, or commercial arc.
```

---

### 6.4 Section 4 — VISUAL STORY

Purpose:

- Turn raw seed into actual visible action.
- Define the story beat of this block.
- In Frames mode: storyline must come from the uploaded frame.
- In Ingredients mode: storyline must be assembled from role-mapped assets.
- Must avoid internal labels inside spoken dialogue.

Correct:

```text
Visual action: Avatar keeps the product visible near the drawer, makes a small
natural hand adjustment, then brings the label closer to camera without changing
product scale. Narrative function: practical storage proof and compact standby cue.
```

---

### 6.5 Section 5 — SHOT & CAMERA RULES

Purpose:

- Define camera behavior.
- Prevent scene reset, product drift, and product redesign.
- For Google Flow continuation, seam must be literal and stateful.

Correct:

```text
Use controlled handheld UGC motion, no sudden zoom, no scene reset, no extreme macro
distortion. Keep label readable and product scale believable.
```

---

### 6.6 Section 6 — SPOKEN DIALOGUE

Purpose:

- Contains the exact spoken line for this set/block.
- Malay by default for TikTok Malaysia unless operator requests otherwise.
- Hook/body/CTA stay spoken. They must not auto-convert into overlay text.
- **Dialogue must be budgeted per block, not total duration.** (See Section 9 WPS table.)

Correct:

```text
On-camera presenter speaks the lines to camera with accurate lip-sync; on any
product-hero cutaway the same line continues as tightly synced voice with no audio
gap: "Letak dalam drawer pun kemas, kecil je macam lip balm, senang standby dekat
meja kerja."
```

---

### 6.7 Section 7 — VOICE & DELIVERY

Purpose:

- Specify language, delivery pace, tone, and no dead air.
- Should not leak numeric WPS metadata.
- Should not mix "voiceover only" with on-camera lip-sync unless product-only route is selected.

Correct:

```text
Spoken delivery in Malay at a brisk, conversational UGC pace. Keep the presenter
talking naturally across the full clip with real breaths between phrases. Do not
rush or clip the final phrase.
```

---

### 6.8 Section 8 — CTA & END FRAME

Purpose:

- CTA handling.
- End-frame instruction.
- In non-final set: usually no final CTA yet.
- In final set: CTA lands naturally.

Correct for opening set:

```text
No CTA yet. End frame holds the product near the drawer, label still readable, with
momentum ready for the next segment.
```

Correct for final set:

```text
Deliver the spoken CTA naturally: "Tap tengok harga sekarang, boss." End frame holds
the product as clean hero, label readable, scale intact.
```

---

### 6.9 Section 9 — NO_OVERLAY

Purpose:

- Enforce overlay law.
- Default is NO_OVERLAY.
- Hook/body/CTA remain spoken unless overlay is explicitly allowed.
- No captions, subtitles, lower-thirds, sticker text, price text, or on-screen copy if overlay is false.

Correct:

```text
NO_OVERLAY. No visual text layer of any kind. Spoken hook/body/CTA must remain
spoken and never be converted into visual copy.
```

**Note:** Section 9 is the overlay enforcement instruction only. QA status belongs outside the copy-paste prompt block in the final handoff (separate line after the prompt block).

---

## 7. Multi-Set / Block Prompt Logic

### 7.1 Bila Output Perlu Lebih Daripada Satu Set?

Jika derived `block_plan` lebih daripada satu block, final output mesti jadi:

```text
MULTI-PROMPT SET
```

Setiap block mesti ada:

- set index
- set duration
- set role
- continuation status
- dialogue budget (per block, dari WPS table)
- complete 9 sections

Setiap set/block dihantar ke generator sebagai separate prompt/generation request.

---

### 7.2 Engine Duration Rules

**Authority: `WPS_Blocking_Template_REPAIRED.xlsx` — sheet `jadual_durasi`**

#### GROK

Block unit: **6s atau 10s sahaja**. GROK tidak guna 8s block.

```text
6s   = [6]
10s  = [10]
12s  = [6,6]
16s  = [10,6]
18s  = [6,6,6]
20s  = [10,10]
30s  = [10,10,10]
```

**Critical:**  
GROK 16s adalah `[10,6]`.  
Jangan guna `[8,8]` untuk GROK 16s.  
Jangan guna `[6,10]` — block 10s sentiasa dahulu untuk GROK 16s.

---

#### GOOGLE FLOW

Google Flow menggunakan **satu block size sahaja per sesi** — pilihan antara **8s atau 10s**.  
Kedua-dua lane tidak boleh dicampur dalam satu render.

**Lane 8s** (pilih 8s sebagai block unit):

```text
8s   = [8]
16s  = [8,8]
24s  = [8,8,8]
32s  = [8,8,8,8]
40s  = [8,8,8,8,8]
56s  = [8,8,8,8,8,8]
```

**Lane 10s** (pilih 10s sebagai block unit):

```text
10s  = [10]
20s  = [10,10]
30s  = [10,10,10]
40s  = [10,10,10,10]
50s  = [10,10,10,10,10]
60s  = [10,10,10,10,10,10]
```

**Note untuk 40s:** Boleh dihasilkan sama ada dengan Lane 8s `[8×5]` atau Lane 10s `[10×4]`. Operator mesti pilih lane dahulu.

**Critical:**  
Google Flow 16s adalah `[8,8]` — bukan `[10,6]`.  
Google Flow tidak guna split GROK. Dua lane tidak boleh campur dalam satu render.

---

### 7.3 Multi-Set Law

Untuk multi-set output:

```text
Total duration = 16s
Engine = GROK
Derived block plan = [10,6]

Output:
SET 1 - 10 SECONDS - complete 9 sections
SET 2 - 6 SECONDS - complete 9 sections
```

Jangan tulis:

```text
Create one 16-second prompt...
```

Jangan tulis:

```text
SET 2: Continue same scene and say CTA.
```

Betul:

```text
SET 2 must still include all 9 sections.
```

---

### 7.4 Continuation Law

Continuation set must not restart:

- scene
- product intro
- avatar identity
- lighting
- scale
- wardrobe
- camera style
- commercial arc

Continuation set must inherit:

- product truth
- avatar identity
- scene state
- lighting direction
- camera movement
- dialogue momentum
- end-frame state

**Untuk Google Flow**, continuation mesti lebih explicit daripada sekadar "continue from last frame". Ia mesti state:

```text
Previous clip final second state: [describe exact final visual]
Continue from that exact state into: [next action]
Continuity seam: [lock product / label / scale / avatar / scene / camera direction]
```

---

## 8. Dialogue Budget (WPS) per Block

### 8.1 WPS Reference — Per Language

**Authority: retained WPS profiles in `WPS_Blocking_Template_REPAIRED.xlsx` — sheet `Config`**

| Language | Min WPS | Safe WPS | Max WPS | Ceiling WPS | Tokenization Risk |
|---|---|---|---|---|---|
| Malay | 1.8 | 2.4 | 2.8 | 3.0 | LOW |
| English | 1.7 | 2.3 | 2.6 | 3.0 | LOW |
| Indonesian | 1.8 | 2.4 | 2.8 | 3.0 | LOW |
| Mandarin | 1.8 | 2.5 | 2.8 | 3.0 | HIGH ⚠️ |
| Hindustani | 1.8 | 2.3 | 2.7 | 3.0 | MEDIUM |
| Tamil | 1.7 | 2.2 | 2.6 | 3.0 | MEDIUM |
| Bengali | 1.7 | 2.2 | 2.6 | 3.0 | MEDIUM |
| Thai | 1.6 | 2.1 | 2.5 | 3.0 | HIGH ⚠️ |
| Burmese | 1.5 | 2.0 | 2.4 | 3.0 | HIGH ⚠️ |

**Audit Warning:** Mandarin, Thai, dan Burmese memerlukan semakan timing secondary menggunakan character/syllable/native VO count kerana WPS tokenization boleh mengelirukan.

**Hard Ceiling:** 3.0 WPS adalah absolute ceiling untuk semua bahasa kecuali operator override manually.

---

### 8.2 Word Budget per Block Duration

**Authority: retained WPS profiles in `WPS_Blocking_Template_REPAIRED.xlsx` — sheet `Config`**  
**Formula:** word_count = duration_seconds × WPS

**Guna Safe Words sebagai target minimum untuk final ad script.**  
**Guna Max Words hanya untuk fast VO atau non-critical lines.**

---

#### 6s Block (GROK Block Unit)

| Language | Min Words | Safe Words | Max Words | Ceiling @3.0 WPS |
|---|---|---|---|---|
| Malay | 11 | 14 | 17 | 18 |
| English | 10 | 14 | 16 | 18 |
| Indonesian | 11 | 14 | 17 | 18 |
| Hindustani | 11 | 14 | 16 | 18 |
| Mandarin | 11 | 15 | 17 | 18 |
| Tamil | 10 | 13 | 16 | 18 |
| Bengali | 10 | 13 | 16 | 18 |
| Thai | 10 | 13 | 15 | 18 |
| Burmese | 9 | 12 | 14 | 18 |

---

#### 8s Block (Google Flow Block Unit — Lane 8s)

| Language | Min Words | Safe Words | Max Words | Ceiling @3.0 WPS |
|---|---|---|---|---|
| Malay | 14 | 19 | 22 | 24 |
| English | 14 | 18 | 21 | 24 |
| Indonesian | 14 | 19 | 22 | 24 |
| Hindustani | 14 | 18 | 22 | 24 |
| Mandarin | 14 | 20 | 22 | 24 |
| Tamil | 14 | 18 | 21 | 24 |
| Bengali | 14 | 18 | 21 | 24 |
| Thai | 13 | 17 | 20 | 24 |
| Burmese | 12 | 16 | 19 | 24 |

---

#### 10s Block (GROK Block Unit / Google Flow Block Unit — Lane 10s)

| Language | Min Words | Safe Words | Max Words | Ceiling @3.0 WPS |
|---|---|---|---|---|
| Malay | 18 | 24 | 28 | 30 |
| English | 17 | 23 | 26 | 30 |
| Indonesian | 18 | 24 | 28 | 30 |
| Hindustani | 18 | 23 | 27 | 30 |
| Mandarin | 18 | 25 | 28 | 30 |
| Tamil | 17 | 22 | 26 | 30 |
| Bengali | 17 | 22 | 26 | 30 |
| Thai | 16 | 21 | 25 | 30 |
| Burmese | 15 | 20 | 24 | 30 |

---

### 8.3 Cara Guna WPS Table

1. Identify engine dan block duration (6s, 8s, atau 10s per block)
2. Identify language
3. Lookup Safe Words → gunakan sebagai minimum target dialogue per block
4. Jangan exceed Max Words kecuali VO fast-paced explicit
5. Jangan go below Min Words — akan menyebabkan dead air / filler motion

**Contoh: GROK 16s [10,6], bahasa Malay:**
```
Block 1 (10s): target 24 words (Safe), max 28 words
Block 2 (6s):  target 14 words (Safe), max 17 words
Total target:  38 words across full 16s
```

**Contoh: Google Flow 16s [8,8], bahasa English:**
```
Block 1 (8s): target 18 words (Safe), max 21 words
Block 2 (8s): target 18 words (Safe), max 21 words
Total target: 36 words across full 16s
```

---

## 9. Example Final Polished Output: HYBRID, GROK 16s [10,6]

### SET 1 - 10 SECONDS

```text
SET 1 - 10 SECONDS

SECTION 1 - ROLE & OBJECTIVE
Build a complete 10-second GROK commercial video for TikTok, covering the opening
product-discovery beat. This is the opening segment of a continuous two-part video;
render only this beat cleanly and let it flow into the next segment without trying
to close the whole sale inside this clip.

SECTION 2 - PRODUCT TRUTH LOCK
Use the uploaded product photo as the product truth anchor. Preserve the exact BOSMAX
Serum 5ML / BOSMAX HERBS Herbal Oil Roll On identity: tiny slim matte-black cylindrical
roll-on bottle, glossy black cap, white BOSMAX HERBS wordmark, leaf icon, and "Herbal
Oil Roll On" label. The product must remain exactly lip balm size / chapstick size.
Do not enlarge, stretch, relabel, recolor, redesign, duplicate, crop, replace, or turn
it into perfume, spray, supplement, skincare serum, or tall cosmetic bottle.

SECTION 3 - CONTINUITY & STATE LOCK
Use the uploaded product photo as the exact product reference. No avatar image is
provided. Use one approved Malaysian young adult presenter with light-medium skin
tone, medium tidy hair, smart office wear, and a calm neutral expression in a
practical modern work-desk and drawer standby setup. Keep product scale believable
and label readable.

SECTION 4 - VISUAL STORY
Visual action: Presenter appears in a natural UGC desk setting, shows the tiny BOSMAX
bottle near a drawer, keeps the label facing camera, then places it beside everyday
desk items to prove it looks neat and compact. Narrative function: opening hook and
practical storage proof.

SECTION 5 - SHOT & CAMERA RULES
Use controlled handheld UGC framing with stable close product visibility. No sudden
zoom, no over-shaky motion, no extreme macro distortion, no product redesign, no label
blur, and no camera angle that makes the bottle look oversized.

SECTION 6 - SPOKEN DIALOGUE
On-camera presenter says the line directly to camera with visible mouth, lips,
jaw, and facial muscles synchronized from the first moment. No product-only
cutaway during the spoken line:
"Letak dalam drawer pun kemas, kecil je macam lip balm, senang standby dekat meja
kerja tanpa nampak serabut."

SECTION 7 - VOICE & DELIVERY
Spoken delivery in Malay at a brisk, conversational UGC pace. Keep the presenter
talking naturally across the full 10 seconds with real breaths between phrases. Fill
the beat edge to edge so there is no silent dead air.

SECTION 8 - CTA & END FRAME
No final CTA yet. End frame holds the BOSMAX bottle beside the drawer with label
readable, cap intact, product scale small, and the presenter still in the same desk
environment ready to continue into the next segment.

SECTION 9 - NO_OVERLAY
NO_OVERLAY. No visual text layer of any kind. Spoken hook/body/CTA must remain
spoken and never be converted into visual copy.
```

---

### SET 2 - 6 SECONDS

```text
SET 2 - 6 SECONDS

SECTION 1 - ROLE & OBJECTIVE
Build a complete 6-second GROK commercial video for TikTok, covering the final CTA
beat. This continues seamlessly from the previous segment with the same presenter,
product, scene, and momentum; render only this beat and do not restart or recap.

SECTION 2 - PRODUCT TRUTH LOCK
Continue preserving the exact BOSMAX Serum 5ML / BOSMAX HERBS Herbal Oil Roll On
identity: tiny slim matte-black cylindrical roll-on bottle, glossy black cap, white
BOSMAX HERBS wordmark, leaf icon, and "Herbal Oil Roll On" label. The product must
remain exactly lip balm size / chapstick size. Do not alter bottle shape, cap/body
proportion, label, color, size, or category.

SECTION 3 - CONTINUITY & STATE LOCK
Continue directly from the previous prompt set. Do not restart the scene, product
intro, avatar identity, lighting, scale, wardrobe, camera style, or commercial arc.
Keep the same Malaysian presenter, same desk/drawer setup, same product placement
logic, same compact scale, and same label direction.

SECTION 4 - VISUAL STORY
Visual action: Presenter keeps the product near the drawer, gives one small natural
product adjustment toward camera, then holds the label cleanly for the final selling
moment. Narrative function: reinforce compact standby cue and land the final purchase
action.

SECTION 5 - SHOT & CAMERA RULES
Resume inside 0.5–1.0 seconds from the previous spoken seam. Do not restart greeting
or re-introduce the presenter. Use the same handheld UGC camera language, same
lighting direction, and same product distance. Keep label readable and product scale
small.

SECTION 6 - SPOKEN DIALOGUE
On-camera presenter says the line directly to camera with visible mouth, lips,
jaw, and facial muscles synchronized from the first moment. No product-only
cutaway during the spoken line:
"Simpan je dekat drawer, ambil bila perlu. Tap tengok harga sekarang, boss."

SECTION 7 - VOICE & DELIVERY
Spoken delivery in Malay at a brisk, conversational UGC pace. Keep the presenter
talking naturally across the full 6 seconds with real breaths between phrases. Do
not rush the CTA or clip the final word.

SECTION 8 - CTA & END FRAME
Deliver the spoken CTA naturally: "Tap tengok harga sekarang, boss." End frame holds
the product as clean hero beside the drawer, label readable, cap intact, scale small,
no product drift.

SECTION 9 - NO_OVERLAY
NO_OVERLAY. No visual text layer of any kind. Spoken hook/body/CTA must remain
spoken and never be converted into visual copy.
```

---

## 10. Part 2 Seam + Lipsync Continuation Patch

Part 2 is not a new shot. It is the next visible beat of the same shot-chain.

- Write the literal previous-final-frame state before the next action.
- The first 0.5 seconds must show mouth movement beginning the next spoken phrase and hand/product micro-motion continuing immediately.
- The first 1-2 seconds must keep face and mouth visible when lipsync is required.
- The product stays visible in hand, but product-only cutaway is blocked until lipsync is established.
- GROK 6s Malay continuation should target 11-13 words as a soft seam target while still respecting retained base WPS authority.
- Google Flow 8s Malay continuation should target 14-18 words.
- No product-only cutaway during the spoken line. The line must come from the visible presenter’s mouth.

## 11. Example Final Polished Output: FRAMES, GROK 16s [10,6]

### SET 1 - 10 SECONDS

```text
SET 1 - 10 SECONDS

SECTION 1 - ROLE & OBJECTIVE
Build a complete 10-second GROK commercial video for TikTok, covering the opening
continuation beat from the uploaded finished frame. This is the opening segment of
a continuous two-part video; animate only the existing frame truth and let it flow
into the next segment.

SECTION 2 - PRODUCT TRUTH LOCK
The product visible in the uploaded finished frame must remain the same product.
Preserve product position, label orientation, packaging shape, cap/body proportion,
and product scale exactly as shown in the frame. Do not redesign, relabel, rescale,
crop, duplicate, or replace the product.

SECTION 3 - CONTINUITY & STATE LOCK
The uploaded finished frame is the single visual truth source. Lock avatar identity,
wardrobe, pose, product grip, product position, label orientation, product scale,
scene, lighting, background, and camera angle from the frame. Motion-delta only.
Do not rebuild the avatar, product, scene, wardrobe, lighting, grip, or product
scale from scratch.

SECTION 4 - VISUAL STORY
Visual action: Continue from the existing frame. Avatar makes a small natural hand
movement while holding or presenting the product, keeps the product visible, and
slightly adjusts expression or posture without changing the composition. Narrative
function: convert the still frame into a believable product-use continuation.

SECTION 5 - SHOT & CAMERA RULES
Use restrained continuation movement only. Keep the camera language close to the
uploaded frame. No scene reset, no new room, no new wardrobe, no new avatar, no
new product setup, no large camera swing, and no product re-introduction.

SECTION 6 - SPOKEN DIALOGUE
On-camera presenter speaks the line to camera with accurate lip-sync; if the face
is partially off-frame, keep the spoken line naturally synced to the visible
continuation: "Yang ni memang senang standby, kecil je, letak dekat tempat biasa
pun nampak kemas."

SECTION 7 - VOICE & DELIVERY
Spoken delivery in Malay at a brisk, conversational UGC pace. Keep the voice natural
and matched to the existing frame mood. Fill the 10-second beat without dead air,
but do not overact or break the frame's realism.

SECTION 8 - CTA & END FRAME
No final CTA yet. End frame keeps the same avatar, same product position, same visual
direction, and a stable product-readable moment ready for continuation.

SECTION 9 - NO_OVERLAY
NO_OVERLAY. No visual text layer of any kind. Spoken hook/body/CTA must remain
spoken and never be converted into visual copy.
```

---

### SET 2 - 6 SECONDS

```text
SET 2 - 6 SECONDS

SECTION 1 - ROLE & OBJECTIVE
Build a complete 6-second GROK commercial video for TikTok, covering the final
continuation and CTA beat. This continues seamlessly from Set 1 with the same
uploaded-frame identity, product, scene, lighting, and camera logic.

SECTION 2 - PRODUCT TRUTH LOCK
Continue preserving the exact product as shown in the uploaded finished frame. Keep
the same label direction, cap/body proportion, physical scale, hand relationship,
and product placement. Do not invent a different product or rescale it.

SECTION 3 - CONTINUITY & STATE LOCK
Continue directly from the previous prompt set. Do not restart the scene, product
intro, avatar identity, lighting, scale, wardrobe, camera style, or commercial arc.
The uploaded frame remains the source truth for avatar, product, scene, pose, and
composition.

SECTION 4 - VISUAL STORY
Visual action: Avatar performs one final small natural motion, keeps the product
stable and readable, then holds the product for the purchase cue. Narrative function:
finish the same visual moment with a direct CTA.

SECTION 5 - SHOT & CAMERA RULES
Resume inside 0.5–1.0 seconds from the previous spoken seam. Do not restart greeting
or re-introduce the presenter. Maintain frame continuity, lighting direction, product
scale, and camera perspective.

SECTION 6 - SPOKEN DIALOGUE
On-camera presenter says the line directly to camera with visible mouth, lips,
jaw, and facial muscles synchronized from the first moment. No product-only
cutaway during the spoken line: "Kalau nak standby satu, tap tengok harga sekarang, boss."

SECTION 7 - VOICE & DELIVERY
Spoken delivery in Malay at a brisk, conversational UGC pace. Keep the CTA clear,
direct, and natural. No dead air, no rushed ending, no clipped final phrase.

SECTION 8 - CTA & END FRAME
Deliver the spoken CTA naturally: "Tap tengok harga sekarang, boss." End frame must
hold the same product and avatar-frame continuity, with product visible and believable.

SECTION 9 - NO_OVERLAY
NO_OVERLAY. No visual text layer of any kind. Spoken hook/body/CTA must remain
spoken and never be converted into visual copy.
```

---

## 12. Example Final Polished Output: INGREDIENTS, GROK 16s [10,6]

### SET 1 - 10 SECONDS

```text
SET 1 - 10 SECONDS

SECTION 1 - ROLE & OBJECTIVE
Build a complete 10-second GROK commercial video for TikTok, covering the opening
asset-set assembly beat. This is the opening segment of a continuous two-part video;
combine the uploaded ingredient images according to their asset roles and establish
the product-led story.

SECTION 2 - PRODUCT TRUTH LOCK
Use the product reference image (image_1) as the highest authority for product
identity. Preserve product packaging, label, cap, body shape, material, color,
product scale, and category. Avatar or style images must never redesign, recolor,
resize, relabel, duplicate, or replace the product.

SECTION 3 - CONTINUITY & STATE LOCK
Use the explicit asset role map. image_1 is PRODUCT_REFERENCE and highest
authority for product truth and scale. image_2 is AVATAR_REFERENCE and controls
identity, wardrobe, and pose DNA. No style image is uploaded in this path, so
derive mood, environment, lighting, and surface only from SCENE_CONTEXT.
Product truth outranks avatar identity, and avatar identity outranks environment.
If any image role is ambiguous, do not silently guess.

SECTION 4 - VISUAL STORY
Visual action: Avatar appears in the SCENE_CONTEXT-guided environment, interacts
naturally with the product reference, keeps the product readable, and presents
the compact standby cue. Narrative function: assemble the separate images into
one coherent product-led UGC scene without blending roles incorrectly.

SECTION 5 - SHOT & CAMERA RULES
Use controlled handheld UGC framing. Keep the avatar identity stable, product
truth stable, and SCENE_CONTEXT influence limited to environment and mood. No
morphing between images, no product redesign from environment cues, no avatar
face drift, no label blur, and no inconsistent scale.

SECTION 6 - SPOKEN DIALOGUE
On-camera presenter says the line directly to camera with visible mouth, lips,
jaw, and facial muscles synchronized from the first moment. No product-only
cutaway during the spoken line:
"Letak dekat meja pun nampak kemas, kecil je, senang capai bila perlu, tak makan
ruang."

SECTION 7 - VOICE & DELIVERY
Spoken delivery in Malay at a brisk, conversational UGC pace. Keep the presenter
talking naturally across the full 10 seconds with real breaths between phrases. Fill
the beat without rushing or creating dead air.

SECTION 8 - CTA & END FRAME
No final CTA yet. End frame keeps the avatar, product, and scene assembled cleanly
with product label readable and visual roles still intact for Set 2 continuation.

SECTION 9 - NO_OVERLAY
NO_OVERLAY. No visual text layer of any kind. Spoken hook/body/CTA must remain
spoken and never be converted into visual copy.
```

---

### SET 2 - 6 SECONDS

```text
SET 2 - 6 SECONDS

SECTION 1 - ROLE & OBJECTIVE
Build a complete 6-second GROK commercial video for TikTok, covering the final CTA
beat. This continues seamlessly from Set 1 with the same asset-set assembly, same
avatar identity, same product truth, same SCENE_CONTEXT-guided scene, and same commercial
momentum.

SECTION 2 - PRODUCT TRUTH LOCK
Continue using the product reference image (image_1) as highest authority. Product
packaging, cap, label, body shape, material, color, scale, and category must remain
unchanged. Do not let avatar or background/style reference alter the product.

SECTION 3 - CONTINUITY & STATE LOCK
Continue directly from the previous prompt set. Do not restart the scene, product
intro, avatar identity, lighting, scale, wardrobe, camera style, or commercial arc.
Preserve the same asset role hierarchy: PRODUCT_TRUTH > AVATAR_IDENTITY > STYLE_SCENE.

SECTION 4 - VISUAL STORY
Visual action: Avatar holds or positions the product for the final clean product-
readable moment, keeps the scene stable, then lands the purchase cue. Narrative
function: final reinforcement and CTA close.

SECTION 5 - SHOT & CAMERA RULES
Resume inside 0.5–1.0 seconds from the previous spoken seam. Maintain avatar identity,
product scale, lighting, camera style, and role-separated asset integrity. No new
background, no new avatar, no product morph, no label distortion.

SECTION 6 - SPOKEN DIALOGUE
On-camera presenter says the line directly to camera with visible mouth, lips,
jaw, and facial muscles synchronized from the first moment. No product-only
cutaway during the spoken line:
"Kalau nak satu yang senang standby, tap tengok harga sekarang, boss."

SECTION 7 - VOICE & DELIVERY
Spoken delivery in Malay at a brisk, conversational UGC pace. Keep CTA clear, direct,
and natural across the full 6 seconds. Do not rush or clip the final phrase.

SECTION 8 - CTA & END FRAME
Deliver the spoken CTA naturally: "Tap tengok harga sekarang, boss." End frame holds
product as clean hero, avatar identity stable, product truth intact, style/background
supportive only.

SECTION 9 - NO_OVERLAY
NO_OVERLAY. No visual text layer of any kind. Spoken hook/body/CTA must remain
spoken and never be converted into visual copy.
```

---

## 13. What AI Sebelah Must Do

AI sebelah mesti behave sebagai **senior video prompt compiler**, bukan creative writer bebas.

### 13.1 Required Parse Order

```text
1. Identify engine.
2. Identify duration.
3. Lookup block plan dari jadual_durasi (WPS_Blocking_Template).
4. Identify intake_mode: HYBRID / FRAMES / INGREDIENTS.
5. Normalize intake_mode:
   - HYBRID      → PRODUCT_ONLY     → HYBRID_PRODUCT_ANCHOR_MODE
   - FRAMES      → READY_FRAME      → READY_FRAME_MODE
   - INGREDIENTS → ASSET_SET        → REFERENCE_SET_MODE
5. Classify uploaded assets dan assign asset role map.
6. Lock product truth (PRODUCT_REFERENCE = highest authority).
7. Lock avatar/frame/style authority.
8. Identify language → lookup WPS table.
9. Assign dialogue budget per block (Safe Words sebagai minimum target).
10. Build storyline/storyboard.
11. Split dialogue per block ikut budget.
12. Output final 9-section prompt per set.
```

---

### 13.2 Do Not Do These

AI sebelah must not:

- Treat Hybrid / Frames / Ingredients as generic prompt styles.
- Rebuild a ready frame from scratch.
- Ignore uploaded avatar in Ingredients mode.
- Declare `image_3: STYLE_SCENE_REFERENCE` when no third style image is uploaded.
- Treat image order as role authority; role binding is explicit, order alone is not.
- Let background/style image override product truth.
- Use `image_1` as default AVATAR — repo default is `image_1: PRODUCT_REFERENCE`.
- Collapse GROK 16s into one 16s prompt.
- Use `[8,8]` for GROK 16s.
- Use `[10,6]` for Google Flow 16s.
- Mix 8s and 10s blocks in one Google Flow render.
- Put runtime metadata inside engine-facing prompt.
- Put `block_plan`, `output_mode`, `prompt_set_count`, `safe_max_words`, avatar pool wording, source-mode taxonomy, atau WPS numbers inside the prompt body.
- Convert spoken hook/body/CTA into overlay text when `overlay_allowed:false`.
- Use English/internal labels inside Malay spoken dialogue such as "family shelf", "shelf cue", "product hero", atau "b-roll".
- Budget dialogue untuk total duration — mesti per block.

---

### 13.3 Required Output Behavior

#### Single-block duration

```text
SINGLE PROMPT
SET 1 - [duration] SECONDS
SECTION 1 - ROLE & OBJECTIVE
...
SECTION 9 - NO_OVERLAY
```

#### Multi-block duration

```text
MULTI-PROMPT SET

SET 1 - [duration] SECONDS
SECTION 1 - ROLE & OBJECTIVE
...
SECTION 9 - NO_OVERLAY

SET 2 - [duration] SECONDS
SECTION 1 - ROLE & OBJECTIVE
...
SECTION 9 - NO_OVERLAY
```

Every block must be independently copy-paste ready.

---

## 13. Final Handoff Format to Operator

Final delivery to operator should contain:

```text
[Final copy-paste prompt block(s)]

QA: VERIFICATION PASSED — [mode] | [date]
```

If there are unresolved gaps:

```text
⚠️ Gap: [one-line issue operator must confirm]
```

If there are warnings:

```text
⚠️ Warning: [one-line warning that affects generator output]
```

Do not include:

- internal routing notes
- full pre-flight logs
- debug JSON
- full compliance checklist
- work order text
- storyboard working notes
- master narrative brief

Unless operator explicitly asks.

QA status line must appear **outside** the copy-paste prompt blocks — not inside Section 9.

---

## 13.1 QA Fail Conditions for Final Prompt Body

Fail final output if any engine-facing prompt body contains:

- unresolved avatar source references
- avatar pool wording or selection instructions
- source-mode taxonomy such as Hybrid intake, Frames mode, Ingredients mode, or source mode
- WPS values
- `block_plan`
- `prompt_set_count`
- debug JSON
- runtime metadata

For HYBRID output, fail final output if the prompt body does not contain one concrete approved Malaysian adult presenter description.

---

## 14. Final Checklist

Before accepting the final polished prompt:

- [ ] Intake mode correctly identified (HYBRID / FRAMES / INGREDIENTS).
- [ ] Hybrid = product photo only + one resolved concrete approved Malaysian adult presenter description in the final prompt body.
- [ ] Frames = one completed frame, continuation/motion-delta only.
- [ ] Ingredients = multiple images with explicit asset role map.
- [ ] Ingredients asset role map: `image_1: PRODUCT_REFERENCE` (repo default).
- [ ] If only two Ingredients images are uploaded, `style_scene_source: SCENE_CONTEXT_ONLY` is declared, or any stray missing `image_3` is auto-normalized away before final output.
- [ ] Product truth priority enforced (PRODUCT > AVATAR > STYLE).
- [ ] Avatar source correctly resolved.
- [ ] Style/background limited to mood/environment only.
- [ ] Engine identified.
- [ ] Duration identified.
- [ ] Block plan derived dari jadual_durasi — not hand-authored.
- [ ] GROK 16s uses `[10,6]`.
- [ ] Google Flow 16s uses `[8,8]`.
- [ ] Google Flow 8s and 10s lanes not mixed in one render.
- [ ] Language identified → WPS table looked up.
- [ ] Dialogue budget assigned per block (Safe Words as minimum target).
- [ ] Single-block output emits one complete 9-section prompt.
- [ ] Multi-block output emits separate complete 9-section prompt per block.
- [ ] Continuation set does not restart the scene.
- [ ] CTA lands in final set.
- [ ] Section 9 is `NO_OVERLAY`.
- [ ] Hook/body/CTA not converted into on-screen text when overlay is false.
- [ ] No internal metadata, source-mode taxonomy, avatar pool wording, or unresolved selection instructions leaked into engine-facing prompt.
- [ ] Final output is copy-paste ready for video engine generator.
- [ ] QA status line is outside the prompt block, not inside Section 9.

---

**End of corrected report — v2**
