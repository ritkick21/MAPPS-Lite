"""
MAPPS-Lite Week 7
Candidate Risk and Failure-Mode Assessment

Purpose
-------
Evaluate the principal scientific and practical risks associated with
the Week 7 cathode candidates.

The script:
1. Loads Week 7 theoretical-performance results.
2. Integrates structural, redox, performance, and Week 6 evidence signals.
3. Evaluates explicit risk categories.
4. Assigns a total risk score and severity class.
5. Separates scientific uncertainty from candidate quality.
6. Produces a detailed CSV and Markdown report.

Input
-----
data/week7_theoretical_performance.csv

Optional Week 6 context
-----------------------
data/week6_final_ranking.csv
data/week6_literature_validation.csv
data/week6_synthesis_feasibility.csv
data/week6_resource_assessment.csv
data/week6_transport_evaluation.csv
data/week6_provenance_validation.csv

Outputs
-------
data/week7_risk_assessment.csv
reports/week7_risk_assessment.md

Scientific Interpretation
-------------------------
Risk score is NOT the same thing as candidate quality.

A high-performance candidate may still have high research risk.
A moderate-performance candidate may be scientifically safer.

This stage is intended to expose those distinctions explicitly.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_theoretical_performance.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_risk_assessment.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week7_risk_assessment.md"
)


# Optional Week 6 evidence files

WEEK6_FILES = {
    "final": (
        PROJECT_ROOT
        / "data"
        / "week6_final_ranking.csv"
    ),

    "literature": (
        PROJECT_ROOT
        / "data"
        / "week6_literature_validation.csv"
    ),

    "synthesis": (
        PROJECT_ROOT
        / "data"
        / "week6_synthesis_feasibility.csv"
    ),

    "resource": (
        PROJECT_ROOT
        / "data"
        / "week6_resource_assessment.csv"
    ),

    "transport": (
        PROJECT_ROOT
        / "data"
        / "week6_transport_evaluation.csv"
    ),

    "provenance": (
        PROJECT_ROOT
        / "data"
        / "week6_provenance_validation.csv"
    ),
}


# ============================================================
# ELEMENT RISK CONFIGURATION
# ============================================================

# These values are screening penalties rather than regulatory or
# economic claims.

ELEMENT_RISK_WEIGHTS = {
    # Higher concern
    "Co": 8,
    "Ni": 6,
    "Cr": 6,
    "V": 4,
    "Mo": 4,
    "W": 4,

    # Moderate concern
    "Mn": 2,
    "Cu": 2,
    "Nb": 3,
    "Ta": 4,

    # Lower concern
    "Fe": 0,
    "Ti": 0,
    "Li": 0,
    "P": 0,
    "Si": 0,
    "O": 0,
    "F": 1,
    "H": 0,
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_float(value: Any) -> float | None:
    """
    Convert value to finite float when possible.
    """

    try:
        if value is None:
            return None

        number = float(value)

        if not np.isfinite(number):
            return None

        return number

    except (TypeError, ValueError):
        return None


def safe_text(value: Any) -> str:
    """
    Normalize text fields.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def find_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    """
    Find the first matching column name.
    """

    normalized = {
        str(column).strip().lower(): column
        for column in dataframe.columns
    }

    for candidate in candidates:

        key = candidate.strip().lower()

        if key in normalized:
            return normalized[key]

    return None


def format_value(
    value: Any,
    digits: int = 2,
) -> str:
    """
    Format values for Markdown output.
    """

    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"
    except (TypeError, ValueError):
        pass

    if isinstance(
        value,
        (
            float,
            np.floating,
        ),
    ):
        return f"{value:.{digits}f}"

    return str(value)


# ============================================================
# LOAD WEEK 7 PERFORMANCE DATA
# ============================================================

