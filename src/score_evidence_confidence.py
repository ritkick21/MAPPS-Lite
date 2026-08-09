"""
MAPPS-Lite Week 7
Evidence Confidence and Research Potential Scoring

Purpose
-------
Separate two fundamentally different questions:

1. Research Potential:
   How promising does the material appear from its structure,
   redox chemistry, theoretical performance, and risk profile?

2. Evidence Confidence:
   How strongly is that assessment supported by literature,
   provenance, synthesis evidence, transport evidence,
   resource data, and Week 7 inference confidence?

The script also distinguishes known cathode controls from
discovery candidates so established materials do not automatically
dominate the discovery ranking simply because they have more
published evidence.

Input
-----
data/week7_candidate_comparison.csv

Outputs
-------
data/week7_evidence_scores.csv
reports/week7_evidence_confidence.md
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
    / "week7_candidate_comparison.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_evidence_scores.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week7_evidence_confidence.md"
)


# ============================================================
# WEIGHTING
# ============================================================

# Research potential intentionally EXCLUDES evidence.
#
# This answers:
# "How promising does the material itself appear?"

POTENTIAL_WEIGHTS = {
    "structure": 0.20,
    "redox": 0.25,
    "performance": 0.35,
    "risk_quality": 0.20,
}


# Evidence confidence answers:
# "How strongly do we trust the current assessment?"

EVIDENCE_WEIGHTS = {
    "literature": 0.25,
    "provenance": 0.20,
    "synthesis": 0.15,
    "transport": 0.10,
    "resource": 0.05,
    "week6_quality": 0.10,
    "week7_confidence": 0.15,
}


# Discovery priority combines:
#
# physical research potential
# + evidence support
# + novelty
#
# It is only intended for NON-CONTROL candidates.

DISCOVERY_WEIGHTS = {
    "potential": 0.70,
    "evidence": 0.20,
    "novelty": 0.10,
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
    Normalize text values.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def safe_bool(value: Any) -> bool | None:
    """
    Convert common boolean representations.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            bool,
            np.bool_,
        ),
    ):
        return bool(value)

    text = str(value).strip().lower()

    if text in {
        "true",
        "1",
        "yes",
        "y",
    }:
        return True

    if text in {
        "false",
        "0",
        "no",
        "n",
    }:
        return False

    return None


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


def normalize_score(
    value: float | None,
) -> float | None:
    """
    Convert likely 0-1 or 0-100 score to 0-100.
    """

    if value is None:
        return None

    if 0 <= value <= 1:
        value *= 100.0

    return clamp_100(
        value
    )


