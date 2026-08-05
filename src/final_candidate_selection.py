"""
MAPPS-Lite
Week 5: Final Candidate Selection

This stage combines the major Week 5 evidence streams into a final,
scientifically interpretable candidate-selection system.

Inputs:
    data/electrochemical_evaluation.csv
    data/exact_structure_validation.csv
    data/cathode_benchmarks.csv
    data/benchmark_comparison.csv

Outputs:
    data/final_candidate_ranking.csv
    data/week5_shortlist.csv
    reports/final_candidate_selection.md

Selection philosophy
--------------------

MAPPS-Lite now separates candidates into three evidence tracks:

1. EXACT ELECTRODE CANDIDATES
   The candidate's exact Materials Project material ID has a lithium
   insertion-electrode record.

2. FORMULA-FAMILY FOLLOW-UP
   An insertion-electrode pathway exists for the chemistry, but the
   exact candidate structure was not directly validated.

3. DISCOVERY REVIEW
   No Materials Project insertion-electrode evidence was found.
   These candidates are not automatically rejected and are not
   automatically considered novel.

Important:
    The final score is a screening priority score.

    It does NOT predict experimental cycle life, rate capability,
    synthesis feasibility, safety, cost, ionic conductivity,
    electronic conductivity, or commercial viability.
"""

from pathlib import Path
import math

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVALUATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "electrochemical_evaluation.csv"
)

VALIDATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "exact_structure_validation.csv"
)

BENCHMARK_FILE = (
    PROJECT_ROOT
    / "data"
    / "cathode_benchmarks.csv"
)

BENCHMARK_COMPARISON_FILE = (
    PROJECT_ROOT
    / "data"
    / "benchmark_comparison.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "final_candidate_ranking.csv"
)

SHORTLIST_FILE = (
    PROJECT_ROOT
    / "data"
    / "week5_shortlist.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "final_candidate_selection.md"
)


# =========================================================
# SETTINGS
# =========================================================

SHORTLIST_SIZE = 15

REPORT_TOP_COUNT = 20

DISCOVERY_REVIEW_COUNT = 10

FORMULA_FOLLOWUP_COUNT = 10


# =========================================================
# FINAL SCORE WEIGHTS
# =========================================================

WEIGHTS = {
    "original_pipeline": 0.20,
    "electrochemical": 0.65,
    "evidence_strength": 0.15,
}


# =========================================================
# EVIDENCE STRENGTH
# =========================================================

EVIDENCE_SCORES = {
    "EXACT_ELECTRODE_MATCH": 100.0,
    "FORMULA_FAMILY_ONLY": 60.0,
    "NO_ELECTRODE_EVIDENCE": 20.0,
}


# =========================================================
# LOAD DATA
# =========================================================

def load_data():
    """
    Load all Week 5 datasets required for final selection.
    """

    required_files = [
        EVALUATION_FILE,
        VALIDATION_FILE,
        BENCHMARK_FILE,
        BENCHMARK_COMPARISON_FILE,
    ]

    for file_path in required_files:

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required Week 5 file not found:\n"
                f"{file_path}"
            )

    evaluation = pd.read_csv(
        EVALUATION_FILE
    )

    validation = pd.read_csv(
        VALIDATION_FILE
    )

    benchmarks = pd.read_csv(
        BENCHMARK_FILE
    )

    benchmark_comparison = pd.read_csv(
        BENCHMARK_COMPARISON_FILE
    )

    return (
        evaluation,
        validation,
        benchmarks,
        benchmark_comparison,
    )


# =========================================================
# NUMERIC HELPERS
# =========================================================

def to_float(value):
    """
    Safely convert values to floats.
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


# =========================================================
# PERCENTILE SCORING
# =========================================================

def percentile_scores(
    series,
    higher_is_better=True,
):
    """
    Convert a numeric series into a 0-100 relative score.

    Best candidate:
        approximately 100

    Worst candidate:
        approximately 0

    Percentile scoring is used rather than assuming that the original
    MAPPS-Lite score is calibrated on exactly the same numerical scale
    as the Week 5 electrochemical score.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid_count = (
        numeric.notna().sum()
    )

    if valid_count == 0:
        return pd.Series(
            [None] * len(series),
            index=series.index,
        )

    if valid_count == 1:

        result = pd.Series(
            [None] * len(series),
            index=series.index,
            dtype="float",
        )

        result.loc[
            numeric.notna()
        ] = 100.0

        return result

    ranks = numeric.rank(
        method="average",
        ascending=not higher_is_better,
    )

    scores = (
        100.0
        * (
            1.0
            - (
                ranks - 1.0
            )
            / (
                valid_count - 1.0
            )
        )
    )

    return scores


# =========================================================
# BENCHMARK STATISTICS
# =========================================================

