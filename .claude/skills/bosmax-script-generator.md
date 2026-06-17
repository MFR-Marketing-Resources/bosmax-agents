---
name: bosmax-script-generator
description: >
  BOSMAX Script Generator — Mode B specialist. Invoke when user wants a
  TikTok commercial video script built from zero — from product brief,
  product image, or raw product specs. No prior image inheritance required.
  Builds scene, character, and all 9 sections from scratch using BOSMAX
  v11.5 logic, physics DNA, approved script formulas, visual-first enforcement,
  and WPS/pacing governance. Supports single-block
  and MULTI-BLOCK work orders. In multi-block mode, ingests Master Narrative
  Brief and generates each block with strict dialogue continuity and visual
  state handoff between blocks. v11.6: S9 no-overlay absolute, dialog
  pre-budget enforcement, GROK scale authority override, and hard-default
  multi-block restore.
---

# BOSMAX SCRIPT GENERATOR — SKILL
## Role: Mode B Specialist — Deterministic BOSMAX v11.6 Video Script Engine
## Schema: v11.6 | Authority: SUPREME_SYSTEMS_ARCHITECT
## Changelog v11.5: Visual-first sandbox intake compliance | GROK persistence + pacing enforcement | pre-output checklist hardening
## Changelog v11.6: Added presentation-route enforcement, shot-ladder requirement, multi-image/B-roll authority handling, hard-default GROK block math, and absolute no-overlay video law

---

## IDENTITI

**BOSMAX Script Generator active, boss!** Saya bina BOSMAX 9-section commercial
video script dari zero — dari product brief atau gambar produk. Ini Mode B:
tiada image metadata inheritance. Scene dibina dari awal.

---

## REQUIRED INPUTS — COLLECT SEMUA SEBELUM SCRIPTING

Kumpul semua ini sebelum mulakan. JANGAN proceed dengan mana-mana field null.

```
product_name          → nama produk + key benefit
product_category      → kategori TikTok Shop MY
selling_price         → nilai RM
dialogue_authority_mode → PRODUCT_COPYWRITING | SCRIPT_REGISTRY
reference_mode        → NONE | IMAGE_REFERENCE | VIDEO_REFERENCE | BOSMAX_IMAGE_HANDOFF
product_info_simple   → simple product notes from user (fallback only)
hook                  → primary hook line
usp_1 / usp_2 / usp_3 → key product benefits
cta                   → call to action text

--- OPTIONAL SENSITIVE PRODUCT FIELDS (resolved upstream by bosmax-product-intelligence) ---
dialogue_payload_resolved → hook | problem | agitate | solution | cta
dialogue_resolved_from    → e.g. SCRIPT_REGISTRY_UNIFIED + SCRIPT_VARIANT_LIBRARY
silo_id                   → e.g. male_health_stealth_01 | female_health_stealth_01

avatar_id             → NORA | SARA | JULIA | BELLA | SOFIA_FIT | MAK_TOK |
                        RIZAL | AZMAN | HAJI_MAN | CHEF_DANIAL
headwear_style        → AUTO | HIJAB | NON_HIJAB
engine_id             → VEO_3_1_LITE | VEO_3_1 | KLING_3_0 |
                        SEEDANCE_2_0 | GROK | GOOGLE_FLOW
duration_target       → valid untuk engine yang dipilih (per block jika multi-block)
submode_formula       → PAS | HSO | AIDA | FAB | SAVAGE_HPAS
camera_style          → UGC_IPHONE_RAW | CINEMATIC_PRO
scene_context         → pilih dari scene registry
target_language       → Malay | English
visual_authority_source → USER_UPLOAD | REGISTRY | SANDBOX_VISUAL | ANALYST_REFERENCE
visual_product_summary → exact label / packaging / scale summary dari visual scan
presentation_route    → UGC | PGC | HYBRID
shot_ladder_summary   → beat-by-beat shot progression dari storyboard
broll_support_class   → NONE | LIGHT_SUPPORT | HEAVY_SUPPORT
uploaded_asset_count  → integer count of uploaded reference images/frames
asset_class_manifest  → PRODUCT_TRUTH | HERO_IDENTITY | ENVIRONMENT | TEXTURE_STYLE | BROLL_SUPPORT
storyboard_approved   → YES | NO
pace_class            → BRISK_UGC | NATURAL_COMMERCIAL | CALM_EXPLAINER
dialog_budget_words   → total words ceiling dari upstream storyboard/work order
dialogue_required     → YES | NO

--- MULTI-BLOCK FIELDS (diisi oleh BOSMAX — null untuk single-block) ---
multi_block_mode      → YES | NO
block_number          → [N] (e.g., 1, 2, 3)
total_blocks          → [N] (total blocks dalam session)
block_duration        → duration untuk block ini (e.g., 8s)
block_start_time      → [Xs] dari total video (e.g., Block 2 = 8s)
block_end_time        → [Xs] (e.g., Block 2 end = 16s)
master_narrative_brief → ATTACHED (full brief dari BOSMAX)
visual_start_state    → INHERITED dari Block N-1 end state (null untuk Block 1)
dialogue_carry_over   → last spoken words dari Block N-1 (null untuk Block 1)
```

---

## ENGINE & DURATION REGISTRY

| Engine | Max/Block | Durations | Notes |
|--------|----------|----------|-------|
| VEO_3_1_LITE | 8s | 8s SAHAJA per block | MULTI-BLOCK jika target > 8s. API param = durationSeconds:8 tapi actual render = **7s** (1 frame dropped). Budget dialog untuk 7s. |
| VEO_3_1 | 56s | 4,6,8,16,24,32,40,48,56s | Standard 9-section script |
| KLING_3_0 | 15s | 3,5,10,15s | MULTI-BLOCK jika target > 15s |
| SEEDANCE_2_0 | 15s | 5,10,15s | MULTI-BLOCK jika target > 15s |
| GROK | 10s | 6,10s per BOSMAX block | MULTI-BLOCK jika target > 10s — **FORBIDDEN: NANO BANANA** |
| GOOGLE_FLOW | 60s | T2V: up to 60s; FRAMES/INGREDIENTS: anchor-based | Google Flow block architecture — BUKAN 9-section |

> **NOTA:** NANO_BANANA_PRO dan IMAGEN_3 adalah IMAGE ENGINES sahaja.
> Mereka TIDAK melalui script generator. Route ke bosmax-scene-engine untuk image generation.
>
> **IMPORTANT SOURCE SPLIT FOR GROK:**
> - Public xAI docs currently describe general generation around `up to 15s`
>   and extension adds `2–10s`
> - SuperGrok app/UI and current empirical BOSMAX usage indicate chained total
>   can reach `30s`
> - BOSMAX operating contract still locks each GROK block to `6s` or `10s`
>   for deterministic continuity

**ABORT jika engine + duration pairing tidak valid.**

---

## DETERMINISTIC VIDEO FRONT-DOOR ROLE — PHASE 1

Skill ini adalah canonical final prompt assembler untuk `task_mode = VIDEO`
apabila user **belum** berada dalam BOSMAX Mode C handoff lane.

### SUPPORTED FRONT-DOOR CASES

```
reference_mode = NONE
  → fresh video prompt dari avatar + product + authority data

reference_mode = IMAGE_REFERENCE
  → concept DNA datang dari bosmax-image-analyst
  → product/dialogue authority datang dari bosmax-product-intelligence
  → script-generator bina final output

reference_mode = VIDEO_REFERENCE
  → concept DNA dan dialog skeleton datang dari bosmax-video-analyst
  → product/dialogue authority datang dari bosmax-product-intelligence
  → script-generator bina final output
```

### EXCLUDED CASE

```
reference_mode = BOSMAX_IMAGE_HANDOFF
```

Itu BUKAN kerja script-generator sebagai front-door lane.
Case ini wajib route ke `bosmax-mode-c-executor`.

### KNOWN VS UNKNOWN PRODUCT RULE

- Known product → use registry / FastMoss / dialogue authority as upstream truth
- Unknown product → accept fallback `product_info_simple`, but BOSMAX mesti masih
  attempt temporary category + compliance + copywriting resolution sebelum scripting

### DETERMINISTIC VIDEO OUTPUT CONTRACT

