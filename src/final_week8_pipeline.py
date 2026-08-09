"""
MAPPS-Lite Week 8
Final Pipeline Integration

This script provides a single entry point for the MAPPS-Lite v1.0 pipeline.

Default behavior:
    - Does NOT rerun expensive Materials Project searches.
    - Inspects the outputs already produced during Weeks 1-7.
    - Builds a reproducibility manifest.
    - Generates a Week 8 pipeline-integration report.

Optional behavior:
    python src/final_week8_pipeline.py --rebuild

    Attempts to rerun the known MAPPS-Lite pipeline scripts in chronological
    order before generating the final integration report.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# =============================================================================
# PROJECT PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

MANIFEST_PATH = DATA_DIR / "week8_pipeline_manifest.csv"
REPORT_PATH = REPORTS_DIR / "week8_pipeline_integration.md"


# =============================================================================
# ARTIFACT DEFINITIONS
# =============================================================================

@dataclass
class Artifact:
    week: str
    stage: str
    relative_path: str
    required: bool = True


ARTIFACTS = [
    # -------------------------------------------------------------------------
    # Weeks 1-4: Materials discovery and thermodynamic screening
    # -------------------------------------------------------------------------
    Artifact(
        "Weeks 1-4",
        "Materials Project candidate dataset",
        "data/materials.csv",
    ),
    Artifact(
        "Weeks 1-4",
        "Thermodynamic ranking",
        "data/ranked_materials.csv",
    ),
    Artifact(
        "Weeks 1-4",
        "Screened candidate dataset",
        "data/screened_materials.csv",
    ),
    Artifact(
        "Weeks 1-4",
        "Top-materials report",
        "reports/top_materials_report.md",
    ),

    # -------------------------------------------------------------------------
    # Week 5: Electrochemical and structural validation
    # -------------------------------------------------------------------------
    Artifact(
        "Week 5",
        "Electrochemical evaluation",
        "data/electrochemical_evaluation.csv",
    ),
    Artifact(
        "Week 5",
        "Reference cathode benchmarks",
        "data/cathode_benchmarks.csv",
    ),
    Artifact(
        "Week 5",
        "Benchmark comparison",
        "data/benchmark_comparison.csv",
    ),
    Artifact(
        "Week 5",
        "Exact structure validation",
        "data/exact_structure_validation.csv",
    ),
    Artifact(
        "Week 5",
        "Final candidate ranking",
        "data/final_candidate_ranking.csv",
    ),
    Artifact(
        "Week 5",
        "Week 5 shortlist",
        "data/week5_shortlist.csv",
    ),
    Artifact(
        "Week 5",
        "Week 5 progress report",
        "reports/week5_progress.md",
    ),

    # -------------------------------------------------------------------------
    # Week 6: Scientific validation
    # -------------------------------------------------------------------------
    Artifact(
        "Week 6",
        "Research shortlist",
        "data/week6_research_shortlist.csv",
    ),
    Artifact(
        "Week 6",
        "Literature validation",
        "data/week6_literature_validation.csv",
    ),
    Artifact(
        "Week 6",
        "Synthesis feasibility",
        "data/week6_synthesis_feasibility.csv",
    ),
    Artifact(
        "Week 6",
        "Transport evaluation",
        "data/week6_transport_evaluation.csv",
    ),
    Artifact(
        "Week 6",
        "Resource sustainability assessment",
        "data/week6_resource_assessment.csv",
    ),
    Artifact(
        "Week 6",
        "Provenance validation",
        "data/week6_provenance_validation.csv",
    ),
    Artifact(
        "Week 6",
        "Final Week 6 ranking",
        "data/week6_final_ranking.csv",
    ),
    Artifact(
        "Week 6",
        "Final selection report",
        "reports/week6_final_selection.md",
    ),
    Artifact(
        "Week 6",
        "Week 6 progress report",
        "reports/week6_progress.md",
    ),

    # -------------------------------------------------------------------------
    # Week 7: Evidence-confidence and final recommendation
    # -------------------------------------------------------------------------
    Artifact(
        "Week 7",
        "Final Week 7 ranking",
        "data/week7_final_ranking.csv",
    ),
    Artifact(
        "Week 7",
        "Final research recommendation",
        "reports/week7_final_recommendation.md",
    ),
    Artifact(
        "Week 7",
        "Week 7 progress report",
        "reports/week7_progress.md",
    ),
]


# =============================================================================
# PIPELINE SCRIPT DEFINITIONS
# =============================================================================

@dataclass
class PipelineStage:
    name: str
    script_candidates: tuple[str, ...]
    optional: bool = False


PIPELINE_STAGES = [
    PipelineStage(
        "Materials search",
        ("materials_search.py",),
    ),
    PipelineStage(
        "Thermodynamic ranking",
        ("rank_materials.py",),
    ),
    PipelineStage(
        "Candidate analysis",
        ("analyze_materials.py",),
    ),
    PipelineStage(
        "Electrochemical evaluation",
        ("evaluate_electrochemistry.py",),
    ),
    PipelineStage(
        "Reference cathode benchmarking",
        ("benchmark_cathodes.py",),
    ),
    PipelineStage(
        "Exact structure validation",
        ("validate_electrode_structures.py",),
    ),
    PipelineStage(
        "Week 5 final candidate selection",
        ("final_candidate_selection.py",),
    ),
    PipelineStage(
        "Battery literature validation",
        (
            "validate_battery_literature.py",
            "validate_literature.py",
        ),
    ),
    PipelineStage(
        "Synthesis feasibility assessment",
        ("assess_synthesis_feasibility.py",),
    ),
    PipelineStage(
        "Transport property evaluation",
        ("evaluate_transport_properties.py",),
    ),
    PipelineStage(
        "Resource sustainability assessment",
        ("assess_resource_sustainability.py",),
    ),
    PipelineStage(
        "Provenance validation",
        (
            "validate_provenance.py",
            "validate_candidate_provenance.py",
            "validate_material_provenance.py",
        ),
        optional=True,
    ),
    PipelineStage(
        "Week 6 final selection",
        ("final_week6_selection.py",),
    ),
    PipelineStage(
        "Week 7 evidence-confidence evaluation",
        (
            "evaluate_evidence_confidence.py",
            "assess_evidence_confidence.py",
            "week7_evidence_confidence.py",
        ),
        optional=True,
    ),
    PipelineStage(
        "Week 7 final research recommendation",
        ("final_week7_recommendation.py",),
    ),
]


# =============================================================================
# FILE UTILITIES
# =============================================================================

def sha256_file(path: Path) -> str:
    """Return SHA-256 hash for reproducibility tracking."""
    hasher = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def count_csv_rows(path: Path) -> int | None:
    """
    Count data rows in a CSV file, excluding the header.

    Returns None if the file is not a CSV or cannot be read.
    """
    if path.suffix.lower() != ".csv":
        return None

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.reader(file)

            try:
                next(reader)
            except StopIteration:
                return 0

            return sum(1 for _ in reader)

    except Exception:
        return None


def format_bytes(size: int) -> str:
    """Return a human-readable file size."""
    if size < 1024:
        return f"{size} B"

    if size < 1024 ** 2:
        return f"{size / 1024:.1f} KB"

    return f"{size / (1024 ** 2):.1f} MB"


# =============================================================================
# PIPELINE REBUILD
# =============================================================================

def locate_script(stage: PipelineStage) -> Path | None:
    """Find the first available script for a pipeline stage."""
    for script_name in stage.script_candidates:
        candidate = SRC_DIR / script_name

        if candidate.exists():
            return candidate

    return None


def run_pipeline_stage(stage_number: int, stage: PipelineStage) -> bool:
    """Run one existing MAPPS-Lite pipeline script."""
    script = locate_script(stage)

    print()
    print("-" * 80)
    print(f"STAGE {stage_number}: {stage.name}")
    print("-" * 80)

    if script is None:
        if stage.optional:
            print("[SKIP] No matching script found.")
            return True

        print("[ERROR] Required pipeline script not found.")
        print("Checked:")

        for candidate in stage.script_candidates:
            print(f"  - src/{candidate}")

        return False

    print(f"Running: {script.relative_to(PROJECT_ROOT)}")
    print()

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        print()
        print(
            f"[ERROR] Stage failed with exit code "
            f"{result.returncode}: {stage.name}"
        )
        return False

    print()
    print(f"[PASS] {stage.name}")

    return True


def rebuild_pipeline() -> bool:
    """
    Attempt to rerun the existing MAPPS-Lite pipeline from beginning to end.

    This is intentionally optional because the Materials Project search can be
    comparatively expensive and may require API access.
    """
    print()
    print("=" * 80)
    print("MAPPS-LITE WEEK 8")
    print("FULL PIPELINE REBUILD")
    print("=" * 80)

    for index, stage in enumerate(PIPELINE_STAGES, start=1):
        success = run_pipeline_stage(index, stage)

        if not success:
            print()
            print("=" * 80)
            print("PIPELINE REBUILD STOPPED")
            print("=" * 80)
            return False

    print()
    print("=" * 80)
    print("PIPELINE REBUILD COMPLETE")
    print("=" * 80)

    return True


# =============================================================================
# ARTIFACT INSPECTION
# =============================================================================

def inspect_artifacts() -> list[dict]:
    """Inspect the major research artifacts generated during Weeks 1-7."""
    records = []

    for artifact in ARTIFACTS:
        path = PROJECT_ROOT / artifact.relative_path
        exists = path.exists()

        record = {
            "week": artifact.week,
            "stage": artifact.stage,
            "artifact": artifact.relative_path,
            "required": artifact.required,
            "exists": exists,
            "status": "PASS" if exists else "MISSING",
            "rows": "",
            "size_bytes": "",
            "sha256": "",
        }

        if exists:
            record["size_bytes"] = path.stat().st_size
            record["sha256"] = sha256_file(path)

            row_count = count_csv_rows(path)

            if row_count is not None:
                record["rows"] = row_count

        records.append(record)

    return records


def find_week7_confidence_files() -> list[Path]:
    """
    Find Week 7 confidence/evidence datasets even if their exact filename
    changed during development.
    """
    patterns = [
        "week7*confidence*.csv",
        "week7*evidence*.csv",
    ]

    matches = []

    for pattern in patterns:
        for path in DATA_DIR.glob(pattern):
            if path.name != "week7_final_ranking.csv" and path not in matches:
                matches.append(path)

    return sorted(matches)


# =============================================================================
# MANIFEST
# =============================================================================

def save_manifest(records: list[dict]) -> None:
    """Save a machine-readable manifest of major pipeline artifacts."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fields = [
        "week",
        "stage",
        "artifact",
        "required",
        "exists",
        "status",
        "rows",
        "size_bytes",
        "sha256",
    ]

    with MANIFEST_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


