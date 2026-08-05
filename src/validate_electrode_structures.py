"""
MAPPS-Lite
Week 5: Exact Electrode Structure Validation

This stage strengthens the electrochemical evidence gathered earlier.

Previous Week 5 stages searched Materials Project insertion-electrode
data by chemical formula. That identifies electrode pathways associated
with a chemistry, but does not necessarily prove that the exact
MAPPS-Lite material ID participates in that electrode system.

This script performs a stronger query using Materials Project battery IDs.

For a candidate such as:

    mp-22526

the lithium insertion-electrode battery ID is queried as:

    mp-22526_Li

Inputs:
    data/electrochemical_evaluation.csv

Outputs:
    data/exact_structure_validation.csv
    reports/exact_structure_validation.md

Evidence classes:

    EXACT_ELECTRODE_MATCH
        Materials Project returned an insertion-electrode record using
        the candidate material's battery ID.

    FORMULA_FAMILY_ONLY
        No direct battery-ID record was returned, but the earlier
        formula-based search found an electrode pathway.

    NO_ELECTRODE_EVIDENCE
        Neither exact battery-ID evidence nor formula-family
        insertion-electrode evidence is available.

Important:
    "NO_ELECTRODE_EVIDENCE" does NOT mean the material is novel.
"""

from pathlib import Path
import argparse
import math
import os

import pandas as pd
from mp_api.client import MPRester


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "electrochemical_evaluation.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "exact_structure_validation.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "exact_structure_validation.md"
)


# =========================================================
# SETTINGS
# =========================================================

DEFAULT_LIMIT = 10

WORKING_ION_SYMBOL = "Li"


# =========================================================
# MATERIALS PROJECT FIELDS
# =========================================================

ELECTRODE_FIELDS = [
    "battery_type",
    "battery_formula",
    "material_ids",
    "framework",
    "framework_formula",
    "chemsys",
    "formula_charge",
    "formula_discharge",
    "id_charge",
    "id_discharge",
    "average_voltage",
    "capacity_grav",
    "capacity_vol",
    "energy_grav",
    "energy_vol",
    "fracA_charge",
    "fracA_discharge",
    "num_steps",
    "max_voltage_step",
    "max_delta_volume",
    "stability_charge",
    "stability_discharge",
]


# =========================================================
# SCORE WEIGHTS
#
# Same weights used in our earlier Week 5 evaluator.
# =========================================================

WEIGHTS = {
    "voltage": 0.20,
    "capacity": 0.20,
    "energy": 0.20,
    "volume_change": 0.15,
    "stability": 0.20,
    "voltage_steps": 0.05,
}


# =========================================================
# LOAD DATA
# =========================================================

def load_evaluation():
    """
    Load the Week 5 electrochemical candidate evaluation.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find:\n{INPUT_FILE}"
        )

    data = pd.read_csv(
        INPUT_FILE
    )

    required_columns = {
        "material_id",
        "formula",
        "database_match_type",
        "electrochemical_score",
    }

    missing = (
        required_columns
        - set(data.columns)
    )

    if missing:
        raise ValueError(
            "electrochemical_evaluation.csv "
            "is missing required columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    return data


# =========================================================
# CANDIDATE SELECTION
# =========================================================

def select_candidates(
    data,
    limit,
):
    """
    Select candidates for direct battery-ID validation.

    Candidates are checked in existing Week 5 ranking order.
    """

    selected = (
        data.copy()
    )

    if (
        "week5_electrochemical_rank"
        in selected.columns
    ):
        selected = selected.sort_values(
            "week5_electrochemical_rank",
            ascending=True,
        )

    elif "electrochemical_score" in selected.columns:
        selected = selected.sort_values(
            "electrochemical_score",
            ascending=False,
            na_position="last",
        )

    if (
        limit is not None
        and limit > 0
    ):
        selected = selected.head(
            limit
        )

    return selected.reset_index(
        drop=True
    )


# =========================================================
# NUMERIC HELPERS
# =========================================================

def to_float(value):
    """
    Convert value to float.

    Invalid or missing values become None.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None

        number = float(
            value
        )

        if math.isnan(number):
            return None

        return number

    except (
        ValueError,
        TypeError,
    ):
        return None