def calculate_benchmark_statistics(
    benchmarks,
):
    """
    Calculate the reference-cathode score distribution.
    """

    if (
        "electrochemical_score"
        not in benchmarks.columns
    ):
        raise ValueError(
            "cathode_benchmarks.csv does not contain "
            "'electrochemical_score'."
        )

    scores = pd.to_numeric(
        benchmarks[
            "electrochemical_score"
        ],
        errors="coerce",
    ).dropna()

    if scores.empty:
        raise ValueError(
            "No usable benchmark electrochemical scores found."
        )

    return {
        "minimum":
            float(
                scores.min()
            ),

        "median":
            float(
                scores.median()
            ),

        "mean":
            float(
                scores.mean()
            ),

        "maximum":
            float(
                scores.max()
            ),
    }


# =========================================================
# PREPARE BASE DATA
# =========================================================

def prepare_base_dataset(
    benchmark_comparison,
    validation,
):
    """
    Merge benchmark comparison data with exact-structure validation.

    benchmark_comparison contains:
        - original MAPPS-Lite ranking
        - original MAPPS-Lite score
        - formula-level electrochemical score
        - reference chemistry labels

    exact_structure_validation contains:
        - exact electrode evidence
        - exact electrochemical scores
        - exact endpoint properties
    """

    base = (
        benchmark_comparison.copy()
    )

    base[
        "material_id"
    ] = (
        base[
            "material_id"
        ]
        .astype(str)
    )

    validation = (
        validation.copy()
    )

    validation[
        "material_id"
    ] = (
        validation[
            "material_id"
        ]
        .astype(str)
    )

    validation_columns = [
        "material_id",
        "battery_id_queried",
        "exact_record_found",
        "exact_record_count",
        "validation_error",
        "previous_database_match_type",
        "previous_electrochemical_score",
        "evidence_class",
        "exact_electrochemical_score",
        "score_delta_vs_formula_search",
        "exact_data_completeness",
        "battery_type",
        "battery_formula",
        "framework",
        "framework_formula",
        "formula_charge",
        "formula_discharge",
        "charged_material_id",
        "discharged_material_id",
        "average_voltage_V",
        "capacity_grav_mAh_g",
        "capacity_vol_mAh_cc",
        "energy_grav_Wh_kg",
        "energy_vol_Wh_L",
        "li_fraction_charge",
        "li_fraction_discharge",
        "num_voltage_steps",
        "max_voltage_step_V",
        "max_volume_change_percent",
        "stability_charge_eV_atom",
        "stability_discharge_eV_atom",
    ]

    available_validation_columns = [
        column
        for column in validation_columns
        if column in validation.columns
    ]

    validation = validation[
        available_validation_columns
    ]

    merged = base.merge(
        validation,
        on="material_id",
        how="left",
        suffixes=(
            "_formula",
            "_exact",
        ),
    )

    return merged


# =========================================================
# ORIGINAL MAPPS-LITE PRIOR
# =========================================================

def add_original_pipeline_score(
    data,
):
    """
    Convert the original MAPPS-Lite ranking into a normalized
    0-100 prior score.

    overall_score is preferred when available.

    original_rank is used as fallback.
    """

    result = (
        data.copy()
    )

    if (
        "original_overall_score"
        in result.columns
    ):
        result[
            "original_pipeline_percentile"
        ] = percentile_scores(
            result[
                "original_overall_score"
            ],
            higher_is_better=True,
        )

    else:
        result[
            "original_pipeline_percentile"
        ] = None

    # -----------------------------------------------------
    # FALLBACK TO ORIGINAL RANK
    # -----------------------------------------------------

    if (
        "original_rank"
        in result.columns
    ):

        rank_percentile = (
            percentile_scores(
                result[
                    "original_rank"
                ],
                higher_is_better=False,
            )
        )

        missing_mask = (
            result[
                "original_pipeline_percentile"
            ].isna()
        )

        result.loc[
            missing_mask,
            "original_pipeline_percentile",
        ] = rank_percentile[
            missing_mask
        ]

    return result


# =========================================================
# FINAL ELECTROCHEMICAL SCORE
# =========================================================

def select_electrochemical_score(
    row,
):
    """
    Select the strongest appropriate electrochemical evidence.

    EXACT_ELECTRODE_MATCH:
        use exact-structure score.

    FORMULA_FAMILY_ONLY:
        use the earlier formula-family score.

    NO_ELECTRODE_EVIDENCE:
        no electrochemical score is assigned.

    Exact scores intentionally override formula-level scores.
    """

    evidence = row.get(
        "evidence_class"
    )

    if (
        evidence
        == "EXACT_ELECTRODE_MATCH"
    ):
        return to_float(
            row.get(
                "exact_electrochemical_score"
            )
        )

    if (
        evidence
        == "FORMULA_FAMILY_ONLY"
    ):
        return to_float(
            row.get(
                "electrochemical_score"
            )
        )

    return None