def load_week7_performance() -> pd.DataFrame:
    """
    Load theoretical-performance dataset.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "\nCould not find Week 7 performance dataset:\n"
            f"{INPUT_FILE}\n\n"
            "Run src/estimate_theoretical_performance.py first."
        )

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    if dataframe.empty:

        raise ValueError(
            "week7_theoretical_performance.csv contains no candidates."
        )

    required = [
        "material_id",
        "formula",
        "performance_score",
        "performance_rating",
        "screening_capacity_mAh_g",
        "estimated_average_voltage_V",
        "formal_redox_electrons",
        "structure_score",
        "redox_score",
    ]

    missing = [
        column
        for column in required
        if column not in dataframe.columns
    ]

    if missing:

        raise ValueError(
            "Missing required columns:\n"
            + ", ".join(
                missing
            )
        )

    return dataframe.copy()


# ============================================================
# OPTIONAL WEEK 6 DATA
# ============================================================

def load_optional_week6_files() -> dict[str, pd.DataFrame]:
    """
    Load any available Week 6 evidence tables.

    The script does not fail if one is unavailable.
    """

    loaded: dict[str, pd.DataFrame] = {}

    for name, path in WEEK6_FILES.items():

        if not path.exists():
            continue

        try:

            dataframe = pd.read_csv(
                path
            )

            if not dataframe.empty:

                loaded[name] = dataframe

        except Exception:
            continue

    return loaded


def merge_best_available_context(
    week7: pd.DataFrame,
    week6_tables: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Add useful Week 6 context without depending on fixed column names.

    Only columns not already present are copied.
    """

    result = week7.copy()

    for table_name, dataframe in week6_tables.items():

        id_column = find_column(
            dataframe,
            [
                "material_id",
                "mp_id",
                "materials_project_id",
            ],
        )

        if id_column is None:
            continue

        table = dataframe.copy()

        if id_column != "material_id":

            table = table.rename(
                columns={
                    id_column: "material_id"
                }
            )

        table["material_id"] = (
            table["material_id"]
            .astype(str)
            .str.strip()
        )

        # Prefix Week 6 fields to avoid collisions.

        rename_map = {}

        for column in table.columns:

            if column == "material_id":
                continue

            rename_map[column] = (
                f"week6_{table_name}_{column}"
            )

        table = table.rename(
            columns=rename_map
        )

        # Keep first record per MP ID.

        table = table.drop_duplicates(
            subset=["material_id"],
            keep="first",
        )

        result = result.merge(
            table,
            on="material_id",
            how="left",
        )

    return result


# ============================================================
# FORMULA ELEMENT EXTRACTION
# ============================================================

def extract_elements(
    formula: str,
) -> list[str]:
    """
    Extract element symbols using a lightweight parser.

    This parser is sufficient for identifying constituent elements
    for resource/toxicity screening.
    """

    import re

    symbols = re.findall(
        r"[A-Z][a-z]?",
        str(formula),
    )

    unique = []

    for symbol in symbols:

        if symbol not in unique:
            unique.append(symbol)

    return unique


# ============================================================
# RISK COMPONENT 1: STRUCTURAL RISK
# ============================================================

def assess_structural_risk(
    row: pd.Series,
) -> tuple[float, list[str]]:
    """
    Assess structural and thermodynamic risk.
    """

    risk = 0.0
    reasons: list[str] = []

    structure_score = safe_float(
        row.get(
            "structure_score"
        )
    )

    if structure_score is None:
        risk += 10
        reasons.append(
            "Structural score unavailable."
        )

    elif structure_score < 60:
        risk += 14
        reasons.append(
            "Weak structural screening score."
        )

    elif structure_score < 75:
        risk += 8
        reasons.append(
            "Only moderate structural screening support."
        )

    elif structure_score < 85:
        risk += 3

    energy_above_hull = safe_float(
        row.get(
            "energy_above_hull_ev_atom"
        )
    )

    if energy_above_hull is not None:

        if energy_above_hull > 0.10:
            risk += 12
            reasons.append(
                "High energy above hull indicates substantial "
                "thermodynamic metastability."
            )

        elif energy_above_hull > 0.05:
            risk += 7
            reasons.append(
                "Moderate thermodynamic metastability."
            )

        elif energy_above_hull > 0.025:
            risk += 3

    lattice_anisotropy = safe_float(
        row.get(
            "lattice_anisotropy"
        )
    )

    if (
        lattice_anisotropy is not None
        and lattice_anisotropy > 3.0
    ):
        risk += 4
        reasons.append(
            "Highly anisotropic lattice may increase directional "
            "transport or mechanical sensitivity."
        )

    return (
        min(
            25.0,
            risk,
        ),
        reasons,
    )