def interpolate_score(
    value,
    points,
):
    """
    Piecewise-linear interpolation.
    """

    if value is None:
        return None

    points = sorted(
        points,
        key=lambda item: item[0],
    )

    if value <= points[0][0]:
        return float(
            points[0][1]
        )

    if value >= points[-1][0]:
        return float(
            points[-1][1]
        )

    for index in range(
        len(points) - 1
    ):
        x1, y1 = points[index]
        x2, y2 = points[index + 1]

        if (
            x1
            <= value
            <= x2
        ):
            fraction = (
                (value - x1)
                / (x2 - x1)
            )

            return (
                y1
                + fraction
                * (y2 - y1)
            )

    return None


# =========================================================
# ELECTROCHEMICAL SUB-SCORES
# =========================================================

def voltage_score(voltage):
    """
    Score average cathode voltage.
    """

    return interpolate_score(
        voltage,
        [
            (1.5, 0),
            (2.0, 15),
            (2.5, 35),
            (3.0, 65),
            (3.5, 100),
            (4.0, 100),
            (4.3, 100),
            (4.5, 85),
            (5.0, 45),
            (5.5, 10),
            (6.0, 0),
        ],
    )


def capacity_score(capacity):
    """
    Score gravimetric capacity.
    """

    return interpolate_score(
        capacity,
        [
            (0, 0),
            (50, 10),
            (100, 50),
            (150, 75),
            (200, 100),
            (300, 100),
        ],
    )


def energy_score(energy):
    """
    Score gravimetric specific energy.
    """

    return interpolate_score(
        energy,
        [
            (0, 0),
            (150, 10),
            (300, 40),
            (500, 75),
            (700, 100),
            (1000, 100),
        ],
    )


def volume_change_score(
    volume_change,
):
    """
    Score structural volume change.
    """

    if volume_change is None:
        return None

    volume_change = abs(
        volume_change
    )

    return interpolate_score(
        volume_change,
        [
            (0, 100),
            (5, 100),
            (10, 85),
            (15, 65),
            (25, 35),
            (40, 0),
            (100, 0),
        ],
    )


def stability_score(
    charge,
    discharge,
):
    """
    Score the less stable electrode endpoint.
    """

    values = []

    if charge is not None:
        values.append(
            charge
        )

    if discharge is not None:
        values.append(
            discharge
        )

    if not values:
        return None

    worst = max(
        values
    )

    return interpolate_score(
        worst,
        [
            (0.00, 100),
            (0.025, 100),
            (0.05, 85),
            (0.10, 55),
            (0.20, 20),
            (0.30, 0),
            (1.00, 0),
        ],
    )


def voltage_steps_score(
    num_steps,
):
    """
    Give a small preference to simpler voltage profiles.
    """

    if num_steps is None:
        return None

    return interpolate_score(
        num_steps,
        [
            (1, 100),
            (2, 90),
            (3, 75),
            (4, 60),
            (5, 50),
            (8, 30),
            (12, 20),
        ],
    )


# =========================================================
# COMPLETE SCORE
# =========================================================

def calculate_score(
    document,
):
    """
    Calculate the same Week 5 electrochemical score using an
    exact battery-ID electrode record.
    """

    voltage = to_float(
        document.get(
            "average_voltage"
        )
    )

    capacity = to_float(
        document.get(
            "capacity_grav"
        )
    )

    energy = to_float(
        document.get(
            "energy_grav"
        )
    )

    volume_change = to_float(
        document.get(
            "max_delta_volume"
        )
    )

    stability_charge = to_float(
        document.get(
            "stability_charge"
        )
    )

    stability_discharge = to_float(
        document.get(
            "stability_discharge"
        )
    )

    num_steps = to_float(
        document.get(
            "num_steps"
        )
    )

    scores = {
        "voltage":
            voltage_score(
                voltage
            ),

        "capacity":
            capacity_score(
                capacity
            ),

        "energy":
            energy_score(
                energy
            ),

        "volume_change":
            volume_change_score(
                volume_change
            ),

        "stability":
            stability_score(
                stability_charge,
                stability_discharge,
            ),

        "voltage_steps":
            voltage_steps_score(
                num_steps
            ),
    }

    weighted_total = 0.0
    available_weight = 0.0
    available_metrics = 0

    for metric, score in (
        scores.items()
    ):
        if score is None:
            continue

        weight = WEIGHTS[
            metric
        ]

        weighted_total += (
            score
            * weight
        )

        available_weight += (
            weight
        )

        available_metrics += 1

    if available_weight == 0:
        return None, 0.0

    raw_score = (
        weighted_total
        / available_weight
    )

    completeness = (
        available_metrics
        / len(WEIGHTS)
    )

    confidence_factor = (
        0.50
        + 0.50
        * completeness
    )

    final_score = (
        raw_score
        * confidence_factor
    )

    return (
        final_score,
        completeness,
    )


