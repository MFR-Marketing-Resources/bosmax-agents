---
name: bosmax-notion-row-intake-adapter
description: >
  BOSMAX Notion Row Intake Adapter — Structured intake layer that converts compact
  Notion Copywriting Landbank rows into internal BOSMAX pipeline fields. Invoked
  automatically when input contains Notion-style column keys (Product:, Mode:, Angle:,
  Hook:, Subhook:, USP 1:, CTA:, Visual Seed:, Output:). Returns a clean intake object
  for the normal Route A SELLING_POSTER flow. Does NOT generate prompts. Does NOT
  pass rows through as final prompt output. Does NOT ask Notion to store instructions.
---

# BOSMAX NOTION ROW INTAKE ADAPTER — SKILL
## Role: Structured Intake Parser | Notion → BOSMAX Pipeline Bridge
## Schema: v1.0 | Authority: SUPREME_SYSTEMS_ARCHITECT

---

## PURPOSE

Notion Copywriting Landbank rows are compact structured data only.
This adapter converts that structured data into BOSMAX pipeline fields deterministically.
The adapter is the intelligence layer between Notion rows and the Route A pipeline.

**Notion row = compact data.**
**BOSMAX = expansion, product truth, compliance, and poster assembly.**
**Image generator = receives final polished prompt only.**

Do not treat compact Notion rows as final image prompts.
Do not return a template skeleton with unfilled placeholders.
Do not push prompt instruction work back into Notion.

---

## APPEND-ONLY DATABASE INTENT DETECTION

This skill has two distinct operating lanes:

1. `NOTION_ROW_TO_PROMPT`
   - Existing lane.
   - Use when the operator pastes one compact Notion row for prompt generation.
2. `APPEND_ONLY_DELTA_CSV`
   - Governance lane.
   - Use when the operator asks to tambah row database, update database, append
     landbank, tambah CSV Notion, add import rows, continue Poster ID numbering,
     continue Landbank Row ID numbering, or prepare CSV for Notion import.

If the request sounds like database growth rather than single-row prompt generation,
default to `APPEND_ONLY_DELTA_CSV` and apply the mandatory gate below before any CSV
row generation.

---

## NOTION DATABASE STATE GATE — MANDATORY FOR APPEND JOBS

For `APPEND_ONLY_DELTA_CSV`, do not generate CSV rows until current database state
has been proven.

Required proof surface in the current session:

- live Notion query / API / browser inspection, OR
- operator-supplied fresh export / snapshot from the target database in the
  current session with enough fields to verify numbering and collisions

Minimum state that must be captured:

1. target database name and URL or database ID
2. schema for import-relevant properties
3. current row count
4. ID property name and type
5. whether the numbering field is:
   - Notion auto-generated `Unique ID` / auto-increment, OR
   - CSV-controlled custom ID such as `Poster ID` / `Landbank Row ID`
6. highest existing custom ID and max numeric suffix
7. latest batch marker if the database exposes one
8. collision scan against existing IDs and stable row keys

Blocked mode:

- If current database state is not available, ABORT append generation.
- If schema is ambiguous, ABORT append generation.
- If the ID property type cannot be determined, ABORT append generation.
- If collision risk cannot be ruled out, ABORT append generation.

Abort message shape:

```
APPEND BLOCKED — live Notion database state not verified.
Need current database proof before BOSMAX may generate append CSV rows.
Missing: [database state items].
```

`100-row landbank` or any other repo prose snapshot is historical context only.
It is never sufficient proof for append numbering.

Authoritative protocol:
- `.claude/protocols/notion-csv-append-protocol.md`

---

## TRIGGER DETECTION

Invoke this adapter when input contains three or more of these structured column keys:

```
Product:
Mode:
Angle:
Hook:
Subhook:
USP 1:
USP 2:
USP 3:
CTA:
Visual Seed:
Output:
```

