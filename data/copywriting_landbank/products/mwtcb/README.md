# MWTCB Copywriting Landbank

This folder contains the repository-native copywriting landbank for `Minyak Warisan Tok Cap Burung` (`MWTCB_25ML`).

## Canonical Files

- `product.copy.yaml`: product-level copy profile from uploaded landbank facts only.
- `buyer_motivations.csv`: merged buyer motivation rows from both uploaded sources.
- `motivation_classification.csv`: merged classification rows aligned to the buyer rows.
- `angle_bank.csv`: Angle Master Bank containing exactly 150 unique, high-quality copywriting angles.
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

## Part 2 Angle Master Bank

Completed Part 2 implementation. The Angle Master Bank is located at `angle_bank.csv`, containing exactly 150 unique copywriting angles generated from the 64 HIGH-priority buyer motivations. All angles map back to the respective motivation IDs and specify detailed hook style, visual scenes, and commercial reasoning.

## Video and Poster Use

- Video: filter `motivation_classification.csv` by `best_content_format`, `best_platform_surface`, `persona_fit`, and `boldness_level`.
- Poster: prioritize headline-capable rows from `top_poster_ads`, `top_aggressive_hooks`, `top_safe_hooks`, and `VISUAL_RECOGNITION` / `STANDBY_BEFORE_NEED` buckets.

## Dedupe

Exact duplicates are removed. Near-duplicate rows stay when they provide different commercial leverage; the stronger expansion anchor is marked in the duplicate report.
