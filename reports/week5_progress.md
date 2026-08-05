# MAPPS-Lite — Week 5 Progress Report

## Week 5 Goal

The goal of Week 5 was to extend MAPPS-Lite beyond preliminary thermodynamic and composition-based screening and introduce a scientifically stronger electrochemical evaluation layer.

Prior to Week 5, MAPPS-Lite could identify materials that appeared thermodynamically stable and chemically plausible as lithium cathode candidates.

Week 5 added the ability to ask a more important question:

> Does a candidate have calculated lithium insertion/extraction behavior that supports its use as an electrode material?

The Week 5 workflow introduced Materials Project insertion-electrode data, electrochemical scoring, comparison against established cathodes, exact material-ID validation, and final candidate selection.

---

# Starting Point

The Week 4 pipeline processed:

* 13,221 Materials Project records retrieved
* 4,949 materials remaining after preliminary cathode filtering
* 4,717 cleaned and ranked materials
* 179 PROMISING candidates
* 4,414 POSSIBLE candidates
* 124 REVIEW candidates

Week 4 primarily evaluated:

* energy above hull
* formation energy
* Materials Project stability
* lithium-containing compositions
* oxygen-containing compositions
* battery-relevant transition metals
* flagged elements
* overall thermodynamic ranking

These criteria were useful for candidate screening but did not directly evaluate battery behavior.

---

# Week 5 Pipeline

Week 5 added the following stages:

```text
screened_materials.csv
        |
        v
electrochemical_features.py
        |
        v
electrode_matches.csv
        |
        v
electrochemical evaluation
        |
        v
electrochemical_evaluation.csv
        |
        v
benchmark_cathodes.py
        |
        +----------------------------+
        |                            |
        v                            v
cathode_benchmarks.csv      benchmark_comparison.csv
        |
        v
validate_electrode_structures.py
        |
        v
exact_structure_validation.csv
        |
        v
final_candidate_selection.py
        |
        +-----------------------------+
        |                             |
        v                             v
final_candidate_ranking.csv   week5_shortlist.csv
```

---

# 1. Electrochemical Feature Retrieval

Week 5 first connected MAPPS-Lite PROMISING candidates with the Materials Project insertion-electrode database.

The following calculated properties were retrieved when available:

* average voltage
* gravimetric capacity
* volumetric capacity
* gravimetric energy
* volumetric energy
* lithium fraction in charged state
* lithium fraction in discharged state
* number of voltage steps
* maximum voltage step
* maximum structural volume change
* charged-state thermodynamic stability
* discharged-state thermodynamic stability

This was an important methodological improvement.

MAPPS-Lite does not attempt to infer battery voltage from formation energy or other unrelated properties.

Instead, battery-specific calculated data is retrieved directly from Materials Project.

---

# 2. Electrochemical Candidate Evaluation

All 179 PROMISING candidates were evaluated.

Initial Materials Project formula-level electrode matching produced:

* 123 candidates with insertion-electrode records
* 56 candidates without insertion-electrode records

The preliminary electrochemical ratings were:

* HIGH_PRIORITY: 69
* PROMISING: 38
* MODERATE: 13
* LOW_PRIORITY: 3
* UNVERIFIED: 56

The electrochemical scoring model considered:

* average voltage — 20%
* gravimetric capacity — 20%
* gravimetric energy — 20%
* maximum volume change — 15%
* charged/discharged stability — 20%
* voltage-profile complexity — 5%

Missing electrochemical properties reduced confidence instead of being treated as favorable values.

---

# 3. Reference Cathode Benchmarking

MAPPS-Lite was benchmarked against established lithium cathode chemistries.

The benchmark set included:

| Cathode | Formula | Electrochemical Score |
| ------- | ------- | --------------------: |
| LCO     | LiCoO2  |                  99.5 |
| LFP     | LiFePO4 |                  94.3 |
| LMO     | LiMn2O4 |                  93.1 |
| LNO     | LiNiO2  |                  94.3 |
| LMP     | LiMnPO4 |                  97.5 |
| LCP     | LiCoPO4 |                  96.7 |

The benchmark distribution was:

* Minimum: 93.1
* Median: 95.5
* Maximum: 99.5

This was an important validation of the electrochemical scoring system because known strong cathode chemistries received high scores.

Among the original candidate comparison:

* 1 non-reference candidate exceeded the maximum benchmark score
* 6 additional non-reference candidates exceeded the reference median
* 110 were below the reference median
* 56 remained electrochemically unverified
* 6 candidates corresponded directly to reference chemistries

