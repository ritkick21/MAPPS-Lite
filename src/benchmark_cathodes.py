"""
MAPPS-Lite
Week 5: Cathode Benchmarking

This stage compares MAPPS-Lite electrochemically evaluated
candidates against established lithium-ion cathode chemistries.

Inputs:
    data/electrochemical_evaluation.csv

Outputs:
    data/cathode_benchmarks.csv
    data/benchmark_comparison.csv
    reports/cathode_benchmark_report.md

Reference cathodes:
    LCO  - LiCoO2
    LFP  - LiFePO4
    LMO  - LiMn2O4
    LNO  - LiNiO2
    LMP  - LiMnPO4
    LCP  - LiCoPO4

Important:
    This is a computational benchmark.

    A high score does NOT prove that a candidate is experimentally
    superior to an established cathode.

    Properties such as cycle life, kinetics, conductivity,
    synthesis difficulty, safety, cost, and electrolyte compatibility
    are not fully captured here.
"""

from pathlib import Path
import math
import os

import pandas as pd

from mp_api.client import MPRester
from pymatgen.core import Element, Composition


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVALUATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "electrochemical_evaluation.csv"
)

BENCHMARK_FILE = (
    PROJECT_ROOT
    / "data"
    / "cathode_benchmarks.csv"
)

COMPARISON_FILE = (
    PROJECT_ROOT
    / "data"
    / "benchmark_comparison.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "cathode_benchmark_report.md"
)


# =========================================================
# SETTINGS
# =========================================================

WORKING_ION = Element("Li")

TOP_CANDIDATE_COUNT = 20


# =========================================================
# REFERENCE CATHODES
# =========================================================

REFERENCE_CATHODES = [
    {
        "name": "Lithium cobalt oxide",
        "abbreviation": "LCO",
        "formula": "LiCoO2",
    },
    {
        "name": "Lithium iron phosphate",
        "abbreviation": "LFP",
        "formula": "LiFePO4",
    },
    {
        "name": "Lithium manganese oxide",
        "abbreviation": "LMO",
        "formula": "LiMn2O4",
    },
    {
        "name": "Lithium nickel oxide",
        "abbreviation": "LNO",
        "formula": "LiNiO2",
    },
    {
        "name": "Lithium manganese phosphate",
        "abbreviation": "LMP",
        "formula": "LiMnPO4",
    },
    {
        "name": "Lithium cobalt phosphate",
        "abbreviation": "LCP",
        "formula": "LiCoPO4",
    },
]


# =========================================================
# SCORE WEIGHTS
#
# These match the Week 5 electrochemical evaluator.
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
# NUMERIC HELPERS
# =========================================================

def to_float(value):
    """
    Convert a value to float.

    Missing or invalid values become None.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None

        value = float(value)

        if math.isnan(value):
            return None

        return value

    except (ValueError, TypeError):
        return None


def interpolate_score(value, points):
    """
    Piecewise-linear scoring function.
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

        if x1 <= value <= x2:
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
#
# These intentionally match evaluate_electrochemistry.py
# so benchmarks and candidates are compared on the same scale.
# =========================================================

def calculate_voltage_score(voltage):
    """
    Score average electrode voltage.
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


def calculate_capacity_score(capacity):
    """
    Score gravimetric capacity in mAh/g.
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


def calculate_energy_score(energy):
    """
    Score gravimetric specific energy in Wh/kg.
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


def calculate_volume_score(volume_change):
    """
    Score structural volume change.

    Smaller volume changes receive higher scores.
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