def select_performance_source(
    row,
):
    """
    Describe where the final electrochemical score came from.
    """

    evidence = row.get(
        "evidence_class"
    )

    if (
        evidence
        == "EXACT_ELECTRODE_MATCH"
    ):
        return (
            "EXACT_STRUCTURE"
        )

    if (
        evidence
        == "FORMULA_FAMILY_ONLY"
    ):
        return (
            "FORMULA_FAMILY"
        )

    return (
        "NO_ELECTROCHEMICAL_SCORE"
    )


# =========================================================
# EVIDENCE STRENGTH SCORE
# =========================================================

def evidence_strength_score(
    evidence_class,
):
    """
    Convert evidence type into a numerical confidence score.
    """

    return EVIDENCE_SCORES.get(
        str(evidence_class),
        0.0,
    )


# =========================================================
# WEIGHTED SCORE
# =========================================================

def weighted_selection_score(
    original_score,
    electrochemical_score,
    evidence_score,
):
    """
    Calculate the final validated candidate score.

    Electrochemical performance receives the largest weight.

    Candidates without electrochemical data receive no final
    validated-selection score. They remain in the separate
    discovery-review track.
    """

    if electrochemical_score is None:
        return None

    components = {
        "original_pipeline":
            original_score,

        "electrochemical":
            electrochemical_score,

        "evidence_strength":
            evidence_score,
    }

    weighted_total = 0.0
    available_weight = 0.0

    for component, value in (
        components.items()
    ):

        if value is None:
            continue

        weight = WEIGHTS[
            component
        ]

        weighted_total += (
            value
            * weight
        )

        available_weight += (
            weight
        )

    if available_weight == 0:
        return None

    return (
        weighted_total
        / available_weight
    )


# =========================================================
# BENCHMARK CLASSIFICATION
# =========================================================

def classify_against_benchmarks(
    score,
    reference_chemistry,
    benchmark_stats,
):
    """
    Compare final electrochemical performance with established
    reference cathodes.
    """

    if (
        reference_chemistry is not None
        and not pd.isna(
            reference_chemistry
        )
    ):
        return (
            "REFERENCE_CHEMISTRY"
        )

    if score is None:
        return (
            "UNVERIFIED"
        )

    if (
        score
        >= benchmark_stats[
            "maximum"
        ]
    ):
        return (
            "ABOVE_REFERENCE_MAX"
        )

    if (
        score
        >= benchmark_stats[
            "median"
        ]
    ):
        return (
            "ABOVE_REFERENCE_MEDIAN"
        )

    if (
        score
        >= benchmark_stats[
            "minimum"
        ]
    ):
        return (
            "WITHIN_REFERENCE_RANGE"
        )

    return (
        "BELOW_REFERENCE_RANGE"
    )


# =========================================================
# SELECTION TIER
# =========================================================

def determine_selection_tier(
    row,
    benchmark_stats,
):
    """
    Assign a scientifically interpretable selection tier.
    """

    reference_chemistry = row.get(
        "reference_chemistry"
    )

    if (
        reference_chemistry is not None
        and not pd.isna(
            reference_chemistry
        )
    ):
        return (
            "REFERENCE_BASELINE"
        )

    evidence = row.get(
        "evidence_class"
    )

    score = to_float(
        row.get(
            "final_electrochemical_score"
        )
    )

    # -----------------------------------------------------
    # EXACT STRUCTURE
    # -----------------------------------------------------

    if (
        evidence
        == "EXACT_ELECTRODE_MATCH"
    ):

        if (
            score is not None
            and score
            >= benchmark_stats[
                "median"
            ]
        ):
            return (
                "TIER_1_EXACT_COMPETITIVE"
            )

        if (
            score is not None
            and score
            >= benchmark_stats[
                "minimum"
            ]
        ):
            return (
                "TIER_2_EXACT_REFERENCE_RANGE"
            )

        if (
            score is not None
            and score >= 80
        ):
            return (
                "TIER_3_EXACT_PROMISING"
            )

        return (
            "EXACT_LOWER_PRIORITY"
        )

    # -----------------------------------------------------
    # FORMULA FAMILY
    # -----------------------------------------------------

    if (
        evidence
        == "FORMULA_FAMILY_ONLY"
    ):

        if (
            score is not None
            and score
            >= benchmark_stats[
                "median"
            ]
        ):
            return (
                "FORMULA_FAMILY_HIGH_PRIORITY"
            )

        if (
            score is not None
            and score >= 80
        ):
            return (
                "FORMULA_FAMILY_FOLLOWUP"
            )

        return (
            "FORMULA_FAMILY_LOWER_PRIORITY"
        )

    # -----------------------------------------------------
    # NO ELECTRODE EVIDENCE
    # -----------------------------------------------------

    return (
        "DISCOVERY_REVIEW_NO_ELECTRODE_DATA"
    )