---

# 4. Exact Electrode Structure Validation

Formula matching alone does not prove that the exact MAPPS-Lite crystal structure participates in a lithium insertion pathway.

Therefore, Week 5 introduced a stronger validation stage.

Each candidate Materials Project ID was queried using a lithium battery identifier of the form:

```text
mp-XXXXX_Li
```

This produced:

* Exact electrode matches: 105
* Formula-family-only matches: 18
* No electrode evidence: 56
* Query errors: 0

This substantially strengthened the evidence behind the MAPPS-Lite shortlist.

---

# Evidence Hierarchy

Week 5 now uses three levels of electrochemical evidence.

## EXACT_ELECTRODE_MATCH

The exact Materials Project structure has a lithium insertion-electrode record.

This is currently the strongest evidence level in MAPPS-Lite.

## FORMULA_FAMILY_ONLY

An insertion-electrode pathway exists for the chemical formula, but the exact MAPPS-Lite material ID was not validated.

These materials remain candidates for further investigation.

## NO_ELECTRODE_EVIDENCE

No Materials Project insertion-electrode record was found through either exact-ID or formula-based searching.

This does not mean the material is impossible or novel.

It means only that MAPPS-Lite currently lacks Materials Project electrochemical evidence for it.

---

# Importance of Exact Structure Validation

Week 5 demonstrated why formula-level evidence is not sufficient.

For example, some materials initially received extremely high formula-family electrochemical scores but considerably lower exact-structure scores.

Therefore:

> Exact-structure electrochemical data now overrides formula-family electrochemical data whenever an exact electrode record exists.

This prevents MAPPS-Lite from assigning one crystal structure the electrochemical performance of another structure with the same chemical formula.

---

# 5. Final Candidate Selection

The final selection system combines three evidence components:

* original MAPPS-Lite screening priority — 20%
* electrochemical performance — 65%
* electrochemical evidence strength — 15%

Electrochemical performance receives the largest weight because Week 5 is intended to move MAPPS-Lite beyond preliminary thermodynamic screening.

Exact electrode candidates receive stronger evidence weighting than formula-family-only candidates.

Candidates without electrochemical data are not forced into the same ranking.

Instead, they remain in a separate discovery-review track.

---

# Final Evidence Distribution

The original 179 PROMISING candidates are now separated into:

```text
179 PROMISING candidates
|
+-- 105 EXACT_ELECTRODE_MATCH
|
+-- 18 FORMULA_FAMILY_ONLY
|
+-- 56 NO_ELECTRODE_EVIDENCE
```

This is significantly more informative than the original PROMISING/POSSIBLE/REVIEW classification alone.

---

# Primary Week 5 Research Shortlist

The final selection system produced the following top 15 non-reference exact-structure candidates.

| Rank | Material ID | Formula       | Final Score | Electrochemical Score |
| ---: | ----------- | ------------- | ----------: | --------------------: |
|    1 | mp-25448    | LiCrPO4F      |        93.9 |                  94.7 |
|    2 | mp-850951   | Li3MnV(P2O7)2 |        93.1 |                  95.3 |
|    3 | mp-849522   | Li8V3P8O29    |        92.8 |                  93.7 |
|    4 | mp-850939   | Li2MnV(P2O7)2 |        92.1 |                  95.3 |
|    5 | mp-6396     | Li3V2(PO4)3   |        92.0 |                  92.1 |
|    6 | mp-25410    | LiMnPO4F      |        91.7 |                  96.8 |
|    7 | mp-753866   | Li2VCr(P2O7)2 |        91.2 |                  91.8 |
|    8 | mp-26963    | LiVPO5        |        91.1 |                  93.6 |
|    9 | mp-759232   | LiMnV(P2O7)2  |        90.1 |                  95.3 |
|   10 | mp-1177781  | Li2VFe(P2O7)2 |        90.1 |                  94.1 |
|   11 | mp-1539853  | LiV(OF)2      |        88.7 |                  87.6 |
|   12 | mp-18860    | Li2VSiO5      |        88.4 |                  86.1 |
|   13 | mp-780606   | Li3Cr2(PO4)3  |        88.3 |                  89.0 |
|   14 | mp-775982   | Li3V2P4(HO8)2 |        87.1 |                  90.6 |
|   15 | mp-26227    | LiVP2O7       |        86.6 |                  84.3 |

