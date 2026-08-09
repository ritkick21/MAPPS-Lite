from pathlib import Path

import pandas as pd
from pymatgen.core import Composition


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_transport_evaluation.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_resource_assessment.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week6_resource_assessment.md"
)


# =========================================================
# RESOURCE-RISK MODEL
# =========================================================

# These are MAPPS-Lite screening weights.
#
# They are informed by the 2025 U.S. critical-minerals
# classification and published USGS risk-tier analysis.
#
# They are NOT:
#
# - official USGS numeric scores
# - commodity prices
# - life-cycle assessment values
# - environmental toxicity scores
#
# Higher number = greater resource/supply concern.

ELEMENT_RESOURCE_DATA = {

    "Li": {
        "critical": True,
        "commodity": "Lithium",
        "tier": "MODERATE",
        "risk_weight": 45,
    },

    "V": {
        "critical": True,
        "commodity": "Vanadium",
        "tier": "ELEVATED",
        "risk_weight": 70,
    },

    "Mn": {
        "critical": True,
        "commodity": "Manganese",
        "tier": "ELEVATED",
        "risk_weight": 65,
    },

    "Cr": {
        "critical": True,
        "commodity": "Chromium",
        "tier": "ELEVATED",
        "risk_weight": 65,
    },

    "Si": {
        "critical": True,
        "commodity": "Silicon",
        "tier": "ELEVATED",
        "risk_weight": 60,
    },

    # The U.S. list names phosphate rather than
    # elemental phosphorus. We use phosphorus as
    # a composition-level proxy for phosphate demand.
    "P": {
        "critical": True,
        "commodity": "Phosphate proxy",
        "tier": "CRITICAL_LIST",
        "risk_weight": 50,
    },

    # The U.S. list names fluorspar rather than
    # elemental fluorine. F is therefore treated
    # as a formula-level proxy.
    "F": {
        "critical": True,
        "commodity": "Fluorspar proxy",
        "tier": "MODERATE",
        "risk_weight": 45,
    },

    "Fe": {
        "critical": False,
        "commodity": "Iron",
        "tier": "LOW",
        "risk_weight": 15,
    },

    "O": {
        "critical": False,
        "commodity": "Oxygen",
        "tier": "LOW",
        "risk_weight": 0,
    },

    "H": {
        "critical": False,
        "commodity": "Hydrogen",
        "tier": "LOW",
        "risk_weight": 0,
    },
}


DEFAULT_ELEMENT_DATA = {

    "critical": False,
    "commodity": "Unclassified",
    "tier": "UNKNOWN",
    "risk_weight": 50,
}


# =========================================================
# FORMULA PARSING
# =========================================================

def parse_formula(formula):
    """
    Parse chemical formula using pymatgen.

    Returns a dictionary such as:

    Li2VSiO5
        ->
    {
        "Li": 2,
        "V": 1,
        "Si": 1,
        "O": 5
    }
    """

    try:

        composition = Composition(
            str(formula)
        )

        return (
            composition.get_el_amt_dict(),
            "PARSED",
        )

    except Exception as exc:

        return (
            {},
            f"PARSE_ERROR: {exc}",
        )


# =========================================================
# PROCESS / CHEMISTRY FLAGS
# =========================================================

def process_flags(elements):
    """
    Add chemistry-review flags.

    These do NOT claim that a material is unsafe
    or unsynthesizable.
    """

    element_set = set(
        elements
    )

    flags = []

    if "F" in element_set:

        flags.append(
            "FLUORINE_BEARING_PROCESS_REVIEW"
        )

    if "Cr" in element_set:

        flags.append(
            "CHROMIUM_CHEMISTRY_REVIEW"
        )

    if "V" in element_set:

        flags.append(
            "VANADIUM_SUPPLY_REVIEW"
        )

    if "H" in element_set:

        flags.append(
            "HYDROGEN_CONTAINING_PHASE_REVIEW"
        )

    if not flags:

        return (
            "NO_SPECIAL_PROCESS_FLAG"
        )

    return ";".join(
        flags
    )


# =========================================================
# RESOURCE METRICS
# =========================================================

