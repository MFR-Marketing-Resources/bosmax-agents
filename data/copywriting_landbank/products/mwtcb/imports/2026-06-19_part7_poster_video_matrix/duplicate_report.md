# Batch Duplicate Report - 2026-06-19_part7_poster_video_matrix

This report details the duplicate checks performed on the generated Video and Poster Copy Matrices.

## 1. Exact Duplicates
- **Checked Files**: `video_copy_matrix.csv`, `poster_copy_matrix.csv`
- **Exact duplicates found**: 0. All 500 rows are unique.

## 2. Near-Duplicate Analysis
- **Components overlap**: Pairs of hooks and subhooks are combined with different USPs or CTAs, and mapped to separate creative formats (`video_format`, `poster_format`), visual scenes (`scene_direction`, `poster_visual_direction`), or usage contexts.
- **Resolution**: Since they represent different creative execution outputs, the overlap is deliberate and necessary for testing alternative hooks.

## 3. Integrity Constraints
- **Primary Keys Unique**: Both matrices have unique primary keys (`MWTCB_VIDMAT_001` to `500` and `MWTCB_POSTMAT_001` to `500`).
- **All components trace back**: 100% of rows trace back to legitimate motivation, angle, hook, subhook, USP, and CTA source IDs.
