"""
MAPPS-Lite Week 7
Candidate Crystal Structure Analysis

Purpose
-------
Perform a deeper structural analysis of the strongest candidates surviving
Week 6.

The script:
1. Loads the Week 6 final ranking.
2. Selects the highest-ranked candidates.
3. Retrieves crystal structures from the Materials Project.
4. Extracts structural, symmetry, lithium, and framework descriptors.
5. Calculates transport-relevant structural proxies.
6. Assigns a structural assessment and confidence level.
7. Saves a CSV and Markdown report.

Inputs
------
data/week6_final_ranking.csv

Outputs
-------
data/week7_candidate_structures.csv
reports/week7_structure_analysis.md
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mp_api.client import MPRester
from pymatgen.core import Structure


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "week6_final_ranking.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "week7_candidate_structures.csv"
REPORT_FILE = PROJECT_ROOT / "reports" / "week7_structure_analysis.md"


# ============================================================
# CONFIGURATION
# ============================================================

# We begin Week 7 with a manageable research set.
# This can be changed later if needed.
TOP_N_CANDIDATES = int(os.getenv("WEEK7_TOP_N", "10"))

# Radius used only as a descriptive local-environment proxy.
LI_NEIGHBOR_RADIUS = 3.0

# Materials Project query fields.
MP_FIELDS = [
    "material_id",
    "formula_pretty",
    "structure",
    "symmetry",
    "density",
    "energy_above_hull",
    "formation_energy_per_atom",
    "is_stable",
    "band_gap",
    "volume",
    "nsites",
]


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_float(value: Any) -> float | None:
    """
    Convert a value to float when possible.

    Returns None for missing, invalid, or non-finite values.
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


def find_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    """
    Find the first matching column from a list of possible names.

    This makes the Week 7 script tolerant of small naming differences
    in Week 6 files.
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


def get_document_value(document: Any, field: str) -> Any:
    """
    Safely retrieve a field from either a pydantic-style document
    or dictionary returned by the Materials Project API.
    """

    if document is None:
        return None

    if isinstance(document, dict):
        return document.get(field)

    return getattr(document, field, None)


# ============================================================
# LOAD WEEK 6 CANDIDATES
# ============================================================

def load_week6_candidates() -> pd.DataFrame:
    """
    Load and select the strongest Week 6 candidates.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find Week 6 ranking file:\n{INPUT_FILE}"
        )

    dataframe = pd.read_csv(INPUT_FILE)

    if dataframe.empty:
        raise ValueError(
            "week6_final_ranking.csv exists but contains no candidates."
        )

    material_id_column = find_column(
        dataframe,
        [
            "material_id",
            "mp_id",
            "materials_project_id",
        ],
    )

    if material_id_column is None:
        raise ValueError(
            "Could not locate a Materials Project ID column.\n"
            "Expected something similar to 'material_id'."
        )

    if material_id_column != "material_id":
        dataframe = dataframe.rename(
            columns={material_id_column: "material_id"}
        )

    dataframe["material_id"] = (
        dataframe["material_id"]
        .astype(str)
        .str.strip()
    )

    # Remove obviously invalid IDs.
    dataframe = dataframe[
        dataframe["material_id"].str.startswith("mp-")
    ].copy()

    if dataframe.empty:
        raise ValueError(
            "No valid Materials Project IDs were found in the Week 6 ranking."
        )

    # Try to preserve the Week 6 ranking.
    rank_column = find_column(
        dataframe,
        [
            "final_rank",
            "week6_rank",
            "rank",
            "ranking",
        ],
    )

    score_column = find_column(
        dataframe,
        [
            "final_score",
            "week6_score",
            "overall_score",
            "composite_score",
            "score",
        ],
    )

    if rank_column is not None:
        dataframe[rank_column] = pd.to_numeric(
            dataframe[rank_column],
            errors="coerce",
        )

        dataframe = dataframe.sort_values(
            rank_column,
            ascending=True,
            na_position="last",
        )

    elif score_column is not None:
        dataframe[score_column] = pd.to_numeric(
            dataframe[score_column],
            errors="coerce",
        )

        dataframe = dataframe.sort_values(
            score_column,
            ascending=False,
            na_position="last",
        )

    # Remove duplicate MP IDs before analysis.
    dataframe = dataframe.drop_duplicates(
        subset=["material_id"],
        keep="first",
    )

    selected = dataframe.head(TOP_N_CANDIDATES).copy()

    selected.insert(
        0,
        "week7_input_rank",
        range(1, len(selected) + 1),
    )

    return selected