def resource_metrics(amounts):
    """
    Calculate resource-practicality metrics.

    O and H are excluded from the weighted resource
    average because oxygen-rich compounds would
    otherwise appear artificially low-risk.

    Example:

        LiVPO5

    Resource-relevant atoms:

        Li
        V
        P

    rather than counting all five oxygen atoms toward
    supply-chain practicality.
    """

    if not amounts:

        return {

            "resource_weighted_risk": None,

            "resource_practicality_score": None,

            "resource_profile_class": "UNKNOWN",

            "critical_resource_count": 0,

            "critical_resource_fraction": None,

            "highest_risk_element": "",

            "highest_risk_weight": None,

            "critical_commodities": "",

            "resource_risk_tiers": "",

            "resource_process_flags": "",
        }

    # -----------------------------------------------------
    # Exclude O and H from supply-risk weighting
    # -----------------------------------------------------

    resource_amounts = {

        element: amount

        for element, amount
        in amounts.items()

        if element not in {
            "O",
            "H",
        }
    }

    total_resource_atoms = sum(
        resource_amounts.values()
    )

    if total_resource_atoms <= 0:

        return {

            "resource_weighted_risk": 0.0,

            "resource_practicality_score": 100.0,

            "resource_profile_class":
                "MORE_FAVORABLE_RESOURCE_PROFILE",

            "critical_resource_count": 0,

            "critical_resource_fraction": 0.0,

            "highest_risk_element": "",

            "highest_risk_weight": 0,

            "critical_commodities": "",

            "resource_risk_tiers": "",

            "resource_process_flags":
                process_flags(
                    amounts.keys()
                ),
        }

    # -----------------------------------------------------
    # Calculate weighted resource risk
    # -----------------------------------------------------

    weighted_sum = 0.0

    critical_amount = 0.0

    critical_elements = []

    commodities = []

    tiers = []

    highest_element = ""

    highest_weight = -1

    for element, amount in (
        resource_amounts.items()
    ):

        data = (
            ELEMENT_RESOURCE_DATA.get(
                element,
                DEFAULT_ELEMENT_DATA,
            )
        )

        weight = float(
            data["risk_weight"]
        )

        weighted_sum += (
            amount
            * weight
        )

        # Highest-risk component
        if weight > highest_weight:

            highest_weight = weight

            highest_element = (
                element
            )

        # Critical-mineral burden
        if data["critical"]:

            critical_amount += (
                amount
            )

            critical_elements.append(
                element
            )

            commodities.append(
                data["commodity"]
            )

            tiers.append(
                f"{element}:"
                f"{data['tier']}"
            )

    weighted_risk = (
        weighted_sum
        / total_resource_atoms
    )

    critical_count = len(
        set(
            critical_elements
        )
    )

    critical_fraction = (
        critical_amount
        / total_resource_atoms
    )

    # -----------------------------------------------------
    # Critical-resource diversity penalty
    # -----------------------------------------------------
    #
    # Depending on several different critical resources
    # increases supply-chain complexity.
    #
    # We only penalize candidates once they depend on
    # more than two distinct critical commodities.
    # -----------------------------------------------------

    diversity_penalty = min(

        max(
            critical_count - 2,
            0,
        )
        * 4.0,

        12.0,
    )

    # -----------------------------------------------------
    # Small chemistry/process-review penalties
    # -----------------------------------------------------
    #
    # These are intentionally modest.
    #
    # They are NOT toxicity or actual manufacturing-
    # cost calculations.
    # -----------------------------------------------------

    element_set = set(
        amounts
    )

    process_penalty = 0.0

    if "F" in element_set:

        process_penalty += 5.0

    if "Cr" in element_set:

        process_penalty += 4.0

    if "V" in element_set:

        process_penalty += 2.0

    if "H" in element_set:

        process_penalty += 3.0

    # -----------------------------------------------------
    # Final resource practicality score
    # -----------------------------------------------------

    score = (

        100.0

        - weighted_risk

        - diversity_penalty

        - process_penalty
    )

    score = round(

        max(
            0.0,
            min(
                100.0,
                score,
            ),
        ),

        1,
    )

    # -----------------------------------------------------
    # Resource classification
    # -----------------------------------------------------

    if score >= 45:

        profile = (
            "MORE_FAVORABLE_RESOURCE_PROFILE"
        )

    elif score >= 35:

        profile = (
            "MODERATE_RESOURCE_PRESSURE"
        )

    else:

        profile = (
            "HIGHER_RESOURCE_PRESSURE"
        )

    return {

        "resource_weighted_risk":
            round(
                weighted_risk,
                1,
            ),

        "resource_practicality_score":
            score,

        "resource_profile_class":
            profile,

        "critical_resource_count":
            critical_count,

        "critical_resource_fraction":
            round(
                critical_fraction,
                4,
            ),

        "highest_risk_element":
            highest_element,

        "highest_risk_weight":
            highest_weight,

        "critical_commodities":
            ";".join(
                sorted(
                    set(
                        commodities
                    )
                )
            ),

        "resource_risk_tiers":
            ";".join(
                sorted(
                    set(
                        tiers
                    )
                )
            ),

        "resource_process_flags":
            process_flags(
                amounts.keys()
            ),
    }