Detection is case-insensitive and trims leading/trailing whitespace from values.
Partial rows (missing some columns) are accepted — map what is present, apply defaults
for what is absent per the DEFAULT RESOLUTION TABLE below.

---

## FIELD MAPPING — DETERMINISTIC

Map each Notion column to its BOSMAX pipeline field:

| Notion Column | BOSMAX Field | Notes |
|---|---|---|
| `Product` | `product_name_raw` → STEP 0 product lookup input | Normalise to canonical name (see NAMING RULES) |
| `Mode` | `subject_mode` | See MODE MAPPING below |
| `Angle` | `angle_group_id` | Pass verbatim to CPD and scene-engine as commercial context signal |
| `Hook` | `copywriting.hook` | Operator-supplied hook — overrides registry default for this request |
| `Subhook` | `copywriting.subhook` | Operator-supplied subhook — must be passed to scene-engine; do not drop |
| `USP 1` | `copywriting.usp_1` | Benefit chip text — inject verbatim |
| `USP 2` | `copywriting.usp_2` | Benefit chip text — inject verbatim |
| `USP 3` | `copywriting.usp_3` | Benefit chip text — inject verbatim |
| `CTA` | `copywriting.cta` | CTA text — system enforces TikTok "Tap" rule; override if user supplies "Klik" |
| `Visual Seed` | `operator_scene_direction` | Scene direction for bosmax-scene-engine; do not treat as copy |
| `Output` | Platform + format + image_goal inference | See OUTPUT INFERENCE below |
| `Commercial Lane` | `compliance_lane` | If present, validate against product YAML compliance.lane |
| `Compliance Status` | `copy_compliance_status` | If present and ≠ APPROVED: WARN before proceeding |

---

## NAMING RULES — CANONICAL PRODUCT NAME

The canonical product name for this product family is:

```
Minyak Warisan Tok Cap Burung
```

The following are recognised aliases and must be normalised:

| Input alias | Normalised output name |
|---|---|
| Minyak Warisan Cap Burung | Minyak Warisan Tok Cap Burung |
| Minyak Warisan Tok Cap Burung | Minyak Warisan Tok Cap Burung (unchanged) |
| Tok Cap Burung | Minyak Warisan Tok Cap Burung |
| Cap Burung | Minyak Warisan Tok Cap Burung |
| Minyak Cap Burung | Minyak Warisan Tok Cap Burung |

Rules:
- Accept old alias as lookup input → product_name_raw (for STEP 0 lookup)
- Normalise to canonical name for all output, prompt generation, and user-facing text
- All final prompt output must use: **Minyak Warisan Tok Cap Burung**
- Do not expose the alias in final generated prompt — only the canonical name
- The alias normalisation must be transparent to the user; no blocking step required

---

## MODE MAPPING

```
Notion Mode value                        → subject_mode
─────────────────────────────────────────────────────────────────
"Product-only poster"                    → product_only
"Product only"                           → product_only
"Product-only"                           → product_only
"Avatar + Product"                       → avatar_product
"Presenter + Product"                    → avatar_product
(any value containing "product only")    → product_only
(absent / null)                          → product_only (default — no avatar signal)
```

---

## OUTPUT INFERENCE

Parse the `Output` column value to infer:

```
If Output contains "TikTok" or "TikTok Shop":
  → platform = "TikTok Shop Malaysia"
  → language = "Malay" (default for TikTok Shop MY)
  → image_goal = "SELLING_POSTER" (poster keyword implied)

If Output contains "9:16" or "9:16 poster" or "poster prompt":
  → format = "9:16 vertical, 1080×1920px, sRGB"
  → image_goal = "SELLING_POSTER"

If Output contains "Shopee":
  → platform = "Shopee MY"
  → format = "1:1, 2000×2000px, sRGB"
  → image_goal = "SELLING_POSTER"

If Output is absent:
  → platform = "TikTok Shop Malaysia" (default)
  → format = "9:16 vertical, 1080×1920px, sRGB" (default)
  → image_goal = "SELLING_POSTER" (default for poster rows)
```

