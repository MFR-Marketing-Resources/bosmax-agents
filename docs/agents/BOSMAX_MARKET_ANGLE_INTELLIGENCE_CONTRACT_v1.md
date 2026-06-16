# BOSMAX Market-Angle Intelligence Contract
# Version: v1
# Authority: BOSMAX Systems Architecture
# Status: ACTIVE — docs-only contract
# Last updated: 2026-06-17
# Governs: Unit 16 — bosmax-market-angle-intelligence (PRE-FLIGHT STEP 0.5, opt-in)

---

## 1. PURPOSE

BOSMAX needs a repeatable upstream intelligence layer that can identify a product,
use existing `product_record` truth, optionally inspect source-backed
market/competitor evidence, and generate a structured `angle_intelligence_pack`
for downstream poster, video, and landbank workflows — so the operator does not
re-explain product angles, hooks, subhooks, USP 1/2/3, CTA, poster direction, or
video dialogue seed every session.

This layer is **intelligence only**. It does not produce final creative.

---

## 2. AGENT NATURE

`bosmax-market-angle-intelligence` is a Claude Code prompt-level skill persona
(`.claude/skills/bosmax-market-angle-intelligence.md`), consistent with every
other BOSMAX unit. It is NOT an autonomous runtime process, scheduler, scraper,
or Notion automation. It runs only inside a human-initiated Claude Code session
when the orchestrator appoints it.

---

## 3. POSITION IN THE PIPELINE

```
PRE-FLIGHT STEP 0    bosmax-product-intelligence   → product_record (truth)
PRE-FLIGHT STEP 0.5  bosmax-market-angle-intelligence (OPT-IN)
                        → angle_intelligence_pack (no final creative)
        ↓ route dispatch unchanged
  Route A poster  → CPD consumes overlay_safe_text → scene-engine
  Route B/D video → storyboard gate → script-generator consumes spoken_dialogue_seed
  Route BULK/landbank → notion_landbank_ready_rows (candidate rows only)
        ↓
  bosmax-compliance-gate  (re-audits ALL final creative — never bypassed)
        ↓ bosmax-final-output-agent → operator
        ↓ (manual, PR #51 governed) append-only delta CSV → Notion
```

STEP 0.5 is **opt-in** and never sits in the mandatory STEP 0 hot path.

---

## 4. TRIGGERS

Run STEP 0.5 ONLY when the operator asks for:

- angle, market angle, research, competitor, landbank, copy pack, angle bank
- riset, analisa pasaran, cari angle, competitor analysis
- hook / subhook / USP / CTA generation from product intelligence
- Route BULK copy-landbank preparation
- `ON_THE_FLY_PRODUCT` with no `angle_taxonomy_file` AND operator asks for angle help

Do NOT trigger for:

- VIDEO_SUPPORT clean image
- Mode C continuity
- product registration only
- single-shot creative where the operator already supplied final copy
- Notion CSV append jobs without an angle generation request

---

## 5. SOURCE / COMPETITOR RESEARCH LAW

Competitor research is optional and source-gated.

- DEFAULT: `competitor_research = NOT_RUN`, `competitor_source_kind = NONE`.
- If no verified source exists:
  - emit zero `competitor_patterns`
  - emit zero sourced `customer_language`
  - candidate angles may still be generated from product truth, approved taxonomy,
    category archetypes, and safe first principles
  - mark those candidates `claim_status: INFERRED` and `proof_required: true`
- Never fabricate a competitor source.
- Allowed source kinds: `NONE`, `FASTMOSS`, `OPERATOR_PASTED`,
  `OPERATOR_SCREENSHOT`, `OPERATOR_EXPORT`, `WEB_EVIDENCE`, `OTHER_VERIFIED`.
- Source adapters may be expanded later. Do **not** hardcode Motion, WebSearch,
  WebFetch, TikTok, Shopee, Lazada, or Meta as guaranteed capabilities; map a
  real, cited source to `WEB_EVIDENCE` / `OTHER_VERIFIED` only when it actually
  exists in the repo/environment.

---

## 6. TAXONOMY LAW

