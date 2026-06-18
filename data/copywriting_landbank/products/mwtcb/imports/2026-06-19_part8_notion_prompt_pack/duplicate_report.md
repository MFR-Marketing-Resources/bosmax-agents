# Batch Duplicate Report - 2026-06-19_part8_notion_prompt_pack

This report details the duplicate check and referential integrity verification performed on the Notion Production Rows and Prompt Packs.

## 1. Exact Duplicates
- **Checked Files**: `notion_production_rows.csv`, `video_prompt_pack.csv`, `poster_prompt_pack.csv`
- **Exact duplicates found**: 0. All IDs and prompt briefs are distinct.

## 2. Integrity Constraints
- **Primary Keys Unique**:
  - `notion_row_id`: `MWTCB_NOTION_ROW_0001` to `1000` are 100% unique.
  - `video_prompt_pack_id`: `MWTCB_VID_PACK_001` to `500` are 100% unique.
  - `poster_prompt_pack_id`: `MWTCB_POST_PACK_001` to `500` are 100% unique.
- **All components trace back**:
  - 100% of Notion rows reference valid source matrix IDs (`MWTCB_VIDMAT_001-500` and `MWTCB_POSTMAT_001-500`).
  - 100% of Notion rows reference valid master component banks.
