# MAPPS-Lite

**Multi-Stage Computational Screening and Evidence Validation for Lithium-Ion Battery Cathode Discovery**

MAPPS-Lite is a Python-based materials discovery pipeline designed to identify and prioritize lithium-ion battery cathode candidates using Materials Project data.

The system begins with broad materials retrieval and thermodynamic screening, then progressively applies battery-specific electrochemical evaluation, benchmark comparison, exact-structure validation, literature evidence, synthesis feasibility, transport assessment, resource sustainability, provenance validation, evidence confidence, and risk-aware final ranking.

MAPPS-Lite is intended as a **research prioritization system**. It does not claim experimental discovery of a new cathode. Instead, it reduces a large computational search space into a smaller and more defensible set of materials for future computational or experimental study.

---

## Project Status

**MAPPS-Lite v1.0**

Final pipeline status:

* Pipeline integration: complete
* Scientific validation: complete
* Cross-stage traceability: validated
* Final ranking: complete
* Reproducibility manifest: generated
* Final scientific report: generated

---

## Research Question

MAPPS-Lite investigates the following question:

> How can a large computational materials database be systematically reduced into a defensible shortlist of lithium-ion battery cathode research candidates?

Rather than relying on a single property, MAPPS-Lite evaluates candidates through multiple independent research stages.

---

## Pipeline Architecture

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

## Pipeline Scale

The MAPPS-Lite v1.0 workflow processed the materials search space through increasingly selective stages.

| Stage                                           | Approximate Scale |
| ----------------------------------------------- | ----------------: |
| Materials Project records retrieved             |            13,221 |
| Cathode-like candidates after initial filtering |             4,949 |
| Cleaned materials                               |             4,717 |
| Thermodynamically ranked materials              |             4,717 |
| Detailed electrochemical evaluations            |               179 |
| Week 5 final candidate population               |               179 |
| Final Week 7 research candidates                |                10 |

The reduction in candidate count is intentional. Early stages maximize recall, while later stages demand progressively stronger scientific evidence.

---

## Methodology

### 1. Materials Search

`src/materials_search.py`

The first stage queries Materials Project and collects lithium-containing materials with properties relevant to cathode screening.

Retrieved properties include information such as:

* material ID
* chemical formula
* elemental composition
* density
* band gap
* energy above hull
* formation energy per atom
* thermodynamic stability

The resulting candidate dataset is stored in:

```text
data/materials.csv
```

---

### 2. Thermodynamic Ranking

`src/rank_materials.py`

Candidates are ranked using thermodynamic properties that provide an initial indication of material plausibility.

The ranking emphasizes:

* energy above hull
* formation energy
* stability

This stage reduces the importance of materials that appear thermodynamically unfavorable before battery-specific analysis is performed.

Primary output:

```text
data/ranked_materials.csv
```

---

### 3. Candidate Screening

`src/analyze_materials.py`

The analysis stage interprets the thermodynamic ranking and classifies candidates into research-oriented screening categories.

Primary outputs include:

```text
data/screened_materials.csv
reports/top_materials_report.md
```

Thermodynamic performance alone is not treated as proof that a material will function as a practical cathode.

---

### 4. Pipeline Orchestration

`src/main.py`

The main pipeline integrates the early discovery stages into a reproducible workflow:

```text
Search
  ->
Ranking
  ->
Screening
  ->
Reporting
```

Additional utility modules provide configuration, validation, and run summaries.

---

## Electrochemical Validation

### 5. Electrochemical Feature Construction

`src/electrochemical_features.py`

Battery-specific properties are extracted and normalized for use in later candidate evaluation.

---

### 6. Electrochemical Evaluation

`src/evaluate_electrochemistry.py`

Candidates are evaluated using available electrode evidence and battery-relevant quantities such as:

* average voltage
* gravimetric capacity
* volumetric capacity
* gravimetric energy density
* volumetric energy density
* volume change
* voltage-step behavior
* charged-state stability
* discharged-state stability
* data completeness

Primary output:

```text
data/electrochemical_evaluation.csv
```

---