---

## DEFAULT RESOLUTION TABLE

For absent or null Notion columns, apply these defaults before passing to pipeline:

```
Absent column         Default resolution
──────────────────────────────────────────────────────────────────────────
Mode                → subject_mode = product_only
Output              → platform = TikTok Shop Malaysia, format = 9:16
language            → Malay (TikTok Shop Malaysia default)
image_goal          → SELLING_POSTER
archetype           → CPD_BEST_FIT (bosmax-commercial-poster-director auto-selects)
subject_mode        → product_only (no avatar unless Mode explicitly says avatar)
Commercial Lane     → DIRECT (default for Minyak Warisan Tok Cap Burung)
Compliance Status   → UNVERIFIED (warn user if row used without APPROVED status)
```

---

## CTA ENFORCEMENT RULE

TikTok Shop Malaysia CTA must use "Tap" not "Klik".

```
IF copywriting.cta contains "Klik":
  → Replace "Klik" with "Tap" (e.g., "Klik Tengok Harga" → "Tap Tengok Harga")
  → Log internally: [CTA AUTO-CORRECT: Klik → Tap for TikTok Shop MY]
  → Do not block the pipeline; correct silently

IF copywriting.cta is null or absent:
  → Default: copywriting.cta = "Tap Tengok Harga"
```

---

## COPY CONTAMINATION PRE-CHECK

Before passing copywriting fields to the pipeline, run this fast contamination scan:

```
Scan: Hook, Subhook, USP 1, USP 2, USP 3, CTA for forbidden terms.

HARD BLOCK (ABORT row, do not proceed):
  - "menyembuhkan" / "merawat" / "mengubati" / "sembuh" / "jaminan" / "terbukti klinikal"
  - These are forbidden health claim verbs for traditional remedy category

CONTAMINATION WARNING (warn, offer to proceed with fix):
  - "roll-on" / "roller ball" / "rollerball" / "WG40" / "30ml" / "5ML" / "10ML"
  - "BOSMAX" or "Serum" in USP fields (BOSMAX Serum bleed from legacy copywriting)

If HARD BLOCK detected:
  → ABORT this row
  → Surface exact forbidden term and field name
  → "Baris ini mengandungi klaim kesihatan yang dilarang dalam field [field name]:
     '[forbidden term]'. Sila tulis semula sebelum guna baris ini."
  → Do not proceed until copy is fixed

If CONTAMINATION WARNING detected:
  → Flag the field and term
  → Ask: "USP [X] mengandungi '[term]' — ini nampak seperti data dari produk lain.
     Boleh boss sahkan ini betul untuk Minyak Warisan Tok Cap Burung?"
  → Wait for confirmation before proceeding
```

---

## OUTPUT — INTAKE OBJECT

After mapping and defaults, this adapter returns a structured intake object to the BOSMAX orchestrator for normal Route A SELLING_POSTER flow:

```yaml
notion_row_intake:
  # PRODUCT
  product_name_raw: "[from row, normalised to canonical]"
  product_name_canonical: "Minyak Warisan Tok Cap Burung"

  # ROUTING
  task_mode: "IMAGE"
  image_goal: "SELLING_POSTER"
  subject_mode: "product_only"  # or avatar_product if Mode says so
  platform: "TikTok Shop Malaysia"
  language: "Malay"
  format: "9:16 vertical, 1080×1920px, sRGB"

  # COMMERCIAL CONTEXT
  angle_group_id: "[from row Angle field]"
  compliance_lane: "DIRECT"
  copy_compliance_status: "[from row or UNVERIFIED]"

  # COPYWRITING (operator-supplied — takes precedence over registry defaults)
  copywriting:
    hook: "[from row Hook]"
    subhook: "[from row Subhook, null if absent]"
    usp_1: "[from row USP 1]"
    usp_2: "[from row USP 2]"
    usp_3: "[from row USP 3]"
    cta: "[from row CTA, Tap-enforced]"

  # SCENE DIRECTION
  operator_scene_direction: "[from row Visual Seed, null if absent]"

  # FLAGS
  flags:
    alias_normalised: true   # if input product name was an alias
    copy_contamination_check: "PASSED" | "WARNED" | "BLOCKED"
    cta_corrected: false | true
```