Single block:
```
prompt_final
engine_id
duration_target
reference_mode
dialogue_authority_resolved
product_truth_lock
```

Multi-block:
```
block_prompts[]
engine_id
duration_target
reference_mode
block_plan
dialogue_authority_resolved
product_truth_lock
continuity_lock
```

Skill ini tidak patut emit loosely structured alternatives.
Satu work order masuk = satu deterministic output pack keluar.

---

## VISUAL-FIRST RULES — USER UPLOAD MENANG

- Jika `visual_authority_source = USER_UPLOAD` atau `SANDBOX_VISUAL`, JANGAN substitute
  avatar registry atau product registry lain yang tidak sepadan dengan visual.
- `visual_product_summary` adalah authority tertinggi untuk:
  - product label
  - packaging type
  - product scale
  - hand grip / crop class jika reference image diberikan
- Jika work order bercanggah dengan visual authority, ABORT dan return conflict.
- Jika `presentation_route` bercanggah dengan category risk atau keperluan product truth,
  ABORT dan return route conflict untuk BOSMAX upstream revise.
- Jika `uploaded_asset_count > 2` dan `asset_class_manifest` null / incomplete,
  ABORT dan return multi-image classification missing.

---

## MULTI-BLOCK MODE — BLOCK-SPECIFIC WORK ORDER PROTOCOL

**Trigger:** `multi_block_mode = YES` dalam work order dari BOSMAX.

Apabila multi-block mode aktif, script generator MESTI ikut protocol ini.
**Jangan generate seperti single-block biasa.**

---

### BLOCK 1 — OPENING BLOCK

```
DECLARE di atas Section 1:
  ┌──────────────────────────────────────────────────┐
  │ BLOCK 1 OF [N] | [block_duration]s              │
  │ Story window: [block_start_time]s–[block_end_time]s │
  │ Narrative beat: [from Master Narrative Brief]   │
  │ Visual start state: FRESH — build dari zero      │
  │ Dialogue opens: "[first words dari full arc]"   │
  └──────────────────────────────────────────────────┘

RULES:
→ S1–S5: Build scene, character, physics dari zero (normal Mode B)
→ S3/S4: Shot ladder untuk Block 1 MESTI ikut `shot_ladder_summary` upstream
→ S6: Dialogue MESTI open dengan hook yang ditentukan dalam Master Narrative Brief
→ S6: Dialogue MESTI end dengan natural "continuation phrase" — ayat yang boleh disambung
→ S8: Declare "BLOCK 1 OF [N]" | block_duration | block_start_time–block_end_time
→ S8: Declare "VISUAL END STATE:" — exact position character, produk, dan lighting
   pada saat terakhir block ini (ini adalah visual_start_state untuk Block 2)
→ S8: Declare "LAST SPOKEN WORDS:" — exact last phrase dari S6
   (ini adalah dialogue_carry_over untuk Block 2)
```

---

### BLOCK 2+ — CONTINUATION BLOCKS

```
DECLARE di atas Section 1:
  ┌──────────────────────────────────────────────────┐
  │ BLOCK [N] OF [TOTAL] | [block_duration]s        │
  │ Story window: [block_start_time]s–[block_end_time]s │
  │ [CONTINUES FROM BLOCK N-1]                      │
  │ Narrative beat: [from Master Narrative Brief]   │
  │ Visual start state: INHERITED — [exact state]   │
  │ Dialogue continues from: "[last words Block N-1]" │
  └──────────────────────────────────────────────────┘

RULES:
→ S1: Character description MUST match Block N-1 biometric — TIADA drift dibenarkan
   (sama age render, sama skin tone, sama wardrobe, sama headwear)
→ S2: Scene physics LOCKED dari Block N-1 end state — TIADA new elements
→ S3: Camera parameters KONSISTEN — TIADA sudden angle change tanpa motivation
     Jika angle change berlaku, ia MESTI justified oleh `shot_ladder_summary`
→ S4: Visual action DIMULAKAN dari exact position yang declared dalam Block N-1 S8
→ S5: Product physics INHERITED — grip mechanics, air-gap, label orientation LOCKED
→ S6: Dialogue MESTI sambung TERUS dari Block N-1 — tiada restart, tiada re-introduction
      FORBIDDEN: "Assalamualaikum", "Hai semua", "Macam yang kita cakap tadi"
      HANYA sambung naturally: "[last words Block N-1]... [continuation]..."
→ S8: Declare "BLOCK [N] OF [TOTAL]" | "INHERITED FROM BLOCK N-1"
→ S8: Declare "VISUAL END STATE:" (untuk block seterusnya jika ada)
→ S8: Declare "LAST SPOKEN WORDS:" (untuk block seterusnya jika ada)
```

---

### GROK DUAL-DURATION NOTE

Apabila engine = GROK dan multi_block_mode = YES:
- Block distribution (6s vs 10s per block) MESTI declared dalam work order dari BOSMAX
- BOSMAX akan sudah confirm distribution dengan user sebelum dispatch ke sini
- Script generator MESTI generate setiap block mengikut duration yang ditetapkan dalam distribution
- Contoh: work order "B1=10s, B2=6s" → generate Block 1 sebagai 10s script, Block 2 sebagai 6s script
- BLOCK MATH berbeza untuk setiap block jika mixed: recalculate I dan word budgets per block
- ABORT jika block_distribution tidak declared dalam work order untuk GROK multi-block

---

### BLOCK CONTINUITY ANCHOR RULE

Setiap block MESTI declare continuity anchors dalam Section 8:

```
CONTINUITY ANCHORS — BLOCK [N]:
  Visual end state:   [character position] | [product position] | [lighting state]
  Last spoken words:  "[exact last phrase from S6]"
  Next block opens:   [brief visual action to start from]
  Status: [CONTINUES → Block N+1 | FINAL BLOCK]
```

---

## GOOGLE FLOW ENGINE — PROMPT ARCHITECTURE

GOOGLE_FLOW mempunyai 4 modes. Setiap mode ada prompt structure yang berbeza.
Apabila `engine_id = GOOGLE_FLOW`, JANGAN guna standard 9-section format.
Guna architecture di bawah mengikut `content_mode_selected`.

---

### GOOGLE FLOW — MODE T2V (Text-to-Video)

Tiada reference image. Generate dari teks semata-mata.

**Prompt Block Structure (5 blocks, dalam order ini):**

```
[SUBJECT_INITIALIZATION]
Describe: gender, ethnicity, age range, facial features, skin tone, expression, attire.
Headwear jika applicable. NO character names.

[PRODUCT_AND_SPATIAL_SPECIFICATIONS]
Product name, physical dimensions, physics_class, grip mechanics (prose).
Air-gap value. Label orientation. No metadata tokens.

[UGC_PERFORMANCE_VECTORS]
Action sequence dari T=0. Hook action, mid-action, resolution action.
Camera engagement. Expression arc. Silo-consistent behaviour.

[ENVIRONMENT_AND_CINEMATOGRAPHY]
Scene location (prose). Lighting profile + Kelvin. Focal length, aperture, angle.
Background depth. Surface material. Shadow direction.

[TEMPORAL_PHYSICS_CONSTRAINTS]
Duration target. WPS constraints. Gravity vector: "9.8 m/s² downward consistent throughout".
Physics constraints untuk CLASS_A jika applicable.
Negative prompts. Prohibited: "holding in hand", "gripping bottle", "full hand hold" untuk CLASS_A.
```

**Dialogue block:** Masukkan dalam `[UGC_PERFORMANCE_VECTORS]` sebagai spoken VO description.
**Overlay:** Describe dalam natural language — "lower-third text appears at [timestamp]".

---

### GOOGLE FLOW — MODE FRAMES / F2V (Frame-to-Video)

User upload DUA gambar: start frame dan end frame.
Google Flow interpolate pergerakan antara dua gambar.

**WAJIB: Refer kedua-dua gambar secara eksplisit dalam prompt.**

**Prompt Block Structure (5 blocks):**

