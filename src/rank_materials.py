"""
MAPPS-Lite Material Ranking

Loads the cleaned cathode-candidate dataset, calculates
normalized thermodynamic scores, applies the configured
ranking weights, ranks every material, and saves the
resulting dataset.
"""

from pathlib import Path

import pandas as pd

try:
    from config import (
        HULL_WEIGHT,
        FORMATION_ENERGY_WEIGHT,
        STABILITY_WEIGHT,
        validate_ranking_weights,
    )
except ImportError:
    from .config import (
        HULL_WEIGHT,
        FORMATION_ENERGY_WEIGHT,
        STABILITY_WEIGHT,
        validate_ranking_weights,
    )


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "materials.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "ranked_materials.csv"
)


# ---------------------------------------------------------
# Required dataset columns
# ---------------------------------------------------------

REQUIRED_COLUMNS = {
    "material_id",
    "formula",
    "energy_above_hull",
    "formation_energy_per_atom",
    "is_stable",
}


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------

def load_materials():
    """
    Load the cleaned material candidates created by
    materials_search.py.

    Returns:
        pandas.DataFrame:
            Cleaned material-candidate dataset.

    Raises:
        FileNotFoundError:
            If data/materials.csv does not exist.

        ValueError:
            If required columns are missing.
    """

    if not INPUT_PATH.exists():

        raise FileNotFoundError(
            "Could not find the material candidate file:\n"
            f"{INPUT_PATH}\n\n"
            "Run one of these commands first:\n"
            "python src/materials_search.py\n"
            "python src/main.py"
        )

    materials_df = pd.read_csv(
        INPUT_PATH
    )

    missing_columns = (
        REQUIRED_COLUMNS
        - set(materials_df.columns)
    )

    if missing_columns:

        missing_text = ", ".join(
            sorted(missing_columns)
        )

        raise ValueError(
            "Cannot rank materials because required "
            f"column(s) are missing: {missing_text}"
        )

    if materials_df.empty:

        raise ValueError(
            "The material candidate dataset is empty."
        )

    return materials_df


# ---------------------------------------------------------
# Numeric validation
# ---------------------------------------------------------

def prepare_numeric_columns(
    materials_df
):
    """
    Convert ranking properties to numeric values and remove
    rows that cannot be scored.

    Args:
        materials_df:
            Candidate material dataset.

    Returns:
        pandas.DataFrame:
            Dataset containing valid numeric ranking data.
    """

    prepared_df = materials_df.copy()

    numeric_columns = [
        "energy_above_hull",
        "formation_energy_per_atom",
    ]

    for column in numeric_columns:

        prepared_df[column] = pd.to_numeric(
            prepared_df[column],
            errors="coerce",
        )

    prepared_df = prepared_df.dropna(
        subset=numeric_columns
    )

    prepared_df = prepared_df.reset_index(
        drop=True
    )

    if prepared_df.empty:

        raise ValueError(
            "No materials contain valid numeric values "
            "for the ranking properties."
        )

    return prepared_df


# ---------------------------------------------------------
# Normalization
# ---------------------------------------------------------

def normalize_lower_is_better(
    series
):
    """
    Normalize a numeric pandas Series to a score from
    0 to 1, where lower original values receive higher
    normalized scores.

    Best original value:
        1.0

    Worst original value:
        0.0

    Args:
        series:
            Numeric pandas Series.

    Returns:
        pandas.Series:
            Normalized values aligned to the original
            Series index.
    """

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:

        return pd.Series(
            1.0,
            index=series.index,
            dtype=float,
        )

    normalized_series = (
        maximum - series
    ) / (
        maximum - minimum
    )

    return normalized_series


# ---------------------------------------------------------
# Stability conversion
# ---------------------------------------------------------

def convert_stability_to_score(
    series
):
    """
    Convert Materials Project stability values into
    numeric scores.

    Stable:
        1.0

    Not stable or unrecognized:
        0.0

    This supports both Boolean values and strings read
    from CSV files.

    Args:
        series:
            Stability column.

    Returns:
        pandas.Series:
            Numeric stability scores.
    """

    normalized_values = (
        series
        .astype(str)
        .str.strip()
        .str.lower()
    )

    stability_scores = (
        normalized_values
        .map(
            {
                "true": 1.0,
                "false": 0.0,
            }
        )
        .fillna(0.0)
    )

    return stability_scores


# ---------------------------------------------------------
# Scoring
# ---------------------------------------------------------