# =========================================================
# RECOMMENDATION
# =========================================================

def determine_recommendation(
    row,
):
    """
    Convert selection tier into a practical next action.
    """

    tier = row.get(
        "selection_tier"
    )

    if (
        tier
        == "REFERENCE_BASELINE"
    ):
        return (
            "BENCHMARK_ONLY"
        )

    if tier in {
        "TIER_1_EXACT_COMPETITIVE",
        "TIER_2_EXACT_REFERENCE_RANGE",
    }:
        return (
            "ADVANCE_TO_DETAILED_REVIEW"
        )

    if (
        tier
        == "TIER_3_EXACT_PROMISING"
    ):
        return (
            "SECONDARY_EXACT_CANDIDATE"
        )

    if (
        tier
        == "EXACT_LOWER_PRIORITY"
    ):
        return (
            "DEPRIORITIZE_EXACT_CANDIDATE"
        )

    if (
        tier
        == "FORMULA_FAMILY_HIGH_PRIORITY"
    ):
        return (
            "VALIDATE_EXACT_STRUCTURE"
        )

    if (
        tier
        == "FORMULA_FAMILY_FOLLOWUP"
    ):
        return (
            "FOLLOW_UP_STRUCTURE_AND_LITERATURE"
        )

    if (
        tier
        == "FORMULA_FAMILY_LOWER_PRIORITY"
    ):
        return (
            "LOW_PRIORITY_FOLLOWUP"
        )

    return (
        "DISCOVERY_REVIEW"
    )


# =========================================================
# BUILD FINAL SELECTION DATASET
# =========================================================

def build_final_selection(
    merged,
    benchmark_stats,
):
    """
    Construct the final Week 5 candidate-selection dataset.
    """

    result = (
        merged.copy()
    )

    result = (
        add_original_pipeline_score(
            result
        )
    )

    final_electrochemical_scores = []

    performance_sources = []

    evidence_scores = []

    final_scores = []

    benchmark_classes = []

    selection_tiers = []

    recommendations = []

    discovery_scores = []

    for _, row in (
        result.iterrows()
    ):

        electrochemical_score = (
            select_electrochemical_score(
                row
            )
        )

        final_electrochemical_scores.append(
            electrochemical_score
        )

        performance_sources.append(
            select_performance_source(
                row
            )
        )

        evidence_score = (
            evidence_strength_score(
                row.get(
                    "evidence_class"
                )
            )
        )

        evidence_scores.append(
            evidence_score
        )

        original_score = to_float(
            row.get(
                "original_pipeline_percentile"
            )
        )

        final_score = (
            weighted_selection_score(
                original_score,
                electrochemical_score,
                evidence_score,
            )
        )

        final_scores.append(
            final_score
        )

        reference_chemistry = (
            row.get(
                "reference_chemistry"
            )
        )

        benchmark_classes.append(
            classify_against_benchmarks(
                electrochemical_score,
                reference_chemistry,
                benchmark_stats,
            )
        )

        # -------------------------------------------------
        # Discovery score
        #
        # Used ONLY when electrochemical evidence is absent.
        #
        # It is deliberately not mixed with validated scores.
        # -------------------------------------------------

        if electrochemical_score is None:
            discovery_scores.append(
                original_score
            )

        else:
            discovery_scores.append(
                None
            )

    result[
        "final_electrochemical_score"
    ] = final_electrochemical_scores

    result[
        "electrochemical_score_source"
    ] = performance_sources

    result[
        "evidence_strength_score"
    ] = evidence_scores

    result[
        "final_selection_score"
    ] = final_scores

    result[
        "final_benchmark_category"
    ] = benchmark_classes

    result[
        "discovery_priority_score"
    ] = discovery_scores

    # -----------------------------------------------------
    # SELECTION TIER
    # -----------------------------------------------------

    for _, row in (
        result.iterrows()
    ):
        selection_tiers.append(
            determine_selection_tier(
                row,
                benchmark_stats,
            )
        )

    result[
        "selection_tier"
    ] = selection_tiers

    # -----------------------------------------------------
    # RECOMMENDATION
    # -----------------------------------------------------

    for _, row in (
        result.iterrows()
    ):
        recommendations.append(
            determine_recommendation(
                row
            )
        )

    result[
        "recommended_action"
    ] = recommendations

    return result


# =========================================================
# ASSIGN FINAL RANKS
# =========================================================

