"""
MAPPS-Lite Week 7
Final Candidate Head-to-Head Comparison

Purpose
-------
Compare surviving cathode candidates across the strongest Week 6 and
Week 7 evidence dimensions.

This version directly uses explicit Week 6 numeric evidence scores
instead of fuzzy keyword matching.

Input
-----
data/week7_risk_assessment.csv

Outputs
-------
data/week7_candidate_comparison.csv
reports/week7_candidate_comparison.md
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_risk_assessment.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_candidate_comparison.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week7_candidate_comparison.md"
)


# ============================================================
# CONFIGURATION
# ============================================================

FINALIST_COUNT = 5

WEIGHTS = {
    "structure": 0.15,
    "redox": 0.20,
    "performance": 0.25,
    "risk": 0.20,
    "evidence": 0.10,
    "confidence": 0.10,
}


# ============================================================
# HELPERS
# ============================================================

def safe_float(value: Any) -> float | None:
    """
    Convert value to finite float.
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
    Normalize text.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def clamp_100(value: float) -> float:
    """
    Clamp score to 0-100.
    """

    return max(
        0.0,
        min(
            100.0,
            value,
        ),
    )


def format_value(
    value: Any,
    digits: int = 2,
) -> str:
    """
    Format Markdown values.
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


def first_numeric(
    row: pd.Series,
    columns: list[str],
) -> float | None:
    """
    Return first usable numeric field.
    """

    for column in columns:

        if column not in row.index:
            continue

        value = safe_float(
            row.get(column)
        )

        if value is not None:
            return value

    return None


# ============================================================
# LOAD DATA
# ============================================================

def load_risk_assessment() -> pd.DataFrame:
    """
    Load Week 7 risk assessment.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "\nCould not find Week 7 risk assessment:\n"
            f"{INPUT_FILE}\n\n"
            "Run src/assess_candidate_risks.py first."
        )

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    if dataframe.empty:

        raise ValueError(
            "week7_risk_assessment.csv contains no candidates."
        )

    required = [
        "material_id",
        "formula",
        "structure_score",
        "redox_score",
        "performance_score",
        "total_risk_score",
        "risk_rating",
    ]

    missing = [
        column
        for column in required
        if column not in dataframe.columns
    ]

    if missing:

        raise ValueError(
            "Missing required columns:\n"
            + ", ".join(missing)
        )

    return dataframe.copy()


# ============================================================
# SCORE NORMALIZATION
# ============================================================

def normalize_score(
    value: float | None,
) -> float | None:
    """
    Normalize likely 0-1 or 0-100 scores.

    If the value is between 0 and 1, convert to 0-100.
    Otherwise clamp to 0-100.
    """

    if value is None:
        return None

    if 0 <= value <= 1:
        value *= 100

    return clamp_100(
        value
    )


# ============================================================
# WEEK 6 EXPLICIT EVIDENCE
# ============================================================

def get_prefixed_value(
    row: pd.Series,
    suffixes: list[str],
) -> float | None:
    """
    Search merged Week 6 columns using exact suffix names.

    assess_candidate_risks.py prefixes Week 6 columns as:

        week6_final_<column>
        week6_literature_<column>
        week6_synthesis_<column>
        week6_resource_<column>
        week6_transport_<column>
        week6_provenance_<column>
    """

    for suffix in suffixes:

        # First try exact direct column.
        if suffix in row.index:

            value = safe_float(
                row.get(suffix)
            )

            if value is not None:
                return value

        # Then search prefixed Week 6 variants.
        for column in row.index:

            column_text = str(
                column
            )

            if column_text.endswith(
                f"_{suffix}"
            ):

                value = safe_float(
                    row.get(column)
                )

                if value is not None:
                    return value

    return None


