from pathlib import Path
import re

import pandas as pd


# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "ranked_materials.csv"

SCREENED_OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "screened_materials.csv"
)

REPORT_OUTPUT_FILE = (
    PROJECT_ROOT / "reports" / "top_materials_report.md"
)


# ---------------------------------------------------------
# Chemistry screening settings
# ---------------------------------------------------------

BATTERY_RELEVANT_METALS = {
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
}

FLAGGED_ELEMENTS = {
    "Pb": "contains lead",
    "Hg": "contains mercury",
    "Cd": "contains cadmium",
    "U": "contains uranium",
}


# ---------------------------------------------------------
# Load ranked dataset
# ---------------------------------------------------------

def load_ranked_materials():
    """Load the ranked materials CSV file."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find ranked materials file: {INPUT_FILE}"
        )

    materials = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(materials)} ranked materials.")

    return materials


# ---------------------------------------------------------
# Extract elements from formula
# ---------------------------------------------------------

def extract_elements(formula):
    """
    Extract element symbols from a chemical formula.

    Example:
        Li2Ti3MnO8

    Returns:
        {'Li', 'Ti', 'Mn', 'O'}
    """

    elements = re.findall(
        r"[A-Z][a-z]?",
        str(formula)
    )

    return set(elements)


# ---------------------------------------------------------
# Analyze material composition
# ---------------------------------------------------------

def analyze_composition(formula):
    """Analyze the chemical composition of a material."""

    elements = extract_elements(formula)

    contains_lithium = "Li" in elements
    contains_oxygen = "O" in elements

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
        "elements": elements,
        "contains_lithium": contains_lithium,
        "contains_oxygen": contains_oxygen,
        "relevant_metals": relevant_metals,
        "flagged_elements": flagged_elements,
    }


# ---------------------------------------------------------
# Explain thermodynamic ranking
# ---------------------------------------------------------

def explain_material(material):
    """Generate thermodynamic explanations for a material."""

    explanations = []

    energy_above_hull = material[
        "energy_above_hull"
    ]

    formation_energy = material[
        "formation_energy_per_atom"
    ]

    is_stable = material[
        "is_stable"
    ]

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

    if is_stable:

        explanations.append(
            "Materials Project identifies the material "
            "as stable."
        )

    else:

        explanations.append(
            "Materials Project does not currently classify "
            "the material as stable."
        )

    return explanations


# ---------------------------------------------------------
# Generate composition assessment
# ---------------------------------------------------------

def build_composition_assessment(composition):
    """Create readable composition screening statements."""

    assessment = []

    if composition["contains_lithium"]:

        assessment.append(
            "✓ Contains lithium."
        )

    else:

        assessment.append(
            "⚠ Does not contain lithium."
        )

    if composition["contains_oxygen"]:

        assessment.append(
            "✓ Contains oxygen."
        )

    else:

        assessment.append(
            "⚠ Does not contain oxygen."
        )

    if composition["relevant_metals"]:

        metals = ", ".join(
            composition["relevant_metals"]
        )

        assessment.append(
            f"✓ Contains battery-relevant "
            f"transition metal(s): {metals}."
        )

    else:

        assessment.append(
            "⚠ No transition metals from the current "
            "MAPPS-Lite screening list were detected."
        )

    if composition["flagged_elements"]:

        for element in composition[
            "flagged_elements"
        ]:

            reason = FLAGGED_ELEMENTS[
                element
            ]

            assessment.append(
                f"⚠ Flagged for review: "
                f"{element} ({reason})."
            )

    else:

        assessment.append(
            "✓ No elements from the current "
            "MAPPS-Lite review list were detected."
        )

    return assessment


# ---------------------------------------------------------
# Assign candidate status
# ---------------------------------------------------------

def determine_candidate_status(
    material,
    composition
):
    """
    Assign a preliminary MAPPS-Lite candidate status.

    This is not a final electrochemical judgment.
    """

    if composition["flagged_elements"]:

        return (
            "REVIEW",
            "Thermodynamically promising, but the "
            "composition contains one or more elements "
            "flagged for additional review."
        )

    if not composition["relevant_metals"]:

        return (
            "REVIEW",
            "Thermodynamically promising, but no "
            "transition metal from the current "
            "battery-relevant screening list "
            "was identified."
        )

    if (
        material["energy_above_hull"] == 0
        and material["is_stable"]
    ):

        return (
            "PROMISING",
            "Strong thermodynamic candidate based on "
            "the current MAPPS-Lite screening criteria. "
            "Further electrochemical evaluation "
            "is required."
        )

    return (
        "POSSIBLE",
        "Candidate passes basic composition screening "
        "but requires additional stability and "
        "electrochemical evaluation."
    )


# ---------------------------------------------------------
# Screen every ranked material
# ---------------------------------------------------------

def screen_all_materials(materials):
    """
    Apply composition screening to every ranked material.

    Adds:
    - battery_relevant_metals
    - flagged_elements
    - screening_status
    """

    screened_materials = materials.copy()

    relevant_metals_column = []
    flagged_elements_column = []
    status_column = []

    for _, material in screened_materials.iterrows():

        formula = material[
            "formula"
        ]

        composition = analyze_composition(
            formula
        )

        relevant_metals = ", ".join(
            composition["relevant_metals"]
        )

        flagged_elements = ", ".join(
            composition["flagged_elements"]
        )

        status, _ = determine_candidate_status(
            material,
            composition
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
    """Save the screened materials dataset."""

    SCREENED_OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    screened_materials.to_csv(
        SCREENED_OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved {len(screened_materials)} "
        f"screened materials to:"
    )

    print(
        SCREENED_OUTPUT_FILE
    )


# ---------------------------------------------------------
# Generate screening statistics
# ---------------------------------------------------------

def generate_screening_summary(
    screened_materials
):
    """
    Generate summary statistics for the complete
    screened materials dataset.
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

    promising_count = status_counts.get(
        "PROMISING",
        0
    )

    possible_count = status_counts.get(
        "POSSIBLE",
        0
    )

    review_count = status_counts.get(
        "REVIEW",
        0
    )

    flagged_counts = {
        element: 0
        for element in FLAGGED_ELEMENTS
    }

    for flagged_value in screened_materials[
        "flagged_elements"
    ].fillna(""):

        if not flagged_value:
            continue

        elements = [
            element.strip()
            for element in flagged_value.split(",")
        ]

        for element in elements:

            if element in flagged_counts:

                flagged_counts[
                    element
                ] += 1

    return {
        "total_materials": total_materials,
        "promising_count": promising_count,
        "possible_count": possible_count,
        "review_count": review_count,
        "flagged_counts": flagged_counts,
    }


