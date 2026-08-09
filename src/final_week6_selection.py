from pathlib import Path

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_resource_assessment.csv"
)

RANKING_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_final_ranking.csv"
)

SHORTLIST_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_research_shortlist.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week6_final_selection.md"
)

PROGRESS_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week6_progress.md"
)


# =========================================================
# GENERAL HELPERS
# =========================================================

def safe_float(value, default=0.0):

    try:

        if pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def normalize_100(value):
    """
    Convert a numeric score to a 0-100 scale.

    Handles both:
        0-1
    and
        0-100
    inputs.
    """

    value = safe_float(
        value,
        default=0.0,
    )

    if 0.0 <= value <= 1.0:
        value *= 100.0

    return max(
        0.0,
        min(
            100.0,
            value,
        ),
    )


# =========================================================
# ELECTROCHEMICAL SCORE DETECTION
# =========================================================

def find_electrochemical_column(df):
    """
    Week 5 files may use slightly different names.

    Prefer a true electrochemical score before falling
    back to a broader Week 5 ranking score.
    """

    preferred_columns = [
        "electrochemical_score",
        "electrochem_score",
        "electrochemical_evaluation_score",
        "electrochemical_rating_score",
        "electrode_score",
        "cathode_score",
    ]

    for column in preferred_columns:

        if column in df.columns:
            return column

    # -----------------------------------------------------
    # Search column names heuristically
    # -----------------------------------------------------

    for column in df.columns:

        name = column.lower()

        if (
            "electrochem" in name
            and "score" in name
        ):
            return column

    # -----------------------------------------------------
    # Last-resort Week 5 scores
    # -----------------------------------------------------

    fallback_columns = [
        "final_score",
        "ranking_score",
        "candidate_score",
        "score",
    ]

    for column in fallback_columns:

        if column in df.columns:
            return column

    return None


# =========================================================
# PROVENANCE CONFIDENCE
# =========================================================

def provenance_confidence(
    provenance_class,
):
    """
    Convert provenance classification to 0-100.
    """

    scores = {

        "EXPERIMENTAL_STRUCTURE_EVIDENCE":
            100.0,

        "REFERENCED_PROVENANCE":
            75.0,

        "COMPUTATIONAL_WITH_REFERENCES":
            55.0,

        "LIMITED_PROVENANCE":
            35.0,

        "COMPUTATIONAL_ONLY":
            25.0,
    }

    return scores.get(
        str(provenance_class),
        35.0,
    )


# =========================================================
# LITHIUM NETWORK SCORE
# =========================================================

def li_network_score(
    network_class,
):
    """
    Low-weight structural proxy.

    This is deliberately given only 5% of the final
    technical merit because Li-Li geometry does not
    equal Li-ion mobility.
    """

    scores = {

        "COMPACT_LI_NETWORK":
            100.0,

        "INTERMEDIATE_LI_NETWORK":
            70.0,

        "SPARSE_LI_NETWORK":
            35.0,

        "INSUFFICIENT_LI_NETWORK_DATA":
            50.0,
    }

    return scores.get(
        str(network_class),
        50.0,
    )


# =========================================================
# NOVELTY / DISCOVERY SCORE
# =========================================================

def novelty_score(
    novelty_signal,
):
    """
    Literature exploration score.

    IMPORTANT:
    This is not proof of scientific novelty.

    It only reflects the amount of prior cathode
    literature found by Stage 6.2.
    """

    scores = {

        "UNDEREXPLORED_CATHODE_SIGNAL":
            90.0,

        "INCONCLUSIVE_NO_EXACT_MATCH":
            70.0,

        "BATTERY_STUDIED_NO_DIRECT_CATHODE_SIGNAL":
            60.0,

        "LIMITED_CATHODE_LITERATURE":
            40.0,

        "WELL_STUDIED_CATHODE":
            0.0,
    }

    return scores.get(
        str(novelty_signal),
        50.0,
    )


# =========================================================
# CONTROL DETECTION
# =========================================================

def is_known_control(
    discovery_class,
    novelty_signal,
):

    if (
        discovery_class
        == "KNOWN_CATHODE_CONTROL"
    ):
        return True

    if (
        novelty_signal
        == "WELL_STUDIED_CATHODE"
    ):
        return True

    return False


