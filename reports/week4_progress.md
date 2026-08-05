# MAPPS-Lite Week 4 Progress Report

## Overview

Week 4 focused on transforming MAPPS-Lite from a collection of separate Python scripts into a coordinated and configurable materials-discovery workflow.

Before Week 4, the search, ranking, and screening stages were primarily executed independently. During Week 4, these components were refactored so they can be called by a central orchestrator, configured from a shared settings file, validated automatically, and documented after each run.

The resulting pipeline can now execute the complete workflow using a single command.

---

## 1. Pipeline Orchestration

A new central program was created:

`src/main.py`

This file acts as the MAPPS-Lite orchestrator.

The complete workflow is now:

Materials Project
↓
Material Search
↓
Initial Cathode Filtering
↓
Thermodynamic Ranking
↓
Chemical Composition Screening
↓
Candidate Classification
↓
Automated Validation
↓
Final Reports

The complete system can be executed with:

`python src/main.py`

This replaces the previous process of manually running each Python script separately.

---

## 2. Search Pipeline Refactoring

`src/materials_search.py` was refactored so the material search process can be called by another Python program.

The primary callable function is:

`run_search_pipeline()`

The search workflow now performs the following steps:

1. Connects to the Materials Project API.
2. Searches for compounds containing lithium and oxygen.
3. Restricts the number of elements in each compound.
4. Retrieves relevant thermodynamic and material properties.
5. Filters compounds for cathode-relevant metals.
6. Applies the configured energy-above-hull threshold.
7. Removes incomplete and duplicate entries.
8. Saves the resulting dataset.

Output:

`data/materials.csv`

During the current pipeline run:

* 13,221 materials were retrieved from Materials Project.
* 4,949 passed the initial cathode filter.
* 4,717 remained after cleaning.

The Materials Project API call was also updated to use the current `num_elements` parameter.

---

## 3. Ranking Pipeline Refactoring

`src/rank_materials.py` was refactored around the callable function:

`run_ranking_pipeline()`

The ranking model evaluates candidates using three thermodynamic factors:

* Energy above hull: 55%
* Formation energy per atom: 35%
* Materials Project stability flag: 10%

Lower energy above hull and lower formation energy receive stronger normalized scores.

Each candidate receives the following calculated fields:

* `hull_score`
* `formation_score`
* `stability_score`
* `score`
* `rank`

The candidates are then sorted from highest to lowest score.

Output:

`data/ranked_materials.csv`

During the current pipeline run, all 4,717 cleaned candidates were successfully ranked.

---

## 4. Chemistry Screening and Candidate Classification

`src/analyze_materials.py` was refactored around:

`run_analysis_pipeline()`

The secondary screening stage evaluates chemical composition after thermodynamic ranking.

The screening process identifies:

* lithium
* oxygen
* battery-relevant transition metals
* configured flagged elements

The current battery-relevant transition metals are:

* Ti
* V
* Cr
* Mn
* Fe
* Co
* Ni

The current flagged elements are:

* Pb — lead
* Hg — mercury
* Cd — cadmium
* U — uranium

Candidates are classified into three categories.

### PROMISING

A material is classified as PROMISING when:

* it contains a battery-relevant transition metal,
* it does not contain a configured flagged element,
* its energy above hull is 0 eV/atom,
* and Materials Project identifies it as stable.

### POSSIBLE

A material is classified as POSSIBLE when it passes the basic composition screen but does not satisfy the strongest thermodynamic requirements used for PROMISING classification.

### REVIEW

A material is classified as REVIEW when:

* it contains a flagged element, or
* no transition metal from the configured battery-relevant list is detected.

These classifications are preliminary screening labels and are not final electrochemical judgments.

The current screening results are:

* PROMISING: 179
* POSSIBLE: 4,414
* REVIEW: 124

Output:

`data/screened_materials.csv`

---

## 5. Automated Candidate Report

The analysis pipeline generates:

`reports/top_materials_report.md`

The report selects the highest-ranked PROMISING candidates and summarizes:

* Materials Project ID
* overall ranking
* MAPPS-Lite ranking score
* energy above hull
* formation energy
* stability classification
* density
* band gap when available
* thermodynamic ranking explanation
* composition assessment
* MAPPS-Lite candidate assessment

The number of candidates shown in the report is controlled by the MAPPS-Lite configuration.

---

## 6. Central Configuration System

A new file was created:

`src/config.py`

This file centralizes the scientific parameters used throughout MAPPS-Lite.

It currently controls:

### Materials Search

* required elements
* minimum number of elements
* maximum number of elements
* Materials Project hull-energy search range
* candidate hull-energy threshold
* cathode-relevant metals
* Materials Project fields

