# MAPPS-Lite Week 5 Electrochemical Evaluation

## Purpose

This report evaluates MAPPS-Lite PROMISING cathode candidates using lithium insertion-electrode properties retrieved from Materials Project.

The electrochemical score is a screening metric rather than a prediction of experimental battery performance. Cycle life, rate capability, electronic conductivity, ionic diffusivity, synthesis feasibility, electrolyte compatibility, and safety still require additional evaluation.

## Database Evidence

- PROMISING candidates evaluated: **179**
- Exact MP structure matches: **0**
- Formula-family electrode matches: **123**
- No MP insertion-electrode record: **56**

A candidate with no Materials Project electrode record is labeled **UNVERIFIED**, not novel. Database absence alone is not evidence that a material has never been studied experimentally or computationally.

## Electrochemical Ratings

- HIGH_PRIORITY: **69**
- PROMISING: **38**
- MODERATE: **13**
- LOW_PRIORITY: **3**
- UNVERIFIED: **56**

## Scoring Method

The screening score combines:

- average voltage: 20%
- gravimetric capacity: 20%
- gravimetric specific energy: 20%
- maximum volume change: 15%
- charged/discharged thermodynamic stability: 20%
- voltage-step complexity: 5%

Missing electrochemical fields reduce the confidence-adjusted score rather than being silently treated as ideal values.

## Match Definitions

**DIRECT_STRUCTURE_MATCH** means the candidate's exact Materials Project material ID occurs in the retrieved lithium insertion pathway.

**FORMULA_FAMILY_MATCH** means an electrode pathway was found for the same chemical formula, but the exact candidate structure ID was not identified in that pathway.

**NO_MP_ELECTRODE_RECORD** means no insertion-electrode entry was returned for that candidate formula.

## Highest-Ranked Verified Candidates

| Rank | Material | Formula | Evidence | Score | Voltage (V) | Capacity (mAh/g) | Energy (Wh/kg) | Volume Δ (%) | Rating |
|---:|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | mp-1203394 | Li2MnP2O7 | FORMULA_FAMILY_MATCH | 100.0 | 4.03 | 220.8 | 889.4 | 0.1 | HIGH_PRIORITY |
| 2 | mp-31924 | LiMnP2O7 | FORMULA_FAMILY_MATCH | 99.5 | 4.03 | 220.8 | 889.1 | 0.1 | HIGH_PRIORITY |
| 3 | mp-22526 | LiCoO2 | FORMULA_FAMILY_MATCH | 99.5 | 3.79 | 273.8 | 1037.8 | 0.0 | HIGH_PRIORITY |
| 4 | mp-1177382 | Li4MnCo5O12 | FORMULA_FAMILY_MATCH | 98.8 | 4.21 | 188.3 | 793.6 | 0.1 | HIGH_PRIORITY |
| 5 | mp-18997 | LiMnPO4 | FORMULA_FAMILY_MATCH | 97.5 | 4.13 | 293.2 | 1210.3 | 0.1 | HIGH_PRIORITY |
| 6 | mp-25410 | LiMnPO4F | FORMULA_FAMILY_MATCH | 97.5 | 4.13 | 293.2 | 1210.3 | 0.1 | HIGH_PRIORITY |
| 7 | mp-19340 | LiVO2 | FORMULA_FAMILY_MATCH | 97.1 | 3.68 | 246.2 | 906.4 | 0.0 | HIGH_PRIORITY |
| 8 | mp-758022 | LiCoPO4 | FORMULA_FAMILY_MATCH | 96.7 | 4.26 | 166.6 | 709.5 | 0.1 | HIGH_PRIORITY |
| 9 | mp-19294 | LiFeP2O7 | FORMULA_FAMILY_MATCH | 96.6 | 3.93 | 220.0 | 865.1 | 0.0 | HIGH_PRIORITY |
| 10 | mp-754656 | LiMnO2 | FORMULA_FAMILY_MATCH | 96.2 | 3.26 | 285.5 | 931.6 | 0.2 | HIGH_PRIORITY |
| 11 | mp-850951 | Li3MnV(P2O7)2 | FORMULA_FAMILY_MATCH | 95.3 | 4.03 | 169.4 | 683.4 | 0.1 | HIGH_PRIORITY |
| 12 | mp-850939 | Li2MnV(P2O7)2 | FORMULA_FAMILY_MATCH | 95.3 | 4.03 | 169.4 | 683.4 | 0.1 | HIGH_PRIORITY |
| 13 | mp-759232 | LiMnV(P2O7)2 | FORMULA_FAMILY_MATCH | 95.3 | 4.03 | 169.4 | 683.4 | 0.1 | HIGH_PRIORITY |
| 14 | mp-25448 | LiCrPO4F | FORMULA_FAMILY_MATCH | 94.7 | 3.38 | 298.0 | 1006.3 | 0.2 | HIGH_PRIORITY |
| 15 | mp-2348641 | LiNiO2 | FORMULA_FAMILY_MATCH | 94.3 | 3.78 | 183.0 | 691.0 | 0.0 | HIGH_PRIORITY |
| 16 | mp-19017 | LiFePO4 | FORMULA_FAMILY_MATCH | 94.3 | 3.50 | 169.9 | 594.5 | 0.1 | HIGH_PRIORITY |
| 17 | mp-780606 | Li3Cr2(PO4)3 | FORMULA_FAMILY_MATCH | 94.2 | 3.89 | 257.3 | 1000.6 | 0.1 | HIGH_PRIORITY |
| 18 | mp-1177781 | Li2VFe(P2O7)2 | FORMULA_FAMILY_MATCH | 94.1 | 3.76 | 169.1 | 636.0 | 0.1 | HIGH_PRIORITY |
| 19 | mp-1539853 | LiV(OF)2 | FORMULA_FAMILY_MATCH | 93.9 | 3.74 | 198.8 | 744.2 | 0.0 | HIGH_PRIORITY |
| 20 | mp-849522 | Li8V3P8O29 | FORMULA_FAMILY_MATCH | 93.7 | 4.14 | 173.5 | 718.5 | 0.0 | HIGH_PRIORITY |