# ============================================================
# MATERIALS PROJECT DATA
# ============================================================

def retrieve_mp_documents(
    material_ids: list[str],
) -> dict[str, Any]:
    """
    Retrieve Materials Project summary documents for candidate IDs.
    """

    api_key = os.getenv("MP_API_KEY")

    if not api_key:
        raise RuntimeError(
            "\nMP_API_KEY was not found.\n\n"
            "Set your Materials Project API key before running this script.\n"
            "For Windows Command Prompt:\n"
            'set MP_API_KEY=YOUR_API_KEY\n\n'
            "For PowerShell:\n"
            '$env:MP_API_KEY="YOUR_API_KEY"\n'
        )

    print()
    print("Connecting to Materials Project...")
    print(f"Retrieving structures for {len(material_ids)} candidates...")

    with MPRester(api_key) as mpr:
        documents = mpr.materials.summary.search(
            material_ids=material_ids,
            fields=MP_FIELDS,
        )

    document_map: dict[str, Any] = {}

    for document in documents:
        material_id = str(
            get_document_value(document, "material_id")
        )

        document_map[material_id] = document

    print(
        f"Retrieved {len(document_map)} "
        f"of {len(material_ids)} requested structures."
    )

    return document_map


# ============================================================
# CHEMISTRY / FRAMEWORK CLASSIFICATION
# ============================================================

def classify_framework(structure: Structure) -> str:
    """
    Classify the broad anion/framework chemistry.

    This is a chemistry-based family label, not a claim that the
    material has a specific commercial cathode structure.
    """

    elements = {
        str(element)
        for element in structure.composition.elements
    }

    has_o = "O" in elements
    has_f = "F" in elements
    has_s = "S" in elements
    has_p = "P" in elements
    has_si = "Si" in elements
    has_b = "B" in elements
    has_c = "C" in elements

    if has_o and has_p:
        return "PHOSPHATE / OXYPHOSPHATE"

    if has_o and has_si:
        return "SILICATE / OXYSILICATE"

    if has_o and has_b:
        return "BORATE / OXYBORATE"

    if has_o and has_s:
        return "SULFATE / OXYSULFATE"

    if has_o and has_c:
        return "CARBONATE / OXYCARBON"

    if has_o and has_f:
        return "OXYFLUORIDE"

    if has_f and not has_o:
        return "FLUORIDE"

    if has_s and not has_o:
        return "SULFIDE"

    if has_o:
        return "OXIDE"

    return "OTHER"


# ============================================================
# LITHIUM DESCRIPTORS
# ============================================================

def calculate_lithium_descriptors(
    structure: Structure,
) -> dict[str, Any]:
    """
    Calculate lithium-related structural descriptors.

    These are structural proxies only. They do not directly calculate
    migration barriers or ionic conductivity.
    """

    total_sites = len(structure)

    li_indices = [
        index
        for index, site in enumerate(structure)
        if site.specie.symbol == "Li"
    ]

    li_sites = len(li_indices)

    li_atomic_fraction = (
        li_sites / total_sites
        if total_sites > 0
        else 0.0
    )

    if li_sites == 0:
        return {
            "li_sites": 0,
            "li_atomic_fraction": 0.0,
            "min_li_li_distance": None,
            "mean_li_li_distance": None,
            "mean_li_neighbor_count": None,
        }

    nearest_li_distances: list[float] = []
    local_neighbor_counts: list[int] = []

    for li_index in li_indices:
        li_site = structure[li_index]

        # ----------------------------------------------------
        # Local coordination proxy
        # ----------------------------------------------------

        neighbors = structure.get_neighbors(
            li_site,
            LI_NEIGHBOR_RADIUS,
        )

        non_li_neighbors = [
            neighbor
            for neighbor in neighbors
            if neighbor.specie.symbol != "Li"
        ]

        local_neighbor_counts.append(
            len(non_li_neighbors)
        )

        # ----------------------------------------------------
        # Nearest Li-Li distance
        # ----------------------------------------------------

        li_neighbors = [
            neighbor
            for neighbor in structure.get_neighbors(
                li_site,
                6.0,
            )
            if neighbor.specie.symbol == "Li"
        ]

        if li_neighbors:
            nearest_distance = min(
                float(neighbor.nn_distance)
                for neighbor in li_neighbors
            )

            nearest_li_distances.append(
                nearest_distance
            )

    return {
        "li_sites": li_sites,
        "li_atomic_fraction": round(
            li_atomic_fraction,
            4,
        ),
        "min_li_li_distance": (
            round(min(nearest_li_distances), 4)
            if nearest_li_distances
            else None
        ),
        "mean_li_li_distance": (
            round(float(np.mean(nearest_li_distances)), 4)
            if nearest_li_distances
            else None
        ),
        "mean_li_neighbor_count": (
            round(float(np.mean(local_neighbor_counts)), 2)
            if local_neighbor_counts
            else None
        ),
    }


