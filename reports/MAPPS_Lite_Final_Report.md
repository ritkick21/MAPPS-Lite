# MAPPS-Lite v1.0 Final Research Report

**Multi-Stage Computational Screening and Evidence Validation for Lithium-Ion Battery Cathode Discovery**

Generated: 2026-08-09 18:51:03

---

## Executive Summary

MAPPS-Lite is a computational materials-screening pipeline designed to identify and prioritize lithium-ion battery cathode candidates using Materials Project data and a sequence of increasingly strict scientific validation stages.

The system begins with broad candidate retrieval and thermodynamic screening, then progressively incorporates electrochemical performance, known cathode benchmarking, exact-structure evidence, literature support, synthesis feasibility, transport behavior, resource sustainability, provenance, evidence confidence, and overall research risk.

The purpose of MAPPS-Lite is not to claim experimental discovery of a new cathode. Instead, it provides a reproducible computational framework for narrowing a large materials search space into a small set of candidates that justify deeper computational or experimental investigation.

The highest-ranked Week 7 material is **Li3V2(PO4)3 (mp-6396)**.

- Final recommendation: **VALIDATED_REFERENCE**
- Research potential score: **82.5**
- Evidence confidence score: **87.9**
- Total risk score: **19.0**
- Week 7 final score: **80.2**

---

## 1. Research Objective

The central research question of MAPPS-Lite is:

> How can a large computational materials database be systematically reduced into a defensible shortlist of lithium-ion cathode research candidates?

MAPPS-Lite addresses this problem through staged filtering rather than relying on a single property or score.

---

## 2. Pipeline Architecture

```text
Materials Project
       |
       v
Candidate Search
       |
       v
Thermodynamic Ranking
       |
       v
Stability Screening
       |
       v
Electrochemical Evaluation
       |
       v
Reference Cathode Benchmarking
       |
       v
Exact Structure Validation
       |
       v
Research Candidate Selection
       |
       v
Literature Validation
       |
       v
Synthesis Feasibility
       |
       v
Transport Evaluation
       |
       v
Resource Sustainability
       |
       v
Provenance Validation
       |
       v
Evidence Confidence and Risk
       |
       v
FINAL RESEARCH RECOMMENDATION
```

---

## 3. Dataset Progression

| Pipeline Stage | Records |
|---|---:|
| Cleaned Materials Project candidates | 4717 |
| Thermodynamically ranked materials | 4717 |
| Screened materials | 4717 |
| Detailed electrochemical evaluations | 179 |
| Exact-structure validation records | 179 |
| Week 5 final candidate population | 179 |
| Week 5 shortlist | 15 |
| Week 6 research shortlist | 5 |
| Week 6 final ranking | 15 |
| Week 7 final research ranking | 10 |

The reduction in candidate count across later stages reflects the transition from broad database screening to increasingly evidence-intensive research evaluation.

---

## 4. Thermodynamic Screening

The early MAPPS-Lite stages use Materials Project properties to identify lithium-containing compounds with characteristics relevant to cathode screening.

The thermodynamic ranking emphasizes energy above hull, formation energy, and database stability. These variables provide an initial indication of whether a candidate is energetically plausible before more expensive or specialized battery-specific evaluation is performed.

This stage is deliberately broad. Thermodynamic favorability alone does not establish that a material will function as a practical battery cathode.

---

## 5. Electrochemical Evaluation

Week 5 introduced battery-specific evaluation. Candidate materials were compared against available Materials Project electrode records and formula-family evidence.

Electrochemical evaluation incorporates available properties such as voltage, gravimetric and volumetric capacity, energy density, volume change, voltage-step behavior, and charged/discharged-state stability.

The stored electrochemical evaluation contains **179 candidate records**.

---

## 6. Reference Cathode Benchmarking

Known cathode chemistries are retained as reference controls. These materials help calibrate whether candidate scores fall within ranges observed for established battery materials.

Reference materials are not automatically treated as new discoveries. They may instead receive a benchmark-only role so that the discovery ranking remains distinct from the validation controls.