def assign_ranks(
    data,
):
    """
    Assign two independent rankings:

    final_selection_rank
        For non-reference candidates with electrochemical evidence.

    discovery_review_rank
        For candidates without MP electrode evidence.
    """

    result = (
        data.copy()
    )

    result[
        "final_selection_rank"
    ] = None

    result[
        "discovery_review_rank"
    ] = None

    # -----------------------------------------------------
    # VALIDATED / FORMULA-FAMILY RESEARCH RANKING
    # -----------------------------------------------------

    reference_mask = (
        result[
            "reference_chemistry"
        ].notna()
    )

    validated_mask = (
        result[
            "final_selection_score"
        ].notna()
        &
        ~reference_mask
    )

    validated = result[
        validated_mask
    ].copy()

    validated = (
        validated.sort_values(
            [
                "final_selection_score",
                "final_electrochemical_score",
            ],
            ascending=[
                False,
                False,
            ],
        )
    )

    for rank, index in enumerate(
        validated.index,
        start=1,
    ):
        result.loc[
            index,
            "final_selection_rank",
        ] = rank

    # -----------------------------------------------------
    # DISCOVERY REVIEW RANKING
    # -----------------------------------------------------

    discovery_mask = (
        result[
            "evidence_class"
        ]
        == "NO_ELECTRODE_EVIDENCE"
    )

    discovery = result[
        discovery_mask
    ].copy()

    discovery = (
        discovery.sort_values(
            "discovery_priority_score",
            ascending=False,
            na_position="last",
        )
    )

    for rank, index in enumerate(
        discovery.index,
        start=1,
    ):
        result.loc[
            index,
            "discovery_review_rank",
        ] = rank

    return result


# =========================================================
# SORT FINAL DATASET
# =========================================================

def sort_final_dataset(
    data,
):
    """
    Sort output by practical research priority.
    """

    tier_order = {
        "TIER_1_EXACT_COMPETITIVE": 0,
        "TIER_2_EXACT_REFERENCE_RANGE": 1,
        "TIER_3_EXACT_PROMISING": 2,
        "FORMULA_FAMILY_HIGH_PRIORITY": 3,
        "FORMULA_FAMILY_FOLLOWUP": 4,
        "EXACT_LOWER_PRIORITY": 5,
        "FORMULA_FAMILY_LOWER_PRIORITY": 6,
        "REFERENCE_BASELINE": 7,
        "DISCOVERY_REVIEW_NO_ELECTRODE_DATA": 8,
    }

    result = (
        data.copy()
    )

    result[
        "_tier_order"
    ] = (
        result[
            "selection_tier"
        ]
        .map(
            tier_order
        )
        .fillna(99)
    )

    result = (
        result.sort_values(
            [
                "_tier_order",
                "final_selection_score",
                "discovery_priority_score",
            ],
            ascending=[
                True,
                False,
                False,
            ],
            na_position="last",
        )
    )

    result = result.drop(
        columns=[
            "_tier_order"
        ]
    )

    return result


# =========================================================
# BUILD SHORTLIST
# =========================================================