def calculate_scores(
    materials_df
):
    """
    Calculate the MAPPS-Lite component scores and final
    weighted ranking score.

    The ranking weights are imported from config.py.

    Args:
        materials_df:
            Validated candidate material dataset.

    Returns:
        pandas.DataFrame:
            Dataset with component and final scores.
    """

    validate_ranking_weights()

    scored_df = materials_df.copy()

    scored_df["hull_score"] = (
        normalize_lower_is_better(
            scored_df[
                "energy_above_hull"
            ]
        )
    )

    scored_df["formation_score"] = (
        normalize_lower_is_better(
            scored_df[
                "formation_energy_per_atom"
            ]
        )
    )

    scored_df["stability_score"] = (
        convert_stability_to_score(
            scored_df[
                "is_stable"
            ]
        )
    )

    scored_df["score"] = (
        HULL_WEIGHT
        * scored_df[
            "hull_score"
        ]

        + FORMATION_ENERGY_WEIGHT
        * scored_df[
            "formation_score"
        ]

        + STABILITY_WEIGHT
        * scored_df[
            "stability_score"
        ]
    )

    return scored_df


# ---------------------------------------------------------
# Ranking
# ---------------------------------------------------------

def rank_materials(
    scored_df
):
    """
    Sort materials from highest to lowest MAPPS-Lite
    score and assign sequential rank numbers.

    Args:
        scored_df:
            Material dataset containing the score column.

    Returns:
        pandas.DataFrame:
            Ranked material dataset.
    """

    if "score" not in scored_df.columns:

        raise ValueError(
            "Cannot rank materials because the "
            "'score' column is missing."
        )

    ranked_df = (
        scored_df
        .sort_values(
            by=[
                "score",
                "energy_above_hull",
                "formation_energy_per_atom",
            ],
            ascending=[
                False,
                True,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    ranked_df.insert(
        0,
        "rank",
        ranked_df.index + 1,
    )

    return ranked_df


# ---------------------------------------------------------
# Save results
# ---------------------------------------------------------

def save_ranked_materials(
    ranked_df
):
    """
    Save the ranked candidate dataset.

    Args:
        ranked_df:
            Ranked material dataset.

    Returns:
        pandas.DataFrame:
            The same dataset after it has been saved.
    """

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ranked_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    return ranked_df


# ---------------------------------------------------------
# Display top candidates
# ---------------------------------------------------------

def print_top_materials(
    ranked_df,
    count=20,
):
    """
    Print the highest-ranked candidates to the terminal.

    Args:
        ranked_df:
            Ranked material dataset.

        count:
            Maximum number of candidates to display.
    """

    display_columns = [
        "rank",
        "material_id",
        "formula",
        "energy_above_hull",
        "formation_energy_per_atom",
        "is_stable",
        "score",
    ]

    available_columns = [
        column
        for column in display_columns
        if column in ranked_df.columns
    ]

    display_count = min(
        count,
        len(ranked_df),
    )

    print()
    print(
        f"Top {display_count} materials:"
    )
    print()

    print(
        ranked_df[
            available_columns
        ]
        .head(display_count)
        .to_string(
            index=False
        )
    )


# ---------------------------------------------------------
# Ranking model display
# ---------------------------------------------------------

def print_ranking_model():
    """
    Print the active ranking weights.
    """

    print("Active ranking model:")

    print(
        "  Energy above hull: "
        f"{HULL_WEIGHT * 100:.0f}%"
    )

    print(
        "  Formation energy per atom: "
        f"{FORMATION_ENERGY_WEIGHT * 100:.0f}%"
    )

    print(
        "  Materials Project stability flag: "
        f"{STABILITY_WEIGHT * 100:.0f}%"
    )

    print()


# ---------------------------------------------------------
# Ranking pipeline
# ---------------------------------------------------------

def run_ranking_pipeline():
    """
    Run the complete MAPPS-Lite ranking pipeline.

    Workflow:

    1. Load data/materials.csv.
    2. Validate and prepare the ranking properties.
    3. Normalize thermodynamic properties.
    4. Calculate the configured weighted score.
    5. Sort candidates and assign ranks.
    6. Save data/ranked_materials.csv.

    Returns:
        pandas.DataFrame:
            Complete ranked material dataset.
    """

    print(
        "Loading material candidates..."
    )

    materials_df = load_materials()

    print(
        f"Loaded {len(materials_df)} materials."
    )

    prepared_df = prepare_numeric_columns(
        materials_df
    )

    removed_count = (
        len(materials_df)
        - len(prepared_df)
    )

    if removed_count > 0:

        print(
            f"Removed {removed_count} materials with "
            "invalid ranking values."
        )

    print_ranking_model()

    print(
        "Calculating ranking scores..."
    )

    scored_df = calculate_scores(
        prepared_df
    )

    ranked_df = rank_materials(
        scored_df
    )

    save_ranked_materials(
        ranked_df
    )

    print(
        f"Saved {len(ranked_df)} ranked materials to:"
    )

    print(
        OUTPUT_PATH
    )

    print_top_materials(
        ranked_df,
        count=20,
    )

    return ranked_df


# ---------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------

def main():
    """
    Run the ranking stage independently.
    """

    run_ranking_pipeline()


if __name__ == "__main__":
    main()