# =========================================================
# BATTERY ID
# =========================================================

def create_battery_id(
    material_id,
):
    """
    Construct the Materials Project lithium battery ID.

    Example:

        mp-22526
            ->
        mp-22526_Li
    """

    return (
        f"{material_id}_"
        f"{WORKING_ION_SYMBOL}"
    )


# =========================================================
# MATERIALS PROJECT QUERY
# =========================================================

def query_exact_electrode(
    mpr,
    material_id,
):
    """
    Query the Materials Project insertion-electrode endpoint using
    the exact candidate battery ID.
    """

    battery_id = (
        create_battery_id(
            material_id
        )
    )

    try:
        documents = (
            mpr.materials
            .insertion_electrodes
            .search(
                battery_ids=battery_id,
                all_fields=False,
                fields=ELECTRODE_FIELDS,
            )
        )

        return (
            battery_id,
            documents,
            None,
        )

    except Exception as error:
        return (
            battery_id,
            [],
            str(error),
        )


# =========================================================
# SELECT BEST EXACT RECORD
# =========================================================

def select_best_record(
    documents,
):
    """
    When multiple direct electrode records are returned, select the
    one with the highest Week 5 electrochemical score.
    """

    if not documents:
        return None

    evaluated = []

    for document in documents:

        if not isinstance(
            document,
            dict,
        ):
            if hasattr(
                document,
                "model_dump",
            ):
                document = (
                    document.model_dump()
                )

            elif hasattr(
                document,
                "dict",
            ):
                document = (
                    document.dict()
                )

            else:
                continue

        score, completeness = (
            calculate_score(
                document
            )
        )

        result = {
            **document,
            "_exact_score":
                score,

            "_completeness":
                completeness,
        }

        evaluated.append(
            result
        )

    if not evaluated:
        return None

    def ranking_key(record):
        score = record.get(
            "_exact_score"
        )

        if score is None:
            return -1

        return score

    return max(
        evaluated,
        key=ranking_key,
    )


# =========================================================
# EVIDENCE CLASSIFICATION
# =========================================================

def determine_evidence_class(
    exact_found,
    previous_match_type,
):
    """
    Combine exact battery-ID evidence with our previous formula-level
    evidence.
    """

    if exact_found:
        return (
            "EXACT_ELECTRODE_MATCH"
        )

    if (
        str(previous_match_type)
        == "FORMULA_FAMILY_MATCH"
    ):
        return (
            "FORMULA_FAMILY_ONLY"
        )

    return (
        "NO_ELECTRODE_EVIDENCE"
    )


# =========================================================
# VALIDATE CANDIDATES
# =========================================================

