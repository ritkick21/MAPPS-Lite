# MAPPS-Lite Run Summary

**Run Time:** 2026-08-05 16:05:31 Central Daylight Time

**Pipeline Mode:** ANALYSIS ONLY

This file records the configuration and outputs associated with the most recent MAPPS-Lite run.

---

## Dataset Counts

- Cleaned cathode candidates: 4717
- Ranked materials: 4717
- Screened materials: 4717

## Screening Results

- PROMISING: 179
- POSSIBLE: 4414
- REVIEW: 124

## Search Configuration

- Required elements: Li, O
- Number of elements allowed: 3 to 5
- Materials Project energy-above-hull search range: 0.000 to 0.100 eV/atom
- Candidate energy-above-hull maximum: 0.050 eV/atom
- Initial cathode metals: Co, Cr, Cu, Fe, Mn, Ni, Ti, V

## Ranking Model

- Energy above hull weight: 55.0%
- Formation energy weight: 35.0%
- Stability flag weight: 10.0%

## Chemistry Screening

- Battery-relevant metals: Co, Cr, Fe, Mn, Ni, Ti, V

### Flagged Elements

- Pb: contains lead
- Hg: contains mercury
- Cd: contains cadmium
- U: contains uranium

### Flagged Element Counts

- Pb: 3
- Hg: 0
- Cd: 0
- U: 1

## Report Settings

- Number of top PROMISING candidates included in report: 10

## Output Files

- `data/materials.csv`
- `data/ranked_materials.csv`
- `data/screened_materials.csv`
- `reports/top_materials_report.md`
- `reports/run_summary.md`

---

MAPPS-Lite classifications are preliminary screening results and should not be interpreted as final electrochemical validation.