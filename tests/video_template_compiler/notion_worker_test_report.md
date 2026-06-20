# Notion Video Prompt Worker Test Report

## Scope

Proof for the Notion-backed BOSMAX Video Prompt Compiler Bridge using the three
starter rows:

- HYBRID
- FRAMES
- INGREDIENTS

## Commands run

```bash
python scripts/validate_notion_video_prompt_worker.py
python scripts/validate_video_template_schema.py
python scripts/validate_video_prompt_compiler.py
python scripts/validate_video_template_export_readiness.py
npx @biomejs/biome check --write .
npx depcruise scripts --no-config
npx tsx scripts/mandor-check.ts
```

## Expected bridge results

- `HYBRID` normalizes to `PRODUCT_ONLY`
- `FRAMES` normalizes to `READY_FRAME`
- `INGREDIENTS` normalizes to `ASSET_SET`
- all three samples compile to `MULTI_PROMPT_SET`
- GROK 16s remains exactly two prompt sets
- raw prompt keeps product truth ref, hook/body/CTA, and mode-specific locks
- final output keeps `SECTION 9 - NO_OVERLAY`
- row URL parsing accepts a full Notion row URL
- writeback aliases resolve to either legacy or operator-facing field names

## Current result

Status: PASS

- `validate_notion_video_prompt_worker.py`
  - HYBRID PASS -> `PRODUCT_ONLY`
  - FRAMES PASS -> `READY_FRAME`
  - INGREDIENTS PASS -> `ASSET_SET`
  - alias writeback PASS
  - row URL parse PASS
- `validate_video_template_schema.py` PASS
- `validate_video_prompt_compiler.py` PASS
- `validate_video_template_export_readiness.py` PASS
- `npx @biomejs/biome check --write .` PASS
- `npx depcruise scripts --no-config` PASS
- `npx tsx scripts/mandor-check.ts` PASS

## Live Notion operator hygiene

Updated operator-facing views in `BOSMAX_VIDEO_PROMPT_RUNS`:

- `START HERE - OPERATOR ONLY`
  - added `Uploaded Asset Notes`
  - added `Asset Role Map`
  - kept backend rollups hidden
- `TEMPLATES - USE THESE`
  - added `Uploaded Asset Notes`
  - added `Asset Role Map`
  - kept backend rollups hidden
- `NEEDS ASSET`
  - added `Uploaded Asset Notes`
  - added `Asset Role Map`

## Resulting bridge state

The bridge is ready for live row-by-URL execution once `NOTION_API_TOKEN` is set.
Offline proof, schema gates, compiler gates, and alias/writeback contract are all
validated.