def calculate_stability_score(
    stability_charge,
    stability_discharge,
):
    """
    Score thermodynamic endpoint stability.

    The worse endpoint is used.
    """

    values = []

    if stability_charge is not None:
        values.append(
            stability_charge
        )

    if stability_discharge is not None:
        values.append(
            stability_discharge
        )

    if not values:
        return None

    worst_stability = max(
        values
    )

    return interpolate_score(
        worst_stability,
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


def calculate_voltage_step_score(
    num_steps,
):
    """
    Score voltage-profile complexity.
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
# COMPLETE ELECTROCHEMICAL SCORE
# =========================================================

def calculate_electrochemical_score(
    electrode,
):
    """
    Calculate the same confidence-adjusted electrochemical
    score used for MAPPS-Lite candidates.
    """

    voltage = to_float(
        electrode.get(
            "average_voltage"
        )
    )

    capacity = to_float(
        electrode.get(
            "capacity_grav"
        )
    )

    energy = to_float(
        electrode.get(
            "energy_grav"
        )
    )

    volume_change = to_float(
        electrode.get(
            "max_delta_volume"
        )
    )

    stability_charge = to_float(
        electrode.get(
            "stability_charge"
        )
    )

    stability_discharge = to_float(
        electrode.get(
            "stability_discharge"
        )
    )

    num_steps = to_float(
        electrode.get(
            "num_steps"
        )
    )

    scores = {
        "voltage":
            calculate_voltage_score(
                voltage
            ),

        "capacity":
            calculate_capacity_score(
                capacity
            ),

        "energy":
            calculate_energy_score(
                energy
            ),

        "volume_change":
            calculate_volume_score(
                volume_change
            ),

        "stability":
            calculate_stability_score(
                stability_charge,
                stability_discharge,
            ),

        "voltage_steps":
            calculate_voltage_step_score(
                num_steps
            ),
    }

    weighted_total = 0.0
    available_weight = 0.0
    available_metrics = 0

    for metric, score in scores.items():

        if score is None:
            continue

        weight = WEIGHTS[
            metric
        ]

        weighted_total += (
            score * weight
        )

        available_weight += (
            weight
        )

        available_metrics += 1

    if available_weight == 0:
        return {
            "electrochemical_score_raw":
                None,

            "electrochemical_score":
                None,

            "data_completeness":
                0.0,
        }

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
        + 0.50 * completeness
    )

    adjusted_score = (
        raw_score
        * confidence_factor
    )

    return {
        "electrochemical_score_raw":
            raw_score,

        "electrochemical_score":
            adjusted_score,

        "data_completeness":
            completeness,

        "voltage_score":
            scores["voltage"],

        "capacity_score":
            scores["capacity"],

        "energy_score":
            scores["energy"],

        "volume_change_score":
            scores["volume_change"],

        "stability_score":
            scores["stability"],

        "voltage_steps_score":
            scores["voltage_steps"],
    }


# =========================================================
# LOAD MAPPS-LITE EVALUATION
# =========================================================

def load_candidate_evaluation():
    """
    Load Week 5 candidate evaluation.
    """

    if not EVALUATION_FILE.exists():
        raise FileNotFoundError(
            "Could not find:\n"
            f"{EVALUATION_FILE}\n\n"
            "Complete the Week 5 electrochemical "
            "evaluation first."
        )

    evaluation = pd.read_csv(
        EVALUATION_FILE
    )

    required_columns = {
        "material_id",
        "formula",
        "electrochemical_score",
        "database_match_type",
    }

    missing = (
        required_columns
        - set(evaluation.columns)
    )

    if missing:
        raise ValueError(
            "electrochemical_evaluation.csv "
            "is missing required columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    return evaluation


# =========================================================
# FORMULA NORMALIZATION
# =========================================================

def normalize_formula(formula):
    """
    Convert formulas to a reduced pymatgen formula for
    more reliable chemistry comparisons.
    """

    if formula is None:
        return None

    try:
        if pd.isna(formula):
            return None
    except TypeError:
        pass

    try:
        composition = Composition(
            str(formula)
        )

        return (
            composition.reduced_formula
        )

    except Exception:
        return str(
            formula
        ).replace(
            " ",
            "",
        )


# =========================================================
# MATERIALS PROJECT QUERY
# =========================================================

def search_reference_cathode(
    mpr,
    formula,
):
    """
    Retrieve Materials Project lithium insertion-electrode
    records associated with a reference cathode chemistry.
    """

    try:
        documents = (
            mpr.materials
            .insertion_electrodes
            .search(
                formula=formula,
                working_ion=WORKING_ION,
                all_fields=False,
                fields=ELECTRODE_FIELDS,
            )
        )

        return documents, None

    except Exception as error:
        return [], str(error)


# =========================================================
# SELECT BEST REFERENCE RECORD
# =========================================================

def select_best_reference_record(
    documents,
):
    """
    Score all electrode records associated with one reference
    chemistry and select the highest-scoring pathway.

    We do this because a formula can correspond to multiple
    calculated structures or insertion pathways.
    """

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

        score_data = (
            calculate_electrochemical_score(
                document
            )
        )

        combined = {
            **document,
            **score_data,
        }

        evaluated.append(
            combined
        )

    if not evaluated:
        return None

    def score_key(record):

        score = record.get(
            "electrochemical_score"
        )

        if score is None:
            return -1

        return score

    return max(
        evaluated,
        key=score_key,
    )


# =========================================================
# BUILD BENCHMARK DATASET
# =========================================================

def retrieve_benchmarks(
    api_key,
):
    """
    Query Materials Project for all reference cathode chemistries.
    """

    results = []

    print()
    print("=" * 72)
    print("MAPPS-Lite Week 5")
    print("Reference Cathode Benchmarking")
    print("=" * 72)

    with MPRester(
        api_key,
        use_document_model=False,
        mute_progress_bars=True,
    ) as mpr:

        for reference in (
            REFERENCE_CATHODES
        ):

            name = reference[
                "name"
            ]

            abbreviation = reference[
                "abbreviation"
            ]

            formula = reference[
                "formula"
            ]

            print(
                f"{abbreviation:<4} | "
                f"{formula:<12} | "
                f"{name}"
            )

            documents, error = (
                search_reference_cathode(
                    mpr,
                    formula,
                )
            )

            if error is not None:

                print(
                    f"     QUERY ERROR: "
                    f"{error}"
                )

                results.append(
                    {
                        "reference_name":
                            name,

                        "abbreviation":
                            abbreviation,

                        "reference_formula":
                            formula,

                        "query_status":
                            "ERROR",

                        "error_message":
                            error,
                    }
                )

                continue

            if not documents:

                print(
                    "     No MP electrode "
                    "record found"
                )

                results.append(
                    {
                        "reference_name":
                            name,

                        "abbreviation":
                            abbreviation,

                        "reference_formula":
                            formula,

                        "query_status":
                            "NOT_FOUND",
                    }
                )

                continue

            print(
                f"     Found "
                f"{len(documents)} "
                f"electrode record(s)"
            )

            best = (
                select_best_reference_record(
                    documents
                )
            )

            if best is None:

                results.append(
                    {
                        "reference_name":
                            name,

                        "abbreviation":
                            abbreviation,

                        "reference_formula":
                            formula,

                        "query_status":
                            "NO_USABLE_DATA",
                    }
                )

                continue

            score = best.get(
                "electrochemical_score"
            )

            print(
                f"     Best score: "
                f"{score:.1f}"
                if score is not None
                else
                "     Best score: unavailable"
            )

            results.append(
                {
                    "reference_name":
                        name,

                    "abbreviation":
                        abbreviation,

                    "reference_formula":
                        formula,

                    "query_status":
                        "FOUND",

                    "electrode_record_count":
                        len(documents),

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

                    "average_voltage_V":
                        best.get(
                            "average_voltage"
                        ),

                    "capacity_grav_mAh_g":
                        best.get(
                            "capacity_grav"
                        ),

                    "energy_grav_Wh_kg":
                        best.get(
                            "energy_grav"
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

                    "num_voltage_steps":
                        best.get(
                            "num_steps"
                        ),

                    "electrochemical_score_raw":
                        best.get(
                            "electrochemical_score_raw"
                        ),

                    "electrochemical_score":
                        best.get(
                            "electrochemical_score"
                        ),

                    "data_completeness":
                        best.get(
                            "data_completeness"
                        ),
                }
            )

    return pd.DataFrame(
        results
    )


# =========================================================
# BENCHMARK STATISTICS
# =========================================================

def calculate_benchmark_statistics(
    benchmarks,
):
    """
    Calculate reference score statistics.
    """

    valid = benchmarks[
        benchmarks[
            "electrochemical_score"
        ].notna()
    ].copy()

    if valid.empty:
        return {
            "count": 0,
            "minimum": None,
            "median": None,
            "mean": None,
            "maximum": None,
        }

    scores = valid[
        "electrochemical_score"
    ].astype(float)

    return {
        "count":
            len(scores),

        "minimum":
            scores.min(),

        "median":
            scores.median(),

        "mean":
            scores.mean(),

        "maximum":
            scores.max(),
    }


# =========================================================
# REFERENCE-CHEMISTRY DETECTION
# =========================================================

def create_reference_formula_map():
    """
    Map normalized formulas to reference cathode names.
    """

    reference_map = {}

    for reference in (
        REFERENCE_CATHODES
    ):

        normalized = normalize_formula(
            reference["formula"]
        )

        reference_map[
            normalized
        ] = reference[
            "abbreviation"
        ]

    return reference_map


# =========================================================
# COMPARE MAPPS-LITE CANDIDATES
# =========================================================

def compare_candidates(
    evaluation,
    benchmark_stats,
):
    """
    Compare each MAPPS-Lite candidate score against the
    reference-cathode score distribution.
    """

    comparison = (
        evaluation.copy()
    )

    reference_map = (
        create_reference_formula_map()
    )

    normalized_formulas = []

    known_reference_labels = []

    comparison_categories = []

    score_differences = []

    for _, row in (
        comparison.iterrows()
    ):

        formula = row.get(
            "formula"
        )

        normalized = (
            normalize_formula(
                formula
            )
        )

        normalized_formulas.append(
            normalized
        )

        reference_label = (
            reference_map.get(
                normalized
            )
        )

        if reference_label:
            known_reference_labels.append(
                reference_label
            )
        else:
            known_reference_labels.append(
                None
            )

        score = to_float(
            row.get(
                "electrochemical_score"
            )
        )

        if score is None:
            comparison_categories.append(
                "UNVERIFIED"
            )

            score_differences.append(
                None
            )

            continue

        if reference_label:
            comparison_categories.append(
                "REFERENCE_CHEMISTRY"
            )

        elif (
            benchmark_stats[
                "maximum"
            ] is not None
            and score
            >= benchmark_stats[
                "maximum"
            ]
        ):
            comparison_categories.append(
                "ABOVE_REFERENCE_RANGE"
            )

        elif (
            benchmark_stats[
                "median"
            ] is not None
            and score
            >= benchmark_stats[
                "median"
            ]
        ):
            comparison_categories.append(
                "ABOVE_REFERENCE_MEDIAN"
            )

        else:
            comparison_categories.append(
                "BELOW_REFERENCE_MEDIAN"
            )

        if (
            benchmark_stats[
                "median"
            ] is not None
        ):
            score_differences.append(
                score
                - benchmark_stats[
                    "median"
                ]
            )

        else:
            score_differences.append(
                None
            )

    comparison[
        "normalized_formula"
    ] = normalized_formulas

    comparison[
        "reference_chemistry"
    ] = known_reference_labels

    comparison[
        "benchmark_category"
    ] = comparison_categories

    comparison[
        "score_minus_reference_median"
    ] = score_differences

    return comparison


# =========================================================
# SAVE DATA
# =========================================================

def save_outputs(
    benchmarks,
    comparison,
):
    """
    Save benchmark and comparison datasets.
    """

    BENCHMARK_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    benchmarks.to_csv(
        BENCHMARK_FILE,
        index=False,
    )

    comparison.to_csv(
        COMPARISON_FILE,
        index=False,
    )

    print()
    print(
        "Benchmark data saved to:"
    )

    print(
        BENCHMARK_FILE
    )

    print()
    print(
        "Candidate comparison saved to:"
    )

    print(
        COMPARISON_FILE
    )


# =========================================================
# REPORT FORMATTING
# =========================================================

def format_value(
    value,
    decimals=1,
):
    """
    Format values for Markdown output.
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
# BENCHMARK MARKDOWN TABLE
# =========================================================

def benchmark_markdown_table(
    benchmarks,
):
    """
    Create benchmark summary table.
    """

    lines = [
        (
            "| Reference | Formula | "
            "Score | Voltage (V) | "
            "Capacity (mAh/g) | "
            "Energy (Wh/kg) | "
            "Volume Δ (%) |\n"
        ),
        (
            "|---|---|---:|---:|---:|"
            "---:|---:|\n"
        ),
    ]

    for _, row in (
        benchmarks.iterrows()
    ):

        lines.append(
            "| "
            f"{row.get('abbreviation', '-')} | "
            f"{row.get('reference_formula', '-')} | "
            f"{format_value(row.get('electrochemical_score'))} | "
            f"{format_value(row.get('average_voltage_V'), 2)} | "
            f"{format_value(row.get('capacity_grav_mAh_g'))} | "
            f"{format_value(row.get('energy_grav_Wh_kg'))} | "
            f"{format_value(row.get('max_volume_change_percent'))} |\n"
        )

    return "".join(
        lines
    )


# =========================================================
# CANDIDATE MARKDOWN TABLE
# =========================================================

def candidate_markdown_table(
    candidates,
):
    """
    Create candidate comparison table.
    """

    lines = [
        (
            "| Rank | Material | Formula | "
            "Score | Benchmark comparison | "
            "Database evidence |\n"
        ),
        (
            "|---:|---|---|---:|---|---|\n"
        ),
    ]

    for _, row in (
        candidates.iterrows()
    ):

        lines.append(
            "| "
            f"{row.get('week5_electrochemical_rank', '-')} | "
            f"{row.get('material_id', '-')} | "
            f"{row.get('formula', '-')} | "
            f"{format_value(row.get('electrochemical_score'))} | "
            f"{row.get('benchmark_category', '-')} | "
            f"{row.get('database_match_type', '-')} |\n"
        )

    return "".join(
        lines
    )


# =========================================================
# GENERATE REPORT
# =========================================================

def generate_report(
    benchmarks,
    comparison,
    benchmark_stats,
):
    """
    Generate the Week 5 benchmark report.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    verified = comparison[
        comparison[
            "electrochemical_score"
        ].notna()
    ].copy()

    verified = verified.sort_values(
        "electrochemical_score",
        ascending=False,
    )

    reference_candidates = verified[
        verified[
            "benchmark_category"
        ]
        == "REFERENCE_CHEMISTRY"
    ]

    non_reference = verified[
        verified[
            "benchmark_category"
        ]
        != "REFERENCE_CHEMISTRY"
    ].copy()

    top_non_reference = (
        non_reference.head(
            TOP_CANDIDATE_COUNT
        )
    )

    above_range = (
        comparison[
            "benchmark_category"
        ]
        == "ABOVE_REFERENCE_RANGE"
    ).sum()

    above_median = (
        comparison[
            "benchmark_category"
        ]
        == "ABOVE_REFERENCE_MEDIAN"
    ).sum()

    below_median = (
        comparison[
            "benchmark_category"
        ]
        == "BELOW_REFERENCE_MEDIAN"
    ).sum()

    unverified = (
        comparison[
            "benchmark_category"
        ]
        == "UNVERIFIED"
    ).sum()

    report = []

    report.append(
        "# MAPPS-Lite Week 5 Cathode Benchmark Report\n\n"
    )

    report.append(
        "## Purpose\n\n"
    )

    report.append(
        "This analysis compares MAPPS-Lite candidates against "
        "established lithium-ion cathode chemistries using the same "
        "Materials Project insertion-electrode properties and the "
        "same MAPPS-Lite electrochemical scoring system.\n\n"
    )

    report.append(
        "The goal is to determine whether MAPPS-Lite reproduces "
        "known strong cathode behavior and whether other candidate "
        "chemistries appear competitive on the calculated metrics.\n\n"
    )

    report.append(
        "## Reference Cathodes\n\n"
    )

    report.append(
        benchmark_markdown_table(
            benchmarks
        )
    )

    report.append(
        "\n## Reference Score Distribution\n\n"
    )

    report.append(
        f"- Reference cathodes with usable data: "
        f"**{benchmark_stats['count']}**\n"
    )

    report.append(
        f"- Minimum reference score: "
        f"**{format_value(benchmark_stats['minimum'])}**\n"
    )

    report.append(
        f"- Median reference score: "
        f"**{format_value(benchmark_stats['median'])}**\n"
    )

    report.append(
        f"- Mean reference score: "
        f"**{format_value(benchmark_stats['mean'])}**\n"
    )

    report.append(
        f"- Maximum reference score: "
        f"**{format_value(benchmark_stats['maximum'])}**\n\n"
    )

    report.append(
        "## MAPPS-Lite Comparison\n\n"
    )

    report.append(
        f"- Candidates at or above the best reference score: "
        f"**{above_range}**\n"
    )

    report.append(
        f"- Other candidates at or above the reference median: "
        f"**{above_median}**\n"
    )

    report.append(
        f"- Candidates below the reference median: "
        f"**{below_median}**\n"
    )

    report.append(
        f"- Candidates without MP electrochemical verification: "
        f"**{unverified}**\n"
    )

    report.append(
        f"- MAPPS-Lite candidates that are themselves one of the "
        f"reference chemistries: **{len(reference_candidates)}**\n\n"
    )

    report.append(
        "## Highest-Ranked Non-Reference Candidates\n\n"
    )

    if top_non_reference.empty:

        report.append(
            "No verified non-reference candidates were available.\n\n"
        )

    else:

        report.append(
            candidate_markdown_table(
                top_non_reference
            )
        )

        report.append(
            "\n"
        )

    report.append(
        "## Interpretation\n\n"
    )

    report.append(
        "Candidates classified as ABOVE_REFERENCE_RANGE or "
        "ABOVE_REFERENCE_MEDIAN should not automatically be interpreted "
        "as experimentally superior to LCO, LFP, LMO, or other established "
        "cathodes. The current comparison focuses on computed voltage, "
        "capacity, specific energy, volume change, endpoint stability, "
        "and voltage-profile complexity.\n\n"
    )

    report.append(
        "Important experimental and engineering properties remain "
        "outside the present score, including lithium diffusivity, "
        "electronic conductivity, cycle life, irreversible phase "
        "transformations, oxygen evolution, synthesis feasibility, "
        "raw-material cost, toxicity, electrolyte compatibility, "
        "and manufacturability.\n\n"
    )

    report.append(
        "Additionally, MAPPS-Lite currently has formula-family "
        "electrode evidence for many candidates but no exact-structure "
        "matches among the PROMISING set. Therefore, these benchmark "
        "results should be treated as chemistry-level evidence until "
        "the exact candidate structures are validated.\n\n"
    )

    report.append(
        "## Novelty Warning\n\n"
    )

    report.append(
        "A candidate that is not one of the benchmark formulas is "
        "not necessarily novel. Novelty requires separate literature "
        "and database investigation. This report only identifies whether "
        "a candidate matches the small set of established reference "
        "chemistries used for benchmarking.\n"
    )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "".join(report)
        )

    print()
    print(
        "Benchmark report saved to:"
    )

    print(
        REPORT_FILE
    )


# =========================================================
# TERMINAL SUMMARY
# =========================================================

def print_summary(
    benchmarks,
    comparison,
    benchmark_stats,
):
    """
    Print benchmark results to the terminal.
    """

    print()
    print("=" * 72)
    print("WEEK 5 CATHODE BENCHMARK SUMMARY")
    print("=" * 72)

    print()
    print("Reference cathodes:")

    for _, row in (
        benchmarks.iterrows()
    ):

        abbreviation = row.get(
            "abbreviation",
            "-",
        )

        formula = row.get(
            "reference_formula",
            "-",
        )

        score = to_float(
            row.get(
                "electrochemical_score"
            )
        )

        if score is None:

            score_text = (
                "no score"
            )

        else:

            score_text = (
                f"{score:.1f}"
            )

        print(
            f"  {abbreviation:<4} "
            f"{formula:<12} "
            f"{score_text}"
        )

    print()

    print(
        "Reference median score: "
        f"{format_value(benchmark_stats['median'])}"
    )

    print(
        "Reference maximum score: "
        f"{format_value(benchmark_stats['maximum'])}"
    )

    print()

    category_counts = (
        comparison[
            "benchmark_category"
        ]
        .value_counts()
    )

    print(
        "Candidate comparison:"
    )

    for category, count in (
        category_counts.items()
    ):

        print(
            f"  {category:<25} "
            f"{count}"
        )

    print()
    print(
        "Top non-reference candidates:"
    )

    non_reference = comparison[
        (
            comparison[
                "electrochemical_score"
            ].notna()
        )
        &
        (
            comparison[
                "benchmark_category"
            ]
            != "REFERENCE_CHEMISTRY"
        )
    ].copy()

    non_reference = (
        non_reference.sort_values(
            "electrochemical_score",
            ascending=False,
        )
        .head(10)
    )

    if non_reference.empty:

        print(
            "  No verified non-reference "
            "candidates found."
        )

    else:

        for _, row in (
            non_reference.iterrows()
        ):

            print(
                f"  {row['material_id']:<12} "
                f"{row['formula']:<22} "
                f"{row['electrochemical_score']:6.1f}  "
                f"{row['benchmark_category']}"
            )

    print()
    print("=" * 72)


# =========================================================
# MAIN
# =========================================================

def main():
    """
    Run Week 5 cathode benchmarking.
    """

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
        "Loading MAPPS-Lite "
        "electrochemical evaluation..."
    )

    evaluation = (
        load_candidate_evaluation()
    )

    print(
        f"Loaded {len(evaluation):,} "
        "candidates."
    )

    benchmarks = (
        retrieve_benchmarks(
            api_key
        )
    )

    benchmark_stats = (
        calculate_benchmark_statistics(
            benchmarks
        )
    )

    comparison = (
        compare_candidates(
            evaluation,
            benchmark_stats,
        )
    )

    save_outputs(
        benchmarks,
        comparison,
    )

    generate_report(
        benchmarks,
        comparison,
        benchmark_stats,
    )

    print_summary(
        benchmarks,
        comparison,
        benchmark_stats,
    )

    print()
    print(
        "Week 5 cathode benchmarking "
        "completed successfully."
    )


if __name__ == "__main__":
    main()