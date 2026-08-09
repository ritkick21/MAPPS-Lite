"""
MAPPS-Lite Week 7
Candidate Redox Chemistry Analysis

Purpose
-------
Analyze the likely charge-storage chemistry of the strongest Week 7
cathode candidates.

The script:
1. Loads the Week 7 crystal-structure analysis.
2. Reconstructs each candidate composition.
3. Determines plausible charge-balanced oxidation states.
4. Identifies likely redox-active transition metals.
5. Determines chemically plausible oxidation directions.
6. Estimates a conservative electron-transfer inventory.
7. Flags unusual or questionable redox chemistry.
8. Produces a redox score and confidence assessment.

Input
-----
data/week7_candidate_structures.csv

Outputs
-------
data/week7_redox_analysis.csv
reports/week7_redox_analysis.md

Important Scientific Limitation
-------------------------------
Oxidation-state analysis does NOT directly predict electrochemical
voltage, reversibility, kinetics, or structural stability during
cycling.

The electron-transfer estimates produced here are screening-level
chemical estimates and should not be treated as experimentally
validated capacities.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from pymatgen.core import Composition, Element


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_candidate_structures.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_redox_analysis.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week7_redox_analysis.md"
)


# ============================================================
# CHEMISTRY CONFIGURATION
# ============================================================

# Transition-metal elements that are commonly capable of
# participating in cathode redox chemistry.
#
# This is intentionally broader than the elements currently present
# in the shortlist so the script can be reused later.

REDOX_ACTIVE_METALS = {
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Mo",
    "W",
    "Nb",
    "Ta",
    "Ru",
    "Rh",
    "Ir",
}


# Common oxidation states relevant to battery chemistry.
#
# These are used for conservative redox-window estimates.
# We intentionally avoid using every formally possible oxidation
# state because rare oxidation states can create unrealistic
# predictions.

REDOX_WINDOWS = {
    "Ti": (3, 4),
    "V": (2, 5),
    "Cr": (2, 6),
    "Mn": (2, 4),
    "Fe": (2, 4),
    "Co": (2, 4),
    "Ni": (2, 4),
    "Cu": (1, 3),
    "Mo": (3, 6),
    "W": (4, 6),
    "Nb": (3, 5),
    "Ta": (3, 5),
    "Ru": (2, 5),
    "Rh": (2, 4),
    "Ir": (3, 5),
}


# Particularly common cathode redox couples.
#
# These are not guaranteed reaction pathways. They are used for
# interpretation and scoring.

KNOWN_CATHODE_COUPLES = {
    "Ti": [
        (3, 4),
    ],
    "V": [
        (3, 4),
        (4, 5),
    ],
    "Cr": [
        (3, 4),
        (4, 5),
        (5, 6),
    ],
    "Mn": [
        (2, 3),
        (3, 4),
    ],
    "Fe": [
        (2, 3),
        (3, 4),
    ],
    "Co": [
        (2, 3),
        (3, 4),
    ],
    "Ni": [
        (2, 3),
        (3, 4),
    ],
    "Cu": [
        (1, 2),
        (2, 3),
    ],
    "Mo": [
        (4, 5),
        (5, 6),
    ],
    "W": [
        (4, 5),
        (5, 6),
    ],
    "Nb": [
        (3, 4),
        (4, 5),
    ],
}


# Expected oxidation states for spectator / framework elements.
#
# These are useful for detecting clearly unusual chemistry.

FRAMEWORK_EXPECTATIONS = {
    "Li": {1},
    "Na": {1},
    "K": {1},

    "Mg": {2},
    "Ca": {2},
    "Sr": {2},
    "Ba": {2},

    "Al": {3},

    "Si": {4},
    "P": {5},
    "B": {3},

    "O": {-2},
    "F": {-1},
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_float(
    value: Any,
) -> float | None:
    """
    Convert a value to a finite float when possible.
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


def safe_bool(
    value: Any,
) -> bool | None:
    """
    Convert common boolean-like values to bool.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (np.bool_,)):
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


def format_number(
    value: Any,
    digits: int = 3,
) -> str:
    """
    Format values for report output.
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


def round_if_number(
    value: Any,
    digits: int = 4,
) -> Any:
    """
    Round numeric values when possible.
    """

    number = safe_float(value)

    if number is None:
        return value

    return round(number, digits)


# ============================================================
# LOAD STRUCTURAL CANDIDATES
# ============================================================