def build_shortlist(
    data,
):
    """
    Select the top exact-structure, non-reference research candidates.

    Formula-family candidates are deliberately excluded from the main
    shortlist until exact structural evidence is obtained.
    """

    shortlist = data[
        (
            data[
                "evidence_class"
            ]
            == "EXACT_ELECTRODE_MATCH"
        )
        &
        (
            data[
                "reference_chemistry"
            ].isna()
        )
        &
        (
            data[
                "final_selection_score"
            ].notna()
        )
    ].copy()

    shortlist = (
        shortlist.sort_values(
            [
                "final_selection_score",
                "final_electrochemical_score",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(
            SHORTLIST_SIZE
        )
    )

    shortlist.insert(
        0,
        "shortlist_rank",
        range(
            1,
            len(shortlist) + 1,
        ),
    )

    return shortlist


# =========================================================
# SAVE OUTPUTS
# =========================================================

def save_outputs(
    final_data,
    shortlist,
):
    """
    Save final Week 5 ranking datasets.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    shortlist.to_csv(
        SHORTLIST_FILE,
        index=False,
    )

    print()
    print(
        "Final candidate ranking saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "Week 5 shortlist saved to:"
    )

    print(
        SHORTLIST_FILE
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
# SHORTLIST TABLE
# =========================================================

def shortlist_markdown_table(
    shortlist,
):
    """
    Build the primary candidate shortlist table.
    """

    lines = [
        (
            "| Rank | Material | Formula | Final Score | "
            "Exact Electrochem | Benchmark | Tier |\n"
        ),
        (
            "|---:|---|---|---:|---:|---|---|\n"
        ),
    ]

    for _, row in (
        shortlist.iterrows()
    ):

        lines.append(
            f"| {row.get('shortlist_rank', '-')} "
            f"| {row.get('material_id', '-')} "
            f"| {row.get('formula', '-')} "
            f"| {format_value(row.get('final_selection_score'))} "
            f"| {format_value(row.get('final_electrochemical_score'))} "
            f"| {row.get('final_benchmark_category', '-')} "
            f"| {row.get('selection_tier', '-')} |\n"
        )

    return "".join(
        lines
    )


# =========================================================
# FOLLOW-UP TABLE
# =========================================================

def followup_markdown_table(
    data,
):
    """
    Show strongest formula-family candidates requiring exact
    structural validation.
    """

    followup = data[
        data[
            "evidence_class"
        ]
        == "FORMULA_FAMILY_ONLY"
    ].copy()

    followup = (
        followup.sort_values(
            "final_selection_score",
            ascending=False,
            na_position="last",
        )
        .head(
            FORMULA_FOLLOWUP_COUNT
        )
    )

    if followup.empty:
        return (
            "No formula-family-only candidates remain.\n"
        )

    lines = [
        (
            "| Material | Formula | Final Score | "
            "Formula Electrochem | Benchmark |\n"
        ),
        (
            "|---|---|---:|---:|---|\n"
        ),
    ]

    for _, row in (
        followup.iterrows()
    ):

        lines.append(
            f"| {row.get('material_id', '-')} "
            f"| {row.get('formula', '-')} "
            f"| {format_value(row.get('final_selection_score'))} "
            f"| {format_value(row.get('final_electrochemical_score'))} "
            f"| {row.get('final_benchmark_category', '-')} |\n"
        )

    return "".join(
        lines
    )


# =========================================================
# DISCOVERY REVIEW TABLE
# =========================================================

def discovery_markdown_table(
    data,
):
    """
    Show highest-priority candidates lacking electrode data.

    These are NOT directly comparable to electrochemically validated
    candidates.
    """

    discovery = data[
        data[
            "evidence_class"
        ]
        == "NO_ELECTRODE_EVIDENCE"
    ].copy()

    discovery = (
        discovery.sort_values(
            "discovery_priority_score",
            ascending=False,
            na_position="last",
        )
        .head(
            DISCOVERY_REVIEW_COUNT
        )
    )

    if discovery.empty:
        return (
            "No candidates remain in the discovery-review track.\n"
        )

    lines = [
        (
            "| Discovery Rank | Material | Formula | "
            "Original Pipeline Priority |\n"
        ),
        (
            "|---:|---|---|---:|\n"
        ),
    ]

    for _, row in (
        discovery.iterrows()
    ):

        lines.append(
            f"| {row.get('discovery_review_rank', '-')} "
            f"| {row.get('material_id', '-')} "
            f"| {row.get('formula', '-')} "
            f"| {format_value(row.get('discovery_priority_score'))} |\n"
        )

    return "".join(
        lines
    )


# =========================================================
# LARGE FORMULA VS EXACT SCORE CHANGES
# =========================================================

def score_delta_table(
    data,
):
    """
    Identify exact structures whose electrochemical scores differ
    strongly from the earlier formula-family estimate.
    """

    if (
        "score_delta_vs_formula_search"
        not in data.columns
    ):
        return (
            "Exact/formula score-delta data unavailable.\n"
        )

    exact = data[
        (
            data[
                "evidence_class"
            ]
            == "EXACT_ELECTRODE_MATCH"
        )
        &
        (
            data[
                "score_delta_vs_formula_search"
            ].notna()
        )
    ].copy()

    if exact.empty:
        return (
            "No exact/formula score comparisons available.\n"
        )

    exact[
        "_absolute_delta"
    ] = (
        exact[
            "score_delta_vs_formula_search"
        ]
        .abs()
    )

    largest = (
        exact.sort_values(
            "_absolute_delta",
            ascending=False,
        )
        .head(10)
    )

    lines = [
        (
            "| Material | Formula | Formula Score | "
            "Exact Score | Change |\n"
        ),
        (
            "|---|---|---:|---:|---:|\n"
        ),
    ]

    for _, row in (
        largest.iterrows()
    ):

        lines.append(
            f"| {row.get('material_id', '-')} "
            f"| {row.get('formula', '-')} "
            f"| {format_value(row.get('previous_electrochemical_score'))} "
            f"| {format_value(row.get('exact_electrochemical_score'))} "
            f"| {format_value(row.get('score_delta_vs_formula_search'))} |\n"
        )

    return "".join(
        lines
    )


# =========================================================
# GENERATE REPORT
# =========================================================

def generate_report(
    final_data,
    shortlist,
    benchmark_stats,
):
    """
    Generate the final Week 5 candidate-selection report.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    exact_count = (
        final_data[
            "evidence_class"
        ]
        == "EXACT_ELECTRODE_MATCH"
    ).sum()

    family_count = (
        final_data[
            "evidence_class"
        ]
        == "FORMULA_FAMILY_ONLY"
    ).sum()

    no_evidence_count = (
        final_data[
            "evidence_class"
        ]
        == "NO_ELECTRODE_EVIDENCE"
    ).sum()

    reference_count = (
        final_data[
            "reference_chemistry"
        ].notna()
    ).sum()

    tier_counts = (
        final_data[
            "selection_tier"
        ]
        .value_counts()
    )

    report = []

    report.append(
        "# MAPPS-Lite Week 5 Final Candidate Selection\n\n"
    )

    report.append(
        "## Overview\n\n"
    )

    report.append(
        "Week 5 extends MAPPS-Lite from composition-level screening "
        "into electrochemical and structure-specific candidate "
        "evaluation.\n\n"
    )

    report.append(
        "The final selection system combines the original MAPPS-Lite "
        "screening result with Materials Project lithium insertion "
        "electrode performance and the strength of the available "
        "electrochemical evidence.\n\n"
    )

    report.append(
        "## Evidence Summary\n\n"
    )

    report.append(
        f"- Exact electrode matches: **{exact_count}**\n"
    )

    report.append(
        f"- Formula-family-only matches: **{family_count}**\n"
    )

    report.append(
        f"- No MP electrode evidence: **{no_evidence_count}**\n"
    )

    report.append(
        f"- Reference cathode chemistries in candidate set: "
        f"**{reference_count}**\n\n"
    )

    report.append(
        "## Reference Cathode Distribution\n\n"
    )

    report.append(
        f"- Minimum benchmark score: "
        f"**{benchmark_stats['minimum']:.1f}**\n"
    )

    report.append(
        f"- Median benchmark score: "
        f"**{benchmark_stats['median']:.1f}**\n"
    )

    report.append(
        f"- Mean benchmark score: "
        f"**{benchmark_stats['mean']:.1f}**\n"
    )

    report.append(
        f"- Maximum benchmark score: "
        f"**{benchmark_stats['maximum']:.1f}**\n\n"
    )

    report.append(
        "## Final Score\n\n"
    )

    report.append(
        "For candidates with electrochemical evidence, the final "
        "selection score uses:\n\n"
    )

    report.append(
        "- Original MAPPS-Lite screening priority: **20%**\n"
    )

    report.append(
        "- Electrochemical performance: **65%**\n"
    )

    report.append(
        "- Evidence strength: **15%**\n\n"
    )

    report.append(
        "Exact-structure electrochemical scores always replace the "
        "earlier formula-family score when an exact electrode record "
        "exists.\n\n"
    )

    report.append(
        "Candidates with no electrode data are not assigned a "
        "validated-selection score. They remain in a separate "
        "discovery-review track based on the original MAPPS-Lite "
        "screening priority.\n\n"
    )

    report.append(
        "## Selection Tiers\n\n"
    )

    for tier, count in (
        tier_counts.items()
    ):
        report.append(
            f"- {tier}: **{count}**\n"
        )

    report.append(
        "\n"
    )

    report.append(
        "## Primary Research Shortlist\n\n"
    )

    report.append(
        "The primary shortlist contains the strongest non-reference "
        "candidates with exact Materials Project lithium insertion "
        "electrode evidence.\n\n"
    )

    if shortlist.empty:

        report.append(
            "No candidates satisfied the exact-structure shortlist "
            "criteria.\n\n"
        )

    else:

        report.append(
            shortlist_markdown_table(
                shortlist
            )
        )

        report.append(
            "\n"
        )

    report.append(
        "## Formula-Family Follow-Up Candidates\n\n"
    )

    report.append(
        "These candidates have chemistry-level electrode evidence but "
        "lack direct validation for the exact MAPPS-Lite structure.\n\n"
    )

    report.append(
        followup_markdown_table(
            final_data
        )
    )

    report.append(
        "\n"
    )

    report.append(
        "## Discovery Review Candidates\n\n"
    )

    report.append(
        "These candidates have no Materials Project insertion-electrode "
        "record through the searches performed in Week 5. They are "
        "retained for investigation rather than treated as failures.\n\n"
    )

    report.append(
        discovery_markdown_table(
            final_data
        )
    )

    report.append(
        "\n"
    )

    report.append(
        "## Formula-Level vs Exact-Structure Differences\n\n"
    )

    report.append(
        "Large differences between formula-family and exact-structure "
        "scores demonstrate why direct structural validation is "
        "important.\n\n"
    )

    report.append(
        score_delta_table(
            final_data
        )
    )

    report.append(
        "\n"
    )

    report.append(
        "## Interpretation\n\n"
    )

    report.append(
        "The primary research shortlist should be interpreted as a "
        "prioritized computational screening result, not as a list of "
        "materials proven experimentally superior to commercial "
        "cathodes.\n\n"
    )

    report.append(
        "A candidate can score highly because of favorable calculated "
        "voltage, capacity, energy density, stability, and structural "
        "behavior while still performing poorly experimentally because "
        "of kinetic barriers, low lithium diffusivity, poor electronic "
        "conductivity, difficult synthesis, irreversible transitions, "
        "electrolyte incompatibility, toxicity, cost, or other effects "
        "not captured by the present model.\n\n"
    )

    report.append(
        "## Next Scientific Stage\n\n"
    )

    report.append(
        "The next development stage should investigate the final "
        "shortlist using literature evidence and additional properties "
        "such as synthesis history, known cathode behavior, ionic "
        "transport, electronic properties, and novelty relative to "
        "previously reported battery materials.\n"
    )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "".join(
                report
            )
        )

    print()
    print(
        "Final candidate report saved to:"
    )

    print(
        REPORT_FILE
    )


# =========================================================
# TERMINAL SUMMARY
# =========================================================

def print_summary(
    final_data,
    shortlist,
    benchmark_stats,
):
    """
    Print the final Week 5 candidate-selection summary.
    """

    exact = (
        final_data[
            "evidence_class"
        ]
        == "EXACT_ELECTRODE_MATCH"
    ).sum()

    family = (
        final_data[
            "evidence_class"
        ]
        == "FORMULA_FAMILY_ONLY"
    ).sum()

    no_evidence = (
        final_data[
            "evidence_class"
        ]
        == "NO_ELECTRODE_EVIDENCE"
    ).sum()

    print()
    print("=" * 76)
    print("MAPPS-LITE WEEK 5 FINAL CANDIDATE SELECTION")
    print("=" * 76)

    print()
    print(
        f"Exact electrode candidates:   {exact}"
    )

    print(
        f"Formula-family candidates:    {family}"
    )

    print(
        f"Discovery-review candidates:  {no_evidence}"
    )

    print()

    print(
        "Reference cathode scores:"
    )

    print(
        f"  Minimum: {benchmark_stats['minimum']:.1f}"
    )

    print(
        f"  Median:  {benchmark_stats['median']:.1f}"
    )

    print(
        f"  Maximum: {benchmark_stats['maximum']:.1f}"
    )

    print()
    print(
        "Primary Week 5 shortlist:"
    )

    if shortlist.empty:

        print(
            "  No candidates available."
        )

    else:

        for _, row in (
            shortlist.iterrows()
        ):

            print(
                f"  "
                f"#{int(row['shortlist_rank']):<2} "
                f"{row['material_id']:<12} "
                f"{row['formula']:<22} "
                f"final={row['final_selection_score']:5.1f} "
                f"electrochem={row['final_electrochemical_score']:5.1f} "
                f"{row['selection_tier']}"
            )

    print()
    print("=" * 76)


# =========================================================
# MAIN
# =========================================================

def main():
    """
    Run the final Week 5 candidate-selection stage.
    """

    print(
        "Loading Week 5 candidate evidence..."
    )

    (
        evaluation,
        validation,
        benchmarks,
        benchmark_comparison,
    ) = load_data()

    print(
        f"Electrochemical evaluation: "
        f"{len(evaluation):,} candidates"
    )

    print(
        f"Exact structure validation: "
        f"{len(validation):,} candidates"
    )

    # -----------------------------------------------------
    # BENCHMARK STATISTICS
    # -----------------------------------------------------

    benchmark_stats = (
        calculate_benchmark_statistics(
            benchmarks
        )
    )

    # -----------------------------------------------------
    # MERGE EVIDENCE
    # -----------------------------------------------------

    merged = (
        prepare_base_dataset(
            benchmark_comparison,
            validation,
        )
    )

    # -----------------------------------------------------
    # FINAL SELECTION SCORES
    # -----------------------------------------------------

    final_data = (
        build_final_selection(
            merged,
            benchmark_stats,
        )
    )

    # -----------------------------------------------------
    # RANKS
    # -----------------------------------------------------

    final_data = (
        assign_ranks(
            final_data
        )
    )

    final_data = (
        sort_final_dataset(
            final_data
        )
    )

    # -----------------------------------------------------
    # SHORTLIST
    # -----------------------------------------------------

    shortlist = (
        build_shortlist(
            final_data
        )
    )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    save_outputs(
        final_data,
        shortlist,
    )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    generate_report(
        final_data,
        shortlist,
        benchmark_stats,
    )

    # -----------------------------------------------------
    # TERMINAL SUMMARY
    # -----------------------------------------------------

    print_summary(
        final_data,
        shortlist,
        benchmark_stats,
    )

    print()
    print(
        "Week 5 final candidate selection "
        "completed successfully."
    )


if __name__ == "__main__":
    main()