# MAPPS-Lite

MAPPS-Lite is a lightweight materials discovery and screening pipeline inspired by the MAPPS framework.

The project is designed to explore how computational tools can collect, filter, score, and rank candidate materials for battery-related applications.

The current version focuses on lithium-containing cathode candidate screening using real data from the Materials Project database.

---

## Project Goals

MAPPS-Lite aims to build a simplified materials discovery workflow that can:

- Collect materials data from external scientific databases
- Filter large material datasets into smaller candidate pools
- Calculate screening metrics
- Rank candidate materials
- Produce interpretable outputs for further analysis
- Eventually incorporate more advanced materials-property prediction and AI-assisted screening

---

## Current Workflow

The current MAPPS-Lite pipeline is:

```text
Materials Project API
        ↓
src/materials_search.py
        ↓
13,221 initial Li/O-containing materials
        ↓
Cathode-oriented filtering
        ↓
4,949 candidates
        ↓
Missing-data and duplicate cleanup
        ↓
4,717 clean candidates
        ↓
data/materials.csv
        ↓
src/rank_materials.py
        ↓
Thermodynamic scoring
        ↓
Candidate ranking
        ↓
data/ranked_materials.csv