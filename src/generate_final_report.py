"""
MAPPS-Lite Week 8
Final Scientific Report Generator

Generates the final MAPPS-Lite v1.0 research report directly from the
pipeline outputs created during Weeks 1-8.

Output:
    reports/MAPPS_Lite_Final_Report.md
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path


# =============================================================================
# PROJECT PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

OUTPUT_PATH = REPORTS_DIR / "MAPPS_Lite_Final_Report.md"


# =============================================================================
# FILES
# =============================================================================

FILES = {
    "materials": "materials.csv",
    "ranked": "ranked_materials.csv",
    "screened": "screened_materials.csv",
    "electrochemical": "electrochemical_evaluation.csv",
    "exact_structure": "exact_structure_validation.csv",
    "week5_final": "final_candidate_ranking.csv",
    "week5_shortlist": "week5_shortlist.csv",
    "week6_shortlist": "week6_research_shortlist.csv",
    "week6_literature": "week6_literature_validation.csv",
    "week6_synthesis": "week6_synthesis_feasibility.csv",
    "week6_transport": "week6_transport_evaluation.csv",
    "week6_resource": "week6_resource_assessment.csv",
    "week6_provenance": "week6_provenance_validation.csv",
    "week6_final": "week6_final_ranking.csv",
    "week7_final": "week7_final_ranking.csv",
    "week8_validation": "week8_validation_results.csv",
}


# =============================================================================
# UTILITIES
# =============================================================================

def path_for(key: str) -> Path:
    return DATA_DIR / FILES[key]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def safe_float(value) -> float | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def format_number(
    value,
    decimals: int = 1,
) -> str:
    number = safe_float(value)

    if number is None:
        return "-"

    return f"{number:.{decimals}f}"


def clean_markdown(value) -> str:
    if value is None:
        return "-"

    text = str(value).strip()

    if not text:
        return "-"

    return (
        text
        .replace("|", "/")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def first_present(
    row: dict,
    columns: list[str],
):
    for column in columns:
        value = row.get(column)

        if value is not None:
            text = str(value).strip()

            if text:
                return value

    return None


def count_values(
    rows: list[dict],
    column: str,
) -> Counter:
    counter = Counter()

    for row in rows:
        value = str(
            row.get(column, "")
        ).strip()

        if value:
            counter[value] += 1

    return counter


def sort_by_numeric_column(
    rows: list[dict],
    column: str,
) -> list[dict]:
    def key(row):
        value = safe_float(
            row.get(column)
        )

        if value is None:
            return float("inf")

        return value

    return sorted(
        rows,
        key=key,
    )


# =============================================================================
# LOAD DATA
# =============================================================================

def load_datasets() -> dict[str, list[dict]]:
    datasets = {}

    for key in FILES:
        datasets[key] = read_csv(
            path_for(key)
        )

    return datasets


# =============================================================================
# VALIDATION SUMMARY
# =============================================================================

def validation_summary(
    rows: list[dict],
) -> dict[str, int]:
    counts = Counter()

    for row in rows:
        status = str(
            row.get(
                "status",
                "",
            )
        ).strip().upper()

        if status:
            counts[status] += 1

    return {
        "PASS": counts.get("PASS", 0),
        "WARN": counts.get("WARN", 0),
        "FAIL": counts.get("FAIL", 0),
        "TOTAL": sum(counts.values()),
    }


# =============================================================================
# WEEK 5 ROLE SUMMARY
# =============================================================================

def week5_role_summary(
    rows: list[dict],
) -> dict[str, int]:
    final_selection = 0
    discovery_review = 0
    benchmark_only = 0

    for row in rows:
        final_rank = safe_float(
            row.get(
                "final_selection_rank"
            )
        )

        discovery_rank = safe_float(
            row.get(
                "discovery_review_rank"
            )
        )

        action = str(
            row.get(
                "recommended_action",
                "",
            )
        ).strip()

        if final_rank is not None:
            final_selection += 1

        if discovery_rank is not None:
            discovery_review += 1

        if action == "BENCHMARK_ONLY":
            benchmark_only += 1

    return {
        "final_selection": final_selection,
        "discovery_review": discovery_review,
        "benchmark_only": benchmark_only,
        "total": len(rows),
    }


# =============================================================================
# FINAL CANDIDATE TABLE
# =============================================================================

def final_candidate_table(
    rows: list[dict],
    limit: int = 10,
) -> list[str]:
    if not rows:
        return [
            "_Week 7 final ranking dataset was not found._"
        ]

    ranked = sort_by_numeric_column(
        rows,
        "week7_final_rank",
    )

    lines = [
        (
            "| Rank | Material ID | Formula | Recommendation | "
            "Research Potential | Evidence Confidence | "
            "Risk | Final Score |"
        ),
        (
            "|---:|---|---|---|---:|---:|---:|---:|"
        ),
    ]

    for row in ranked[:limit]:
        rank = clean_markdown(
            row.get("week7_final_rank")
        )

        material_id = clean_markdown(
            row.get("material_id")
        )

        formula = clean_markdown(
            row.get("formula")
        )

        recommendation = clean_markdown(
            row.get(
                "final_recommendation"
            )
        )

        research = format_number(
            row.get(
                "research_potential_score"
            )
        )

        confidence = format_number(
            row.get(
                "evidence_confidence_score"
            )
        )

        risk = format_number(
            row.get(
                "total_risk_score"
            )
        )

        final_score = format_number(
            row.get(
                "week7_final_score"
            )
        )

        lines.append(
            f"| {rank} "
            f"| {material_id} "
            f"| {formula} "
            f"| {recommendation} "
            f"| {research} "
            f"| {confidence} "
            f"| {risk} "
            f"| {final_score} |"
        )

    return lines


# =============================================================================
# RECOMMENDATION DISTRIBUTION
# =============================================================================

def recommendation_section(
    rows: list[dict],
) -> list[str]:
    counts = count_values(
        rows,
        "final_recommendation",
    )

    if not counts:
        return [
            "_No recommendation categories were detected._"
        ]

    lines = [
        "| Recommendation Role | Candidates |",
        "|---|---:|",
    ]

    for category, count in counts.most_common():
        lines.append(
            f"| {clean_markdown(category)} | {count} |"
        )

    return lines


# =============================================================================
# TOP CANDIDATE SUMMARY
# =============================================================================

def top_candidate_summary(
    rows: list[dict],
) -> list[str]:
    if not rows:
        return [
            "No Week 7 final candidate data were available."
        ]

    ranked = sort_by_numeric_column(
        rows,
        "week7_final_rank",
    )

    top = ranked[0]

    material_id = clean_markdown(
        top.get("material_id")
    )

    formula = clean_markdown(
        top.get("formula")
    )

    recommendation = clean_markdown(
        top.get(
            "final_recommendation"
        )
    )

    research = format_number(
        top.get(
            "research_potential_score"
        )
    )

    confidence = format_number(
        top.get(
            "evidence_confidence_score"
        )
    )

    risk = format_number(
        top.get(
            "total_risk_score"
        )
    )

    final_score = format_number(
        top.get(
            "week7_final_score"
        )
    )

    return [
        (
            f"The highest-ranked Week 7 material is "
            f"**{formula} ({material_id})**."
        ),
        "",
        f"- Final recommendation: **{recommendation}**",
        f"- Research potential score: **{research}**",
        f"- Evidence confidence score: **{confidence}**",
        f"- Total risk score: **{risk}**",
        f"- Week 7 final score: **{final_score}**",
    ]


# =============================================================================
# DATASET PROGRESSION
# =============================================================================

def dataset_progression(
    datasets: dict[str, list[dict]],
) -> list[str]:
    stages = [
        (
            "Cleaned Materials Project candidates",
            "materials",
        ),
        (
            "Thermodynamically ranked materials",
            "ranked",
        ),
        (
            "Screened materials",
            "screened",
        ),
        (
            "Detailed electrochemical evaluations",
            "electrochemical",
        ),
        (
            "Exact-structure validation records",
            "exact_structure",
        ),
        (
            "Week 5 final candidate population",
            "week5_final",
        ),
        (
            "Week 5 shortlist",
            "week5_shortlist",
        ),
        (
            "Week 6 research shortlist",
            "week6_shortlist",
        ),
        (
            "Week 6 final ranking",
            "week6_final",
        ),
        (
            "Week 7 final research ranking",
            "week7_final",
        ),
    ]

    lines = [
        "| Pipeline Stage | Records |",
        "|---|---:|",
    ]

    for label, key in stages:
        lines.append(
            f"| {label} | {len(datasets[key])} |"
        )

    return lines


# =============================================================================
# REPORT GENERATION
# =============================================================================

def build_report(
    datasets: dict[str, list[dict]],
) -> str:
    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    week5_roles = week5_role_summary(
        datasets["week5_final"]
    )

    validation = validation_summary(
        datasets["week8_validation"]
    )

    final_rows = datasets["week7_final"]

    lines = [
        "# MAPPS-Lite v1.0 Final Research Report",
        "",
        (
            "**Multi-Stage Computational Screening and Evidence "
            "Validation for Lithium-Ion Battery Cathode Discovery**"
        ),
        "",
        f"Generated: {timestamp}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        (
            "MAPPS-Lite is a computational materials-screening pipeline "
            "designed to identify and prioritize lithium-ion battery "
            "cathode candidates using Materials Project data and a "
            "sequence of increasingly strict scientific validation stages."
        ),
        "",
        (
            "The system begins with broad candidate retrieval and "
            "thermodynamic screening, then progressively incorporates "
            "electrochemical performance, known cathode benchmarking, "
            "exact-structure evidence, literature support, synthesis "
            "feasibility, transport behavior, resource sustainability, "
            "provenance, evidence confidence, and overall research risk."
        ),
        "",
        (
            "The purpose of MAPPS-Lite is not to claim experimental "
            "discovery of a new cathode. Instead, it provides a "
            "reproducible computational framework for narrowing a large "
            "materials search space into a small set of candidates that "
            "justify deeper computational or experimental investigation."
        ),
        "",
        *top_candidate_summary(final_rows),
        "",
        "---",
        "",
        "## 1. Research Objective",
        "",
        (
            "The central research question of MAPPS-Lite is:"
        ),
        "",
        (
            "> How can a large computational materials database be "
            "systematically reduced into a defensible shortlist of "
            "lithium-ion cathode research candidates?"
        ),
        "",
        (
            "MAPPS-Lite addresses this problem through staged filtering "
            "rather than relying on a single property or score."
        ),
        "",
        "---",
        "",
        "## 2. Pipeline Architecture",
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
        "Research Candidate Selection",
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
        "Evidence Confidence and Risk",
        "       |",
        "       v",
        "FINAL RESEARCH RECOMMENDATION",
        "```",
        "",
        "---",
        "",
        "## 3. Dataset Progression",
        "",
        *dataset_progression(datasets),
        "",
        (
            "The reduction in candidate count across later stages reflects "
            "the transition from broad database screening to increasingly "
            "evidence-intensive research evaluation."
        ),
        "",
        "---",
        "",
        "## 4. Thermodynamic Screening",
        "",
        (
            "The early MAPPS-Lite stages use Materials Project properties "
            "to identify lithium-containing compounds with characteristics "
            "relevant to cathode screening."
        ),
        "",
        (
            "The thermodynamic ranking emphasizes energy above hull, "
            "formation energy, and database stability. These variables "
            "provide an initial indication of whether a candidate is "
            "energetically plausible before more expensive or specialized "
            "battery-specific evaluation is performed."
        ),
        "",
        (
            "This stage is deliberately broad. Thermodynamic favorability "
            "alone does not establish that a material will function as a "
            "practical battery cathode."
        ),
        "",
        "---",
        "",
        "## 5. Electrochemical Evaluation",
        "",
        (
            "Week 5 introduced battery-specific evaluation. Candidate "
            "materials were compared against available Materials Project "
            "electrode records and formula-family evidence."
        ),
        "",
        (
            "Electrochemical evaluation incorporates available properties "
            "such as voltage, gravimetric and volumetric capacity, energy "
            "density, volume change, voltage-step behavior, and charged/"
            "discharged-state stability."
        ),
        "",
        (
            f"The stored electrochemical evaluation contains "
            f"**{len(datasets['electrochemical'])} candidate records**."
        ),
        "",
        "---",
        "",
        "## 6. Reference Cathode Benchmarking",
        "",
        (
            "Known cathode chemistries are retained as reference controls. "
            "These materials help calibrate whether candidate scores fall "
            "within ranges observed for established battery materials."
        ),
        "",
        (
            "Reference materials are not automatically treated as new "
            "discoveries. They may instead receive a benchmark-only role "
            "so that the discovery ranking remains distinct from the "
            "validation controls."
        ),
        "",
        "---",
        "",
        "## 7. Exact Structure Validation",
        "",
        (
            "Formula-level matching can overstate evidence because two "
            "materials with related compositions may correspond to "
            "different structures or electrode records."
        ),
        "",
        (
            "MAPPS-Lite therefore performs an exact-material validation "
            "stage. Exact electrode evidence is treated as stronger than "
            "formula-family evidence, while candidates lacking electrode "
            "records remain available for discovery review rather than "
            "being incorrectly labeled as validated cathodes."
        ),
        "",
        "---",
        "",
        "## 8. Week 5 Candidate Roles",
        "",
        (
            "Week 5 separates the candidate population into multiple "
            "research roles rather than forcing every material into the "
            "same ranking."
        ),
        "",
        "| Week 5 Role | Materials |",
        "|---|---:|",
        (
            f"| Main final-selection ranking "
            f"| {week5_roles['final_selection']} |"
        ),
        (
            f"| Discovery-review ranking "
            f"| {week5_roles['discovery_review']} |"
        ),
        (
            f"| Benchmark-only controls "
            f"| {week5_roles['benchmark_only']} |"
        ),
        (
            f"| Total Week 5 population "
            f"| {week5_roles['total']} |"
        ),
        "",
        (
            "This distinction is important because absence of a known "
            "electrode record is not equivalent to proof that a material "
            "is unsuitable. Such candidates instead carry greater "
            "uncertainty and require further investigation."
        ),
        "",
        "---",
        "",
        "## 9. Week 6 Scientific Validation",
        "",
        (
            "Week 6 expanded the evaluation beyond database-derived "
            "electrochemical properties. Candidates were assessed across "
            "several scientific and practical dimensions."
        ),
        "",
        "### 9.1 Literature Validation",
        "",
        (
            f"`week6_literature_validation.csv` contains "
            f"**{len(datasets['week6_literature'])} records**."
        ),
        "",
        (
            "Literature evidence is used to determine whether a candidate "
            "or closely related chemistry has meaningful external support "
            "and to separate database evidence from broader scientific "
            "evidence."
        ),
        "",
        "### 9.2 Synthesis Feasibility",
        "",
        (
            f"`week6_synthesis_feasibility.csv` contains "
            f"**{len(datasets['week6_synthesis'])} records**."
        ),
        "",
        (
            "Synthesis feasibility estimates whether a candidate appears "
            "reasonable to pursue experimentally based on the evidence "
            "available to the pipeline."
        ),
        "",
        "### 9.3 Transport Evaluation",
        "",
        (
            f"`week6_transport_evaluation.csv` contains "
            f"**{len(datasets['week6_transport'])} records**."
        ),
        "",
        (
            "Transport-related evaluation adds another constraint because "
            "thermodynamic stability and theoretical energy performance "
            "alone do not guarantee useful ion or electron transport."
        ),
        "",
        "### 9.4 Resource Sustainability",
        "",
        (
            f"`week6_resource_assessment.csv` contains "
            f"**{len(datasets['week6_resource'])} records**."
        ),
        "",
        (
            "Resource assessment introduces practical considerations such "
            "as elemental availability and material risk so that scientific "
            "performance is not evaluated in isolation."
        ),
        "",
        "### 9.5 Provenance Validation",
        "",
        (
            f"`week6_provenance_validation.csv` contains "
            f"**{len(datasets['week6_provenance'])} records**."
        ),
        "",
        (
            "Provenance validation preserves traceability between final "
            "recommendations and the source evidence used to construct "
            "them."
        ),
        "",
        "---",
        "",
        "## 10. Week 7 Evidence Confidence and Final Ranking",
        "",
        (
            "Week 7 combines the scientific evidence accumulated in the "
            "previous stages into the final MAPPS-Lite research ranking."
        ),
        "",
        (
            "The final evaluation distinguishes between research potential "
            "and evidence confidence. This prevents a highly interesting "
            "but weakly supported material from being interpreted as "
            "equivalent to a well-established reference material."
        ),
        "",
        (
            "Risk is retained as a separate quantity so that the final "
            "recommendation reflects both opportunity and uncertainty."
        ),
        "",
        "### Final Recommendation Distribution",
        "",
        *recommendation_section(final_rows),
        "",
        "### Final Top Candidates",
        "",
        *final_candidate_table(
            final_rows,
            limit=10,
        ),
        "",
        "---",
        "",
        "## 11. Pipeline Validation and Reproducibility",
        "",
        (
            "Week 8 performs final structural validation of the stored "
            "pipeline outputs."
        ),
        "",
        "| Validation Result | Count |",
        "|---|---:|",
        f"| PASS | {validation['PASS']} |",
        f"| WARN | {validation['WARN']} |",
        f"| FAIL | {validation['FAIL']} |",
        f"| TOTAL | {validation['TOTAL']} |",
        "",
    ]

    if validation["FAIL"] == 0:
        lines.extend([
            (
                "**Final pipeline validation status: VALID**"
            ),
            "",
            (
                "No unresolved integrity failures were detected in the "
                "final Week 8 validation run."
            ),
        ])
    else:
        lines.extend([
            (
                "**Final pipeline validation status: REVIEW REQUIRED**"
            ),
            "",
            (
                "One or more validation failures remain and should be "
                "reviewed before the project is treated as a final release."
            ),
        ])

    lines.extend([
        "",
        (
            "Week 8 also generates a pipeline manifest containing SHA-256 "
            "checksums for major project artifacts. These hashes provide a "
            "snapshot of the exact files used for the final MAPPS-Lite "
            "v1.0 results."
        ),
        "",
        "---",
        "",
        "## 12. Scientific Interpretation",
        "",
        (
            "The MAPPS-Lite ranking should be interpreted as a research "
            "prioritization system rather than a prediction that the "
            "highest-ranked discovery candidate will necessarily become "
            "a successful commercial cathode."
        ),
        "",
        (
            "A high final ranking indicates that a material performs well "
            "under the evidence and scoring framework implemented by "
            "MAPPS-Lite. A lower evidence-confidence score or higher risk "
            "score indicates that additional computational or experimental "
            "work is necessary before strong conclusions should be drawn."
        ),
        "",
        (
            "Known reference cathodes provide an important internal "
            "control. Their presence allows the system to verify that its "
            "scoring framework can recognize established battery materials "
            "while still maintaining a separate discovery pathway for "
            "less-characterized candidates."
        ),
        "",
        "---",
        "",
        "## 13. Limitations",
        "",
        (
            "MAPPS-Lite v1.0 has several important limitations:"
        ),
        "",
        (
            "1. **Database dependence.** Results depend on the structures "
            "and properties available through the underlying Materials "
            "Project datasets."
        ),
        "",
        (
            "2. **Heuristic scoring.** The multi-stage scores are research "
            "prioritization tools rather than experimentally calibrated "
            "probabilities of cathode success."
        ),
        "",
        (
            "3. **Incomplete electrochemical evidence.** Absence of an "
            "electrode record does not establish that a material cannot "
            "function electrochemically."
        ),
        "",
        (
            "4. **No new first-principles calculations.** MAPPS-Lite v1.0 "
            "primarily evaluates existing computational evidence rather "
            "than performing new DFT calculations for every candidate."
        ),
        "",
        (
            "5. **No experimental validation.** Final candidates have not "
            "been synthesized or electrochemically tested as part of this "
            "software pipeline."
        ),
        "",
        (
            "6. **Literature and provenance limitations.** Evidence quality "
            "depends on the availability and reliability of external "
            "scientific records."
        ),
        "",
        "---",
        "",
        "## 14. Future Work",
        "",
        (
            "A future MAPPS-Lite v2 could extend the current system with:"
        ),
        "",
        "- automated first-principles calculations",
        "- learned battery-property prediction models",
        "- diffusion-barrier and ionic-conductivity calculations",
        "- structural transformation prediction during cycling",
        "- automated literature retrieval and evidence extraction",
        "- uncertainty calibration",
        "- active-learning candidate selection",
        "- autonomous research agents",
        "- experimental collaboration and synthesis validation",
        "",
        "---",
        "",
        "## 15. Conclusion",
        "",
        (
            "MAPPS-Lite v1.0 demonstrates a complete computational workflow "
            "for reducing a large materials database into a small, "
            "traceable set of lithium-ion cathode research recommendations."
        ),
        "",
        (
            "The project progresses from broad thermodynamic screening to "
            "battery-specific electrochemical evaluation, structural "
            "validation, external evidence assessment, practical research "
            "constraints, confidence estimation, and final risk-aware "
            "ranking."
        ),
        "",
        (
            "The final output is therefore not simply a list of materials. "
            "It is an evidence-linked research prioritization framework "
            "designed to show why each candidate advances through the "
            "pipeline and how strongly the available evidence supports the "
            "final recommendation."
        ),
        "",
        "---",
        "",
        "## 16. Primary Final Artifacts",
        "",
        "- `data/week7_final_ranking.csv`",
        "- `data/week8_pipeline_manifest.csv`",
        "- `data/week8_validation_results.csv`",
        "- `reports/week7_final_recommendation.md`",
        "- `reports/week8_pipeline_integration.md`",
        "- `reports/week8_pipeline_validation.md`",
        "- `reports/MAPPS_Lite_Final_Report.md`",
        "",
        (
            "**MAPPS-Lite v1.0 final scientific pipeline complete.**"
        ),
        "",
    ])

    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    print()
    print("=" * 80)
    print("MAPPS-LITE WEEK 8")
    print("FINAL SCIENTIFIC REPORT GENERATOR")
    print("=" * 80)

    print()
    print("[1/4] Loading final pipeline datasets...")

    datasets = load_datasets()

    print(
        f"Loaded {len(datasets['week7_final'])} "
        "Week 7 final candidates."
    )

    print()
    print("[2/4] Building final scientific summary...")

    report = build_report(
        datasets
    )

    print()
    print("[3/4] Saving final MAPPS-Lite report...")

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print(f"Saved: {OUTPUT_PATH}")

    print()
    print("[4/4] Final report complete.")

    print()
    print("=" * 80)
    print("WEEK 8.3 COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()