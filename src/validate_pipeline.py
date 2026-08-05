"""
MAPPS-Lite Pipeline Validation

Checks the integrity and internal consistency of the
datasets produced by the MAPPS-Lite pipeline.

Validation includes:

- configuration validity
- required output files
- required columns
- duplicate material IDs
- ranking score bounds
- sequential ranks
- ranking order
- screening status validity
- dataset size consistency
- material identity consistency
- candidate hull-energy threshold
"""

from pathlib import Path

import pandas as pd

try:
    from config import (
        CANDIDATE_MAX_HULL_ENERGY,
        STATUS_PROMISING,
        STATUS_POSSIBLE,
        STATUS_REVIEW,
        validate_configuration,
    )
except ImportError:
    from .config import (
        CANDIDATE_MAX_HULL_ENERGY,
        STATUS_PROMISING,
        STATUS_POSSIBLE,
        STATUS_REVIEW,
        validate_configuration,
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


# ---------------------------------------------------------
# Required columns
# ---------------------------------------------------------

MATERIALS_REQUIRED_COLUMNS = {
    "material_id",
    "formula",
    "elements",
    "density",
    "band_gap",
    "energy_above_hull",
    "formation_energy_per_atom",
    "is_stable",
}

RANKED_REQUIRED_COLUMNS = (
    MATERIALS_REQUIRED_COLUMNS
    | {
        "rank",
        "hull_score",
        "formation_score",
        "stability_score",
        "score",
    }
)

SCREENED_REQUIRED_COLUMNS = (
    RANKED_REQUIRED_COLUMNS
    | {
        "battery_relevant_metals",
        "flagged_elements",
        "screening_status",
    }
)


# ---------------------------------------------------------
# Validation result helper
# ---------------------------------------------------------

def record_result(
    results,
    name,
    passed,
    details,
):
    """
    Store one validation result.
    """

    results.append(
        {
            "name": name,
            "passed": passed,
            "details": details,
        }
    )


# ---------------------------------------------------------
# File loading
# ---------------------------------------------------------

def load_required_csv(
    file_path,
):
    """
    Load a required pipeline CSV file.

    Raises FileNotFoundError if the file does not exist.
    """

    if not file_path.exists():

        raise FileNotFoundError(
            "Required pipeline file was not found:\n"
            f"{file_path}"
        )

    return pd.read_csv(
        file_path
    )


# ---------------------------------------------------------
# Column validation
# ---------------------------------------------------------

def validate_required_columns(
    dataframe,
    required_columns,
    dataset_name,
    results,
):
    """
    Confirm that a dataset contains all required columns.
    """

    missing_columns = (
        required_columns
        - set(
            dataframe.columns
        )
    )

    if missing_columns:

        record_result(
            results,
            f"{dataset_name} required columns",
            False,
            "Missing column(s): "
            + ", ".join(
                sorted(
                    missing_columns
                )
            ),
        )

        return False

    record_result(
        results,
        f"{dataset_name} required columns",
        True,
        "All required columns are present.",
    )

    return True


# ---------------------------------------------------------
# Duplicate validation
# ---------------------------------------------------------

def validate_unique_material_ids(
    dataframe,
    dataset_name,
    results,
):
    """
    Confirm that material_id is unique.
    """

    duplicate_count = (
        dataframe[
            "material_id"
        ]
        .duplicated()
        .sum()
    )

    passed = (
        duplicate_count == 0
    )

    record_result(
        results,
        f"{dataset_name} unique material IDs",
        passed,
        (
            "No duplicate material IDs."
            if passed
            else
            f"{duplicate_count} duplicate material ID(s)."
        ),
    )


# ---------------------------------------------------------
# Candidate threshold validation
# ---------------------------------------------------------

def validate_hull_threshold(
    materials,
    results,
):
    """
    Confirm that cleaned candidate materials respect the
    configured energy-above-hull limit.
    """

    hull_values = pd.to_numeric(
        materials[
            "energy_above_hull"
        ],
        errors="coerce",
    )

    invalid_numeric_count = (
        hull_values
        .isna()
        .sum()
    )

    if invalid_numeric_count > 0:

        record_result(
            results,
            "Candidate hull-energy values",
            False,
            (
                f"{invalid_numeric_count} material(s) "
                "have invalid hull-energy values."
            ),
        )

        return

    violations = (
        hull_values
        > CANDIDATE_MAX_HULL_ENERGY
    )

    violation_count = (
        violations.sum()
    )

    passed = (
        violation_count == 0
    )

    record_result(
        results,
        "Candidate hull-energy threshold",
        passed,
        (
            "All materials satisfy the configured "
            f"<= {CANDIDATE_MAX_HULL_ENERGY:.3f} "
            "eV/atom threshold."
            if passed
            else
            f"{violation_count} material(s) exceed "
            "the configured hull-energy threshold."
        ),
    )


# ---------------------------------------------------------
# Score validation
# ---------------------------------------------------------

def validate_score_bounds(
    ranked,
    results,
):
    """
    Confirm that component and final scores remain between
    0 and 1.
    """

    score_columns = [
        "hull_score",
        "formation_score",
        "stability_score",
        "score",
    ]

    for column in score_columns:

        values = pd.to_numeric(
            ranked[
                column
            ],
            errors="coerce",
        )

        invalid_count = (
            values
            .isna()
            .sum()
        )

        out_of_bounds_count = (
            (
                (values < 0)
                | (values > 1)
            )
            .sum()
        )

        passed = (
            invalid_count == 0
            and out_of_bounds_count == 0
        )

        record_result(
            results,
            f"{column} bounds",
            passed,
            (
                "All values are between 0 and 1."
                if passed
                else
                (
                    f"{invalid_count} invalid numeric "
                    "value(s), "
                    f"{out_of_bounds_count} value(s) "
                    "outside [0, 1]."
                )
            ),
        )


# ---------------------------------------------------------
# Rank validation
# ---------------------------------------------------------

def validate_sequential_ranks(
    ranked,
    results,
):
    """
    Confirm that ranks are exactly:

    1, 2, 3, ..., N
    """

    actual_ranks = pd.to_numeric(
        ranked[
            "rank"
        ],
        errors="coerce",
    )

    expected_ranks = pd.Series(
        range(
            1,
            len(ranked) + 1,
        ),
        index=ranked.index,
        dtype=float,
    )

    passed = (
        actual_ranks.notna().all()
        and actual_ranks.astype(float).equals(
            expected_ranks
        )
    )

    record_result(
        results,
        "Sequential ranks",
        passed,
        (
            f"Ranks correctly run from 1 to {len(ranked)}."
            if passed
            else
            "Rank values are not sequential."
        ),
    )


def validate_ranking_order(
    ranked,
    results,
):
    """
    Confirm that final ranking scores are ordered from
    highest to lowest.
    """

    scores = pd.to_numeric(
        ranked[
            "score"
        ],
        errors="coerce",
    )

    passed = (
        scores.notna().all()
        and scores.is_monotonic_decreasing
    )

    record_result(
        results,
        "Ranking score order",
        passed,
        (
            "Scores are ordered from highest to lowest."
            if passed
            else
            "Ranking scores are not monotonically decreasing."
        ),
    )


# ---------------------------------------------------------
# Screening validation
# ---------------------------------------------------------

def validate_screening_statuses(
    screened,
    results,
):
    """
    Confirm that every screening status is recognized.
    """

    valid_statuses = {
        STATUS_PROMISING,
        STATUS_POSSIBLE,
        STATUS_REVIEW,
    }

    actual_statuses = set(
        screened[
            "screening_status"
        ]
        .dropna()
        .unique()
    )

    invalid_statuses = (
        actual_statuses
        - valid_statuses
    )

    missing_status_count = (
        screened[
            "screening_status"
        ]
        .isna()
        .sum()
    )

    passed = (
        not invalid_statuses
        and missing_status_count == 0
    )

    if passed:

        details = (
            "All screening statuses are valid."
        )

    else:

        details_parts = []

        if invalid_statuses:

            details_parts.append(
                "Invalid status(es): "
                + ", ".join(
                    sorted(
                        invalid_statuses
                    )
                )
            )

        if missing_status_count > 0:

            details_parts.append(
                f"{missing_status_count} missing "
                "screening status value(s)."
            )

        details = " ".join(
            details_parts
        )

    record_result(
        results,
        "Screening status validity",
        passed,
        details,
    )


# ---------------------------------------------------------
# Dataset consistency
# ---------------------------------------------------------

def validate_dataset_counts(
    materials,
    ranked,
    screened,
    results,
):
    """
    Confirm that the material count remains consistent
    through ranking and screening.
    """

    materials_count = len(
        materials
    )

    ranked_count = len(
        ranked
    )

    screened_count = len(
        screened
    )

    passed = (
        materials_count
        == ranked_count
        == screened_count
    )

    record_result(
        results,
        "Dataset row-count consistency",
        passed,
        (
            "All pipeline stages contain "
            f"{materials_count} materials."
            if passed
            else
            (
                "Row counts differ: "
                f"materials={materials_count}, "
                f"ranked={ranked_count}, "
                f"screened={screened_count}."
            )
        ),
    )


def validate_material_identity(
    materials,
    ranked,
    screened,
    results,
):
    """
    Confirm that the same material IDs survive through
    the entire pipeline.
    """

    materials_ids = set(
        materials[
            "material_id"
        ]
        .astype(str)
    )

    ranked_ids = set(
        ranked[
            "material_id"
        ]
        .astype(str)
    )

    screened_ids = set(
        screened[
            "material_id"
        ]
        .astype(str)
    )

    passed = (
        materials_ids
        == ranked_ids
        == screened_ids
    )

    if passed:

        details = (
            "Material IDs are consistent across "
            "all pipeline stages."
        )

    else:

        missing_from_ranked = (
            materials_ids
            - ranked_ids
        )

        missing_from_screened = (
            ranked_ids
            - screened_ids
        )

        details = (
            f"{len(missing_from_ranked)} material(s) "
            "missing from ranked dataset; "
            f"{len(missing_from_screened)} material(s) "
            "missing from screened dataset."
        )

    record_result(
        results,
        "Material identity consistency",
        passed,
        details,
    )


# ---------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------

def run_configuration_validation(
    results,
):
    """
    Run validation checks defined in config.py.
    """

    try:

        validate_configuration()

        record_result(
            results,
            "Configuration validity",
            True,
            "MAPPS-Lite configuration is valid.",
        )

    except Exception as error:

        record_result(
            results,
            "Configuration validity",
            False,
            str(error),
        )


# ---------------------------------------------------------
# Print results
# ---------------------------------------------------------

def print_validation_results(
    results
):
    """
    Display all validation results in the terminal.
    """

    print()
    print("Validation results:")
    print()

    for result in results:

        status = (
            "PASS"
            if result[
                "passed"
            ]
            else "FAIL"
        )

        print(
            f"[{status}] "
            f"{result['name']}"
        )

        print(
            f"       {result['details']}"
        )

    print()


# ---------------------------------------------------------
# Complete validation pipeline
# ---------------------------------------------------------

def run_pipeline_validation():
    """
    Validate the complete MAPPS-Lite pipeline.

    Returns:
        list:
            Individual validation results.

    Raises:
        RuntimeError:
            If one or more validation checks fail.
    """

    results = []

    # -----------------------------------------------------
    # Configuration
    # -----------------------------------------------------

    run_configuration_validation(
        results
    )

    # -----------------------------------------------------
    # Load pipeline outputs
    # -----------------------------------------------------

    materials = load_required_csv(
        MATERIALS_FILE
    )

    ranked = load_required_csv(
        RANKED_FILE
    )

    screened = load_required_csv(
        SCREENED_FILE
    )

    # -----------------------------------------------------
    # Required columns
    # -----------------------------------------------------

    materials_columns_valid = (
        validate_required_columns(
            materials,
            MATERIALS_REQUIRED_COLUMNS,
            "materials.csv",
            results,
        )
    )

    ranked_columns_valid = (
        validate_required_columns(
            ranked,
            RANKED_REQUIRED_COLUMNS,
            "ranked_materials.csv",
            results,
        )
    )

    screened_columns_valid = (
        validate_required_columns(
            screened,
            SCREENED_REQUIRED_COLUMNS,
            "screened_materials.csv",
            results,
        )
    )

    # -----------------------------------------------------
    # Dataset-specific checks
    # -----------------------------------------------------

    if materials_columns_valid:

        validate_unique_material_ids(
            materials,
            "materials.csv",
            results,
        )

        validate_hull_threshold(
            materials,
            results,
        )

    if ranked_columns_valid:

        validate_unique_material_ids(
            ranked,
            "ranked_materials.csv",
            results,
        )

        validate_score_bounds(
            ranked,
            results,
        )

        validate_sequential_ranks(
            ranked,
            results,
        )

        validate_ranking_order(
            ranked,
            results,
        )

    if screened_columns_valid:

        validate_unique_material_ids(
            screened,
            "screened_materials.csv",
            results,
        )

        validate_screening_statuses(
            screened,
            results,
        )

    # -----------------------------------------------------
    # Cross-stage checks
    # -----------------------------------------------------

    if (
        materials_columns_valid
        and ranked_columns_valid
        and screened_columns_valid
    ):

        validate_dataset_counts(
            materials,
            ranked,
            screened,
            results,
        )

        validate_material_identity(
            materials,
            ranked,
            screened,
            results,
        )

    # -----------------------------------------------------
    # Display results
    # -----------------------------------------------------

    print_validation_results(
        results
    )

    failed_results = [
        result
        for result in results
        if not result[
            "passed"
        ]
    ]

    if failed_results:

        raise RuntimeError(
            "MAPPS-Lite validation failed: "
            f"{len(failed_results)} check(s) failed."
        )

    print(
        "All MAPPS-Lite validation checks passed."
    )

    return results


# ---------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------

def main():
    """
    Run validation independently.
    """

    run_pipeline_validation()


if __name__ == "__main__":
    main()