# Copywriting Landbank

The copywriting landbank is the repo-native storage layer for commercial copy assets by product. It keeps row-heavy copy in CSV, reusable rules and schemas in YAML, and import / duplicate audits in Markdown.

## Canonical Data

- Canonical row data lives under `data/copywriting_landbank/products/<product_key>/`.
- CSV is the source of truth for row-heavy assets such as buyer motivations and classification layers.
- YAML is the source of truth for schemas, product profiles, taxonomies, rankings, and manifests.
- Markdown is the source of truth for human-facing import and duplicate reports.
- Excel under `data/copywriting_landbank/exports/` is export-only.

## Why Excel Is Export-Only

Excel is easy to inspect but poor as a canonical diff surface. The repo stores deterministic text-first artifacts so changes are reviewable, mergeable, and script-validated.

## Add a New Product

1. Create `data/copywriting_landbank/products/<product_key>/`.
2. Seed `product.copy.yaml`, `source_manifest.yaml`, and only the CSVs backed by real imported data.
3. Reuse the shared taxonomies in `data/copywriting_landbank/global/` and the schemas in `data/copywriting_landbank/schema/`.
4. Add a batch snapshot under `imports/<date>_<batch_name>/`.
5. Run `python scripts/validate_copywriting_landbank.py`.

## Add a New Batch For an Existing Product

1. Copy the untouched sources into `imports/<date>_<batch_name>/raw_input/`.
2. Write normalized snapshots into `imports/<date>_<batch_name>/normalized/` with the same metadata columns used in the canonical CSVs.
3. Merge only exact-new rows into the canonical CSVs.
4. Update `rankings.yaml`, `source_manifest.yaml`, `import_report.md`, and `duplicate_report.md`.
5. Regenerate the export artifacts.

## Part 2 Angle Master Bank Expansion

Do not create empty angle, hook, subhook, USP, CTA, video matrix, or poster matrix CSVs. Define the schemas now, then add those CSVs only when real data exists. Start Part 2 from `rankings.yaml` plus the near-duplicate canonical anchors documented in the duplicate report.

## Video Copywriting Use

- Use `buyer_motivations.csv` for raw scenario pain, desire, hook, subhook, CTA, and proof seeds.
- Use `motivation_classification.csv` to filter by persona, boldness, format, platform surface, and bucket.
- Use `rankings.yaml` to decide which rows to expand first for TikTok Shop, UGC, hybrid, and product-only lanes.

## Poster Copywriting Use

- Use the same buyer-motivation spine, but bias toward rows tagged `poster_ad`, `poster_ads`, `product_page_asset`, or `VISUAL_RECOGNITION` / `STANDBY_BEFORE_NEED` buckets.
- Preserve the strongest source hooks for poster headlines; do not auto-sanitize during import.

## Dedupe Rule

- Delete exact duplicates only.
- For near duplicates, keep both when the sales use is materially different and record the canonical-vs-variant decision in the duplicate report.