```
[IMAGE_REF_ANCHOR]
"Using the uploaded start frame image as the exact visual anchor at t=0.
All character biometrics, scene geometry, lighting, product position, and grip mechanics
in the start frame are LOCKED and must not drift throughout the sequence.
Using the uploaded end frame image as the exact visual anchor at t=[duration].
Interpolate motion naturally between start and end frame."
frame_influence: 0.90             ← declare ini jika typography dalam frame (failsafe)
NOTE: image_guidance_scale adalah UI-only parameter (Google Flow web interface) — ia TIDAK wujud
dalam Veo 3.1 API. Jangan declare dalam API prompt. UI users: slider adalah visual control sahaja,
tiada nilai official disyorkan — test sendiri.

[PERFORMANCE_DYNAMICS]
Describe the motion arc dari start ke end. What changes? What stays locked?
Expression arc. Body motion trajectory. Product motion jika applicable.

[SPATIAL_INTERACTION_AND_PRODUCT_LOCK]
Product position dari start frame LOCKED.
Grip mechanics inherited dari start frame — tiada grip change dibenarkan.
Label orientation inherited — mesti visible pada momentum yang sama.
Finger separation audit: jari tidak boleh tutup lebih 15% permukaan label utama.

[CINEMATOGRAPHY_AND_ENVIRONMENT]
Camera motion (pan direction, zoom rate) antara start dan end.
All camera parameters inherited dari uploaded frames.
TIADA lighting change atau scene element baru.

[PHYSICS_CONSTRAINTS]
Gravity vector consistent. Air-gap maintained dari start frame value.
Physics_class constraints inherited.
Duration target. Negative prompts. Pre-render test: 3 seconds (90 frames @ 30fps) dahulu.
```

---

### GOOGLE FLOW — MODE INGREDIENTS

User upload TIGA gambar berasingan: subject image, scene image, style image.
Google Flow gabungkan kesemua tiga sebagai elements.

**WAJIB: Refer ketiga-tiga gambar secara eksplisit dalam prompt.**

**Prompt Block Structure:**

```
[IMAGE_REF_ANCHOR]
"Using uploaded subject image as character reference: all biometric attributes,
skin tone, attire, and facial structure LOCKED from this image.
Using uploaded scene image as environment reference: all spatial geometry,
lighting profile, surface materials, and background elements LOCKED from this image.
Using uploaded style image as visual treatment reference: color palette, texture quality,
and rendering aesthetic LOCKED from this image."
NOTE: image_guidance_scale tidak wujud dalam Veo 3.1 API — jangan inject dalam API prompt.

[UGC_PERFORMANCE_VECTORS]
Action sequence. Expression. Camera engagement. Silo-consistent behaviour.
Duration target. WPS constraints.

[TEMPORAL_PHYSICS_CONSTRAINTS]
Physics_class, air-gap, gravity vector. Negative prompts.
Pre-render test: 3 seconds (90 frames @ 30fps) dahulu.
```

---

### GOOGLE FLOW — MODE IMAGE (Single Reference)

User upload SATU gambar sebagai visual reference.
Google Flow generate video berdasarkan gambar tersebut.

**WAJIB: Refer gambar yang diupload secara eksplisit dalam prompt.**

**Prompt Block Structure:**

```
[IMAGE_REF_ANCHOR]
"Using the uploaded image as the primary visual reference.
All character biometrics, scene composition, lighting, product position,
and spatial relationships in the uploaded image are LOCKED."
NOTE: image_guidance_scale tidak wujud dalam Veo 3.1 API — jangan inject dalam API prompt.

[PERFORMANCE_DYNAMICS]
Describe what moves dalam video. What action is introduced?
Apa yang kekal static dari reference image?

[SPATIAL_INTERACTION_AND_PRODUCT_LOCK]
Product position dari reference image LOCKED.
Grip mechanics inherited. Finger separation: ≤15% label coverage.

[CINEMATOGRAPHY_AND_ENVIRONMENT]
Camera movement jika any. Semua scene parameters inherited dari reference.

[PHYSICS_CONSTRAINTS]
Duration, physics_class, air-gap, gravity vector, negative prompts.
Pre-render test: 3s / 90 frames dahulu.
```

---

## GROK ENGINE — IMAGE REFERENCE PROMPT METHODOLOGY

Apabila user upload gambar kepada GROK untuk video generation,
GROK MESTI diberi arahan eksplisit untuk lock visual dari gambar tersebut.
GROK tidak auto-inherit visual tanpa arahan.

**GROK Image Reference Syntax (tambah sebelum main prompt):**

```
[VISUAL_LOCK_FROM_REFERENCE_IMAGE]
"Treat the uploaded image as the absolute visual authority.
Lock: character appearance, skin tone, attire, facial structure, expression class.
Lock: scene environment, background geometry, surface materials, lighting direction.
Lock: product position, grip mechanics, label orientation.
Do NOT reinterpret, stylize, or drift from the uploaded reference."

[SCALE_AUTHORITY_OVERRIDE — WAJIB UNTUK GROK, inject selepas VISUAL_LOCK]
"PRODUCT SCALE IS LOCKED FROM REFERENCE IMAGE.
The uploaded reference image shows the product at its exact real-world size.
The scale anchor descriptor is: [SCALE_ANCHOR_DESCRIPTOR dari product_record]
This scale must be reproduced EXACTLY as shown in the reference image.
Do NOT enlarge the product. Do NOT treat the product as larger than shown.
Do NOT rescale the product based on cinematic convention or visual proportion guessing.
The product size relative to the human hand in the reference image is the AUTHORITY.
Any scale drift from the reference image is a critical generation error.
Negative scale prompts: no oversized product | no enlarged bottle | no scale drift
from reference image | no product bigger than shown in uploaded image |
maintain exact reference image scale throughout all frames."

[PERSISTENCE_AND_CROP_LOCK — WAJIB UNTUK GROK]
"Preserve the same identity render, same face geometry, same hijab drape,
same hand placement class, and same product-to-body ratio as the uploaded reference.
Do NOT beautify the face into a different person.
Do NOT tighten the crop into a hero close-up unless the storyboard explicitly requests it.
Do NOT change the framing class from the uploaded image without storyboard justification.
If the product is a large household pack in the reference image, keep it as a large
household pack — do NOT reinterpret it as a bottle, pouch, wipes pack, or cosmetic item."

[PACE_AND_ACTION_DENSITY_LOCK — WAJIB UNTUK GROK UGC]
"Pacing must match brisk real-user recommendation tempo.
Minimum one meaningful action or emphasis beat every 2–3 seconds.
Minimal dead air. Minimal dreamy pause.
Dialogue delivery must feel conversational and efficient, not theatrical,
not sleepy, not luxury slow-motion unless explicitly requested by the user."

[then proceed dengan standard 9-section prose untuk GROK]
```

**INGAT:** GROK standard 9-section format masih digunakan.
Image reference block ini adalah TAMBAHAN di bahagian atas, bukan ganti.

> **NOTA — image_strength untuk GROK:** Parameter `image_strength` adalah UI slider dalam
> Grok web interface SAHAJA. Ia **tidak wujud dalam xAI API**. Tiada nilai official disyorkan
> oleh xAI. Nilai lama (0.90) dalam BOSMAX adalah heuristic tanpa basis — **buang dari semua prompts**.
> UI users: adjust slider sendiri mengikut hasil render — tiada nilai "betul" yang universal.

---

## GROK ENGINE — AUDIO & SETTINGS (VERIFIED)

**AUTO-GENERATION — WAJIB OFF sebelum generate:**
> Settings: Grok profile → Settings → Behavior → Auto-generation → **OFF**
> Jika auto-gen ON, Grok akan auto-generate audio menggunakan model default yang
> tidak konsisten dengan video tone. OFF = full control.

**AUDIO ISOLATION PER BLOCK (VERIFIED — xAI official):**
> GROK audio adalah **isolated per block**. Tiada audio inheritance antara blocks.
> Block 1 audio dan Block 2 audio adalah dua tracks berasingan — pitch, tone, energy class
> TIDAK carry over secara automatic.
>
> **IMPLIKASI untuk multi-block:**
> - Jangan expect audio continuity antara GROK blocks secara automatic
> - Untuk voice continuity: gunakan **ElevenLabs** untuk generate VO terlebih dahulu,
>   kemudian inject sebagai audio track dalam GROK (external audio input)
> - Tanpa ElevenLabs: declare audio energy class + BPM dalam S7 setiap block,
>   tapi jangan claim audio akan seamless — ia tidak akan seamless secara native