def validate_candidates(
    candidates,
    api_key,
):
    """
    Query every selected candidate using its direct Materials Project
    battery identifier.
    """

    results = []

    total = len(
        candidates
    )

    exact_count = 0
    family_only_count = 0
    no_evidence_count = 0
    error_count = 0

    print()
    print("=" * 72)
    print("MAPPS-Lite Week 5")
    print("Exact Electrode Structure Validation")
    print("=" * 72)

    print(
        f"Candidates to validate: {total}"
    )

    print(
        f"Working ion: {WORKING_ION_SYMBOL}"
    )

    print()

    with MPRester(
        api_key,
        use_document_model=False,
        mute_progress_bars=True,
    ) as mpr:

        for position, (_, candidate) in enumerate(
            candidates.iterrows(),
            start=1,
        ):
            material_id = str(
                candidate[
                    "material_id"
                ]
            )

            formula = candidate[
                "formula"
            ]

            previous_match_type = (
                candidate.get(
                    "database_match_type"
                )
            )

            previous_score = (
                to_float(
                    candidate.get(
                        "electrochemical_score"
                    )
                )
            )

            print(
                f"[{position}/{total}] "
                f"{material_id} | "
                f"{formula}"
            )

            (
                battery_id,
                documents,
                error,
            ) = query_exact_electrode(
                mpr,
                material_id,
            )

            # ---------------------------------------------
            # QUERY ERROR
            # ---------------------------------------------

            if error is not None:
                error_count += 1

                print(
                    f"  QUERY ERROR: {error}"
                )

                evidence_class = (
                    determine_evidence_class(
                        False,
                        previous_match_type,
                    )
                )

                results.append(
                    {
                        "material_id":
                            material_id,

                        "formula":
                            formula,

                        "battery_id_queried":
                            battery_id,

                        "exact_record_found":
                            False,

                        "exact_record_count":
                            0,

                        "validation_error":
                            error,

                        "previous_database_match_type":
                            previous_match_type,

                        "previous_electrochemical_score":
                            previous_score,

                        "evidence_class":
                            evidence_class,
                    }
                )

                continue

            # ---------------------------------------------
            # NO EXACT RECORD
            # ---------------------------------------------

            if not documents:

                evidence_class = (
                    determine_evidence_class(
                        False,
                        previous_match_type,
                    )
                )

                if (
                    evidence_class
                    == "FORMULA_FAMILY_ONLY"
                ):
                    family_only_count += 1

                else:
                    no_evidence_count += 1

                print(
                    f"  No exact battery-ID record "
                    f"({battery_id})"
                )

                print(
                    f"  Evidence: "
                    f"{evidence_class}"
                )

                results.append(
                    {
                        "material_id":
                            material_id,

                        "formula":
                            formula,

                        "battery_id_queried":
                            battery_id,

                        "exact_record_found":
                            False,

                        "exact_record_count":
                            0,

                        "validation_error":
                            None,

                        "previous_database_match_type":
                            previous_match_type,

                        "previous_electrochemical_score":
                            previous_score,

                        "evidence_class":
                            evidence_class,
                    }
                )

                continue

            # ---------------------------------------------
            # EXACT RECORD FOUND
            # ---------------------------------------------

            exact_count += 1

            best = select_best_record(
                documents
            )

            evidence_class = (
                "EXACT_ELECTRODE_MATCH"
            )

            exact_score = None

            if best is not None:
                exact_score = (
                    best.get(
                        "_exact_score"
                    )
                )

            score_delta = None

            if (
                exact_score is not None
                and previous_score is not None
            ):
                score_delta = (
                    exact_score
                    - previous_score
                )

            print(
                f"  EXACT MATCH: "
                f"{battery_id}"
            )

            print(
                f"  Electrode records: "
                f"{len(documents)}"
            )

            if exact_score is not None:
                print(
                    f"  Exact electrochemical "
                    f"score: {exact_score:.1f}"
                )

            if (
                best is None
            ):
                best = {}

            results.append(
                {
                    "material_id":
                        material_id,

                    "formula":
                        formula,

                    "battery_id_queried":
                        battery_id,

                    "exact_record_found":
                        True,

                    "exact_record_count":
                        len(documents),

                    "validation_error":
                        None,

                    "previous_database_match_type":
                        previous_match_type,

                    "previous_electrochemical_score":
                        previous_score,

                    "evidence_class":
                        evidence_class,

                    "exact_electrochemical_score":
                        exact_score,

                    "score_delta_vs_formula_search":
                        score_delta,

                    "exact_data_completeness":
                        best.get(
                            "_completeness"
                        ),

                    "battery_type":
                        best.get(
                            "battery_type"
                        ),

                    "battery_formula":
                        best.get(
                            "battery_formula"
                        ),

                    "framework":
                        best.get(
                            "framework"
                        ),

                    "framework_formula":
                        best.get(
                            "framework_formula"
                        ),

                    "formula_charge":
                        best.get(
                            "formula_charge"
                        ),

                    "formula_discharge":
                        best.get(
                            "formula_discharge"
                        ),

                    "charged_material_id":
                        best.get(
                            "id_charge"
                        ),

                    "discharged_material_id":
                        best.get(
                            "id_discharge"
                        ),

                    "average_voltage_V":
                        best.get(
                            "average_voltage"
                        ),

                    "capacity_grav_mAh_g":
                        best.get(
                            "capacity_grav"
                        ),

                    "capacity_vol_mAh_cc":
                        best.get(
                            "capacity_vol"
                        ),

                    "energy_grav_Wh_kg":
                        best.get(
                            "energy_grav"
                        ),

                    "energy_vol_Wh_L":
                        best.get(
                            "energy_vol"
                        ),

                    "li_fraction_charge":
                        best.get(
                            "fracA_charge"
                        ),

                    "li_fraction_discharge":
                        best.get(
                            "fracA_discharge"
                        ),

                    "num_voltage_steps":
                        best.get(
                            "num_steps"
                        ),

                    "max_voltage_step_V":
                        best.get(
                            "max_voltage_step"
                        ),

                    "max_volume_change_percent":
                        best.get(
                            "max_delta_volume"
                        ),

                    "stability_charge_eV_atom":
                        best.get(
                            "stability_charge"
                        ),

                    "stability_discharge_eV_atom":
                        best.get(
                            "stability_discharge"
                        ),
                }
            )

    print()
    print("-" * 72)

    print(
        f"Exact electrode matches: "
        f"{exact_count}"
    )

    print(
        f"Formula-family only:      "
        f"{family_only_count}"
    )

    print(
        f"No electrode evidence:    "
        f"{no_evidence_count}"
    )

    print(
        f"Query errors:              "
        f"{error_count}"
    )

    print("-" * 72)

    return pd.DataFrame(
        results
    )


