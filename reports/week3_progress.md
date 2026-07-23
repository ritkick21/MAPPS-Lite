# MAPPS-Lite Week 3 Progress Report

## Objective

The goal of Week 3 was to extend MAPPS-Lite beyond simple thermodynamic ranking by adding an analysis and secondary screening layer for candidate battery cathode materials.

The Week 2 pipeline ranked materials using thermodynamic properties, but inspection of the highest-ranked materials showed that thermodynamic stability alone does not guarantee practical cathode suitability. Week 3 therefore focused on interpreting the ranked results and identifying candidates that may require additional review.

## Work Completed

### 1. Created `analyze_materials.py`

A new analysis module was added:

`src/analyze_materials.py`

The script loads the ranked material dataset produced during Week 2 and applies an additional composition-based screening process.

### 2. Added Chemical Formula Analysis

The program extracts individual chemical elements from each material formula.

For example:

`Li2Ti3MnO8`

is interpreted as containing:

* Li
* Ti
* Mn
* O

This allows MAPPS-Lite to examine material composition in addition to thermodynamic properties.

### 3. Added Battery-Relevant Metal Detection

The screening system currently checks for the following transition metals commonly associated with battery electrode chemistry:

* Ti
* V
* Cr
* Mn
* Fe
* Co
* Ni

Materials containing at least one of these elements can pass the current transition-metal screening requirement.

### 4. Added Element Review Flags

The screening layer currently flags several elements for additional review:

* Pb
* Hg
* Cd
* U

These materials are not automatically rejected. Instead, MAPPS-Lite assigns them a `REVIEW` status so that they can receive further human evaluation.

### 5. Added Candidate Status Classification

Each material is assigned one of three preliminary screening statuses:

#### PROMISING

The material:

* Passes the current composition screening
* Contains at least one battery-relevant transition metal
* Contains no currently flagged elements
* Has an energy above hull of 0 eV/atom
* Is identified as stable

#### POSSIBLE

The material passes the basic composition screening but does not meet all of the current thermodynamic requirements for `PROMISING` status.

#### REVIEW

The material contains a flagged element or does not contain a transition metal from the current battery-relevant screening list.

These classifications are preliminary screening labels and are not final judgments of electrochemical performance.

### 6. Screened the Full Ranked Dataset

Instead of analyzing only the top 10 materials, the Week 3 pipeline now applies the composition screening process to every ranked candidate.

The results are saved to:

`data/screened_materials.csv`

The screened dataset includes the original material properties and additional columns for:

* Battery-relevant metals
* Flagged elements
* Screening status

### 7. Added Full-Dataset Screening Statistics

The analysis script now calculates summary statistics for the entire screened dataset, including:

* Total materials screened
* Number of `PROMISING` materials
* Number of `POSSIBLE` materials
* Number of `REVIEW` materials
* Number of materials containing each flagged element

### 8. Improved the Top Materials Report

The analysis pipeline generates:

`reports/top_materials_report.md`

The report now includes:

* Full-dataset screening statistics
* Current ranking methodology
* Flagged element statistics
* Top 10 highest-ranked `PROMISING` candidates
* Thermodynamic properties
* Composition assessments
* Human-readable ranking explanations
* Preliminary MAPPS-Lite candidate assessments

## Current MAPPS-Lite Pipeline

The complete pipeline at the end of Week 3 is:

Materials Project API
↓
`materials_search.py`
↓
`materials.csv`
↓
`rank_materials.py`
↓
`ranked_materials.csv`
↓
`analyze_materials.py`
↓
`screened_materials.csv`
↓
`top_materials_report.md`

## Key Finding

Week 3 revealed an important limitation in the original ranking system.

Because the ranking model heavily rewards low energy above hull and thermodynamic stability, some chemically questionable candidates can still receive very high scores.

The Week 3 screening layer addresses this limitation by separating thermodynamic ranking from composition-based review.

MAPPS-Lite now follows a more structured workflow:

Search
↓
Rank
↓
Screen
↓
Analyze
↓
Recommend candidates for further investigation

## Week 3 Outcome

By the end of Week 3, MAPPS-Lite can:

* Search for candidate materials
* Rank materials using thermodynamic properties
* Analyze chemical formulas
* Identify selected battery-relevant transition metals
* Flag selected elements for review
* Assign preliminary screening statuses
* Screen the complete material dataset
* Generate screening statistics
* Produce a human-readable report of the strongest current candidates

The next stage of development can focus on improving the scientific relevance of the ranking model by introducing additional battery-specific properties and evaluating candidates based on predicted electrochemical performance.
