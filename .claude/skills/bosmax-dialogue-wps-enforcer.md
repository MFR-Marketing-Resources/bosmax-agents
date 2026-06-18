---
name: bosmax-dialogue-wps-enforcer
description: >
  BOSMAX dialogue WPS hard gate. Invoke before final video prompt output for
  any spoken-dialogue lane so underfilled or over-ceiling dialogue never
  reaches the clean operator-facing prompt.
---

# BOSMAX DIALOGUE WPS ENFORCER — SKILL
## Role: Universal pre-output dialogue corridor gate
## Schema: v2 | Authority: SUPREME_SYSTEMS_ARCHITECT

---

## TRIGGER

Run this skill **before final video prompt output** whenever `dialogue_required = YES`.
This applies to all spoken-dialogue video engines:

- GROK
- GOOGLE_FLOW / FLOW_EXTEND_UI
- VEO
- VEO_3_1
- VEO_3_1_LITE
- KLING_3_0
- SEEDANCE_2_0
- any future BOSMAX spoken-dialogue video engine

---

## INPUT

```
engine_id
total_duration_seconds
block_plan
block_duration
language
pace_class
dialogue_required
candidate_dialogue_by_block
```

`candidate_dialogue_by_block` is the exact spoken line draft for each block before final prompt assembly.

---

## OUTPUT

```
PASS
BLOCKED
```

- `PASS` — every dialogue block has passed corridor audit; final prompt may receive the approved spoken line
- `BLOCKED` — at least one required dialogue block remains invalid after 3 rewrite attempts; final output must stop

Internal rewrite is not an output state. Rewrite is always performed internally before returning `PASS` or `BLOCKED`.

---

## COMPLIANCE SCRUB — MANDATORY

Run before any WPS audit. If any forbidden surface is detected in `candidate_dialogue_by_block`, return `BLOCKED` immediately. Do not proceed to corridor audit. No rewrite is permitted for compliance failures.

**Medical and treatment claims — FORBIDDEN:**
- rawat / merawat / menyembuhkan / sembuh
- ubat / perubatan / klinikal / hospital / doktor
- treatment / cure / clinical / terbukti sembuh / hilangkan penyakit
- 100% guaranteed / dijamin sembuh / proven cure / clinical trial

**Infant-adjacent and baby-context — FORBIDDEN:**
- kembung / kolik / colic
- sakit perut bayi / sapu perut bayi / urut perut bayi
- before-after baby behaviour claims (e.g. baby tidur selepas / baby tenang selepas pakai)
- apply on tummy / apply on baby skin
- any usage instruction implying direct infant skin contact

**CLASS_B / BOSMAX STEALTH lane — FORBIDDEN in dialogue:**
- direct adult-performance claims of any kind
- explicit sensitive-intent language
- before-after performance framing for male subject
- clinical proof cues combined with performance implication
- unapproved vocab tokens (see `registries/BOSMAX_SILO_VOCAB_PLACEHOLDER_v1_STRICT.yaml`)

Any compliance failure → `BLOCKED`. No rewrite. No further audit.

---

## DIALOGUE PRE-BUDGET — INTERNAL ONLY

This section governs internal audit scaffolding only. Nothing resolved here may appear in the final clean prompt.

Before counting words, resolve:
1. `engine_id` → look up block plan in `registries/video_engine_duration_contracts.yaml`
2. `block_plan` → number of blocks, duration per block
3. `language` + `pace_class` + `block_duration` → look up corridor row in `registries/dialogue_budget_corridor.yaml`
4. Extract from corridor row: `minimum_words`, `target_min_words`, `target_max_words`, `safe_max_words`, `hard_ceiling_words`
5. Count words in `candidate_dialogue_by_block` for each block separately

---

## WORD BUDGET AUTHORITY

**Primary authority — per-block corridor:**
`registries/dialogue_budget_corridor.yaml`

The per-block corridor row (keyed by `language` + `pace_class` + `block_duration`) is the sole authority for all accept/reject decisions. No other budget calculation overrides it.

**Secondary sanity check only — total-duration budget:**
`total_duration_seconds × language_wps_safe_max`

