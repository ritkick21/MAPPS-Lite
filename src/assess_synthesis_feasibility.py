import os
import re
from pathlib import Path

import pandas as pd
from mp_api.client import MPRester


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "week6_literature_validation.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "week6_synthesis_feasibility.csv"
REPORT_FILE = PROJECT_ROOT / "reports" / "week6_synthesis_feasibility.md"


# =========================================================
# GENERAL HELPERS
# =========================================================

def normalize_material_id(value):
    """
    Convert Materials Project IDs into a predictable mp-12345 format.
    """

    if value is None:
        return ""

    text = str(value).strip()

    match = re.search(
        r"mp-\d+",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(0).lower()

    return text.lower()


def safe_int(value, default=0):

    if pd.isna(value):
        return default

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def empty_mp_record():
    """
    Ensure every candidate always has the expected MP fields.
    """

    return {
        "mp_formula_stage63": None,
        "energy_above_hull": None,
        "formation_energy_per_atom_stage63": None,
        "mp_is_stable_stage63": None,
        "mp_theoretical_stage63": None,
        "nsites_stage63": None,
        "num_elements_stage63": None,
        "elements_stage63": "",
        "chemistry_flags": "MP_METADATA_UNAVAILABLE",
        "mp_metadata_status": "NOT_FOUND",
    }


# =========================================================
# THERMODYNAMIC STABILITY
# =========================================================

def thermodynamic_score(energy_above_hull):

    if pd.isna(energy_above_hull):
        return 10.0

    value = float(energy_above_hull)

    if value <= 0.005:
        return 45.0

    if value <= 0.025:
        return 40.0

    if value <= 0.050:
        return 34.0

    if value <= 0.100:
        return 25.0

    if value <= 0.200:
        return 14.0

    return 4.0


def stability_label(energy_above_hull):

    if pd.isna(energy_above_hull):
        return "UNKNOWN"

    value = float(energy_above_hull)

    if value <= 0.005:
        return "ON_OR_NEAR_HULL"

    if value <= 0.025:
        return "VERY_LOW_METASTABILITY"

    if value <= 0.050:
        return "LOW_METASTABILITY"

    if value <= 0.100:
        return "MODERATE_METASTABILITY"

    if value <= 0.200:
        return "HIGH_METASTABILITY"

    return "VERY_HIGH_METASTABILITY"


# =========================================================
# PROVENANCE SUPPORT
# =========================================================

def provenance_score(provenance_class):

    scores = {
        "EXPERIMENTAL_STRUCTURE_EVIDENCE": 25.0,
        "REFERENCED_PROVENANCE": 17.0,
        "COMPUTATIONAL_WITH_REFERENCES": 12.0,
        "COMPUTATIONAL_ONLY": 4.0,
        "LIMITED_PROVENANCE": 6.0,
    }

    return scores.get(
        str(provenance_class),
        6.0,
    )


# =========================================================
# LITERATURE SUPPORT
# =========================================================

def literature_support_score(
    direct_cathode_papers,
    battery_related_papers,
    chemistry_only_papers,
):

    direct = safe_int(
        direct_cathode_papers
    )

    battery = safe_int(
        battery_related_papers
    )

    chemistry = safe_int(
        chemistry_only_papers
    )

    if direct >= 3:
        return 20.0

    if direct >= 1:
        return 15.0

    if battery >= 1:
        return 10.0

    if chemistry >= 1:
        return 5.0

    return 0.0


# =========================================================
# STRUCTURAL COMPLEXITY
# =========================================================

def complexity_score(
    num_elements,
    nsites,
):

    score = 0.0

    # -------------------------------
    # Number of elements
    # -------------------------------

    if pd.isna(num_elements):

        score += 2.5

    else:

        n = int(num_elements)

        if n <= 3:
            score += 5.0

        elif n == 4:
            score += 4.5

        elif n == 5:
            score += 3.5

        elif n == 6:
            score += 2.5

        else:
            score += 1.5

    # -------------------------------
    # Number of structural sites
    # -------------------------------

    if pd.isna(nsites):

        score += 2.5

    else:

        n = int(nsites)

        if n <= 20:
            score += 5.0

        elif n <= 40:
            score += 4.0

        elif n <= 80:
            score += 3.0

        elif n <= 150:
            score += 2.0

        else:
            score += 1.0

    return round(
        score,
        1,
    )


# =========================================================
# CHEMISTRY FLAGS
# =========================================================

def normalize_elements(elements):

    if elements is None:
        return []

    if not isinstance(
        elements,
        list,
    ):

        try:
            elements = list(
                elements
            )

        except TypeError:
            return []

    return [
        str(element)
        for element in elements
    ]


def chemistry_flags(elements):

    element_set = set(
        elements
    )

    flags = []

    if (
        "F" in element_set
        and "O" in element_set
    ):
        flags.append(
            "MIXED_OXYFLUORIDE_CHEMISTRY"
        )

    if "H" in element_set:
        flags.append(
            "HYDROGEN_CONTAINING_PHASE"
        )

    if len(element_set) >= 6:
        flags.append(
            "HIGH_COMPOSITIONAL_COMPLEXITY"
        )

    if not flags:
        flags.append(
            "NO_SPECIAL_COMPLEXITY_FLAG"
        )

    return ";".join(
        flags
    )


# =========================================================
# FINAL CLASSIFICATION
# =========================================================

def readiness_class(score):

    if score >= 75:
        return "STRONG_SYNTHESIS_SUPPORT"

    if score >= 55:
        return "MODERATE_SYNTHESIS_SUPPORT"

    if score >= 35:
        return "HIGHER_EXPERIMENTAL_UNCERTAINTY"

    return "LOW_SYNTHESIS_SUPPORT"


def discovery_class(
    provenance_class,
    novelty_signal,
    synthesis_score,
):

    experimental = (
        provenance_class
        == "EXPERIMENTAL_STRUCTURE_EVIDENCE"
    )

    no_exact_match = (
        novelty_signal
        == "INCONCLUSIVE_NO_EXACT_MATCH"
    )

    well_studied = (
        novelty_signal
        == "WELL_STUDIED_CATHODE"
    )

    limited_cathode = (
        novelty_signal
        == "LIMITED_CATHODE_LITERATURE"
    )

    if well_studied:

        return (
            "KNOWN_CATHODE_CONTROL"
        )

    if limited_cathode:

        return (
            "KNOWN_BUT_LESS_EXPLORED_CATHODE"
        )

    if (
        experimental
        and no_exact_match
        and synthesis_score >= 55
    ):

        return (
            "EXPERIMENTALLY_GROUNDED_UNDEREXPLORED"
        )

    if (
        experimental
        and no_exact_match
    ):

        return (
            "EXPERIMENTAL_STRUCTURE_HIGHER_UNCERTAINTY"
        )

    if (
        no_exact_match
        and synthesis_score >= 55
    ):

        return (
            "COMPUTATIONAL_DISCOVERY_PLAUSIBLE"
        )

    if no_exact_match:

        return (
            "COMPUTATIONAL_DISCOVERY_HIGH_RISK"
        )

    return "REQUIRES_REVIEW"


# =========================================================
# MATERIALS PROJECT
# =========================================================

def build_mp_record(doc):

    elements = normalize_elements(
        doc.get(
            "elements",
            [],
        )
    )

    return {
        "mp_formula_stage63": (
            doc.get(
                "formula_pretty"
            )
        ),
        "energy_above_hull": (
            doc.get(
                "energy_above_hull"
            )
        ),
        "formation_energy_per_atom_stage63": (
            doc.get(
                "formation_energy_per_atom"
            )
        ),
        "mp_is_stable_stage63": (
            doc.get(
                "is_stable"
            )
        ),
        "mp_theoretical_stage63": (
            doc.get(
                "theoretical"
            )
        ),
        "nsites_stage63": (
            doc.get(
                "nsites"
            )
        ),
        "num_elements_stage63": (
            len(elements)
        ),
        "elements_stage63": (
            ";".join(elements)
        ),
        "chemistry_flags": (
            chemistry_flags(
                elements
            )
        ),
        "mp_metadata_status": (
            "MATCHED"
        ),
    }


def query_materials_project(
    material_ids,
):

    api_key = os.getenv(
        "MP_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "MP_API_KEY is not set.\n\n"
            "In Command Prompt run:\n"
            "set MP_API_KEY=YOUR_API_KEY"
        )

    normalized_ids = [
        normalize_material_id(
            material_id
        )
        for material_id in material_ids
    ]

    fields = [
        "material_id",
        "formula_pretty",
        "energy_above_hull",
        "formation_energy_per_atom",
        "is_stable",
        "theoretical",
        "nsites",
        "elements",
    ]

    result = {}

    with MPRester(
        api_key,
        use_document_model=False,
        mute_progress_bars=True,
    ) as mpr:

        # -------------------------------------------------
        # First try one bulk request
        # -------------------------------------------------

        docs = (
            mpr.materials.summary.search(
                material_ids=normalized_ids,
                fields=fields,
            )
        )

        for doc in docs:

            material_id = (
                normalize_material_id(
                    doc.get(
                        "material_id"
                    )
                )
            )

            if material_id:

                result[
                    material_id
                ] = build_mp_record(
                    doc
                )

        # -------------------------------------------------
        # Retry anything that did not map correctly
        # -------------------------------------------------

        missing_ids = [
            material_id
            for material_id
            in normalized_ids
            if material_id
            not in result
        ]

        for material_id in missing_ids:

            try:

                docs = (
                    mpr.materials.summary.search(
                        material_ids=[
                            material_id
                        ],
                        fields=fields,
                    )
                )

                if not docs:
                    continue

                doc = docs[0]

                result[
                    material_id
                ] = build_mp_record(
                    doc
                )

            except Exception:

                continue

    return result


# =========================================================
# REPORT
# =========================================================

def format_hull_value(value):

    if pd.isna(value):
        return "N/A"

    return (
        f"{float(value):.6f}"
    )


def write_report(df):

    lines = []

    lines.append(
        "# MAPPS-Lite Week 6 Synthesis Feasibility"
    )

    lines.append("")

    lines.append(
        "This stage estimates synthesis readiness "
        "using thermodynamic stability, structural "
        "provenance, literature evidence, and "
        "structural complexity."
    )

    lines.append("")

    lines.append(
        "**Important:** this is a screening heuristic. "
        "It does not prove that a material can or "
        "cannot be synthesized."
    )

    lines.append("")

    lines.append(
        "## Materials Project Metadata"
    )

    lines.append("")

    matched_count = int(
        (
            df["mp_metadata_status"]
            == "MATCHED"
        ).sum()
    )

    lines.append(
        f"- MP metadata matched: "
        f"{matched_count}/{len(df)}"
    )

    lines.append("")
    lines.append(
        "## Readiness Summary"
    )
    lines.append("")

    counts = (
        df[
            "synthesis_readiness_class"
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
        "## Discovery Interpretation"
    )
    lines.append("")

    counts = (
        df[
            "discovery_class"
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

    ranked = df.sort_values(
        "synthesis_feasibility_score",
        ascending=False,
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
            "- MP metadata: "
            f"{row['mp_metadata_status']}"
        )

        lines.append(
            "- Energy above hull: "
            f"{format_hull_value(row['energy_above_hull'])} "
            "eV/atom"
        )

        lines.append(
            "- Thermodynamic class: "
            f"{row['thermodynamic_class']}"
        )

        lines.append(
            "- Synthesis feasibility score: "
            f"{row['synthesis_feasibility_score']}"
        )

        lines.append(
            "- Synthesis readiness: "
            f"{row['synthesis_readiness_class']}"
        )

        lines.append(
            "- Discovery interpretation: "
            f"{row['discovery_class']}"
        )

        lines.append(
            "- Chemistry flags: "
            f"{row['chemistry_flags']}"
        )

        lines.append("")

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 74)
    print("MAPPS-LITE WEEK 6")
    print(
        "STAGE 6.3 - "
        "SYNTHESIS FEASIBILITY"
    )
    print("=" * 74)

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "Could not find Stage 6.2 output:\n"
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

    required_columns = [
        "material_id",
        "week6_formula",
        "provenance_class",
        "literature_novelty_signal",
    ]

    missing_columns = [
        column
        for column
        in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required input columns: "
            + ", ".join(
                missing_columns
            )
        )

    material_ids = (
        df["material_id"]
        .map(
            normalize_material_id
        )
        .tolist()
    )

    print()
    print(
        "Querying Materials Project "
        "thermodynamic metadata..."
    )

    mp_data = (
        query_materials_project(
            material_ids
        )
    )

    matched_count = sum(
        material_id in mp_data
        for material_id in material_ids
    )

    print(
        f"Matched Materials Project metadata: "
        f"{matched_count}/{len(material_ids)}"
    )

    # -----------------------------------------------------
    # Important safety check
    # -----------------------------------------------------

    if matched_count == 0:

        raise RuntimeError(
            "Materials Project returned no usable "
            "metadata matches. Stage 6.3 stopped "
            "before producing misleading scores."
        )

    records = []

    print()

    for number, (_, row) in enumerate(
        df.iterrows(),
        start=1,
    ):

        material_id = (
            normalize_material_id(
                row["material_id"]
            )
        )

        formula = str(
            row["week6_formula"]
        ).strip()

        mp_record = (
            empty_mp_record()
        )

        mp_record.update(
            mp_data.get(
                material_id,
                {},
            )
        )

        print(
            f"[{number}/{len(df)}] "
            f"{material_id} | "
            f"{formula} | "
            f"MP={mp_record['mp_metadata_status']}"
        )

        energy_above_hull = (
            mp_record[
                "energy_above_hull"
            ]
        )

        num_elements = (
            mp_record[
                "num_elements_stage63"
            ]
        )

        nsites = (
            mp_record[
                "nsites_stage63"
            ]
        )

        thermo_score = (
            thermodynamic_score(
                energy_above_hull
            )
        )

        prov_score = (
            provenance_score(
                row.get(
                    "provenance_class",
                    "",
                )
            )
        )

        lit_score = (
            literature_support_score(
                row.get(
                    "direct_cathode_papers",
                    0,
                ),
                row.get(
                    "battery_related_papers",
                    0,
                ),
                row.get(
                    "chemistry_only_papers",
                    0,
                ),
            )
        )

        comp_score = (
            complexity_score(
                num_elements,
                nsites,
            )
        )

        total_score = round(
            thermo_score
            + prov_score
            + lit_score
            + comp_score,
            1,
        )

        readiness = (
            readiness_class(
                total_score
            )
        )

        discovery = (
            discovery_class(
                row.get(
                    "provenance_class",
                    "",
                ),
                row.get(
                    "literature_novelty_signal",
                    "",
                ),
                total_score,
            )
        )

        record = (
            row.to_dict()
        )

        record[
            "material_id"
        ] = material_id

        # Remove any stale value from earlier stages
        record.pop(
            "energy_above_hull",
            None,
        )

        # Add fresh Stage 6.3 MP metadata
        record.update(
            mp_record
        )

        record[
            "thermodynamic_score"
        ] = thermo_score

        record[
            "thermodynamic_class"
        ] = stability_label(
            energy_above_hull
        )

        record[
            "provenance_support_score"
        ] = prov_score

        record[
            "literature_support_score"
        ] = lit_score

        record[
            "structural_complexity_score"
        ] = comp_score

        record[
            "synthesis_feasibility_score"
        ] = total_score

        record[
            "synthesis_readiness_class"
        ] = readiness

        record[
            "discovery_class"
        ] = discovery

        records.append(
            record
        )

    output_df = pd.DataFrame(
        records
    )

    output_df[
        "energy_above_hull"
    ] = pd.to_numeric(
        output_df[
            "energy_above_hull"
        ],
        errors="coerce",
    )

    output_df = (
        output_df.sort_values(
            "synthesis_feasibility_score",
            ascending=False,
        )
    )

    # =====================================================
    # SAVE OUTPUTS
    # =====================================================

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
    print("=" * 74)
    print(
        "SYNTHESIS FEASIBILITY COMPLETE"
    )
    print("=" * 74)

    print()
    print(
        "Synthesis readiness:"
    )

    print(
        output_df[
            "synthesis_readiness_class"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Discovery interpretation:"
    )

    print(
        output_df[
            "discovery_class"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Candidate synthesis ranking:"
    )
    print()

    display_columns = [
        "material_id",
        "week6_formula",
        "energy_above_hull",
        "thermodynamic_class",
        "synthesis_feasibility_score",
        "synthesis_readiness_class",
        "discovery_class",
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