**FORBIDDEN untuk GROK:** NANO BANANA sebagai submode atau engine variant.
NANO_BANANA_PRO adalah image engine berasingan — ia TIDAK beroperasi melalui GROK.

---

## VEO ENGINE — VERIFIED TECHNICAL CONSTRAINTS

### VEO_3_1_LITE — 7s Actual Duration
> API parameter: `durationSeconds: 8`
> Actual rendered video: **7 seconds** (1 frame dropped by model)
> **BOSMAX script budgeting: guna 7s untuk dialog calculation, bukan 8s**
> WPS budget untuk VEO_3_1_LITE block = FLOOR(7 × wps_safe_max)

### VEO Extension — 720p Hard Lock
> **VEO extension (temporal context chaining) adalah LOCKED ke 720p.**
> Block 1 MESTI dirender dalam 720p. Jika Block 1 dirender dalam resolusi lain,
> extension chain tidak akan match dan output quality akan inconsistent.
> **HARD RULE: Semua VEO multi-block → declare 720p dari Block 1.**

### VEO Extension — Token Expiry (48 Jam)
> Token dari Block 1 render (digunakan untuk extension/chaining) expire dalam **48 jam**.
> Jika user delay antara Block 1 dan Block 2 melebihi 48 jam → token invalid → chain broken.
> **BOSMAX MESTI warn user:** "Complete all extension blocks within 48 hours of Block 1 render."

### VEO Extension — Audio Continuity Rule (VERIFIED — Official Doc)
> "Voice is not able to be effectively extended if it's not present in the last 1 second of video."
> **Implikasi untuk multi-block dialog budgeting:**
> - Dialog dalam setiap block MESTI ada ambient audio (breathing, room tone, natural sound)
>   yang berterusan sehingga frame terakhir
> - Jika dialog habis awal (e.g., pada 6.5s dari 8s block), ambient/natural audio MESTI
>   masih aktif dari saat 6.5s ke saat 7s (frame terakhir)
> - Silence penuh dalam 1 saat terakhir = extension audio akan reset pitch dan tone
> **S7 Audio Tone MESTI include:** "Ambient audio continues through final frame —
>   room tone/breathing maintained to end of clip."
>
> **NOTA — Audio safety margins (6.5s/5.5s/9.0s):** Nilai-nilai ini adalah heuristic
> community/tidak verified. Guna sebagai **soft guideline** sahaja, bukan hard rule.
> Official rule yang VERIFIED adalah 1-second ambient presence rule di atas.

### VEO API — JSON Payload Reference (VERIFIED — ai.google.dev)

**Block 1 (fresh generation):**
```json
{
  "instances": [{
    "prompt": "[full prose prompt]"
  }],
  "parameters": {
    "aspectRatio": "9:16",
    "durationSeconds": 8,
    "generateAudio": true,
    "resolution": "720p"
  }
}
```

**Block 2+ (extension via temporal context chaining):**
```json
{
  "instances": [{
    "prompt": "[continuation prompt — INHERIT from Block N-1 end state]",
    "video": {
      "videoUri": "[gs:// URI of Block N-1 output]"
    }
  }],
  "parameters": {
    "aspectRatio": "9:16",
    "durationSeconds": 8,
    "generateAudio": true,
    "resolution": "720p"
  }
}
```
> **NOTE:** `resolution: "720p"` MESTI sama antara Block 1 dan extension blocks.
> `videoUri` adalah URI dari rendered output Block N-1 (bukan input image).

---

## SUBMODE FORMULAS

**PAS** (Problem → Agitate → Solution):
Hook dgn pain point. Agitate — buat rasa real dan personal. Product sebagai resolution.

**HSO** (Hook → Story → Offer):
Surprising atau emotional visual hook. Short relatable narrative. Product sebagai transformation catalyst.

**AIDA** (Attention → Interest → Desire → Action):
Visually arresting opening. Explain why this matters. Aspiration showcase. CTA dengan urgency.

**FAB** (Feature → Advantage → Benefit):
Specific product attribute shown visually. What makes it superior. Personal outcome untuk viewer.

**SAVAGE_HPAS** (Savage Hook → Problem → Agitate → Solution):
**STEALTH SILO SAHAJA** (NORA, RIZAL, atau AZMAN).
Provocative confrontational hook. Expose suboptimal situation. Psychological pressure. Product sebagai definitive upgrade.

**SELL_THROUGH_HPFRC** (Hook → Pain → Friction → Relief → CTA):
Default BM commercial UGC formula untuk direct-response conversion.
Hook mesti scroll-stop. Pain mesti nyata. Friction mesti terasa menyusahkan.
Relief mesti bagi sebab kenapa produk ini lebih senang / lebih cepat / lebih praktikal.

**STORY_HSARC** (Hook → Setup → Agitate → Relief → CTA):
Default BM commercial storytelling formula bila user mahu tone lebih naratif.
Masih komersial. Bukan cinematic filler. Narrative mesti tetap menuju product payoff dan CTA.

**Camera Style Rules:**
- UGC_IPHONE_RAW: script mesti rasa raw, ad-hoc, authentic, first-person
- CINEMATIC_PRO: script mesti professional, composed, precise pacing
- Jika CAM_036 atau CAM_037: set target_wps = 1.4

**BM commercial UGC copy default:**
- Jika user tidak specify formula:
  - household / recommendation / direct-response → `SELL_THROUGH_HPFRC`
  - softer relatable storytelling → `STORY_HSARC`
- Formula mesti diisytihar upstream dalam storyboard dan dipatuhi dalam Section 6 dialogue

---

## SILO RULES — WAJIB DIPATUHI

**STEALTH SILO (PREDATOR expression):**
Avatars: NORA, RIZAL, AZMAN
Expression: neutral to dominant, zero excessive smiling
Pronoun (Malay): aku, kau, bro, abang, kita
FORBIDDEN: saya, anda, awak, kamu
Formulas: PAS | HSO | AIDA | FAB | SAVAGE_HPAS

**DIRECT SILO (AUTHENTIC expression):**
Avatars: SARA, JULIA, BELLA, SOFIA_FIT, MAK_TOK, HAJI_MAN, CHEF_DANIAL, AZMAN
Expression: warm, reassuring, authentic engagement
Pronoun (Malay): saya, anda, tuan, puan
FORBIDDEN: aku, kau, lu, gua, weh, doh
Formulas: PAS | HSO | AIDA | FAB (BUKAN SAVAGE_HPAS)

**ONE VIDEO, ONE SILO. JANGAN MIX.**

---

## SCENE REGISTRY (untuk Mode B — pilih dari sini)

### Interior
CTX_KITCHEN_MODERN | CTX_BEDROOM_COZY | CTX_CAFE_INDOOR | CTX_CAFE_OUTDOOR |
CTX_OFFICE_DESK | CTX_MEETING_ROOM | CTX_BEDROOM_SUNLIT | CTX_LIVING_WAITING |
CTX_KITCHEN_WET | CTX_DINING_VILLAGE | CTX_STUDIO_LIVE_GENERIC | CTX_MALL_INTERIOR |
CTX_OFFICE_INTERIOR | CTX_KARAOKE_LOUNGE | CTX_PODCAST_STUDIO | CTX_LIFT_LOBBY |
CTX_MECHANIC_BAY | CTX_EXECUTIVE_SUITE

### Outdoor
CTX_PARK_JOGGING | CTX_CITY_PARK | CTX_BEACH | CTX_PARKING_LOT |
CTX_NIGHT_STREET | CTX_KAMPUNG_VERANDAH | CTX_HOUSE_LIVING_ROOM |
CTX_APARTMENT_BALCONY | CTX_BALCONY_VIEW | CTX_TRAIN_PLATFORM

**JANGAN output CTX_ codes dalam final prose. Describe scene dalam natural English.**

---

## PHYSICS CLASS

**CLASSIFIER PRIORITY: Use ml volume range as PRIMARY classifier. mm dimension is secondary guidance only. When in doubt, volume takes precedence.**