Language safe max reference:
- BM = 2.5
- EN = 3.0
- ID = 2.6
- ZH = 2.6
- HI = 2.4
- BN = 2.4
- AR = 2.2

The total-duration budget exists as a secondary consistency check only. It must never replace the per-block corridor as the accept/reject authority. If total-duration budget conflicts with per-block corridor, the per-block corridor wins.

---

## PER-BLOCK AUDIT PROCEDURE

For each block in `candidate_dialogue_by_block`:

1. Resolve `engine_id` → block plan from `registries/video_engine_duration_contracts.yaml`
2. Resolve `block_duration` for this specific block
3. Resolve `pace_class` for this block
4. Look up corridor row: match `language` + `pace_class` + `block_duration`
5. Extract: `minimum_words`, `target_min_words`, `target_max_words`, `safe_max_words`, `hard_ceiling_words`
6. Count words in candidate dialogue for this block
7. Assign status per STATUS LAW

---

## STATUS LAW

Use exact enum only. No variants, no spaces in names.

| Status | Condition |
|---|---|
| `UNDERFILLED` | `final_word_count < minimum_words` |
| `TARGET_RANGE` | `target_min_words <= final_word_count <= target_max_words` |
| `OVER_SAFE` | `target_max_words < final_word_count <= safe_max_words` |
| `HARD_FAIL` | `final_word_count > safe_max_words` |

`hard_ceiling_words` is an absolute emergency ceiling — any count above it is also `HARD_FAIL`. The operational rewrite trigger starts immediately after `safe_max_words`.

**Accept:**
- `TARGET_RANGE`
- `OVER_SAFE`

**Reject → set `REWRITE_REQUIRED` and trigger internal rewrite:**
- `UNDERFILLED` → `REWRITE_REQUIRED` (expand to fill the beat — underfill opens dead
  air that the video model fills with hallucinated drift/glitch)
- `HARD_FAIL` → `REWRITE_REQUIRED` (trim into corridor)

`REWRITE_REQUIRED` is an internal transition, never an output state and never a
final-prompt surface. A block that is still `UNDERFILLED` or `HARD_FAIL` after the
rewrite limit returns `BLOCKED`. Underfilled dialogue must never pass as a warning.

---

## REWRITE LAW

If any block is `UNDERFILLED` or `HARD_FAIL`, rewrite the candidate dialogue internally before final prompt assembly. Do not expose rewrite activity in the final prompt.

**If `UNDERFILLED`:**
- Expand with useful spoken content: add a USP beat, a proof cue, or a context line
- No filler words, no padding, no empty bridge phrases
- Re-count and re-audit

**If `HARD_FAIL`:**
- Reduce in priority order:
  1. Remove weak or redundant USP qualifier first
  2. Remove secondary qualifier or bridging phrase second
  3. Compress hook or subhook if still above minimum after steps 1–2
- Do not remove the CTA line if the route requires it
- Re-count and re-audit

**Rewrite limit:**
```
max_rewrite_attempts: 3
```

After 3 attempts per block:
- If the block still fails, return `BLOCKED`
- Do not deliver a non-passing dialogue block to the final prompt under any circumstance

---

## ROUTE LAW

For TikTok Shop Malaysia UGC videos with `dialogue_required = YES` and total duration above 10 seconds:

- default route = `AVATAR_PRODUCT_UGC`
- product-only / no-avatar route allowed only on explicit operator request, 6s CTA close, silent route, or avatar-free image-to-video continuation

---

## FINAL PROMPT LAW

The final clean prompt must stay operator-facing and natural.

The following must **never** appear in the final prompt body:

- WPS metadata of any kind
- word-count tables or word counts
- validator proof or audit status
- corridor labels, range labels, or budget thresholds
- hidden budget labels
- status enum values (`UNDERFILLED`, `TARGET_RANGE`, `OVER_SAFE`, `HARD_FAIL`, `BLOCKED`, `PASS`)
- rewrite notes or iteration counts
- any internal audit scaffolding from DIALOGUE PRE-BUDGET or PER-BLOCK AUDIT PROCEDURE

Only the exact approved natural spoken dialogue line, after passing all corridor and compliance audits, may be forwarded into final prompt assembly.