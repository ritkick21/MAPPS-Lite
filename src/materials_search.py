from pathlib import Path

import pandas as pd
from mp_api.client import MPRester


# Path where the final filtered dataset will be saved
OUTPUT_PATH = Path("data/materials.csv")


# Transition metals that may be useful in lithium cathode materials
CATHODE_METALS = {
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
}


def fetch_materials():
    """
    Download lithium- and oxygen-containing materials
    from the Materials Project database.
    """

    fields = [
        "material_id",
        "formula_pretty",
        "elements",
        "density",
        "band_gap",
        "energy_above_hull",
        "formation_energy_per_atom",
        "is_stable",
    ]

    with MPRester() as mpr:
        materials = mpr.materials.summary.search(
            elements=["Li", "O"],
            num_elements=(3, 5),
            energy_above_hull=(0, 0.1),
            deprecated=False,
            fields=fields,
        )

    return materials


def materials_to_dataframe(materials):
    """
    Convert Materials Project material objects
    into a Pandas DataFrame.
    """

    rows = []

    for material in materials:
        row = {
            "material_id": str(material.material_id),
            "formula": material.formula_pretty,
            "elements": ",".join(
                str(element) for element in material.elements
            ),
            "density": material.density,
            "band_gap": material.band_gap,
            "energy_above_hull": material.energy_above_hull,
            "formation_energy_per_atom":
                material.formation_energy_per_atom,
            "is_stable": material.is_stable,
        }

        rows.append(row)

    return pd.DataFrame(rows)


def filter_cathode_candidates(df):
    """
    Apply basic screening filters to identify more plausible
    lithium cathode material candidates.

    This does not guarantee that a material is a functional cathode.
    It simply reduces the search space before ranking.
    """

    def contains_cathode_metal(elements_string):
        """
        Check whether the material contains at least one
        transition metal from CATHODE_METALS.
        """

        elements = set(elements_string.split(","))

        return bool(elements.intersection(CATHODE_METALS))

    # Create a copy so the original DataFrame is not modified
    df = df.copy()

    # Keep materials containing at least one selected transition metal
    df = df[
        df["elements"].apply(contains_cathode_metal)
    ]

    # Keep materials relatively close to thermodynamic stability
    df = df[
        df["energy_above_hull"] <= 0.05
    ]

    return df


def save_materials(df):
    """
    Clean the filtered dataset and save it as a CSV file.
    """

    # Create the data folder if it does not already exist
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Remove rows missing important numerical properties
    df = df.dropna(
        subset=[
            "density",
            "energy_above_hull",
            "formation_energy_per_atom",
        ]
    )

    # Remove duplicate Materials Project entries
    df = df.drop_duplicates(
        subset=["material_id"]
    )

    # Reset row numbers after filtering
    df = df.reset_index(drop=True)

    # Save the dataset
    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    return df


def main():
    """
    Run the complete Materials Project candidate search pipeline.
    """

    print(
        "Fetching materials from Materials Project..."
    )

    # Step 1: Download materials
    materials = fetch_materials()

    print(
        f"Downloaded {len(materials)} materials."
    )

    # Step 2: Convert API results to a DataFrame
    df = materials_to_dataframe(materials)

    print(
        f"Converted {len(df)} materials to DataFrame."
    )

    # Step 3: Filter for more plausible cathode candidates
    df = filter_cathode_candidates(df)

    print(
        f"{len(df)} materials remain after cathode filtering."
    )

    # Step 4: Clean and save the filtered dataset
    df = save_materials(df)

    print(
        f"Saved {len(df)} cleaned materials to:"
    )

    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()