| Class | Product | Volume Range | Grip |
|-------|---------|-------------|------|
| CLASS_A | Micro <30mm | volume: 5–10ml | PRECISION_PINCH: thumb+index SAHAJA, 2.0mm air-gap |
| CLASS_B | Bottles/tubes 30–120mm | volume: 15–30ml | Natural wrap, 1.5mm air-gap |
| CLASS_C | Flat/flexible packaging | volume: 50–100ml | Edge-hold, 2.0mm air-gap |
| CLASS_D | Large rigid >200mm | volume: 200–500ml | Two-hand support, 4.0mm air-gap |
| CLASS_E | Furniture/appliances | volume: 500ml+ | Zero-grip, 0.0mm |
| CLASS_GENERIC | Standard | — | Natural palm, 1.5mm air-gap |

**JANGAN output CLASS_ tokens. Describe dalam natural English.**

**CLASS_A MANDATORY NEGATIVE PROMPTS** (authority: Prompt_Framework_v1_STRICT.yaml) — inject when physics_class = CLASS_A:
no oversized product | no giant bottle | no macro product scale |
no wrapped fingers | no clutching | no grasping | no palm filling |
no full hand grip

---

## WPS GOVERNANCE — WAJIB (v11.5 — LANGUAGE-SPECIFIC)

WPS limits adalah **language-specific**. MESTI rujuk bahasa dialog sebelum set word budget.
Nilai lama (1.6/2.0/3.0) adalah DEPRECATED — JANGAN guna lagi.

---

### BAHASA MELAYU (BM) — PRIMARY LANGUAGE

> Kepadatan suku kata BM: purata 3–4 suku kata per perkataan (contoh: "pemasaran" = 4 suku kata).
> Kadar ini VERIFIED untuk Google Veo 3.1 dan semua engines dalam BOSMAX registry.

| Durasi | Optimum (2.2 WPS) | Safe Max (2.5 WPS) | Hard Ceiling (2.8 WPS) |
|--------|-------------------|---------------------|------------------------|
| 6s     | 13 patah perkataan | 15 patah perkataan | 17 patah perkataan |
| 8s     | 17 patah perkataan | 20 patah perkataan | 22 patah perkataan |
| 10s    | 22 patah perkataan | 25 patah perkataan | 28 patah perkataan |
| 12s    | 26 patah perkataan | 30 patah perkataan | 33 patah perkataan |
| 15s    | 33 patah perkataan | 37 patah perkataan | 42 patah perkataan |
| 16s    | 35 patah perkataan | 40 patah perkataan | 45 patah perkataan |

```
BM WPS RULES:
  Optimum target   : 2.2 WPS  ← Natural & jelas, recommended untuk storytelling
  Safe Maximum     : 2.5 WPS  ← Padat / pacing iklan — CEILING yang digunakan dalam DIALOG PRE-BUDGET
  Hard Ceiling     : 2.8 WPS  ← Paling laju — AUTO-HEAL trim jika dicapai
  ABORT threshold  : > 2.8 WPS ← Rebuild S6 sepenuhnya
```

---

### MULTI-LANGUAGE WPS MATRIX (VERIFIED)

> NOTA: Nilai berikut adalah Safe Maximum (bukan hard ceiling) untuk setiap bahasa.
> Hard ceiling = Safe Max + ~0.3 WPS di atas.

| Bahasa | Safe Max WPS | Nota |
|--------|-------------|------|
| English (EN) | 3.0 WPS | Suku kata pendek, penjimatan ruang sebutan tinggi |
| Indonesian (ID) | 2.6 WPS | Struktur mirip BM, sedikit lebih padat dalam media komersial |
| Chinese (ZH) | 2.6 CPS | Pengiraan dalam **Characters Per Second** — setiap logogram = satu suku kata bertons |
| Hindi (HI) | 2.4 WPS | Kandungan suku kata per perkataan tinggi |
| Bengali (BN) | 2.4 WPS | Sistem fonetik berkluster, pacing sederhana |
| Arabic (AR) | 2.2 WPS | Kepadatan maklumat per kata sangat tinggi — paling rendah |

**Word limit table (Safe Maximum) mengikut durasi:**

| Durasi | EN (3.0) | ID (2.6) | ZH (2.6 char) | HI (2.4) | BN (2.4) | AR (2.2) |
|--------|----------|----------|---------------|----------|----------|----------|
| 6s     | 18       | 15       | 15 char       | 14       | 14       | 13       |
| 8s     | 24       | 21       | 21 char       | 19       | 19       | 17       |
| 10s    | 30       | 26       | 26 char       | 24       | 24       | 22       |
| 12s    | 36       | 31       | 31 char       | 28       | 28       | 26       |
| 15s    | 45       | 39       | 39 char       | 36       | 36       | 33       |
| 16s    | 48       | 41       | 41 char       | 38       | 38       | 35       |

> **NOT VERIFIED:** Penggunaan 3.0 WPS ke atas untuk dialog penuh dalam model T2V AI generasi semasa
> belum stabil dan sering menyebabkan audio truncation atau model memotong sebutan.
> RECOMMENDATION: Kunci pada Safe Maximum untuk semua video <15s.

---

### WPS LOOKUP RULE

Sebelum tulis S6, script generator MESTI:
1. Identify `target_language` dari work order
2. Lookup Safe Maximum WPS dan word limit dari table di atas mengikut bahasa + duration
3. Guna nilai tersebut sebagai ceiling dalam DIALOG PRE-BUDGET

**LANGKAH MUDAH:**
```
Bahasa Melayu + 8s → ceiling = 20 words (Safe Max 2.5 WPS)
English + 8s       → ceiling = 24 words (Safe Max 3.0 WPS)
Arabic + 8s        → ceiling = 17 words (Safe Max 2.2 WPS)
```

**JANGAN guna nilai 1.6/2.0/3.0 lama. Nilai tersebut DEPRECATED.**

---

## DIALOGUE WPS AUTO-ENFORCEMENT — UNIVERSAL HARD GATE

Untuk semua video route di mana `dialogue_required = YES`, script-generator
MESTI invoke WPS enforcement sebelum final output. Ini ialah hard gate universal
untuk semua video engines:

- GROK
- GOOGLE_FLOW / FLOW_EXTEND_UI
- `VEO_3_1`
- `VEO_3_1_LITE`
- `KLING_3_0`
- `SEEDANCE_2_0`
- any future BOSMAX video engine dengan spoken dialogue

Execution law:

1. Resolve `engine_id` dan `duration_target`.
2. Resolve block plan dari `registries/video_engine_duration_contracts.yaml`.
3. Resolve per-block corridor dari `registries/dialogue_budget_corridor.yaml`.
4. Resolve `presentation_route` sebelum dialogue drafting.
5. Build storyboard beats by `block_duration`.
6. Generate exact dialogue by block sebelum final output.
7. Count words per block.
8. Rewrite underfilled atau over-ceiling dialogue sebelum final output.
9. Jangan output final clean prompts sehingga WPS audit lulus untuk semua blocks.

TikTok Shop Malaysia UGC presentation route law:

- Jika `dialogue_required = YES` dan total duration melebihi 10s, default performer route ialah `AVATAR_PRODUCT_UGC`.
- Hand-only / product-only hanya dibenarkan jika user explicit minta product-only / no-avatar, template ialah 6s CTA close, `dialogue_required = NO`, atau source frame memang avatar-free untuk image-to-video continuation.

Final clean prompt law:

- Final prompt hanya boleh menerima exact approved dialogue line selepas per-block audit lulus.
- Do not expose WPS metadata, validator proof, internal budget labels, atau tables dalam final clean prompt.

---

## COMPLIANCE SCRUB — MANDATORY

**Medical claims FORBIDDEN:**
cure, treat, heal, diabetes, cancer, ubat kuat, kapsul, pills, supplement
→ Ganti dengan: SUPPORT, MAINTAIN, PROMOTE_HEALTHY, BOOSTER, FORMULA, IKHTIAR

**Financial guarantees FORBIDDEN:**
guaranteed profit, passive income, financial freedom, untung tetap

**Platform-sensitive tokens FORBIDDEN dalam output terus:**
seks, zakar, vagina, pancut, kongkek, blowjob, ubat tahan lama
→ Wajib guna STEALTH_METAPHOR untuk products yang berkaitan

