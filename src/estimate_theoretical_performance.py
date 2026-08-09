"""
MAPPS-Lite Week 7
Theoretical Cathode Performance Estimation

Purpose
-------
Convert Week 7 redox chemistry results into physically interpretable
battery-performance descriptors.

The script:
1. Loads Week 7 redox-analysis results.
2. Calculates formula molar mass.
3. Calculates formal theoretical specific capacity.
4. Calculates a conservative screening capacity.
5. Assigns an approximate voltage class.
6. Estimates gravimetric specific energy.
7. Produces a performance score and confidence level.
8. Generates a CSV dataset and Markdown report.

Input
-----
data/week7_redox_analysis.csv

Outputs
-------
data/week7_theoretical_performance.csv
reports/week7_theoretical_performance.md

Scientific Limitations
----------------------
The capacity calculated from electron count and molar mass is a
stoichiometric upper-bound estimate.

The conservative screening capacity applies utilization assumptions
to avoid treating complete delithiation as automatically reversible.

Voltage values in this script are coarse chemistry-family estimates,
NOT DFT-calculated voltages and NOT experimentally measured voltages.

Therefore estimated specific energy is also a screening-level metric.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from pymatgen.core import Composition


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_redox_analysis.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week7_theoretical_performance.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week7_theoretical_performance.md"
)


# ============================================================
# PHYSICAL CONSTANTS
# ============================================================

# Faraday constant in coulombs per mole of electrons.
FARADAY_CONSTANT = 96485.33212

# Conversion:
#
# 1 Ah = 3600 C
#
# mAh/g = n * F / (3.6 * molar_mass)
#
CAPACITY_CONVERSION = FARADAY_CONSTANT / 3.6


# ============================================================
# CONSERVATIVE UTILIZATION MODEL
# ============================================================

# Formal oxidation-state analysis can allow complete removal of
# several lithium ions even when such deep delithiation would be
# structurally unstable.
#
# The values below intentionally reduce the formal electron inventory
# before estimating screening-level practical capacity.

UTILIZATION_BY_ELECTRON_COUNT = {
    0: 0.00,
    1: 0.90,
    2: 0.80,
    3: 0.70,
    4: 0.60,
    5: 0.55,
}


# ============================================================
# APPROXIMATE VOLTAGE MODEL
# ============================================================

# These are deliberately broad screening estimates.
#
# They represent approximate voltage classes associated with
# transition-metal chemistry and polyanion inductive effects.
#
# They are NOT experimental voltages.

BASE_METAL_VOLTAGES = {
    "Ti": 2.5,
    "V": 3.7,
    "Cr": 4.0,
    "Mn": 4.0,
    "Fe": 3.5,
    "Co": 4.0,
    "Ni": 3.8,
    "Cu": 3.7,
    "Mo": 3.0,
    "W": 3.0,
    "Nb": 2.5,
    "Ta": 2.5,
    "Ru": 3.8,
    "Rh": 3.8,
    "Ir": 3.8,
}


# Framework adjustments capture broad inductive trends.
#
# Fluorinated and phosphate frameworks often push transition-metal
# redox potentials upward relative to simple oxides.

FRAMEWORK_VOLTAGE_ADJUSTMENTS = {
    "PHOSPHATE / OXYPHOSPHATE": 0.15,
    "SILICATE / OXYSILICATE": 0.10,
    "OXYFLUORIDE": 0.30,
    "FLUORIDE": 0.40,
    "SULFATE / OXYSULFATE": 0.30,
    "BORATE / OXYBORATE": 0.10,
    "OXIDE": 0.00,
    "SULFIDE": -0.50,
    "OTHER": 0.00,
}


# ============================================================
# HELPERS
# ============================================================

def safe_float(value: Any) -> float | None:
    """
    Convert a value to a finite float.
    """

    try:
        if value is None:
            return None

        result = float(value)

        if not np.isfinite(result):
            return None

        return result

    except (TypeError, ValueError):
        return None


def format_value(
    value: Any,
    digits: int = 2,
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

    if isinstance(value, (float, np.floating)):
        return f"{value:.{digits}f}"

    return str(value)


def split_metals(value: Any) -> list[str]:
    """
    Convert CSV redox-metal text into a list.
    """

    if value is None:
        return []

    try:
        if pd.isna(value):
            return []
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if not text:
        return []

    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]


# ============================================================
# LOAD DATA
# ============================================================

def load_redox_results() -> pd.DataFrame:
    """
    Load Week 7 redox-analysis results.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "\nCould not find Week 7 redox dataset:\n"
            f"{INPUT_FILE}\n\n"
            "Run src/analyze_redox_chemistry.py first."
        )

    dataframe = pd.read_csv(INPUT_FILE)

    if dataframe.empty:

        raise ValueError(
            "week7_redox_analysis.csv contains no candidates."
        )

    required_columns = [
        "material_id",
        "formula",
        "estimated_extractable_electrons",
        "redox_active_metals",
        "redox_score",
        "structure_score",
    ]

    missing = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing:

        raise ValueError(
            "Required columns are missing from the redox dataset:\n"
            + ", ".join(missing)
        )

    return dataframe.copy()


