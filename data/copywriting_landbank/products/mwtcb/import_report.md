# MWTCB Copywriting Landbank Import Report

## Scope

Imported the uploaded MWTCB copywriting landbank inputs into the repository-native copywriting landbank module.

- Product ID: `MWTCB_25ML`
- Product name: `Minyak Warisan Tok Cap Burung`
- Import version: `2026-06-19_initial_landbank`
- Canonical storage: CSV for row data, YAML for schemas/manifests/taxonomies, Markdown for reports
- Excel status: export-only

## Source Intake

- `mwtcb_copywriting_landbank.xlsx`
  - Buyer Motivation Map: 60 rows
  - Classification Layer: 60 rows
  - Ranking sheets: Top 15 Expand, Bundle Top10, UGC Top10, ProductOnly Top10, Poster Top10, Aggressive Hooks, Safe Hooks, Park Later
- `mwtcb_gemini_copywriting_landbank_csv.zip`
  - Buyer_Motivation_Map.csv: 60 rows
  - Classification_Layer.csv: 60 rows
  - Ranking CSVs: Top_15_Expand, Bundle_Top10, UGC_Top10, ProductOnly_Top10, Poster_Top10, Aggressive_Hooks, Safe_Hooks, Park_Later

## Canonical Outputs

- `buyer_motivations.csv`: 120 rows
- `motivation_classification.csv`: 120 rows
- `rankings.yaml`: 8 ranking groups with source-preserved sublists
- `product.copy.yaml`: seeded from uploaded landbank facts only
- `source_manifest.yaml`: source hashes, batch snapshots, and export pointers

## Normalization Decisions

- Headers normalized to canonical `snake_case`.
- Added `product_id`, source metadata, and deterministic canonical row ids.
- Preserved source copy intensity, including aggressive hooks and raw vernacular phrasing.
- Preserved both source batches; no merged rank order was invented across the two inputs.
- Ranking groups remain source-preserved inside each canonical group so future Part 2 work can decide cross-source winners explicitly.

## Exact Dedupe Result

- Buyer motivation rows removed as exact duplicates: 0
- Classification rows removed as exact duplicates: 0

## Near-Duplicate Review

- Near-duplicate clusters documented: 3
- Rows parked due to duplicate review: 0
- `park_later` source ranking lists were preserved as prioritization guidance, not treated as deletions.

## Batch History

### Batch 1: 2026-06-19_initial_landbank
- Imported 120 buyer motivations and 120 classifications.
- Seeded rankings and product profile.

### Batch 2: 2026-06-19_part2_angle_bank (Part 2 Implementation)
- Generated exactly 150 unique, high-quality copywriting angles from the 64 HIGH-priority motivations.
- Outputs written to `angle_bank.csv` and the corresponding import snapshot directory.
- All angles mapped to a unique motivation ID, and verified against the 29 canonical columns.
- Retained raw Malaysian-vernacular phrasing, high-priority motivations first, with complete commercial trigger, visual scene, and explanation of why it can sell.

