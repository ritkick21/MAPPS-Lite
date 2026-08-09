"""
MAPPS-Lite Week 8
Final Pipeline Integrity Validation

This script validates the structural and scientific integrity of the
MAPPS-Lite v1.0 outputs generated during Weeks 1-7.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# =============================================================================
# PROJECT PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

RESULTS_PATH = DATA_DIR / "week8_validation_results.csv"
REPORT_PATH = REPORTS_DIR / "week8_pipeline_validation.md"


# =============================================================================
# DATASETS
# =============================================================================

KEY_DATASETS = [
    "materials.csv",
    "ranked_materials.csv",
    "screened_materials.csv",
    "electrochemical_evaluation.csv",
    "exact_structure_validation.csv",
    "final_candidate_ranking.csv",
    "week5_shortlist.csv",
    "week6_research_shortlist.csv",
    "week6_literature_validation.csv",
    "week6_synthesis_feasibility.csv",
    "week6_transport_evaluation.csv",
    "week6_resource_assessment.csv",
    "week6_provenance_validation.csv",
    "week6_final_ranking.csv",
    "week7_final_ranking.csv",
]


UNIQUE_ID_DATASETS = [
    "materials.csv",
    "ranked_materials.csv",
    "screened_materials.csv",
    "electrochemical_evaluation.csv",
    "exact_structure_validation.csv",
    "final_candidate_ranking.csv",
    "week5_shortlist.csv",
    "week6_research_shortlist.csv",
    "week6_final_ranking.csv",
    "week7_final_ranking.csv",
]


# =============================================================================
# VALIDATION RESULT
# =============================================================================

@dataclass
class ValidationResult:
    category: str
    check: str
    status: str
    details: str


RESULTS: list[ValidationResult] = []


def add_result(
    category: str,
    check: str,
    status: str,
    details: str,
) -> None:
    RESULTS.append(
        ValidationResult(
            category=category,
            check=check,
            status=status,
            details=details,
        )
    )


# =============================================================================
# CSV UTILITIES
# =============================================================================

def read_csv(filename: str) -> list[dict]:
    path = DATA_DIR / filename

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def get_columns(filename: str) -> list[str]:
    path = DATA_DIR / filename

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        return reader.fieldnames or []


def normalize_id(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip()


def get_material_ids(filename: str) -> set[str]:
    rows = read_csv(filename)

    return {
        normalize_id(row.get("material_id"))
        for row in rows
        if normalize_id(row.get("material_id"))
    }


def safe_float(value: object) -> float | None:
    if value is None:
        return None

    text = str(value).strip()

    if text == "":
        return None

    try:
        return float(text)
    except ValueError:
        return None


# =============================================================================
# 1. DATASET PRESENCE
# =============================================================================

def validate_dataset_presence() -> None:
    for filename in KEY_DATASETS:
        path = DATA_DIR / filename

        if not path.exists():
            add_result(
                "Dataset",
                f"{filename} exists",
                "FAIL",
                "Required dataset is missing.",
            )
            continue

        try:
            rows = read_csv(filename)

            if len(rows) == 0:
                add_result(
                    "Dataset",
                    f"{filename} contains data",
                    "FAIL",
                    "CSV exists but contains zero data rows.",
                )
            else:
                add_result(
                    "Dataset",
                    f"{filename} contains data",
                    "PASS",
                    f"{len(rows)} rows detected.",
                )

        except Exception as exc:
            add_result(
                "Dataset",
                f"{filename} readable",
                "FAIL",
                f"Could not read CSV: {exc}",
            )


# =============================================================================
# 2. MATERIAL IDS
# =============================================================================

def validate_material_ids() -> None:
    for filename in UNIQUE_ID_DATASETS:
        path = DATA_DIR / filename

        if not path.exists():
            continue

        columns = get_columns(filename)

        if "material_id" not in columns:
            add_result(
                "Material IDs",
                f"{filename} material_id column",
                "FAIL",
                "material_id column is missing.",
            )
            continue

        rows = read_csv(filename)

        ids = [
            normalize_id(row.get("material_id"))
            for row in rows
        ]

        blank_ids = sum(
            1
            for material_id in ids
            if material_id == ""
        )

        if blank_ids:
            add_result(
                "Material IDs",
                f"{filename} missing material IDs",
                "FAIL",
                f"{blank_ids} blank material_id values detected.",
            )
        else:
            add_result(
                "Material IDs",
                f"{filename} material IDs present",
                "PASS",
                f"All {len(ids)} rows contain material_id.",
            )

        populated = [
            material_id
            for material_id in ids
            if material_id
        ]

        duplicate_count = (
            len(populated)
            - len(set(populated))
        )

        if duplicate_count:
            add_result(
                "Material IDs",
                f"{filename} duplicate material IDs",
                "FAIL",
                f"{duplicate_count} duplicate material IDs detected.",
            )
        else:
            add_result(
                "Material IDs",
                f"{filename} unique material IDs",
                "PASS",
                "No duplicate material_id values detected.",
            )


# =============================================================================
# 3. NUMERIC INTEGRITY
# =============================================================================

def looks_numeric_column(
    rows: list[dict],
    column: str,
) -> bool:
    inspected = 0
    numeric = 0

    for row in rows[:100]:
        value = row.get(column)

        if value is None or str(value).strip() == "":
            continue

        inspected += 1

        if safe_float(value) is not None:
            numeric += 1

    if inspected == 0:
        return False

    return numeric / inspected >= 0.90


def validate_numeric_integrity() -> None:
    for filename in KEY_DATASETS:
        path = DATA_DIR / filename

        if not path.exists():
            continue

        rows = read_csv(filename)

        if not rows:
            continue

        numeric_columns = [
            column
            for column in rows[0]
            if looks_numeric_column(
                rows,
                column,
            )
        ]

        invalid_locations = []

        for column in numeric_columns:
            for row_number, row in enumerate(
                rows,
                start=2,
            ):
                value = safe_float(
                    row.get(column)
                )

                if value is None:
                    continue

                if math.isinf(value):
                    invalid_locations.append(
                        f"{column} row {row_number}"
                    )

        if invalid_locations:
            preview = ", ".join(
                invalid_locations[:5]
            )

            add_result(
                "Numeric Integrity",
                f"{filename} finite numeric values",
                "FAIL",
                f"Infinite values detected: {preview}",
            )
        else:
            add_result(
                "Numeric Integrity",
                f"{filename} finite numeric values",
                "PASS",
                f"Checked {len(numeric_columns)} numeric columns.",
            )


# =============================================================================
# 4. SCORE RANGES
# =============================================================================

def is_score_like_column(column: str) -> bool:
    name = column.lower()

    keywords = [
        "score",
        "confidence",
        "risk",
        "probability",
    ]

    return any(
        keyword in name
        for keyword in keywords
    )


def is_signed_comparison_column(column: str) -> bool:
    """
    Return True for metrics where negative values are meaningful.

    Examples:
        score_minus_reference_median
        score_delta_vs_formula_search
    """

    name = column.lower()

    signed_keywords = [
        "_delta_",
        "delta_vs",
        "_minus_",
        "_difference_",
        "_diff_",
        "_margin_",
        "change_vs",
    ]

    return any(
        keyword in name
        for keyword in signed_keywords
    )


def validate_score_ranges() -> None:
    for filename in KEY_DATASETS:
        path = DATA_DIR / filename

        if not path.exists():
            continue

        rows = read_csv(filename)

        if not rows:
            continue

        columns = [
            column
            for column in rows[0]
            if is_score_like_column(column)
        ]

        for column in columns:
            values = []

            for row in rows:
                value = safe_float(
                    row.get(column)
                )

                if value is not None:
                    values.append(value)

            if not values:
                continue

            minimum = min(values)
            maximum = max(values)

            if is_signed_comparison_column(column):
                add_result(
                    "Score Range",
                    f"{filename}: {column}",
                    "PASS",
                    (
                        "Signed comparison metric. "
                        "Negative values are valid. "
                        f"Observed range: "
                        f"{minimum:.4f} to {maximum:.4f}"
                    ),
                )
                continue

            if minimum < 0 or maximum > 100:
                add_result(
                    "Score Range",
                    f"{filename}: {column}",
                    "FAIL",
                    (
                        "Values outside expected 0-100 range. "
                        f"Min={minimum:.4f}, "
                        f"Max={maximum:.4f}"
                    ),
                )
            else:
                add_result(
                    "Score Range",
                    f"{filename}: {column}",
                    "PASS",
                    (
                        f"Range valid. "
                        f"Min={minimum:.4f}, "
                        f"Max={maximum:.4f}"
                    ),
                )


# =============================================================================
# 5. RANK VALIDATION
# =============================================================================

def validate_rank_column(
    filename: str,
    rank_column: str,
) -> None:
    """
    Validate a complete ranking.

    Every row must contain an integer rank and ranks must form a complete
    unique sequence from 1 through N.
    """

    path = DATA_DIR / filename

    if not path.exists():
        return

    rows = read_csv(filename)

    if not rows:
        return

    if rank_column not in rows[0]:
        add_result(
            "Ranking",
            f"{filename} {rank_column}",
            "FAIL",
            f"{rank_column} column not present.",
        )
        return

    ranks = []
    invalid_ranks = 0

    for row in rows:
        value = safe_float(
            row.get(rank_column)
        )

        if value is None:
            invalid_ranks += 1
            continue

        if not value.is_integer():
            invalid_ranks += 1
            continue

        ranks.append(
            int(value)
        )

    if invalid_ranks:
        add_result(
            "Ranking",
            f"{filename} valid rank values",
            "FAIL",
            (
                f"{invalid_ranks} rows contain missing "
                "or non-integer rank values."
            ),
        )
        return

    expected = list(
        range(
            1,
            len(rows) + 1,
        )
    )

    actual = sorted(ranks)

    if actual == expected:
        add_result(
            "Ranking",
            f"{filename} complete ranking",
            "PASS",
            (
                f"Ranks form a complete unique sequence "
                f"from 1 to {len(rows)}."
            ),
        )
    else:
        missing = sorted(
            set(expected)
            - set(actual)
        )

        duplicate_count = (
            len(ranks)
            - len(set(ranks))
        )

        add_result(
            "Ranking",
            f"{filename} complete ranking",
            "FAIL",
            (
                f"Rank values do not form a complete unique "
                f"sequence from 1 to {len(rows)}. "
                f"Missing ranks: {missing[:10]}. "
                f"Duplicate rank count: {duplicate_count}."
            ),
        )


def validate_partial_rank_column(
    filename: str,
    rank_column: str,
) -> None:
    """
    Validate a ranking that intentionally applies only to part of a dataset.

    Blank ranks are allowed. All populated ranks must form a complete,
    unique integer sequence from 1 through N.
    """

    path = DATA_DIR / filename

    if not path.exists():
        return

    rows = read_csv(filename)

    if not rows:
        return

    if rank_column not in rows[0]:
        add_result(
            "Ranking",
            f"{filename} {rank_column}",
            "FAIL",
            f"{rank_column} column not present.",
        )
        return

    ranks = []
    invalid_ranks = 0
    blank_ranks = 0

    for row in rows:
        raw_value = row.get(rank_column)

        if raw_value is None or str(raw_value).strip() == "":
            blank_ranks += 1
            continue

        value = safe_float(raw_value)

        if value is None or not value.is_integer():
            invalid_ranks += 1
            continue

        ranks.append(
            int(value)
        )

    if invalid_ranks:
        add_result(
            "Ranking",
            f"{filename} {rank_column} valid values",
            "FAIL",
            (
                f"{invalid_ranks} populated rows contain "
                "non-integer rank values."
            ),
        )
        return

    if not ranks:
        add_result(
            "Ranking",
            f"{filename} {rank_column} populated",
            "FAIL",
            "No populated rank values detected.",
        )
        return

    expected = list(
        range(
            1,
            len(ranks) + 1,
        )
    )

    actual = sorted(ranks)

    if actual == expected:
        add_result(
            "Ranking",
            f"{filename} {rank_column} ranking",
            "PASS",
            (
                f"{len(ranks)} ranked rows form a complete "
                f"unique sequence from 1 to {len(ranks)}. "
                f"{blank_ranks} rows are intentionally "
                "outside this ranking track."
            ),
        )
    else:
        missing = sorted(
            set(expected)
            - set(actual)
        )

        duplicate_count = (
            len(ranks)
            - len(set(ranks))
        )

        add_result(
            "Ranking",
            f"{filename} {rank_column} ranking",
            "FAIL",
            (
                f"Populated ranks are not a complete unique "
                f"sequence from 1 to {len(ranks)}. "
                f"Missing ranks: {missing[:10]}. "
                f"Duplicate count: {duplicate_count}."
            ),
        )


def validate_score_order_by_rank(
    filename: str,
    rank_column: str,
    score_column: str,
) -> None:
    """
    Verify that scores decrease as rank worsens.

    Rows are sorted by explicit rank before comparison, so the physical
    order of rows in the CSV does not matter.
    """

    path = DATA_DIR / filename

    if not path.exists():
        return

    rows = read_csv(filename)

    if not rows:
        return

    missing_columns = []

    if rank_column not in rows[0]:
        missing_columns.append(rank_column)

    if score_column not in rows[0]:
        missing_columns.append(score_column)

    if missing_columns:
        add_result(
            "Ranking",
            f"{filename} rank-score relationship",
            "FAIL",
            "Missing columns: " + ", ".join(missing_columns),
        )
        return

    ranked_scores = []

    for row in rows:
        rank = safe_float(
            row.get(rank_column)
        )

        score = safe_float(
            row.get(score_column)
        )

        if rank is None or score is None:
            continue

        ranked_scores.append(
            (
                int(rank),
                score,
            )
        )

    ranked_scores.sort(
        key=lambda pair: pair[0]
    )

    scores = [
        score
        for _, score in ranked_scores
    ]

    descending = all(
        scores[index]
        >= scores[index + 1]
        for index in range(
            len(scores) - 1
        )
    )

    if descending:
        add_result(
            "Ranking",
            (
                f"{filename} "
                f"{score_column} agrees with ranking"
            ),
            "PASS",
            (
                f"{score_column} decreases consistently "
                f"with {rank_column}."
            ),
        )
    else:
        add_result(
            "Ranking",
            (
                f"{filename} "
                f"{score_column} agrees with ranking"
            ),
            "FAIL",
            (
                f"{score_column} does not decrease "
                f"consistently with {rank_column}."
            ),
        )


def validate_week5_ranking_tracks() -> None:
    """
    Validate the Week 5 multi-track ranking system.

    Week 5 contains:

    1. final_selection_rank
       Main candidates with sufficient electrochemical/structural evidence.

    2. discovery_review_rank
       Candidates without sufficient electrode data but retained for
       discovery review.

    3. BENCHMARK_ONLY
       Known reference cathodes retained as controls.
    """

    filename = "final_candidate_ranking.csv"
    path = DATA_DIR / filename

    if not path.exists():
        return

    rows = read_csv(filename)

    if not rows:
        return

    required_columns = [
        "final_selection_rank",
        "discovery_review_rank",
        "recommended_action",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in rows[0]
    ]

    if missing_columns:
        add_result(
            "Ranking",
            "Week 5 ranking-track schema",
            "FAIL",
            "Missing columns: " + ", ".join(missing_columns),
        )
        return

    final_rank_count = 0
    discovery_rank_count = 0
    benchmark_only_count = 0
    conflicting_rows = 0
    unclassified_rows = 0

    for row in rows:
        final_rank = safe_float(
            row.get("final_selection_rank")
        )

        discovery_rank = safe_float(
            row.get("discovery_review_rank")
        )

        action = str(
            row.get(
                "recommended_action",
                "",
            )
        ).strip()

        has_final_rank = final_rank is not None
        has_discovery_rank = discovery_rank is not None

        if has_final_rank:
            final_rank_count += 1

        if has_discovery_rank:
            discovery_rank_count += 1

        if action == "BENCHMARK_ONLY":
            benchmark_only_count += 1

        if (
            has_final_rank
            and has_discovery_rank
        ):
            conflicting_rows += 1

        if (
            not has_final_rank
            and not has_discovery_rank
            and action != "BENCHMARK_ONLY"
        ):
            unclassified_rows += 1

    if conflicting_rows:
        add_result(
            "Ranking",
            "Week 5 mutually exclusive ranking tracks",
            "FAIL",
            (
                f"{conflicting_rows} materials appear in both "
                "final_selection_rank and discovery_review_rank."
            ),
        )
    else:
        add_result(
            "Ranking",
            "Week 5 mutually exclusive ranking tracks",
            "PASS",
            "No candidate appears in both Week 5 ranking tracks.",
        )

    if unclassified_rows:
        add_result(
            "Ranking",
            "Week 5 candidate role coverage",
            "FAIL",
            (
                f"{unclassified_rows} materials have neither "
                "a final-selection rank, discovery-review rank, "
                "nor BENCHMARK_ONLY role."
            ),
        )
    else:
        add_result(
            "Ranking",
            "Week 5 candidate role coverage",
            "PASS",
            (
                f"All {len(rows)} materials belong to a "
                "recognized Week 5 role."
            ),
        )

    total_classified = (
        final_rank_count
        + discovery_rank_count
        + benchmark_only_count
    )

    if total_classified == len(rows):
        add_result(
            "Ranking",
            "Week 5 ranking-track population",
            "PASS",
            (
                f"Final selection: {final_rank_count}; "
                f"discovery review: {discovery_rank_count}; "
                f"benchmark controls: {benchmark_only_count}; "
                f"total: {len(rows)}."
            ),
        )
    else:
        add_result(
            "Ranking",
            "Week 5 ranking-track population",
            "FAIL",
            (
                f"Ranking-role counts total {total_classified}, "
                f"but dataset contains {len(rows)} rows."
            ),
        )


def validate_rankings() -> None:
    # ---------------------------------------------------------------------
    # WEEK 5
    #
    # Week 5 intentionally contains two ranking tracks plus benchmark
    # controls.
    # ---------------------------------------------------------------------

    validate_partial_rank_column(
        "final_candidate_ranking.csv",
        "final_selection_rank",
    )

    validate_partial_rank_column(
        "final_candidate_ranking.csv",
        "discovery_review_rank",
    )

    validate_week5_ranking_tracks()

    # ---------------------------------------------------------------------
    # WEEK 7
    #
    # Week 7 contains the unified final research ranking.
    # ---------------------------------------------------------------------

    validate_rank_column(
        "week7_final_ranking.csv",
        "week7_final_rank",
    )

    validate_score_order_by_rank(
        "week7_final_ranking.csv",
        "week7_final_rank",
        "week7_final_score",
    )


# =============================================================================
# 6. CROSS-STAGE TRACEABILITY
# =============================================================================

def validate_subset(
    child_file: str,
    parent_file: str,
    description: str,
    allow_warning: bool = False,
) -> None:
    child_path = DATA_DIR / child_file
    parent_path = DATA_DIR / parent_file

    if (
        not child_path.exists()
        or not parent_path.exists()
    ):
        return

    child_ids = get_material_ids(
        child_file
    )

    parent_ids = get_material_ids(
        parent_file
    )

    if not child_ids:
        add_result(
            "Traceability",
            description,
            "FAIL",
            f"No material IDs found in {child_file}.",
        )
        return

    missing = (
        child_ids
        - parent_ids
    )

    if not missing:
        add_result(
            "Traceability",
            description,
            "PASS",
            (
                f"All {len(child_ids)} candidates in "
                f"{child_file} trace to {parent_file}."
            ),
        )
        return

    status = (
        "WARN"
        if allow_warning
        else "FAIL"
    )

    preview = ", ".join(
        sorted(missing)[:5]
    )

    add_result(
        "Traceability",
        description,
        status,
        (
            f"{len(missing)} candidates do not appear "
            f"in {parent_file}. Examples: {preview}"
        ),
    )


def validate_cross_stage_traceability() -> None:
    validate_subset(
        "ranked_materials.csv",
        "materials.csv",
        (
            "Ranked materials trace to "
            "raw candidate dataset"
        ),
    )

    validate_subset(
        "screened_materials.csv",
        "ranked_materials.csv",
        (
            "Screened materials trace to "
            "thermodynamic ranking"
        ),
    )

    validate_subset(
        "electrochemical_evaluation.csv",
        "screened_materials.csv",
        (
            "Electrochemical candidates trace "
            "to screened materials"
        ),
        allow_warning=True,
    )

    validate_subset(
        "week5_shortlist.csv",
        "final_candidate_ranking.csv",
        (
            "Week 5 shortlist traces to "
            "Week 5 final candidate ranking"
        ),
    )

    validate_subset(
        "week6_final_ranking.csv",
        "week6_resource_assessment.csv",
        (
            "Week 6 final ranking traces to "
            "Week 6 validated candidate population"
        ),
    )

    validate_subset(
        "week6_research_shortlist.csv",
        "week6_final_ranking.csv",
        (
            "Week 6 research shortlist traces "
            "to Week 6 final ranking"
        ),
    )

    validate_subset(
        "week7_final_ranking.csv",
        "week6_final_ranking.csv",
        (
            "Week 7 final ranking traces to "
            "Week 6 final ranking"
        ),
    )


# =============================================================================
# 7. WEEK 7 FINAL DATASET
# =============================================================================

def validate_week7_final_dataset() -> None:
    filename = "week7_final_ranking.csv"
    path = DATA_DIR / filename

    if not path.exists():
        return

    rows = read_csv(filename)

    required_columns = [
        "material_id",
        "formula",
        "final_recommendation",
        "research_potential_score",
        "evidence_confidence_score",
        "total_risk_score",
        "week7_final_score",
    ]

    actual_columns = set(
        rows[0].keys()
        if rows
        else []
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in actual_columns
    ]

    if missing_columns:
        add_result(
            "Week 7 Final",
            "Required final recommendation columns",
            "FAIL",
            "Missing columns: " + ", ".join(missing_columns),
        )
    else:
        add_result(
            "Week 7 Final",
            "Required final recommendation columns",
            "PASS",
            (
                "All required Week 7 recommendation "
                "columns are present."
            ),
        )

    if rows:
        recommendation_values = {
            str(
                row.get(
                    "final_recommendation",
                    "",
                )
            ).strip()
            for row in rows
        }

        recommendation_values.discard("")

        if recommendation_values:
            add_result(
                "Week 7 Final",
                "Final recommendation roles",
                "PASS",
                (
                    f"{len(recommendation_values)} recommendation "
                    f"categories detected: "
                    + ", ".join(
                        sorted(
                            recommendation_values
                        )
                    )
                ),
            )
        else:
            add_result(
                "Week 7 Final",
                "Final recommendation roles",
                "FAIL",
                "No final recommendation categories detected.",
            )


# =============================================================================
# SAVE VALIDATION RESULTS
# =============================================================================

def save_validation_results() -> None:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            "category",
            "check",
            "status",
            "details",
        ])

        for result in RESULTS:
            writer.writerow([
                result.category,
                result.check,
                result.status,
                result.details,
            ])


# =============================================================================
# REPORT
# =============================================================================

def build_report() -> str:
    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    passes = sum(
        result.status == "PASS"
        for result in RESULTS
    )

    warnings = sum(
        result.status == "WARN"
        for result in RESULTS
    )

    failures = sum(
        result.status == "FAIL"
        for result in RESULTS
    )

    overall_status = (
        "VALID"
        if failures == 0
        else "REVIEW REQUIRED"
    )

    lines = [
        "# MAPPS-Lite Week 8 Pipeline Validation",
        "",
        f"Generated: {timestamp}",
        "",
        "## Overall Status",
        "",
        f"**Pipeline status: {overall_status}**",
        "",
        f"- Passed checks: {passes}",
        f"- Warnings: {warnings}",
        f"- Failed checks: {failures}",
        f"- Total checks: {len(RESULTS)}",
        "",
        "## Validation Results",
        "",
        "| Category | Check | Status | Details |",
        "|---|---|---|---|",
    ]

    for result in RESULTS:
        details = result.details.replace(
            "|",
            "/",
        )

        lines.append(
            f"| {result.category} "
            f"| {result.check} "
            f"| {result.status} "
            f"| {details} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
    ])

    if failures == 0:
        lines.extend([
            (
                "No pipeline integrity failures were detected. "
                "The major MAPPS-Lite datasets are internally "
                "consistent and the final Week 7 recommendations "
                "remain traceable through the preceding research stages."
            ),
            "",
            (
                "Signed comparison metrics such as score deltas and "
                "differences from reference medians may legitimately "
                "contain negative values because they represent relative "
                "differences rather than bounded scores."
            ),
            "",
            (
                "Week 5 uses multiple candidate roles: a main final "
                "selection ranking, a discovery-review ranking, and "
                "benchmark-only reference controls. These ranking tracks "
                "are validated independently."
            ),
            "",
            (
                "Week 7 is treated as the unified final MAPPS-Lite "
                "ranking and is validated directly against "
                "week7_final_score."
            ),
        ])
    else:
        lines.append(
            (
                "One or more integrity failures were detected. "
                "These checks should be reviewed before the "
                "MAPPS-Lite v1.0 release is finalized."
            )
        )

    lines.extend([
        "",
        "## Validation Scope",
        "",
        "- dataset existence and readability",
        "- non-empty research outputs",
        "- material identifier completeness",
        "- duplicate material identifiers",
        "- finite numeric values",
        "- bounded score ranges",
        "- signed comparison metrics",
        "- Week 5 multi-track ranking integrity",
        "- Week 7 unified rank integrity",
        "- final score/rank consistency",
        "- cross-stage candidate traceability",
        "- Week 7 final recommendation schema",
        "",
    ])

    return "\n".join(lines)


def save_report() -> None:
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        build_report(),
        encoding="utf-8",
    )


# =============================================================================
# CONSOLE SUMMARY
# =============================================================================

def print_summary() -> None:
    passes = sum(
        result.status == "PASS"
        for result in RESULTS
    )

    warnings = sum(
        result.status == "WARN"
        for result in RESULTS
    )

    failures = sum(
        result.status == "FAIL"
        for result in RESULTS
    )

    print()
    print("=" * 80)
    print("MAPPS-LITE WEEK 8")
    print("FINAL PIPELINE INTEGRITY VALIDATION")
    print("=" * 80)

    print()
    print("[1/6] Validating datasets...")
    print("[2/6] Validating material identifiers...")
    print("[3/6] Validating numeric integrity...")
    print("[4/6] Validating score and ranking behavior...")
    print("[5/6] Validating cross-stage traceability...")
    print("[6/6] Validating final Week 7 recommendation...")

    print()
    print("Validation summary:")
    print()
    print(f"  PASS: {passes}")
    print(f"  WARN: {warnings}")
    print(f"  FAIL: {failures}")
    print(f"  TOTAL: {len(RESULTS)}")

    print()
    print(f"Saved: {RESULTS_PATH}")
    print(f"Saved: {REPORT_PATH}")

    print()

    if failures == 0:
        print("PIPELINE STATUS: VALID")
    else:
        print("PIPELINE STATUS: REVIEW REQUIRED")

    if warnings:
        print()
        print(
            "Warnings are non-critical but should be reviewed "
            "before the final v1.0 release."
        )

    print()
    print("=" * 80)
    print("WEEK 8.2 COMPLETE")
    print("=" * 80)


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    validate_dataset_presence()
    validate_material_ids()
    validate_numeric_integrity()
    validate_score_ranges()
    validate_rankings()
    validate_cross_stage_traceability()
    validate_week7_final_dataset()

    save_validation_results()
    save_report()

    print_summary()


if __name__ == "__main__":
    main()