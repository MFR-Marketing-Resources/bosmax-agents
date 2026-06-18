# MWTCB Copywriting Landbank

This folder contains the repository-native copywriting landbank for `Minyak Warisan Tok Cap Burung` (`MWTCB_25ML`).

## Canonical Files

- `product.copy.yaml`: product-level copy profile from uploaded landbank facts only.
- `buyer_motivations.csv`: merged buyer motivation rows from both uploaded sources.
- `motivation_classification.csv`: merged classification rows aligned to the buyer rows.
- `angle_bank.csv`: Angle Master Bank containing exactly 150 unique, high-quality copywriting angles.
- `hook_bank.csv`: Hook Bank containing exactly 450 unique copywriting hooks.
- `subhook_bank.csv`: Subhook Bank containing exactly 450 unique supporting subhooks.
- `usp_bank.csv`: USP Bank containing exactly 200 unique product USPs.
- `cta_bank.csv`: CTA Bank containing exactly 150 unique call-to-actions.
- `rankings.yaml`: source-preserved ranking groups and park-later lists.
- `source_manifest.yaml`: import batches, hashes, and export pointers.
- `import_report.md`: batch summary and normalization trace.
- `duplicate_report.md`: exact and near-duplicate audit.

## Excel Status

- `data/copywriting_landbank/exports/mwtcb_copywriting_landbank.xlsx` is export-only.
- `data/copywriting_landbank/exports/mwtcb_copywriting_landbank_csv.zip` is export-only.
- Raw uploaded files are preserved under `imports/2026-06-19_initial_landbank/raw_input/` for traceability.

## Add Another MWTCB Batch

1. Create a new folder under `imports/`.
2. Copy the untouched sources into `raw_input/`.
3. Normalize them into `normalized/` with the same metadata columns used in the canonical CSVs.
4. Merge exact-new rows only; document cross-batch overlaps in `duplicate_report.md`.
5. Regenerate exports and rerun validation.

## Part 2, Part 3–6 & Part 7 Implementation

- **Angle Master Bank** (`angle_bank.csv`): Completed Part 2 implementation with exactly 150 unique copywriting angles generated from the 64 HIGH-priority buyer motivations.
- **Copy Component Banks** (`hook_bank.csv`, `subhook_bank.csv`, `usp_bank.csv`, `cta_bank.csv`): Completed Part 3-6 implementation with exactly 450 hooks, 450 subhooks, 200 USPs, and 150 CTAs. All elements map back to their source motivation and angle IDs.
- **Poster and Video Copy Matrices** (`video_copy_matrix.csv`, `poster_copy_matrix.csv`): Completed Part 7 implementation with exactly 500 rows each. All rows combine existing copywriting components mapped back to source IDs, complete with detailed scene/poster directions, formatting, and claim tolerance reviews.

## Part 8 Implementation

- **Notion Production Rows** (`notion_production_rows.csv`): Completed Part 8 implementation with exactly 1000 rows (500 video + 500 poster). Each row maps a source matrix entry to a prompt pack ID, carries `operator_edit_required` routing, a numeric `priority_score`, and full referential integrity back to all component banks.
- **Video Prompt Pack** (`video_prompt_pack.csv`): 500 engine-neutral prompt briefs for video creative execution. Contains locked product truth, packaging lock, scene direction, textual copy, and negative rules. Not final Grok/Veo/Sora prompts — operator review required.
- **Poster Prompt Pack** (`poster_prompt_pack.csv`): 500 engine-neutral prompt briefs for poster/image creative execution. Contains locked product truth, packaging lock, visual direction, textual copy, and negative rules. Not final image-model prompts — operator review required.

## Video and Poster Use

- Video: filter `video_copy_matrix.csv` by `video_format`, `primary_bucket`, and `raw_claim_tolerance`.
- Poster: filter `poster_copy_matrix.csv` by `poster_format`, `primary_bucket`, and `raw_claim_tolerance`.
- Notion rows: filter `notion_production_rows.csv` by `operator_edit_required` and `priority_score` for campaign scheduling.
- Prompt packs: use `video_prompt_pack.csv` and `poster_prompt_pack.csv` as operator-review briefs before handing off to any image or video generation engine.

## Dedupe

Exact duplicates are removed. Near-duplicate rows stay when they provide different commercial leverage; the stronger expansion anchor is marked in the duplicate report.