# =========================================================
# REPORT
# =========================================================

def write_report(df):

    lines = []

    lines.append(
        "# MAPPS-Lite Week 6 "
        "Resource and Sustainability Assessment"
    )

    lines.append("")

    lines.append(
        "This stage compares candidate formulas "
        "using a transparent supply-risk and "
        "resource-practicality heuristic."
    )

    lines.append("")

    lines.append(
        "**Important:** the numeric weights are "
        "MAPPS-Lite screening weights informed by "
        "current U.S. critical-mineral classifications. "
        "They are not official USGS scores, commodity "
        "prices, or life-cycle-assessment results."
    )

    lines.append("")

    lines.append(
        "## Resource Profile Summary"
    )

    lines.append("")

    counts = (
        df[
            "resource_profile_class"
        ]
        .value_counts()
    )

    for label, count in (
        counts.items()
    ):

        lines.append(
            f"- {label}: {count}"
        )

    lines.append("")
    lines.append(
        "## Candidate Results"
    )
    lines.append("")

    ranked = (
        df.sort_values(
            "resource_practicality_score",
            ascending=False,
        )
    )

    for _, row in (
        ranked.iterrows()
    ):

        lines.append(
            f"### {row['material_id']} | "
            f"{row['week6_formula']}"
        )

        lines.append("")

        lines.append(
            "- Resource practicality score: "
            f"{row['resource_practicality_score']}"
        )

        lines.append(
            "- Resource profile: "
            f"{row['resource_profile_class']}"
        )

        lines.append(
            "- Weighted supply-risk proxy: "
            f"{row['resource_weighted_risk']}"
        )

        lines.append(
            "- Critical-resource count: "
            f"{row['critical_resource_count']}"
        )

        lines.append(
            "- Critical commodities: "
            f"{row['critical_commodities']}"
        )

        lines.append(
            "- Highest-risk element proxy: "
            f"{row['highest_risk_element']}"
        )

        lines.append(
            "- Process-review flags: "
            f"{row['resource_process_flags']}"
        )

        lines.append("")

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 76)
    print("MAPPS-LITE WEEK 6")

    print(
        "STAGE 6.5 - "
        "RESOURCE / SUPPLY-CHAIN ASSESSMENT"
    )

    print("=" * 76)

    # -----------------------------------------------------
    # Load Stage 6.4
    # -----------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "Could not find Stage 6.4 output:\n"
            f"{INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    print()
    print(
        f"Loaded {len(df)} candidates."
    )

    print(
        f"Input: {INPUT_FILE}"
    )

    required = [
        "material_id",
        "week6_formula",
    ]

    missing = [

        column

        for column
        in required

        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                missing
            )
        )

    records = []

    print()

    # =====================================================
    # ANALYZE EACH CANDIDATE
    # =====================================================

    for number, (_, row) in enumerate(
        df.iterrows(),
        start=1,
    ):

        formula = str(
            row[
                "week6_formula"
            ]
        ).strip()

        amounts, parse_status = (
            parse_formula(
                formula
            )
        )

        metrics = (
            resource_metrics(
                amounts
            )
        )

        record = (
            row.to_dict()
        )

        record[
            "resource_formula_parse_status"
        ] = parse_status

        record[
            "resource_elements"
        ] = ";".join(
            sorted(
                amounts.keys()
            )
        )

        record.update(
            metrics
        )

        records.append(
            record
        )

        print(
            f"[{number}/{len(df)}] "
            f"{row['material_id']} | "
            f"{formula} | "
            f"score="
            f"{metrics['resource_practicality_score']} | "
            f"{metrics['resource_profile_class']}"
        )

    # =====================================================
    # SAVE
    # =====================================================

    output_df = pd.DataFrame(
        records
    )

    output_df = (
        output_df.sort_values(
            "resource_practicality_score",
            ascending=False,
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    write_report(
        output_df
    )

    # =====================================================
    # TERMINAL SUMMARY
    # =====================================================

    print()
    print("=" * 76)

    print(
        "STAGE 6.5 COMPLETE"
    )

    print("=" * 76)

    print()
    print(
        "Resource profile classes:"
    )

    print(
        output_df[
            "resource_profile_class"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Candidate resource results:"
    )

    print()

    display_columns = [

        "material_id",

        "week6_formula",

        "resource_practicality_score",

        "resource_profile_class",

        "resource_weighted_risk",

        "critical_resource_count",

        "highest_risk_element",

        "critical_commodities",
    ]

    print(
        output_df[
            display_columns
        ]
        .to_string(
            index=False
        )
    )

    print()
    print(
        "Saved data:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "Saved report:"
    )

    print(
        REPORT_FILE
    )


if __name__ == "__main__":
    main()