def calculate_week6_evidence(
    row: pd.Series,
) -> tuple[
    float,
    dict[str, float],
    list[str],
]:
    """
    Calculate evidence quality from explicit Week 6 metrics.

    Components
    ----------
    Provenance          20%
    Literature          25%
    Synthesis           20%
    Transport           15%
    Resources           10%
    Week 6 confidence   10%
    """

    notes: list[str] = []

    # --------------------------------------------------------
    # Provenance
    # --------------------------------------------------------

    provenance = normalize_score(
        get_prefixed_value(
            row,
            [
                "provenance_evidence_score",
                "provenance_support_score",
            ],
        )
    )

    # --------------------------------------------------------
    # Literature
    # --------------------------------------------------------

    literature = normalize_score(
        get_prefixed_value(
            row,
            [
                "literature_evidence_score",
                "literature_support_score",
            ],
        )
    )

    # --------------------------------------------------------
    # Synthesis
    # --------------------------------------------------------

    synthesis = normalize_score(
        get_prefixed_value(
            row,
            [
                "synthesis_feasibility_score",
            ],
        )
    )

    # --------------------------------------------------------
    # Transport
    # --------------------------------------------------------

    transport = normalize_score(
        get_prefixed_value(
            row,
            [
                "electronic_accessibility_score",
                "week6_li_network_score",
            ],
        )
    )

    # --------------------------------------------------------
    # Resources
    # --------------------------------------------------------

    resource = normalize_score(
        get_prefixed_value(
            row,
            [
                "resource_practicality_score",
            ],
        )
    )

    # --------------------------------------------------------
    # Week 6 research confidence
    # --------------------------------------------------------

    confidence_numeric = normalize_score(
        get_prefixed_value(
            row,
            [
                "research_priority_score",
                "technical_merit_score",
            ],
        )
    )

    # --------------------------------------------------------
    # Fallback handling
    # --------------------------------------------------------

    component_values = {
        "provenance": provenance,
        "literature": literature,
        "synthesis": synthesis,
        "transport": transport,
        "resource": resource,
        "week6_quality": confidence_numeric,
    }

    available = {
        key: value
        for key, value in component_values.items()
        if value is not None
    }

    if not available:

        return (
            50.0,
            {
                key: 50.0
                for key in component_values
            },
            [
                "No explicit Week 6 evidence metrics were available."
            ],
        )

    # Missing components use neutral 50 rather than zero.
    completed = {
        key: (
            value
            if value is not None
            else 50.0
        )
        for key, value in component_values.items()
    }

    evidence_score = (
        0.20 * completed["provenance"]
        + 0.25 * completed["literature"]
        + 0.20 * completed["synthesis"]
        + 0.15 * completed["transport"]
        + 0.10 * completed["resource"]
        + 0.10 * completed["week6_quality"]
    )

    # --------------------------------------------------------
    # Notes
    # --------------------------------------------------------

    if completed["literature"] >= 75:
        notes.append(
            "Strong literature evidence."
        )

    elif completed["literature"] < 40:
        notes.append(
            "Literature evidence remains weak."
        )

    if completed["provenance"] >= 75:
        notes.append(
            "Strong provenance support."
        )

    elif completed["provenance"] < 40:
        notes.append(
            "Provenance support is limited."
        )

    if completed["synthesis"] >= 75:
        notes.append(
            "Synthesis feasibility appears favorable."
        )

    elif completed["synthesis"] < 40:
        notes.append(
            "Synthesis feasibility remains uncertain."
        )

    if completed["transport"] >= 75:
        notes.append(
            "Transport/electronic-accessibility screening is favorable."
        )

    elif completed["transport"] < 40:
        notes.append(
            "Transport/electronic-accessibility screening is weak."
        )

    if completed["resource"] >= 75:
        notes.append(
            "Resource practicality appears favorable."
        )

    elif completed["resource"] < 40:
        notes.append(
            "Resource practicality is a concern."
        )

    return (
        round(
            evidence_score,
            1,
        ),
        {
            key: round(
                value,
                1,
            )
            for key, value in completed.items()
        },
        notes,
    )


# ============================================================
# CONFIDENCE
# ============================================================

def confidence_to_score(
    confidence: Any,
) -> float:
    """
    Convert qualitative confidence to numeric score.
    """

    text = safe_text(
        confidence
    ).upper()

    if text == "HIGH":
        return 100.0

    if text == "MODERATE":
        return 75.0

    if text == "LOW":
        return 40.0

    return 50.0


def calculate_combined_confidence(
    row: pd.Series,
) -> tuple[float, str]:
    """
    Combine Week 7 confidence signals.
    """

    structure = confidence_to_score(
        row.get(
            "structure_confidence"
        )
    )

    redox = confidence_to_score(
        row.get(
            "redox_confidence"
        )
    )

    performance = confidence_to_score(
        row.get(
            "performance_confidence"
        )
    )

    combined = (
        0.30 * structure
        + 0.40 * redox
        + 0.30 * performance
    )

    if combined >= 85:
        label = "HIGH"

    elif combined >= 65:
        label = "MODERATE"

    else:
        label = "LOW"

    return (
        round(
            combined,
            1,
        ),
        label,
    )


# ============================================================
# COMPARISON SCORE
# ============================================================