Pass this object to BOSMAX orchestrator PRE-FLIGHT STEP 0 as the intake data source.
Normal Route A SELLING_POSTER flow proceeds from here.

---

## WHAT THIS ADAPTER DOES NOT DO

```
❌ Does not generate image prompts
❌ Does not generate append CSV rows without live database state proof
❌ Does not treat last-known row counts as current Notion truth
❌ Does not populate Notion auto-generated Unique ID / auto-increment fields in CSV
❌ Does not restart custom Poster ID / Landbank Row ID numbering from stale snapshots
❌ Does not emit full replacement CSV files for append jobs unless operator explicitly requests full reimport
❌ Does not return template skeletons with {{PLACEHOLDER}} unfilled
❌ Does not require Notion to store long prompt instructions
❌ Does not push overlay copy decisions back to Notion
❌ Does not override product truth from products/*.yaml
❌ Does not override image_prompt_locks from product YAML
❌ Does not override compliance guardrails
❌ Does not expose internal BOSMAX field names to user in normal flow
❌ Does not require Notion rows to contain archetype, module_stack, or format specs
```

---

## INTEGRATION WITH ROUTE A SELLING_POSTER

After this adapter returns the intake object, proceed normally:

```
notion_row_intake object
  → BOSMAX PRE-FLIGHT STEP 0 (product lookup using product_name_canonical)
  → STEP 1 fields already resolved from intake object (skip NLU parsing)
  → STEP 1A defaults already applied
  → STEP 1B assumptions: declare alias normalisation if active
  → STEP 2 validation (CHECK 1 etc.) against resolved fields
  → Route A → bosmax-subject-dna → bosmax-commercial-poster-director → bosmax-scene-engine
  → bosmax-compliance-gate → bosmax-final-output-agent → User
```

Key handoffs:
- `copywriting.hook` and `copywriting.subhook` → scene-engine TOP ZONE
- `copywriting.usp_1/2/3` → scene-engine LOWER ZONE (chip stack)
- `copywriting.cta` → scene-engine BOTTOM ZONE (CTA button)
- `operator_scene_direction` → scene-engine STEP 2 BUILD SCENE (primary scene input)
- `angle_group_id` → CPD (archetype selection context signal)

---

## APPEND-ONLY DELTA CSV LAW

When this skill is used for database growth tasks instead of prompt generation:

- Default mode = `APPEND_ONLY_DELTA_CSV`
- Generate new rows only; never export the entire database as a replacement CSV
- If the target ID field is a custom text/number field such as `Poster ID` or
  `Landbank Row ID`, continue from the verified live high-water mark
- If the target ID field is a Notion-managed `Unique ID` / auto-increment field,
  leave it blank in CSV and let Notion populate it
- Validate parseability, duplicate IDs, ID continuity, and collision risk before
  finalizing any CSV
- Emit a manifest and QA checklist with source database proof
- If live connector access is unavailable and no fresh operator snapshot exists,
  remain blocked; do not guess numbering

Forbidden behavior:

- using repo snapshots as numbering authority
- generating a full replacement CSV for a simple append request
- assuming Notion merge/update semantics by key
- manually filling Notion-generated unique ID columns
- skipping the manifest

For exact checklist, manifest fields, and blocked-mode rules, follow:
- `.claude/protocols/notion-csv-append-protocol.md`

---

*BOSMAX Notion Row Intake Adapter | v1.0 | 2026-06-14*
*Active for: products/MINYAK_WARISAN_TOK_CAP_BURUNG_25ML.yaml*
*Template reference: templates/poster/03A-P1_PRODUCT_ONLY_COPY_LANDBANK_POSTER.md*