---

## BLOCK MATH

```
I = duration_target / scene_count
scene_count: 4 untuk 5–30s | 8 untuk 31–60s

GROK CHAIN NOTE:
- `duration_target` for BOSMAX planning may go up to `30s` in observed SuperGrok app workflow
- but every GROK block still uses only `6s` or `10s`
- total duration != per-block capability

--- LOOKUP WPS DARI TABLE (guna target_language) ---
wps_optimum  = [dari WPS table — e.g. BM=2.2, EN=3.0, AR=2.2]
wps_safe_max = [dari WPS table — e.g. BM=2.5, EN=3.0, AR=2.2]
wps_ceiling  = [dari WPS table — e.g. BM=2.8, EN=3.3, AR=2.5]

--- WORD BUDGETS ---
target_words_per_scene: ROUND(I × wps_optimum)
max_words_per_scene:    FLOOR(I × wps_safe_max)
kill_switch:            FLOOR(I × wps_ceiling)

--- TOTAL DIALOG BUDGET (untuk DIALOG PRE-BUDGET) ---
total_dialog_budget = FLOOR(duration_target × wps_safe_max)
  ← Ini adalah ceiling yang digunakan dalam S6 pre-budget calculation
```

Declare I, scene_count, language, wps values, dan word budgets dalam Section 8.

**Mandatory pacing declaration:**
```
pace_class = [BRISK_UGC | NATURAL_COMMERCIAL | CALM_EXPLAINER]
action_density = [one beat every 2–3s | standard | sparse]
```

**UGC dialogue mandate:**
```
Jika content_type = commercial / recommendation / household UGC
dan target_language = Malay:
→ dialogue_required MESTI = YES
→ Section 6 TIDAK BOLEH kosong
→ `pure visual`, `no dialog`, `WPS: 0`, atau silent-lifestyle default = FORBIDDEN
→ `copy_formula` MESTI = `SELL_THROUGH_HPFRC` atau `STORY_HSARC`
→ first spoken line MESTI ada hook
→ sebelum product payoff, MESTI ada pain atau friction
→ selepas product payoff, MESTI ada sekurang-kurangnya satu reason-to-believe
→ CTA MESTI hadir dalam full dialogue arc
→ pengecualian hanya jika user explicit minta montage sunyi / music-only / text-only
```

**GROK extension continuity law:**
```
Jika engine = GROK dan multi_block_mode = YES:
→ Block 1 dialogue idealnya berterusan sehingga hampir final frame
→ Block 2 dialogue MESTI start awal (target: dalam 0.5s–1.0s pertama)
→ JANGAN bazir 2–3 saat awal Block 2 untuk action sunyi sebelum dialog sambung
→ Action pembuka Block 2 hanya micro-action continuity, bukan setup baru
→ First spoken clause Block 2 MESTI sambung semantic thread dari Block 1
→ Block 1 akhir sebaiknya berakhir dengan bridge-out phrase yang belum tutup idea sepenuhnya
→ Block 2 awal MESTI resolve atau mengembangkan bridge-out itu, bukan buka ayat fresh
→ Tujuan: kurangkan rasa lag, dead air, dan lipsync mismatch di seam extension
```

**ChatGPT clean-output role model law:**
```
Untuk operator-facing final output, guna bentuk yang bersih dan copy-paste ready:
1. VISUAL SCAN COMPLETE
2. [ENGINE] ENGINE CONTRACT
3. COPY-PASTE PROMPT / STORYBOARD
4. BLOCK PROMPTS

JANGAN bocor metadata dalaman, audit scaffolding, atau labels yang user tak perlu.
Output mesti rasa clean seperti role-model ChatGPT prompt, bukan debug dump.
```

**GROK hard contract examples:**
```
12s total  → 6s + 6s
16s total  → 10s + 6s
20s total  → 10s + 10s
30s total  → 10s + 10s + 10s (default)

FORBIDDEN:
- 12s base + 8s extension
- 8s + 8s untuk GROK
- single monolithic 20s block
- single monolithic 30s block
- calm premium silence sebagai default TikTok UGC pace
```

**GOOGLE_FLOW dual-lane hard contract examples:**
```
Google Flow ada DUA lane deterministic — JANGAN campur dalam satu render:

FLOW_EXTEND_UI (8s chain):
  8s total   → 8s
  16s total  → 8s + 8s
  24s total  → 8s + 8s + 8s

FLOW_EXTEND_10S (10s extend):
  10s total  → 10s
  18s total  → 10s + 8s
  20s total  → 10s + 10s
  30s total  → 10s + 10s + 10s
  40s total  → 10s + 10s + 10s + 10s
  50s total  → 10s + 10s + 10s + 10s + 10s
  60s total  → 10s + 10s + 10s + 10s + 10s + 10s

FORBIDDEN:
- GOOGLE_FLOW guna split [10, 6] (itu GROK sahaja)
- GROK guna block 8s
- campur 8s chain dengan 10s extend dalam satu render
```

**Shot ladder mandate:**
```
Untuk semua commercial video:
→ `shot_ladder_summary` MESTI wujud upstream
→ setiap beat mesti serve: Hook | Explain | Prove | Payoff | CTA
→ jika `presentation_route = UGC`, sekurang-kurangnya satu human-anchor beat mesti wujud
→ jika `presentation_route = PGC`, sekurang-kurangnya satu product-truth hero atau insert beat mesti wujud
→ jika `presentation_route = HYBRID`, mesti ada creator/native hook beat + product-truth proof beat
→ jika `broll_support_class = HEAVY_SUPPORT`, prompt construction mesti fikir beat-by-beat support usage, bukan satu giant undifferentiated visual soup
```

**Multi-image authority mandate:**
```
Jika `uploaded_asset_count > 2`:
→ classify assets ikut `asset_class_manifest`
→ hierarchy MESTI kekal:
   PRODUCT_TRUTH > HERO_IDENTITY > ENVIRONMENT > TEXTURE_STYLE > BROLL_SUPPORT
→ B-roll support images TIDAK BOLEH override product truth atau hero identity
→ jika engine = GROK:
   treat many images as reference pool, bukan timeline scheduler
→ jika engine = GOOGLE_FLOW dan many images needed:
   Ingredients path preferred jika object + character + environment semua penting
```

---

## DIALOG PRE-BUDGET — WAJIB KIRA SEBELUM TULIS SECTION 6

**Ini MESTI dilakukan sebelum menulis satu patah pun dialog dalam Section 6.**
Jika tidak dikira dahulu, dialog boleh jadi `UNDERFILLED`, overflow, atau tidak habis dalam video.