# ============================================================
# RISK COMPONENT 2: REDOX RISK
# ============================================================

def assess_redox_risk(
    row: pd.Series,
) -> tuple[float, list[str]]:
    """
    Assess oxidation-state and charge-storage risk.
    """

    risk = 0.0
    reasons: list[str] = []

    redox_score = safe_float(
        row.get(
            "redox_score"
        )
    )

    if redox_score is None:
        risk += 12
        reasons.append(
            "Redox score unavailable."
        )

    elif redox_score < 50:
        risk += 18
        reasons.append(
            "Weak conventional cation-redox plausibility."
        )

    elif redox_score < 65:
        risk += 12
        reasons.append(
            "Moderate redox uncertainty."
        )

    elif redox_score < 80:
        risk += 5

    electrons = safe_float(
        row.get(
            "formal_redox_electrons"
        )
    )

    if electrons is None:
        electrons = 0.0

    if electrons <= 0:

        risk += 15
        reasons.append(
            "No conventional transition-metal oxidation headroom "
            "was identified."
        )

    elif electrons > 4:

        risk += 10
        reasons.append(
            "Candidate depends on very deep multi-electron "
            "delithiation."
        )

    elif electrons > 3:

        risk += 8
        reasons.append(
            "Candidate depends on extensive multi-electron "
            "delithiation."
        )

    elif electrons >= 3:

        risk += 5
        reasons.append(
            "Full performance requires deep delithiation."
        )

    confidence = safe_text(
        row.get(
            "redox_confidence"
        )
    ).upper()

    if confidence == "LOW":

        risk += 8
        reasons.append(
            "Low confidence in oxidation-state interpretation."
        )

    elif confidence == "MODERATE":

        risk += 3

    concerns = safe_text(
        row.get(
            "redox_concerns"
        )
    ).lower()

    if "upper oxidation-state limit" in concerns:

        risk += 5
        reasons.append(
            "Redox-active metal begins near its conservative "
            "upper oxidation-state limit."
        )

    return (
        min(
            25.0,
            risk,
        ),
        reasons,
    )


# ============================================================
# RISK COMPONENT 3: PERFORMANCE / VOLTAGE RISK
# ============================================================

def assess_performance_risk(
    row: pd.Series,
) -> tuple[float, list[str]]:
    """
    Assess performance-related implementation risk.
    """

    risk = 0.0
    reasons: list[str] = []

    capacity = safe_float(
        row.get(
            "screening_capacity_mAh_g"
        )
    )

    if capacity is None:

        risk += 7
        reasons.append(
            "Screening capacity unavailable."
        )

    elif capacity < 60:

        risk += 10
        reasons.append(
            "Low estimated usable gravimetric capacity."
        )

    elif capacity < 100:

        risk += 6
        reasons.append(
            "Only modest estimated usable capacity."
        )

    voltage = safe_float(
        row.get(
            "estimated_average_voltage_V"
        )
    )

    if voltage is not None:

        if voltage >= 4.5:

            risk += 10
            reasons.append(
                "Very high estimated operating voltage may "
                "challenge electrolyte stability."
            )

        elif voltage >= 4.2:

            risk += 6
            reasons.append(
                "High estimated voltage may increase electrolyte "
                "and interface compatibility risk."
            )

    utilization = safe_float(
        row.get(
            "utilization_fraction"
        )
    )

    if (
        utilization is not None
        and utilization < 0.65
    ):

        risk += 6
        reasons.append(
            "Performance depends on a heavily penalized utilization "
            "fraction."
        )

    elif (
        utilization is not None
        and utilization < 0.75
    ):

        risk += 3

    confidence = safe_text(
        row.get(
            "performance_confidence"
        )
    ).upper()

    if confidence == "LOW":

        risk += 6
        reasons.append(
            "Low confidence in performance estimate."
        )

    elif confidence == "MODERATE":

        risk += 2

    return (
        min(
            20.0,
            risk,
        ),
        reasons,
    )


