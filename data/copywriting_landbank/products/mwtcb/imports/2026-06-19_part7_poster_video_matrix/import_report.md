# Batch Import Report - 2026-06-19_part7_poster_video_matrix

This report details the intake statistics, distributions, and verification results for the MWTCB Video and Poster Copy Matrices batch.

## 1. Metadata and Summary
- **Source Files Used**: 
  - `angle_bank.csv` (150 angles)
  - `hook_bank.csv` (450 hooks)
  - `subhook_bank.csv` (450 subhooks)
  - `usp_bank.csv` (200 USPs)
  - `cta_bank.csv` (150 CTAs)
- **Video Copy Matrix Row Count**: 500
- **Poster Copy Matrix Row Count**: 500
- **Unique Source Angles Covered**: 150
- **Unique Source Component IDs Seedeed**: 
  - Hooks: 450
  - Subhooks: 450
  - USPs: 200
  - CTAs: 150

## 2. Distribution Statistics

### Primary Bucket Distribution
| primary_bucket      |   count |
|:--------------------|--------:|
| STANDBY_BEFORE_NEED |     100 |
| FAMILY_HOME         |      80 |
| NOSTALGIA_TRUST     |      65 |
| MULTI_BUY           |      60 |
| PRACTICAL_STORAGE   |      60 |
| TRAVEL_CAR_BAG      |      45 |
| PERSONA_SPECIFIC    |      36 |
| TIKTOK_CURIOSITY    |      30 |
| VISUAL_RECOGNITION  |      15 |
| SEASONAL_CONTEXT    |       9 |

### Boldness Level Distribution
| boldness_level   |   count |
|:-----------------|--------:|
| BOLD             |     222 |
| MODERATE         |     158 |
| SOFT             |      75 |
| AGGRESSIVE       |      45 |

### Video Format Distribution
| video_format            |   count |
|:------------------------|--------:|
| product_only_video      |     130 |
| POV_scene               |      85 |
| TikTok_shop_short       |      65 |
| product_demo_style      |      60 |
| frames_video            |      45 |
| hybrid_video            |      44 |
| UGC_talking_head        |      41 |
| WhatsApp_followup_video |      30 |

### Poster Format Distribution
| poster_format           |   count |
|:------------------------|--------:|
| family_shelf_poster     |      80 |
| whatsapp_feedback_style |      65 |
| heritage_label_poster   |      65 |
| TikTok_shop_static_ad   |      64 |
| product_only_poster     |      64 |
| multi_buy_bundle_poster |      60 |
| travel_bag_poster       |      48 |
| drawer_standby_poster   |      36 |
| car_standby_poster      |      18 |

### Raw Claim Tolerance Distribution
| raw_claim_tolerance   |   count |
|:----------------------|--------:|
| HIGH                  |     396 |
| MEDIUM                |     102 |
| LOW                   |       2 |

### Production Review Required Distribution
| production_review_required   |   count |
|:-----------------------------|--------:|
| YES                          |     396 |
| NO                           |     104 |

## 3. Duplicate and Formatting Validation
- **Exact Duplicate Count**: 0 (all 500 rows have unique combination pairings and distinct scene/layout parameters).
- **Near-Duplicate Mitigation**: Component combinations reuse hooks/subhooks across different video/poster formats, buyer stages, or contexts to build diverse paths. No two rows share identical combination pairings and visual directions.

## 4. Quality Strategy & Weak Directions Avoided
- **Avoided generic AI prompts**: Every scene direction contains real local cues (e.g. *glove box kereta, laci dapur, meja vintaj, beg lampin baby*) that align with natural Malay vernacular.
- **Visual-first poster cues**: Avoided text-only layouts by detailing props, backgrounds, overlay hierarchies, and camera placement.

## 5. Sample Rows (Top 30 Video Matrix)
| video_matrix_id   | angle_name                       | video_format       | video_duration_fit   | raw_claim_tolerance   | production_review_required   |
|:------------------|:---------------------------------|:-------------------|:---------------------|:----------------------|:-----------------------------|
| MWTCB_VIDMAT_001  | Kecemasan Anak Tengah Malam      | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_002  | Kecemasan Anak Tengah Malam      | POV_scene          | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_003  | Kecemasan Anak Tengah Malam      | hybrid_video       | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_004  | Kecemasan Anak Tengah Malam      | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_005  | Hero Laci Dapur                  | product_only_video | 6s                   | MEDIUM                | NO                           |
| MWTCB_VIDMAT_006  | Hero Laci Dapur                  | POV_scene          | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_007  | Hero Laci Dapur                  | UGC_talking_head   | 30s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_008  | Hero Laci Dapur                  | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_009  | Need-Before-Need Mindset         | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_010  | Need-Before-Need Mindset         | POV_scene          | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_011  | Need-Before-Need Mindset         | hybrid_video       | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_012  | Need-Before-Need Mindset         | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_013  | Notis Sengal Sendi Tiba-Tiba     | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_014  | Notis Sengal Sendi Tiba-Tiba     | POV_scene          | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_015  | Notis Sengal Sendi Tiba-Tiba     | hybrid_video       | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_016  | Notis Sengal Sendi Tiba-Tiba     | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_017  | Bedside Table Standby            | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_018  | Bedside Table Standby            | POV_scene          | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_019  | Bedside Table Standby            | UGC_talking_head   | 30s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_020  | Bedside Table Standby            | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_021  | Kecemasan Tengah Malam Orang Tua | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_022  | Kecemasan Tengah Malam Orang Tua | POV_scene          | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_023  | Kecemasan Tengah Malam Orang Tua | hybrid_video       | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_024  | Kecemasan Tengah Malam Orang Tua | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_025  | Penyesalan Malam Sunyi           | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_026  | Penyesalan Malam Sunyi           | POV_scene          | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_027  | Penyesalan Malam Sunyi           | hybrid_video       | 20s                  | HIGH                  | YES                          |
| MWTCB_VIDMAT_028  | Penyesalan Malam Sunyi           | product_only_video | 6s                   | HIGH                  | YES                          |
| MWTCB_VIDMAT_029  | First Aid Box Checklist          | product_only_video | 6s                   | MEDIUM                | NO                           |
| MWTCB_VIDMAT_030  | First Aid Box Checklist          | POV_scene          | 20s                  | HIGH                  | YES                          |

