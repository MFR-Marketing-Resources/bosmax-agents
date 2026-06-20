# Notion Video Prompt Worker

## Purpose

`scripts/notion_video_prompt_worker.py` is the Notion-backed BOSMAX Video Prompt
Compiler Bridge. Notion is operator intake only. The worker resolves authority
relations in code, validates mode-specific asset requirements, generates a clean
compiler payload, and writes the result back to the selected operator row.

## Operator-facing databases

The only operator-facing databases are:

- `BOSMAX HYBRID Operator Intake`
- `BOSMAX FRAMES Operator Intake`
- `BOSMAX INGREDIENTS Operator Intake`

`BOSMAX Video Prompt Requests`, `BOSMAX_VIDEO_PROMPT_RUNS`, and the old combined front-end surfaces are backend/admin surfaces. The backend database export is invalid for operators.

## Required live inputs

- shared authority relations:
  - `Product`
  - `Engine + Duration`
  - `Copy Source`
  - exactly one of `BOSMAX Copy Set` or `MWTCB Copy Set`
- mode-specific asset inputs:
  - `HYBRID`
    - `Product Photo Upload`
    - `Scene Context`
    - optional `Avatar Ai`
  - `FRAMES`
    - `Completed Frame Upload`
    - `Motion Delta`
    - `Frame Context`
  - `INGREDIENTS`
    - `Product Reference Photo`
    - `Avatar Reference Photo`
    - `Style Scene Reference Photo` when required by `Asset Role Map`
    - `Asset Role Map`
    - `style_scene_source`

## Writeback contract

The worker writes only to operator-facing output fields already present on the
row:

- `Compiler Payload / RAW Prompt`
- `Output From Compiler`
- `QA Notes`
- `Request Status`

No backend rollup, formula, debug, compiler-status, or admin-only fields are
added to the three operator intake databases.

## Setup

1. Install the repo dependencies already used by the compiler lane.
2. Set `NOTION_API_TOKEN` for live runs.
3. Create or open a row in one of:
   - `BOSMAX HYBRID Operator Intake`
   - `BOSMAX FRAMES Operator Intake`
   - `BOSMAX INGREDIENTS Operator Intake`
4. Fill the required authority relations and mode-specific asset fields.
5. Keep `Request Status = Not started` until the worker picks the row up.

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

Operator queue sweep across the three intake databases:

```bash
set NOTION_API_TOKEN=secret_xxx
python scripts/notion_video_prompt_worker.py --page-size 10
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

- HYBRID/FRAMES/INGREDIENTS mode detection and schema exclusivity
- correct operator-facing data source IDs
- deterministic normalization to `PRODUCT_ONLY`, `READY_FRAME`, `ASSET_SET`
- generated compiler payload contains only the correct mode-specific sections
- `product_truth_ref`, engine/duration, and hook/body/CTA are populated
- missing required assets fail closed
- backend operator export is blocked by governance docs
- `Compiler Payload / RAW Prompt` and `Output From Compiler` are the correct
  operator export surfaces