# ============================================================
# RISK COMPONENT 4: RESOURCE / ELEMENT RISK
# ============================================================

def assess_element_risk(
    row: pd.Series,
) -> tuple[float, list[str]]:
    """
    Assess broad resource and element-related risk.
    """

    formula = safe_text(
        row.get(
            "formula"
        )
    )

    elements = extract_elements(
        formula
    )

    risk = 0.0
    reasons: list[str] = []

    for element in elements:

        penalty = ELEMENT_RISK_WEIGHTS.get(
            element,
            1,
        )

        if penalty > 0:

            risk += penalty

            if penalty >= 6:

                reasons.append(
                    f"{element} contributes elevated resource, "
                    f"cost, toxicity, or supply-chain concern."
                )

            elif penalty >= 3:

                reasons.append(
                    f"{element} contributes moderate practical "
                    f"resource or supply concern."
                )

    # Fluorinated chemistries receive a small processing penalty.

    if "F" in elements:

        risk += 2
        reasons.append(
            "Fluorinated chemistry may increase synthesis, handling, "
            "or processing complexity."
        )

    return (
        min(
            15.0,
            risk,
        ),
        reasons,
    )


# ============================================================
# RISK COMPONENT 5: EVIDENCE RISK
# ============================================================

def search_row_for_keywords(
    row: pd.Series,
    keywords: list[str],
) -> bool:
    """
    Search all row values for evidence-related keywords.
    """

    combined = " ".join(
        safe_text(
            value
        ).lower()
        for value in row.values
    )

    return any(
        keyword.lower() in combined
        for keyword in keywords
    )


def assess_evidence_risk(
    row: pd.Series,
) -> tuple[float, list[str]]:
    """
    Assess uncertainty arising from incomplete Week 6 evidence.

    This function deliberately uses flexible keyword searches because
    Week 6 output column names may vary.
    """

    risk = 0.0
    reasons: list[str] = []

    # --------------------------------------------------------
    # Literature evidence
    # --------------------------------------------------------

    has_literature_support = (
        search_row_for_keywords(
            row,
            [
                "strong literature",
                "validated literature",
                "direct literature",
                "experimental evidence",
                "battery evidence",
            ],
        )
    )

    weak_literature_signal = (
        search_row_for_keywords(
            row,
            [
                "no literature",
                "literature gap",
                "unverified",
                "no direct evidence",
            ],
        )
    )

    if weak_literature_signal:

        risk += 5
        reasons.append(
            "Literature evidence appears limited or indirect."
        )

    elif not has_literature_support:

        risk += 2

    # --------------------------------------------------------
    # Synthesis
    # --------------------------------------------------------

    weak_synthesis_signal = (
        search_row_for_keywords(
            row,
            [
                "difficult synthesis",
                "low feasibility",
                "no synthesis",
                "synthesis unknown",
                "unverified synthesis",
            ],
        )
    )

    if weak_synthesis_signal:

        risk += 5
        reasons.append(
            "Synthesis feasibility remains uncertain."
        )

    # --------------------------------------------------------
    # Transport
    # --------------------------------------------------------

    weak_transport_signal = (
        search_row_for_keywords(
            row,
            [
                "poor transport",
                "low transport",
                "transport risk",
                "diffusion concern",
            ],
        )
    )

    if weak_transport_signal:

        risk += 4
        reasons.append(
            "Previous transport screening indicates possible "
            "Li-ion mobility concerns."
        )

    # --------------------------------------------------------
    # Provenance
    # --------------------------------------------------------

    weak_provenance_signal = (
        search_row_for_keywords(
            row,
            [
                "provenance failed",
                "provenance concern",
                "unverified provenance",
            ],
        )
    )

    if weak_provenance_signal:

        risk += 4
        reasons.append(
            "Candidate provenance is not fully validated."
        )

    return (
        min(
            15.0,
            risk,
        ),
        reasons,
    )


