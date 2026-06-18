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

## Part 2 & Part 3–6 Implementation

- **Angle Master Bank** (`angle_bank.csv`): Completed Part 2 implementation with exactly 150 unique copywriting angles generated from the 64 HIGH-priority buyer motivations.
- **Copy Component Banks** (`hook_bank.csv`, `subhook_bank.csv`, `usp_bank.csv`, `cta_bank.csv`): Completed Part 3-6 implementation with exactly 450 hooks, 450 subhooks, 200 USPs, and 150 CTAs. All elements map back to their source motivation and angle IDs and are formatted native to TikTok Shop Malaysia.

## Video and Poster Use

- Video: filter `motivation_classification.csv` by `best_content_format`, `best_platform_surface`, `persona_fit`, and `boldness_level`.
- Poster: prioritize headline-capable rows from `top_poster_ads`, `top_aggressive_hooks`, `top_safe_hooks`, and `VISUAL_RECOGNITION` / `STANDBY_BEFORE_NEED` buckets.

## Dedupe

Exact duplicates are removed. Near-duplicate rows stay when they provide different commercial leverage; the stronger expansion anchor is marked in the duplicate report.