- If `product_record.angle_taxonomy_file` exists, load it first as TIER 1.
- Approved taxonomy wins over the generated pack.
- The generated pack cannot override an approved MCA status.
- `REVIEW_ONLY` stays `REVIEW_ONLY`.
- A conflicting generated angle goes to `blocked_rows` unless the operator
  explicitly promotes it after audit.
- If no taxonomy exists, the generated pack stays `session_only` and must be
  explicitly approved/persisted before it becomes registry truth.

---

## 7. FORBIDDEN CLAIMS LAW

`forbidden_claims` is aggregated from existing authority surfaces only:

- product YAML `label_forbidden`
- product YAML `copywriting_safety.forbidden_phrasing`
- `registries/product_copy_router.yaml` `forbidden_claim_patterns`
- the active product taxonomy's forbidden claim styles / phrase classes (if present)

Do not invent forbidden claims beyond these authorities unless clearly marked
`source: "INFERRED"` with a reason and routed for review.

---

## 8. POSTER VS VIDEO SPLIT

- Poster consumption uses `copy_candidates[].overlay_safe_text`
  (compact, overlay-safe hook / subhook / USP chips / CTA).
- Video consumption uses `copy_candidates[].spoken_dialogue_seed`
  (a seed for `bosmax-script-generator` — NOT a final script).
- Do not reuse poster overlay copy blindly as spoken dialogue.
- Video overlays remain forbidden by default unless explicitly requested elsewhere.

---

## 9. NOTION / LANDBANK BOUNDARY

The skill may emit `recommended_next_action.notion_landbank_ready_rows` as
candidate rows only. It must not:

- create CSV files by itself unless explicitly routed to the Notion append workflow
- write Notion
- update a Notion database
- decide final import numbering

The existing PR #51 governance remains the sole append path: live Notion proof →
delta CSV only → high-water-mark custom ID → collision check → manifest → QA
checklist (`.claude/protocols/notion-csv-append-protocol.md`). `blocked_rows`
must never enter the landbank.

---

## 10. COMPLIANCE BOUNDARY

The pack pre-classifies risk for routing convenience only. It does NOT replace or
weaken `bosmax-compliance-gate`. Every final creative is still re-audited by the
terminal gate. The pack is never a compliance bypass. No compliance hard gate is
modified by this layer.

---

## 11. PRODUCT_RECORD POINTERS (v1)

The only product_record schema additions for this layer are two optional,
nullable pointer fields in `products/_SCHEMA.yaml`:

- `angle_taxonomy_file` — path to the product's approved angle taxonomy registry.
- `competitor_research_policy` — `ALLOWED | RESTRICTED | REVIEW_ONLY` (or blank).

Generated angle packs are NOT stored inside `product_record`. Existing product
YAML bodies are not mutated.

---

## 12. OUTPUT CONTRACT

The pack shape is defined by `registries/angle_intelligence_pack.schema.yaml`.
Key invariants:

- `pack_header.session_only: true`, `pack_header.do_not_autopublish: true` by default
- `source_status.competitor_research` defaults `NOT_RUN`
- `risk_class` enum is `GREEN | YELLOW | RED | REVIEW_ONLY`
- `copy_candidates` separate `overlay_safe_text` (poster) from
  `spoken_dialogue_seed` (video)
- `forbidden_claims` aggregated, not invented

---

## 13. NON-SCOPE (V1)

```
❌ live scraper
❌ TikTok / Shopee / Lazada / Meta API integration
❌ auto-persisted angle packs
❌ final creative generation (poster prompt / video script)
❌ Notion write
```

---

## 14. RELATED FILES

| File | Purpose |
|------|---------|
| `.claude/skills/bosmax-market-angle-intelligence.md` | Unit 16 persona |
| `registries/angle_intelligence_pack.schema.yaml` | Pack output schema |
| `.claude/skills/bosmax-product-intelligence.md` | Unit 02 — STEP 0 resolver (upstream) |
| `registries/product_copy_router.yaml` | route_mode, risk, forbidden_claim_patterns |
| `registries/mwcb_copywriting_angle_taxonomy.yaml` | Example approved taxonomy (TIER 1) |
| `.claude/protocols/notion-csv-append-protocol.md` | PR #51 sole Notion append path |
| `.claude/CLAUDE.md` | Orchestrator — PRE-FLIGHT STEP 0.5 wiring |