# ============================================================
# CAPACITY CALCULATIONS
# ============================================================

def calculate_molar_mass(
    formula: str,
) -> float:
    """
    Calculate formula molar mass in g/mol.
    """

    composition = Composition(
        str(formula)
    )

    return float(
        composition.weight
    )


def calculate_theoretical_capacity(
    electrons: float,
    molar_mass: float,
) -> float:
    """
    Calculate theoretical gravimetric capacity.

    Q = nF / (3.6M)

    where:
        n = electrons per formula unit
        F = Faraday constant
        M = molar mass in g/mol

    Result:
        mAh/g
    """

    if (
        electrons <= 0
        or molar_mass <= 0
    ):
        return 0.0

    capacity = (
        electrons
        * CAPACITY_CONVERSION
        / molar_mass
    )

    return round(
        capacity,
        2,
    )


# ============================================================
# CONSERVATIVE ELECTRON UTILIZATION
# ============================================================

def calculate_utilization_fraction(
    electrons: float,
    redox_confidence: str,
) -> float:
    """
    Estimate a conservative fraction of the formal redox inventory.

    This prevents complete multi-electron delithiation from being
    automatically treated as practical.

    Confidence slightly modifies the utilization factor.
    """

    if electrons <= 0:
        return 0.0

    rounded_electrons = int(
        np.floor(
            electrons + 1e-8
        )
    )

    rounded_electrons = max(
        1,
        min(
            5,
            rounded_electrons,
        ),
    )

    utilization = (
        UTILIZATION_BY_ELECTRON_COUNT[
            rounded_electrons
        ]
    )

    confidence = str(
        redox_confidence
    ).upper()

    if confidence == "HIGH":
        multiplier = 1.00

    elif confidence == "MODERATE":
        multiplier = 0.95

    else:
        multiplier = 0.85

    utilization *= multiplier

    return round(
        min(
            utilization,
            0.95,
        ),
        3,
    )


# ============================================================
# APPROXIMATE VOLTAGE
# ============================================================

def estimate_voltage(
    redox_metals: list[str],
    framework_family: str,
    redox_electrons: float,
) -> tuple[float | None, str]:
    """
    Estimate a coarse average cathode voltage class.

    This estimate is intended only for ranking and hypothesis
    generation.

    It should NOT be interpreted as a calculated equilibrium voltage.
    """

    metal_voltages: list[float] = []

    for metal in redox_metals:

        if metal in BASE_METAL_VOLTAGES:

            metal_voltages.append(
                BASE_METAL_VOLTAGES[
                    metal
                ]
            )

    if not metal_voltages:

        return None, "LOW"

    base_voltage = float(
        np.mean(
            metal_voltages
        )
    )

    adjustment = (
        FRAMEWORK_VOLTAGE_ADJUSTMENTS.get(
            str(framework_family),
            0.0,
        )
    )

    voltage = (
        base_voltage
        + adjustment
    )

    # Very high multi-electron extraction typically spans several
    # redox plateaus. We reduce the average estimate slightly rather
    # than assuming every electron operates at the highest voltage.

    if redox_electrons >= 4:
        voltage -= 0.20

    elif redox_electrons >= 3:
        voltage -= 0.10

    voltage = max(
        2.0,
        min(
            5.0,
            voltage,
        ),
    )

    return (
        round(
            voltage,
            2,
        ),
        "LOW",
    )


