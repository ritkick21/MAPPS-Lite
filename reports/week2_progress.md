# MAPPS-Lite — Week 2 Progress Report

## Week 2 Goal

The goal of Week 2 was to move MAPPS-Lite from a manually created materials dataset to a real materials-screening pipeline using data from the Materials Project API.

By the end of Week 2, MAPPS-Lite can:

- Connect to the Materials Project API
- Download thousands of lithium- and oxygen-containing materials
- Convert API results into a Pandas DataFrame
- Filter the dataset for more plausible cathode candidates
- Remove incomplete or duplicate records
- Calculate preliminary thermodynamic screening scores
- Rank thousands of candidate materials
- Save the ranked results to a CSV file

---

## Project Pipeline

The Week 2 pipeline is:

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
Ranking
        ↓
data/ranked_materials.csv