def load_candidates() -> pd.DataFrame:
    """
    Load the Week 7 structural-analysis output.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "\nCould not find Week 7 structural input:\n"
            f"{INPUT_FILE}\n\n"
            "Run src/analyze_candidate_structures.py first."
        )

    dataframe = pd.read_csv(INPUT_FILE)

    if dataframe.empty:
        raise ValueError(
            "week7_candidate_structures.csv contains no candidates."
        )

    material_column = find_column(
        dataframe,
        [
            "material_id",
            "mp_id",
        ],
    )

    if material_column is None:
        raise ValueError(
            "Could not locate material_id in the structural dataset."
        )

    if material_column != "material_id":
        dataframe = dataframe.rename(
            columns={
                material_column: "material_id"
            }
        )

    formula_column = find_column(
        dataframe,
        [
            "mp_formula",
            "formula",
            "formula_pretty",
        ],
    )

    if formula_column is None:
        raise ValueError(
            "Could not locate a chemical formula column."
        )

    if formula_column != "formula":
        dataframe["formula"] = dataframe[
            formula_column
        ]

    dataframe["material_id"] = (
        dataframe["material_id"]
        .astype(str)
        .str.strip()
    )

    return dataframe.copy()


# ============================================================
# COMPOSITION HANDLING
# ============================================================

def build_composition(
    formula: str,
) -> Composition:
    """
    Convert a chemical formula into a pymatgen Composition.
    """

    try:
        composition = Composition(
            str(formula)
        )

    except Exception as exc:
        raise ValueError(
            f"Could not parse formula '{formula}': {exc}"
        ) from exc

    return composition


def get_element_amounts(
    composition: Composition,
) -> dict[str, float]:
    """
    Return element amounts in the reduced composition.
    """

    reduced = composition.reduced_composition

    result: dict[str, float] = {}

    for element, amount in reduced.items():
        result[str(element)] = float(amount)

    return result


# ============================================================
# OXIDATION STATE ANALYSIS
# ============================================================

def get_oxidation_state_guesses(
    composition: Composition,
) -> tuple[list[dict[str, float]], str]:
    """
    Determine plausible oxidation-state combinations.

    pymatgen returns combinations ordered from more likely to less
    likely using oxidation-state occurrence statistics.

    We first use commonly observed oxidation states.

    If no solution is found, we perform a broader search using all
    known oxidation states. A solution from the broader search is
    assigned lower confidence.
    """

    reduced = composition.reduced_composition

    # --------------------------------------------------------
    # Standard / common-state search
    # --------------------------------------------------------

    try:
        guesses = list(
            reduced.oxi_state_guesses(
                all_oxi_states=False,
            )
        )

    except Exception:
        guesses = []

    if guesses:
        return guesses, "COMMON_STATES"

    # --------------------------------------------------------
    # Broader fallback search
    # --------------------------------------------------------

    try:
        guesses = list(
            reduced.oxi_state_guesses(
                all_oxi_states=True,
            )
        )

    except Exception:
        guesses = []

    if guesses:
        return guesses, "ALL_STATES_FALLBACK"

    return [], "NO_SOLUTION"


def normalize_oxidation_guess(
    guess: dict[Any, Any],
) -> dict[str, float]:
    """
    Normalize oxidation-state keys and values.
    """

    normalized: dict[str, float] = {}

    for element, oxidation_state in guess.items():

        symbol = str(element)

        value = safe_float(
            oxidation_state
        )

        if value is not None:
            normalized[symbol] = value

    return normalized


def oxidation_guess_string(
    guess: dict[str, float],
) -> str:
    """
    Produce a compact oxidation-state description.
    """

    if not guess:
        return "No charge-balanced assignment"

    pieces: list[str] = []

    for symbol in sorted(
        guess.keys(),
        key=lambda x: Element(x).Z,
    ):

        oxidation_state = guess[symbol]

        if oxidation_state > 0:
            formatted = f"+{oxidation_state:g}"

        else:
            formatted = f"{oxidation_state:g}"

        pieces.append(
            f"{symbol}{formatted}"
        )

    return ", ".join(pieces)


# ============================================================
# REDOX-ACTIVE ELEMENT IDENTIFICATION
# ============================================================

def identify_redox_metals(
    composition: Composition,
) -> list[str]:
    """
    Identify candidate redox-active transition metals.
    """

    symbols = {
        str(element)
        for element in composition.elements
    }

    redox_metals = sorted(
        symbols.intersection(
            REDOX_ACTIVE_METALS
        ),
        key=lambda x: Element(x).Z,
    )

    return redox_metals


# ============================================================
# FRAMEWORK CHEMISTRY VALIDATION
# ============================================================

def assess_framework_oxidation_states(
    guess: dict[str, float],
) -> tuple[list[str], list[str]]:
    """
    Check whether common spectator/framework elements appear in
    chemically ordinary oxidation states.
    """

    positives: list[str] = []
    concerns: list[str] = []

    for element, expected_states in (
        FRAMEWORK_EXPECTATIONS.items()
    ):

        if element not in guess:
            continue

        oxidation_state = guess[element]

        rounded = int(
            round(oxidation_state)
        )

        if (
            math.isclose(
                oxidation_state,
                rounded,
                abs_tol=0.05,
            )
            and rounded in expected_states
        ):
            continue

        expected_text = "/".join(
            f"{state:+d}"
            for state in sorted(
                expected_states
            )
        )

        concerns.append(
            f"{element} has inferred average oxidation state "
            f"{oxidation_state:+.2f}; typical framework expectation "
            f"is {expected_text}."
        )

    if not concerns:
        positives.append(
            "Framework elements have conventional "
            "charge-balanced oxidation states."
        )

    return positives, concerns


# ============================================================
# REDOX WINDOW ANALYSIS
# ============================================================

def determine_redox_window(
    metal: str,
    starting_oxidation_state: float,
) -> dict[str, Any]:
    """
    Evaluate oxidation/reduction room for one candidate redox metal.

    For a charged cathode during lithium extraction, the usual
    direction is oxidation of the transition metal.

    Therefore the most important quantity for cathode screening is
    the number of electrons available before reaching a conservative
    upper oxidation-state bound.
    """

    if metal not in REDOX_WINDOWS:

        return {
            "metal": metal,
            "starting_oxidation_state":
                starting_oxidation_state,
            "minimum_state": None,
            "maximum_state": None,
            "oxidation_room": 0.0,
            "reduction_room": 0.0,
            "known_couple": False,
            "couple_description": "Unknown",
        }

    minimum_state, maximum_state = (
        REDOX_WINDOWS[metal]
    )

    oxidation_room = max(
        0.0,
        maximum_state - starting_oxidation_state,
    )

    reduction_room = max(
        0.0,
        starting_oxidation_state - minimum_state,
    )

    known_couple = False
    couple_descriptions: list[str] = []

    for lower, upper in KNOWN_CATHODE_COUPLES.get(
        metal,
        [],
    ):

        # Starting oxidation state may be fractional because
        # pymatgen can report an average mixed-valence state.

        if (
            starting_oxidation_state >= lower - 0.25
            and starting_oxidation_state <= upper + 0.25
        ):

            known_couple = True

            couple_descriptions.append(
                f"{metal}{lower}+/{metal}{upper}+"
            )

    if couple_descriptions:
        description = ", ".join(
            couple_descriptions
        )
    else:
        description = "No standard couple identified"

    return {
        "metal": metal,
        "starting_oxidation_state":
            round(starting_oxidation_state, 4),
        "minimum_state": minimum_state,
        "maximum_state": maximum_state,
        "oxidation_room": round(
            oxidation_room,
            4,
        ),
        "reduction_room": round(
            reduction_room,
            4,
        ),
        "known_couple": known_couple,
        "couple_description": description,
    }


# ============================================================
# ELECTRON INVENTORY
# ============================================================

def estimate_redox_electrons(
    composition: Composition,
    oxidation_guess: dict[str, float],
    redox_metals: list[str],
) -> dict[str, Any]:
    """
    Estimate conservative redox electron inventory.

    The value represents the amount of transition-metal oxidation
    available within our selected oxidation-state windows.

    We separately calculate a lithium-limited value because a
    lithium cathode cannot normally extract more Li-associated
    electrons than its available lithium inventory.

    This estimate does not prove reversibility.
    """

    reduced = composition.reduced_composition

    raw_redox_electrons = 0.0

    metal_details: list[dict[str, Any]] = []

    for metal in redox_metals:

        if metal not in oxidation_guess:
            continue

        amount = safe_float(
            reduced.get_el_amt_dict().get(
                metal,
                0,
            )
        )

        if amount is None:
            amount = 0.0

        starting_state = oxidation_guess[
            metal
        ]

        redox_window = determine_redox_window(
            metal,
            starting_state,
        )

        contribution = (
            amount
            * redox_window["oxidation_room"]
        )

        raw_redox_electrons += contribution

        redox_window[
            "atom_amount"
        ] = round(
            amount,
            4,
        )

        redox_window[
            "electron_contribution"
        ] = round(
            contribution,
            4,
        )

        metal_details.append(
            redox_window
        )

    lithium_amount = safe_float(
        reduced.get_el_amt_dict().get(
            "Li",
            0,
        )
    )

    if lithium_amount is None:
        lithium_amount = 0.0

    lithium_limited_electrons = min(
        raw_redox_electrons,
        lithium_amount,
    )

    return {
        "raw_redox_electrons":
            round(raw_redox_electrons, 4),

        "lithium_amount":
            round(lithium_amount, 4),

        "estimated_extractable_electrons":
            round(
                lithium_limited_electrons,
                4,
            ),

        "metal_redox_details":
            metal_details,
    }


# ============================================================
# REDOX INTERPRETATION
# ============================================================

def summarize_redox_metals(
    metal_details: list[dict[str, Any]],
) -> str:
    """
    Create compact redox-metal summary.
    """

    if not metal_details:
        return "None identified"

    summaries: list[str] = []

    for detail in metal_details:

        metal = detail["metal"]

        starting = detail[
            "starting_oxidation_state"
        ]

        maximum = detail[
            "maximum_state"
        ]

        if maximum is None:

            summaries.append(
                f"{metal}({starting:+.2f})"
            )

            continue

        summaries.append(
            f"{metal}({starting:+.2f} → "
            f"up to +{maximum})"
        )

    return "; ".join(
        summaries
    )


def generate_redox_notes(
    composition: Composition,
    oxidation_guess: dict[str, float],
    redox_metals: list[str],
    electron_data: dict[str, Any],
    framework_positives: list[str],
    framework_concerns: list[str],
) -> tuple[list[str], list[str]]:
    """
    Generate qualitative redox strengths and concerns.
    """

    positives = list(
        framework_positives
    )

    concerns = list(
        framework_concerns
    )

    # --------------------------------------------------------
    # Presence of redox-active metals
    # --------------------------------------------------------

    if redox_metals:

        positives.append(
            "Contains transition-metal species capable of "
            "supporting cathode redox chemistry."
        )

    else:

        concerns.append(
            "No conventional transition-metal redox center "
            "was identified."
        )

    # --------------------------------------------------------
    # Oxidation room
    # --------------------------------------------------------

    extractable = electron_data[
        "estimated_extractable_electrons"
    ]

    if extractable >= 2.0:

        positives.append(
            "Multiple transition-metal oxidation equivalents "
            "are chemically available before the selected "
            "upper oxidation-state limits."
        )

    elif extractable >= 1.0:

        positives.append(
            "At least one electron equivalent of "
            "transition-metal oxidation is available."
        )

    elif extractable > 0:

        concerns.append(
            "Only a fractional electron equivalent of "
            "transition-metal oxidation is available."
        )

    else:

        concerns.append(
            "No conventional transition-metal oxidation "
            "capacity was identified from the inferred "
            "starting oxidation state."
        )

    # --------------------------------------------------------
    # Lithium content
    # --------------------------------------------------------

    lithium_amount = electron_data[
        "lithium_amount"
    ]

    if lithium_amount <= 0:

        concerns.append(
            "No lithium inventory is present in the "
            "reduced formula."
        )

    elif lithium_amount >= 2:

        positives.append(
            "The reduced formula contains multiple lithium "
            "ions that could potentially participate in "
            "delithiation."
        )

    # --------------------------------------------------------
    # Known couples
    # --------------------------------------------------------

    known_couples = [
        detail
        for detail in electron_data[
            "metal_redox_details"
        ]
        if detail["known_couple"]
    ]

    if known_couples:

        couple_names = sorted(
            {
                detail[
                    "couple_description"
                ]
                for detail in known_couples
            }
        )

        positives.append(
            "Starting chemistry overlaps with familiar "
            "transition-metal redox windows: "
            + "; ".join(couple_names)
            + "."
        )

    else:

        concerns.append(
            "No familiar cathode redox couple was matched "
            "near the inferred starting oxidation state."
        )

    # --------------------------------------------------------
    # Extremely oxidized metals
    # --------------------------------------------------------

    for metal in redox_metals:

        oxidation_state = oxidation_guess.get(
            metal
        )

        if oxidation_state is None:
            continue

        maximum = REDOX_WINDOWS.get(
            metal,
            (None, None),
        )[1]

        if (
            maximum is not None
            and oxidation_state >= maximum - 0.1
        ):

            concerns.append(
                f"{metal} begins near the conservative "
                f"upper oxidation-state limit "
                f"({oxidation_state:+.2f}), leaving little "
                f"conventional cation-redox headroom."
            )

    return positives, concerns


# ============================================================
# REDOX SCORE
# ============================================================

def calculate_redox_score(
    *,
    oxidation_solution_found: bool,
    oxidation_method: str,
    redox_metals: list[str],
    electron_data: dict[str, Any],
    framework_concerns: list[str],
) -> float:
    """
    Calculate a screening-level redox score.

    This score measures chemical plausibility, NOT electrochemical
    performance.
    """

    score = 35.0

    # --------------------------------------------------------
    # Charge-balanced oxidation-state solution
    # --------------------------------------------------------

    if oxidation_solution_found:

        if oxidation_method == "COMMON_STATES":
            score += 20

        elif (
            oxidation_method
            == "ALL_STATES_FALLBACK"
        ):
            score += 8

    else:
        score -= 25

    # --------------------------------------------------------
    # Redox-active metals
    # --------------------------------------------------------

    if len(redox_metals) >= 2:
        score += 12

    elif len(redox_metals) == 1:
        score += 10

    else:
        score -= 20

    # --------------------------------------------------------
    # Electron inventory
    # --------------------------------------------------------

    electrons = electron_data[
        "estimated_extractable_electrons"
    ]

    if electrons >= 2.0:
        score += 18

    elif electrons >= 1.0:
        score += 14

    elif electrons >= 0.5:
        score += 5

    elif electrons > 0:
        score += 1

    else:
        score -= 15

    # --------------------------------------------------------
    # Familiar redox couples
    # --------------------------------------------------------

    known_count = sum(
        1
        for detail in electron_data[
            "metal_redox_details"
        ]
        if detail["known_couple"]
    )

    if known_count >= 1:
        score += 8

    # --------------------------------------------------------
    # Framework chemistry penalty
    # --------------------------------------------------------

    score -= min(
        20,
        8 * len(
            framework_concerns
        ),
    )

    return round(
        max(
            0.0,
            min(
                100.0,
                score,
            ),
        ),
        1,
    )


def classify_redox_score(
    score: float,
) -> str:
    """
    Convert score into a redox screening category.
    """

    if score >= 85:
        return "STRONG"

    if score >= 72:
        return "PROMISING"

    if score >= 58:
        return "MODERATE"

    if score >= 42:
        return "REVIEW"

    return "WEAK"


# ============================================================
# CONFIDENCE
# ============================================================

def determine_redox_confidence(
    oxidation_method: str,
    number_of_guesses: int,
    framework_concerns: list[str],
) -> str:
    """
    Estimate confidence in the oxidation-state inference.
    """

    if oxidation_method == "NO_SOLUTION":
        return "LOW"

    if oxidation_method == "ALL_STATES_FALLBACK":
        return "LOW"

    # Multiple valid oxidation-state solutions imply some chemical
    # ambiguity even if pymatgen ranks one as most probable.

    if (
        number_of_guesses <= 3
        and not framework_concerns
    ):
        return "HIGH"

    return "MODERATE"


# ============================================================
# SINGLE-CANDIDATE ANALYSIS
# ============================================================

def analyze_candidate(
    row: pd.Series,
) -> dict[str, Any]:
    """
    Perform complete redox analysis for one candidate.
    """

    result = row.to_dict()

    material_id = str(
        row["material_id"]
    )

    formula = str(
        row["formula"]
    )

    composition = build_composition(
        formula
    )

    reduced_composition = (
        composition.reduced_composition
    )

    reduced_formula = (
        reduced_composition.reduced_formula
    )

    # --------------------------------------------------------
    # Oxidation-state guesses
    # --------------------------------------------------------

    guesses, oxidation_method = (
        get_oxidation_state_guesses(
            reduced_composition
        )
    )

    normalized_guesses = [
        normalize_oxidation_guess(
            guess
        )
        for guess in guesses
    ]

    oxidation_solution_found = (
        len(normalized_guesses) > 0
    )

    if oxidation_solution_found:

        primary_guess = (
            normalized_guesses[0]
        )

        primary_guess_text = (
            oxidation_guess_string(
                primary_guess
            )
        )

    else:

        primary_guess = {}

        primary_guess_text = (
            "No charge-balanced assignment"
        )

    # Store up to three alternative guesses for transparency.

    alternative_texts = [
        oxidation_guess_string(
            guess
        )
        for guess in normalized_guesses[
            1:4
        ]
    ]

    alternative_guess_text = (
        " | ".join(
            alternative_texts
        )
        if alternative_texts
        else ""
    )

    # --------------------------------------------------------
    # Identify redox metals
    # --------------------------------------------------------

    redox_metals = identify_redox_metals(
        reduced_composition
    )

    # --------------------------------------------------------
    # Framework validation
    # --------------------------------------------------------

    (
        framework_positives,
        framework_concerns,
    ) = assess_framework_oxidation_states(
        primary_guess
    )

    # --------------------------------------------------------
    # Electron-transfer analysis
    # --------------------------------------------------------

    if oxidation_solution_found:

        electron_data = (
            estimate_redox_electrons(
                reduced_composition,
                primary_guess,
                redox_metals,
            )
        )

    else:

        lithium_amount = safe_float(
            reduced_composition
            .get_el_amt_dict()
            .get(
                "Li",
                0,
            )
        )

        electron_data = {
            "raw_redox_electrons": 0.0,
            "lithium_amount":
                lithium_amount or 0.0,
            "estimated_extractable_electrons":
                0.0,
            "metal_redox_details": [],
        }

    # --------------------------------------------------------
    # Qualitative interpretation
    # --------------------------------------------------------

    positives, concerns = (
        generate_redox_notes(
            reduced_composition,
            primary_guess,
            redox_metals,
            electron_data,
            framework_positives,
            framework_concerns,
        )
    )

    # --------------------------------------------------------
    # Redox score
    # --------------------------------------------------------

    redox_score = calculate_redox_score(
        oxidation_solution_found=
            oxidation_solution_found,

        oxidation_method=
            oxidation_method,

        redox_metals=
            redox_metals,

        electron_data=
            electron_data,

        framework_concerns=
            framework_concerns,
    )

    redox_rating = classify_redox_score(
        redox_score
    )

    redox_confidence = (
        determine_redox_confidence(
            oxidation_method,
            len(normalized_guesses),
            framework_concerns,
        )
    )

    # --------------------------------------------------------
    # Metal-specific summaries
    # --------------------------------------------------------

    metal_details = electron_data[
        "metal_redox_details"
    ]

    redox_summary = (
        summarize_redox_metals(
            metal_details
        )
    )

    # Individual oxidation-state columns for easier downstream use.

    inferred_states = {
        f"inferred_oxi_{symbol}":
            round(
                oxidation_state,
                4,
            )
        for symbol, oxidation_state
        in primary_guess.items()
    }

    result.update(
        {
            "redox_reduced_formula":
                reduced_formula,

            "oxidation_solution_found":
                oxidation_solution_found,

            "oxidation_inference_method":
                oxidation_method,

            "oxidation_guess_count":
                len(normalized_guesses),

            "primary_oxidation_states":
                primary_guess_text,

            "alternative_oxidation_states":
                alternative_guess_text,

            "redox_active_metals":
                ", ".join(
                    redox_metals
                ),

            "redox_metal_count":
                len(redox_metals),

            "redox_pathway_summary":
                redox_summary,

            "raw_redox_electrons":
                electron_data[
                    "raw_redox_electrons"
                ],

            "formula_lithium_inventory":
                electron_data[
                    "lithium_amount"
                ],

            "estimated_extractable_electrons":
                electron_data[
                    "estimated_extractable_electrons"
                ],

            "redox_score":
                redox_score,

            "redox_rating":
                redox_rating,

            "redox_confidence":
                redox_confidence,

            "redox_positives":
                " | ".join(
                    positives
                ),

            "redox_concerns":
                " | ".join(
                    concerns
                ),

            **inferred_states,
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
    Generate the Week 7 redox chemistry report.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ranked = dataframe.sort_values(
        [
            "redox_score",
            "structure_score",
        ],
        ascending=[
            False,
            False,
        ],
    ).copy()

    lines: list[str] = []

    lines.append(
        "# MAPPS-Lite Week 7 Redox Chemistry Analysis"
    )

    lines.append("")

    # ========================================================
    # Objective
    # ========================================================

    lines.append("## Objective")
    lines.append("")

    lines.append(
        "This stage evaluates whether each surviving cathode "
        "candidate contains chemically plausible transition-metal "
        "redox chemistry capable of supporting lithium extraction "
        "and reinsertion."
    )

    lines.append("")

    lines.append(
        "Charge-balanced oxidation states are inferred using "
        "pymatgen. The most probable assignment is used as the "
        "primary screening hypothesis."
    )

    lines.append("")

    lines.append(
        "**Important:** oxidation-state plausibility does not prove "
        "electrochemical reversibility, operating voltage, kinetic "
        "performance, or cycling stability."
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

    solved = int(
        dataframe[
            "oxidation_solution_found"
        ]
        .fillna(False)
        .sum()
    )

    lines.append(
        f"- Charge-balanced oxidation-state solutions: "
        f"**{solved}/{len(dataframe)}**"
    )

    ratings = (
        dataframe[
            "redox_rating"
        ]
        .value_counts()
        .to_dict()
    )

    for rating in [
        "STRONG",
        "PROMISING",
        "MODERATE",
        "REVIEW",
        "WEAK",
    ]:

        count = ratings.get(
            rating,
            0,
        )

        if count > 0:

            lines.append(
                f"- {rating}: **{count}**"
            )

    lines.append("")

    # ========================================================
    # Ranking
    # ========================================================

    lines.append(
        "## Redox Screening Ranking"
    )

    lines.append("")

    lines.append(
        "| Rank | Material | Formula | Redox Metals | "
        "Electrons | Score | Rating | Confidence |"
    )

    lines.append(
        "|---:|---|---|---|---:|---:|---|---|"
    )

    for rank, (_, row) in enumerate(
        ranked.iterrows(),
        start=1,
    ):

        lines.append(
            f"| {rank} "
            f"| {format_number(row.get('material_id'))} "
            f"| {format_number(row.get('formula'))} "
            f"| {format_number(row.get('redox_active_metals'))} "
            f"| {format_number(row.get('estimated_extractable_electrons'), 2)} "
            f"| {format_number(row.get('redox_score'), 1)} "
            f"| {format_number(row.get('redox_rating'))} "
            f"| {format_number(row.get('redox_confidence'))} |"
        )

    lines.append("")

    # ========================================================
    # Candidate details
    # ========================================================

    lines.append(
        "## Candidate Redox Details"
    )

    lines.append("")

    for rank, (_, row) in enumerate(
        ranked.iterrows(),
        start=1,
    ):

        material_id = format_number(
            row.get(
                "material_id"
            )
        )

        formula = format_number(
            row.get(
                "formula"
            )
        )

        lines.append(
            f"### {rank}. {formula} ({material_id})"
        )

        lines.append("")

        lines.append(
            f"- Redox score: "
            f"**{format_number(row.get('redox_score'), 1)}/100**"
        )

        lines.append(
            f"- Redox rating: "
            f"**{format_number(row.get('redox_rating'))}**"
        )

        lines.append(
            f"- Evidence confidence: "
            f"**{format_number(row.get('redox_confidence'))}**"
        )

        lines.append(
            f"- Oxidation inference method: "
            f"{format_number(row.get('oxidation_inference_method'))}"
        )

        lines.append(
            f"- Plausible oxidation-state combinations: "
            f"{format_number(row.get('oxidation_guess_count'))}"
        )

        lines.append(
            f"- Primary oxidation-state assignment: "
            f"{format_number(row.get('primary_oxidation_states'))}"
        )

        alternatives = row.get(
            "alternative_oxidation_states"
        )

        if (
            alternatives is not None
            and not pd.isna(alternatives)
            and str(
                alternatives
            ).strip()
        ):

            lines.append(
                f"- Alternative assignments: "
                f"{alternatives}"
            )

        lines.append(
            f"- Redox-active metals: "
            f"{format_number(row.get('redox_active_metals'))}"
        )

        lines.append(
            f"- Proposed redox window: "
            f"{format_number(row.get('redox_pathway_summary'))}"
        )

        lines.append(
            f"- Lithium inventory per reduced formula: "
            f"{format_number(row.get('formula_lithium_inventory'), 2)}"
        )

        lines.append(
            f"- Raw transition-metal oxidation inventory: "
            f"{format_number(row.get('raw_redox_electrons'), 2)} "
            f"e⁻/formula"
        )

        lines.append(
            f"- Conservative Li-limited electron estimate: "
            f"**{format_number(row.get('estimated_extractable_electrons'), 2)} "
            f"e⁻/formula**"
        )

        # ----------------------------------------------------
        # Positives
        # ----------------------------------------------------

        positives = row.get(
            "redox_positives"
        )

        if (
            positives is not None
            and not pd.isna(
                positives
            )
            and str(
                positives
            ).strip()
        ):

            lines.append("")
            lines.append(
                "**Positive indicators**"
            )
            lines.append("")

            for item in str(
                positives
            ).split(
                " | "
            ):

                lines.append(
                    f"- {item}"
                )

        # ----------------------------------------------------
        # Concerns
        # ----------------------------------------------------

        concerns = row.get(
            "redox_concerns"
        )

        if (
            concerns is not None
            and not pd.isna(
                concerns
            )
            and str(
                concerns
            ).strip()
        ):

            lines.append("")
            lines.append(
                "**Redox concerns**"
            )
            lines.append("")

            for item in str(
                concerns
            ).split(
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
        "## Scientific Interpretation"
    )

    lines.append("")

    lines.append(
        "Cathode operation normally requires oxidation of a "
        "redox-active species during lithium extraction and "
        "reduction during lithium reinsertion."
    )

    lines.append("")

    lines.append(
        "This analysis estimates how much conventional "
        "transition-metal oxidation capacity exists between the "
        "inferred starting state and a conservative upper oxidation "
        "state for each metal."
    )

    lines.append("")

    lines.append(
        "The estimate is then limited by the amount of lithium "
        "available in the reduced chemical formula. This prevents "
        "the screening model from assigning more conventional "
        "Li-coupled electrons than the composition contains."
    )

    lines.append("")

    lines.append(
        "A high redox score therefore means that the composition "
        "has a plausible charge-balanced starting chemistry, one or "
        "more recognizable transition-metal redox centers, and "
        "meaningful conventional oxidation headroom."
    )

    lines.append("")

    lines.append(
        "It does **not** mean that all predicted electrons can be "
        "reversibly extracted in a real battery."
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
        "The next Week 7 stage will combine composition, molar mass, "
        "and the conservative electron-transfer estimate to calculate "
        "screening-level theoretical specific capacity and related "
        "performance descriptors."
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
    Run the complete Week 7 redox analysis.
    """

    print()
    print("=" * 72)
    print("MAPPS-LITE WEEK 7")
    print("CANDIDATE REDOX CHEMISTRY ANALYSIS")
    print("=" * 72)

    # --------------------------------------------------------
    # Stage 1
    # --------------------------------------------------------

    print()
    print(
        "[1/4] Loading Week 7 structural candidates..."
    )

    candidates = load_candidates()

    print(
        f"Loaded {len(candidates)} candidates."
    )

    # --------------------------------------------------------
    # Stage 2
    # --------------------------------------------------------

    print()
    print(
        "[2/4] Inferring oxidation states and redox chemistry..."
    )

    results: list[dict[str, Any]] = []

    total = len(
        candidates
    )

    for index, (_, row) in enumerate(
        candidates.iterrows(),
        start=1,
    ):

        material_id = row[
            "material_id"
        ]

        formula = row[
            "formula"
        ]

        print(
            f"  [{index}/{total}] "
            f"{material_id} {formula}"
        )

        try:

            result = analyze_candidate(
                row
            )

        except Exception as exc:

            result = row.to_dict()

            result.update(
                {
                    "redox_reduced_formula":
                        formula,

                    "oxidation_solution_found":
                        False,

                    "oxidation_inference_method":
                        "ANALYSIS_ERROR",

                    "oxidation_guess_count":
                        0,

                    "primary_oxidation_states":
                        "Analysis failed",

                    "alternative_oxidation_states":
                        "",

                    "redox_active_metals":
                        "",

                    "redox_metal_count":
                        0,

                    "redox_pathway_summary":
                        "Analysis failed",

                    "raw_redox_electrons":
                        0.0,

                    "formula_lithium_inventory":
                        None,

                    "estimated_extractable_electrons":
                        0.0,

                    "redox_score":
                        0.0,

                    "redox_rating":
                        "WEAK",

                    "redox_confidence":
                        "LOW",

                    "redox_positives":
                        "",

                    "redox_concerns":
                        f"Redox analysis failed: {exc}",
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
            "redox_score",
            "structure_score",
            "week7_input_rank",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    ).reset_index(
        drop=True
    )

    dataframe.insert(
        0,
        "redox_rank",
        range(
            1,
            len(
                dataframe
            ) + 1,
        ),
    )

    # --------------------------------------------------------
    # Stage 3
    # --------------------------------------------------------

    print()
    print(
        "[3/4] Saving redox dataset..."
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
        "[4/4] Generating redox report..."
    )

    generate_report(
        dataframe
    )

    print(
        f"Saved: {REPORT_FILE}"
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "WEEK 7 REDOX CHEMISTRY ANALYSIS COMPLETE"
    )
    print("=" * 72)

    print()
    print(
        "Top redox candidates:"
    )
    print()

    preview_columns = [
        "redox_rank",
        "material_id",
        "formula",
        "primary_oxidation_states",
        "redox_active_metals",
        "estimated_extractable_electrons",
        "redox_score",
        "redox_rating",
        "redox_confidence",
    ]

    available_columns = [
        column
        for column in preview_columns
        if column in dataframe.columns
    ]

    print(
        dataframe[
            available_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "NOTE: Redox scores measure chemical plausibility only."
    )

    print(
        "They do not directly predict voltage, reversible capacity, "
        "cycle life, or reaction kinetics."
    )

    print()


if __name__ == "__main__":

    try:

        main()

    except Exception as exc:

        print()
        print("=" * 72)
        print("ERROR")
        print("=" * 72)
        print(exc)
        print()

        sys.exit(1)