# =========================================================
# SORT RESULTS
# =========================================================

def sort_results(
    results,
):
    """
    Sort strongest evidence first.
    """

    order = {
        "EXACT_ELECTRODE_MATCH":
            0,

        "FORMULA_FAMILY_ONLY":
            1,

        "NO_ELECTRODE_EVIDENCE":
            2,
    }

    results[
        "_evidence_order"
    ] = (
        results[
            "evidence_class"
        ]
        .map(order)
        .fillna(3)
    )

    score_column = (
        "exact_electrochemical_score"
    )

    if (
        score_column
        not in results.columns
    ):
        results[
            score_column
        ] = None

    results = (
        results.sort_values(
            [
                "_evidence_order",
                score_column,
                "previous_electrochemical_score",
            ],
            ascending=[
                True,
                False,
                False,
            ],
            na_position="last",
        )
    )

    results = results.drop(
        columns=[
            "_evidence_order"
        ]
    )

    return results


# =========================================================
# SAVE CSV
# =========================================================

def save_results(
    results,
):
    """
    Save structure-validation dataset.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "Exact structure validation "
        "saved to:"
    )

    print(
        OUTPUT_FILE
    )


# =========================================================
# FORMAT REPORT VALUES
# =========================================================

def format_value(
    value,
    decimals=1,
):
    """
    Format Markdown values.
    """

    if value is None:
        return "-"

    try:
        if pd.isna(value):
            return "-"
    except TypeError:
        pass

    if isinstance(
        value,
        (float, int),
    ):
        return (
            f"{value:.{decimals}f}"
        )

    return str(value)


# =========================================================
# GENERATE REPORT
# =========================================================

def generate_report(
    results,
):
    """
    Generate a Markdown structure-validation report.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    exact = results[
        results[
            "evidence_class"
        ]
        == "EXACT_ELECTRODE_MATCH"
    ]

    family = results[
        results[
            "evidence_class"
        ]
        == "FORMULA_FAMILY_ONLY"
    ]

    none = results[
        results[
            "evidence_class"
        ]
        == "NO_ELECTRODE_EVIDENCE"
    ]

    errors = results[
        results[
            "validation_error"
        ].notna()
    ]

    report = []

    report.append(
        "# MAPPS-Lite Week 5 Exact Electrode Validation\n\n"
    )

    report.append(
        "## Purpose\n\n"
    )

    report.append(
        "Earlier Week 5 electrochemical evaluation searched "
        "Materials Project by chemical formula. That established "
        "chemistry-level insertion-electrode evidence but did not "
        "necessarily validate the exact MAPPS-Lite material ID.\n\n"
    )

    report.append(
        "This stage queries Materials Project using a direct lithium "
        "battery identifier constructed from each candidate material "
        "ID, such as `mp-22526_Li`.\n\n"
    )

    report.append(
        "## Results\n\n"
    )

    report.append(
        f"- Candidates checked: **{len(results)}**\n"
    )

    report.append(
        f"- Exact electrode matches: **{len(exact)}**\n"
    )

    report.append(
        f"- Formula-family evidence only: **{len(family)}**\n"
    )

    report.append(
        f"- No MP electrode evidence: **{len(none)}**\n"
    )

    report.append(
        f"- Query errors: **{len(errors)}**\n\n"
    )

    report.append(
        "## Evidence Interpretation\n\n"
    )

    report.append(
        "**EXACT_ELECTRODE_MATCH** provides the strongest Materials "
        "Project evidence in the current MAPPS-Lite pipeline because "
        "the insertion-electrode record is associated directly with "
        "the candidate's battery identifier.\n\n"
    )

    report.append(
        "**FORMULA_FAMILY_ONLY** means the chemistry participates in "
        "a calculated insertion-electrode system, but a direct battery "
        "record for the exact MAPPS-Lite material ID was not returned.\n\n"
    )

    report.append(
        "**NO_ELECTRODE_EVIDENCE** does not imply novelty or "
        "impossibility. It only means the Materials Project insertion "
        "electrode dataset did not provide evidence through either "
        "search method used here.\n\n"
    )

    report.append(
        "## Exact Matches\n\n"
    )

    if exact.empty:
        report.append(
            "No exact lithium insertion-electrode matches were found "
            "for the candidates checked.\n"
        )

    else:
        report.append(
            "| Material | Formula | Score | Voltage (V) | "
            "Capacity (mAh/g) | Energy (Wh/kg) | "
            "Volume Change (%) |\n"
        )

        report.append(
            "|---|---|---:|---:|---:|---:|---:|\n"
        )

        for _, row in exact.head(
            25
        ).iterrows():

            report.append(
                f"| {row.get('material_id', '-')} "
                f"| {row.get('formula', '-')} "
                f"| {format_value(row.get('exact_electrochemical_score'))} "
                f"| {format_value(row.get('average_voltage_V'), 2)} "
                f"| {format_value(row.get('capacity_grav_mAh_g'))} "
                f"| {format_value(row.get('energy_grav_Wh_kg'))} "
                f"| {format_value(row.get('max_volume_change_percent'))} |\n"
            )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            "".join(report)
        )

    print(
        "Validation report saved to:"
    )

    print(
        REPORT_FILE
    )