def classify_voltage(
    voltage: float | None,
) -> str:
    """
    Convert voltage estimate to broad class.
    """

    if voltage is None:
        return "UNKNOWN"

    if voltage >= 4.3:
        return "VERY_HIGH"

    if voltage >= 3.8:
        return "HIGH"

    if voltage >= 3.2:
        return "MODERATE"

    return "LOW"


# ============================================================
# SPECIFIC ENERGY
# ============================================================

def calculate_specific_energy(
    capacity_mAh_g: float,
    voltage: float | None,
) -> float | None:
    """
    Estimate active-material gravimetric specific energy.

    Wh/kg numerically equals:

        mAh/g * V
    """

    if voltage is None:
        return None

    return round(
        capacity_mAh_g
        * voltage,
        1,
    )


# ============================================================
# CAPACITY CLASSIFICATION
# ============================================================

def classify_capacity(
    capacity: float,
) -> str:
    """
    Classify screening capacity.
    """

    if capacity >= 200:
        return "VERY_HIGH"

    if capacity >= 150:
        return "HIGH"

    if capacity >= 100:
        return "MODERATE"

    if capacity >= 50:
        return "LOW"

    return "VERY_LOW"


def classify_energy(
    energy: float | None,
) -> str:
    """
    Classify screening specific energy.
    """

    if energy is None:
        return "UNKNOWN"

    if energy >= 700:
        return "VERY_HIGH"

    if energy >= 550:
        return "HIGH"

    if energy >= 350:
        return "MODERATE"

    if energy >= 200:
        return "LOW"

    return "VERY_LOW"


# ============================================================
# PERFORMANCE NOTES
# ============================================================

def generate_performance_notes(
    *,
    theoretical_capacity: float,
    screening_capacity: float,
    utilization: float,
    voltage: float | None,
    voltage_class: str,
    electrons: float,
) -> tuple[list[str], list[str]]:
    """
    Generate strengths and concerns.
    """

    positives: list[str] = []
    concerns: list[str] = []

    if theoretical_capacity >= 180:

        positives.append(
            "Formal redox inventory supports high theoretical "
            "gravimetric capacity."
        )

    elif theoretical_capacity >= 120:

        positives.append(
            "Formal theoretical capacity is competitive with "
            "many conventional cathode materials."
        )

    elif theoretical_capacity < 80:

        concerns.append(
            "Low theoretical gravimetric capacity limits "
            "energy-density potential."
        )

    if screening_capacity >= 150:

        positives.append(
            "Conservative screening capacity remains high after "
            "applying a utilization penalty."
        )

    elif screening_capacity < 75:

        concerns.append(
            "Conservative capacity estimate is relatively low."
        )

    if electrons >= 3:

        concerns.append(
            "Performance relies on deep multi-electron delithiation; "
            "full reversible extraction should not be assumed."
        )

    if utilization < 0.70 and electrons > 0:

        concerns.append(
            "A substantial utilization penalty was applied because "
            "the formal redox inventory requires deep delithiation."
        )

    if voltage_class in {
        "HIGH",
        "VERY_HIGH",
    }:

        positives.append(
            "Estimated chemistry falls in a high-voltage cathode class."
        )

    if voltage_class == "VERY_HIGH":

        concerns.append(
            "Very high operating voltage could create electrolyte "
            "stability and interfacial compatibility challenges."
        )

    if voltage is None:

        concerns.append(
            "No voltage-class estimate could be assigned from the "
            "identified redox chemistry."
        )

    return positives, concerns


# ============================================================
# PERFORMANCE SCORE
# ============================================================

