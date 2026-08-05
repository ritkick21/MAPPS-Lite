# MAPPS-Lite Week 5 Final Candidate Selection

## Overview

Week 5 extends MAPPS-Lite from composition-level screening into electrochemical and structure-specific candidate evaluation.

The final selection system combines the original MAPPS-Lite screening result with Materials Project lithium insertion electrode performance and the strength of the available electrochemical evidence.

## Evidence Summary

- Exact electrode matches: **105**
- Formula-family-only matches: **18**
- No MP electrode evidence: **56**
- Reference cathode chemistries in candidate set: **6**

## Reference Cathode Distribution

- Minimum benchmark score: **93.1**
- Median benchmark score: **95.5**
- Mean benchmark score: **95.9**
- Maximum benchmark score: **99.5**

## Final Score

For candidates with electrochemical evidence, the final selection score uses:

- Original MAPPS-Lite screening priority: **20%**
- Electrochemical performance: **65%**
- Evidence strength: **15%**

Exact-structure electrochemical scores always replace the earlier formula-family score when an exact electrode record exists.

Candidates with no electrode data are not assigned a validated-selection score. They remain in a separate discovery-review track based on the original MAPPS-Lite screening priority.

## Selection Tiers

- DISCOVERY_REVIEW_NO_ELECTRODE_DATA: **56**
- EXACT_LOWER_PRIORITY: **51**
- TIER_3_EXACT_PROMISING: **38**
- FORMULA_FAMILY_LOWER_PRIORITY: **9**
- FORMULA_FAMILY_FOLLOWUP: **8**
- TIER_2_EXACT_REFERENCE_RANGE: **7**
- REFERENCE_BASELINE: **6**
- TIER_1_EXACT_COMPETITIVE: **3**
- FORMULA_FAMILY_HIGH_PRIORITY: **1**

## Primary Research Shortlist

The primary shortlist contains the strongest non-reference candidates with exact Materials Project lithium insertion electrode evidence.

| Rank | Material | Formula | Final Score | Exact Electrochem | Benchmark | Tier |
|---:|---|---|---:|---:|---|---|
| 1 | mp-25448 | LiCrPO4F | 93.9 | 94.7 | WITHIN_REFERENCE_RANGE | TIER_2_EXACT_REFERENCE_RANGE |
| 2 | mp-850951 | Li3MnV(P2O7)2 | 93.1 | 95.3 | WITHIN_REFERENCE_RANGE | TIER_2_EXACT_REFERENCE_RANGE |
| 3 | mp-849522 | Li8V3P8O29 | 92.8 | 93.7 | WITHIN_REFERENCE_RANGE | TIER_2_EXACT_REFERENCE_RANGE |
| 4 | mp-850939 | Li2MnV(P2O7)2 | 92.1 | 95.3 | WITHIN_REFERENCE_RANGE | TIER_2_EXACT_REFERENCE_RANGE |
| 5 | mp-6396 | Li3V2(PO4)3 | 92.0 | 92.1 | BELOW_REFERENCE_RANGE | TIER_3_EXACT_PROMISING |
| 6 | mp-25410 | LiMnPO4F | 91.7 | 96.8 | ABOVE_REFERENCE_MEDIAN | TIER_1_EXACT_COMPETITIVE |
| 7 | mp-753866 | Li2VCr(P2O7)2 | 91.2 | 91.8 | BELOW_REFERENCE_RANGE | TIER_3_EXACT_PROMISING |
| 8 | mp-26963 | LiVPO5 | 91.1 | 93.6 | WITHIN_REFERENCE_RANGE | TIER_2_EXACT_REFERENCE_RANGE |
| 9 | mp-759232 | LiMnV(P2O7)2 | 90.1 | 95.3 | WITHIN_REFERENCE_RANGE | TIER_2_EXACT_REFERENCE_RANGE |
| 10 | mp-1177781 | Li2VFe(P2O7)2 | 90.1 | 94.1 | WITHIN_REFERENCE_RANGE | TIER_2_EXACT_REFERENCE_RANGE |
| 11 | mp-1539853 | LiV(OF)2 | 88.7 | 87.6 | BELOW_REFERENCE_RANGE | TIER_3_EXACT_PROMISING |
| 12 | mp-18860 | Li2VSiO5 | 88.4 | 86.1 | BELOW_REFERENCE_RANGE | TIER_3_EXACT_PROMISING |
| 13 | mp-780606 | Li3Cr2(PO4)3 | 88.3 | 89.0 | BELOW_REFERENCE_RANGE | TIER_3_EXACT_PROMISING |
| 14 | mp-775982 | Li3V2P4(HO8)2 | 87.1 | 90.6 | BELOW_REFERENCE_RANGE | TIER_3_EXACT_PROMISING |
| 15 | mp-26227 | LiVP2O7 | 86.6 | 84.3 | BELOW_REFERENCE_RANGE | TIER_3_EXACT_PROMISING |