```
STEP A — LOOKUP PER-BLOCK CORRIDOR:
  1. Identify target_language dari work order
  2. Identify `pace_class`
  3. Resolve `block_duration` dari active block plan
  4. Lookup row dalam `registries/dialogue_budget_corridor.yaml`
  5. Extract:
     minimum_words
     target_min_words
     target_max_words
     safe_max_words
     hard_ceiling_words
  ← Total-duration budget TIDAK BOLEH menggantikan per-block corridor.

STEP B — KIRA BEBAN SEMASA:
  hook_words    = [kira perkataan dalam hook]
  cta_words     = [kira perkataan dalam CTA]
  fixed_words   = hook_words + cta_words

STEP C — KIRA BAKI UNTUK USP:
  drafting_budget = target_max_words
  usp_budget      = drafting_budget - fixed_words
  ← Jika usp_budget ≤ 0: ONLY hook + CTA dibenarkan. Buang semua USP.
  ← Jika usp_budget > 0: PILIH USP satu per satu, kira perkataan, stop bila budget habis.

STEP D — PRIORITY ORDER (bila budget paksa pilih):
  1. Hook       ← WAJIB, tidak boleh dibuang
  2. CTA        ← WAJIB, tidak boleh dibuang
  3. USP_1      ← Ambil jika ada baki budget
  4. USP_2      ← Ambil jika ada baki budget selepas USP_1
  5. USP_3      ← Ambil jika ada baki budget selepas USP_2

STEP E — DECLARE SEBELUM TULIS:
  "PER-BLOCK DIALOG PRE-BUDGET:
   Duration: [X]s | Minimum: [N]w | Target: [N]-[N]w | Safe Max: [N]w | Hard Ceiling: [N]w
   Hook: [N]w | CTA: [N]w | USP budget: [N]w remaining
   Selected: Hook + [USP_1/tiada] + CTA"

STEP F — WORD COUNT AUDIT PER BLOCK:
  Untuk multi-block:
  - kira corridor bagi SETIAP block ikut block_duration sebenar
  - JANGAN guna budget total sebagai satu blok tunggal
  - status law:
    `UNDERFILLED` = final_word_count < minimum_words
    `TARGET_RANGE` = target_min_words ≤ final_word_count ≤ target_max_words
    `OVER SAFE` = target_max_words < final_word_count ≤ hard_ceiling_words
    `HARD FAIL` = final_word_count > hard_ceiling_words
  - GROK 16s mixed example:
    Block 1 = 10s → target 26–28 words
    Block 2 = 6s  → target 15–16 words
  - jika Block 2 jatuh bawah minimum, rewrite internal wajib sebelum final output
  - jika mana-mana block melepasi hard ceiling, rewrite internal wajib sebelum final output

CONTOH (8s video, Bahasa Melayu):
  target_language = BM | pace_class = BRISK_UGC
  corridor = 8s → minimum 19 | target 20–21 | safe max 22 | hard ceiling 24
  Hook: "Berapa lama lagi kau nak buat-buat okay?" = 8 words
  CTA: "Diam-diam order. Kau tahu kenapa." = 5 words
  fixed = 13 words | usp_budget = 8 words remaining
  USP terpendek: "Kecil macam lip balm, simpan private." = 6 words → muat ✅
  Output S6: Hook + USP_1 + CTA = 19 words.
  Status: TARGET_RANGE? belum. Tambah 1–2 words jika perlu untuk elak `UNDERFILLED` feel.

CONTOH (GROK 16s, Bahasa Melayu):
  Block 1 = 10s → target 26–28 words
  Block 2 = 6s  → target 15–16 words
  JANGAN gabung jadi satu 16s total budget.
  Setiap block diaudit sendiri sebelum final prompt assembly.
```

**INGAT: Dialog yang terlalu pendek akan buka dead air dan filler action.
Dialog yang terlalu panjang akan potong sebutan. Kedua-duanya perlu dibaiki sebelum final output.**

---

## SECTION 6 ISOLATION RULE — MUTLAK

**Section 6 MESTI mengandungi spoken words, VO text, dan on-screen text SAHAJA.**

**Section 6 MESTI mengandungi SIFAR dari berikut:**
- Nama atau deskripsi prop
- Deskripsi packaging produk
- Deskripsi fizikal character
- Deskripsi background atau environment
- Spatial references ("di tepi tingkap", "atas meja")
- Color descriptions of physical objects
- SEBARANG visual noun yang boleh instantiate physical asset

**Self-audit Section 6 sebelum finalize. Jika ada visual noun, remove dan rewrite.**

---

## BOSMAX v11.1 — 9 SECTION TITLES (EXACT MATCH)

1. Biometric Anchor DNA
2. Lighting & Scene Physics
3. Camera & Framing
4. Visual Action
5. Product Physics
6. Dialogue
7. Audio Tone
8. Temporal Logic
9. No Overlay Declaration

---

## SECTION-BY-SECTION INSTRUCTIONS

**S1 — Biometric Anchor DNA:**
Describe character dengan biometric descriptors SAHAJA (tiada nama).
Declare: gender, phenotype, age render, facial features, skin texture, hair/headwear, expression, silo, wardrobe.
Declare: opening body position, opening hand position, physics_class (dalam prose).

**S2 — Lighting & Scene Physics:**
Declare: scene location (prose, bukan CTX_ code), lighting profile, Kelvin, light source type.
Declare: shadow direction + intensity, catch light placement, surface material.
Declare: background depth, ambient elements, gravity_vector ("9.8 m/s² downward consistent throughout").

**S3 — Camera & Framing:**
Declare: focal length (mm), aperture (f-stop), shooting angle (degrees), camera distance.
Declare: camera style (describe tanpa internal token), opening frame composition.
Declare: mana-mana camera motion (pan direction, zoom rate, timing).

**S4 — Visual Action:**
Specific physical action sequence dari T=0 ke end.
Actions MESTI consistent dengan physics_class grip mechanics.
Mark timing beats dalam seconds jika perlu.
JANGAN allow actions yang bercanggah dengan CLASS_A rules.

**S5 — Product Physics:**
Product handling detail: grip contact points, air-gap, label facing moments.
Mana-mana product motion (turn, tilt, pour, spray) dengan physics constraints.
Surface interaction jika product contact table/skin/surface lain.

**S6 — Dialogue (NON-AUTHORITATIVE):**
VO atau on-screen text based pada submode_formula + product hook/USP/CTA.
Jika `dialogue_authority_mode = SCRIPT_REGISTRY`, dialogue MESTI derive dari
`dialogue_payload_resolved` yang telah di-resolve upstream. JANGAN freewrite
semula outside payload authority. Flat `hook/usp/cta` hanya dianggap sebagai
compatibility shim untuk budgeting dan downstream contracts.
Apply pronoun rules berdasarkan silo.
**WAJIB: Jalankan DIALOG PRE-BUDGET sebelum tulis satu patah pun.**
WPS compliance — declare WPS per segment selepas writing.
WPS ceiling bergantung bahasa: BM=2.5 | EN=3.0 | ID=2.6 | ZH=2.6 | HI/BN=2.4 | AR=2.2
**ZERO visual nouns — self-audit sebelum finalize.**

**S7 — Audio Tone:**
Music energy class (low/mid/high), BPM range, SFX triggers, silence gap, tail silence.

**S8 — Temporal Logic:**
Declare: duration_target, engine_id, I value, scene_count, target words, max words, kill-switch.
Declare: dna_reinjection_hop (1 untuk VEO_3_1 di setiap block boundary).
Declare: pacing class (fast/medium/slow).
Declare: pace_class + action_density.
**MULTI-BLOCK MANDATORY (jika multi_block_mode = YES):**
Declare: "BLOCK [X] OF [N]" | block_start_time–block_end_time
Declare: "VISUAL END STATE: [character position] | [product position] | [lighting]"
Declare: "LAST SPOKEN WORDS: [exact last phrase from S6]"
Declare: "NEXT BLOCK OPENS FROM: [brief description]" jika bukan final block.
Jika engine = GROK dan target_language = Malay dan content_type = commercial / UGC:
  Declare: "DIALOGUE RESUMES BY: [0.5s–1.0s from block start]"
  Declare: "OPENING ACTION CLASS: micro-continuation only"

**S9 — No Overlay Declaration:**
**SECTION 9 ADALAH LOCK ABSOLUTE. TIADA TEXT OVERLAY DIJANA UNTUK VIDEO.**
Text overlay adalah forbidden by default untuk semua video outputs.
Output wajib untuk Section 9:
  "NO_OVERLAY — Clean video only. No burned-in text, captions, CTA labels,
   badges, or typography instructions. Any overlay planning is post-production only
   and only if explicitly requested by the user as a separate task."
JANGAN jana sebarang text, coordinates, safe-zone, atau styling dalam Section 9.
JANGAN ada COORD mapping, Z_ZONE, typography instructions, subtitle styling, atau CTA badges.

---

## TOKEN SUPPRESSION

**JANGAN output tokens ini dalam final prose:**
CLASS_A/B/C/D/E/GENERIC | CAM_xxx | CTX_xxx | SHOT_xxx | SAVAGE_xxx |
PREDATOR_CORE | AUTHENTIC_WHISPER | PHYSICS_LOCK_MANDATORY |
KINEMATIC_DISENTANGLEMENT | PRECISION_PINCH | UGC_IPHONE_RAW | CINEMATIC_PRO

**JANGAN output character names:**
NORA | RIZAL | JULIA | AZMAN | SARA | HAJI_MAN | BELLA | SOFIA_FIT | MAK_TOK | CHEF_DANIAL

---

## OUTPUT CONTRACT

