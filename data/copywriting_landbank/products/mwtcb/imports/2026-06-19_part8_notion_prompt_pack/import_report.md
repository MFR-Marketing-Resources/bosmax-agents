# Batch Import Report - 2026-06-19_part8_notion_prompt_pack

This report details the generation statistics, distributions, and verification results for the MWTCB Notion Production Rows and Prompt Packs.

## 1. Metadata and Summary
- **Source Files Used**: 
  - `video_copy_matrix.csv` (500 rows)
  - `poster_copy_matrix.csv` (500 rows)
- **Notion Production Rows Count**: 1000
- **Video Prompt Pack Count**: 500
- **Poster Prompt Pack Count**: 500
- **Product ID Locked**: MWTCB_25ML

## 2. Distribution Statistics

### Production Type Distribution
| production_type   |   count |
|:------------------|--------:|
| video             |     500 |
| poster            |     500 |

### Raw Claim Tolerance Distribution
| raw_claim_tolerance   |   count |
|:----------------------|--------:|
| HIGH                  |     792 |
| MEDIUM                |     204 |
| LOW                   |       4 |

### Production Review Required Distribution
| production_review_required   |   count |
|:-----------------------------|--------:|
| YES                          |     792 |
| NO                           |     208 |

### Operator Edit Required Distribution
| operator_edit_required   |   count |
|:-------------------------|--------:|
| YES                      |     792 |
| OPTIONAL                 |     204 |
| NO                       |       4 |

### Priority Score Distribution (Descriptive Statistics)
|       |   priority_score |
|:------|-----------------:|
| count |        1000      |
| mean  |          28.484  |
| std   |          17.1766 |
| min   |          15      |
| 25%   |          18      |
| 50%   |          22      |
| 75%   |          25      |
| max   |          92      |

## 3. Duplicate and Formatting Validation
- **Exact Duplicate Count**: 0 (all 1000 notion rows have unique IDs and reference unique matrix combination paths).
- **Prompt Pack Mappings**: 100% of Notion rows map to valid, unique prompt pack entries.

## 4. Sample Rows (Top 20 Notion Production Rows)
| notion_row_id         | production_type   | source_matrix_id   | prompt_pack_id     | raw_claim_tolerance   | production_review_required   | operator_edit_required   |   priority_score |
|:----------------------|:------------------|:-------------------|:-------------------|:----------------------|:-----------------------------|:-------------------------|-----------------:|
| MWTCB_NOTION_ROW_0001 | video             | MWTCB_VIDMAT_001   | MWTCB_VID_PACK_001 | HIGH                  | YES                          | YES                      |               15 |
| MWTCB_NOTION_ROW_0002 | video             | MWTCB_VIDMAT_002   | MWTCB_VID_PACK_002 | HIGH                  | YES                          | YES                      |               15 |
| MWTCB_NOTION_ROW_0003 | video             | MWTCB_VIDMAT_003   | MWTCB_VID_PACK_003 | HIGH                  | YES                          | YES                      |               15 |
| MWTCB_NOTION_ROW_0004 | video             | MWTCB_VIDMAT_004   | MWTCB_VID_PACK_004 | HIGH                  | YES                          | YES                      |               15 |
| MWTCB_NOTION_ROW_0005 | video             | MWTCB_VIDMAT_005   | MWTCB_VID_PACK_005 | MEDIUM                | NO                           | OPTIONAL                 |               62 |
| MWTCB_NOTION_ROW_0006 | video             | MWTCB_VIDMAT_006   | MWTCB_VID_PACK_006 | HIGH                  | YES                          | YES                      |               22 |
| MWTCB_NOTION_ROW_0007 | video             | MWTCB_VIDMAT_007   | MWTCB_VID_PACK_007 | HIGH                  | YES                          | YES                      |               22 |
| MWTCB_NOTION_ROW_0008 | video             | MWTCB_VIDMAT_008   | MWTCB_VID_PACK_008 | HIGH                  | YES                          | YES                      |               22 |
| MWTCB_NOTION_ROW_0009 | video             | MWTCB_VIDMAT_009   | MWTCB_VID_PACK_009 | HIGH                  | YES                          | YES                      |               18 |
| MWTCB_NOTION_ROW_0010 | video             | MWTCB_VIDMAT_010   | MWTCB_VID_PACK_010 | HIGH                  | YES                          | YES                      |               18 |
| MWTCB_NOTION_ROW_0011 | video             | MWTCB_VIDMAT_011   | MWTCB_VID_PACK_011 | HIGH                  | YES                          | YES                      |               18 |
| MWTCB_NOTION_ROW_0012 | video             | MWTCB_VIDMAT_012   | MWTCB_VID_PACK_012 | HIGH                  | YES                          | YES                      |               18 |
| MWTCB_NOTION_ROW_0013 | video             | MWTCB_VIDMAT_013   | MWTCB_VID_PACK_013 | HIGH                  | YES                          | YES                      |               18 |
| MWTCB_NOTION_ROW_0014 | video             | MWTCB_VIDMAT_014   | MWTCB_VID_PACK_014 | HIGH                  | YES                          | YES                      |               18 |
| MWTCB_NOTION_ROW_0015 | video             | MWTCB_VIDMAT_015   | MWTCB_VID_PACK_015 | HIGH                  | YES                          | YES                      |               18 |
| MWTCB_NOTION_ROW_0016 | video             | MWTCB_VIDMAT_016   | MWTCB_VID_PACK_016 | HIGH                  | YES                          | YES                      |               18 |
| MWTCB_NOTION_ROW_0017 | video             | MWTCB_VIDMAT_017   | MWTCB_VID_PACK_017 | HIGH                  | YES                          | YES                      |               25 |
| MWTCB_NOTION_ROW_0018 | video             | MWTCB_VIDMAT_018   | MWTCB_VID_PACK_018 | HIGH                  | YES                          | YES                      |               25 |
| MWTCB_NOTION_ROW_0019 | video             | MWTCB_VIDMAT_019   | MWTCB_VID_PACK_019 | HIGH                  | YES                          | YES                      |               25 |
| MWTCB_NOTION_ROW_0020 | video             | MWTCB_VIDMAT_020   | MWTCB_VID_PACK_020 | HIGH                  | YES                          | YES                      |               25 |