# =========================================================
# TECHNICAL MERIT
# =========================================================

def technical_merit_score(
    electrochemical,
    synthesis,
    electronic,
    resource,
    provenance,
    li_network,
):
    """
    Final technical score.

    Weighting:

    Electrochemical performance      35%
    Synthesis feasibility            20%
    Electronic accessibility         15%
    Resource practicality            15%
    Provenance confidence            10%
    Li structural descriptor          5%
                                    ----
                                    100%
    """

    score = (

        0.35 * electrochemical
        + 0.20 * synthesis
        + 0.15 * electronic
        + 0.15 * resource
        + 0.10 * provenance
        + 0.05 * li_network
    )

    return round(
        score,
        2,
    )


# =========================================================
# RESEARCH PRIORITY
# =========================================================

def research_priority_score(
    technical_score,
    novelty,
):
    """
    Research priority combines technical merit
    with an exploration bonus.

    Technical merit = 90%
    Literature exploration signal = 10%
    """

    score = (
        0.90 * technical_score
        + 0.10 * novelty
    )

    return round(
        score,
        2,
    )


# =========================================================
# PRIORITY TIERS
# =========================================================

def assign_priority_tier(
    score,
    known_control,
):

    if known_control:
        return "BENCHMARK_CONTROL"

    if score >= 80:
        return "RESEARCH_PRIORITY_1"

    if score >= 70:
        return "RESEARCH_PRIORITY_2"

    if score >= 60:
        return "RESEARCH_PRIORITY_3"

    return "RESEARCH_REVIEW"


# =========================================================
# CONFIDENCE LEVEL
# =========================================================

def research_confidence(
    provenance_class,
    synthesis_score,
):

    synthesis_score = normalize_100(
        synthesis_score
    )

    if (
        provenance_class
        == "EXPERIMENTAL_STRUCTURE_EVIDENCE"
        and synthesis_score >= 70
    ):
        return "HIGH_CONFIDENCE"

    if synthesis_score >= 55:
        return "MODERATE_CONFIDENCE"

    return "LOWER_CONFIDENCE"


# =========================================================
# CANDIDATE INTERPRETATION
# =========================================================

def candidate_interpretation(
    row,
):
    """
    Generate a concise scientific interpretation.
    """

    control = bool(
        row[
            "is_known_cathode_control"
        ]
    )

    discovery_class = str(
        row.get(
            "discovery_class",
            "",
        )
    )

    electronic = str(
        row.get(
            "stage64_transport_class",
            "",
        )
    )

    network = str(
        row.get(
            "li_network_class",
            "",
        )
    )

    if control:

        return (
            "Established cathode retained as a "
            "benchmark rather than a discovery lead."
        )

    if (
        discovery_class
        == "EXPERIMENTALLY_GROUNDED_UNDEREXPLORED"
    ):

        if (
            electronic
            == "FAVORABLE_ELECTRONIC_SIGNAL"
        ):

            return (
                "Experimentally grounded and "
                "underexplored with a favorable "
                "electronic screening signal."
            )

        return (
            "Experimentally grounded and "
            "underexplored; electronic transport "
            "may require engineering or further study."
        )

    if (
        discovery_class
        == "COMPUTATIONAL_DISCOVERY_PLAUSIBLE"
    ):

        if (
            electronic
            == "FAVORABLE_ELECTRONIC_SIGNAL"
        ):

            if network == "SPARSE_LI_NETWORK":

                return (
                    "Promising computational discovery "
                    "with strong electronic accessibility, "
                    "but sparse Li geometry adds transport "
                    "uncertainty."
                )

            return (
                "Promising computational discovery "
                "with favorable electronic screening "
                "and acceptable structural descriptors."
            )

        return (
            "Thermodynamically plausible computational "
            "discovery requiring experimental validation "
            "and deeper transport calculations."
        )

    if (
        discovery_class
        == "KNOWN_BUT_LESS_EXPLORED_CATHODE"
    ):

        return (
            "Previously investigated cathode with "
            "more limited literature than the benchmark "
            "materials."
        )

    return (
        "Candidate remains scientifically interesting "
        "but requires additional validation."
    )


# =========================================================
# REPORT
# =========================================================

