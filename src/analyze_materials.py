"""
MAPPS-Lite Material Analysis

Loads ranked materials, performs chemistry screening,
assigns MAPPS-Lite candidate statuses, saves the screened
dataset, and generates the final Markdown report.

Scientific settings are imported from config.py so the
analysis stage stays synchronized with the rest of the
pipeline.
"""

from pathlib import Path
import re

import pandas as pd

try:
    from config import (
        BATTERY_RELEVANT_METALS,
        FLAGGED_ELEMENTS,
        STATUS_PROMISING,
        STATUS_POSSIBLE,
        STATUS_REVIEW,
        TOP_CANDIDATE_COUNT,
        get_ranking_model_summary,
    )
except ImportError:
    from .config import (
        BATTERY_RELEVANT_METALS,
        FLAGGED_ELEMENTS,
        STATUS_PROMISING,
        STATUS_POSSIBLE,
        STATUS_REVIEW,
        TOP_CANDIDATE_COUNT,
        get_ranking_model_summary,
    )


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "ranked_materials.csv"
)

SCREENED_OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "screened_materials.csv"
)

REPORT_OUTPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "top_materials_report.md"
)


# ---------------------------------------------------------
# Required dataset columns
# ---------------------------------------------------------

REQUIRED_COLUMNS = {
    "material_id",
    "formula",
    "energy_above_hull",
    "formation_energy_per_atom",
    "is_stable",
}


# ---------------------------------------------------------
# Load ranked dataset
# ---------------------------------------------------------