# ============================================================
# LATTICE DESCRIPTORS
# ============================================================

def calculate_lattice_descriptors(
    structure: Structure,
) -> dict[str, Any]:
    """
    Extract basic unit-cell and lattice geometry.
    """

    lattice = structure.lattice

    lengths = [
        float(lattice.a),
        float(lattice.b),
        float(lattice.c),
    ]

    shortest = min(lengths)
    longest = max(lengths)

    lattice_anisotropy = (
        longest / shortest
        if shortest > 0
        else None
    )

    volume_per_atom = (
        structure.volume / len(structure)
        if len(structure) > 0
        else None
    )

    return {
        "lattice_a": round(float(lattice.a), 4),
        "lattice_b": round(float(lattice.b), 4),
        "lattice_c": round(float(lattice.c), 4),
        "alpha": round(float(lattice.alpha), 3),
        "beta": round(float(lattice.beta), 3),
        "gamma": round(float(lattice.gamma), 3),
        "cell_volume": round(
            float(structure.volume),
            4,
        ),
        "volume_per_atom": (
            round(float(volume_per_atom), 4)
            if volume_per_atom is not None
            else None
        ),
        "lattice_anisotropy": (
            round(float(lattice_anisotropy), 4)
            if lattice_anisotropy is not None
            else None
        ),
    }


# ============================================================
# STRUCTURAL SCORE
# ============================================================

def calculate_structure_score(
    *,
    is_stable: bool | None,
    energy_above_hull: float | None,
    li_fraction: float | None,
    min_li_li_distance: float | None,
    volume_per_atom: float | None,
) -> tuple[float, list[str], list[str]]:
    """
    Create a conservative structure-screening score.

    Important:
    This is NOT an electrochemical performance score.

    It only measures whether several structural characteristics appear
    broadly favorable for continued cathode investigation.
    """

    score = 50.0

    positives: list[str] = []
    concerns: list[str] = []

    # --------------------------------------------------------
    # Thermodynamic stability
    # --------------------------------------------------------

    if is_stable is True:
        score += 15
        positives.append(
            "Reported stable on the Materials Project convex hull."
        )

    elif energy_above_hull is not None:

        if energy_above_hull <= 0.025:
            score += 10
            positives.append(
                "Very low energy above hull."
            )

        elif energy_above_hull <= 0.050:
            score += 5
            positives.append(
                "Relatively low energy above hull."
            )

        elif energy_above_hull > 0.100:
            score -= 12
            concerns.append(
                "Elevated energy above hull may indicate "
                "thermodynamic metastability."
            )

        else:
            concerns.append(
                "Material is metastable but remains "
                "within a moderate energy range."
            )

    # --------------------------------------------------------
    # Lithium availability
    # --------------------------------------------------------

    if li_fraction is not None:

        if 0.15 <= li_fraction <= 0.50:
            score += 10
            positives.append(
                "Substantial lithium fraction is present "
                "in the crystal structure."
            )

        elif li_fraction < 0.08:
            score -= 8
            concerns.append(
                "Low lithium fraction may limit practical "
                "extractable lithium inventory."
            )

    # --------------------------------------------------------
    # Li-Li spacing proxy
    # --------------------------------------------------------

    if min_li_li_distance is not None:

        if 2.5 <= min_li_li_distance <= 4.0:
            score += 8
            positives.append(
                "Li-Li separation lies in a potentially "
                "reasonable transport-relevant range."
            )

        elif min_li_li_distance > 5.0:
            score -= 6
            concerns.append(
                "Large Li-Li separation may indicate a "
                "poorly connected lithium sublattice."
            )

        elif min_li_li_distance < 2.0:
            score -= 4
            concerns.append(
                "Very short Li-Li separation warrants "
                "closer structural inspection."
            )

    # --------------------------------------------------------
    # Atomic packing proxy
    # --------------------------------------------------------

    if volume_per_atom is not None:

        if 8 <= volume_per_atom <= 30:
            score += 5
            positives.append(
                "Atomic packing density is within a broadly "
                "reasonable inorganic-solid range."
            )

        elif volume_per_atom > 45:
            score -= 4
            concerns.append(
                "Large volume per atom suggests an unusually "
                "open or low-density framework."
            )

    score = max(
        0.0,
        min(100.0, score),
    )

    return (
        round(score, 1),
        positives,
        concerns,
    )


