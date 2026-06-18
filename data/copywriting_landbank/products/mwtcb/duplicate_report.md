# MWTCB Copywriting Landbank Duplicate Report

## Exact Duplicates Removed

- Buyer motivation rows removed: 0
- Classification rows removed: 0

## Near Duplicates Detected

### ND-001 — Balik kampung / practical gift for mak ayah
- Canonical row: `MWTCB_25ML__zip_csv__BM014`
- Variants kept: `MWTCB_25ML__xlsx__BM004`, `MWTCB_25ML__xlsx__BM022`
- Decision: `kept`
- Reason: Stronger seasonal urgency and sharper gifting hook for family-return travel.
- Note: All three stay imported. The ZIP row is the canonical Part 2 expansion anchor; the XLSX rows preserve broader gifting variants.
### ND-002 — Household drawer / standby location problem
- Canonical row: `MWTCB_25ML__zip_csv__BM007`
- Variants kept: `MWTCB_25ML__xlsx__BM006`
- Decision: `kept`
- Reason: Higher tension because it dramatizes the emergency search moment and fixed-location logic.
- Note: Keep both. XLSX BM006 is the home-organisation slap angle; ZIP BM_007 is the panic-at-use angle.
### ND-003 — Standby rumah / preparedness gap
- Canonical row: `MWTCB_25ML__zip_csv__BM023`
- Variants kept: `MWTCB_25ML__xlsx__BM028`
- Decision: `kept`
- Reason: More aggressive household inadequacy framing and clearer midnight-emergency visual.
- Note: Keep both. The ZIP row is the sharper conversion-first anchor; the XLSX row fits cleaner rack-setup or poster language.
## Rows Kept

- All 120 buyer motivation rows were retained in canonical CSV storage because no exact duplicates existed.
- Near-duplicate rows were kept when they served a different selling surface, urgency pattern, or gifting-vs-standby nuance.

## Rows Parked

- Rows parked by duplicate review: 0
- Source-provided `park_later` ranking entries remain in `rankings.yaml` as future expansion guidance and were not deleted from canonical storage.

## Decision Rule Applied

- Exact duplicates only: delete.
- Similar but commercially distinct: keep both, nominate one canonical anchor for future Part 2 expansion, document the sibling variant here.
- No copy was softened or rewritten beyond header normalization, row ids, and source metadata fields.

## Batch 2 (2026-06-19_part2_angle_bank) Near-Duplicate Review
- Generated exactly 150 unique, high-quality copywriting angles from 64 HIGH-priority motivations.
- No exact duplicate angles were generated.
- Unique commercial triggers, visual scenes, and copy hooks were developed for all sibling angles referencing the same motivation ID to prevent near-duplication.

## Batch 3 (2026-06-19_part3_6_copy_components) Near-Duplicate Review
- Generated exactly 450 hooks, 450 subhooks, 200 USPs, and 150 CTAs.
- No exact duplicate components were generated.
- Unique texts were generated for sibling hooks, subhooks, USPs, and CTAs utilizing specific context variables, styles, and roles to prevent near-duplication.

## Batch 4 (2026-06-19_part7_poster_video_matrix) Near-Duplicate Review
- Generated exactly 500 video copy matrix rows and 500 poster copy matrix rows.
- No exact duplicate matrix rows were generated.
- Component combinations and creative details (formats, visual scene directions, overlays) vary systematically across rows to ensure uniqueness and distinct testing routes.

## Batch 5 (2026-06-19_part8_notion_prompt_pack) Near-Duplicate Review
- Generated exactly 1000 Notion production rows and 1000 prompt pack entries (500 video + 500 poster).
- No exact duplicate rows were generated.
- All `notion_row_id`, `video_prompt_pack_id`, and `poster_prompt_pack_id` primary keys are unique.
- Prompt briefs differ systematically because they inherit distinct scene directions, visual contexts, copy angles, and USP chips from the unique Part 7 source matrix rows.