def load_ranked_materials():
    """
    Load the ranked materials dataset.

    Returns:
        pandas.DataFrame:
            Ranked material dataset.

    Raises:
        FileNotFoundError:
            If ranked_materials.csv does not exist.

        ValueError:
            If required columns are missing.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "Could not find ranked materials file:\n"
            f"{INPUT_FILE}\n\n"
            "Run one of these commands first:\n"
            "python src/rank_materials.py\n"
            "python src/main.py --skip-search"
        )

    materials = pd.read_csv(
        INPUT_FILE
    )

    missing_columns = (
        REQUIRED_COLUMNS
        - set(materials.columns)
    )

    if missing_columns:

        missing_text = ", ".join(
            sorted(missing_columns)
        )

        raise ValueError(
            "Cannot analyze materials because required "
            f"column(s) are missing: {missing_text}"
        )

    if materials.empty:

        raise ValueError(
            "The ranked materials dataset is empty."
        )

    print(
        f"Loaded {len(materials)} ranked materials."
    )

    return materials


# ---------------------------------------------------------
# Extract elements from formula
# ---------------------------------------------------------

def extract_elements(
    formula
):
    """
    Extract chemical element symbols from a formula.

    Example:
        Li2Ti3MnO8

    Returns:
        {'Li', 'Ti', 'Mn', 'O'}
    """

    elements = re.findall(
        r"[A-Z][a-z]?",
        str(formula),
    )

    return set(
        elements
    )


# ---------------------------------------------------------
# Analyze material composition
# ---------------------------------------------------------

def analyze_composition(
    formula
):
    """
    Analyze the chemical composition of a material.

    Returns:
        dict:
            Composition information used by the
            MAPPS-Lite screening stage.
    """

    elements = extract_elements(
        formula
    )

    contains_lithium = (
        "Li" in elements
    )

    contains_oxygen = (
        "O" in elements
    )

    relevant_metals = sorted(
        elements.intersection(
            BATTERY_RELEVANT_METALS
        )
    )

    flagged_elements = sorted(
        elements.intersection(
            FLAGGED_ELEMENTS.keys()
        )
    )

    return {
        "elements":
            elements,

        "contains_lithium":
            contains_lithium,

        "contains_oxygen":
            contains_oxygen,

        "relevant_metals":
            relevant_metals,

        "flagged_elements":
            flagged_elements,
    }


# ---------------------------------------------------------
# Stability conversion
# ---------------------------------------------------------

def is_material_stable(
    value
):
    """
    Convert the Materials Project stability field into a
    reliable Boolean value.

    Supports:
    - True / False
    - "True" / "False"
    """

    if isinstance(
        value,
        bool,
    ):
        return value

    return (
        str(value)
        .strip()
        .lower()
        == "true"
    )


# ---------------------------------------------------------
# Ranking score helper
# ---------------------------------------------------------

def get_ranking_score(
    material
):
    """
    Return the MAPPS-Lite ranking score for a material.

    Current datasets use:
        score

    Older MAPPS-Lite datasets may use:
        overall_score
    """

    if "score" in material.index:

        return material[
            "score"
        ]

    if "overall_score" in material.index:

        return material[
            "overall_score"
        ]

    raise ValueError(
        "Material does not contain a ranking score. "
        "Expected 'score' or 'overall_score'."
    )


# ---------------------------------------------------------
# Explain thermodynamic ranking
# ---------------------------------------------------------

def explain_material(
    material
):
    """
    Generate readable thermodynamic explanations for
    a ranked material.
    """

    explanations = []

    energy_above_hull = material[
        "energy_above_hull"
    ]

    formation_energy = material[
        "formation_energy_per_atom"
    ]

    stable = is_material_stable(
        material[
            "is_stable"
        ]
    )

    if energy_above_hull == 0:

        explanations.append(
            "It lies on the convex hull "
            "(energy above hull = 0 eV/atom), "
            "indicating strong thermodynamic stability."
        )

    elif energy_above_hull < 0.05:

        explanations.append(
            "It has a low energy above hull, indicating "
            "that it is relatively close to "
            "thermodynamic stability."
        )

    else:

        explanations.append(
            "Its energy above hull is higher than the "
            "most stable candidates, reducing its "
            "stability contribution."
        )

    if formation_energy < 0:

        explanations.append(
            "Its negative formation energy contributed "
            "positively under the current MAPPS-Lite "
            "ranking model."
        )

    else:

        explanations.append(
            "Its formation energy provided a weaker "
            "contribution to the current ranking score."
        )

    if stable:

        explanations.append(
            "Materials Project identifies the material "
            "as stable."
        )

    else:

        explanations.append(
            "Materials Project does not currently "
            "classify the material as stable."
        )

    return explanations


# ---------------------------------------------------------
# Composition assessment
# ---------------------------------------------------------

def build_composition_assessment(
    composition
):
    """
    Build readable chemistry-screening statements.
    """

    assessment = []

    if composition[
        "contains_lithium"
    ]:

        assessment.append(
            "[OK] Contains lithium."
        )

    else:

        assessment.append(
            "[REVIEW] Does not contain lithium."
        )

    if composition[
        "contains_oxygen"
    ]:

        assessment.append(
            "[OK] Contains oxygen."
        )

    else:

        assessment.append(
            "[REVIEW] Does not contain oxygen."
        )

    if composition[
        "relevant_metals"
    ]:

        metals = ", ".join(
            composition[
                "relevant_metals"
            ]
        )

        assessment.append(
            "[OK] Contains battery-relevant "
            f"transition metal(s): {metals}."
        )

    else:

        assessment.append(
            "[REVIEW] No transition metals from "
            "the current MAPPS-Lite screening list "
            "were detected."
        )

    if composition[
        "flagged_elements"
    ]:

        for element in composition[
            "flagged_elements"
        ]:

            reason = FLAGGED_ELEMENTS[
                element
            ]

            assessment.append(
                "[REVIEW] Flagged for review: "
                f"{element} ({reason})."
            )

    else:

        assessment.append(
            "[OK] No elements from the current "
            "MAPPS-Lite review list were detected."
        )

    return assessment


# ---------------------------------------------------------
# Candidate status
# ---------------------------------------------------------

def determine_candidate_status(
    material,
    composition,
):
    """
    Assign a preliminary MAPPS-Lite status.

    PROMISING:
        Stable convex-hull material that passes the
        configured composition screening.

    POSSIBLE:
        Passes composition screening but does not meet
        the strongest thermodynamic criteria.

    REVIEW:
        Contains a flagged element or lacks a configured
        battery-relevant transition metal.

    This is not a final electrochemical judgment.
    """

    if composition[
        "flagged_elements"
    ]:

        return (
            STATUS_REVIEW,
            "Thermodynamically promising, but the "
            "composition contains one or more elements "
            "flagged for additional review.",
        )

    if not composition[
        "relevant_metals"
    ]:

        return (
            STATUS_REVIEW,
            "Thermodynamically promising, but no "
            "transition metal from the current "
            "battery-relevant screening list "
            "was identified.",
        )

    stable = is_material_stable(
        material[
            "is_stable"
        ]
    )

    if (
        material[
            "energy_above_hull"
        ] == 0
        and stable
    ):

        return (
            STATUS_PROMISING,
            "Strong thermodynamic candidate based on "
            "the current MAPPS-Lite screening criteria. "
            "Further electrochemical evaluation "
            "is required.",
        )

    return (
        STATUS_POSSIBLE,
        "Candidate passes basic composition screening "
        "but requires additional stability and "
        "electrochemical evaluation.",
    )


# ---------------------------------------------------------
# Screen every material
# ---------------------------------------------------------

def screen_all_materials(
    materials
):
    """
    Apply chemistry screening to every ranked material.

    Adds:
    - battery_relevant_metals
    - flagged_elements
    - screening_status
    """

    screened_materials = (
        materials.copy()
    )

    relevant_metals_column = []
    flagged_elements_column = []
    status_column = []

    for _, material in (
        screened_materials.iterrows()
    ):

        composition = (
            analyze_composition(
                material[
                    "formula"
                ]
            )
        )

        relevant_metals = ", ".join(
            composition[
                "relevant_metals"
            ]
        )

        flagged_elements = ", ".join(
            composition[
                "flagged_elements"
            ]
        )

        status, _ = (
            determine_candidate_status(
                material,
                composition,
            )
        )

        relevant_metals_column.append(
            relevant_metals
        )

        flagged_elements_column.append(
            flagged_elements
        )

        status_column.append(
            status
        )

    screened_materials[
        "battery_relevant_metals"
    ] = relevant_metals_column

    screened_materials[
        "flagged_elements"
    ] = flagged_elements_column

    screened_materials[
        "screening_status"
    ] = status_column

    return screened_materials


# ---------------------------------------------------------
# Save screened dataset
# ---------------------------------------------------------

def save_screened_materials(
    screened_materials
):
    """
    Save the complete screened dataset.
    """

    SCREENED_OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    screened_materials.to_csv(
        SCREENED_OUTPUT_FILE,
        index=False,
    )

    print(
        f"Saved {len(screened_materials)} "
        "screened materials to:"
    )

    print(
        SCREENED_OUTPUT_FILE
    )

    return screened_materials


# ---------------------------------------------------------
# Screening statistics
# ---------------------------------------------------------

def generate_screening_summary(
    screened_materials
):
    """
    Generate statistics for the complete screened
    materials dataset.
    """

    total_materials = len(
        screened_materials
    )

    status_counts = (
        screened_materials[
            "screening_status"
        ]
        .value_counts()
        .to_dict()
    )

    promising_count = (
        status_counts.get(
            STATUS_PROMISING,
            0,
        )
    )

    possible_count = (
        status_counts.get(
            STATUS_POSSIBLE,
            0,
        )
    )

    review_count = (
        status_counts.get(
            STATUS_REVIEW,
            0,
        )
    )

    flagged_counts = {
        element: 0
        for element
        in FLAGGED_ELEMENTS
    }

    for flagged_value in (
        screened_materials[
            "flagged_elements"
        ]
        .fillna("")
    ):

        if not flagged_value:

            continue

        elements = [
            element.strip()
            for element
            in flagged_value.split(",")
        ]

        for element in elements:

            if element in flagged_counts:

                flagged_counts[
                    element
                ] += 1

    return {
        "total_materials":
            total_materials,

        "promising_count":
            promising_count,

        "possible_count":
            possible_count,

        "review_count":
            review_count,

        "flagged_counts":
            flagged_counts,
    }


# ---------------------------------------------------------
# Print screening summary
# ---------------------------------------------------------

def print_screening_summary(
    summary
):
    """
    Display screening statistics in the terminal.
    """

    print()
    print(
        "Screening summary:"
    )
    print()

    print(
        f"{STATUS_PROMISING}: "
        f"{summary['promising_count']}"
    )

    print(
        f"{STATUS_POSSIBLE}: "
        f"{summary['possible_count']}"
    )

    print(
        f"{STATUS_REVIEW}: "
        f"{summary['review_count']}"
    )

    print()


# ---------------------------------------------------------
# Select top candidates
# ---------------------------------------------------------

def select_top_promising_materials(
    screened_materials,
    top_n=TOP_CANDIDATE_COUNT,
):
    """
    Select the highest-ranked PROMISING candidates.
    """

    promising_materials = (
        screened_materials[
            screened_materials[
                "screening_status"
            ]
            == STATUS_PROMISING
        ]
    )

    if "rank" in promising_materials.columns:

        top_materials = (
            promising_materials
            .sort_values(
                by="rank",
                ascending=True,
            )
            .head(
                top_n
            )
        )

    elif "score" in promising_materials.columns:

        top_materials = (
            promising_materials
            .sort_values(
                by="score",
                ascending=False,
            )
            .head(
                top_n
            )
        )

    elif (
        "overall_score"
        in promising_materials.columns
    ):

        top_materials = (
            promising_materials
            .sort_values(
                by="overall_score",
                ascending=False,
            )
            .head(
                top_n
            )
        )

    else:

        raise ValueError(
            "The dataset must contain 'rank', "
            "'score', or 'overall_score'."
        )

    print(
        f"Found {len(promising_materials)} "
        f"{STATUS_PROMISING} materials."
    )

    print(
        f"Selecting top "
        f"{min(top_n, len(promising_materials))} "
        "for the report."
    )

    return top_materials


# ---------------------------------------------------------
# Build Markdown report
# ---------------------------------------------------------

def build_report(
    top_materials,
    summary,
):
    """
    Build the complete Markdown screening report.
    """

    report = []

    ranking_model = (
        get_ranking_model_summary()
    )

    hull_percent = (
        ranking_model[
            "energy_above_hull_percent"
        ]
    )

    formation_percent = (
        ranking_model[
            "formation_energy_percent"
        ]
    )

    stability_percent = (
        ranking_model[
            "stability_flag_percent"
        ]
    )

    # -----------------------------------------------------
    # Report header
    # -----------------------------------------------------

    report.append(
        "# MAPPS-Lite Materials Screening Report"
    )

    report.append("")

    report.append(
        "This report summarizes the complete "
        "MAPPS-Lite screening process and presents "
        "the highest-ranked PROMISING cathode candidates."
    )

    report.append("")

    # -----------------------------------------------------
    # Screening summary
    # -----------------------------------------------------

    report.append(
        "## Screening Summary"
    )

    report.append("")

    report.append(
        "**Total Materials Screened:** "
        f"{summary['total_materials']}"
    )

    report.append("")

    report.append(
        f"- {STATUS_PROMISING}: "
        f"{summary['promising_count']}"
    )

    report.append(
        f"- {STATUS_POSSIBLE}: "
        f"{summary['possible_count']}"
    )

    report.append(
        f"- {STATUS_REVIEW}: "
        f"{summary['review_count']}"
    )

    report.append("")

    # -----------------------------------------------------
    # Flagged elements
    # -----------------------------------------------------

    report.append(
        "### Flagged Element Summary"
    )

    report.append("")

    any_flagged = False

    for element, count in (
        summary[
            "flagged_counts"
        ]
        .items()
    ):

        if count > 0:

            report.append(
                f"- {element}: "
                f"{count} material(s)"
            )

            any_flagged = True

    if not any_flagged:

        report.append(
            "- No flagged elements "
            "were detected."
        )

    report.append("")

    # -----------------------------------------------------
    # Ranking model
    # -----------------------------------------------------

    report.append(
        "## Current Ranking Model"
    )

    report.append("")

    report.append(
        "The thermodynamic ranking model uses:"
    )

    report.append("")

    report.append(
        "- Energy above hull: "
        f"{hull_percent:.0f}%"
    )

    report.append(
        "- Formation energy per atom: "
        f"{formation_percent:.0f}%"
    )

    report.append(
        "- Materials Project stability flag: "
        f"{stability_percent:.0f}%"
    )

    report.append("")

    report.append(
        "These values are loaded directly from "
        "`src/config.py`."
    )

    report.append("")

    report.append(
        "The secondary screening layer evaluates "
        "chemical composition, identifies "
        "battery-relevant transition metals, and "
        "flags selected elements for additional review."
    )

    report.append("")

    report.append("---")

    report.append("")

    report.append(
        f"# Top {TOP_CANDIDATE_COUNT} "
        "Promising Candidates"
    )

    report.append("")

    # -----------------------------------------------------
    # Individual material reports
    # -----------------------------------------------------

    for position, (_, material) in enumerate(
        top_materials.iterrows(),
        start=1,
    ):

        formula = material[
            "formula"
        ]

        material_id = material[
            "material_id"
        ]

        ranking_score = (
            get_ranking_score(
                material
            )
        )

        energy_above_hull = (
            material[
                "energy_above_hull"
            ]
        )

        formation_energy = (
            material[
                "formation_energy_per_atom"
            ]
        )

        stable = (
            is_material_stable(
                material[
                    "is_stable"
                ]
            )
        )

        composition = (
            analyze_composition(
                formula
            )
        )

        explanations = (
            explain_material(
                material
            )
        )

        composition_assessment = (
            build_composition_assessment(
                composition
            )
        )

        status, status_explanation = (
            determine_candidate_status(
                material,
                composition,
            )
        )

        # -------------------------------------------------
        # Material header
        # -------------------------------------------------

        report.append(
            f"## {position}. {formula}"
        )

        report.append("")

        report.append(
            "**Materials Project ID:** "
            f"{material_id}"
        )

        report.append("")

        if "rank" in material.index:

            report.append(
                "**Overall Rank:** "
                f"{int(material['rank'])}"
            )

            report.append("")

        report.append(
            "**Ranking Score:** "
            f"{ranking_score:.4f}"
        )

        report.append("")

        report.append(
            "**MAPPS-Lite Status:** "
            f"{status}"
        )

        report.append("")

        # -------------------------------------------------
        # Thermodynamic properties
        # -------------------------------------------------

        report.append(
            "### Thermodynamic Properties"
        )

        report.append("")

        report.append(
            "**Energy Above Hull:** "
            f"{energy_above_hull:.4f} eV/atom"
        )

        report.append("")

        report.append(
            "**Formation Energy:** "
            f"{formation_energy:.4f} eV/atom"
        )

        report.append("")

        report.append(
            f"**Stable:** {stable}"
        )

        report.append("")

        if (
            "density" in material.index
            and pd.notna(
                material[
                    "density"
                ]
            )
        ):

            report.append(
                "**Density:** "
                f"{material['density']:.4f} g/cm^3"
            )

            report.append("")

        if (
            "band_gap" in material.index
            and pd.notna(
                material[
                    "band_gap"
                ]
            )
        ):

            report.append(
                "**Band Gap:** "
                f"{material['band_gap']:.4f} eV"
            )

            report.append("")

        # -------------------------------------------------
        # Ranking explanation
        # -------------------------------------------------

        report.append(
            "### Why It Ranked Highly"
        )

        report.append("")

        for explanation in explanations:

            report.append(
                f"- {explanation}"
            )

        report.append("")

        # -------------------------------------------------
        # Composition screening
        # -------------------------------------------------

        report.append(
            "### Composition Assessment"
        )

        report.append("")

        for statement in (
            composition_assessment
        ):

            report.append(
                f"- {statement}"
            )

        report.append("")

        # -------------------------------------------------
        # Final assessment
        # -------------------------------------------------

        report.append(
            "### MAPPS-Lite Assessment"
        )

        report.append("")

        report.append(
            status_explanation
        )

        report.append("")

        report.append("---")

        report.append("")

    return "\n".join(
        report
    )


# ---------------------------------------------------------
# Save report
# ---------------------------------------------------------

def save_report(
    report
):
    """
    Save the Markdown analysis report.
    """

    REPORT_OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_OUTPUT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    print(
        "Saved analysis report to:"
    )

    print(
        REPORT_OUTPUT_FILE
    )


# ---------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------

def run_analysis_pipeline():
    """
    Run the complete MAPPS-Lite screening and reporting
    pipeline.

    Workflow:

    1. Load ranked materials.
    2. Screen every composition.
    3. Assign PROMISING / POSSIBLE / REVIEW.
    4. Save screened_materials.csv.
    5. Generate screening statistics.
    6. Select the configured number of top candidates.
    7. Build the Markdown report.
    8. Save top_materials_report.md.

    Returns:
        pandas.DataFrame:
            Complete screened materials dataset.
    """

    print(
        "Loading ranked materials..."
    )

    materials = (
        load_ranked_materials()
    )

    print(
        "Screening material compositions..."
    )

    screened_materials = (
        screen_all_materials(
            materials
        )
    )

    save_screened_materials(
        screened_materials
    )

    summary = (
        generate_screening_summary(
            screened_materials
        )
    )

    print_screening_summary(
        summary
    )

    top_materials = (
        select_top_promising_materials(
            screened_materials,
            top_n=TOP_CANDIDATE_COUNT,
        )
    )

    report = (
        build_report(
            top_materials,
            summary,
        )
    )

    save_report(
        report
    )

    return screened_materials


# ---------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------

def main():
    """
    Run the screening stage independently.
    """

    run_analysis_pipeline()


if __name__ == "__main__":
    main()