### Ranking

* energy-above-hull weight
* formation-energy weight
* stability weight

### Screening

* battery-relevant transition metals
* flagged elements
* candidate status labels

### Reporting

* number of top candidates displayed

This removes duplicated scientific settings from individual scripts.

Changing a ranking weight in `config.py`, for example, automatically changes the value used by the ranking algorithm and the value displayed in generated reports.

Configuration validation was also added to ensure that the ranking weights sum to 1.0 and that configured thresholds are internally consistent.

---

## 7. Multiple Pipeline Execution Modes

The central orchestrator now supports several execution modes.

### Full Pipeline

`python src/main.py`

Runs:

Search → Ranking → Screening → Validation → Run Summary

### Skip Search

`python src/main.py --skip-search`

Uses the existing:

`data/materials.csv`

and runs:

Ranking → Screening → Validation → Run Summary

This avoids unnecessary Materials Project API requests while developing the ranking model.

### Analysis Only

`python src/main.py --analysis-only`

Uses the existing:

`data/ranked_materials.csv`

and runs:

Screening → Validation → Run Summary

This is useful while modifying screening rules or report generation.

---

## 8. Run Provenance Tracking

A new module was created:

`src/run_summary.py`

After every successful MAPPS-Lite execution, the pipeline generates:

`reports/run_summary.md`

The run summary records:

* execution time
* pipeline mode
* dataset sizes
* screening results
* search configuration
* hull-energy thresholds
* ranking weights
* cathode-metal configuration
* battery-relevant metals
* flagged elements
* flagged-element counts
* report settings
* generated output files

This improves reproducibility by recording the scientific configuration associated with the most recent MAPPS-Lite results.

---

## 9. Automated Pipeline Validation

A new validation module was created:

`src/validate_pipeline.py`

Validation now executes automatically before the run summary is generated.

The system checks:

* configuration validity
* required dataset columns
* unique Materials Project IDs
* candidate hull-energy thresholds
* score bounds
* component-score bounds
* sequential ranking
* ranking order
* valid screening statuses
* consistent dataset sizes
* consistent material identities between stages

If any validation check fails, MAPPS-Lite stops and reports the failure instead of treating the run as successful.

This provides an automated integrity check when the ranking model or screening rules are modified in future development.

---

## 10. Current MAPPS-Lite Architecture

The project workflow after Week 4 is:

`src/config.py`
↓
shared scientific configuration

`src/materials_search.py`
↓
`data/materials.csv`

`src/rank_materials.py`
↓
`data/ranked_materials.csv`

`src/analyze_materials.py`
↓
`data/screened_materials.csv`
↓
`reports/top_materials_report.md`

`src/validate_pipeline.py`
↓
pipeline integrity checks

`src/run_summary.py`
↓
`reports/run_summary.md`

All stages are coordinated by:

`src/main.py`

---

## 11. Week 4 Accomplishments

Week 4 completed the following major improvements:

* Created a central MAPPS-Lite orchestrator.
* Converted search, ranking, and analysis scripts into callable pipeline components.
* Added full-pipeline execution with one command.
* Added reusable skip-search and analysis-only execution modes.
* Centralized scientific parameters in `config.py`.
* Added configuration validation.
* Added dataset validation.
* Added ranking validation.
* Added screening validation.
* Added cross-stage material consistency validation.
* Added automatic run provenance tracking.
* Improved error handling.
* Removed duplicated scientific settings.
* Improved report consistency.
* Preserved the Week 2 and Week 3 scientific workflow while significantly improving software architecture.

---

## 12. Current Pipeline Results

The current successful MAPPS-Lite run produced:

* Materials Project records retrieved: 13,221
* Candidates after initial cathode filtering: 4,949
* Candidates after cleaning: 4,717
* Ranked materials: 4,717
* Screened materials: 4,717

Final screening classifications:

* PROMISING: 179
* POSSIBLE: 4,414
* REVIEW: 124

The complete workflow successfully runs from Materials Project retrieval through final candidate reporting and automated validation.

---

## Next Development Stage

Week 4 established the software architecture needed for more advanced scientific development.

Future work can now focus less on pipeline infrastructure and more on improving the scientific quality of candidate evaluation.

Potential next steps include:

* incorporating additional electrochemical properties,
* evaluating theoretical voltage,
* considering lithium extraction and insertion behavior,
* evaluating theoretical capacity,
* distinguishing known cathode materials from more novel candidates,
* improving chemical plausibility screening,
* comparing MAPPS-Lite rankings against known battery materials,
* and developing more advanced candidate-selection strategies.

These improvements can now be integrated into the existing pipeline without restructuring the entire project.