def calculate_comparison_score(
    *,
    structure_score: float,
    redox_score: float,
    performance_score: float,
    risk_score: float,
    evidence_score: float,
    confidence_score: float,
) -> float:
    """
    Calculate final Week 7 comparison score.
    """

    risk_quality = (
        100.0
        - risk_score
    )

    result = (
        WEIGHTS["structure"]
        * structure_score

        + WEIGHTS["redox"]
        * redox_score

        + WEIGHTS["performance"]
        * performance_score

        + WEIGHTS["risk"]
        * risk_quality

        + WEIGHTS["evidence"]
        * evidence_score

        + WEIGHTS["confidence"]
        * confidence_score
    )

    return round(
        clamp_100(
            result
        ),
        1,
    )


# ============================================================
# TIERING
# ============================================================

def classify_comparison_tier(
    score: float,
    risk_score: float,
    confidence: str,
) -> str:
    """
    Assign comparison tier.
    """

    if (
        score >= 80
        and risk_score <= 25
        and confidence in {
            "HIGH",
            "MODERATE",
        }
    ):
        return "TIER_1_FINALIST"

    if (
        score >= 70
        and risk_score <= 40
    ):
        return "TIER_2_STRONG"

    if score >= 60:
        return "TIER_3_RESEARCH"

    if score >= 45:
        return "TIER_4_REVIEW"

    return "TIER_5_DEPRIORITIZE"


# ============================================================
# STRENGTHS / CAVEATS
# ============================================================

def generate_summary(
    row: pd.Series,
    evidence_score: float,
    confidence_label: str,
) -> tuple[list[str], list[str]]:
    """
    Generate concise comparison interpretation.
    """

    strengths: list[str] = []
    caveats: list[str] = []

    structure_score = safe_float(
        row.get(
            "structure_score"
        )
    ) or 0.0

    redox_score = safe_float(
        row.get(
            "redox_score"
        )
    ) or 0.0

    performance_score = safe_float(
        row.get(
            "performance_score"
        )
    ) or 0.0

    risk_score = safe_float(
        row.get(
            "total_risk_score"
        )
    )

    if risk_score is None:
        risk_score = 100.0

    capacity = safe_float(
        row.get(
            "screening_capacity_mAh_g"
        )
    )

    energy = safe_float(
        row.get(
            "screening_specific_energy_Wh_kg"
        )
    )

    electrons = safe_float(
        row.get(
            "formal_redox_electrons"
        )
    )

    voltage = safe_float(
        row.get(
            "estimated_average_voltage_V"
        )
    )

    # Strengths

    if structure_score >= 85:
        strengths.append(
            "Strong structural profile."
        )

    if redox_score >= 85:
        strengths.append(
            "Strong redox plausibility."
        )

    if performance_score >= 72:
        strengths.append(
            "Promising theoretical-performance profile."
        )

    if (
        capacity is not None
        and capacity >= 130
    ):
        strengths.append(
            "Competitive conservative capacity."
        )

    if (
        energy is not None
        and energy >= 500
    ):
        strengths.append(
            "Competitive estimated specific energy."
        )

    if risk_score <= 20:
        strengths.append(
            "Low aggregate research risk."
        )

    if evidence_score >= 70:
        strengths.append(
            "Strong Week 6 supporting evidence."
        )

    if confidence_label == "HIGH":
        strengths.append(
            "High confidence in current interpretation."
        )

    # Caveats

    if (
        electrons is not None
        and electrons >= 3
    ):
        caveats.append(
            "Requires deep multi-electron delithiation."
        )

    if (
        voltage is not None
        and voltage >= 4.2
    ):
        caveats.append(
            "High-voltage operation may challenge electrolyte stability."
        )

    if risk_score > 35:
        caveats.append(
            "Aggregate research risk is elevated."
        )

    if evidence_score < 50:
        caveats.append(
            "Supporting Week 6 evidence remains limited."
        )

    if confidence_label == "LOW":
        caveats.append(
            "Current conclusions have low confidence."
        )

    if not strengths:
        strengths.append(
            "No dominant strength beyond baseline screening."
        )

    if not caveats:
        caveats.append(
            "No major comparison-level caveat identified."
        )

    return (
        strengths,
        caveats,
    )


# ============================================================
# SINGLE CANDIDATE
# ============================================================