### 7. Reference Cathode Benchmarking

`src/benchmark_cathodes.py`

Known lithium-ion cathode chemistries are retained as internal reference materials.

Reference families include chemistries such as:

* LCO
* LFP
* LMO
* LNO
* LMP
* LCP

These benchmarks help determine whether candidate performance falls within ranges observed for established cathode materials.

Outputs include:

```text
data/cathode_benchmarks.csv
data/benchmark_comparison.csv
reports/cathode_benchmark_report.md
```

---

### 8. Exact Structure Validation

`src/validate_electrode_structures.py`

Formula-level matches are not automatically treated as exact electrochemical evidence.

MAPPS-Lite therefore checks whether the exact candidate material has a corresponding electrode record.

Evidence can be separated into categories such as:

* exact electrode match
* formula-family match
* no electrode evidence

This prevents chemically related but structurally different materials from being treated as equivalent.

Primary output:

```text
data/exact_structure_validation.csv
```

---

### 9. Week 5 Candidate Selection

`src/final_candidate_selection.py`

Week 5 separates the candidate population into several research roles.

The final population contains three important categories:

1. **Final selection candidates**
   Materials with sufficient evidence for the principal ranked candidate list.

2. **Discovery-review candidates**
   Materials that remain scientifically interesting but lack sufficient electrode evidence.

3. **Benchmark-only controls**
   Established cathodes retained to calibrate the scoring system rather than being treated as new discoveries.

Primary outputs:

```text
data/final_candidate_ranking.csv
data/week5_shortlist.csv
reports/final_candidate_selection.md
reports/week5_progress.md
```

---

## Scientific Validation

Week 6 extends MAPPS-Lite beyond database scoring and evaluates whether shortlisted materials remain plausible research targets under broader scientific constraints.

### 10. Literature Validation

The pipeline evaluates available scientific evidence associated with candidate materials and related chemistries.

Primary outputs:

```text
data/week6_literature_hits.csv
data/week6_literature_validation.csv
reports/week6_literature_validation.md
```

---

### 11. Synthesis Feasibility

`src/assess_synthesis_feasibility.py`

Candidates are evaluated for practical synthesis plausibility based on the evidence available to MAPPS-Lite.

Primary output:

```text
data/week6_synthesis_feasibility.csv
```

---

### 12. Transport Evaluation

`src/evaluate_transport_properties.py`

Transport behavior is considered because thermodynamic stability and theoretical capacity do not guarantee useful battery kinetics.

Primary output:

```text
data/week6_transport_evaluation.csv
```

---

### 13. Resource Sustainability

`src/assess_resource_sustainability.py`

The pipeline introduces practical resource considerations so that theoretical performance is not evaluated independently of elemental availability and material risk.

Primary output:

```text
data/week6_resource_assessment.csv
```

---

### 14. Provenance Validation

Candidate evidence is checked for traceability across the research workflow.

Primary output:

```text
data/week6_provenance_validation.csv
```

---

### 15. Week 6 Final Ranking

`src/final_week6_selection.py`

The Week 6 stage integrates literature, synthesis, transport, sustainability, provenance, and electrochemical evidence into a more stringent research ranking.

Primary outputs:

```text
data/week6_final_ranking.csv
data/week6_research_shortlist.csv
reports/week6_final_selection.md
reports/week6_progress.md
```

---

## Evidence Confidence and Final Recommendation

### 16. Week 7 Final Research Recommendation

`src/final_week7_recommendation.py`

Week 7 separates three concepts that should not be treated as identical:

* **research potential**
* **evidence confidence**
* **research risk**

A material may be scientifically interesting while still carrying weak evidence or high uncertainty.

The final Week 7 ranking therefore provides an evidence-aware interpretation of candidate quality rather than treating every numerical score as equally reliable.

Primary outputs:

```text
data/week7_final_ranking.csv
reports/week7_final_recommendation.md
reports/week7_progress.md
```

---

## Final Results

The final Week 7 dataset contains **10 research candidates**.

Each candidate includes quantities such as:

```text
week7_final_rank
material_id
formula
final_recommendation
research_potential_score
evidence_confidence_score
total_risk_score
week7_final_score
```

Known cathode materials can appear in the final evaluation as validated references. Their presence provides an internal check that the pipeline can recognize established battery materials.

Discovery candidates should be interpreted as research priorities, not experimentally confirmed cathodes.

For the complete final ranking, see:

```text
data/week7_final_ranking.csv
```

For the human-readable interpretation, see:

```text
reports/week7_final_recommendation.md
```

---

## Week 8 Final Integration

### Pipeline Integration

`src/final_week8_pipeline.py`

Week 8 verifies that all major research artifacts from Weeks 1 through 7 are present and generates a reproducibility manifest.

Primary outputs:

```text
data/week8_pipeline_manifest.csv
reports/week8_pipeline_integration.md
```

The manifest records SHA-256 hashes for major research outputs.

---

### Final Integrity Validation

`src/final_pipeline_validation.py`

The final validator checks:

* required datasets
* non-empty outputs
* material ID completeness
* duplicate material IDs
* finite numerical values
* bounded score ranges
* signed comparison metrics
* Week 5 ranking-track integrity
* Week 7 final ranking integrity
* cross-stage candidate traceability
* final recommendation schema

Primary outputs:

```text
data/week8_validation_results.csv
reports/week8_pipeline_validation.md
```

The completed v1.0 pipeline passes the final integrity validation with no unresolved failures.

---

### Final Scientific Report

`src/generate_final_report.py`

The final report generator reads the actual MAPPS-Lite datasets and produces a consolidated scientific summary.

Output:

```text
reports/MAPPS_Lite_Final_Report.md
```

---

## Repository Structure

