# Notion Video Prompt Worker Test Report

## Scope

Proof for the operator-intake-only BOSMAX Notion Video Prompt Worker using the
three starter rows:

- HYBRID
- FRAMES
- INGREDIENTS

## Commands run

```bash
python scripts/validate_notion_video_prompt_worker.py
python scripts/validate_video_template_schema.py
python scripts/validate_video_prompt_compiler.py
python scripts/validate_video_template_export_readiness.py
npx @biomejs/biome check .
npx depcruise scripts --no-config
npx tsx scripts/mandor-check.ts
```

## Expected bridge results

- each mode compiles only from its own operator intake schema
- HYBRID contains no FRAMES/INGREDIENTS-only fields
- FRAMES contains no HYBRID/INGREDIENTS-only fields
- INGREDIENTS contains no HYBRID/FRAMES-only fields
- generated `Compiler Payload / RAW Prompt` contains only the correct mode
- `product_truth_ref`, engine/duration, hook/body/CTA are populated
- missing required assets fail closed
- final output remains `MULTI-PROMPT SET`
- final output keeps `SECTION 9 - NO_OVERLAY`

## Export governance

Exporting backend Notion pages is not an operator workflow.

The following surfaces are backend/admin only:

- `BOSMAX Video Prompt Requests`
- `BOSMAX_VIDEO_PROMPT_RUNS`
- legacy combined front-end / backend diagnostic pages

Exporting `Compiler Payload / RAW Prompt` and `Output From Compiler` is the correct operator workflow.

## Current result

Status: PASS

- `validate_notion_video_prompt_worker.py`
  - HYBRID schema exclusivity PASS
  - FRAMES schema exclusivity PASS
  - INGREDIENTS schema exclusivity PASS
  - mode payload isolation PASS
  - product truth / engine / copy population PASS
  - missing asset fail-closed PASS
  - docs governance PASS
  - alias writeback PASS
  - row URL parse PASS
- `validate_video_template_schema.py` PASS
- `validate_video_prompt_compiler.py` PASS
- `validate_video_template_export_readiness.py` PASS
- `npx @biomejs/biome check .` PASS
- `npx depcruise scripts --no-config` PASS
- `npx tsx scripts/mandor-check.ts` PASS

## Resulting bridge state

The worker is ready for live row-by-URL execution from the three mode-specific
operator intake databases only. Backend database export is explicitly invalid
for operators, and the writeback contract is confined to:

- `Compiler Payload / RAW Prompt`
- `Output From Compiler`
- `QA Notes`
- `Request Status`