def write_report(
    ranking_df,
    shortlist_df,
    electrochemical_column,
):

    lines = []

    lines.append(
        "# MAPPS-Lite Week 6 Final Research Selection"
    )

    lines.append("")

    lines.append(
        "Week 6 combines electrochemical performance, "
        "experimental provenance, literature evidence, "
        "thermodynamic feasibility, electronic screening, "
        "lithium structural descriptors, and resource "
        "practicality."
    )

    lines.append("")

    lines.append(
        "**Important:** the final research-priority score "
        "is a screening metric, not proof that a material "
        "will function successfully as a battery cathode."
    )

    lines.append("")

    lines.append(
        f"- Electrochemical source column: "
        f"`{electrochemical_column}`"
    )

    lines.append(
        f"- Total candidates: "
        f"{len(ranking_df)}"
    )

    lines.append(
        f"- Discovery shortlist: "
        f"{len(shortlist_df)}"
    )

    controls = int(
        ranking_df[
            "is_known_cathode_control"
        ].sum()
    )

    lines.append(
        f"- Benchmark controls: "
        f"{controls}"
    )

    # -----------------------------------------------------
    # Shortlist
    # -----------------------------------------------------

    lines.append("")
    lines.append(
        "## Final Discovery Shortlist"
    )
    lines.append("")

    if shortlist_df.empty:

        lines.append(
            "No candidates passed the discovery "
            "shortlist criteria."
        )

    else:

        for _, row in (
            shortlist_df.iterrows()
        ):

            lines.append(
                f"### #{int(row['research_rank'])} "
                f"{row['material_id']} | "
                f"{row['week6_formula']}"
            )

            lines.append("")

            lines.append(
                "- Research priority score: "
                f"{row['research_priority_score']}"
            )

            lines.append(
                "- Technical merit score: "
                f"{row['technical_merit_score']}"
            )

            lines.append(
                "- Priority tier: "
                f"{row['research_priority_tier']}"
            )

            lines.append(
                "- Confidence: "
                f"{row['research_confidence']}"
            )

            lines.append(
                "- Discovery class: "
                f"{row['discovery_class']}"
            )

            lines.append(
                "- Electrochemical score: "
                f"{row['week6_electrochemical_score']}"
            )

            lines.append(
                "- Synthesis score: "
                f"{row['synthesis_feasibility_score']}"
            )

            lines.append(
                "- Band gap: "
                f"{row['band_gap']} eV"
            )

            lines.append(
                "- Li network: "
                f"{row['li_network_class']}"
            )

            lines.append(
                "- Resource practicality: "
                f"{row['resource_practicality_score']}"
            )

            lines.append(
                "- Interpretation: "
                f"{row['candidate_interpretation']}"
            )

            lines.append("")

    # -----------------------------------------------------
    # Controls
    # -----------------------------------------------------

    lines.append("")
    lines.append(
        "## Benchmark Controls"
    )
    lines.append("")

    control_df = ranking_df[
        ranking_df[
            "is_known_cathode_control"
        ]
    ]

    if control_df.empty:

        lines.append(
            "No established cathode controls "
            "were identified."
        )

    else:

        for _, row in (
            control_df.iterrows()
        ):

            lines.append(
                f"- {row['material_id']} | "
                f"{row['week6_formula']} | "
                f"technical merit "
                f"{row['technical_merit_score']}"
            )

    # -----------------------------------------------------
    # Full ranking
    # -----------------------------------------------------

    lines.append("")
    lines.append(
        "## Full Research Ranking"
    )
    lines.append("")

    for _, row in (
        ranking_df.iterrows()
    ):

        lines.append(
            f"{int(row['research_rank'])}. "
            f"{row['week6_formula']} "
            f"({row['material_id']}) — "
            f"{row['research_priority_score']} — "
            f"{row['research_priority_tier']}"
        )

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )


# =========================================================
# WEEK 6 PROGRESS REPORT
# =========================================================