# =========================================================
# TERMINAL SUMMARY
# =========================================================

def print_summary(
    results,
):
    """
    Print final validation summary.
    """

    exact = results[
        results[
            "evidence_class"
        ]
        == "EXACT_ELECTRODE_MATCH"
    ]

    family = results[
        results[
            "evidence_class"
        ]
        == "FORMULA_FAMILY_ONLY"
    ]

    none = results[
        results[
            "evidence_class"
        ]
        == "NO_ELECTRODE_EVIDENCE"
    ]

    errors = results[
        results[
            "validation_error"
        ].notna()
    ]

    print()
    print("=" * 72)
    print("WEEK 5 EXACT ELECTRODE VALIDATION SUMMARY")
    print("=" * 72)

    print(
        f"Exact electrode matches: "
        f"{len(exact)}"
    )

    print(
        f"Formula-family only:      "
        f"{len(family)}"
    )

    print(
        f"No electrode evidence:    "
        f"{len(none)}"
    )

    print(
        f"Query errors:              "
        f"{len(errors)}"
    )

    if not exact.empty:

        print()
        print(
            "Top exact matches:"
        )

        top = exact.sort_values(
            "exact_electrochemical_score",
            ascending=False,
        ).head(10)

        for _, row in (
            top.iterrows()
        ):

            score = to_float(
                row.get(
                    "exact_electrochemical_score"
                )
            )

            score_text = (
                f"{score:.1f}"
                if score is not None
                else "-"
            )

            print(
                f"  "
                f"{row['material_id']:<12} "
                f"{row['formula']:<22} "
                f"{score_text}"
            )

    print("=" * 72)


# =========================================================
# COMMAND-LINE ARGUMENTS
# =========================================================

def parse_arguments():
    """
    Parse command-line arguments.

    --limit 10
        Validate the first 10 candidates.

    --limit 0
        Validate all candidates.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Validate MAPPS-Lite candidates "
            "using direct Materials Project "
            "lithium battery IDs."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=(
            "Number of candidates to validate. "
            "Use 0 for all candidates. "
            "Default: 10"
        ),
    )

    return parser.parse_args()


# =========================================================
# MAIN
# =========================================================

def main():
    """
    Run exact electrode validation.
    """

    args = parse_arguments()

    api_key = os.getenv(
        "MP_API_KEY"
    )

    if not api_key:
        raise EnvironmentError(
            "MP_API_KEY is not set.\n\n"
            "On Windows Command Prompt run:\n"
            "set MP_API_KEY=YOUR_API_KEY"
        )

    print(
        "Loading Week 5 "
        "electrochemical evaluation..."
    )

    data = (
        load_evaluation()
    )

    print(
        f"Loaded {len(data):,} candidates."
    )

    candidates = (
        select_candidates(
            data,
            args.limit,
        )
    )

    results = (
        validate_candidates(
            candidates,
            api_key,
        )
    )

    results = (
        sort_results(
            results
        )
    )

    save_results(
        results
    )

    generate_report(
        results
    )

    print_summary(
        results
    )

    print()
    print(
        "Week 5 exact electrode "
        "validation completed successfully."
    )


if __name__ == "__main__":
    main()