---

## 7. Exact Structure Validation

Formula-level matching can overstate evidence because two materials with related compositions may correspond to different structures or electrode records.

MAPPS-Lite therefore performs an exact-material validation stage. Exact electrode evidence is treated as stronger than formula-family evidence, while candidates lacking electrode records remain available for discovery review rather than being incorrectly labeled as validated cathodes.

---

## 8. Week 5 Candidate Roles

Week 5 separates the candidate population into multiple research roles rather than forcing every material into the same ranking.

| Week 5 Role | Materials |
|---|---:|
| Main final-selection ranking | 117 |
| Discovery-review ranking | 56 |
| Benchmark-only controls | 6 |
| Total Week 5 population | 179 |

This distinction is important because absence of a known electrode record is not equivalent to proof that a material is unsuitable. Such candidates instead carry greater uncertainty and require further investigation.

---

## 9. Week 6 Scientific Validation

Week 6 expanded the evaluation beyond database-derived electrochemical properties. Candidates were assessed across several scientific and practical dimensions.

### 9.1 Literature Validation

`week6_literature_validation.csv` contains **15 records**.

Literature evidence is used to determine whether a candidate or closely related chemistry has meaningful external support and to separate database evidence from broader scientific evidence.

### 9.2 Synthesis Feasibility

`week6_synthesis_feasibility.csv` contains **15 records**.

Synthesis feasibility estimates whether a candidate appears reasonable to pursue experimentally based on the evidence available to the pipeline.

### 9.3 Transport Evaluation

`week6_transport_evaluation.csv` contains **15 records**.

Transport-related evaluation adds another constraint because thermodynamic stability and theoretical energy performance alone do not guarantee useful ion or electron transport.

### 9.4 Resource Sustainability

`week6_resource_assessment.csv` contains **15 records**.

Resource assessment introduces practical considerations such as elemental availability and material risk so that scientific performance is not evaluated in isolation.

### 9.5 Provenance Validation

`week6_provenance_validation.csv` contains **15 records**.

Provenance validation preserves traceability between final recommendations and the source evidence used to construct them.

---

## 10. Week 7 Evidence Confidence and Final Ranking

Week 7 combines the scientific evidence accumulated in the previous stages into the final MAPPS-Lite research ranking.

The final evaluation distinguishes between research potential and evidence confidence. This prevents a highly interesting but weakly supported material from being interpreted as equivalent to a well-established reference material.

Risk is retained as a separate quantity so that the final recommendation reflects both opportunity and uncertainty.

### Final Recommendation Distribution

| Recommendation Role | Candidates |
|---|---:|
| RESEARCH_SHORTLIST | 3 |
| HIGH_VALUE_VALIDATION_TARGET | 2 |
| EXPLORATORY | 2 |
| VALIDATED_REFERENCE | 1 |
| PRIMARY_DISCOVERY_RECOMMENDATION | 1 |
| SECONDARY_DISCOVERY_RECOMMENDATION | 1 |

### Final Top Candidates

| Rank | Material ID | Formula | Recommendation | Research Potential | Evidence Confidence | Risk | Final Score |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | mp-6396 | Li3V2(PO4)3 | VALIDATED_REFERENCE | 82.5 | 87.9 | 19.0 | 80.2 |
| 2 | mp-18860 | Li2VSiO5 | PRIMARY_DISCOVERY_RECOMMENDATION | 84.4 | 59.1 | 8.0 | 78.8 |
| 3 | mp-26963 | LiVPO5 | SECONDARY_DISCOVERY_RECOMMENDATION | 81.8 | 62.4 | 11.0 | 77.7 |
| 4 | mp-25410 | LiMnPO4F | HIGH_VALUE_VALIDATION_TARGET | 81.5 | 42.5 | 12.0 | 73.1 |
| 5 | mp-780606 | Li3Cr2(PO4)3 | HIGH_VALUE_VALIDATION_TARGET | 82.5 | 47.7 | 21.0 | 70.2 |
| 6 | mp-775982 | Li3V2P4(HO8)2 | RESEARCH_SHORTLIST | 75.7 | 40.6 | 26.0 | 67.4 |
| 7 | mp-850939 | Li2MnV(P2O7)2 | RESEARCH_SHORTLIST | 72.3 | 42.2 | 27.0 | 65.9 |
| 8 | mp-849522 | Li8V3P8O29 | RESEARCH_SHORTLIST | 72.5 | 37.9 | 37.0 | 63.3 |
| 9 | mp-759232 | LiMnV(P2O7)2 | EXPLORATORY | 62.8 | 38.8 | 36.0 | 58.9 |
| 10 | mp-1539853 | LiV(OF)2 | EXPLORATORY | 50.0 | 37.9 | 54.0 | 49.2 |