def classify_structure_score(score: float) -> str:
    """
    Convert numerical structure score into a research category.
    """

    if score >= 82:
        return "STRONG"

    if score >= 70:
        return "PROMISING"

    if score >= 58:
        return "MODERATE"

    if score >= 45:
        return "REVIEW"

    return "WEAK"


def calculate_confidence(
    structure: Structure | None,
    symmetry: Any,
    energy_above_hull: float | None,
) -> str:
    """
    Estimate confidence in the structural assessment.

    Confidence reflects data completeness, not candidate quality.
    """

    available = 0

    if structure is not None:
        available += 1

    if symmetry is not None:
        available += 1

    if energy_above_hull is not None:
        available += 1

    if available == 3:
        return "HIGH"

    if available == 2:
        return "MODERATE"

    return "LOW"


# ============================================================
# SYMMETRY EXTRACTION
# ============================================================

def extract_symmetry(symmetry: Any) -> dict[str, Any]:
    """
    Extract crystal system and space group information.
    """

    if symmetry is None:
        return {
            "crystal_system": None,
            "space_group_symbol": None,
            "space_group_number": None,
        }

    if isinstance(symmetry, dict):

        crystal_system = symmetry.get(
            "crystal_system"
        )

        symbol = symmetry.get("symbol")
        number = symmetry.get("number")

    else:

        crystal_system = getattr(
            symmetry,
            "crystal_system",
            None,
        )

        symbol = getattr(
            symmetry,
            "symbol",
            None,
        )

        number = getattr(
            symmetry,
            "number",
            None,
        )

    if hasattr(crystal_system, "value"):
        crystal_system = crystal_system.value

    return {
        "crystal_system": (
            str(crystal_system)
            if crystal_system is not None
            else None
        ),
        "space_group_symbol": symbol,
        "space_group_number": number,
    }


# ============================================================
# INDIVIDUAL CANDIDATE ANALYSIS
# ============================================================