# ============================================================
# TOTAL RISK SCORE
# ============================================================

def calculate_total_risk(
    structural: float,
    redox: float,
    performance: float,
    element: float,
    evidence: float,
) -> float:
    """
    Combine risk components.

    Maximum possible score:
        Structural   25
        Redox        25
        Performance  20
        Elements     15
        Evidence     15
        ----------------
        Total       100
    """

    total = (
        structural
        + redox
        + performance
        + element
        + evidence
    )

    return round(
        max(
            0.0,
            min(
                100.0,
                total,
            ),
        ),
        1,
    )


def classify_risk(
    risk_score: float,
) -> str:
    """
    Convert risk score to severity category.

    Lower is better.
    """

    if risk_score <= 20:
        return "LOW"

    if risk_score <= 35:
        return "MODERATE"

    if risk_score <= 50:
        return "ELEVATED"

    if risk_score <= 65:
        return "HIGH"

    return "VERY_HIGH"


# ============================================================
# RESEARCH UPSIDE VS RISK
# ============================================================

def calculate_risk_adjusted_score(
    performance_score: float,
    redox_score: float,
    structure_score: float,
    risk_score: float,
) -> float:
    """
    Calculate a research-priority score after explicit risk penalties.

    This is not the final Week 7 ranking.

    It provides an intermediate measure for identifying candidates
    with high upside but excessive uncertainty.
    """

    quality_score = (
        0.50 * performance_score
        + 0.30 * redox_score
        + 0.20 * structure_score
    )

    risk_penalty = (
        risk_score
        * 0.55
    )

    final = (
        quality_score
        - risk_penalty
    )

    return round(
        max(
            0.0,
            min(
                100.0,
                final,
            ),
        ),
        1,
    )


def classify_research_profile(
    performance_score: float,
    risk_score: float,
) -> str:
    """
    Describe candidate as safe, balanced, or speculative.
    """

    if (
        performance_score >= 70
        and risk_score <= 30
    ):
        return "HIGH_VALUE_LOW_RISK"

    if (
        performance_score >= 70
        and risk_score > 30
    ):
        return "HIGH_VALUE_HIGH_RISK"

    if (
        performance_score >= 55
        and risk_score <= 40
    ):
        return "BALANCED_RESEARCH_CANDIDATE"

    if (
        performance_score >= 55
        and risk_score > 40
    ):
        return "SPECULATIVE_RESEARCH_CANDIDATE"

    if risk_score <= 30:
        return "LOW_UPSIDE_LOW_RISK"

    return "LOW_PRIORITY_HIGH_RISK"


# ============================================================
# INDIVIDUAL CANDIDATE ANALYSIS
# ============================================================