def format_value(
    value: Any,
    digits: int = 1,
) -> str:
    """
    Format report values.
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


def find_suffix_value(
    row: pd.Series,
    suffixes: list[str],
) -> Any:
    """
    Find a direct or prefixed column ending in one of the
    requested names.

    Example:
        is_known_cathode_control

    can match:
        week6_final_is_known_cathode_control
    """

    for suffix in suffixes:

        if suffix in row.index:

            value = row.get(
                suffix
            )

            if value is not None:
                return value

        for column in row.index:

            column_name = str(
                column
            )

            if column_name.endswith(
                f"_{suffix}"
            ):

                value = row.get(
                    column
                )

                if value is not None:
                    return value

    return None


# ============================================================
# LOAD INPUT
# ============================================================

def load_comparison_data() -> pd.DataFrame:
    """
    Load Week 7 candidate comparison.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "\nCould not find Week 7 comparison file:\n"
            f"{INPUT_FILE}\n\n"
            "Run src/compare_final_candidates.py first."
        )

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    if dataframe.empty:

        raise ValueError(
            "week7_candidate_comparison.csv contains no candidates."
        )

    required = [
        "material_id",
        "formula",
        "structure_score",
        "redox_score",
        "performance_score",
        "total_risk_score",
        "comparison_evidence_score",
        "comparison_confidence_score",
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
# CONTROL / DISCOVERY ROLE
# ============================================================

def determine_candidate_role(
    row: pd.Series,
) -> tuple[str, bool]:
    """
    Determine whether candidate is a known cathode control.

    Week 6 already generated an explicit
    is_known_cathode_control field.
    """

    control_value = find_suffix_value(
        row,
        [
            "is_known_cathode_control",
        ],
    )

    is_control = safe_bool(
        control_value
    )

    if is_control is True:

        return (
            "KNOWN_CATHODE_CONTROL",
            True,
        )

    return (
        "DISCOVERY_CANDIDATE",
        False,
    )


# ============================================================
# RESEARCH POTENTIAL
# ============================================================

def calculate_research_potential(
    row: pd.Series,
) -> float:
    """
    Calculate intrinsic research potential.

    Evidence is intentionally excluded.

    Components
    ----------
    Structure      20%
    Redox          25%
    Performance    35%
    Risk quality   20%
    """

    structure = safe_float(
        row.get(
            "structure_score"
        )
    ) or 0.0

    redox = safe_float(
        row.get(
            "redox_score"
        )
    ) or 0.0

    performance = safe_float(
        row.get(
            "performance_score"
        )
    ) or 0.0

    risk = safe_float(
        row.get(
            "total_risk_score"
        )
    )

    if risk is None:
        risk = 100.0

    risk_quality = (
        100.0
        - risk
    )

    potential = (
        POTENTIAL_WEIGHTS["structure"]
        * structure

        + POTENTIAL_WEIGHTS["redox"]
        * redox

        + POTENTIAL_WEIGHTS["performance"]
        * performance

        + POTENTIAL_WEIGHTS["risk_quality"]
        * risk_quality
    )

    return round(
        clamp_100(
            potential
        ),
        1,
    )


def classify_research_potential(
    score: float,
) -> str:
    """
    Classify physical research potential.
    """

    if score >= 80:
        return "VERY_HIGH"

    if score >= 70:
        return "HIGH"

    if score >= 60:
        return "MODERATE"

    if score >= 45:
        return "LOW"

    return "VERY_LOW"


# ============================================================
# EVIDENCE CONFIDENCE
# ============================================================

def calculate_evidence_confidence(
    row: pd.Series,
) -> tuple[float, dict[str, float]]:
    """
    Calculate evidence confidence independently of potential.
    """

    literature = normalize_score(
        safe_float(
            row.get(
                "evidence_literature_score"
            )
        )
    )

    provenance = normalize_score(
        safe_float(
            row.get(
                "evidence_provenance_score"
            )
        )
    )

    synthesis = normalize_score(
        safe_float(
            row.get(
                "evidence_synthesis_score"
            )
        )
    )

    transport = normalize_score(
        safe_float(
            row.get(
                "evidence_transport_score"
            )
        )
    )

    resource = normalize_score(
        safe_float(
            row.get(
                "evidence_resource_score"
            )
        )
    )

    week6_quality = normalize_score(
        safe_float(
            row.get(
                "evidence_week6_quality_score"
            )
        )
    )

    week7_confidence = normalize_score(
        safe_float(
            row.get(
                "comparison_confidence_score"
            )
        )
    )

    # Missing evidence remains neutral rather than becoming zero.
    components = {
        "literature":
            literature if literature is not None else 50.0,

        "provenance":
            provenance if provenance is not None else 50.0,

        "synthesis":
            synthesis if synthesis is not None else 50.0,

        "transport":
            transport if transport is not None else 50.0,

        "resource":
            resource if resource is not None else 50.0,

        "week6_quality":
            week6_quality if week6_quality is not None else 50.0,

        "week7_confidence":
            week7_confidence if week7_confidence is not None else 50.0,
    }

    confidence = (
        EVIDENCE_WEIGHTS["literature"]
        * components["literature"]

        + EVIDENCE_WEIGHTS["provenance"]
        * components["provenance"]

        + EVIDENCE_WEIGHTS["synthesis"]
        * components["synthesis"]

        + EVIDENCE_WEIGHTS["transport"]
        * components["transport"]

        + EVIDENCE_WEIGHTS["resource"]
        * components["resource"]

        + EVIDENCE_WEIGHTS["week6_quality"]
        * components["week6_quality"]

        + EVIDENCE_WEIGHTS["week7_confidence"]
        * components["week7_confidence"]
    )

    return (
        round(
            clamp_100(
                confidence
            ),
            1,
        ),
        {
            key: round(
                value,
                1,
            )
            for key, value in components.items()
        },
    )


def classify_evidence_confidence(
    score: float,
) -> str:
    """
    Classify evidence confidence.
    """

    if score >= 80:
        return "HIGH"

    if score >= 60:
        return "MODERATE"

    if score >= 40:
        return "LIMITED"

    return "LOW"


# ============================================================
# NOVELTY
# ============================================================

def get_novelty_score(
    row: pd.Series,
) -> float:
    """
    Retrieve Week 6 novelty score when available.

    Neutral fallback = 50.
    """

    novelty_value = find_suffix_value(
        row,
        [
            "week6_novelty_score",
            "novelty_score",
        ],
    )

    novelty = normalize_score(
        safe_float(
            novelty_value
        )
    )

    if novelty is None:
        return 50.0

    return round(
        novelty,
        1,
    )


# ============================================================
# EVIDENCE-ADJUSTED RESEARCH SCORE
# ============================================================

def calculate_supported_research_score(
    potential: float,
    evidence_confidence: float,
) -> float:
    """
    Calculate evidence-supported research score.

    Evidence does NOT replace physical potential.

    Instead, confidence determines how much of the potential
    we are currently willing to treat as well supported.

    Confidence multiplier ranges from 0.70 to 1.00.
    """

    multiplier = (
        0.70
        + 0.30
        * (
            evidence_confidence
            / 100.0
        )
    )

    score = (
        potential
        * multiplier
    )

    return round(
        clamp_100(
            score
        ),
        1,
    )


# ============================================================
# DISCOVERY PRIORITY
# ============================================================

def calculate_discovery_priority(
    *,
    potential: float,
    evidence: float,
    novelty: float,
    is_control: bool,
) -> float | None:
    """
    Calculate discovery-specific priority.

    Known controls do not receive a discovery-priority score.
    """

    if is_control:
        return None

    score = (
        DISCOVERY_WEIGHTS["potential"]
        * potential

        + DISCOVERY_WEIGHTS["evidence"]
        * evidence

        + DISCOVERY_WEIGHTS["novelty"]
        * novelty
    )

    return round(
        clamp_100(
            score
        ),
        1,
    )


# ============================================================
# RESEARCH PROFILE MATRIX
# ============================================================

def classify_research_profile(
    *,
    potential: float,
    evidence: float,
    is_control: bool,
) -> str:
    """
    Classify candidate using potential vs evidence.
    """

    if is_control:

        if (
            potential >= 70
            and evidence >= 70
        ):
            return "VALIDATED_REFERENCE_CONTROL"

        return "REFERENCE_CONTROL"

    if (
        potential >= 75
        and evidence >= 75
    ):
        return "HIGH_POTENTIAL_HIGH_CONFIDENCE"

    if (
        potential >= 75
        and evidence >= 55
    ):
        return "HIGH_POTENTIAL_MODERATE_CONFIDENCE"

    if potential >= 75:
        return "HIGH_POTENTIAL_UNDERVALIDATED"

    if (
        potential >= 65
        and evidence >= 60
    ):
        return "SUPPORTED_RESEARCH_CANDIDATE"

    if potential >= 65:
        return "DISCOVERY_CANDIDATE_NEEDS_VALIDATION"

    if potential >= 50:
        return "EXPLORATORY_CANDIDATE"

    return "LOW_PRIORITY"


# ============================================================
# VALIDATION PRIORITY
# ============================================================

def calculate_validation_priority(
    potential: float,
    evidence: float,
    is_control: bool,
) -> float:
    """
    Identify candidates where further validation could be valuable.

    High potential + low evidence = high validation priority.

    Controls receive a reduced value because they are not the main
    target of discovery validation.
    """

    evidence_gap = (
        100.0
        - evidence
    )

    score = (
        potential
        * evidence_gap
        / 100.0
    )

    if is_control:
        score *= 0.40

    return round(
        clamp_100(
            score
        ),
        1,
    )


def classify_validation_priority(
    score: float,
) -> str:
    """
    Classify need for further validation.
    """

    if score >= 40:
        return "VERY_HIGH"

    if score >= 28:
        return "HIGH"

    if score >= 16:
        return "MODERATE"

    return "LOW"


# ============================================================
# NOTES
# ============================================================

def generate_notes(
    *,
    row: pd.Series,
    role: str,
    potential: float,
    evidence: float,
    novelty: float,
) -> tuple[list[str], list[str]]:
    """
    Generate interpretation notes.
    """

    positives: list[str] = []
    limitations: list[str] = []

    literature = safe_float(
        row.get(
            "evidence_literature_score"
        )
    )

    provenance = safe_float(
        row.get(
            "evidence_provenance_score"
        )
    )

    synthesis = safe_float(
        row.get(
            "evidence_synthesis_score"
        )
    )

    if role == "KNOWN_CATHODE_CONTROL":

        positives.append(
            "Identified as a known cathode control; useful for "
            "validating MAPPS-Lite against established chemistry."
        )

    else:

        positives.append(
            "Evaluated as a discovery candidate rather than "
            "an established control."
        )

    if potential >= 75:

        positives.append(
            "Intrinsic Week 7 research potential is high."
        )

    if evidence >= 75:

        positives.append(
            "Current conclusions are strongly supported by the "
            "available evidence package."
        )

    if novelty >= 70 and role != "KNOWN_CATHODE_CONTROL":

        positives.append(
            "Week 6 novelty signal supports further discovery-oriented "
            "investigation."
        )

    if (
        literature is not None
        and literature <= 10
    ):

        limitations.append(
            "Little or no direct literature evidence was identified."
        )

    if (
        provenance is not None
        and provenance < 40
    ):

        limitations.append(
            "Provenance support remains weak."
        )

    if (
        synthesis is not None
        and synthesis < 50
    ):

        limitations.append(
            "Synthesis feasibility remains insufficiently supported."
        )

    if (
        potential >= 70
        and evidence < 55
        and role != "KNOWN_CATHODE_CONTROL"
    ):

        limitations.append(
            "High modeled potential currently exceeds the strength "
            "of experimental or literature validation."
        )

    if not limitations:

        limitations.append(
            "No major evidence-confidence limitation identified "
            "at the current screening level."
        )

    return (
        positives,
        limitations,
    )


# ============================================================
# SINGLE CANDIDATE
# ============================================================

def analyze_candidate(
    row: pd.Series,
) -> dict[str, Any]:
    """
    Analyze evidence confidence for one candidate.
    """

    result = row.to_dict()

    # --------------------------------------------------------
    # Role
    # --------------------------------------------------------

    role, is_control = (
        determine_candidate_role(
            row
        )
    )

    # --------------------------------------------------------
    # Research potential
    # --------------------------------------------------------

    research_potential = (
        calculate_research_potential(
            row
        )
    )

    potential_class = (
        classify_research_potential(
            research_potential
        )
    )

    # --------------------------------------------------------
    # Evidence confidence
    # --------------------------------------------------------

    (
        evidence_confidence,
        evidence_components,
    ) = calculate_evidence_confidence(
        row
    )

    evidence_class = (
        classify_evidence_confidence(
            evidence_confidence
        )
    )

    # --------------------------------------------------------
    # Novelty
    # --------------------------------------------------------

    novelty = get_novelty_score(
        row
    )

    # --------------------------------------------------------
    # Evidence-supported potential
    # --------------------------------------------------------

    supported_score = (
        calculate_supported_research_score(
            research_potential,
            evidence_confidence,
        )
    )

    # --------------------------------------------------------
    # Discovery priority
    # --------------------------------------------------------

    discovery_priority = (
        calculate_discovery_priority(
            potential=research_potential,
            evidence=evidence_confidence,
            novelty=novelty,
            is_control=is_control,
        )
    )

    # --------------------------------------------------------
    # Research profile
    # --------------------------------------------------------

    research_profile = (
        classify_research_profile(
            potential=research_potential,
            evidence=evidence_confidence,
            is_control=is_control,
        )
    )

    # --------------------------------------------------------
    # Validation priority
    # --------------------------------------------------------

    validation_priority = (
        calculate_validation_priority(
            research_potential,
            evidence_confidence,
            is_control,
        )
    )

    validation_class = (
        classify_validation_priority(
            validation_priority
        )
    )

    # --------------------------------------------------------
    # Notes
    # --------------------------------------------------------

    positives, limitations = (
        generate_notes(
            row=row,
            role=role,
            potential=research_potential,
            evidence=evidence_confidence,
            novelty=novelty,
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    result.update(
        {
            "candidate_role":
                role,

            "is_control_candidate":
                is_control,

            "research_potential_score":
                research_potential,

            "research_potential_class":
                potential_class,

            "evidence_confidence_score":
                evidence_confidence,

            "evidence_confidence_class":
                evidence_class,

            "confidence_literature_component":
                evidence_components[
                    "literature"
                ],

            "confidence_provenance_component":
                evidence_components[
                    "provenance"
                ],

            "confidence_synthesis_component":
                evidence_components[
                    "synthesis"
                ],

            "confidence_transport_component":
                evidence_components[
                    "transport"
                ],

            "confidence_resource_component":
                evidence_components[
                    "resource"
                ],

            "confidence_week6_quality_component":
                evidence_components[
                    "week6_quality"
                ],

            "confidence_week7_component":
                evidence_components[
                    "week7_confidence"
                ],

            "novelty_score":
                novelty,

            "evidence_supported_research_score":
                supported_score,

            "discovery_priority_score":
                discovery_priority,

            "research_profile":
                research_profile,

            "validation_priority_score":
                validation_priority,

            "validation_priority_class":
                validation_class,

            "evidence_positive_notes":
                " | ".join(
                    positives
                ),

            "evidence_limitations":
                " | ".join(
                    limitations
                ),
        }
    )

    return result


# ============================================================
# RANKING
# ============================================================

def assign_rankings(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign separate overall, control, and discovery rankings.
    """

    result = dataframe.copy()

    # --------------------------------------------------------
    # Overall supported research ranking
    # --------------------------------------------------------

    result = result.sort_values(
        [
            "evidence_supported_research_score",
            "research_potential_score",
        ],
        ascending=[
            False,
            False,
        ],
    ).reset_index(
        drop=True
    )

    result["evidence_rank"] = range(
        1,
        len(result) + 1,
    )

    # --------------------------------------------------------
    # Discovery ranking
    # --------------------------------------------------------

    result["discovery_rank"] = np.nan

    discovery_rows = result[
        result[
            "is_control_candidate"
        ]
        == False
    ].sort_values(
        [
            "discovery_priority_score",
            "research_potential_score",
        ],
        ascending=[
            False,
            False,
        ],
    )

    for rank, index in enumerate(
        discovery_rows.index,
        start=1,
    ):

        result.loc[
            index,
            "discovery_rank",
        ] = rank

    # --------------------------------------------------------
    # Control ranking
    # --------------------------------------------------------

    result["control_rank"] = np.nan

    control_rows = result[
        result[
            "is_control_candidate"
        ]
        == True
    ].sort_values(
        "evidence_supported_research_score",
        ascending=False,
    )

    for rank, index in enumerate(
        control_rows.index,
        start=1,
    ):

        result.loc[
            index,
            "control_rank",
        ] = rank

    return result


# ============================================================
# REPORT
# ============================================================

def generate_report(
    dataframe: pd.DataFrame,
) -> None:
    """
    Generate Week 7 evidence-confidence report.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ranked = dataframe.sort_values(
        "evidence_rank"
    )

    finalists = ranked[
        ranked[
            "week7_finalist"
        ]
        == True
    ].copy()

    controls = ranked[
        ranked[
            "is_control_candidate"
        ]
        == True
    ].copy()

    discoveries = ranked[
        ranked[
            "is_control_candidate"
        ]
        == False
    ].copy()

    discoveries = discoveries.sort_values(
        "discovery_rank"
    )

    lines: list[str] = []

    lines.append(
        "# MAPPS-Lite Week 7 Evidence Confidence Analysis"
    )

    lines.append("")

    # ========================================================
    # Objective
    # ========================================================

    lines.append(
        "## Objective"
    )

    lines.append("")

    lines.append(
        "This stage separates intrinsic research potential from "
        "the confidence supported by the available evidence."
    )

    lines.append("")

    lines.append(
        "Established cathode controls are also separated from "
        "discovery candidates so strong historical evidence does "
        "not automatically determine the discovery ranking."
    )

    lines.append("")

    # ========================================================
    # Definitions
    # ========================================================

    lines.append(
        "## Score Definitions"
    )

    lines.append("")

    lines.append(
        "**Research potential** uses only structure, redox chemistry, "
        "theoretical performance, and risk."
    )

    lines.append("")

    lines.append(
        "**Evidence confidence** uses literature, provenance, synthesis, "
        "transport, resource data, Week 6 quality, and Week 7 inference "
        "confidence."
    )

    lines.append("")

    lines.append(
        "**Discovery priority** is calculated only for candidates that "
        "are not identified as known cathode controls."
    )

    lines.append("")

    # ========================================================
    # Finalist table
    # ========================================================

    lines.append(
        "## Week 7 Finalist Evidence Matrix"
    )

    lines.append("")

    lines.append(
        "| Material | Formula | Role | Potential | Evidence | "
        "Supported Score | Validation Priority | Profile |"
    )

    lines.append(
        "|---|---|---|---:|---:|---:|---:|---|"
    )

    for _, row in finalists.iterrows():

        lines.append(
            f"| {format_value(row.get('material_id'))} "
            f"| {format_value(row.get('formula'))} "
            f"| {format_value(row.get('candidate_role'))} "
            f"| {format_value(row.get('research_potential_score'))} "
            f"| {format_value(row.get('evidence_confidence_score'))} "
            f"| {format_value(row.get('evidence_supported_research_score'))} "
            f"| {format_value(row.get('validation_priority_score'))} "
            f"| {format_value(row.get('research_profile'))} |"
        )

    lines.append("")

    # ========================================================
    # Controls
    # ========================================================

    lines.append(
        "## Known Cathode Controls"
    )

    lines.append("")

    if controls.empty:

        lines.append(
            "No candidates were explicitly identified as known cathode controls."
        )

    else:

        lines.append(
            "Known controls are retained as validation references rather "
            "than treated as direct competitors for discovery priority."
        )

        lines.append("")

        for _, row in controls.iterrows():

            lines.append(
                f"### {format_value(row.get('formula'))} "
                f"({format_value(row.get('material_id'))})"
            )

            lines.append("")

            lines.append(
                f"- Research potential: "
                f"**{format_value(row.get('research_potential_score'))}/100**"
            )

            lines.append(
                f"- Evidence confidence: "
                f"**{format_value(row.get('evidence_confidence_score'))}/100**"
            )

            lines.append(
                f"- Evidence-supported score: "
                f"**{format_value(row.get('evidence_supported_research_score'))}/100**"
            )

            lines.append(
                f"- Role: "
                f"**{format_value(row.get('research_profile'))}**"
            )

            lines.append("")

    # ========================================================
    # Discovery ranking
    # ========================================================

    lines.append(
        "## Discovery Candidate Ranking"
    )

    lines.append("")

    lines.append(
        "| Discovery Rank | Material | Formula | Potential | "
        "Evidence | Novelty | Discovery Priority | Validation Need |"
    )

    lines.append(
        "|---:|---|---|---:|---:|---:|---:|---|"
    )

    for _, row in discoveries.iterrows():

        discovery_rank = row.get(
            "discovery_rank"
        )

        if pd.isna(
            discovery_rank
        ):
            continue

        lines.append(
            f"| {int(discovery_rank)} "
            f"| {format_value(row.get('material_id'))} "
            f"| {format_value(row.get('formula'))} "
            f"| {format_value(row.get('research_potential_score'))} "
            f"| {format_value(row.get('evidence_confidence_score'))} "
            f"| {format_value(row.get('novelty_score'))} "
            f"| {format_value(row.get('discovery_priority_score'))} "
            f"| {format_value(row.get('validation_priority_class'))} |"
        )

    lines.append("")

    # ========================================================
    # Detailed finalists
    # ========================================================

    lines.append(
        "## Finalist Details"
    )

    lines.append("")

    for _, row in finalists.sort_values(
        "evidence_rank"
    ).iterrows():

        lines.append(
            f"### {format_value(row.get('formula'))} "
            f"({format_value(row.get('material_id'))})"
        )

        lines.append("")

        lines.append(
            f"- Candidate role: "
            f"**{format_value(row.get('candidate_role'))}**"
        )

        lines.append(
            f"- Research potential: "
            f"**{format_value(row.get('research_potential_score'))}/100 "
            f"({format_value(row.get('research_potential_class'))})**"
        )

        lines.append(
            f"- Evidence confidence: "
            f"**{format_value(row.get('evidence_confidence_score'))}/100 "
            f"({format_value(row.get('evidence_confidence_class'))})**"
        )

        lines.append(
            f"- Literature confidence component: "
            f"{format_value(row.get('confidence_literature_component'))}"
        )

        lines.append(
            f"- Provenance confidence component: "
            f"{format_value(row.get('confidence_provenance_component'))}"
        )

        lines.append(
            f"- Synthesis confidence component: "
            f"{format_value(row.get('confidence_synthesis_component'))}"
        )

        lines.append(
            f"- Transport confidence component: "
            f"{format_value(row.get('confidence_transport_component'))}"
        )

        lines.append(
            f"- Resource confidence component: "
            f"{format_value(row.get('confidence_resource_component'))}"
        )

        lines.append(
            f"- Novelty score: "
            f"{format_value(row.get('novelty_score'))}"
        )

        lines.append(
            f"- Evidence-supported research score: "
            f"**{format_value(row.get('evidence_supported_research_score'))}/100**"
        )

        discovery_score = row.get(
            "discovery_priority_score"
        )

        if not pd.isna(
            discovery_score
        ):

            lines.append(
                f"- Discovery priority: "
                f"**{format_value(discovery_score)}/100**"
            )

        lines.append(
            f"- Validation priority: "
            f"**{format_value(row.get('validation_priority_score'))}/100 "
            f"({format_value(row.get('validation_priority_class'))})**"
        )

        lines.append(
            f"- Research profile: "
            f"**{format_value(row.get('research_profile'))}**"
        )

        positives = safe_text(
            row.get(
                "evidence_positive_notes"
            )
        )

        limitations = safe_text(
            row.get(
                "evidence_limitations"
            )
        )

        if positives:

            lines.append("")
            lines.append(
                "**Positive interpretation**"
            )

            lines.append("")

            for item in positives.split(
                " | "
            ):

                lines.append(
                    f"- {item}"
                )

        if limitations:

            lines.append("")
            lines.append(
                "**Evidence limitations**"
            )

            lines.append("")

            for item in limitations.split(
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
        "A high research-potential score with low evidence confidence "
        "should be interpreted as a promising but under-validated "
        "discovery opportunity."
    )

    lines.append("")

    lines.append(
        "A high potential score with high evidence confidence indicates "
        "a substantially better-supported candidate, although established "
        "controls should primarily serve as validation references rather "
        "than discovery claims."
    )

    lines.append("")

    lines.append(
        "Validation priority is intentionally highest when modeled "
        "potential is strong but evidence remains weak."
    )

    lines.append("")

    lines.append(
        "The next stage will use these separate potential, evidence, "
        "control, novelty, and validation signals to produce the final "
        "Week 7 research recommendation."
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
    Run Week 7 evidence-confidence scoring.
    """

    print()
    print("=" * 78)
    print("MAPPS-LITE WEEK 7")
    print("EVIDENCE CONFIDENCE AND RESEARCH POTENTIAL SCORING")
    print("=" * 78)

    # --------------------------------------------------------
    # Stage 1
    # --------------------------------------------------------

    print()
    print(
        "[1/4] Loading Week 7 candidate comparison..."
    )

    candidates = load_comparison_data()

    print(
        f"Loaded {len(candidates)} candidates."
    )

    # --------------------------------------------------------
    # Stage 2
    # --------------------------------------------------------

    print()
    print(
        "[2/4] Separating research potential from evidence confidence..."
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
                    "candidate_role":
                        "ANALYSIS_ERROR",

                    "is_control_candidate":
                        False,

                    "research_potential_score":
                        0.0,

                    "research_potential_class":
                        "VERY_LOW",

                    "evidence_confidence_score":
                        0.0,

                    "evidence_confidence_class":
                        "LOW",

                    "novelty_score":
                        50.0,

                    "evidence_supported_research_score":
                        0.0,

                    "discovery_priority_score":
                        0.0,

                    "research_profile":
                        "ANALYSIS_ERROR",

                    "validation_priority_score":
                        0.0,

                    "validation_priority_class":
                        "LOW",

                    "evidence_positive_notes":
                        "",

                    "evidence_limitations":
                        f"Evidence analysis failed: {exc}",
                }
            )

        results.append(
            result
        )

    dataframe = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Stage 3
    # --------------------------------------------------------

    print()
    print(
        "[3/4] Assigning evidence and discovery rankings..."
    )

    dataframe = assign_rankings(
        dataframe
    )

    # --------------------------------------------------------
    # Stage 4
    # --------------------------------------------------------

    print()
    print(
        "[4/4] Saving evidence-confidence outputs..."
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
    print("=" * 78)
    print(
        "WEEK 7 EVIDENCE CONFIDENCE ANALYSIS COMPLETE"
    )
    print("=" * 78)

    print()
    print(
        "Potential vs evidence:"
    )
    print()

    preview_columns = [
        "evidence_rank",
        "material_id",
        "formula",
        "candidate_role",
        "research_potential_score",
        "evidence_confidence_score",
        "evidence_supported_research_score",
        "validation_priority_score",
        "research_profile",
    ]

    print(
        dataframe[
            preview_columns
        ]
        .sort_values(
            "evidence_rank"
        )
        .head(10)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Controls
    # --------------------------------------------------------

    controls = dataframe[
        dataframe[
            "is_control_candidate"
        ]
        == True
    ]

    print()
    print(
        f"Known cathode controls identified: "
        f"{len(controls)}"
    )

    for _, row in controls.iterrows():

        print(
            f"  {row['material_id']} "
            f"{row['formula']} "
            f"(potential={row['research_potential_score']:.1f}, "
            f"evidence={row['evidence_confidence_score']:.1f})"
        )

    # --------------------------------------------------------
    # Discovery ranking
    # --------------------------------------------------------

    discoveries = dataframe[
        dataframe[
            "is_control_candidate"
        ]
        == False
    ].copy()

    discoveries = discoveries.sort_values(
        "discovery_rank"
    )

    print()
    print(
        "Discovery ranking:"
    )
    print()

    discovery_preview = [
        "discovery_rank",
        "material_id",
        "formula",
        "research_potential_score",
        "evidence_confidence_score",
        "novelty_score",
        "discovery_priority_score",
        "validation_priority_class",
    ]

    print(
        discoveries[
            discovery_preview
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "NOTE: Research potential and evidence confidence are "
        "intentionally separate."
    )

    print(
        "Known cathode controls are retained as validation references "
        "but excluded from the discovery-priority ranking."
    )

    print()


if __name__ == "__main__":

    try:

        main()

    except Exception as exc:

        print()
        print("=" * 78)
        print("ERROR")
        print("=" * 78)
        print(exc)
        print()

        sys.exit(1)