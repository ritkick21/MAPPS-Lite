"""
MAPPS-Lite Materials Search

Queries Materials Project for lithium-oxygen compounds,
converts the results into a pandas DataFrame, applies the
initial cathode screening rules, and saves the cleaned
candidate dataset.
"""

import os
from pathlib import Path

import pandas as pd
from mp_api.client import MPRester

try:
    from config import (
        REQUIRED_ELEMENTS,
        MIN_NUM_ELEMENTS,
        MAX_NUM_ELEMENTS,
        SEARCH_MIN_HULL_ENERGY,
        SEARCH_MAX_HULL_ENERGY,
        CANDIDATE_MAX_HULL_ENERGY,
        CATHODE_METALS,
        MATERIALS_PROJECT_FIELDS,
    )
except ImportError:
    from .config import (
        REQUIRED_ELEMENTS,
        MIN_NUM_ELEMENTS,
        MAX_NUM_ELEMENTS,
        SEARCH_MIN_HULL_ENERGY,
        SEARCH_MAX_HULL_ENERGY,
        CANDIDATE_MAX_HULL_ENERGY,
        CATHODE_METALS,
        MATERIALS_PROJECT_FIELDS,
    )


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "materials.csv"
)


# ---------------------------------------------------------
# API key validation
# ---------------------------------------------------------

def get_api_key():
    """
    Read the Materials Project API key from the
    MP_API_KEY environment variable.

    Returns:
        str:
            Materials Project API key.

    Raises:
        RuntimeError:
            If MP_API_KEY is not configured.
    """

    api_key = os.getenv(
        "MP_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "Materials Project API key was not found.\n\n"
            "Set it in Command Prompt with:\n"
            "set MP_API_KEY=YOUR_MATERIALS_PROJECT_API_KEY"
        )

    return api_key


# ---------------------------------------------------------
# Materials Project search
# ---------------------------------------------------------

def fetch_materials():
    """
    Search Materials Project for lithium-oxygen compounds
    that could potentially be relevant to cathode
    discovery.

    Search parameters are loaded from config.py.
    """

    api_key = get_api_key()

    with MPRester(
        api_key=api_key
    ) as mpr:

        materials = (
            mpr.materials.summary.search(
                elements=REQUIRED_ELEMENTS,

                num_elements=(
                    MIN_NUM_ELEMENTS,
                    MAX_NUM_ELEMENTS,
                ),

                energy_above_hull=(
                    SEARCH_MIN_HULL_ENERGY,
                    SEARCH_MAX_HULL_ENERGY,
                ),

                deprecated=False,

                fields=MATERIALS_PROJECT_FIELDS,
            )
        )

    return materials


# ---------------------------------------------------------
# Convert Materials Project results
# ---------------------------------------------------------

def materials_to_dataframe(
    materials
):
    """
    Convert Materials Project SummaryDoc objects into
    a pandas DataFrame.

    Args:
        materials:
            Materials Project search results.

    Returns:
        pandas.DataFrame:
            Dataset containing the selected material
            properties.
    """

    rows = []

    for material in materials:

        row = {
            "material_id":
                str(
                    material.material_id
                ),

            "formula":
                material.formula_pretty,

            "elements":
                ",".join(
                    str(element)
                    for element
                    in material.elements
                ),

            "density":
                material.density,

            "band_gap":
                material.band_gap,

            "energy_above_hull":
                material.energy_above_hull,

            "formation_energy_per_atom":
                material.formation_energy_per_atom,

            "is_stable":
                material.is_stable,
        }

        rows.append(
            row
        )

    return pd.DataFrame(
        rows
    )


# ---------------------------------------------------------
# Cathode filtering
# ---------------------------------------------------------

def contains_cathode_metal(
    elements
):
    """
    Determine whether an element list contains at least
    one metal from the configured cathode-metal set.

    Args:
        elements:
            Comma-separated element symbols.

    Returns:
        bool:
            True if at least one configured cathode metal
            is present.
    """

    element_set = {
        element.strip()
        for element
        in str(elements).split(",")
        if element.strip()
    }

    return bool(
        element_set
        & CATHODE_METALS
    )