def analyze_candidate(
    row: pd.Series,
) -> dict[str, Any]:
    """
    Perform complete failure-mode analysis.
    """

    result = row.to_dict()

    # --------------------------------------------------------
    # Individual risk dimensions
    # --------------------------------------------------------

    structural_risk, structural_reasons = (
        assess_structural_risk(
            row
        )
    )

    redox_risk, redox_reasons = (
        assess_redox_risk(
            row
        )
    )

    performance_risk, performance_reasons = (
        assess_performance_risk(
            row
        )
    )

    element_risk, element_reasons = (
        assess_element_risk(
            row
        )
    )

    evidence_risk, evidence_reasons = (
        assess_evidence_risk(
            row
        )
    )

    # --------------------------------------------------------
    # Total risk
    # --------------------------------------------------------

    total_risk = calculate_total_risk(
        structural_risk,
        redox_risk,
        performance_risk,
        element_risk,
        evidence_risk,
    )

    risk_rating = classify_risk(
        total_risk
    )

    # --------------------------------------------------------
    # Risk-adjusted research priority
    # --------------------------------------------------------

    performance_score = safe_float(
        row.get(
            "performance_score"
        )
    ) or 0.0

    redox_score = safe_float(
        row.get(
            "redox_score"
        )
    ) or 0.0

    structure_score = safe_float(
        row.get(
            "structure_score"
        )
    ) or 0.0

    risk_adjusted_score = (
        calculate_risk_adjusted_score(
            performance_score,
            redox_score,
            structure_score,
            total_risk,
        )
    )

    research_profile = (
        classify_research_profile(
            performance_score,
            total_risk,
        )
    )

    # --------------------------------------------------------
    # Aggregate reasons
    # --------------------------------------------------------

    all_reasons = (
        structural_reasons
        + redox_reasons
        + performance_reasons
        + element_reasons
        + evidence_reasons
    )

    if not all_reasons:

        all_reasons = [
            "No major failure mode was identified by the current "
            "screening rules."
        ]

    result.update(
        {
            "structural_risk_score":
                round(
                    structural_risk,
                    1,
                ),

            "redox_risk_score":
                round(
                    redox_risk,
                    1,
                ),

            "performance_risk_score":
                round(
                    performance_risk,
                    1,
                ),

            "element_resource_risk_score":
                round(
                    element_risk,
                    1,
                ),

            "evidence_risk_score":
                round(
                    evidence_risk,
                    1,
                ),

            "total_risk_score":
                total_risk,

            "risk_rating":
                risk_rating,

            "risk_adjusted_score":
                risk_adjusted_score,

            "research_profile":
                research_profile,

            "structural_risk_reasons":
                " | ".join(
                    structural_reasons
                ),

            "redox_risk_reasons":
                " | ".join(
                    redox_reasons
                ),

            "performance_risk_reasons":
                " | ".join(
                    performance_reasons
                ),

            "resource_risk_reasons":
                " | ".join(
                    element_reasons
                ),

            "evidence_risk_reasons":
                " | ".join(
                    evidence_reasons
                ),

            "all_risk_reasons":
                " | ".join(
                    all_reasons
                ),
        }
    )

    return result


# ============================================================
# REPORT GENERATION
# ============================================================

