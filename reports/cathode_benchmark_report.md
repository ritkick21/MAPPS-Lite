# MAPPS-Lite Week 5 Cathode Benchmark Report

## Purpose

This analysis compares MAPPS-Lite candidates against established lithium-ion cathode chemistries using the same Materials Project insertion-electrode properties and the same MAPPS-Lite electrochemical scoring system.

The goal is to determine whether MAPPS-Lite reproduces known strong cathode behavior and whether other candidate chemistries appear competitive on the calculated metrics.

## Reference Cathodes

| Reference | Formula | Score | Voltage (V) | Capacity (mAh/g) | Energy (Wh/kg) | Volume Δ (%) |
|---|---|---:|---:|---:|---:|---:|
| LCO | LiCoO2 | 99.5 | 3.79 | 273.8 | 1037.8 | 0.0 |
| LFP | LiFePO4 | 94.3 | 3.50 | 169.9 | 594.5 | 0.1 |
| LMO | LiMn2O4 | 93.1 | 3.42 | 279.5 | 955.0 | 0.1 |
| LNO | LiNiO2 | 94.3 | 3.78 | 183.0 | 691.0 | 0.0 |
| LMP | LiMnPO4 | 97.5 | 4.13 | 293.2 | 1210.3 | 0.1 |
| LCP | LiCoPO4 | 96.7 | 4.26 | 166.6 | 709.5 | 0.1 |

## Reference Score Distribution

- Reference cathodes with usable data: **6**
- Minimum reference score: **93.1**
- Median reference score: **95.5**
- Mean reference score: **95.9**
- Maximum reference score: **99.5**

## MAPPS-Lite Comparison

- Candidates at or above the best reference score: **1**
- Other candidates at or above the reference median: **6**
- Candidates below the reference median: **110**
- Candidates without MP electrochemical verification: **56**
- MAPPS-Lite candidates that are themselves one of the reference chemistries: **6**

## Highest-Ranked Non-Reference Candidates

| Rank | Material | Formula | Score | Benchmark comparison | Database evidence |
|---:|---|---|---:|---|---|
| 1 | mp-1203394 | Li2MnP2O7 | 100.0 | ABOVE_REFERENCE_RANGE | FORMULA_FAMILY_MATCH |
| 2 | mp-31924 | LiMnP2O7 | 99.5 | ABOVE_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 4 | mp-1177382 | Li4MnCo5O12 | 98.8 | ABOVE_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 6 | mp-25410 | LiMnPO4F | 97.5 | ABOVE_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 7 | mp-19340 | LiVO2 | 97.1 | ABOVE_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 9 | mp-19294 | LiFeP2O7 | 96.6 | ABOVE_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 10 | mp-754656 | LiMnO2 | 96.2 | ABOVE_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 11 | mp-850951 | Li3MnV(P2O7)2 | 95.3 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 12 | mp-850939 | Li2MnV(P2O7)2 | 95.3 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 13 | mp-759232 | LiMnV(P2O7)2 | 95.3 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 14 | mp-25448 | LiCrPO4F | 94.7 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 17 | mp-780606 | Li3Cr2(PO4)3 | 94.2 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 18 | mp-1177781 | Li2VFe(P2O7)2 | 94.1 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 19 | mp-1539853 | LiV(OF)2 | 93.9 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 20 | mp-849522 | Li8V3P8O29 | 93.7 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 21 | mp-26963 | LiVPO5 | 93.6 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 23 | mp-753899 | LiFe(CO3)2 | 92.8 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 24 | mp-6396 | Li3V2(PO4)3 | 92.1 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 25 | mp-1101601 | LiV2(PO4)3 | 92.1 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |
| 26 | mp-771112 | Li2Mn3NiO8 | 92.1 | BELOW_REFERENCE_MEDIAN | FORMULA_FAMILY_MATCH |

## Interpretation

Candidates classified as ABOVE_REFERENCE_RANGE or ABOVE_REFERENCE_MEDIAN should not automatically be interpreted as experimentally superior to LCO, LFP, LMO, or other established cathodes. The current comparison focuses on computed voltage, capacity, specific energy, volume change, endpoint stability, and voltage-profile complexity.

Important experimental and engineering properties remain outside the present score, including lithium diffusivity, electronic conductivity, cycle life, irreversible phase transformations, oxygen evolution, synthesis feasibility, raw-material cost, toxicity, electrolyte compatibility, and manufacturability.

Additionally, MAPPS-Lite currently has formula-family electrode evidence for many candidates but no exact-structure matches among the PROMISING set. Therefore, these benchmark results should be treated as chemistry-level evidence until the exact candidate structures are validated.

## Novelty Warning

A candidate that is not one of the benchmark formulas is not necessarily novel. Novelty requires separate literature and database investigation. This report only identifies whether a candidate matches the small set of established reference chemistries used for benchmarking.