def analyze_candidate(
    row: pd.Series,
) -> dict[str, Any]:
    """
    Build complete comparison metrics.
    """

    result = row.to_dict()

    structure_score = safe_float(
        row.get(
            "structure_score"
        )
    ) or 0.0

    redox_score = safe_float(
        row.get(
            "redox_score"
        )
    ) or 0.0

    performance_score = safe_float(
        row.get(
            "performance_score"
        )
    ) or 0.0

    risk_score = safe_float(
        row.get(
            "total_risk_score"
        )
    )

    if risk_score is None:
        risk_score = 100.0

    # --------------------------------------------------------
    # Explicit Week 6 evidence
    # --------------------------------------------------------

    (
        evidence_score,
        evidence_components,
        evidence_notes,
    ) = calculate_week6_evidence(
        row
    )

    # --------------------------------------------------------
    # Week 7 confidence
    # --------------------------------------------------------

    confidence_score, confidence_label = (
        calculate_combined_confidence(
            row
        )
    )

    # --------------------------------------------------------
    # Comparison
    # --------------------------------------------------------

    comparison_score = (
        calculate_comparison_score(
            structure_score=structure_score,
            redox_score=redox_score,
            performance_score=performance_score,
            risk_score=risk_score,
            evidence_score=evidence_score,
            confidence_score=confidence_score,
        )
    )

    comparison_tier = (
        classify_comparison_tier(
            comparison_score,
            risk_score,
            confidence_label,
        )
    )

    strengths, caveats = generate_summary(
        row,
        evidence_score,
        confidence_label,
    )

    result.update(
        {
            "comparison_structure_component":
                round(
                    structure_score,
                    1,
                ),

            "comparison_redox_component":
                round(
                    redox_score,
                    1,
                ),

            "comparison_performance_component":
                round(
                    performance_score,
                    1,
                ),

            "comparison_risk_quality_component":
                round(
                    100.0 - risk_score,
                    1,
                ),

            "evidence_provenance_score":
                evidence_components[
                    "provenance"
                ],

            "evidence_literature_score":
                evidence_components[
                    "literature"
                ],

            "evidence_synthesis_score":
                evidence_components[
                    "synthesis"
                ],

            "evidence_transport_score":
                evidence_components[
                    "transport"
                ],

            "evidence_resource_score":
                evidence_components[
                    "resource"
                ],

            "evidence_week6_quality_score":
                evidence_components[
                    "week6_quality"
                ],

            "comparison_evidence_score":
                evidence_score,

            "comparison_confidence_score":
                confidence_score,

            "comparison_confidence":
                confidence_label,

            "comparison_score":
                comparison_score,

            "comparison_tier":
                comparison_tier,

            "comparison_strengths":
                " | ".join(
                    strengths
                ),

            "comparison_caveats":
                " | ".join(
                    caveats
                ),

            "comparison_evidence_notes":
                " | ".join(
                    evidence_notes
                ),
        }
    )

    return result


# ============================================================
# FINALIST SELECTION
# ============================================================