def generate_report(
    dataframe: pd.DataFrame,
) -> None:
    """
    Generate Week 7 risk-assessment report.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ranked = dataframe.sort_values(
        [
            "risk_adjusted_score",
            "total_risk_score",
        ],
        ascending=[
            False,
            True,
        ],
    )

    lines: list[str] = []

    lines.append(
        "# MAPPS-Lite Week 7 Candidate Risk Assessment"
    )

    lines.append("")

    lines.append("## Objective")
    lines.append("")

    lines.append(
        "This stage identifies the principal scientific, "
        "electrochemical, structural, resource, and evidence risks "
        "associated with the surviving cathode candidates."
    )

    lines.append("")

    lines.append(
        "Risk is evaluated separately from candidate performance. "
        "A material can therefore have high research upside while "
        "still receiving a high risk rating."
    )

    lines.append("")

    # ========================================================
    # Summary
    # ========================================================

    lines.append("## Summary")
    lines.append("")

    lines.append(
        f"- Candidates analyzed: **{len(dataframe)}**"
    )

    counts = (
        dataframe[
            "risk_rating"
        ]
        .value_counts()
        .to_dict()
    )

    for rating in [
        "LOW",
        "MODERATE",
        "ELEVATED",
        "HIGH",
        "VERY_HIGH",
    ]:

        count = counts.get(
            rating,
            0,
        )

        if count > 0:

            lines.append(
                f"- {rating} risk: **{count}**"
            )

    lines.append("")

    # ========================================================
    # Ranking
    # ========================================================

    lines.append(
        "## Risk-Adjusted Research Ranking"
    )

    lines.append("")

    lines.append(
        "| Rank | Material | Formula | Performance | Risk | "
        "Risk Rating | Risk-Adjusted Score | Profile |"
    )

    lines.append(
        "|---:|---|---|---:|---:|---|---:|---|"
    )

    for rank, (_, row) in enumerate(
        ranked.iterrows(),
        start=1,
    ):

        lines.append(
            f"| {rank} "
            f"| {format_value(row.get('material_id'))} "
            f"| {format_value(row.get('formula'))} "
            f"| {format_value(row.get('performance_score'), 1)} "
            f"| {format_value(row.get('total_risk_score'), 1)} "
            f"| {format_value(row.get('risk_rating'))} "
            f"| {format_value(row.get('risk_adjusted_score'), 1)} "
            f"| {format_value(row.get('research_profile'))} |"
        )

    lines.append("")

    # ========================================================
    # Candidate details
    # ========================================================

    lines.append(
        "## Candidate Failure-Mode Details"
    )

    lines.append("")

    for rank, (_, row) in enumerate(
        ranked.iterrows(),
        start=1,
    ):

        formula = format_value(
            row.get(
                "formula"
            )
        )

        material_id = format_value(
            row.get(
                "material_id"
            )
        )

        lines.append(
            f"### {rank}. {formula} ({material_id})"
        )

        lines.append("")

        lines.append(
            f"- Performance score: "
            f"**{format_value(row.get('performance_score'), 1)}/100**"
        )

        lines.append(
            f"- Total risk score: "
            f"**{format_value(row.get('total_risk_score'), 1)}/100**"
        )

        lines.append(
            f"- Risk rating: "
            f"**{format_value(row.get('risk_rating'))}**"
        )

        lines.append(
            f"- Risk-adjusted score: "
            f"**{format_value(row.get('risk_adjusted_score'), 1)}/100**"
        )

        lines.append(
            f"- Research profile: "
            f"**{format_value(row.get('research_profile'))}**"
        )

        lines.append("")

        lines.append(
            "### Risk components"
        )

        lines.append("")

        lines.append(
            f"- Structural risk: "
            f"{format_value(row.get('structural_risk_score'), 1)}/25"
        )

        lines.append(
            f"- Redox risk: "
            f"{format_value(row.get('redox_risk_score'), 1)}/25"
        )

        lines.append(
            f"- Performance risk: "
            f"{format_value(row.get('performance_risk_score'), 1)}/20"
        )

        lines.append(
            f"- Element/resource risk: "
            f"{format_value(row.get('element_resource_risk_score'), 1)}/15"
        )

        lines.append(
            f"- Evidence risk: "
            f"{format_value(row.get('evidence_risk_score'), 1)}/15"
        )

        reasons = safe_text(
            row.get(
                "all_risk_reasons"
            )
        )

        if reasons:

            lines.append("")
            lines.append(
                "**Principal failure modes / concerns**"
            )

            lines.append("")

            for reason in reasons.split(
                " | "
            ):

                lines.append(
                    f"- {reason}"
                )

        lines.append("")

    # ========================================================
    # Interpretation
    # ========================================================

    lines.append(
        "## Interpretation"
    )

    lines.append("")

    lines.append(
        "The total risk score is designed to expose weaknesses that "
        "may not be obvious from an aggregate performance score."
    )

    lines.append("")

    lines.append(
        "For example, a material with high theoretical capacity may "
        "receive a substantial redox-risk penalty if that capacity "
        "requires extraction of several lithium ions and extreme "
        "transition-metal oxidation."
    )

    lines.append("")

    lines.append(
        "Likewise, a high-voltage candidate may have attractive "
        "specific-energy potential while simultaneously creating "
        "electrolyte or interface stability concerns."
    )

    lines.append("")

    lines.append(
        "The risk-adjusted score should therefore be interpreted as "
        "research priority rather than predicted commercial success."
    )

    lines.append("")

    # ========================================================
    # Next stage
    # ========================================================

    lines.append(
        "## Next Stage"
    )

    lines.append("")

    lines.append(
        "The next Week 7 stage will place all surviving candidates "
        "into a head-to-head comparison table combining structural "
        "quality, redox plausibility, capacity, estimated energy, "
        "resource considerations, evidence confidence, and total risk."
    )

    lines.append("")

    REPORT_FILE.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """
    Run Week 7 risk assessment.
    """

    print()
    print("=" * 74)
    print("MAPPS-LITE WEEK 7")
    print("CANDIDATE RISK AND FAILURE-MODE ASSESSMENT")
    print("=" * 74)

    # --------------------------------------------------------
    # Stage 1
    # --------------------------------------------------------

    print()
    print(
        "[1/5] Loading Week 7 performance results..."
    )

    candidates = load_week7_performance()

    print(
        f"Loaded {len(candidates)} candidates."
    )

    # --------------------------------------------------------
    # Stage 2
    # --------------------------------------------------------

    print()
    print(
        "[2/5] Loading optional Week 6 evidence context..."
    )

    week6_tables = load_optional_week6_files()

    if week6_tables:

        print(
            "Loaded Week 6 context from:"
        )

        for name in sorted(
            week6_tables.keys()
        ):

            print(
                f"  - {name}"
            )

    else:

        print(
            "No optional Week 6 tables were loaded."
        )

    # --------------------------------------------------------
    # Stage 3
    # --------------------------------------------------------

    print()
    print(
        "[3/5] Combining Week 6 and Week 7 evidence..."
    )

    combined = merge_best_available_context(
        candidates,
        week6_tables,
    )

    # --------------------------------------------------------
    # Stage 4
    # --------------------------------------------------------

    print()
    print(
        "[4/5] Evaluating failure modes and research risk..."
    )

    results: list[dict[str, Any]] = []

    total = len(
        combined
    )

    for index, (_, row) in enumerate(
        combined.iterrows(),
        start=1,
    ):

        print(
            f"  [{index}/{total}] "
            f"{row['material_id']} "
            f"{row['formula']}"
        )

        try:

            result = analyze_candidate(
                row
            )

        except Exception as exc:

            result = row.to_dict()

            result.update(
                {
                    "structural_risk_score":
                        25.0,

                    "redox_risk_score":
                        25.0,

                    "performance_risk_score":
                        20.0,

                    "element_resource_risk_score":
                        15.0,

                    "evidence_risk_score":
                        15.0,

                    "total_risk_score":
                        100.0,

                    "risk_rating":
                        "VERY_HIGH",

                    "risk_adjusted_score":
                        0.0,

                    "research_profile":
                        "ANALYSIS_ERROR",

                    "all_risk_reasons":
                        f"Risk assessment failed: {exc}",
                }
            )

        results.append(
            result
        )

    dataframe = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Rank
    # --------------------------------------------------------

    dataframe = dataframe.sort_values(
        [
            "risk_adjusted_score",
            "total_risk_score",
            "performance_score",
        ],
        ascending=[
            False,
            True,
            False,
        ],
    ).reset_index(
        drop=True
    )

    dataframe.insert(
        0,
        "risk_adjusted_rank",
        range(
            1,
            len(dataframe) + 1,
        ),
    )

    # --------------------------------------------------------
    # Stage 5
    # --------------------------------------------------------

    print()
    print(
        "[5/5] Saving outputs..."
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    generate_report(
        dataframe
    )

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print(
        f"Saved: {REPORT_FILE}"
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 74)
    print(
        "WEEK 7 RISK ASSESSMENT COMPLETE"
    )
    print("=" * 74)

    print()
    print(
        "Risk-adjusted candidates:"
    )

    print()

    preview_columns = [
        "risk_adjusted_rank",
        "material_id",
        "formula",
        "performance_score",
        "total_risk_score",
        "risk_rating",
        "risk_adjusted_score",
        "research_profile",
    ]

    print(
        dataframe[
            preview_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "NOTE: Lower risk is better."
    )

    print(
        "Risk-adjusted score combines research upside with explicit "
        "penalties for structural, redox, performance, resource, "
        "and evidence uncertainty."
    )

    print()


if __name__ == "__main__":

    try:

        main()

    except Exception as exc:

        print()
        print("=" * 74)
        print("ERROR")
        print("=" * 74)
        print(exc)
        print()

        sys.exit(1)