```text
MAPPS-Lite/
|
├── data/
│   ├── materials.csv
│   ├── ranked_materials.csv
│   ├── screened_materials.csv
│   ├── electrochemical_evaluation.csv
│   ├── cathode_benchmarks.csv
│   ├── benchmark_comparison.csv
│   ├── exact_structure_validation.csv
│   ├── final_candidate_ranking.csv
│   ├── week5_shortlist.csv
│   ├── week6_research_shortlist.csv
│   ├── week6_literature_validation.csv
│   ├── week6_synthesis_feasibility.csv
│   ├── week6_transport_evaluation.csv
│   ├── week6_resource_assessment.csv
│   ├── week6_provenance_validation.csv
│   ├── week6_final_ranking.csv
│   ├── week7_final_ranking.csv
│   ├── week8_pipeline_manifest.csv
│   └── week8_validation_results.csv
│
├── notebooks/
│
├── reports/
│   ├── top_materials_report.md
│   ├── electrochemical_evaluation.md
│   ├── cathode_benchmark_report.md
│   ├── exact_structure_validation.md
│   ├── final_candidate_selection.md
│   ├── week5_progress.md
│   ├── week6_final_selection.md
│   ├── week6_progress.md
│   ├── week7_final_recommendation.md
│   ├── week7_progress.md
│   ├── week8_pipeline_integration.md
│   ├── week8_pipeline_validation.md
│   └── MAPPS_Lite_Final_Report.md
│
├── src/
│   ├── config.py
│   ├── materials_search.py
│   ├── rank_materials.py
│   ├── analyze_materials.py
│   ├── main.py
│   ├── run_summary.py
│   ├── validate_pipeline.py
│   ├── electrochemical_features.py
│   ├── evaluate_electrochemistry.py
│   ├── benchmark_cathodes.py
│   ├── validate_electrode_structures.py
│   ├── final_candidate_selection.py
│   ├── assess_synthesis_feasibility.py
│   ├── evaluate_transport_properties.py
│   ├── assess_resource_sustainability.py
│   ├── final_week6_selection.py
│   ├── final_week7_recommendation.py
│   ├── final_week8_pipeline.py
│   ├── final_pipeline_validation.py
│   └── generate_final_report.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd MAPPS-Lite
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Materials Project API

MAPPS-Lite uses Materials Project data through the Materials Project Python API.

A Materials Project API key may be required when rerunning stages that query the remote database.

API credentials should **never be committed to the repository**.

Store secrets using environment variables or another secure local configuration method.

---

## Running MAPPS-Lite

### Early integrated pipeline

```bash
python src/main.py
```

### Final Week 8 integration check

```bash
python src/final_week8_pipeline.py
```

### Final integrity validation

```bash
python src/final_pipeline_validation.py
```

### Generate final scientific report

```bash
python src/generate_final_report.py
```

---

## Full Rebuild

The final Week 8 pipeline supports an optional rebuild mode:

```bash
python src/final_week8_pipeline.py --rebuild
```

This attempts to rerun available MAPPS-Lite research stages chronologically.

A full rebuild may require:

* internet access
* a valid Materials Project API key
* installed dependencies
* sufficient runtime for remote queries

For ordinary inspection of the final v1.0 results, a full rebuild is not necessary.

---

## Reproducibility

MAPPS-Lite v1.0 includes multiple reproducibility mechanisms.

### Artifact Manifest

```text
data/week8_pipeline_manifest.csv
```

The manifest records:

* artifact path
* existence status
* row count
* file size
* SHA-256 checksum

### Pipeline Validation

```text
data/week8_validation_results.csv
```

The validation dataset records the individual integrity checks applied to the final research pipeline.

Together, these artifacts provide a reproducible snapshot of the MAPPS-Lite v1.0 research outputs.

---

## Interpretation of Results

MAPPS-Lite rankings should be interpreted carefully.

A high score means that a material performs well under the current MAPPS-Lite evidence framework.

It does **not** mean that:

* the material has been experimentally validated
* the material can definitely be synthesized
* the predicted capacity will be achieved experimentally
* the material will cycle stably
* the material will outperform commercial cathodes
* the material is ready for commercial use

Instead, the ranking answers a narrower question:

> Which materials appear most justified for further investigation based on the evidence currently available to MAPPS-Lite?

---

## Limitations

MAPPS-Lite v1.0 has several important limitations.

### Database Dependence

The pipeline depends on the structures, calculations, and electrode data available from external computational databases.

### Heuristic Scoring

The scoring system prioritizes research candidates. Scores should not be interpreted as experimentally calibrated probabilities.

### Missing Electrode Evidence

A material without an existing electrode record may be unexplored rather than electrochemically impossible.

### No New DFT Calculations

MAPPS-Lite v1.0 primarily evaluates existing computational evidence rather than running new density functional theory calculations for every candidate.

### No Experimental Validation

The final candidate ranking has not been experimentally validated within this project.

### Literature Coverage

Scientific evidence depends on the completeness and quality of accessible literature and metadata.

---

## Future Work

Possible MAPPS-Lite v2 extensions include:

* automated DFT calculations
* voltage prediction
* capacity prediction
* diffusion-barrier calculations
* ionic conductivity modeling
* structural evolution during cycling
* machine-learning property prediction
* active learning
* uncertainty calibration
* automated literature retrieval
* LLM-based scientific agents
* automated hypothesis generation
* experimental synthesis collaboration
* electrochemical testing

---

## Final Research Artifacts

The most important final outputs are:

```text
data/week7_final_ranking.csv
data/week8_pipeline_manifest.csv
data/week8_validation_results.csv

reports/week7_final_recommendation.md
reports/week8_pipeline_integration.md
reports/week8_pipeline_validation.md
reports/MAPPS_Lite_Final_Report.md
```

---

## Project Scope

MAPPS-Lite v1.0 demonstrates how a materials discovery workflow can combine:

**large-scale search → thermodynamic screening → electrochemical evidence → structural validation → scientific evidence → practical constraints → uncertainty → final research prioritization**

The project is designed as a lightweight implementation inspired by autonomous materials discovery systems while remaining understandable, reproducible, and suitable for continued extension.

---

## Version

**MAPPS-Lite v1.0**

Final development cycle: Weeks 1 through 8.

---

## Disclaimer

MAPPS-Lite is a research and educational software project. Its outputs are computational research recommendations and should not be interpreted as experimentally validated materials performance or commercial engineering guidance.