def analyze_candidate(
    candidate: pd.Series,
    document: Any,
) -> dict[str, Any]:
    """
    Analyze one Week 7 candidate.
    """

    material_id = candidate["material_id"]

    base_result = candidate.to_dict()

    if document is None:

        base_result.update(
            {
                "mp_formula": None,
                "structure_retrieved": False,
                "structure_score": 0.0,
                "structure_rating": "NO_DATA",
                "structure_confidence": "LOW",
                "structural_positives": "",
                "structural_concerns":
                    "Materials Project structure could not be retrieved.",
            }
        )

        return base_result

    structure = get_document_value(
        document,
        "structure",
    )

    if structure is None:

        base_result.update(
            {
                "mp_formula": get_document_value(
                    document,
                    "formula_pretty",
                ),
                "structure_retrieved": False,
                "structure_score": 0.0,
                "structure_rating": "NO_STRUCTURE",
                "structure_confidence": "LOW",
                "structural_positives": "",
                "structural_concerns":
                    "Materials Project record exists but no "
                    "structure was returned.",
            }
        )

        return base_result

    # --------------------------------------------------------
    # Materials Project properties
    # --------------------------------------------------------

    symmetry = get_document_value(
        document,
        "symmetry",
    )

    energy_above_hull = safe_float(
        get_document_value(
            document,
            "energy_above_hull",
        )
    )

    formation_energy = safe_float(
        get_document_value(
            document,
            "formation_energy_per_atom",
        )
    )

    density = safe_float(
        get_document_value(
            document,
            "density",
        )
    )

    band_gap = safe_float(
        get_document_value(
            document,
            "band_gap",
        )
    )

    is_stable = get_document_value(
        document,
        "is_stable",
    )

    # --------------------------------------------------------
    # Structural descriptors
    # --------------------------------------------------------

    lattice_data = calculate_lattice_descriptors(
        structure
    )

    lithium_data = calculate_lithium_descriptors(
        structure
    )

    symmetry_data = extract_symmetry(
        symmetry
    )

    framework = classify_framework(
        structure
    )

    # --------------------------------------------------------
    # Structural screening score
    # --------------------------------------------------------

    structure_score, positives, concerns = (
        calculate_structure_score(
            is_stable=is_stable,
            energy_above_hull=energy_above_hull,
            li_fraction=lithium_data[
                "li_atomic_fraction"
            ],
            min_li_li_distance=lithium_data[
                "min_li_li_distance"
            ],
            volume_per_atom=lattice_data[
                "volume_per_atom"
            ],
        )
    )

    structure_rating = classify_structure_score(
        structure_score
    )

    confidence = calculate_confidence(
        structure,
        symmetry,
        energy_above_hull,
    )

    # --------------------------------------------------------
    # Build output row
    # --------------------------------------------------------

    result = base_result.copy()

    result.update(
        {
            "mp_formula": get_document_value(
                document,
                "formula_pretty",
            ),
            "structure_retrieved": True,
            "framework_family": framework,
            "crystal_system":
                symmetry_data["crystal_system"],
            "space_group_symbol":
                symmetry_data["space_group_symbol"],
            "space_group_number":
                symmetry_data["space_group_number"],
            "num_sites": len(structure),
            "density_g_cm3": (
                round(density, 4)
                if density is not None
                else None
            ),
            "energy_above_hull_ev_atom": (
                round(energy_above_hull, 6)
                if energy_above_hull is not None
                else None
            ),
            "formation_energy_ev_atom": (
                round(formation_energy, 6)
                if formation_energy is not None
                else None
            ),
            "mp_is_stable": is_stable,
            "band_gap_ev": (
                round(band_gap, 4)
                if band_gap is not None
                else None
            ),
            **lattice_data,
            **lithium_data,
            "structure_score": structure_score,
            "structure_rating": structure_rating,
            "structure_confidence": confidence,
            "structural_positives": " | ".join(
                positives
            ),
            "structural_concerns": " | ".join(
                concerns
            ),
        }
    )

    return result


# ============================================================
# REPORT
# ============================================================

def format_value(
    value: Any,
    digits: int = 3,
) -> str:
    """
    Format values for Markdown output.
    """

    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"
    except (TypeError, ValueError):
        pass

    if isinstance(value, (float, np.floating)):
        return f"{value:.{digits}f}"

    return str(value)