# ---------------------------------------------------------
# Select top promising candidates
# ---------------------------------------------------------

def select_top_promising_materials(
    screened_materials,
    top_n=10
):
    """
    Select the highest-ranked materials classified
    as PROMISING.
    """

    promising_materials = screened_materials[
        screened_materials[
            "screening_status"
        ] == "PROMISING"
    ]

    if "rank" in promising_materials.columns:

        top_materials = (
            promising_materials
            .sort_values("rank")
            .head(top_n)
        )

    elif "overall_score" in promising_materials.columns:

        top_materials = (
            promising_materials
            .sort_values(
                "overall_score",
                ascending=False
            )
            .head(top_n)
        )

    else:

        raise ValueError(
            "The dataset must contain either "
            "'rank' or 'overall_score'."
        )

    print(
        f"Found {len(promising_materials)} "
        f"PROMISING materials."
    )

    return top_materials


# ---------------------------------------------------------
# Build Markdown report
# ---------------------------------------------------------

def build_report(
    top_materials,
    summary
):
    """
    Create a Markdown report containing screening
    statistics and the top promising materials.
    """

    report = []

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
        f"**Total Materials Screened:** "
        f"{summary['total_materials']}"
    )

    report.append("")

    report.append(
        f"- PROMISING: "
        f"{summary['promising_count']}"
    )

    report.append(
        f"- POSSIBLE: "
        f"{summary['possible_count']}"
    )

    report.append(
        f"- REVIEW: "
        f"{summary['review_count']}"
    )

    report.append("")

    # -----------------------------------------------------
    # Flagged element summary
    # -----------------------------------------------------

    report.append(
        "### Flagged Element Summary"
    )

    report.append("")

    any_flagged = False

    for element, count in summary[
        "flagged_counts"
    ].items():

        if count > 0:

            report.append(
                f"- {element}: "
                f"{count} material(s)"
            )

            any_flagged = True

    if not any_flagged:

        report.append(
            "- No flagged elements were detected."
        )

    report.append("")

    # -----------------------------------------------------
    # Ranking model explanation
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
        "- Energy above hull: 55%"
    )

    report.append(
        "- Formation energy per atom: 35%"
    )

    report.append(
        "- Materials Project stability flag: 10%"
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
        "# Top 10 Promising Candidates"
    )

    report.append("")

    # -----------------------------------------------------
    # Top material reports
    # -----------------------------------------------------

    for position, (_, material) in enumerate(
        top_materials.iterrows(),
        start=1
    ):

        formula = material[
            "formula"
        ]

        material_id = material[
            "material_id"
        ]

        overall_score = material[
            "overall_score"
        ]

        energy_above_hull = material[
            "energy_above_hull"
        ]

        formation_energy = material[
            "formation_energy_per_atom"
        ]

        is_stable = material[
            "is_stable"
        ]

        composition = analyze_composition(
            formula
        )

        explanations = explain_material(
            material
        )

        composition_assessment = (
            build_composition_assessment(
                composition
            )
        )

        status, status_explanation = (
            determine_candidate_status(
                material,
                composition
            )
        )

        # Material header

        report.append(
            f"## {position}. {formula}"
        )

        report.append("")

        report.append(
            f"**Materials Project ID:** "
            f"{material_id}"
        )

        report.append("")

        report.append(
            f"**Overall Score:** "
            f"{overall_score:.4f}"
        )

        report.append("")

        report.append(
            f"**MAPPS-Lite Status:** "
            f"{status}"
        )

        report.append("")

        # Thermodynamic properties

        report.append(
            "### Thermodynamic Properties"
        )

        report.append("")

        report.append(
            f"**Energy Above Hull:** "
            f"{energy_above_hull:.4f} eV/atom"
        )

        report.append("")

        report.append(
            f"**Formation Energy:** "
            f"{formation_energy:.4f} eV/atom"
        )

        report.append("")

        report.append(
            f"**Stable:** {is_stable}"
        )

        report.append("")

        if (
            "density" in material.index
            and pd.notna(material["density"])
        ):

            report.append(
                f"**Density:** "
                f"{material['density']:.4f} g/cm³"
            )

            report.append("")

        # Ranking explanation

        report.append(
            "### Why It Ranked Highly"
        )

        report.append("")

        for explanation in explanations:

            report.append(
                f"- {explanation}"
            )

        report.append("")

        # Composition analysis

        report.append(
            "### Composition Assessment"
        )

        report.append("")

        for statement in composition_assessment:

            report.append(
                f"- {statement}"
            )

        report.append("")

        # Final assessment

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

    return "\n".join(report)


# ---------------------------------------------------------
# Save report
# ---------------------------------------------------------

def save_report(report):
    """Save the Markdown analysis report."""

    REPORT_OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORT_OUTPUT_FILE.write_text(
        report,
        encoding="utf-8"
    )

    print(
        "Saved analysis report to:"
    )

    print(
        REPORT_OUTPUT_FILE
    )


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():
    """Run the MAPPS-Lite screening and analysis pipeline."""

    # Step 1:
    # Load all ranked materials.
    materials = load_ranked_materials()

    # Step 2:
    # Screen every material.
    screened_materials = screen_all_materials(
        materials
    )

    # Step 3:
    # Save the complete screened dataset.
    save_screened_materials(
        screened_materials
    )

    # Step 4:
    # Generate statistics for the full dataset.
    summary = generate_screening_summary(
        screened_materials
    )

    # Step 5:
    # Select the top 10 PROMISING materials.
    top_materials = (
        select_top_promising_materials(
            screened_materials,
            top_n=10
        )
    )

    # Step 6:
    # Build the complete screening report.
    report = build_report(
        top_materials,
        summary
    )

    # Step 7:
    # Save the report.
    save_report(
        report
    )


if __name__ == "__main__":
    main()