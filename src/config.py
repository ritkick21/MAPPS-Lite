"""
Central configuration for MAPPS-Lite.

This file stores the scientific assumptions, filtering
thresholds, ranking weights, chemistry screening lists,
and default output settings used across the pipeline.

Keeping these values in one location prevents the search,
ranking, analysis, and reporting stages from using
inconsistent settings.
"""


# ---------------------------------------------------------
# Materials Project search settings
# ---------------------------------------------------------

# Every retrieved material must contain lithium and oxygen.
REQUIRED_ELEMENTS = [
    "Li",
    "O",
]

# Search for compounds containing between 3 and 5
# distinct chemical elements.
MIN_NUM_ELEMENTS = 3
MAX_NUM_ELEMENTS = 5

# Materials Project search limit.
#
# The API initially retrieves materials with an energy
# above hull between 0 and 0.10 eV/atom. A stricter
# MAPPS-Lite filter is applied afterward.
SEARCH_MIN_HULL_ENERGY = 0.00
SEARCH_MAX_HULL_ENERGY = 0.10

# Stricter cathode-candidate filter applied after retrieval.
CANDIDATE_MAX_HULL_ENERGY = 0.05


# ---------------------------------------------------------
# Initial cathode search metals
# ---------------------------------------------------------

# A retrieved compound must contain at least one element
# from this set to pass the initial cathode filter.
#
# Cu is included in the broad search stage so potentially
# relevant compounds are not removed too early.
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


# ---------------------------------------------------------
# Ranking model weights
# ---------------------------------------------------------

# Current MAPPS-Lite thermodynamic ranking model:
#
# 55% energy above hull
# 35% formation energy per atom
# 10% Materials Project stability classification

HULL_WEIGHT = 0.55
FORMATION_ENERGY_WEIGHT = 0.35
STABILITY_WEIGHT = 0.10


# ---------------------------------------------------------
# Ranking validation
# ---------------------------------------------------------

RANKING_WEIGHT_TOLERANCE = 1e-9


def validate_ranking_weights():
    """
    Confirm that the ranking weights sum to 1.0.

    Raises:
        ValueError:
            If the configured weights do not sum to 1.0.
    """

    total_weight = (
        HULL_WEIGHT
        + FORMATION_ENERGY_WEIGHT
        + STABILITY_WEIGHT
    )

    if abs(total_weight - 1.0) > RANKING_WEIGHT_TOLERANCE:
        raise ValueError(
            "MAPPS-Lite ranking weights must sum to 1.0.\n"
            f"Current total: {total_weight:.6f}"
        )


# ---------------------------------------------------------
# Secondary chemistry screening
# ---------------------------------------------------------

# Transition metals currently treated as relevant during
# the secondary battery-composition screening stage.
#
# This list is intentionally narrower than CATHODE_METALS.
# Cu may pass the broad search stage but is not currently
# sufficient by itself for a PROMISING classification.
BATTERY_RELEVANT_METALS = {
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
}


# Elements that trigger a REVIEW classification.
FLAGGED_ELEMENTS = {
    "Pb": "contains lead",
    "Hg": "contains mercury",
    "Cd": "contains cadmium",
    "U": "contains uranium",
}


# ---------------------------------------------------------
# Candidate status labels
# ---------------------------------------------------------

STATUS_PROMISING = "PROMISING"
STATUS_POSSIBLE = "POSSIBLE"
STATUS_REVIEW = "REVIEW"


# ---------------------------------------------------------
# Report settings
# ---------------------------------------------------------

TOP_CANDIDATE_COUNT = 10


# ---------------------------------------------------------
# Materials Project fields
# ---------------------------------------------------------

MATERIALS_PROJECT_FIELDS = [
    "material_id",
    "formula_pretty",
    "elements",
    "density",
    "band_gap",
    "energy_above_hull",
    "formation_energy_per_atom",
    "is_stable",
]


# ---------------------------------------------------------
# Configuration summary
# ---------------------------------------------------------

def get_ranking_model_summary():
    """
    Return the ranking model as percentages.

    This can be used by reports and run-summary files so
    that displayed values always match the actual model.
    """

    return {
        "energy_above_hull_percent":
            HULL_WEIGHT * 100,

        "formation_energy_percent":
            FORMATION_ENERGY_WEIGHT * 100,

        "stability_flag_percent":
            STABILITY_WEIGHT * 100,
    }


def validate_configuration():
    """
    Run all available MAPPS-Lite configuration checks.
    """

    validate_ranking_weights()

    if (
        CANDIDATE_MAX_HULL_ENERGY
        > SEARCH_MAX_HULL_ENERGY
    ):
        raise ValueError(
            "CANDIDATE_MAX_HULL_ENERGY cannot exceed "
            "SEARCH_MAX_HULL_ENERGY."
        )

    if MIN_NUM_ELEMENTS > MAX_NUM_ELEMENTS:
        raise ValueError(
            "MIN_NUM_ELEMENTS cannot exceed "
            "MAX_NUM_ELEMENTS."
        )


# Validate the settings whenever config.py is imported.
validate_configuration()