## 5. Sample Rows (Top 20 Video Prompt Pack Rows)
| video_prompt_pack_id   | video_matrix_id   |   priority_score | source_batch                        |
|:-----------------------|:------------------|-----------------:|:------------------------------------|
| MWTCB_VID_PACK_001     | MWTCB_VIDMAT_001  |               15 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_002     | MWTCB_VIDMAT_002  |               15 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_003     | MWTCB_VIDMAT_003  |               15 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_004     | MWTCB_VIDMAT_004  |               15 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_005     | MWTCB_VIDMAT_005  |               62 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_006     | MWTCB_VIDMAT_006  |               22 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_007     | MWTCB_VIDMAT_007  |               22 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_008     | MWTCB_VIDMAT_008  |               22 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_009     | MWTCB_VIDMAT_009  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_010     | MWTCB_VIDMAT_010  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_011     | MWTCB_VIDMAT_011  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_012     | MWTCB_VIDMAT_012  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_013     | MWTCB_VIDMAT_013  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_014     | MWTCB_VIDMAT_014  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_015     | MWTCB_VIDMAT_015  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_016     | MWTCB_VIDMAT_016  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_017     | MWTCB_VIDMAT_017  |               25 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_018     | MWTCB_VIDMAT_018  |               25 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_019     | MWTCB_VIDMAT_019  |               25 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_VID_PACK_020     | MWTCB_VIDMAT_020  |               25 | 2026-06-19_part8_notion_prompt_pack |

## 6. Sample Rows (Top 20 Poster Prompt Pack Rows)
| poster_prompt_pack_id   | poster_matrix_id   |   priority_score | source_batch                        |
|:------------------------|:-------------------|-----------------:|:------------------------------------|
| MWTCB_POST_PACK_001     | MWTCB_POSTMAT_001  |               15 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_002     | MWTCB_POSTMAT_002  |               15 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_003     | MWTCB_POSTMAT_003  |               15 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_004     | MWTCB_POSTMAT_004  |               15 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_005     | MWTCB_POSTMAT_005  |               62 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_006     | MWTCB_POSTMAT_006  |               22 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_007     | MWTCB_POSTMAT_007  |               22 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_008     | MWTCB_POSTMAT_008  |               22 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_009     | MWTCB_POSTMAT_009  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_010     | MWTCB_POSTMAT_010  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_011     | MWTCB_POSTMAT_011  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_012     | MWTCB_POSTMAT_012  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_013     | MWTCB_POSTMAT_013  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_014     | MWTCB_POSTMAT_014  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_015     | MWTCB_POSTMAT_015  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_016     | MWTCB_POSTMAT_016  |               18 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_017     | MWTCB_POSTMAT_017  |               25 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_018     | MWTCB_POSTMAT_018  |               25 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_019     | MWTCB_POSTMAT_019  |               25 | 2026-06-19_part8_notion_prompt_pack |
| MWTCB_POST_PACK_020     | MWTCB_POSTMAT_020  |               25 | 2026-06-19_part8_notion_prompt_pack |

## 7. Unresolved Issues / Next Step
- **Unresolved Issues**: None.
- **Recommended Next Task**: Complete repository validation and review.