def filter_cathode_candidates(
    materials_df
):
    """
    Apply the initial MAPPS-Lite cathode screening rules.

    A material must:

    1. Contain at least one configured cathode metal.
    2. Have energy above hull less than or equal to the
       configured candidate threshold.

    Args:
        materials_df:
            Raw Materials Project DataFrame.

    Returns:
        pandas.DataFrame:
            Materials passing the initial filter.
    """

    required_columns = {
        "elements",
        "energy_above_hull",
    }

    missing_columns = (
        required_columns
        - set(
            materials_df.columns
        )
    )

    if missing_columns:

        missing_text = ", ".join(
            sorted(
                missing_columns
            )
        )

        raise ValueError(
            "Cannot filter materials because required "
            f"column(s) are missing: {missing_text}"
        )

    cathode_mask = (
        materials_df[
            "elements"
        ]
        .apply(
            contains_cathode_metal
        )
    )

    hull_mask = (
        materials_df[
            "energy_above_hull"
        ]
        <= CANDIDATE_MAX_HULL_ENERGY
    )

    filtered_df = (
        materials_df[
            cathode_mask
            & hull_mask
        ]
        .copy()
    )

    return filtered_df


# ---------------------------------------------------------
# Clean dataset
# ---------------------------------------------------------

def clean_materials(
    materials_df
):
    """
    Remove incomplete and duplicate material records.

    Args:
        materials_df:
            Filtered candidate DataFrame.

    Returns:
        pandas.DataFrame:
            Cleaned candidate dataset.
    """

    required_numeric_columns = [
        "density",
        "energy_above_hull",
        "formation_energy_per_atom",
    ]

    cleaned_df = (
        materials_df
        .dropna(
            subset=required_numeric_columns
        )
        .copy()
    )

    cleaned_df = (
        cleaned_df
        .drop_duplicates(
            subset=[
                "material_id"
            ]
        )
    )

    cleaned_df = (
        cleaned_df
        .reset_index(
            drop=True
        )
    )

    return cleaned_df


# ---------------------------------------------------------
# Save dataset
# ---------------------------------------------------------

def save_materials(
    materials_df
):
    """
    Save the cleaned candidate dataset.

    Args:
        materials_df:
            Cleaned candidate DataFrame.

    Returns:
        pandas.DataFrame:
            The same DataFrame after it has been saved.
    """

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    materials_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    return materials_df


# ---------------------------------------------------------
# Search pipeline
# ---------------------------------------------------------

def run_search_pipeline():
    """
    Run the complete MAPPS-Lite material search pipeline.

    Workflow:

    1. Query Materials Project.
    2. Convert results to a DataFrame.
    3. Apply cathode screening.
    4. Remove incomplete and duplicate records.
    5. Save data/materials.csv.

    Returns:
        pandas.DataFrame:
            Final cleaned candidate dataset.
    """

    print(
        "Fetching materials from Materials Project..."
    )

    materials = fetch_materials()

    print(
        f"Downloaded {len(materials)} materials."
    )

    materials_df = (
        materials_to_dataframe(
            materials
        )
    )

    print(
        f"Converted {len(materials_df)} materials "
        "to DataFrame."
    )

    cathode_candidates = (
        filter_cathode_candidates(
            materials_df
        )
    )

    print(
        f"{len(cathode_candidates)} materials remain "
        "after cathode filtering."
    )

    cleaned_candidates = (
        clean_materials(
            cathode_candidates
        )
    )

    save_materials(
        cleaned_candidates
    )

    print(
        f"Saved {len(cleaned_candidates)} "
        "cleaned materials to:"
    )

    print(
        OUTPUT_PATH
    )

    return cleaned_candidates


# ---------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------

def main():
    """
    Run the search stage independently.
    """

    run_search_pipeline()


if __name__ == "__main__":
    main()