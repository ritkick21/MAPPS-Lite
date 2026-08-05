"""
MAPPS-Lite Run Summary

Creates a reproducibility record after a MAPPS-Lite run.

The summary records:
- execution mode
- dataset sizes
- screening results
- active search settings
- ranking weights
- chemistry screening settings
- output files

The report is saved to:
    reports/run_summary.md
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from config import (
        REQUIRED_ELEMENTS,
        MIN_NUM_ELEMENTS,
        MAX_NUM_ELEMENTS,
        SEARCH_MIN_HULL_ENERGY,
        SEARCH_MAX_HULL_ENERGY,
        CANDIDATE_MAX_HULL_ENERGY,
        CATHODE_METALS,
        BATTERY_RELEVANT_METALS,
        FLAGGED_ELEMENTS,
        HULL_WEIGHT,
        FORMATION_ENERGY_WEIGHT,
        STABILITY_WEIGHT,
        STATUS_PROMISING,
        STATUS_POSSIBLE,
        STATUS_REVIEW,
        TOP_CANDIDATE_COUNT,
    )
except ImportError:
    from .config import (
        REQUIRED_ELEMENTS,
        MIN_NUM_ELEMENTS,
        MAX_NUM_ELEMENTS,
        SEARCH_MIN_HULL_ENERGY,
        SEARCH_MAX_HULL_ENERGY,
        CANDIDATE_MAX_HULL_ENERGY,
        CATHODE_METALS,
        BATTERY_RELEVANT_METALS,
        FLAGGED_ELEMENTS,
        HULL_WEIGHT,
        FORMATION_ENERGY_WEIGHT,
        STABILITY_WEIGHT,
        STATUS_PROMISING,
        STATUS_POSSIBLE,
        STATUS_REVIEW,
        TOP_CANDIDATE_COUNT,
    )


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MATERIALS_FILE = (
    PROJECT_ROOT
    / "data"
    / "materials.csv"
)

RANKED_FILE = (
    PROJECT_ROOT
    / "data"
    / "ranked_materials.csv"
)

SCREENED_FILE = (
    PROJECT_ROOT
    / "data"
    / "screened_materials.csv"
)

TOP_REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "top_materials_report.md"
)

RUN_SUMMARY_FILE = (
    PROJECT_ROOT
    / "reports"
    / "run_summary.md"
)


# ---------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------

def load_csv_if_exists(
    file_path
):
    """
    Load a CSV file if it exists.

    Returns None if the file does not exist.
    """

    if not file_path.exists():
        return None

    return pd.read_csv(
        file_path
    )


def get_dataset_counts():
    """
    Determine the number of records currently stored
    at each major MAPPS-Lite pipeline stage.
    """

    materials = load_csv_if_exists(
        MATERIALS_FILE
    )

    ranked = load_csv_if_exists(
        RANKED_FILE
    )

    screened = load_csv_if_exists(
        SCREENED_FILE
    )

    return {
        "materials":
            0
            if materials is None
            else len(materials),

        "ranked":
            0
            if ranked is None
            else len(ranked),

        "screened":
            0
            if screened is None
            else len(screened),
    }


# ---------------------------------------------------------
# Screening counts
# ---------------------------------------------------------

def get_screening_counts():
    """
    Count PROMISING, POSSIBLE, and REVIEW classifications
    in screened_materials.csv.
    """

    screened = load_csv_if_exists(
        SCREENED_FILE
    )

    if (
        screened is None
        or "screening_status"
        not in screened.columns
    ):

        return {
            STATUS_PROMISING: 0,
            STATUS_POSSIBLE: 0,
            STATUS_REVIEW: 0,
        }

    counts = (
        screened[
            "screening_status"
        ]
        .value_counts()
        .to_dict()
    )

    return {
        STATUS_PROMISING:
            counts.get(
                STATUS_PROMISING,
                0,
            ),

        STATUS_POSSIBLE:
            counts.get(
                STATUS_POSSIBLE,
                0,
            ),

        STATUS_REVIEW:
            counts.get(
                STATUS_REVIEW,
                0,
            ),
    }


# ---------------------------------------------------------
# Flagged element counts
# ---------------------------------------------------------

def get_flagged_element_counts():
    """
    Count how many screened materials contain each
    configured flagged element.
    """

    counts = {
        element: 0
        for element
        in FLAGGED_ELEMENTS
    }

    screened = load_csv_if_exists(
        SCREENED_FILE
    )

    if (
        screened is None
        or "flagged_elements"
        not in screened.columns
    ):

        return counts

    for value in (
        screened[
            "flagged_elements"
        ]
        .fillna("")
    ):

        elements = {
            element.strip()
            for element
            in str(value).split(",")
            if element.strip()
        }

        for element in elements:

            if element in counts:

                counts[
                    element
                ] += 1

    return counts


# ---------------------------------------------------------
# Build run summary
# ---------------------------------------------------------

def build_run_summary(
    mode
):
    """
    Build a Markdown record describing the most recent
    MAPPS-Lite execution and active configuration.
    """

    timestamp = (
        datetime.now()
        .astimezone()
        .strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )
    )

    dataset_counts = (
        get_dataset_counts()
    )

    screening_counts = (
        get_screening_counts()
    )

    flagged_counts = (
        get_flagged_element_counts()
    )

    report = []

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    report.append(
        "# MAPPS-Lite Run Summary"
    )

    report.append("")

    report.append(
        f"**Run Time:** {timestamp}"
    )

    report.append("")

    report.append(
        f"**Pipeline Mode:** {mode}"
    )

    report.append("")

    report.append(
        "This file records the configuration and outputs "
        "associated with the most recent MAPPS-Lite run."
    )

    report.append("")

    report.append("---")

    report.append("")

    # -----------------------------------------------------
    # Dataset counts
    # -----------------------------------------------------

    report.append(
        "## Dataset Counts"
    )

    report.append("")

    report.append(
        "- Cleaned cathode candidates: "
        f"{dataset_counts['materials']}"
    )

    report.append(
        "- Ranked materials: "
        f"{dataset_counts['ranked']}"
    )

    report.append(
        "- Screened materials: "
        f"{dataset_counts['screened']}"
    )

    report.append("")

    # -----------------------------------------------------
    # Screening results
    # -----------------------------------------------------

    report.append(
        "## Screening Results"
    )

    report.append("")

    report.append(
        f"- {STATUS_PROMISING}: "
        f"{screening_counts[STATUS_PROMISING]}"
    )

    report.append(
        f"- {STATUS_POSSIBLE}: "
        f"{screening_counts[STATUS_POSSIBLE]}"
    )

    report.append(
        f"- {STATUS_REVIEW}: "
        f"{screening_counts[STATUS_REVIEW]}"
    )

    report.append("")

    # -----------------------------------------------------
    # Search configuration
    # -----------------------------------------------------

    report.append(
        "## Search Configuration"
    )

    report.append("")

    report.append(
        "- Required elements: "
        + ", ".join(
            REQUIRED_ELEMENTS
        )
    )

    report.append(
        "- Number of elements allowed: "
        f"{MIN_NUM_ELEMENTS} to "
        f"{MAX_NUM_ELEMENTS}"
    )

    report.append(
        "- Materials Project energy-above-hull "
        "search range: "
        f"{SEARCH_MIN_HULL_ENERGY:.3f} to "
        f"{SEARCH_MAX_HULL_ENERGY:.3f} eV/atom"
    )

    report.append(
        "- Candidate energy-above-hull maximum: "
        f"{CANDIDATE_MAX_HULL_ENERGY:.3f} eV/atom"
    )

    report.append(
        "- Initial cathode metals: "
        + ", ".join(
            sorted(
                CATHODE_METALS
            )
        )
    )

    report.append("")

    # -----------------------------------------------------
    # Ranking model
    # -----------------------------------------------------

    report.append(
        "## Ranking Model"
    )

    report.append("")

    report.append(
        "- Energy above hull weight: "
        f"{HULL_WEIGHT * 100:.1f}%"
    )

    report.append(
        "- Formation energy weight: "
        f"{FORMATION_ENERGY_WEIGHT * 100:.1f}%"
    )

    report.append(
        "- Stability flag weight: "
        f"{STABILITY_WEIGHT * 100:.1f}%"
    )

    report.append("")

    # -----------------------------------------------------
    # Chemistry screening
    # -----------------------------------------------------

    report.append(
        "## Chemistry Screening"
    )

    report.append("")

    report.append(
        "- Battery-relevant metals: "
        + ", ".join(
            sorted(
                BATTERY_RELEVANT_METALS
            )
        )
    )

    report.append("")

    report.append(
        "### Flagged Elements"
    )

    report.append("")

    for element, reason in (
        FLAGGED_ELEMENTS.items()
    ):

        report.append(
            f"- {element}: {reason}"
        )

    report.append("")

    report.append(
        "### Flagged Element Counts"
    )

    report.append("")

    for element, count in (
        flagged_counts.items()
    ):

        report.append(
            f"- {element}: {count}"
        )

    report.append("")

    # -----------------------------------------------------
    # Report settings
    # -----------------------------------------------------

    report.append(
        "## Report Settings"
    )

    report.append("")

    report.append(
        "- Number of top PROMISING candidates "
        "included in report: "
        f"{TOP_CANDIDATE_COUNT}"
    )

    report.append("")

    # -----------------------------------------------------
    # Generated files
    # -----------------------------------------------------

    report.append(
        "## Output Files"
    )

    report.append("")

    report.append(
        "- `data/materials.csv`"
    )

    report.append(
        "- `data/ranked_materials.csv`"
    )

    report.append(
        "- `data/screened_materials.csv`"
    )

    report.append(
        "- `reports/top_materials_report.md`"
    )

    report.append(
        "- `reports/run_summary.md`"
    )

    report.append("")

    report.append("---")

    report.append("")

    report.append(
        "MAPPS-Lite classifications are preliminary "
        "screening results and should not be interpreted "
        "as final electrochemical validation."
    )

    return "\n".join(
        report
    )


# ---------------------------------------------------------
# Save run summary
# ---------------------------------------------------------

def save_run_summary(
    mode
):
    """
    Generate and save reports/run_summary.md.
    """

    report = build_run_summary(
        mode
    )

    RUN_SUMMARY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RUN_SUMMARY_FILE.write_text(
        report,
        encoding="utf-8",
    )

    print(
        "Saved run summary to:"
    )

    print(
        RUN_SUMMARY_FILE
    )

    return RUN_SUMMARY_FILE