# MWTCB Angle Master Bank Import Report (2026-06-19_part2_angle_bank)

## Scope
Generated the Angle Master Bank for Minyak Warisan Tok Cap Burung (MWTCB_25ML) from the 64 HIGH-priority buyer motivations in the landbank.

- Product ID: `MWTCB_25ML`
- Batch Version: `2026-06-19_part2_angle_bank`
- Total Angles Generated: 150
- Unique Motivation IDs Used: 64

## Distribution by Bucket
- STANDBY_BEFORE_NEED: 25 angles
- FAMILY_HOME: 20 angles
- NOSTALGIA_TRUST: 20 angles
- MULTI_BUY: 20 angles
- PRACTICAL_STORAGE: 20 angles
- TRAVEL_CAR_BAG: 15 angles
- TIKTOK_CURIOSITY / VISUAL_RECOGNITION: 15 angles
- PERSONA_SPECIFIC / SEASONAL_CONTEXT: 15 angles

## Distribution by Boldness Level
- BOLD: 63 angles
- MODERATE: 49 angles
- AGGRESSIVE: 22 angles
- SOFT: 16 angles

## Top 20 Strongest Angles
1. **Kecemasan Anak Tengah Malam** (STANDBY_BEFORE_NEED / AGGRESSIVE)
2. **Need-Before-Need Mindset** (STANDBY_BEFORE_NEED / BOLD)
3. **Kecemasan Tengah Malam Orang Tua** (STANDBY_BEFORE_NEED / AGGRESSIVE)
4. **Penyesalan Malam Sunyi** (STANDBY_BEFORE_NEED / AGGRESSIVE)
5. **Sakit Sendi Malam Buta** (STANDBY_BEFORE_NEED / BOLD)
6. **Kejang Betis Mengandung** (STANDBY_BEFORE_NEED / BOLD)
7. **Tumit Bisa Pijak Lantai** (STANDBY_BEFORE_NEED / BOLD)
8. **Petua Orang Lama Rumah Moden** (FAMILY_HOME / BOLD)
9. **Ego Rumah Cantik Tanpa Standby** (FAMILY_HOME / BOLD)
10. **Ubat Pinjam Jiran** (FAMILY_HOME / BOLD)
11. **Siksa Lutut Tangga Surau** (FAMILY_HOME / AGGRESSIVE)
12. **Bunyi Lutut Ketat Mak Ayah** (FAMILY_HOME / AGGRESSIVE)
13. **Anti-Hype Gimmick Viral** (NOSTALGIA_TRUST / BOLD)
14. **Bukan Produk OEM Semalam Suntuk** (NOSTALGIA_TRUST / BOLD)
15. **Legenda 1958 vs Gimmick OEM** (NOSTALGIA_TRUST / AGGRESSIVE)
16. **Tiga Lokasi Wajib Ready** (MULTI_BUY / BOLD)
17. **Anti-Botol Besar Menyemak** (PRACTICAL_STORAGE / BOLD)
18. **Trauma Minyak Pecah Beg** (PRACTICAL_STORAGE / AGGRESSIVE)
19. **Roadtrip Pening Kepala** (TRAVEL_CAR_BAG / AGGRESSIVE)
20. **Feed Stop-Scroll Cap Merah** (VISUAL_RECOGNITION / BOLD)

## Validation Results
All 150 rows were verified using `scripts/validate_copywriting_landbank.py --require-pandas`. 
- Checked exact column count (29 columns)
- Verified all motivation IDs map to existing HIGH priority rows
- Confirmed zero null values in critical fields (commercial_trigger, visual_scene, why_it_can_sell, boldness_level)
