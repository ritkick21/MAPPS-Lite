# MAPPS-Lite Week 5 Exact Electrode Validation

## Purpose

Earlier Week 5 electrochemical evaluation searched Materials Project by chemical formula. That established chemistry-level insertion-electrode evidence but did not necessarily validate the exact MAPPS-Lite material ID.

This stage queries Materials Project using a direct lithium battery identifier constructed from each candidate material ID, such as `mp-22526_Li`.

## Results

- Candidates checked: **179**
- Exact electrode matches: **105**
- Formula-family evidence only: **18**
- No MP electrode evidence: **56**
- Query errors: **0**

## Evidence Interpretation

**EXACT_ELECTRODE_MATCH** provides the strongest Materials Project evidence in the current MAPPS-Lite pipeline because the insertion-electrode record is associated directly with the candidate's battery identifier.

**FORMULA_FAMILY_ONLY** means the chemistry participates in a calculated insertion-electrode system, but a direct battery record for the exact MAPPS-Lite material ID was not returned.

**NO_ELECTRODE_EVIDENCE** does not imply novelty or impossibility. It only means the Materials Project insertion electrode dataset did not provide evidence through either search method used here.

## Exact Matches

| Material | Formula | Score | Voltage (V) | Capacity (mAh/g) | Energy (Wh/kg) | Volume Change (%) |
|---|---|---:|---:|---:|---:|---:|
| mp-22526 | LiCoO2 | 99.5 | 3.79 | 273.8 | 1037.8 | 0.0 |
| mp-1177382 | Li4MnCo5O12 | 98.8 | 4.21 | 188.3 | 793.6 | 0.1 |
| mp-25410 | LiMnPO4F | 96.8 | 4.04 | 293.2 | 1183.6 | 0.2 |
| mp-754656 | LiMnO2 | 96.2 | 3.26 | 285.5 | 931.6 | 0.2 |
| mp-758022 | LiCoPO4 | 96.2 | 4.33 | 166.6 | 722.1 | 0.0 |
| mp-18997 | LiMnPO4 | 95.8 | 3.80 | 170.9 | 648.9 | 0.1 |
| mp-850951 | Li3MnV(P2O7)2 | 95.3 | 4.03 | 169.4 | 683.4 | 0.1 |
| mp-850939 | Li2MnV(P2O7)2 | 95.3 | 4.03 | 169.4 | 683.4 | 0.1 |
| mp-759232 | LiMnV(P2O7)2 | 95.3 | 4.03 | 169.4 | 683.4 | 0.1 |
| mp-25448 | LiCrPO4F | 94.7 | 3.38 | 298.0 | 1006.3 | 0.2 |
| mp-2348641 | LiNiO2 | 94.3 | 3.78 | 183.0 | 691.0 | 0.0 |
| mp-19017 | LiFePO4 | 94.3 | 3.50 | 169.9 | 594.5 | 0.1 |
| mp-1177781 | Li2VFe(P2O7)2 | 94.1 | 3.76 | 169.1 | 636.0 | 0.1 |
| mp-849522 | Li8V3P8O29 | 93.7 | 4.14 | 173.5 | 718.5 | 0.0 |
| mp-26963 | LiVPO5 | 93.6 | 3.83 | 158.7 | 608.3 | 0.0 |
| mp-6396 | Li3V2(PO4)3 | 92.1 | 3.16 | 258.6 | 818.0 | 0.1 |
| mp-753866 | Li2VCr(P2O7)2 | 91.8 | 3.42 | 170.5 | 583.3 | 0.1 |
| mp-19107 | LiMnVO4 | 91.0 | 3.55 | 151.6 | 537.5 | 0.1 |
| mp-775982 | Li3V2P4(HO8)2 | 90.6 | 4.11 | 157.2 | 645.9 | 0.1 |
| mp-756507 | LiFePHO5 | 90.5 | 3.74 | 295.0 | 1103.4 | 0.1 |
| mp-753051 | LiCrPHO5 | 89.7 | 4.67 | 156.8 | 732.0 | 0.0 |
| mp-19511 | Li5FeO4 | 89.3 | 3.74 | 216.8 | 811.5 | 0.0 |
| mp-770632 | Li3CrO4 | 89.2 | 2.97 | 195.9 | 580.9 | 0.0 |
| mp-780606 | Li3Cr2(PO4)3 | 89.0 | 4.67 | 196.2 | 916.0 | 0.0 |
| mp-774155 | Li2FeO3 | 88.8 | 4.10 | 227.7 | 933.4 | 0.0 |
