"""
MAPPS-Lite Main Orchestrator

Available modes:

Full pipeline:
    python src/main.py

Skip Materials Project search:
    python src/main.py --skip-search

Analysis only:
    python src/main.py --analysis-only
"""

import argparse
from pathlib import Path

from materials_search import (
    run_search_pipeline,
)

from rank_materials import (
    run_ranking_pipeline,
)

from analyze_materials import (
    run_analysis_pipeline,
)

from validate_pipeline import (
    run_pipeline_validation,
)

from run_summary import (
    save_run_summary,
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

RANKED_MATERIALS_FILE = (
    PROJECT_ROOT
    / "data"
    / "ranked_materials.csv"
)


# ---------------------------------------------------------
# Command-line arguments
# ---------------------------------------------------------

def parse_arguments():
    """
    Read command-line options.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Run the MAPPS-Lite materials "
            "discovery pipeline."
        )
    )

    mode_group = (
        parser.add_mutually_exclusive_group()
    )

    mode_group.add_argument(
        "--skip-search",
        action="store_true",
        help=(
            "Reuse data/materials.csv and run "
            "ranking and analysis."
        ),
    )

    mode_group.add_argument(
        "--analysis-only",
        action="store_true",
        help=(
            "Reuse data/ranked_materials.csv "
            "and run screening/reporting only."
        ),
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Display helpers
# ---------------------------------------------------------

def print_pipeline_header():
    """
    Print the main MAPPS-Lite heading.
    """

    print()
    print("=" * 60)
    print(
        "MAPPS-Lite Materials Discovery Pipeline"
    )
    print("=" * 60)
    print()


def print_stage_header(
    stage_number,
    stage_name,
):
    """
    Print a pipeline stage heading.
    """

    print("=" * 60)

    print(
        f"STAGE {stage_number}: "
        f"{stage_name}"
    )

    print("=" * 60)
    print()


def print_generated_files():
    """
    Print the primary pipeline output files.
    """

    print(
        "Current pipeline files:"
    )

    print()

    print(
        "  data/materials.csv"
    )

    print(
        "  data/ranked_materials.csv"
    )

    print(
        "  data/screened_materials.csv"
    )

    print(
        "  reports/top_materials_report.md"
    )

    print(
        "  reports/run_summary.md"
    )

    print()


# ---------------------------------------------------------
# Input validation
# ---------------------------------------------------------

def require_file(
    file_path,
    required_command,
):
    """
    Verify that a file required by a skipped stage exists.
    """

    if not file_path.exists():

        raise FileNotFoundError(
            "Required file was not found:\n"
            f"{file_path}\n\n"
            "Run this command first:\n"
            f"{required_command}"
        )


# ---------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------

def run_full_pipeline():
    """
    Run search, ranking, analysis, and reporting.
    """

    print_stage_header(
        1,
        "MATERIAL SEARCH",
    )

    materials = (
        run_search_pipeline()
    )

    print()

    print(
        "Search stage complete: "
        f"{len(materials)} "
        "candidate materials."
    )

    print()

    print_stage_header(
        2,
        "MATERIAL RANKING",
    )

    ranked_materials = (
        run_ranking_pipeline()
    )

    print()

    print(
        "Ranking stage complete: "
        f"{len(ranked_materials)} "
        "materials ranked."
    )

    print()

    print_stage_header(
        3,
        "MATERIAL SCREENING",
    )

    screened_materials = (
        run_analysis_pipeline()
    )

    print()

    print(
        "Screening stage complete: "
        f"{len(screened_materials)} "
        "materials screened."
    )

    return screened_materials


# ---------------------------------------------------------
# Skip-search pipeline
# ---------------------------------------------------------

def run_without_search():
    """
    Reuse materials.csv and run ranking + analysis.
    """

    require_file(
        MATERIALS_FILE,
        "python src/main.py",
    )

    print(
        "Search stage skipped."
    )

    print(
        "Using existing file: "
        f"{MATERIALS_FILE}"
    )

    print()

    print_stage_header(
        2,
        "MATERIAL RANKING",
    )

    ranked_materials = (
        run_ranking_pipeline()
    )

    print()

    print(
        "Ranking stage complete: "
        f"{len(ranked_materials)} "
        "materials ranked."
    )

    print()

    print_stage_header(
        3,
        "MATERIAL SCREENING",
    )

    screened_materials = (
        run_analysis_pipeline()
    )

    print()

    print(
        "Screening stage complete: "
        f"{len(screened_materials)} "
        "materials screened."
    )

    return screened_materials


# ---------------------------------------------------------
# Analysis-only pipeline
# ---------------------------------------------------------

def run_analysis_only():
    """
    Reuse ranked_materials.csv and run analysis only.
    """

    require_file(
        RANKED_MATERIALS_FILE,
        "python src/main.py --skip-search",
    )

    print(
        "Search and ranking stages skipped."
    )

    print(
        "Using existing file: "
        f"{RANKED_MATERIALS_FILE}"
    )

    print()

    print_stage_header(
        3,
        "MATERIAL SCREENING",
    )

    screened_materials = (
        run_analysis_pipeline()
    )

    print()

    print(
        "Screening stage complete: "
        f"{len(screened_materials)} "
        "materials screened."
    )

    return screened_materials


# ---------------------------------------------------------
# MAPPS-Lite orchestrator
# ---------------------------------------------------------

def run_mapps_pipeline(
    skip_search=False,
    analysis_only=False,
):
    """
    Select and run the requested MAPPS-Lite workflow.
    """

    print_pipeline_header()

    if analysis_only:

        selected_mode = (
            "ANALYSIS ONLY"
        )

        print(
            f"Pipeline mode: "
            f"{selected_mode}"
        )

        print()

        screened_materials = (
            run_analysis_only()
        )

    elif skip_search:

        selected_mode = (
            "SKIP SEARCH"
        )

        print(
            f"Pipeline mode: "
            f"{selected_mode}"
        )

        print()

        screened_materials = (
            run_without_search()
        )

    else:

        selected_mode = (
            "FULL PIPELINE"
        )

        print(
            f"Pipeline mode: "
            f"{selected_mode}"
        )

        print()

        screened_materials = (
            run_full_pipeline()
        )

    # -----------------------------------------------------
    # Stage 4: Validation
    # -----------------------------------------------------

    print()

    print_stage_header(
        4,
        "PIPELINE VALIDATION",
    )

    validation_results = (
        run_pipeline_validation()
    )

    print(
        f"{len(validation_results)} "
        "validation checks passed."
    )

    # -----------------------------------------------------
    # Stage 5: Run summary
    # -----------------------------------------------------

    print()

    print_stage_header(
        5,
        "RUN SUMMARY",
    )

    save_run_summary(
        selected_mode
    )

    # -----------------------------------------------------
    # Finished
    # -----------------------------------------------------

    print()

    print("=" * 60)

    print(
        "MAPPS-Lite PIPELINE COMPLETE"
    )

    print("=" * 60)

    print()

    print(
        f"Completed mode: "
        f"{selected_mode}"
    )

    print()

    print_generated_files()

    return screened_materials


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():
    """
    Parse arguments and start MAPPS-Lite.
    """

    arguments = (
        parse_arguments()
    )

    try:

        run_mapps_pipeline(
            skip_search=(
                arguments.skip_search
            ),

            analysis_only=(
                arguments.analysis_only
            ),
        )

    except KeyboardInterrupt:

        print()

        print(
            "MAPPS-Lite pipeline "
            "stopped by user."
        )

    except Exception as error:

        print()

        print("=" * 60)

        print(
            "MAPPS-Lite PIPELINE FAILED"
        )

        print("=" * 60)

        print()

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        print()

        raise


if __name__ == "__main__":
    main()