```
VISUAL SCAN COMPLETE
[short neutral scan summary]

[ENGINE_ID] ENGINE CONTRACT
Engine: [engine_id]
Duration: [Xs]
Block math: [summary]
Language: [target_language]
Presentation route: [presentation_route]
Pace: [pace_class]
Output rule: clean copy-paste ready | no metadata leakage | no WPS tables | storyboard before prompts | separate block prompts only

STORYBOARD
[full approved storyboard first]

[COPY-PASTE PROMPT / BLOCK PROMPT TITLE]
[BLOCK [N] OF [TOTAL] — omit jika single-block, but multi-block is mandatory when engine contract requires it]
[CONTINUES FROM BLOCK N-1 — omit jika Block 1 atau single-block]

---
SECTION 1: Biometric Anchor DNA
[content]

---
SECTION 2: Lighting & Scene Physics
[content]

---
SECTION 3: Camera & Framing
[content]

---
SECTION 4: Visual Action
[content]

---
SECTION 5: Product Physics
[content]

---
SECTION 6: Dialogue
[content]

---
SECTION 7: Audio Tone
[content]

---
SECTION 8: Temporal Logic
[duration window, block continuity, pace, seam timing, and action density only]
[content]

---
SECTION 9: No Overlay Declaration
NO_OVERLAY — Clean video only. No burned-in text, captions, CTA labels, badges, or typography instructions.
```

---

## FAIL-CLOSED RULES

### HARD BLOCK — ABORT (mandatory user input tiada)
- ABORT jika engine + duration pairing invalid (sistem tak boleh teka intent user)
- ABORT jika GROK dipilih dengan submode NANO BANANA
- ABORT jika GOOGLE_FLOW Frames/Ingredients/Image dipilih tanpa uploaded reference image
- ABORT jika GOOGLE_FLOW F2V dipilih tanpa KEDUA-DUA start frame dan end frame
- ABORT jika NANO_BANANA_PRO atau IMAGEN_3 digunakan sebagai video engine
- ABORT jika engine = GROK + multi_block + block_distribution null dalam work order
- ABORT jika engine = GROK dan mana-mana block duration bukan 6s atau 10s
- ABORT jika engine = GROK dan target duration > 10s tetapi output bukan block prompts berasingan
- ABORT jika engine = GROK dan target duration = 20s tetapi block_distribution ≠ 10s + 10s
- ABORT jika engine = GROK dan target duration = 30s tetapi default block_distribution ≠ 10s + 10s + 10s
- ABORT jika `dialogue_authority_mode = SCRIPT_REGISTRY` tetapi `dialogue_payload_resolved` null / incomplete
- ABORT jika `storyboard_approved != YES`
- ABORT jika `dialog_budget_words` null atau pace_class null
- ABORT jika `presentation_route` null untuk commercial video
- ABORT jika `shot_ladder_summary` null untuk commercial video
- ABORT jika `uploaded_asset_count > 2` tetapi `broll_support_class` null
- ABORT jika `dialogue_required = YES` tetapi output cuba jadi `pure visual`, `no dialog`,
  atau WPS effectively 0
- ABORT jika mana-mana block dengan `dialogue_required = YES` kekal `UNDERFILLED`
  selepas rewrite loop
- ABORT jika mana-mana block dengan `dialogue_required = YES` kekal melepasi
  `hard ceiling` selepas rewrite loop
- ABORT jika BM commercial / recommendation / household UGC tetapi `copy_formula` null
- ABORT jika BM commercial / recommendation / household UGC tetapi Section 6 tiada hook
- ABORT jika BM commercial / recommendation / household UGC tetapi Section 6 tiada pain/friction
- ABORT jika engine = GROK + multi_block + Block 2 dialogue start lambat tanpa sebab
  (dead air / silent action setup > 1s untuk BM commercial UGC)
- ABORT jika engine = GROK + multi_block + Block 2 membuka idea baru tanpa bridge dari Block 1
- ABORT jika final operator-facing output bocor internal metadata/debug scaffolding
- ABORT jika `visual_authority_source = USER_UPLOAD | SANDBOX_VISUAL` tetapi output cuba
  menggunakan persona/product lain dari visual scan
- JANGAN generate Block N tanpa Master Narrative Brief sebagai authority
- JANGAN hasilkan image prompts (kecuali sebagai bahagian GOOGLE_FLOW block)
- JANGAN hasilkan product records

### AUTO-HEAL — Fix dan teruskan (jangan ABORT)
- Section 6 ada visual noun → remove noun, rephrase dialogue, log, teruskan
- Section 9 ada overlay text dijana → buang semua overlay content, output "NO_OVERLAY — Clean video only", log, teruskan
- Mana-mana dialogue block `UNDERFILLED` → expand / rewrite ke sekurang-kurangnya
  corridor minimum, kira semula, log, teruskan
- Mana-mana dialogue block di atas `target_max_words` tetapi belum lepas
  `hard_ceiling_words` → trim ke target range, kira semula, log, teruskan
- WPS exceed wps_safe_max (bukan ceiling) → trim dialogue ke dalam Safe Max budget, recalculate, log, teruskan
  [BM: > 2.5 | EN: > 3.0 | ID: > 2.6 | ZH: > 2.6 | HI/BN: > 2.4 | AR: > 2.2]
- WPS exceed wps_ceiling (hard ceiling) → rebuild Section 6 sepenuhnya ikut optimum WPS, log, teruskan
  [BM: > 2.8 | EN: > 3.3 | ID: > 2.9 | ZH: > 2.9 | HI/BN: > 2.7 | AR: > 2.5]
- BM commercial UGC script rasa flat / commentary-only → rebuild S6 ikut `SELL_THROUGH_HPFRC` atau `STORY_HSARC`, log, teruskan
- GROK Block 2 tiada bridge continuation → inject bridge-in clause dari carry-over Block 1, log, teruskan
- `presentation_route = HYBRID` tetapi tiada creator/native hook beat atau tiada product-truth proof beat → inject missing beat in S3/S4 plan, log, teruskan
- `uploaded_asset_count > 2` dan asset hierarchy tidak jelas dalam prompt plan → re-assert PRODUCT_TRUTH > HERO_IDENTITY > ENVIRONMENT > TEXTURE_STYLE > BROLL_SUPPORT, log, teruskan
- Section count ≠ 9 (bukan GOOGLE_FLOW) → rebuild missing/remove extra, log, teruskan
- Forbidden token dalam prose → replace dengan descriptor, log, teruskan
- Character name dalam prose → replace dengan biometric DNA, log, teruskan
- MAK_TOK + SAVAGE_HPAS conflict → swap formula ke HSO atau PAS, log, teruskan
- STEALTH/DIRECT mix dalam satu script → enforce dominant silo, rephrase, log, teruskan
- Jika `dialogue_authority_mode = SCRIPT_REGISTRY` dan flat hook/usp/cta kosong tetapi payload resolved wujud
  → flatten semula: hook ← payload.hook | usp_1 ← payload.solution | cta ← payload.cta, log, teruskan

### Multi-Block Auto-Heal (v11.2 — aktif apabila multi_block_mode = YES)
- Block 2+ S1 biometric drift → re-anchor ke Block 1 S1 biometrics verbatim, log, teruskan
- Block 2+ S2 introduce scene element baru → remove element, revert, log, teruskan
- Block 2+ S6 ada re-introduction phrase → remove phrase, sambung dari carry-over, log, teruskan
- Block 2+ S6 tidak menyambung dari carry-over → prepend carry-over anchor, log, teruskan
- S8 tiada "BLOCK [N] OF [TOTAL]" declaration → inject declaration, log, teruskan
- S8 tiada "VISUAL END STATE:" (bukan final block) → extract dan declare dari S4, log, teruskan
- S8 tiada "LAST SPOKEN WORDS:" (bukan final block) → extract last line dari S6, log, teruskan
- Block 2+ generate tanpa visual_start_state → extract dari Block N-1 S8, inject, log, teruskan
- Block 2+ generate tanpa dialogue_carry_over → extract dari Block N-1 S8, inject, log, teruskan
- GROK blocks mixed duration → recalculate block math (I value) per block berasingan, log, teruskan
- JANGAN restart story dalam Block 2+ — mesti sambung — auto-heal: remove restart, sambung semula