def generate_report(
    dataframe: pd.DataFrame,
) -> None:
    """
    Generate Week 7 structural-analysis report.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ranked = dataframe.sort_values(
        "structure_score",
        ascending=False,
    ).copy()

    lines: list[str] = []

    lines.append(
        "# MAPPS-Lite Week 7 Crystal Structure Analysis"
    )
    lines.append("")
    lines.append("## Objective")
    lines.append("")
    lines.append(
        "This stage performs a deeper crystal-structure analysis "
        "of the strongest cathode candidates surviving Week 6."
    )
    lines.append("")
    lines.append(
        "The analysis evaluates crystal symmetry, lattice geometry, "
        "lithium content, lithium-site spacing, thermodynamic stability, "
        "and broad framework chemistry."
    )
    lines.append("")
    lines.append(
        "**Important:** transport-related quantities in this stage are "
        "structural proxies. They are not direct calculations of lithium "
        "migration barriers or ionic conductivity."
    )
    lines.append("")

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"- Candidates analyzed: **{len(dataframe)}**"
    )

    retrieved_count = int(
        dataframe["structure_retrieved"]
        .fillna(False)
        .sum()
    )

    lines.append(
        f"- Structures retrieved: **{retrieved_count}**"
    )

    rating_counts = (
        dataframe["structure_rating"]
        .value_counts()
        .to_dict()
    )

    for rating in [
        "STRONG",
        "PROMISING",
        "MODERATE",
        "REVIEW",
        "WEAK",
        "NO_DATA",
        "NO_STRUCTURE",
    ]:
        count = rating_counts.get(rating, 0)

        if count > 0:
            lines.append(
                f"- {rating}: **{count}**"
            )

    lines.append("")

    # --------------------------------------------------------
    # Ranking table
    # --------------------------------------------------------

    lines.append(
        "## Structural Screening Ranking"
    )
    lines.append("")

    lines.append(
        "| Rank | Material | Formula | Structure Score | "
        "Rating | Crystal System | Framework |"
    )

    lines.append(
        "|---:|---|---|---:|---|---|---|"
    )

    for rank, (_, row) in enumerate(
        ranked.iterrows(),
        start=1,
    ):

        lines.append(
            f"| {rank} "
            f"| {format_value(row.get('material_id'))} "
            f"| {format_value(row.get('mp_formula'))} "
            f"| {format_value(row.get('structure_score'), 1)} "
            f"| {format_value(row.get('structure_rating'))} "
            f"| {format_value(row.get('crystal_system'))} "
            f"| {format_value(row.get('framework_family'))} |"
        )

    lines.append("")

    # --------------------------------------------------------
    # Candidate deep dives
    # --------------------------------------------------------

    lines.append("## Candidate Details")
    lines.append("")

    for rank, (_, row) in enumerate(
        ranked.iterrows(),
        start=1,
    ):

        material_id = format_value(
            row.get("material_id")
        )

        formula = format_value(
            row.get("mp_formula")
        )

        lines.append(
            f"### {rank}. {formula} ({material_id})"
        )

        lines.append("")

        lines.append(
            f"- Structure score: "
            f"**{format_value(row.get('structure_score'), 1)}/100**"
        )

        lines.append(
            f"- Structural rating: "
            f"**{format_value(row.get('structure_rating'))}**"
        )

        lines.append(
            f"- Evidence confidence: "
            f"**{format_value(row.get('structure_confidence'))}**"
        )

        lines.append(
            f"- Crystal system: "
            f"{format_value(row.get('crystal_system'))}"
        )

        lines.append(
            f"- Space group: "
            f"{format_value(row.get('space_group_symbol'))} "
            f"(No. {format_value(row.get('space_group_number'))})"
        )

        lines.append(
            f"- Framework family: "
            f"{format_value(row.get('framework_family'))}"
        )

        lines.append(
            f"- Density: "
            f"{format_value(row.get('density_g_cm3'))} g/cm³"
        )

        lines.append(
            f"- Energy above hull: "
            f"{format_value(row.get('energy_above_hull_ev_atom'), 4)} "
            f"eV/atom"
        )

        lines.append(
            f"- Lithium atomic fraction: "
            f"{format_value(row.get('li_atomic_fraction'), 3)}"
        )

        lines.append(
            f"- Minimum Li-Li distance: "
            f"{format_value(row.get('min_li_li_distance'), 3)} Å"
        )

        lines.append(
            f"- Mean nearest Li-Li distance: "
            f"{format_value(row.get('mean_li_li_distance'), 3)} Å"
        )

        lines.append(
            f"- Mean Li local neighbor count: "
            f"{format_value(row.get('mean_li_neighbor_count'), 2)}"
        )

        lines.append(
            f"- Volume per atom: "
            f"{format_value(row.get('volume_per_atom'), 3)} Å³"
        )

        positives = row.get(
            "structural_positives"
        )

        concerns = row.get(
            "structural_concerns"
        )

        if (
            positives is not None
            and not pd.isna(positives)
            and str(positives).strip()
        ):
            lines.append("")
            lines.append("**Positive indicators**")
            lines.append("")

            for item in str(positives).split(" | "):
                lines.append(
                    f"- {item}"
                )

        if (
            concerns is not None
            and not pd.isna(concerns)
            and str(concerns).strip()
        ):
            lines.append("")
            lines.append("**Structural concerns**")
            lines.append("")

            for item in str(concerns).split(" | "):
                lines.append(
                    f"- {item}"
                )

        lines.append("")

    # --------------------------------------------------------
    # Interpretation
    # --------------------------------------------------------

    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The structure score is intended as a screening metric rather "
        "than a direct prediction of battery performance."
    )
    lines.append("")
    lines.append(
        "A high structural score indicates that the material combines "
        "several favorable characteristics such as low thermodynamic "
        "instability, meaningful lithium content, reasonable Li-site "
        "spacing, and physically plausible atomic packing."
    )
    lines.append("")
    lines.append(
        "Lithium diffusion cannot be established from these descriptors "
        "alone. Reliable transport predictions would require methods such "
        "as migration-path analysis, nudged elastic band calculations, "
        "molecular dynamics, or experimentally measured ionic conductivity."
    )
    lines.append("")

    lines.append("## Next Stage")
    lines.append("")
    lines.append(
        "The next Week 7 stage will analyze oxidation states and "
        "transition-metal redox chemistry to determine whether each "
        "candidate contains a chemically plausible charge-storage "
        "mechanism."
    )
    lines.append("")

    REPORT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """
    Run the complete Week 7 structural analysis.
    """

    print()
    print("=" * 70)
    print("MAPPS-LITE WEEK 7")
    print("CANDIDATE CRYSTAL STRUCTURE ANALYSIS")
    print("=" * 70)

    print()
    print("[1/5] Loading Week 6 final ranking...")

    candidates = load_week6_candidates()

    print(
        f"Selected {len(candidates)} "
        f"top Week 6 candidates."
    )

    print()
    print("Candidates:")

    for _, row in candidates.iterrows():

        formula_column = find_column(
            candidates,
            [
                "formula",
                "formula_pretty",
                "mp_formula",
            ],
        )

        formula = (
            row.get(formula_column)
            if formula_column is not None
            else "Unknown formula"
        )

        print(
            f"  #{row['week7_input_rank']}: "
            f"{row['material_id']} "
            f"{formula}"
        )

    print()
    print("[2/5] Retrieving Materials Project structures...")

    document_map = retrieve_mp_documents(
        candidates["material_id"].tolist()
    )

    print()
    print("[3/5] Calculating structural descriptors...")

    results: list[dict[str, Any]] = []

    total = len(candidates)

    for index, (_, candidate) in enumerate(
        candidates.iterrows(),
        start=1,
    ):

        material_id = candidate["material_id"]

        print(
            f"  [{index}/{total}] "
            f"Analyzing {material_id}..."
        )

        document = document_map.get(
            material_id
        )

        result = analyze_candidate(
            candidate,
            document,
        )

        results.append(result)

    output_dataframe = pd.DataFrame(
        results
    )

    output_dataframe = output_dataframe.sort_values(
        [
            "structure_score",
            "week7_input_rank",
        ],
        ascending=[
            False,
            True,
        ],
    )

    output_dataframe.insert(
        0,
        "structure_rank",
        range(
            1,
            len(output_dataframe) + 1,
        ),
    )

    print()
    print("[4/5] Saving structural dataset...")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print()
    print("[5/5] Generating structure report...")

    generate_report(
        output_dataframe
    )

    print(
        f"Saved: {REPORT_FILE}"
    )

    print()
    print("=" * 70)
    print("WEEK 7 STRUCTURE ANALYSIS COMPLETE")
    print("=" * 70)

    print()
    print("Top structural candidates:")
    print()

    preview_columns = [
        "structure_rank",
        "material_id",
        "mp_formula",
        "structure_score",
        "structure_rating",
        "crystal_system",
        "framework_family",
    ]

    available_preview_columns = [
        column
        for column in preview_columns
        if column in output_dataframe.columns
    ]

    print(
        output_dataframe[
            available_preview_columns
        ]
        .head(10)
        .to_string(index=False)
    )

    print()
    print(
        "NOTE: Structural scores are screening metrics, "
        "not direct predictions of ionic conductivity "
        "or battery performance."
    )
    print()


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)
        print(exc)
        print()

        sys.exit(1)