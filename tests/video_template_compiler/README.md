# Notion Video Prompt Worker

## Purpose

`scripts/notion_video_prompt_worker.py` is the Notion-backed BOSMAX Video Prompt
Compiler Bridge. It treats Notion as operator intake only, resolves authority
relations in code, validates mode-specific requirements, generates a clean
compiler payload, and writes the result back to the selected row.

## Supported run modes

- `HYBRID` -> compiler `intake_mode=PRODUCT_ONLY`
- `FRAMES` -> compiler `intake_mode=READY_FRAME`
- `INGREDIENTS` -> compiler `intake_mode=ASSET_SET`

## Required live inputs

- relation fields:
  - `Product`
  - `Engine Rule`
  - `Angle`
  - `Avatar AI` optional
  - exactly one of `Copy Pack BOSMAX` or `Copy Pack MWTCB`
- shared gates:
  - `Compiler Method = EXTERNAL_COMPILER`
  - `Output Reactivity = SYSTEM_WRITTEN_OUTPUT`
  - `Compiler Output Status = READY_TO_COMPILE`
- mode gates:
  - `HYBRID`: `Product Reference Provided = true`
  - `FRAMES`: `Frame Provided = true` and non-empty `Uploaded Asset Notes`
  - `INGREDIENTS`: `Product Reference Provided = true`, `Asset Roles Verified = true`, and non-empty `Asset Role Map`
  - `INGREDIENTS` with avatar: `Avatar Reference Provided = true`

## Writeback contract

The worker writes to whichever field set exists on the row:

- prompt payload:
  - `Compiler Payload / RAW Prompt`
  - fallback: `RAW_PROMPT_COMPILED`
- final 9-section output:
  - `Final Output 9 Section`
  - fallback: `FINAL_OUTPUT_9_SECTION`
- validation notes:
  - `QA Notes`
  - fallback: `Compiler Output Notes`
- request status:
  - `Request Status`
  - fallback: `Prompt Status`

The worker also writes `Compiler Contract Version`, `Compiler Job ID`,
`Compiler Input Snapshot`, `Compiler Error`, `Compiler Output Status`, and
`COMPILER_QA_STATUS`.

## Setup

1. From repo root, install the repo dependencies already used by the compiler lane.
2. Set `NOTION_API_TOKEN` for live runs.
3. Prepare a row in `BOSMAX_VIDEO_PROMPT_RUNS` using one of the canonical operator templates.
4. Set `Compiler Output Status` to `READY_TO_COMPILE`.

## Commands

Offline snapshot proof:

```bash
python scripts/notion_video_prompt_worker.py --snapshot tests/video_template_compiler/notion_worker_snapshot_bosmax.json
python scripts/notion_video_prompt_worker.py --snapshot tests/video_template_compiler/notion_worker_snapshot_frames.json
python scripts/notion_video_prompt_worker.py --snapshot tests/video_template_compiler/notion_worker_snapshot_ingredients.json
```

Single live row by page id or full URL:

```bash
set NOTION_API_TOKEN=secret_xxx
python scripts/notion_video_prompt_worker.py --run-page https://app.notion.com/p/<row-id>
```

READY queue sweep:

```bash
set NOTION_API_TOKEN=secret_xxx
python scripts/notion_video_prompt_worker.py --data-source-id 537c35a1-fd7a-453a-909b-eeb839b6b979 --page-size 10
```

## Tests

Starter fixtures:

- `tests/video_template_compiler/notion_worker_snapshot_bosmax.json`
- `tests/video_template_compiler/notion_worker_snapshot_frames.json`
- `tests/video_template_compiler/notion_worker_snapshot_ingredients.json`

Bridge validator:

```bash
python scripts/validate_notion_video_prompt_worker.py
```

This validator proves:

- mode detection for `HYBRID`, `FRAMES`, `INGREDIENTS`
- deterministic normalization to `PRODUCT_ONLY`, `READY_FRAME`, `ASSET_SET`
- final output stays `MULTI_PROMPT SET` for GROK 16s `[10,6]`
- Section 9 remains `NO_OVERLAY`
- row URL parsing works
- writeback alias resolution works for old and new field names

## Retained local package files

The bridge keeps the retained local package files as sidecar references, but the
live compile path is relation-driven and repo-governed. It does not depend on
Notion formulas or manual text stitching to generate the final raw prompt.