# =============================================================================
# REPORT GENERATION
# =============================================================================

def build_report(records: list[dict]) -> str:
    """Generate the Week 8 pipeline-integration report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    required_records = [
        record for record in records
        if record["required"]
    ]

    passed = sum(
        1 for record in required_records
        if record["exists"]
    )

    total = len(required_records)
    missing = total - passed

    if missing == 0:
        overall_status = "INTEGRATED"
    else:
        overall_status = "INCOMPLETE"

    lines = [
        "# MAPPS-Lite Week 8 Pipeline Integration",
        "",
        f"Generated: {timestamp}",
        "",
        "## Final Integration Status",
        "",
        f"**Pipeline status: {overall_status}**",
        "",
        f"- Required artifacts found: {passed}/{total}",
        f"- Required artifacts missing: {missing}",
        "",
        "## Pipeline Architecture",
        "",
        "```text",
        "Materials Project",
        "       |",
        "       v",
        "Candidate Search",
        "       |",
        "       v",
        "Thermodynamic Ranking",
        "       |",
        "       v",
        "Stability Screening",
        "       |",
        "       v",
        "Electrochemical Evaluation",
        "       |",
        "       v",
        "Reference Cathode Benchmarking",
        "       |",
        "       v",
        "Exact Structure Validation",
        "       |",
        "       v",
        "Research Shortlist",
        "       |",
        "       v",
        "Literature Validation",
        "       |",
        "       v",
        "Synthesis Feasibility",
        "       |",
        "       v",
        "Transport Evaluation",
        "       |",
        "       v",
        "Resource Sustainability",
        "       |",
        "       v",
        "Provenance Validation",
        "       |",
        "       v",
        "Evidence Confidence",
        "       |",
        "       v",
        "FINAL RESEARCH RECOMMENDATION",
        "```",
        "",
        "## Artifact Manifest",
        "",
        "| Week | Stage | Artifact | Status | Rows | Size |",
        "|---|---|---|---|---:|---:|",
    ]

    for record in records:
        path = PROJECT_ROOT / record["artifact"]

        if record["exists"]:
            size = format_bytes(path.stat().st_size)
            rows = (
                str(record["rows"])
                if record["rows"] != ""
                else "-"
            )
        else:
            size = "-"
            rows = "-"

        lines.append(
            f"| {record['week']} "
            f"| {record['stage']} "
            f"| `{record['artifact']}` "
            f"| {record['status']} "
            f"| {rows} "
            f"| {size} |"
        )

    confidence_files = find_week7_confidence_files()

    lines.extend([
        "",
        "## Week 7 Evidence Files",
        "",
    ])

    if confidence_files:
        for path in confidence_files:
            relative = path.relative_to(PROJECT_ROOT)
            rows = count_csv_rows(path)

            lines.append(
                f"- `{relative}`"
                + (
                    f" ({rows} rows)"
                    if rows is not None
                    else ""
                )
            )
    else:
        lines.append(
            "- No additional Week 7 evidence-confidence CSV was "
            "automatically detected."
        )

    missing_records = [
        record for record in required_records
        if not record["exists"]
    ]

    lines.extend([
        "",
        "## Missing Required Artifacts",
        "",
    ])

    if not missing_records:
        lines.append(
            "All required Week 1-7 pipeline artifacts were detected."
        )
    else:
        for record in missing_records:
            lines.append(
                f"- `{record['artifact']}` "
                f"({record['stage']})"
            )

    lines.extend([
        "",
        "## Reproducibility",
        "",
        (
            "A SHA-256 checksum for every detected major artifact is stored "
            "in `data/week8_pipeline_manifest.csv`."
        ),
        "",
        (
            "These hashes provide a reproducible snapshot of the exact "
            "datasets and reports used at the start of Week 8."
        ),
        "",
        "## Week 8 Interpretation",
        "",
        (
            "Weeks 1-7 produced the scientific screening and validation "
            "results. Week 8 integrates those results into a final "
            "reproducible MAPPS-Lite v1.0 research pipeline."
        ),
        "",
        (
            "The next step is final pipeline integrity validation, which "
            "will test dataset consistency, ranking correctness, duplicate "
            "material IDs, score ranges, missing values, and cross-stage "
            "candidate continuity."
        ),
        "",
    ])

    return "\n".join(lines)


def save_report(report: str) -> None:
    """Save the Week 8 integration report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )


# =============================================================================
# CONSOLE SUMMARY
# =============================================================================

def print_artifact_summary(records: list[dict]) -> None:
    """Print a concise pipeline status summary."""
    required = [
        record for record in records
        if record["required"]
    ]

    passed = sum(
        1 for record in required
        if record["exists"]
    )

    missing = [
        record for record in required
        if not record["exists"]
    ]

    print()
    print("=" * 80)
    print("MAPPS-LITE WEEK 8")
    print("FINAL PIPELINE INTEGRATION")
    print("=" * 80)

    print()
    print("[1/4] Inspecting Weeks 1-7 research artifacts...")
    print(f"Found {passed}/{len(required)} required artifacts.")

    print()
    print("[2/4] Building reproducibility manifest...")
    print(f"Saved: {MANIFEST_PATH}")

    print()
    print("[3/4] Generating pipeline integration report...")
    print(f"Saved: {REPORT_PATH}")

    print()
    print("[4/4] Final integration status...")

    if not missing:
        print()
        print("All required pipeline artifacts were detected.")
        print()
        print("PIPELINE STATUS: INTEGRATED")
    else:
        print()
        print("Missing required artifacts:")

        for record in missing:
            print(f"  - {record['artifact']}")

        print()
        print("PIPELINE STATUS: INCOMPLETE")

    print()
    print("=" * 80)
    print("WEEK 8.1 COMPLETE")
    print("=" * 80)


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Integrate and inspect the complete MAPPS-Lite v1.0 pipeline."
        )
    )

    parser.add_argument(
        "--rebuild",
        action="store_true",
        help=(
            "Rerun known pipeline scripts before generating the "
            "integration manifest."
        ),
    )

    args = parser.parse_args()

    if args.rebuild:
        rebuild_success = rebuild_pipeline()

        if not rebuild_success:
            print()
            print(
                "The rebuild did not complete, but Week 8 will still inspect "
                "the artifacts currently available."
            )

    records = inspect_artifacts()

    save_manifest(records)

    report = build_report(records)
    save_report(report)

    print_artifact_summary(records)


if __name__ == "__main__":
    main()