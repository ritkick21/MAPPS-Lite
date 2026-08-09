# MAPPS-Lite Week 7 Progress

## Week 7 Objective

Week 7 performed a candidate-level deep dive on the strongest materials surviving Week 6.

The objective was to move beyond broad screening scores and determine whether each candidate has physically plausible structure, redox chemistry, capacity, manageable risk, and sufficient evidence to justify additional investigation.

## Completed Stages

### Stage 1 - Crystal Structure Analysis

- Added `src/analyze_candidate_structures.py`.
- Retrieved Materials Project structures for the Week 6 finalists.
- Evaluated crystal system, space group, lattice geometry, Li content, Li-Li spacing, framework family, and structural risk.
- Generated `data/week7_candidate_structures.csv`.
- Generated `reports/week7_structure_analysis.md`.

### Stage 2 - Redox Chemistry

- Added `src/analyze_redox_chemistry.py`.
- Inferred charge-balanced oxidation states.
- Identified redox-active transition metals.
- Estimated conventional Li-coupled electron inventories.
- Generated `data/week7_redox_analysis.csv`.
- Generated `reports/week7_redox_analysis.md`.

### Stage 3 - Theoretical Performance

- Added `src/estimate_theoretical_performance.py`.
- Calculated formal theoretical capacity using electron inventory and molar mass.
- Added conservative utilization penalties for deep delithiation.
- Added heuristic voltage classes and specific-energy estimates.
- Generated `data/week7_theoretical_performance.csv`.
- Generated `reports/week7_theoretical_performance.md`.

### Stage 4 - Risk Assessment

- Added `src/assess_candidate_risks.py`.
- Evaluated structural, redox, performance, resource, and evidence failure modes.
- Generated `data/week7_risk_assessment.csv`.
- Generated `reports/week7_risk_assessment.md`.

### Stage 5 - Head-to-Head Comparison

- Added `src/compare_final_candidates.py`.
- Integrated explicit Week 6 literature, provenance, synthesis, transport, and resource evidence.
- Selected five provisional finalists.
- Generated `data/week7_candidate_comparison.csv`.
- Generated `reports/week7_candidate_comparison.md`.

### Stage 6 - Evidence Confidence

- Added `src/score_evidence_confidence.py`.
- Separated intrinsic research potential from evidence confidence.
- Distinguished known cathode controls from discovery candidates.
- Generated a dedicated discovery ranking and validation priority.
- Generated `data/week7_evidence_scores.csv`.
- Generated `reports/week7_evidence_confidence.md`.

### Stage 7 - Final Research Recommendation

- Added `src/final_week7_recommendation.py`.
- Assigned validated-reference, discovery, validation-target, research-shortlist, exploratory, and deprioritized roles.
- Generated `data/week7_final_ranking.csv`.
- Generated `reports/week7_final_recommendation.md`.

## Week 7 Outcome

- Total candidates deeply analyzed: **10**
- Known cathode controls: **1**
- Discovery candidates: **9**
- High-value validation targets: **2**

- Validated reference: **Li3V2(PO4)3 (mp-6396)**
- Primary discovery recommendation: **Li2VSiO5 (mp-18860)**
- Secondary discovery recommendation: **LiVPO5 (mp-26963)**

## Scientific Interpretation

Week 7 demonstrated that MAPPS-Lite can reject materials that appear structurally attractive but lack conventional cathode redox headroom.

The pipeline also successfully distinguished an established cathode control from less-validated discovery candidates.

The resulting discovery recommendations should be interpreted as candidates for further computational or experimental investigation, not as experimentally proven cathodes.

## Recommended Next Phase

Week 8 should focus on research-grade validation of the primary and secondary discovery recommendations.

Recommended next methods include phase-specific DFT, voltage calculation from lithiated and delithiated structures, Li-ion migration-barrier calculations, structural evolution during delithiation, and more rigorous literature/synthesis validation.