---

## 11. Pipeline Validation and Reproducibility

Week 8 performs final structural validation of the stored pipeline outputs.

| Validation Result | Count |
|---|---:|
| PASS | 487 |
| WARN | 0 |
| FAIL | 0 |
| TOTAL | 487 |

**Final pipeline validation status: VALID**

No unresolved integrity failures were detected in the final Week 8 validation run.

Week 8 also generates a pipeline manifest containing SHA-256 checksums for major project artifacts. These hashes provide a snapshot of the exact files used for the final MAPPS-Lite v1.0 results.

---

## 12. Scientific Interpretation

The MAPPS-Lite ranking should be interpreted as a research prioritization system rather than a prediction that the highest-ranked discovery candidate will necessarily become a successful commercial cathode.

A high final ranking indicates that a material performs well under the evidence and scoring framework implemented by MAPPS-Lite. A lower evidence-confidence score or higher risk score indicates that additional computational or experimental work is necessary before strong conclusions should be drawn.

Known reference cathodes provide an important internal control. Their presence allows the system to verify that its scoring framework can recognize established battery materials while still maintaining a separate discovery pathway for less-characterized candidates.

---

## 13. Limitations

MAPPS-Lite v1.0 has several important limitations:

1. **Database dependence.** Results depend on the structures and properties available through the underlying Materials Project datasets.

2. **Heuristic scoring.** The multi-stage scores are research prioritization tools rather than experimentally calibrated probabilities of cathode success.

3. **Incomplete electrochemical evidence.** Absence of an electrode record does not establish that a material cannot function electrochemically.

4. **No new first-principles calculations.** MAPPS-Lite v1.0 primarily evaluates existing computational evidence rather than performing new DFT calculations for every candidate.

5. **No experimental validation.** Final candidates have not been synthesized or electrochemically tested as part of this software pipeline.

6. **Literature and provenance limitations.** Evidence quality depends on the availability and reliability of external scientific records.

---

## 14. Future Work

A future MAPPS-Lite v2 could extend the current system with:

- automated first-principles calculations
- learned battery-property prediction models
- diffusion-barrier and ionic-conductivity calculations
- structural transformation prediction during cycling
- automated literature retrieval and evidence extraction
- uncertainty calibration
- active-learning candidate selection
- autonomous research agents
- experimental collaboration and synthesis validation

---

## 15. Conclusion

MAPPS-Lite v1.0 demonstrates a complete computational workflow for reducing a large materials database into a small, traceable set of lithium-ion cathode research recommendations.

The project progresses from broad thermodynamic screening to battery-specific electrochemical evaluation, structural validation, external evidence assessment, practical research constraints, confidence estimation, and final risk-aware ranking.

The final output is therefore not simply a list of materials. It is an evidence-linked research prioritization framework designed to show why each candidate advances through the pipeline and how strongly the available evidence supports the final recommendation.

---

## 16. Primary Final Artifacts

- `data/week7_final_ranking.csv`
- `data/week8_pipeline_manifest.csv`
- `data/week8_validation_results.csv`
- `reports/week7_final_recommendation.md`
- `reports/week8_pipeline_integration.md`
- `reports/week8_pipeline_validation.md`
- `reports/MAPPS_Lite_Final_Report.md`

**MAPPS-Lite v1.0 final scientific pipeline complete.**