def select_finalists(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select top Week 7 finalists.
    """

    result = dataframe.copy()

    confidence_order = {
        "HIGH": 3,
        "MODERATE": 2,
        "LOW": 1,
    }

    result["_confidence_order"] = (
        result[
            "comparison_confidence"
        ]
        .map(
            confidence_order
        )
        .fillna(
            0
        )
    )

    result = result.sort_values(
        [
            "comparison_score",
            "total_risk_score",
            "_confidence_order",
        ],
        ascending=[
            False,
            True,
            False,
        ],
    ).reset_index(
        drop=True
    )

    result["comparison_rank"] = range(
        1,
        len(result) + 1,
    )

    result["week7_finalist"] = (
        result[
            "comparison_rank"
        ]
        <= FINALIST_COUNT
    )

    result["week7_finalist_status"] = np.where(
        result[
            "week7_finalist"
        ],
        "FINALIST",
        "NOT_SELECTED",
    )

    result = result.drop(
        columns=[
            "_confidence_order"
        ]
    )

    return result


# ============================================================
# REPORT
# ============================================================

def generate_report(
    dataframe: pd.DataFrame,
) -> None:
    """
    Generate Week 7 comparison report.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ranked = dataframe.sort_values(
        "comparison_rank"
    )

    finalists = ranked[
        ranked[
            "week7_finalist"
        ]
        == True
    ]

    lines: list[str] = []

    lines.append(
        "# MAPPS-Lite Week 7 Candidate Comparison"
    )

    lines.append("")

    lines.append("## Objective")
    lines.append("")

    lines.append(
        "This stage compares surviving cathode candidates using "
        "structural quality, redox plausibility, theoretical "
        "performance, explicit research risk, Week 6 evidence, "
        "and confidence."
    )

    lines.append("")

    lines.append(
        "Unlike the earlier comparison implementation, Week 6 "
        "evidence is now derived from explicit numeric evidence "
        "fields rather than text keyword matching."
    )

    lines.append("")

    # ========================================================
    # Weighting
    # ========================================================

    lines.append(
        "## Comparison Weighting"
    )

    lines.append("")

    lines.append(
        "- Structure: **15%**"
    )

    lines.append(
        "- Redox chemistry: **20%**"
    )

    lines.append(
        "- Performance: **25%**"
    )

    lines.append(
        "- Risk quality: **20%**"
    )

    lines.append(
        "- Week 6 evidence: **10%**"
    )

    lines.append(
        "- Confidence: **10%**"
    )

    lines.append("")

    # ========================================================
    # Evidence weighting
    # ========================================================

    lines.append(
        "## Week 6 Evidence Composition"
    )

    lines.append("")

    lines.append(
        "- Literature: **25%**"
    )

    lines.append(
        "- Provenance: **20%**"
    )

    lines.append(
        "- Synthesis feasibility: **20%**"
    )

    lines.append(
        "- Transport/electronic accessibility: **15%**"
    )

    lines.append(
        "- Resource practicality: **10%**"
    )

    lines.append(
        "- Overall Week 6 quality: **10%**"
    )

    lines.append("")

    # ========================================================
    # Ranking
    # ========================================================

    lines.append(
        "## Head-to-Head Ranking"
    )

    lines.append("")

    lines.append(
        "| Rank | Material | Formula | Structure | Redox | "
        "Performance | Risk | Evidence | Confidence | Final Score | Tier |"
    )

    lines.append(
        "|---:|---|---|---:|---:|---:|---:|---:|---|---:|---|"
    )

    for _, row in ranked.iterrows():

        lines.append(
            f"| {int(row['comparison_rank'])} "
            f"| {format_value(row.get('material_id'))} "
            f"| {format_value(row.get('formula'))} "
            f"| {format_value(row.get('structure_score'), 1)} "
            f"| {format_value(row.get('redox_score'), 1)} "
            f"| {format_value(row.get('performance_score'), 1)} "
            f"| {format_value(row.get('total_risk_score'), 1)} "
            f"| {format_value(row.get('comparison_evidence_score'), 1)} "
            f"| {format_value(row.get('comparison_confidence'))} "
            f"| {format_value(row.get('comparison_score'), 1)} "
            f"| {format_value(row.get('comparison_tier'))} |"
        )

    lines.append("")

    # ========================================================
    # Finalists
    # ========================================================

    lines.append(
        "## Provisional Week 7 Finalists"
    )

    lines.append("")

    lines.append(
        f"The top **{len(finalists)}** candidates are retained "
        "for final evidence-confidence scoring."
    )

    lines.append("")

    for _, row in finalists.iterrows():

        lines.append(
            f"### #{int(row['comparison_rank'])} "
            f"{format_value(row.get('formula'))} "
            f"({format_value(row.get('material_id'))})"
        )

        lines.append("")

        lines.append(
            f"- Comparison score: "
            f"**{format_value(row.get('comparison_score'), 1)}/100**"
        )

        lines.append(
            f"- Tier: "
            f"**{format_value(row.get('comparison_tier'))}**"
        )

        lines.append(
            f"- Structure: "
            f"{format_value(row.get('structure_score'), 1)}"
        )

        lines.append(
            f"- Redox: "
            f"{format_value(row.get('redox_score'), 1)}"
        )

        lines.append(
            f"- Performance: "
            f"{format_value(row.get('performance_score'), 1)}"
        )

        lines.append(
            f"- Risk: "
            f"{format_value(row.get('total_risk_score'), 1)} "
            f"({format_value(row.get('risk_rating'))})"
        )

        lines.append(
            f"- Week 6 evidence: "
            f"**{format_value(row.get('comparison_evidence_score'), 1)}**"
        )

        lines.append(
            f"- Literature evidence: "
            f"{format_value(row.get('evidence_literature_score'), 1)}"
        )

        lines.append(
            f"- Provenance evidence: "
            f"{format_value(row.get('evidence_provenance_score'), 1)}"
        )

        lines.append(
            f"- Synthesis feasibility: "
            f"{format_value(row.get('evidence_synthesis_score'), 1)}"
        )

        lines.append(
            f"- Transport/accessibility: "
            f"{format_value(row.get('evidence_transport_score'), 1)}"
        )

        lines.append(
            f"- Resource practicality: "
            f"{format_value(row.get('evidence_resource_score'), 1)}"
        )

        lines.append(
            f"- Confidence: "
            f"**{format_value(row.get('comparison_confidence'))}**"
        )

        strengths = safe_text(
            row.get(
                "comparison_strengths"
            )
        )

        caveats = safe_text(
            row.get(
                "comparison_caveats"
            )
        )

        if strengths:

            lines.append("")
            lines.append(
                "**Strengths**"
            )

            lines.append("")

            for item in strengths.split(
                " | "
            ):

                lines.append(
                    f"- {item}"
                )

        if caveats:

            lines.append("")
            lines.append(
                "**Caveats**"
            )

            lines.append("")

            for item in caveats.split(
                " | "
            ):

                lines.append(
                    f"- {item}"
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
        "Candidates rank highly only when strong Week 7 physical "
        "performance is supported by manageable risk and credible "
        "Week 6 evidence."
    )

    lines.append("")

    lines.append(
        "The evidence score is no longer neutral across all materials. "
        "Candidates with stronger literature, provenance, synthesis, "
        "transport, and resource support should now receive a measurable "
        "advantage."
    )

    lines.append("")

    lines.append(
        "The next stage will explicitly separate research potential "
        "from evidence confidence before producing the final Week 7 "
        "recommendation."
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
    Run Week 7 candidate comparison.
    """

    print()
    print("=" * 76)
    print("MAPPS-LITE WEEK 7")
    print("FINAL CANDIDATE HEAD-TO-HEAD COMPARISON")
    print("=" * 76)

    print()
    print(
        "[1/4] Loading Week 7 risk assessment..."
    )

    candidates = load_risk_assessment()

    print(
        f"Loaded {len(candidates)} candidates."
    )

    print()
    print(
        "[2/4] Building comparison metrics with explicit Week 6 evidence..."
    )

    results: list[dict[str, Any]] = []

    total = len(
        candidates
    )

    for index, (_, row) in enumerate(
        candidates.iterrows(),
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
                    "comparison_evidence_score": 0.0,
                    "comparison_confidence_score": 0.0,
                    "comparison_confidence": "LOW",
                    "comparison_score": 0.0,
                    "comparison_tier": "TIER_5_DEPRIORITIZE",
                    "comparison_strengths": "",
                    "comparison_caveats":
                        f"Comparison failed: {exc}",
                }
            )

        results.append(
            result
        )

    dataframe = pd.DataFrame(
        results
    )

    print()
    print(
        "[3/4] Selecting provisional Week 7 finalists..."
    )

    dataframe = select_finalists(
        dataframe
    )

    print()
    print(
        "[4/4] Saving comparison outputs..."
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

    print()
    print("=" * 76)
    print(
        "WEEK 7 CANDIDATE COMPARISON COMPLETE"
    )
    print("=" * 76)

    print()
    print(
        "Head-to-head ranking:"
    )
    print()

    preview_columns = [
        "comparison_rank",
        "material_id",
        "formula",
        "structure_score",
        "redox_score",
        "performance_score",
        "total_risk_score",
        "comparison_evidence_score",
        "comparison_confidence",
        "comparison_score",
        "comparison_tier",
        "week7_finalist_status",
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
        "Week 6 evidence components:"
    )
    print()

    evidence_preview = [
        "material_id",
        "evidence_literature_score",
        "evidence_provenance_score",
        "evidence_synthesis_score",
        "evidence_transport_score",
        "evidence_resource_score",
        "comparison_evidence_score",
    ]

    print(
        dataframe[
            evidence_preview
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print()
    print(
        f"Provisional finalists selected: "
        f"{int(dataframe['week7_finalist'].sum())}"
    )

    print()

    finalists = dataframe[
        dataframe[
            "week7_finalist"
        ]
        == True
    ]

    for _, row in finalists.iterrows():

        print(
            f"  #{int(row['comparison_rank'])}: "
            f"{row['material_id']} "
            f"{row['formula']} "
            f"(score={row['comparison_score']:.1f}, "
            f"evidence={row['comparison_evidence_score']:.1f})"
        )

    print()
    print(
        "NOTE: Week 6 evidence is now based on explicit numeric "
        "validation scores."
    )

    print()


if __name__ == "__main__":

    try:

        main()

    except Exception as exc:

        print()
        print("=" * 76)
        print("ERROR")
        print("=" * 76)
        print(exc)
        print()

        sys.exit(1)