## Formula-Family Follow-Up Candidates

These candidates have chemistry-level electrode evidence but lack direct validation for the exact MAPPS-Lite structure.

| Material | Formula | Final Score | Formula Electrochem | Benchmark |
|---|---|---:|---:|---|
| mp-1203394 | Li2MnP2O7 | 89.5 | 100.0 | ABOVE_REFERENCE_MAX |
| mp-775865 | Li2Ti3MnO8 | 82.6 | 83.7 | BELOW_REFERENCE_RANGE |
| mp-19373 | LiVO3 | 76.7 | 88.0 | BELOW_REFERENCE_RANGE |
| mp-1291671 | Li2V3CoO8 | 73.0 | 82.4 | BELOW_REFERENCE_RANGE |
| mp-17159 | Li2CrO4 | 72.8 | 89.2 | BELOW_REFERENCE_RANGE |
| mp-756242 | Li2CrFeO4 | 71.1 | 84.4 | BELOW_REFERENCE_RANGE |
| mp-755721 | Li4Cr3FeO8 | 70.6 | 81.7 | BELOW_REFERENCE_RANGE |
| mp-1193172 | Li2Mn(SO4)2 | 69.7 | 81.8 | BELOW_REFERENCE_RANGE |
| mp-775393 | Li2Cr3SbO8 | 69.3 | 79.3 | BELOW_REFERENCE_RANGE |
| mp-757614 | LiFeO2 | 69.1 | 86.3 | BELOW_REFERENCE_RANGE |

## Discovery Review Candidates

These candidates have no Materials Project insertion-electrode record through the searches performed in Week 5. They are retained for investigation rather than treated as failures.

| Discovery Rank | Material | Formula | Original Pipeline Priority |
|---:|---|---|---:|
| 1 | mp-16691 | SrLi2Ti6O14 | 100.0 |
| 2 | mp-558083 | BaLi2Ti6O14 | 99.4 |
| 3 | mp-774752 | Li2MgTi3O8 | 98.3 |
| 4 | mp-6332 | Li2TiSiO5 | 96.6 |
| 5 | mp-769637 | Li5Ti6FeO16 | 95.5 |
| 6 | mp-774797 | Li2Ti3ZnO8 | 94.9 |
| 7 | mp-6668 | LiTiPO5 | 93.8 |
| 8 | mp-768110 | Li2Ti3CoO8 | 92.1 |
| 9 | mp-2931 | Li2TiO3 | 91.6 |
| 10 | mp-1223017 | Li2TiCr(PO4)3 | 88.8 |

## Formula-Level vs Exact-Structure Differences

Large differences between formula-family and exact-structure scores demonstrate why direct structural validation is important.

| Material | Formula | Formula Score | Exact Score | Change |
|---|---|---:|---:|---:|
| mp-25977 | LiFe(PO3)4 | 81.4 | 54.4 | -27.0 |
| mp-1272804 | LiMn2O4 | 93.1 | 67.4 | -25.7 |
| mp-26997 | LiCo(PO3)4 | 72.9 | 52.0 | -20.9 |
| mp-31924 | LiMnP2O7 | 99.5 | 80.5 | -19.0 |
| mp-691115 | Li4Mn5O12 | 90.2 | 71.2 | -19.0 |
| mp-19294 | LiFeP2O7 | 96.6 | 78.7 | -17.8 |
| mp-26955 | LiV(PO3)4 | 84.2 | 66.7 | -17.5 |
| mp-19340 | LiVO2 | 97.1 | 80.2 | -16.8 |
| mp-26015 | LiCo(PO3)3 | 75.7 | 61.9 | -13.8 |
| mp-26967 | LiCr4(PO4)3 | 74.5 | 61.3 | -13.3 |

## Interpretation

The primary research shortlist should be interpreted as a prioritized computational screening result, not as a list of materials proven experimentally superior to commercial cathodes.

A candidate can score highly because of favorable calculated voltage, capacity, energy density, stability, and structural behavior while still performing poorly experimentally because of kinetic barriers, low lithium diffusivity, poor electronic conductivity, difficult synthesis, irreversible transitions, electrolyte incompatibility, toxicity, cost, or other effects not captured by the present model.

## Next Scientific Stage

The next development stage should investigate the final shortlist using literature evidence and additional properties such as synthesis history, known cathode behavior, ionic transport, electronic properties, and novelty relative to previously reported battery materials.
