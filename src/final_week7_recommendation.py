"""
MAPPS-Lite Week 7
Final Research Recommendation

Purpose
-------
Produce the final Week 7 research recommendation after integrating:

1. Crystal-structure analysis
2. Redox chemistry
3. Theoretical performance
4. Explicit risk assessment
5. Head-to-head comparison
6. Evidence-confidence scoring

The final system distinguishes:

- VALIDATED_REFERENCE
- PRIMARY_DISCOVERY_RECOMMENDATION
- SECONDARY_DISCOVERY_RECOMMENDATION
- HIGH_VALUE_VALIDATION_TARGET
- RESEARCH_SHORTLIST
- EXPLORATORY
- DEPRIORITIZE

Inputs
------
data/week7_evidence_scores.csv

Outputs
-------
data/week7_final_ranking.csv
reports/week7_final_recommendation.md
reports/week7_progress.md

Scientific Principle
--------------------
Known cathode controls are retained as validation references.

They are NOT allowed to automatically become the project's primary
discovery recommendation simply because they possess stronger
historical literature evidence.

Discovery recommendations emphasize intrinsic research potential,
reasonable evidence support, manageable risk, and novelty.
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
    / "week7_evidence_scores.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_final_ranking.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week7_final_recommendation.md"
)

PROGRESS_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week7_progress.md"
)


# ============================================================
# FINAL SCORE WEIGHTS
# ============================================================

# The final score is a summary measure.
#
# It does NOT determine the candidate's role by itself.
#
# Candidate role and discovery/control status are treated separately.

FINAL_SCORE_WEIGHTS = {
    "research_potential": 0.40,
    "evidence_confidence": 0.20,
    "comparison_score": 0.15,
    "risk_quality": 0.15,
    "novelty": 0.10,
}


# ============================================================
# HELPERS
# ============================================================

def safe_float(
    value: Any,
) -> float | None:
    """
    Convert value to finite float.
    """

    try:

        if value is None:
            return None

        number = float(
            value
        )

        if not np.isfinite(
            number
        ):
            return None

        return number

    except (
        TypeError,
        ValueError,
    ):
        return None


def safe_text(
    value: Any,
) -> str:
    """
    Normalize text.
    """

    if value is None:
        return ""

    try:

        if pd.isna(
            value
        ):
            return ""

    except (
        TypeError,
        ValueError,
    ):
        pass

    return str(
        value
    ).strip()


def safe_bool(
    value: Any,
) -> bool:
    """
    Convert common boolean-like values.
    """

    if isinstance(
        value,
        (
            bool,
            np.bool_,
        ),
    ):
        return bool(
            value
        )

    text = safe_text(
        value
    ).lower()

    return text in {
        "true",
        "1",
        "yes",
        "y",
    }


def clamp_100(
    value: float,
) -> float:
    """
    Clamp a score to 0-100.
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
    digits: int = 1,
) -> str:
    """
    Format values for Markdown.
    """

    if value is None:
        return "N/A"

    try:

        if pd.isna(
            value
        ):
            return "N/A"

    except (
        TypeError,
        ValueError,
    ):
        pass

    if isinstance(
        value,
        (
            float,
            np.floating,
        ),
    ):

        return (
            f"{value:.{digits}f}"
        )

    return str(
        value
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_evidence_scores() -> pd.DataFrame:
    """
    Load Week 7 evidence-confidence results.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "\nCould not find Week 7 evidence scores:\n"
            f"{INPUT_FILE}\n\n"
            "Run src/score_evidence_confidence.py first."
        )

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    if dataframe.empty:

        raise ValueError(
            "week7_evidence_scores.csv contains no candidates."
        )

    required = [
        "material_id",
        "formula",
        "candidate_role",
        "is_control_candidate",
        "research_potential_score",
        "evidence_confidence_score",
        "evidence_supported_research_score",
        "novelty_score",
        "validation_priority_score",
        "comparison_score",
        "total_risk_score",
    ]

    missing = [
        column
        for column in required
        if column not in dataframe.columns
    ]

    if missing:

        raise ValueError(
            "Missing required Week 7 fields:\n"
            + ", ".join(
                missing
            )
        )

    return dataframe.copy()


# ============================================================
# FINAL SUMMARY SCORE
# ============================================================

def calculate_final_score(
    row: pd.Series,
) -> float:
    """
    Calculate final Week 7 research-summary score.

    Components
    ----------
    Research potential       40%
    Evidence confidence      20%
    Comparison score         15%
    Risk quality             15%
    Novelty                  10%

    Controls receive a neutral novelty value because novelty should
    not artificially penalize an established validation reference.
    """

    potential = safe_float(
        row.get(
            "research_potential_score"
        )
    ) or 0.0

    evidence = safe_float(
        row.get(
            "evidence_confidence_score"
        )
    ) or 0.0

    comparison = safe_float(
        row.get(
            "comparison_score"
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

    novelty = safe_float(
        row.get(
            "novelty_score"
        )
    )

    if novelty is None:
        novelty = 50.0

    is_control = safe_bool(
        row.get(
            "is_control_candidate"
        )
    )

    if is_control:

        # Controls are not discovery candidates.
        # Novelty should therefore be neutral.
        novelty_component = 50.0

    else:

        novelty_component = novelty

    score = (
        FINAL_SCORE_WEIGHTS[
            "research_potential"
        ]
        * potential

        + FINAL_SCORE_WEIGHTS[
            "evidence_confidence"
        ]
        * evidence

        + FINAL_SCORE_WEIGHTS[
            "comparison_score"
        ]
        * comparison

        + FINAL_SCORE_WEIGHTS[
            "risk_quality"
        ]
        * risk_quality

        + FINAL_SCORE_WEIGHTS[
            "novelty"
        ]
        * novelty_component
    )

    return round(
        clamp_100(
            score
        ),
        1,
    )


# ============================================================
# RECOMMENDATION ROLE
# ============================================================

def assign_recommendation_roles(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign final Week 7 research roles.

    The primary and secondary discovery recommendations are selected
    using the existing discovery ranking.

    High-value validation targets are candidates with high modeled
    potential but substantial unresolved validation needs.
    """

    result = dataframe.copy()

    result[
        "final_recommendation"
    ] = ""

    # --------------------------------------------------------
    # Controls
    # --------------------------------------------------------

    control_mask = (
        result[
            "is_control_candidate"
        ]
        .apply(
            safe_bool
        )
    )

    for index in result[
        control_mask
    ].index:

        potential = safe_float(
            result.loc[
                index,
                "research_potential_score",
            ]
        ) or 0.0

        evidence = safe_float(
            result.loc[
                index,
                "evidence_confidence_score",
            ]
        ) or 0.0

        if (
            potential >= 70
            and evidence >= 70
        ):

            recommendation = (
                "VALIDATED_REFERENCE"
            )

        else:

            recommendation = (
                "REFERENCE_CONTROL"
            )

        result.loc[
            index,
            "final_recommendation",
        ] = recommendation

    # --------------------------------------------------------
    # Discovery candidates
    # --------------------------------------------------------

    discoveries = result[
        ~control_mask
    ].copy()

    if (
        "discovery_rank"
        in discoveries.columns
    ):

        discoveries[
            "discovery_rank"
        ] = pd.to_numeric(
            discoveries[
                "discovery_rank"
            ],
            errors="coerce",
        )

    else:

        discoveries[
            "discovery_rank"
        ] = np.nan

    discoveries = discoveries.sort_values(
        [
            "discovery_rank",
            "discovery_priority_score",
        ],
        ascending=[
            True,
            False,
        ],
        na_position="last",
    )

    # --------------------------------------------------------
    # Primary discovery
    # --------------------------------------------------------

    if len(
        discoveries
    ) >= 1:

        primary_index = (
            discoveries.index[
                0
            ]
        )

        result.loc[
            primary_index,
            "final_recommendation",
        ] = (
            "PRIMARY_DISCOVERY_RECOMMENDATION"
        )

    # --------------------------------------------------------
    # Secondary discovery
    # --------------------------------------------------------

    if len(
        discoveries
    ) >= 2:

        secondary_index = (
            discoveries.index[
                1
            ]
        )

        result.loc[
            secondary_index,
            "final_recommendation",
        ] = (
            "SECONDARY_DISCOVERY_RECOMMENDATION"
        )

    # --------------------------------------------------------
    # Remaining candidates
    # --------------------------------------------------------

    for index in discoveries.index:

        current = safe_text(
            result.loc[
                index,
                "final_recommendation",
            ]
        )

        if current:
            continue

        potential = safe_float(
            result.loc[
                index,
                "research_potential_score",
            ]
        ) or 0.0

        evidence = safe_float(
            result.loc[
                index,
                "evidence_confidence_score",
            ]
        ) or 0.0

        validation_priority = safe_float(
            result.loc[
                index,
                "validation_priority_score",
            ]
        ) or 0.0

        risk = safe_float(
            result.loc[
                index,
                "total_risk_score",
            ]
        )

        if risk is None:
            risk = 100.0

        # High potential but clearly under-validated.
        if (
            potential >= 80
            and validation_priority >= 40
        ):

            recommendation = (
                "HIGH_VALUE_VALIDATION_TARGET"
            )

        # Solid research candidate with reasonable modeled potential.
        elif (
            potential >= 65
            and risk <= 45
        ):

            recommendation = (
                "RESEARCH_SHORTLIST"
            )

        # Some remaining exploratory value.
        elif (
            potential >= 50
            and evidence >= 30
        ):

            recommendation = (
                "EXPLORATORY"
            )

        else:

            recommendation = (
                "DEPRIORITIZE"
            )

        result.loc[
            index,
            "final_recommendation",
        ] = recommendation

    return result


# ============================================================
# RECOMMENDED NEXT ACTION
# ============================================================

def determine_next_action(
    row: pd.Series,
) -> str:
    """
    Assign a research action to each recommendation class.
    """

    recommendation = safe_text(
        row.get(
            "final_recommendation"
        )
    )

    if recommendation == "VALIDATED_REFERENCE":

        return (
            "Use as a benchmark/control for validating MAPPS-Lite "
            "capacity, redox, structural, and ranking behavior."
        )

    if recommendation == "REFERENCE_CONTROL":

        return (
            "Retain as a reference material; do not treat as a "
            "novel discovery claim."
        )

    if (
        recommendation
        == "PRIMARY_DISCOVERY_RECOMMENDATION"
    ):

        return (
            "Prioritize literature expansion, phase-specific DFT, "
            "delithiation stability analysis, Li migration analysis, "
            "and synthesis-route validation."
        )

    if (
        recommendation
        == "SECONDARY_DISCOVERY_RECOMMENDATION"
    ):

        return (
            "Perform targeted literature validation, voltage and "
            "delithiation calculations, and synthesis feasibility "
            "review after the primary candidate."
        )

    if (
        recommendation
        == "HIGH_VALUE_VALIDATION_TARGET"
    ):

        return (
            "Resolve literature, provenance, oxidation-state, and "
            "synthesis evidence gaps before expensive computational "
            "or experimental follow-up."
        )

    if (
        recommendation
        == "RESEARCH_SHORTLIST"
    ):

        return (
            "Retain for secondary computational screening and compare "
            "against primary discoveries after additional validation."
        )

    if recommendation == "EXPLORATORY":

        return (
            "Keep as an exploratory candidate only; require stronger "
            "physical or external evidence before promotion."
        )

    return (
        "Deprioritize under the current MAPPS-Lite evidence model."
    )


# ============================================================
# CANDIDATE INTERPRETATION
# ============================================================

def generate_interpretation(
    row: pd.Series,
) -> tuple[
    list[str],
    list[str],
]:
    """
    Generate final candidate strengths and limitations.
    """

    strengths: list[str] = []
    limitations: list[str] = []

    potential = safe_float(
        row.get(
            "research_potential_score"
        )
    ) or 0.0

    evidence = safe_float(
        row.get(
            "evidence_confidence_score"
        )
    ) or 0.0

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

    capacity = safe_float(
        row.get(
            "screening_capacity_mAh_g"
        )
    )

    electrons = safe_float(
        row.get(
            "formal_redox_electrons"
        )
    )

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

    # --------------------------------------------------------
    # Strengths
    # --------------------------------------------------------

    if potential >= 80:

        strengths.append(
            "Very high intrinsic Week 7 research potential."
        )

    elif potential >= 70:

        strengths.append(
            "High intrinsic Week 7 research potential."
        )

    if structure >= 85:

        strengths.append(
            "Strong structural screening result."
        )

    if redox >= 85:

        strengths.append(
            "Strong conventional redox plausibility."
        )

    if performance >= 72:

        strengths.append(
            "Promising theoretical-performance profile."
        )

    if (
        capacity is not None
        and capacity >= 130
    ):

        strengths.append(
            "Competitive conservative gravimetric capacity."
        )

    if risk <= 20:

        strengths.append(
            "Low identified aggregate research risk."
        )

    if evidence >= 75:

        strengths.append(
            "Strong overall external evidence support."
        )

    # --------------------------------------------------------
    # Limitations
    # --------------------------------------------------------

    if evidence < 50:

        limitations.append(
            "Current evidence confidence remains limited."
        )

    if (
        literature is not None
        and literature <= 10
    ):

        limitations.append(
            "Little or no direct cathode literature evidence "
            "was identified."
        )

    if (
        provenance is not None
        and provenance < 40
    ):

        limitations.append(
            "Candidate provenance remains weakly supported."
        )

    if (
        electrons is not None
        and electrons >= 3
    ):

        limitations.append(
            "High formal capacity depends on deep multi-electron "
            "delithiation."
        )

    if risk > 35:

        limitations.append(
            "Aggregate research risk is elevated."
        )

    if not strengths:

        strengths.append(
            "Candidate retains baseline screening interest."
        )

    if not limitations:

        limitations.append(
            "No major final-stage limitation was identified "
            "by the current screening rules."
        )

    return (
        strengths,
        limitations,
    )


# ============================================================
# ANALYZE CANDIDATE
# ============================================================

def analyze_candidate(
    row: pd.Series,
) -> dict[str, Any]:
    """
    Calculate final candidate fields.
    """

    result = row.to_dict()

    final_score = (
        calculate_final_score(
            row
        )
    )

    result[
        "week7_final_score"
    ] = final_score

    return result


# ============================================================
# FINAL RANKING
# ============================================================

def build_final_ranking(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create final Week 7 ranking and recommendation roles.
    """

    rows: list[dict[str, Any]] = []

    for _, row in dataframe.iterrows():

        rows.append(
            analyze_candidate(
                row
            )
        )

    result = pd.DataFrame(
        rows
    )

    # Assign research roles after all scores exist.
    result = assign_recommendation_roles(
        result
    )

    # Add research actions and interpretation.
    actions: list[str] = []
    strength_strings: list[str] = []
    limitation_strings: list[str] = []

    for _, row in result.iterrows():

        actions.append(
            determine_next_action(
                row
            )
        )

        strengths, limitations = (
            generate_interpretation(
                row
            )
        )

        strength_strings.append(
            " | ".join(
                strengths
            )
        )

        limitation_strings.append(
            " | ".join(
                limitations
            )
        )

    result[
        "recommended_next_action"
    ] = actions

    result[
        "final_strengths"
    ] = strength_strings

    result[
        "final_limitations"
    ] = limitation_strings

    # --------------------------------------------------------
    # Overall research score ranking
    # --------------------------------------------------------

    result = result.sort_values(
        [
            "week7_final_score",
            "research_potential_score",
            "evidence_confidence_score",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).reset_index(
        drop=True
    )

    result.insert(
        0,
        "week7_final_rank",
        range(
            1,
            len(
                result
            ) + 1,
        ),
    )

    # --------------------------------------------------------
    # Discovery recommendation rank
    # --------------------------------------------------------

    result[
        "week7_discovery_recommendation_rank"
    ] = np.nan

    discovery_mask = (
        result[
            "is_control_candidate"
        ]
        .apply(
            lambda value: not safe_bool(
                value
            )
        )
    )

    discoveries = result[
        discovery_mask
    ].sort_values(
        [
            "discovery_rank",
            "week7_final_score",
        ],
        ascending=[
            True,
            False,
        ],
        na_position="last",
    )

    for rank, index in enumerate(
        discoveries.index,
        start=1,
    ):

        result.loc[
            index,
            "week7_discovery_recommendation_rank",
        ] = rank

    return result


# ============================================================
# FINAL RECOMMENDATION REPORT
# ============================================================

def generate_final_report(
    dataframe: pd.DataFrame,
) -> None:
    """
    Generate final Week 7 research recommendation.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines: list[str] = []

    lines.append(
        "# MAPPS-Lite Week 7 Final Research Recommendation"
    )

    lines.append("")

    # ========================================================
    # Executive summary
    # ========================================================

    lines.append(
        "## Executive Summary"
    )

    lines.append("")

    lines.append(
        "Week 7 moved MAPPS-Lite from broad scientific validation "
        "to candidate-level physical and chemical analysis."
    )

    lines.append("")

    lines.append(
        "The final recommendation distinguishes established cathode "
        "controls from discovery candidates and explicitly separates "
        "research potential from evidence confidence."
    )

    lines.append("")

    # ========================================================
    # Recommendation groups
    # ========================================================

    recommendation_order = [
        (
            "VALIDATED_REFERENCE",
            "Validated Reference",
        ),
        (
            "PRIMARY_DISCOVERY_RECOMMENDATION",
            "Primary Discovery Recommendation",
        ),
        (
            "SECONDARY_DISCOVERY_RECOMMENDATION",
            "Secondary Discovery Recommendation",
        ),
        (
            "HIGH_VALUE_VALIDATION_TARGET",
            "High-Value Validation Targets",
        ),
        (
            "RESEARCH_SHORTLIST",
            "Additional Research Shortlist",
        ),
        (
            "EXPLORATORY",
            "Exploratory Candidates",
        ),
        (
            "DEPRIORITIZE",
            "Deprioritized Candidates",
        ),
    ]

    for recommendation, heading in (
        recommendation_order
    ):

        subset = dataframe[
            dataframe[
                "final_recommendation"
            ]
            == recommendation
        ].copy()

        if subset.empty:
            continue

        lines.append(
            f"## {heading}"
        )

        lines.append("")

        subset = subset.sort_values(
            "week7_final_score",
            ascending=False,
        )

        for _, row in subset.iterrows():

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
                f"### {formula} ({material_id})"
            )

            lines.append("")

            lines.append(
                f"- Final Week 7 score: "
                f"**{format_value(row.get('week7_final_score'))}/100**"
            )

            lines.append(
                f"- Research potential: "
                f"**{format_value(row.get('research_potential_score'))}/100**"
            )

            lines.append(
                f"- Evidence confidence: "
                f"**{format_value(row.get('evidence_confidence_score'))}/100**"
            )

            lines.append(
                f"- Comparison score: "
                f"{format_value(row.get('comparison_score'))}/100"
            )

            lines.append(
                f"- Total risk: "
                f"{format_value(row.get('total_risk_score'))}/100 "
                f"({format_value(row.get('risk_rating'))})"
            )

            lines.append(
                f"- Screening capacity: "
                f"{format_value(row.get('screening_capacity_mAh_g'))} mAh/g"
            )

            lines.append(
                f"- Screening specific energy: "
                f"{format_value(row.get('screening_specific_energy_Wh_kg'), 0)} "
                f"Wh/kg"
            )

            lines.append(
                f"- Validation priority: "
                f"{format_value(row.get('validation_priority_score'))}/100 "
                f"({format_value(row.get('validation_priority_class'))})"
            )

            discovery_rank = row.get(
                "discovery_rank"
            )

            if (
                discovery_rank is not None
                and not pd.isna(
                    discovery_rank
                )
            ):

                lines.append(
                    f"- Discovery rank: "
                    f"**#{int(discovery_rank)}**"
                )

            lines.append(
                f"- Recommended action: "
                f"{format_value(row.get('recommended_next_action'))}"
            )

            strengths = safe_text(
                row.get(
                    "final_strengths"
                )
            )

            limitations = safe_text(
                row.get(
                    "final_limitations"
                )
            )

            if strengths:

                lines.append("")
                lines.append(
                    "**Primary strengths**"
                )
                lines.append("")

                for item in strengths.split(
                    " | "
                ):

                    lines.append(
                        f"- {item}"
                    )

            if limitations:

                lines.append("")
                lines.append(
                    "**Primary limitations**"
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
    # Final comparison table
    # ========================================================

    lines.append(
        "## Final Candidate Table"
    )

    lines.append("")

    lines.append(
        "| Overall Rank | Material | Formula | Role | Potential | "
        "Evidence | Risk | Final Score |"
    )

    lines.append(
        "|---:|---|---|---|---:|---:|---:|---:|"
    )

    for _, row in dataframe.sort_values(
        "week7_final_rank"
    ).iterrows():

        lines.append(
            f"| {int(row['week7_final_rank'])} "
            f"| {format_value(row.get('material_id'))} "
            f"| {format_value(row.get('formula'))} "
            f"| {format_value(row.get('final_recommendation'))} "
            f"| {format_value(row.get('research_potential_score'))} "
            f"| {format_value(row.get('evidence_confidence_score'))} "
            f"| {format_value(row.get('total_risk_score'))} "
            f"| {format_value(row.get('week7_final_score'))} |"
        )

    lines.append("")

    # ========================================================
    # Scientific conclusion
    # ========================================================

    lines.append(
        "## Scientific Conclusion"
    )

    lines.append("")

    lines.append(
        "The final Week 7 ranking should not be interpreted as a "
        "claim that the top discovery candidate is already proven to "
        "outperform commercial cathodes."
    )

    lines.append("")

    lines.append(
        "Instead, MAPPS-Lite identifies materials whose structural "
        "plausibility, conventional redox chemistry, estimated "
        "capacity, risk profile, and available evidence justify "
        "additional research."
    )

    lines.append("")

    lines.append(
        "Known cathode controls serve a different purpose: they test "
        "whether the pipeline reproduces credible conclusions for "
        "established materials."
    )

    lines.append("")

    lines.append(
        "For discovery candidates, the highest-value next steps are "
        "phase-specific DFT calculations, delithiation stability "
        "analysis, Li migration-barrier calculations, expanded "
        "literature review, and synthesis-route validation."
    )

    lines.append("")

    REPORT_FILE.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )


# ============================================================
# WEEK 7 PROGRESS REPORT
# ============================================================

def generate_progress_report(
    dataframe: pd.DataFrame,
) -> None:
    """
    Generate Week 7 progress summary.
    """

    PROGRESS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    controls = dataframe[
        dataframe[
            "is_control_candidate"
        ]
        .apply(
            safe_bool
        )
    ]

    discoveries = dataframe[
        ~dataframe[
            "is_control_candidate"
        ]
        .apply(
            safe_bool
        )
    ]

    primary = dataframe[
        dataframe[
            "final_recommendation"
        ]
        == "PRIMARY_DISCOVERY_RECOMMENDATION"
    ]

    secondary = dataframe[
        dataframe[
            "final_recommendation"
        ]
        == "SECONDARY_DISCOVERY_RECOMMENDATION"
    ]

    validation_targets = dataframe[
        dataframe[
            "final_recommendation"
        ]
        == "HIGH_VALUE_VALIDATION_TARGET"
    ]

    lines: list[str] = []

    lines.append(
        "# MAPPS-Lite Week 7 Progress"
    )

    lines.append("")

    lines.append(
        "## Week 7 Objective"
    )

    lines.append("")

    lines.append(
        "Week 7 performed a candidate-level deep dive on the strongest "
        "materials surviving Week 6."
    )

    lines.append("")

    lines.append(
        "The objective was to move beyond broad screening scores and "
        "determine whether each candidate has physically plausible "
        "structure, redox chemistry, capacity, manageable risk, and "
        "sufficient evidence to justify additional investigation."
    )

    lines.append("")

    # ========================================================
    # Completed stages
    # ========================================================

    lines.append(
        "## Completed Stages"
    )

    lines.append("")

    lines.append(
        "### Stage 1 - Crystal Structure Analysis"
    )

    lines.append("")

    lines.append(
        "- Added `src/analyze_candidate_structures.py`."
    )

    lines.append(
        "- Retrieved Materials Project structures for the Week 6 finalists."
    )

    lines.append(
        "- Evaluated crystal system, space group, lattice geometry, "
        "Li content, Li-Li spacing, framework family, and structural risk."
    )

    lines.append(
        "- Generated `data/week7_candidate_structures.csv`."
    )

    lines.append(
        "- Generated `reports/week7_structure_analysis.md`."
    )

    lines.append("")

    lines.append(
        "### Stage 2 - Redox Chemistry"
    )

    lines.append("")

    lines.append(
        "- Added `src/analyze_redox_chemistry.py`."
    )

    lines.append(
        "- Inferred charge-balanced oxidation states."
    )

    lines.append(
        "- Identified redox-active transition metals."
    )

    lines.append(
        "- Estimated conventional Li-coupled electron inventories."
    )

    lines.append(
        "- Generated `data/week7_redox_analysis.csv`."
    )

    lines.append(
        "- Generated `reports/week7_redox_analysis.md`."
    )

    lines.append("")

    lines.append(
        "### Stage 3 - Theoretical Performance"
    )

    lines.append("")

    lines.append(
        "- Added `src/estimate_theoretical_performance.py`."
    )

    lines.append(
        "- Calculated formal theoretical capacity using electron "
        "inventory and molar mass."
    )

    lines.append(
        "- Added conservative utilization penalties for deep delithiation."
    )

    lines.append(
        "- Added heuristic voltage classes and specific-energy estimates."
    )

    lines.append(
        "- Generated `data/week7_theoretical_performance.csv`."
    )

    lines.append(
        "- Generated `reports/week7_theoretical_performance.md`."
    )

    lines.append("")

    lines.append(
        "### Stage 4 - Risk Assessment"
    )

    lines.append("")

    lines.append(
        "- Added `src/assess_candidate_risks.py`."
    )

    lines.append(
        "- Evaluated structural, redox, performance, resource, and "
        "evidence failure modes."
    )

    lines.append(
        "- Generated `data/week7_risk_assessment.csv`."
    )

    lines.append(
        "- Generated `reports/week7_risk_assessment.md`."
    )

    lines.append("")

    lines.append(
        "### Stage 5 - Head-to-Head Comparison"
    )

    lines.append("")

    lines.append(
        "- Added `src/compare_final_candidates.py`."
    )

    lines.append(
        "- Integrated explicit Week 6 literature, provenance, synthesis, "
        "transport, and resource evidence."
    )

    lines.append(
        "- Selected five provisional finalists."
    )

    lines.append(
        "- Generated `data/week7_candidate_comparison.csv`."
    )

    lines.append(
        "- Generated `reports/week7_candidate_comparison.md`."
    )

    lines.append("")

    lines.append(
        "### Stage 6 - Evidence Confidence"
    )

    lines.append("")

    lines.append(
        "- Added `src/score_evidence_confidence.py`."
    )

    lines.append(
        "- Separated intrinsic research potential from evidence confidence."
    )

    lines.append(
        "- Distinguished known cathode controls from discovery candidates."
    )

    lines.append(
        "- Generated a dedicated discovery ranking and validation priority."
    )

    lines.append(
        "- Generated `data/week7_evidence_scores.csv`."
    )

    lines.append(
        "- Generated `reports/week7_evidence_confidence.md`."
    )

    lines.append("")

    lines.append(
        "### Stage 7 - Final Research Recommendation"
    )

    lines.append("")

    lines.append(
        "- Added `src/final_week7_recommendation.py`."
    )

    lines.append(
        "- Assigned validated-reference, discovery, validation-target, "
        "research-shortlist, exploratory, and deprioritized roles."
    )

    lines.append(
        "- Generated `data/week7_final_ranking.csv`."
    )

    lines.append(
        "- Generated `reports/week7_final_recommendation.md`."
    )

    lines.append("")

    # ========================================================
    # Outcome
    # ========================================================

    lines.append(
        "## Week 7 Outcome"
    )

    lines.append("")

    lines.append(
        f"- Total candidates deeply analyzed: **{len(dataframe)}**"
    )

    lines.append(
        f"- Known cathode controls: **{len(controls)}**"
    )

    lines.append(
        f"- Discovery candidates: **{len(discoveries)}**"
    )

    lines.append(
        f"- High-value validation targets: "
        f"**{len(validation_targets)}**"
    )

    lines.append("")

    if not controls.empty:

        best_control = controls.sort_values(
            "evidence_supported_research_score",
            ascending=False,
        ).iloc[0]

        lines.append(
            f"- Validated reference: "
            f"**{best_control['formula']} "
            f"({best_control['material_id']})**"
        )

    if not primary.empty:

        row = primary.iloc[
            0
        ]

        lines.append(
            f"- Primary discovery recommendation: "
            f"**{row['formula']} "
            f"({row['material_id']})**"
        )

    if not secondary.empty:

        row = secondary.iloc[
            0
        ]

        lines.append(
            f"- Secondary discovery recommendation: "
            f"**{row['formula']} "
            f"({row['material_id']})**"
        )

    lines.append("")

    # ========================================================
    # Scientific interpretation
    # ========================================================

    lines.append(
        "## Scientific Interpretation"
    )

    lines.append("")

    lines.append(
        "Week 7 demonstrated that MAPPS-Lite can reject materials that "
        "appear structurally attractive but lack conventional cathode "
        "redox headroom."
    )

    lines.append("")

    lines.append(
        "The pipeline also successfully distinguished an established "
        "cathode control from less-validated discovery candidates."
    )

    lines.append("")

    lines.append(
        "The resulting discovery recommendations should be interpreted "
        "as candidates for further computational or experimental "
        "investigation, not as experimentally proven cathodes."
    )

    lines.append("")

    # ========================================================
    # Next phase
    # ========================================================

    lines.append(
        "## Recommended Next Phase"
    )

    lines.append("")

    lines.append(
        "Week 8 should focus on research-grade validation of the primary "
        "and secondary discovery recommendations."
    )

    lines.append("")

    lines.append(
        "Recommended next methods include phase-specific DFT, voltage "
        "calculation from lithiated and delithiated structures, Li-ion "
        "migration-barrier calculations, structural evolution during "
        "delithiation, and more rigorous literature/synthesis validation."
    )

    lines.append("")

    PROGRESS_FILE.write_text(
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
    Run final Week 7 recommendation.
    """

    print()
    print("=" * 80)
    print("MAPPS-LITE WEEK 7")
    print("FINAL RESEARCH RECOMMENDATION")
    print("=" * 80)

    # --------------------------------------------------------
    # Stage 1
    # --------------------------------------------------------

    print()
    print(
        "[1/4] Loading Week 7 evidence-confidence results..."
    )

    candidates = load_evidence_scores()

    print(
        f"Loaded {len(candidates)} candidates."
    )

    # --------------------------------------------------------
    # Stage 2
    # --------------------------------------------------------

    print()
    print(
        "[2/4] Building final Week 7 ranking..."
    )

    dataframe = build_final_ranking(
        candidates
    )

    # --------------------------------------------------------
    # Stage 3
    # --------------------------------------------------------

    print()
    print(
        "[3/4] Saving final dataset..."
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    # --------------------------------------------------------
    # Stage 4
    # --------------------------------------------------------

    print()
    print(
        "[4/4] Generating Week 7 reports..."
    )

    generate_final_report(
        dataframe
    )

    generate_progress_report(
        dataframe
    )

    print(
        f"Saved: {REPORT_FILE}"
    )

    print(
        f"Saved: {PROGRESS_FILE}"
    )

    # ========================================================
    # Terminal summary
    # ========================================================

    print()
    print("=" * 80)
    print(
        "WEEK 7 COMPLETE"
    )
    print("=" * 80)

    print()
    print(
        "Final research roles:"
    )
    print()

    preview_columns = [
        "week7_final_rank",
        "material_id",
        "formula",
        "final_recommendation",
        "research_potential_score",
        "evidence_confidence_score",
        "total_risk_score",
        "week7_final_score",
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

    # --------------------------------------------------------
    # Control
    # --------------------------------------------------------

    controls = dataframe[
        dataframe[
            "final_recommendation"
        ]
        .isin(
            [
                "VALIDATED_REFERENCE",
                "REFERENCE_CONTROL",
            ]
        )
    ]

    print()
    print(
        "Validated reference/control:"
    )

    if controls.empty:

        print(
            "  None"
        )

    else:

        for _, row in controls.iterrows():

            print(
                f"  {row['material_id']} "
                f"{row['formula']} "
                f"({row['final_recommendation']})"
            )

    # --------------------------------------------------------
    # Primary discovery
    # --------------------------------------------------------

    primary = dataframe[
        dataframe[
            "final_recommendation"
        ]
        == "PRIMARY_DISCOVERY_RECOMMENDATION"
    ]

    print()
    print(
        "Primary discovery recommendation:"
    )

    if primary.empty:

        print(
            "  None"
        )

    else:

        row = primary.iloc[
            0
        ]

        print(
            f"  {row['material_id']} "
            f"{row['formula']} "
            f"(potential={row['research_potential_score']:.1f}, "
            f"evidence={row['evidence_confidence_score']:.1f})"
        )

    # --------------------------------------------------------
    # Secondary
    # --------------------------------------------------------

    secondary = dataframe[
        dataframe[
            "final_recommendation"
        ]
        == "SECONDARY_DISCOVERY_RECOMMENDATION"
    ]

    print()
    print(
        "Secondary discovery recommendation:"
    )

    if secondary.empty:

        print(
            "  None"
        )

    else:

        row = secondary.iloc[
            0
        ]

        print(
            f"  {row['material_id']} "
            f"{row['formula']} "
            f"(potential={row['research_potential_score']:.1f}, "
            f"evidence={row['evidence_confidence_score']:.1f})"
        )

    # --------------------------------------------------------
    # Validation targets
    # --------------------------------------------------------

    targets = dataframe[
        dataframe[
            "final_recommendation"
        ]
        == "HIGH_VALUE_VALIDATION_TARGET"
    ]

    print()
    print(
        "High-value validation targets:"
    )

    if targets.empty:

        print(
            "  None"
        )

    else:

        for _, row in targets.iterrows():

            print(
                f"  {row['material_id']} "
                f"{row['formula']} "
                f"(validation priority="
                f"{row['validation_priority_score']:.1f})"
            )

    print()
    print(
        "Week 7 outputs are ready for review and Git commit."
    )
    print()


if __name__ == "__main__":

    try:

        main()

    except Exception as exc:

        print()
        print("=" * 80)
        print("ERROR")
        print("=" * 80)
        print(exc)
        print()

        sys.exit(1)