## 6. Sample Rows (Top 30 Poster Matrix)
| poster_matrix_id   | angle_name                       | poster_format           | raw_claim_tolerance   | production_review_required   |
|:-------------------|:---------------------------------|:------------------------|:----------------------|:-----------------------------|
| MWTCB_POSTMAT_001  | Kecemasan Anak Tengah Malam      | whatsapp_feedback_style | HIGH                  | YES                          |
| MWTCB_POSTMAT_002  | Kecemasan Anak Tengah Malam      | TikTok_shop_static_ad   | HIGH                  | YES                          |
| MWTCB_POSTMAT_003  | Kecemasan Anak Tengah Malam      | product_only_poster     | HIGH                  | YES                          |
| MWTCB_POSTMAT_004  | Kecemasan Anak Tengah Malam      | whatsapp_feedback_style | HIGH                  | YES                          |
| MWTCB_POSTMAT_005  | Hero Laci Dapur                  | TikTok_shop_static_ad   | MEDIUM                | NO                           |
| MWTCB_POSTMAT_006  | Hero Laci Dapur                  | product_only_poster     | HIGH                  | YES                          |
| MWTCB_POSTMAT_007  | Hero Laci Dapur                  | whatsapp_feedback_style | HIGH                  | YES                          |
| MWTCB_POSTMAT_008  | Hero Laci Dapur                  | TikTok_shop_static_ad   | HIGH                  | YES                          |
| MWTCB_POSTMAT_009  | Need-Before-Need Mindset         | product_only_poster     | HIGH                  | YES                          |
| MWTCB_POSTMAT_010  | Need-Before-Need Mindset         | whatsapp_feedback_style | HIGH                  | YES                          |
| MWTCB_POSTMAT_011  | Need-Before-Need Mindset         | TikTok_shop_static_ad   | HIGH                  | YES                          |
| MWTCB_POSTMAT_012  | Need-Before-Need Mindset         | product_only_poster     | HIGH                  | YES                          |
| MWTCB_POSTMAT_013  | Notis Sengal Sendi Tiba-Tiba     | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_014  | Notis Sengal Sendi Tiba-Tiba     | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_015  | Notis Sengal Sendi Tiba-Tiba     | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_016  | Notis Sengal Sendi Tiba-Tiba     | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_017  | Bedside Table Standby            | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_018  | Bedside Table Standby            | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_019  | Bedside Table Standby            | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_020  | Bedside Table Standby            | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_021  | Kecemasan Tengah Malam Orang Tua | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_022  | Kecemasan Tengah Malam Orang Tua | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_023  | Kecemasan Tengah Malam Orang Tua | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_024  | Kecemasan Tengah Malam Orang Tua | drawer_standby_poster   | HIGH                  | YES                          |
| MWTCB_POSTMAT_025  | Penyesalan Malam Sunyi           | whatsapp_feedback_style | HIGH                  | YES                          |
| MWTCB_POSTMAT_026  | Penyesalan Malam Sunyi           | TikTok_shop_static_ad   | HIGH                  | YES                          |
| MWTCB_POSTMAT_027  | Penyesalan Malam Sunyi           | product_only_poster     | HIGH                  | YES                          |
| MWTCB_POSTMAT_028  | Penyesalan Malam Sunyi           | whatsapp_feedback_style | HIGH                  | YES                          |
| MWTCB_POSTMAT_029  | First Aid Box Checklist          | TikTok_shop_static_ad   | MEDIUM                | NO                           |
| MWTCB_POSTMAT_030  | First Aid Box Checklist          | product_only_poster     | HIGH                  | YES                          |

## 7. Unresolved Issues / Next Step
- **Unresolved Issues**: None.
- **Recommended Next Task**: `PART 8 — Notion Production Row Export and Prompt Pack Assembler`