def calculate_performance_score(
    *,
    screening_capacity: float,
    specific_energy: float | None,
    voltage: float | None,
    redox_score: float,
    structure_score: float,
) -> float:
    """
    Calculate Week 7 theoretical-performance screening score.

    Weighting
    ---------
    Conservative capacity: 35%
    Estimated specific energy: 30%
    Redox chemistry quality: 20%
    Structural quality: 15%
    """

    # --------------------------------------------------------
    # Capacity component
    # --------------------------------------------------------

    capacity_component = min(
        screening_capacity / 200.0,
        1.0,
    ) * 100.0

    # --------------------------------------------------------
    # Energy component
    # --------------------------------------------------------

    if specific_energy is None:
        energy_component = 0.0

    else:
        energy_component = min(
            specific_energy / 750.0,
            1.0,
        ) * 100.0

    # --------------------------------------------------------
    # Existing MAPPS-Lite stages
    # --------------------------------------------------------

    redox_component = max(
        0.0,
        min(
            redox_score,
            100.0,
        ),
    )

    structure_component = max(
        0.0,
        min(
            structure_score,
            100.0,
        ),
    )

    score = (
        0.35 * capacity_component
        + 0.30 * energy_component
        + 0.20 * redox_component
        + 0.15 * structure_component
    )

    # High-voltage penalty for likely electrolyte compatibility risk.
    if (
        voltage is not None
        and voltage >= 4.5
    ):
        score -= 5.0

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


