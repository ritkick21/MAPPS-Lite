import os
import re
from pathlib import Path

import pandas as pd
from mp_api.client import MPRester


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_synthesis_feasibility.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_transport_evaluation.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week6_transport_evaluation.md"
)


# =========================================================
# GENERAL HELPERS
# =========================================================

def normalize_material_id(value):
    """
    Normalize Materials Project IDs to mp-12345.
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


def safe_float(value):
    """
    Safely convert a value to float.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def safe_bool(value):
    """
    Safely normalize boolean-like values.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()

    if text == "true":
        return True

    if text == "false":
        return False

    return None


# =========================================================
# ELECTRONIC SCREENING
# =========================================================

def electronic_score(
    band_gap,
    is_metal,
):
    """
    Electronic-accessibility screening score.

    This is NOT electrical conductivity.
    """

    metal = safe_bool(
        is_metal
    )

    if metal is True:
        return 100.0

    gap = safe_float(
        band_gap
    )

    if gap is None:
        return 50.0

    if gap <= 0.10:
        return 98.0

    if gap <= 0.50:
        return 92.0

    if gap <= 1.00:
        return 84.0

    if gap <= 2.00:
        return 70.0

    if gap <= 3.00:
        return 55.0

    if gap <= 4.00:
        return 40.0

    return 25.0


def electronic_class(
    band_gap,
    is_metal,
):

    metal = safe_bool(
        is_metal
    )

    if metal is True:
        return "METALLIC_SIGNAL"

    gap = safe_float(
        band_gap
    )

    if gap is None:
        return "ELECTRONIC_DATA_UNAVAILABLE"

    if gap <= 0.50:
        return "VERY_LOW_GAP_SIGNAL"

    if gap <= 1.50:
        return "LOW_GAP_SIGNAL"

    if gap <= 3.00:
        return "MODERATE_GAP_SIGNAL"

    return "WIDE_GAP_SIGNAL"


def electronic_risk(
    band_gap,
    is_metal,
):

    metal = safe_bool(
        is_metal
    )

    if metal is True:
        return "LOW_SCREENING_RISK"

    gap = safe_float(
        band_gap
    )

    if gap is None:
        return "UNKNOWN"

    if gap <= 1.00:
        return "LOW_SCREENING_RISK"

    if gap <= 2.50:
        return "MODERATE_SCREENING_RISK"

    return "HIGH_SCREENING_RISK"


# =========================================================
# LITHIUM STRUCTURE DESCRIPTORS
# =========================================================

def is_lithium_site(site):
    """
    Return True if a crystallographic site
    contains lithium.
    """

    try:

        for specie in site.species.keys():

            symbol = getattr(
                specie,
                "symbol",
                str(specie),
            )

            if symbol == "Li":
                return True

    except Exception:
        pass

    try:
        return (
            site.specie.symbol
            == "Li"
        )

    except Exception:
        return False


def classify_li_network(
    mean_nearest_distance,
    li_fraction,
):
    """
    Descriptive Li-network category.

    This is NOT a diffusion prediction.
    """

    distance = safe_float(
        mean_nearest_distance
    )

    fraction = safe_float(
        li_fraction
    )

    if (
        distance is None
        or fraction is None
    ):
        return (
            "INSUFFICIENT_LI_NETWORK_DATA"
        )

    if (
        distance <= 3.5
        and fraction >= 0.15
    ):
        return "COMPACT_LI_NETWORK"

    if distance <= 4.5:
        return "INTERMEDIATE_LI_NETWORK"

    return "SPARSE_LI_NETWORK"


def calculate_li_descriptors(
    structure,
):
    """
    Calculate structural descriptors of the
    lithium sublattice.

    These are not ionic conductivity values,
    migration barriers, or diffusion constants.
    """

    if structure is None:

        return {
            "structure_status": "UNAVAILABLE",
            "structure_volume": None,
            "li_site_count": None,
            "li_atomic_fraction": None,
            "volume_per_li": None,
            "minimum_li_li_distance": None,
            "mean_nearest_li_distance": None,
            "li_network_class": (
                "INSUFFICIENT_LI_NETWORK_DATA"
            ),
        }

    li_indices = []

    for index, site in enumerate(
        structure
    ):

        if is_lithium_site(
            site
        ):
            li_indices.append(
                index
            )

    li_count = len(
        li_indices
    )

    total_sites = len(
        structure
    )

    volume = float(
        structure.volume
    )

    # -----------------------------------------------------
    # Lithium fraction
    # -----------------------------------------------------

    if total_sites > 0:

        li_fraction = (
            li_count
            / total_sites
        )

    else:
        li_fraction = None

    # -----------------------------------------------------
    # Volume per Li
    # -----------------------------------------------------

    if li_count > 0:

        volume_per_li = (
            volume
            / li_count
        )

    else:
        volume_per_li = None

    # -----------------------------------------------------
    # Li-Li distances
    # -----------------------------------------------------

    nearest_distances = []
    pair_distances = []

    if li_count >= 2:

        for i_index in li_indices:

            local_distances = []

            for j_index in li_indices:

                if i_index == j_index:
                    continue

                try:

                    distance = float(
                        structure.get_distance(
                            i_index,
                            j_index,
                        )
                    )

                except Exception:
                    continue

                local_distances.append(
                    distance
                )

                pair_distances.append(
                    distance
                )

            if local_distances:

                nearest_distances.append(
                    min(
                        local_distances
                    )
                )

    if pair_distances:

        minimum_distance = min(
            pair_distances
        )

    else:
        minimum_distance = None

    if nearest_distances:

        mean_nearest_distance = (
            sum(nearest_distances)
            / len(nearest_distances)
        )

    else:
        mean_nearest_distance = None

    network_class = (
        classify_li_network(
            mean_nearest_distance,
            li_fraction,
        )
    )

    return {
        "structure_status": "AVAILABLE",

        "structure_volume": round(
            volume,
            4,
        ),

        "li_site_count": (
            li_count
        ),

        "li_atomic_fraction": (
            round(
                li_fraction,
                4,
            )
            if li_fraction is not None
            else None
        ),

        "volume_per_li": (
            round(
                volume_per_li,
                4,
            )
            if volume_per_li is not None
            else None
        ),

        "minimum_li_li_distance": (
            round(
                minimum_distance,
                4,
            )
            if minimum_distance is not None
            else None
        ),

        "mean_nearest_li_distance": (
            round(
                mean_nearest_distance,
                4,
            )
            if mean_nearest_distance is not None
            else None
        ),

        "li_network_class": (
            network_class
        ),
    }


# =========================================================
# MATERIALS PROJECT ELECTRONIC DATA
# =========================================================

def empty_electronic_record():

    return {
        "transport_mp_formula": None,
        "band_gap": None,
        "is_metal": None,
        "is_gap_direct": None,
        "transport_density": None,
        "transport_mp_volume": None,
        "transport_nsites": None,
        "electronic_metadata_status": (
            "NOT_FOUND"
        ),
    }


def build_electronic_record(doc):

    return {
        "transport_mp_formula": (
            doc.get(
                "formula_pretty"
            )
        ),

        "band_gap": (
            doc.get(
                "band_gap"
            )
        ),

        "is_metal": (
            doc.get(
                "is_metal"
            )
        ),

        "is_gap_direct": (
            doc.get(
                "is_gap_direct"
            )
        ),

        "transport_density": (
            doc.get(
                "density"
            )
        ),

        "transport_mp_volume": (
            doc.get(
                "volume"
            )
        ),

        "transport_nsites": (
            doc.get(
                "nsites"
            )
        ),

        "electronic_metadata_status": (
            "MATCHED"
        ),
    }


def query_mp_data(
    material_ids,
):
    """
    Query each material individually.

    IMPORTANT FIX:
    We use the ID that WE REQUESTED as the dictionary key.

    We do not rely on material_id being returned inside
    the API dictionary.
    """

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
        "formula_pretty",
        "band_gap",
        "is_metal",
        "is_gap_direct",
        "density",
        "volume",
        "nsites",
    ]

    summary_data = {}
    structures = {}

    with MPRester(
        api_key,
        use_document_model=False,
        mute_progress_bars=True,
    ) as mpr:

        # =================================================
        # ELECTRONIC DATA
        # =================================================

        print()
        print(
            "Retrieving electronic metadata "
            "individually..."
        )
        print()

        for number, material_id in enumerate(
            normalized_ids,
            start=1,
        ):

            try:

                docs = (
                    mpr.materials.summary.search(
                        material_ids=[
                            material_id
                        ],
                        fields=fields,
                    )
                )

                if docs:

                    doc = docs[0]

                    # -------------------------------------
                    # CRITICAL FIX
                    #
                    # Map the returned document directly
                    # to the ID we requested.
                    # -------------------------------------

                    summary_data[
                        material_id
                    ] = (
                        build_electronic_record(
                            doc
                        )
                    )

                    band_gap = (
                        summary_data[
                            material_id
                        ][
                            "band_gap"
                        ]
                    )

                    print(
                        f"    electronic "
                        f"[{number}/{len(normalized_ids)}] "
                        f"{material_id} "
                        f"-> MATCHED "
                        f"(gap={band_gap})"
                    )

                else:

                    print(
                        f"    electronic "
                        f"[{number}/{len(normalized_ids)}] "
                        f"{material_id} "
                        f"-> NO DOCUMENT"
                    )

            except Exception as exc:

                print(
                    f"    electronic "
                    f"[{number}/{len(normalized_ids)}] "
                    f"{material_id} "
                    f"-> ERROR: {exc}"
                )

        # =================================================
        # STRUCTURES
        # =================================================

        print()
        print(
            "Retrieving crystal structures..."
        )
        print()

        for number, material_id in enumerate(
            normalized_ids,
            start=1,
        ):

            try:

                structure = (
                    mpr.get_structure_by_material_id(
                        material_id,
                        final=True,
                    )
                )

                structures[
                    material_id
                ] = structure

                print(
                    f"    structure "
                    f"[{number}/{len(normalized_ids)}] "
                    f"{material_id} "
                    f"-> MATCHED"
                )

            except Exception as exc:

                structures[
                    material_id
                ] = None

                print(
                    f"    structure "
                    f"[{number}/{len(normalized_ids)}] "
                    f"{material_id} "
                    f"-> ERROR: {exc}"
                )

    return (
        summary_data,
        structures,
    )


# =========================================================
# STAGE 6.4 INTERPRETATION
# =========================================================

def stage64_class(
    electronic_risk_class,
    structure_status,
):

    if structure_status != "AVAILABLE":

        return (
            "TRANSPORT_DATA_INCOMPLETE"
        )

    if electronic_risk_class == (
        "LOW_SCREENING_RISK"
    ):

        return (
            "FAVORABLE_ELECTRONIC_SIGNAL"
        )

    if electronic_risk_class == (
        "MODERATE_SCREENING_RISK"
    ):

        return (
            "ELECTRONIC_LIMITATION_POSSIBLE"
        )

    if electronic_risk_class == (
        "HIGH_SCREENING_RISK"
    ):

        return (
            "ELECTRONIC_LIMITATION_LIKELY"
        )

    return (
        "TRANSPORT_REQUIRES_REVIEW"
    )


# =========================================================
# REPORT HELPERS
# =========================================================

def format_value(
    value,
    decimals=4,
):

    numeric = safe_float(
        value
    )

    if numeric is None:
        return "N/A"

    return (
        f"{numeric:.{decimals}f}"
    )


def write_report(df):

    lines = []

    lines.append(
        "# MAPPS-Lite Week 6 "
        "Electronic and Li-Transport Descriptors"
    )

    lines.append("")

    lines.append(
        "This stage evaluates calculated electronic "
        "properties and structural descriptors of "
        "the lithium sublattice."
    )

    lines.append("")

    lines.append(
        "**Important:** these descriptors do not "
        "represent measured conductivity, Li-ion "
        "migration barriers, or diffusion coefficients."
    )

    lines.append("")

    # -----------------------------------------------------
    # Availability
    # -----------------------------------------------------

    lines.append(
        "## Data Availability"
    )

    lines.append("")

    metadata_matches = int(
        (
            df[
                "electronic_metadata_status"
            ]
            == "MATCHED"
        ).sum()
    )

    structure_matches = int(
        (
            df[
                "structure_status"
            ]
            == "AVAILABLE"
        ).sum()
    )

    lines.append(
        f"- Electronic metadata: "
        f"{metadata_matches}/{len(df)}"
    )

    lines.append(
        f"- Structures: "
        f"{structure_matches}/{len(df)}"
    )

    # -----------------------------------------------------
    # Electronic results
    # -----------------------------------------------------

    lines.append("")
    lines.append(
        "## Electronic Screening"
    )
    lines.append("")

    counts = (
        df[
            "stage64_transport_class"
        ]
        .value_counts()
    )

    for label, count in (
        counts.items()
    ):

        lines.append(
            f"- {label}: {count}"
        )

    # -----------------------------------------------------
    # Li network
    # -----------------------------------------------------

    lines.append("")
    lines.append(
        "## Lithium Network Descriptors"
    )
    lines.append("")

    counts = (
        df[
            "li_network_class"
        ]
        .value_counts()
    )

    for label, count in (
        counts.items()
    ):

        lines.append(
            f"- {label}: {count}"
        )

    # -----------------------------------------------------
    # Candidate details
    # -----------------------------------------------------

    lines.append("")
    lines.append(
        "## Candidate Results"
    )
    lines.append("")

    ranked = (
        df.sort_values(
            "electronic_accessibility_score",
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
            "- Band gap: "
            f"{format_value(row['band_gap'])} eV"
        )

        lines.append(
            "- Metal: "
            f"{row['is_metal']}"
        )

        lines.append(
            "- Direct band gap: "
            f"{row['is_gap_direct']}"
        )

        lines.append(
            "- Electronic class: "
            f"{row['electronic_class']}"
        )

        lines.append(
            "- Electronic accessibility score: "
            f"{row['electronic_accessibility_score']}"
        )

        lines.append(
            "- Electronic screening risk: "
            f"{row['electronic_screening_risk']}"
        )

        lines.append(
            "- Li sites: "
            f"{row['li_site_count']}"
        )

        lines.append(
            "- Li atomic fraction: "
            f"{format_value(row['li_atomic_fraction'])}"
        )

        lines.append(
            "- Volume per Li: "
            f"{format_value(row['volume_per_li'])} "
            "A^3"
        )

        lines.append(
            "- Minimum Li-Li distance: "
            f"{format_value(row['minimum_li_li_distance'])} "
            "A"
        )

        lines.append(
            "- Mean nearest Li-Li distance: "
            f"{format_value(row['mean_nearest_li_distance'])} "
            "A"
        )

        lines.append(
            "- Li network: "
            f"{row['li_network_class']}"
        )

        lines.append(
            "- Stage 6.4 interpretation: "
            f"{row['stage64_transport_class']}"
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

    print("=" * 76)
    print("MAPPS-LITE WEEK 6")
    print(
        "STAGE 6.4 - "
        "ELECTRONIC AND TRANSPORT DESCRIPTORS"
    )
    print("=" * 76)

    # -----------------------------------------------------
    # Load Stage 6.3
    # -----------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "Could not find Stage 6.3 output:\n"
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
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                missing_columns
            )
        )

    material_ids = (
        df[
            "material_id"
        ]
        .map(
            normalize_material_id
        )
        .tolist()
    )

    # -----------------------------------------------------
    # Query MP
    # -----------------------------------------------------

    print()
    print(
        "Querying Materials Project "
        "electronic properties and structures..."
    )

    summary_data, structures = (
        query_mp_data(
            material_ids
        )
    )

    metadata_matches = sum(
        material_id
        in summary_data
        for material_id
        in material_ids
    )

    structure_matches = sum(
        structures.get(
            material_id
        )
        is not None
        for material_id
        in material_ids
    )

    print()
    print(
        "Electronic metadata matched: "
        f"{metadata_matches}/"
        f"{len(material_ids)}"
    )

    print(
        "Structures retrieved: "
        f"{structure_matches}/"
        f"{len(material_ids)}"
    )

    # -----------------------------------------------------
    # Stop instead of creating misleading scores
    # -----------------------------------------------------

    if metadata_matches == 0:

        raise RuntimeError(
            "No Materials Project electronic "
            "metadata was retrieved."
        )

    records = []

    print()

    # =====================================================
    # ANALYZE CANDIDATES
    # =====================================================

    for number, (_, row) in enumerate(
        df.iterrows(),
        start=1,
    ):

        material_id = (
            normalize_material_id(
                row[
                    "material_id"
                ]
            )
        )

        formula = str(
            row[
                "week6_formula"
            ]
        )

        electronic = (
            empty_electronic_record()
        )

        electronic.update(
            summary_data.get(
                material_id,
                {},
            )
        )

        structure = (
            structures.get(
                material_id
            )
        )

        descriptors = (
            calculate_li_descriptors(
                structure
            )
        )

        band_gap = (
            electronic[
                "band_gap"
            ]
        )

        is_metal = (
            electronic[
                "is_metal"
            ]
        )

        e_score = (
            electronic_score(
                band_gap,
                is_metal,
            )
        )

        e_class = (
            electronic_class(
                band_gap,
                is_metal,
            )
        )

        e_risk = (
            electronic_risk(
                band_gap,
                is_metal,
            )
        )

        interpretation = (
            stage64_class(
                e_risk,
                descriptors[
                    "structure_status"
                ],
            )
        )

        print(
            f"[{number}/{len(df)}] "
            f"{material_id} | "
            f"{formula} | "
            f"gap={band_gap} | "
            f"{interpretation}"
        )

        record = (
            row.to_dict()
        )

        record[
            "material_id"
        ] = material_id

        record.update(
            electronic
        )

        record.update(
            descriptors
        )

        record[
            "electronic_accessibility_score"
        ] = e_score

        record[
            "electronic_class"
        ] = e_class

        record[
            "electronic_screening_risk"
        ] = e_risk

        record[
            "stage64_transport_class"
        ] = interpretation

        records.append(
            record
        )

    # =====================================================
    # SAVE
    # =====================================================

    output_df = pd.DataFrame(
        records
    )

    output_df[
        "band_gap"
    ] = pd.to_numeric(
        output_df[
            "band_gap"
        ],
        errors="coerce",
    )

    output_df = (
        output_df.sort_values(
            "electronic_accessibility_score",
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
        "STAGE 6.4 COMPLETE"
    )
    print("=" * 76)

    print()
    print(
        "Electronic / transport classes:"
    )

    print(
        output_df[
            "stage64_transport_class"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Lithium-network classes:"
    )

    print(
        output_df[
            "li_network_class"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Candidate electronic results:"
    )
    print()

    display_columns = [
        "material_id",
        "week6_formula",
        "band_gap",
        "is_metal",
        "electronic_accessibility_score",
        "electronic_class",
        "li_atomic_fraction",
        "volume_per_li",
        "mean_nearest_li_distance",
        "li_network_class",
        "stage64_transport_class",
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