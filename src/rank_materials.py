from pathlib import Path

import pandas as pd


# Input and output file locations
INPUT_PATH = Path("data/materials.csv")
OUTPUT_PATH = Path("data/ranked_materials.csv")


def load_materials():
    """
    Load the filtered Materials Project candidate dataset.
    """

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_PATH}. "
            "Run src/materials_search.py first."
        )

    df = pd.read_csv(INPUT_PATH)

    return df


def normalize_lower_is_better(series):
    """
    Normalize a numerical column to values between 0 and 1.

    Lower original values receive higher normalized scores.

    Example:
        Lowest energy above hull -> score near 1
        Highest energy above hull -> score near 0
    """

    minimum = series.min()
    maximum = series.max()

    # Avoid division by zero if every value is identical
    if maximum == minimum:
        return pd.Series(
            1.0,
            index=series.index,
        )

    return (maximum - series) / (maximum - minimum)


def calculate_scores(df):
    """
    Calculate preliminary screening scores for each material.

    The current ranking emphasizes:

    1. Low energy above hull
       Materials closer to the thermodynamic stability hull
       receive higher scores.

    2. More negative formation energy per atom
       More negative values receive higher scores in this
       preliminary screening model.

    3. Materials Project stability classification
       Materials marked as stable receive a small bonus.

    This is a screening heuristic, not a direct prediction
    of battery performance.
    """

    df = df.copy()

    # ---------------------------------------------------------
    # Stability score based on energy above hull
    # Lower energy_above_hull is better
    # ---------------------------------------------------------

    df["hull_score"] = normalize_lower_is_better(
        df["energy_above_hull"]
    )

    # ---------------------------------------------------------
    # Formation energy score
    # More negative formation energy receives a higher score
    # ---------------------------------------------------------

    df["formation_score"] = normalize_lower_is_better(
        df["formation_energy_per_atom"]
    )

    # ---------------------------------------------------------
    # Stable material bonus
    # True = 1
    # False = 0
    # ---------------------------------------------------------

    df["stable_score"] = (
        df["is_stable"]
        .astype(bool)
        .astype(int)
    )

    # ---------------------------------------------------------
    # Weighted overall screening score
    #
    # 55% energy above hull
    # 35% formation energy
    # 10% Materials Project stability classification
    # ---------------------------------------------------------

    df["overall_score"] = (
        0.55 * df["hull_score"]
        + 0.35 * df["formation_score"]
        + 0.10 * df["stable_score"]
    )

    return df


def rank_materials(df):
    """
    Sort materials from highest overall screening score
    to lowest and assign each material a rank.
    """

    df = df.sort_values(
        by="overall_score",
        ascending=False,
    )

    df = df.reset_index(drop=True)

    # Rank starts at 1 instead of 0
    df.insert(
        0,
        "rank",
        range(1, len(df) + 1),
    )

    return df


def save_ranked_materials(df):
    """
    Save the ranked material dataset.
    """

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )


def display_top_materials(df, number=20):
    """
    Display the highest-ranked materials in the terminal.
    """

    columns_to_display = [
        "rank",
        "material_id",
        "formula",
        "elements",
        "energy_above_hull",
        "formation_energy_per_atom",
        "is_stable",
        "overall_score",
    ]

    print()
    print(f"Top {number} ranked cathode candidates:")
    print()

    print(
        df[
            columns_to_display
        ].head(number).to_string(index=False)
    )


def main():
    """
    Run the complete material ranking pipeline.
    """

    print("Loading filtered materials...")

    df = load_materials()

    print(
        f"Loaded {len(df)} candidate materials."
    )

    print("Calculating screening scores...")

    df = calculate_scores(df)

    print("Ranking materials...")

    df = rank_materials(df)

    print(
        f"Ranked {len(df)} materials."
    )

    save_ranked_materials(df)

    print(
        f"Saved ranked materials to {OUTPUT_PATH}"
    )

    display_top_materials(
        df,
        number=20,
    )


if __name__ == "__main__":
    main()