def write_progress_report(
    ranking_df,
    shortlist_df,
):

    lines = []

    lines.append(
        "# MAPPS-Lite Week 6 Progress"
    )

    lines.append("")

    lines.append(
        "## Objective"
    )

    lines.append("")

    lines.append(
        "Week 6 performed deeper scientific validation "
        "of the Week 5 cathode shortlist."
    )

    lines.append("")

    lines.append(
        "## Completed Stages"
    )

    lines.append("")

    lines.append(
        "1. Candidate provenance validation"
    )

    lines.append(
        "2. Battery literature validation"
    )

    lines.append(
        "3. Synthesis-feasibility assessment"
    )

    lines.append(
        "4. Electronic and Li-network screening"
    )

    lines.append(
        "5. Resource and supply-chain assessment"
    )

    lines.append(
        "6. Final research-priority ranking"
    )

    lines.append("")

    lines.append(
        "## Final Results"
    )

    lines.append("")

    lines.append(
        f"- Candidates evaluated: "
        f"{len(ranking_df)}"
    )

    lines.append(
        f"- Discovery candidates shortlisted: "
        f"{len(shortlist_df)}"
    )

    controls = int(
        ranking_df[
            "is_known_cathode_control"
        ].sum()
    )

    lines.append(
        f"- Known cathode controls: "
        f"{controls}"
    )

    if not shortlist_df.empty:

        top = shortlist_df.iloc[0]

        lines.append(
            "- Highest-priority discovery candidate: "
            f"{top['week6_formula']} "
            f"({top['material_id']})"
        )

        lines.append(
            "- Highest research-priority score: "
            f"{top['research_priority_score']}"
        )

    lines.append("")

    lines.append(
        "## Interpretation"
    )

    lines.append("")

    lines.append(
        "The Week 6 ranking separates established "
        "benchmark cathodes from underexplored discovery "
        "candidates. Scores integrate multiple independent "
        "evidence layers rather than relying only on "
        "thermodynamic stability or a single predicted "
        "electrochemical property."
    )

    PROGRESS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROGRESS_FILE.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 78)
    print("MAPPS-LITE WEEK 6")

    print(
        "STAGE 6.6 - "
        "FINAL RESEARCH-PRIORITY SELECTION"
    )

    print("=" * 78)

    # -----------------------------------------------------
    # Input
    # -----------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "Could not find Stage 6.5 output:\n"
            f"{INPUT_FILE}\n\n"
            "Run first:\n"
            "python src/assess_resource_sustainability.py"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    print()
    print(
        f"Loaded {len(df)} candidates."
    )

    print(
        f"Input: {INPUT_FILE}"
    )

    # -----------------------------------------------------
    # Required Week 6 columns
    # -----------------------------------------------------

    required_columns = [

        "material_id",
        "week6_formula",

        "synthesis_feasibility_score",

        "electronic_accessibility_score",

        "resource_practicality_score",

        "provenance_class",

        "literature_novelty_signal",

        "li_network_class",

        "discovery_class",
    ]

    missing = [

        column

        for column in required_columns

        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing required columns:\n"
            + "\n".join(
                missing
            )
        )

    # -----------------------------------------------------
    # Find Week 5 electrochemical score
    # -----------------------------------------------------

    electrochemical_column = (
        find_electrochemical_column(
            df
        )
    )

    if electrochemical_column is None:

        print()
        print(
            "Available score-related columns:"
        )

        for column in df.columns:

            if "score" in column.lower():

                print(
                    f"    {column}"
                )

        raise ValueError(
            "Could not identify the Week 5 "
            "electrochemical score column."
        )

    print()
    print(
        "Using Week 5 electrochemical column:"
    )

    print(
        f"    {electrochemical_column}"
    )

    # =====================================================
    # BUILD FINAL SCORES
    # =====================================================

    records = []

    for _, row in (
        df.iterrows()
    ):

        electrochemical = (
            normalize_100(
                row[
                    electrochemical_column
                ]
            )
        )

        synthesis = (
            normalize_100(
                row[
                    "synthesis_feasibility_score"
                ]
            )
        )

        electronic = (
            normalize_100(
                row[
                    "electronic_accessibility_score"
                ]
            )
        )

        resource = (
            normalize_100(
                row[
                    "resource_practicality_score"
                ]
            )
        )

        provenance = (
            provenance_confidence(
                row[
                    "provenance_class"
                ]
            )
        )

        li_network = (
            li_network_score(
                row[
                    "li_network_class"
                ]
            )
        )

        novelty = (
            novelty_score(
                row[
                    "literature_novelty_signal"
                ]
            )
        )

        technical = (
            technical_merit_score(
                electrochemical,
                synthesis,
                electronic,
                resource,
                provenance,
                li_network,
            )
        )

        research_score = (
            research_priority_score(
                technical,
                novelty,
            )
        )

        known_control = (
            is_known_control(
                row[
                    "discovery_class"
                ],
                row[
                    "literature_novelty_signal"
                ],
            )
        )

        priority_tier = (
            assign_priority_tier(
                research_score,
                known_control,
            )
        )

        confidence = (
            research_confidence(
                row[
                    "provenance_class"
                ],
                synthesis,
            )
        )

        record = (
            row.to_dict()
        )

        record[
            "week6_electrochemical_score"
        ] = round(
            electrochemical,
            2,
        )

        record[
            "week6_provenance_confidence"
        ] = provenance

        record[
            "week6_li_network_score"
        ] = li_network

        record[
            "week6_novelty_score"
        ] = novelty

        record[
            "technical_merit_score"
        ] = technical

        record[
            "research_priority_score"
        ] = research_score

        record[
            "is_known_cathode_control"
        ] = known_control

        record[
            "research_priority_tier"
        ] = priority_tier

        record[
            "research_confidence"
        ] = confidence

        records.append(
            record
        )

    output_df = pd.DataFrame(
        records
    )

    # -----------------------------------------------------
    # Rank all candidates
    # -----------------------------------------------------

    output_df = (
        output_df.sort_values(
            [
                "research_priority_score",
                "technical_merit_score",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    output_df[
        "research_rank"
    ] = (
        output_df.index
        + 1
    )

    # -----------------------------------------------------
    # Candidate explanations
    # -----------------------------------------------------

    interpretations = []

    for _, row in (
        output_df.iterrows()
    ):

        interpretations.append(
            candidate_interpretation(
                row
            )
        )

    output_df[
        "candidate_interpretation"
    ] = interpretations

    # =====================================================
    # DISCOVERY SHORTLIST
    # =====================================================

    discovery_df = output_df[
        ~output_df[
            "is_known_cathode_control"
        ]
    ].copy()

    # Keep top 5 discovery leads.
    #
    # Even candidates below the Priority 3 threshold
    # remain visible in the full ranking.

    shortlist_df = (
        discovery_df
        .head(5)
        .copy()
    )

    # =====================================================
    # SAVE
    # =====================================================

    RANKING_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_df.to_csv(
        RANKING_FILE,
        index=False,
    )

    shortlist_df.to_csv(
        SHORTLIST_FILE,
        index=False,
    )

    write_report(
        output_df,
        shortlist_df,
        electrochemical_column,
    )

    write_progress_report(
        output_df,
        shortlist_df,
    )

    # =====================================================
    # TERMINAL SUMMARY
    # =====================================================

    print()
    print("=" * 78)
    print(
        "WEEK 6 FINAL SELECTION COMPLETE"
    )
    print("=" * 78)

    print()
    print(
        "Priority tiers:"
    )

    print(
        output_df[
            "research_priority_tier"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Final discovery shortlist:"
    )
    print()

    display_columns = [

        "research_rank",

        "material_id",

        "week6_formula",

        "research_priority_score",

        "technical_merit_score",

        "research_priority_tier",

        "research_confidence",

        "discovery_class",
    ]

    print(
        shortlist_df[
            display_columns
        ]
        .to_string(
            index=False
        )
    )

    print()
    print(
        "Known cathode controls:"
    )
    print()

    controls = output_df[
        output_df[
            "is_known_cathode_control"
        ]
    ]

    if controls.empty:

        print(
            "None"
        )

    else:

        print(
            controls[
                [
                    "material_id",
                    "week6_formula",
                    "technical_merit_score",
                ]
            ]
            .to_string(
                index=False
            )
        )

    print()
    print(
        "Saved full ranking:"
    )

    print(
        RANKING_FILE
    )

    print()
    print(
        "Saved discovery shortlist:"
    )

    print(
        SHORTLIST_FILE
    )

    print()
    print(
        "Saved final report:"
    )

    print(
        REPORT_FILE
    )

    print()
    print(
        "Saved Week 6 progress report:"
    )

    print(
        PROGRESS_FILE
    )


if __name__ == "__main__":
    main()