Known benchmark chemistries were excluded from this primary research shortlist so that established cathodes such as LiCoO2 do not dominate the research candidate ranking.

---

# Selection Tiers

Candidates are now organized into scientifically interpretable tiers.

## TIER_1_EXACT_COMPETITIVE

Exact Materials Project electrode evidence exists and calculated electrochemical performance is at or above the median established-cathode benchmark.

## TIER_2_EXACT_REFERENCE_RANGE

Exact electrode evidence exists and electrochemical performance lies within the established benchmark range.

## TIER_3_EXACT_PROMISING

Exact electrode evidence exists and performance is promising but below the primary benchmark range.

## EXACT_LOWER_PRIORITY

Exact electrode evidence exists, but the current electrochemical metrics are less competitive.

## FORMULA_FAMILY_HIGH_PRIORITY

Strong chemistry-level electrode evidence exists but exact structural validation is missing.

## FORMULA_FAMILY_FOLLOWUP

Moderate formula-family electrochemical evidence requiring additional validation.

## DISCOVERY_REVIEW_NO_ELECTRODE_DATA

No Materials Project electrode record was identified.

These materials remain candidates for further research rather than automatically being discarded.

---

# Key Scientific Improvements in Week 5

Week 5 changed MAPPS-Lite from primarily a thermodynamic screening system into a preliminary battery-material evaluation system.

The project can now assess:

* whether lithium insertion/extraction pathways are known computationally
* average calculated electrode voltage
* theoretical gravimetric capacity
* theoretical volumetric capacity
* theoretical gravimetric energy
* theoretical volumetric energy
* structural volume changes during cycling
* charged-state stability
* discharged-state stability
* voltage-profile complexity
* exact crystal-structure electrode evidence
* relative performance against established cathode chemistries

---

# Important Limitations

The final MAPPS-Lite score should not be interpreted as proof of experimental battery performance.

The present system does not yet directly model:

* lithium-ion diffusion barriers
* ionic conductivity
* electronic conductivity
* experimentally measured cycle life
* rate capability
* irreversible structural transformations
* oxygen release
* electrolyte decomposition
* thermal safety
* synthesis feasibility
* synthesis cost
* raw-material scarcity
* toxicity beyond the current basic flagged-element system
* manufacturing feasibility

A computationally promising material may therefore still perform poorly experimentally.

---

# Novelty

MAPPS-Lite does not currently label database-absent materials as novel.

A material receiving:

```text
NO_ELECTRODE_EVIDENCE
```

only means that Materials Project did not provide insertion-electrode evidence through the Week 5 search methods.

Determining scientific novelty requires separate literature and database research.

---

# Week 5 Outputs

New data outputs include:

```text
data/electrode_matches.csv
data/electrochemical_evaluation.csv
data/cathode_benchmarks.csv
data/benchmark_comparison.csv
data/exact_structure_validation.csv
data/final_candidate_ranking.csv
data/week5_shortlist.csv
```

New reports include:

```text
reports/electrochemical_evaluation.md
reports/cathode_benchmark_report.md
reports/exact_structure_validation.md
reports/final_candidate_selection.md
reports/week5_progress.md
```

New source files include:

```text
src/electrochemical_features.py
src/evaluate_electrochemistry.py
src/benchmark_cathodes.py
src/validate_electrode_structures.py
src/final_candidate_selection.py
```

---

# Week 5 Outcome

Week 5 successfully transformed the 179 preliminary PROMISING candidates into a much more scientifically structured candidate set.

MAPPS-Lite now distinguishes between:

1. thermodynamic plausibility
2. chemistry-level electrochemical evidence
3. exact-structure electrochemical evidence
4. performance relative to established cathodes
5. computational research priority

The most important result is the identification of a 15-material exact-structure research shortlist for deeper investigation.

---

# Next Development Stage

The next stage should move from computational electrode screening toward deeper candidate verification.

Potential next steps include:

* literature searches for the final shortlist
* determining whether candidates have already been studied as cathodes
* distinguishing established materials from underexplored candidates
* evaluating synthesis feasibility
* investigating lithium diffusion and ionic transport
* evaluating electronic properties
* examining transition-metal cost and abundance
* improving toxicity and sustainability screening
* identifying potentially novel or underexplored candidate systems
* producing detailed candidate dossiers
* selecting a smaller set of materials for higher-level computational or experimental investigation

The Week 5 shortlist should serve as the starting point for this deeper scientific validation.