def classify_performance_score(
    score: float,
) -> str:
    """
    Convert score to performance category.
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

def determine_performance_confidence(
    redox_confidence: str,
    electrons: float,
) -> str:
    """
    Estimate confidence in performance screening.

    Voltage remains heuristic, so overall confidence is intentionally
    capped at MODERATE.
    """

    if electrons <= 0:
        return "LOW"

    if str(redox_confidence).upper() == "LOW":
        return "LOW"

    if electrons > 3:
        return "LOW"

    return "MODERATE"


# ============================================================
# CANDIDATE ANALYSIS
# ============================================================

def analyze_candidate(
    row: pd.Series,
) -> dict[str, Any]:
    """
    Analyze theoretical performance for one candidate.
    """

    result = row.to_dict()

    formula = str(
        row["formula"]
    )

    electrons = safe_float(
        row[
            "estimated_extractable_electrons"
        ]
    )

    if electrons is None:
        electrons = 0.0

    redox_score = safe_float(
        row.get(
            "redox_score"
        )
    )

    if redox_score is None:
        redox_score = 0.0

    structure_score = safe_float(
        row.get(
            "structure_score"
        )
    )

    if structure_score is None:
        structure_score = 0.0

    redox_confidence = str(
        row.get(
            "redox_confidence",
            "LOW",
        )
    )

    framework_family = str(
        row.get(
            "framework_family",
            "OTHER",
        )
    )

    redox_metals = split_metals(
        row.get(
            "redox_active_metals"
        )
    )

    # --------------------------------------------------------
    # Molar mass
    # --------------------------------------------------------

    molar_mass = calculate_molar_mass(
        formula
    )

    # --------------------------------------------------------
    # Formal theoretical capacity
    # --------------------------------------------------------

    theoretical_capacity = (
        calculate_theoretical_capacity(
            electrons,
            molar_mass,
        )
    )

    # --------------------------------------------------------
    # Conservative utilization
    # --------------------------------------------------------

    utilization = (
        calculate_utilization_fraction(
            electrons,
            redox_confidence,
        )
    )

    conservative_electrons = round(
        electrons
        * utilization,
        4,
    )

    screening_capacity = (
        calculate_theoretical_capacity(
            conservative_electrons,
            molar_mass,
        )
    )

    # --------------------------------------------------------
    # Voltage
    # --------------------------------------------------------

    estimated_voltage, voltage_confidence = (
        estimate_voltage(
            redox_metals,
            framework_family,
            electrons,
        )
    )

    voltage_class = classify_voltage(
        estimated_voltage
    )

    # --------------------------------------------------------
    # Energy
    # --------------------------------------------------------

    theoretical_energy = (
        calculate_specific_energy(
            theoretical_capacity,
            estimated_voltage,
        )
    )

    screening_energy = (
        calculate_specific_energy(
            screening_capacity,
            estimated_voltage,
        )
    )

    # --------------------------------------------------------
    # Interpretations
    # --------------------------------------------------------

    capacity_class = classify_capacity(
        screening_capacity
    )

    energy_class = classify_energy(
        screening_energy
    )

    positives, concerns = (
        generate_performance_notes(
            theoretical_capacity=
                theoretical_capacity,

            screening_capacity=
                screening_capacity,

            utilization=
                utilization,

            voltage=
                estimated_voltage,

            voltage_class=
                voltage_class,

            electrons=
                electrons,
        )
    )

    # --------------------------------------------------------
    # Performance score
    # --------------------------------------------------------

    performance_score = (
        calculate_performance_score(
            screening_capacity=
                screening_capacity,

            specific_energy=
                screening_energy,

            voltage=
                estimated_voltage,

            redox_score=
                redox_score,

            structure_score=
                structure_score,
        )
    )

    performance_rating = (
        classify_performance_score(
            performance_score
        )
    )

    confidence = (
        determine_performance_confidence(
            redox_confidence,
            electrons,
        )
    )

    result.update(
        {
            "molar_mass_g_mol":
                round(
                    molar_mass,
                    3,
                ),

            "formal_redox_electrons":
                round(
                    electrons,
                    4,
                ),

            "formal_theoretical_capacity_mAh_g":
                theoretical_capacity,

            "utilization_fraction":
                utilization,

            "screening_electrons":
                conservative_electrons,

            "screening_capacity_mAh_g":
                screening_capacity,

            "capacity_class":
                capacity_class,

            "estimated_average_voltage_V":
                estimated_voltage,

            "voltage_class":
                voltage_class,

            "voltage_estimate_confidence":
                voltage_confidence,

            "formal_specific_energy_Wh_kg":
                theoretical_energy,

            "screening_specific_energy_Wh_kg":
                screening_energy,

            "specific_energy_class":
                energy_class,

            "performance_score":
                performance_score,

            "performance_rating":
                performance_rating,

            "performance_confidence":
                confidence,

            "performance_positives":
                " | ".join(
                    positives
                ),

            "performance_concerns":
                " | ".join(
                    concerns
                ),
        }
    )

    return result


# ============================================================
# REPORT
# ============================================================

def generate_report(
    dataframe: pd.DataFrame,
) -> None:
    """
    Generate Week 7 performance report.
    """

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ranked = dataframe.sort_values(
        [
            "performance_score",
            "screening_specific_energy_Wh_kg",
        ],
        ascending=[
            False,
            False,
        ],
    )

    lines: list[str] = []

    lines.append(
        "# MAPPS-Lite Week 7 Theoretical Performance Analysis"
    )

    lines.append("")

    lines.append("## Objective")
    lines.append("")

    lines.append(
        "This stage converts the Week 7 redox analysis into "
        "screening-level battery-performance estimates."
    )

    lines.append("")

    lines.append(
        "Formal theoretical capacity is calculated from the "
        "electron inventory and formula molar mass."
    )

    lines.append("")

    lines.append(
        "A second conservative capacity estimate applies a utilization "
        "penalty to avoid assuming that deep multi-electron "
        "delithiation is automatically reversible."
    )

    lines.append("")

    lines.append(
        "**Voltage values are chemistry-based screening estimates, "
        "not DFT calculations or experimental measurements.**"
    )

    lines.append("")

    # --------------------------------------------------------
    # Equations
    # --------------------------------------------------------

    lines.append("## Capacity Model")
    lines.append("")

    lines.append(
        "The formal gravimetric capacity is calculated as:"
    )

    lines.append("")

    lines.append(
        "**Q = nF / (3.6M)**"
    )

    lines.append("")

    lines.append(
        "where n is the number of electrons transferred per formula "
        "unit, F is the Faraday constant, and M is the molar mass."
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

    rating_counts = (
        dataframe[
            "performance_rating"
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

        count = rating_counts.get(
            rating,
            0,
        )

        if count:

            lines.append(
                f"- {rating}: **{count}**"
            )

    lines.append("")

    # --------------------------------------------------------
    # Ranking
    # --------------------------------------------------------

    lines.append(
        "## Performance Screening Ranking"
    )

    lines.append("")

    lines.append(
        "| Rank | Material | Formula | Formal Capacity | "
        "Screening Capacity | Voltage | Screening Energy | Score |"
    )

    lines.append(
        "|---:|---|---|---:|---:|---:|---:|---:|"
    )

    for rank, (_, row) in enumerate(
        ranked.iterrows(),
        start=1,
    ):

        lines.append(
            f"| {rank} "
            f"| {format_value(row.get('material_id'))} "
            f"| {format_value(row.get('formula'))} "
            f"| {format_value(row.get('formal_theoretical_capacity_mAh_g'), 1)} "
            f"| {format_value(row.get('screening_capacity_mAh_g'), 1)} "
            f"| {format_value(row.get('estimated_average_voltage_V'), 2)} "
            f"| {format_value(row.get('screening_specific_energy_Wh_kg'), 0)} "
            f"| {format_value(row.get('performance_score'), 1)} |"
        )

    lines.append("")

    # --------------------------------------------------------
    # Candidate details
    # --------------------------------------------------------

    lines.append("## Candidate Details")
    lines.append("")

    for rank, (_, row) in enumerate(
        ranked.iterrows(),
        start=1,
    ):

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
            f"### {rank}. {formula} ({material_id})"
        )

        lines.append("")

        lines.append(
            f"- Formal redox inventory: "
            f"{format_value(row.get('formal_redox_electrons'), 2)} e⁻/formula"
        )

        lines.append(
            f"- Molar mass: "
            f"{format_value(row.get('molar_mass_g_mol'), 2)} g/mol"
        )

        lines.append(
            f"- Formal theoretical capacity: "
            f"**{format_value(row.get('formal_theoretical_capacity_mAh_g'), 1)} "
            f"mAh/g**"
        )

        lines.append(
            f"- Utilization fraction: "
            f"{format_value(row.get('utilization_fraction'), 2)}"
        )

        lines.append(
            f"- Conservative screening capacity: "
            f"**{format_value(row.get('screening_capacity_mAh_g'), 1)} "
            f"mAh/g**"
        )

        lines.append(
            f"- Capacity class: "
            f"{format_value(row.get('capacity_class'))}"
        )

        lines.append(
            f"- Estimated voltage class: "
            f"{format_value(row.get('estimated_average_voltage_V'), 2)} V "
            f"({format_value(row.get('voltage_class'))})"
        )

        lines.append(
            f"- Screening specific energy: "
            f"**{format_value(row.get('screening_specific_energy_Wh_kg'), 0)} "
            f"Wh/kg**"
        )

        lines.append(
            f"- Performance score: "
            f"**{format_value(row.get('performance_score'), 1)}/100**"
        )

        lines.append(
            f"- Performance rating: "
            f"**{format_value(row.get('performance_rating'))}**"
        )

        lines.append(
            f"- Confidence: "
            f"**{format_value(row.get('performance_confidence'))}**"
        )

        positives = row.get(
            "performance_positives"
        )

        if (
            positives is not None
            and not pd.isna(positives)
            and str(positives).strip()
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

        concerns = row.get(
            "performance_concerns"
        )

        if (
            concerns is not None
            and not pd.isna(concerns)
            and str(concerns).strip()
        ):

            lines.append("")
            lines.append(
                "**Performance concerns**"
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

    # --------------------------------------------------------
    # Interpretation
    # --------------------------------------------------------

    lines.append("## Interpretation")
    lines.append("")

    lines.append(
        "The formal theoretical capacity represents the maximum "
        "capacity implied by the selected oxidation-state model."
    )

    lines.append("")

    lines.append(
        "The screening capacity is intentionally more conservative. "
        "Materials requiring extraction of several lithium ions per "
        "formula unit receive progressively larger utilization penalties."
    )

    lines.append("")

    lines.append(
        "Specific-energy estimates combine that conservative capacity "
        "with a chemistry-based approximate voltage. They should only "
        "be used for relative screening within MAPPS-Lite."
    )

    lines.append("")

    lines.append(
        "Reliable voltage predictions would require electrochemical "
        "measurements or first-principles calculations of the energies "
        "of multiple lithiated and delithiated phases."
    )

    lines.append("")

    lines.append("## Next Stage")
    lines.append("")

    lines.append(
        "The next Week 7 stage will explicitly assess failure modes "
        "and candidate risks, including deep-delithiation dependence, "
        "high-voltage electrolyte compatibility, resource concerns, "
        "structural uncertainty, redox uncertainty, and evidence gaps."
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
    Run Week 7 theoretical-performance estimation.
    """

    print()
    print("=" * 74)
    print("MAPPS-LITE WEEK 7")
    print("THEORETICAL CATHODE PERFORMANCE ESTIMATION")
    print("=" * 74)

    # --------------------------------------------------------
    # Stage 1
    # --------------------------------------------------------

    print()
    print(
        "[1/4] Loading Week 7 redox results..."
    )

    candidates = load_redox_results()

    print(
        f"Loaded {len(candidates)} candidates."
    )

    # --------------------------------------------------------
    # Stage 2
    # --------------------------------------------------------

    print()
    print(
        "[2/4] Calculating capacity, voltage, and energy estimates..."
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
                    "molar_mass_g_mol": None,
                    "formal_redox_electrons": 0.0,
                    "formal_theoretical_capacity_mAh_g": 0.0,
                    "utilization_fraction": 0.0,
                    "screening_electrons": 0.0,
                    "screening_capacity_mAh_g": 0.0,
                    "capacity_class": "UNKNOWN",
                    "estimated_average_voltage_V": None,
                    "voltage_class": "UNKNOWN",
                    "voltage_estimate_confidence": "LOW",
                    "formal_specific_energy_Wh_kg": None,
                    "screening_specific_energy_Wh_kg": None,
                    "specific_energy_class": "UNKNOWN",
                    "performance_score": 0.0,
                    "performance_rating": "WEAK",
                    "performance_confidence": "LOW",
                    "performance_positives": "",
                    "performance_concerns":
                        f"Performance analysis failed: {exc}",
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
            "performance_score",
            "redox_score",
            "structure_score",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).reset_index(
        drop=True
    )

    dataframe.insert(
        0,
        "performance_rank",
        range(
            1,
            len(dataframe) + 1,
        ),
    )

    # --------------------------------------------------------
    # Stage 3
    # --------------------------------------------------------

    print()
    print(
        "[3/4] Saving theoretical-performance dataset..."
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
        "[4/4] Generating performance report..."
    )

    generate_report(
        dataframe
    )

    print(
        f"Saved: {REPORT_FILE}"
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 74)
    print(
        "WEEK 7 THEORETICAL PERFORMANCE ANALYSIS COMPLETE"
    )
    print("=" * 74)

    print()
    print(
        "Top performance candidates:"
    )
    print()

    preview_columns = [
        "performance_rank",
        "material_id",
        "formula",
        "formal_redox_electrons",
        "formal_theoretical_capacity_mAh_g",
        "screening_capacity_mAh_g",
        "estimated_average_voltage_V",
        "screening_specific_energy_Wh_kg",
        "performance_score",
        "performance_rating",
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

    print()
    print(
        "NOTE: Capacity is stoichiometric; voltage is heuristic."
    )

    print(
        "These results are screening estimates, not measured "
        "electrochemical performance."
    )

    print()


if __name__ == "__main__":

    try:

        main()

    except Exception as exc:

        print()
        print("=" * 74)
        print("ERROR")
        print("=" * 74)
        print(exc)
        print()

        sys.exit(1)