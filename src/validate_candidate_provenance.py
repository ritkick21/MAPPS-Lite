import os
import re
from pathlib import Path

import pandas as pd
from mp_api.client import MPRester


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "week5_shortlist.csv"

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_provenance_validation.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week6_provenance_validation.md"
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def find_column(df, possible_names):
    """
    Find the first matching column from a list of possible names.
    """

    for name in possible_names:
        if name in df.columns:
            return name

    return None


def extract_icsd_ids(database_ids):
    """
    Extract ICSD identifiers from Materials Project database_IDs.
    """

    if not isinstance(database_ids, dict):
        return []

    ids = database_ids.get("icsd", [])

    if ids is None:
        return []

    if isinstance(ids, (str, int)):
        ids = [ids]

    return [str(x) for x in ids]


def extract_dois(references):
    """
    Extract DOI strings from BibTeX/reference text.
    """

    if not references:
        return []

    doi_pattern = re.compile(
        r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+",
        flags=re.IGNORECASE,
    )

    dois = set()

    for reference in references:
        if not isinstance(reference, str):
            continue

        matches = doi_pattern.findall(reference)

        for doi in matches:
            doi = doi.rstrip(".,;)}]")
            dois.add(doi.lower())

    return sorted(dois)


def calculate_evidence_score(
    theoretical,
    icsd_count,
    reference_count,
    doi_count,
):
    """
    Produce a provenance/evidence score from 0 to 100.

    IMPORTANT:
    This measures evidence that the STRUCTURE is documented.
    It does NOT measure whether the material is a good cathode.
    """

    score = 0.0

    # Experimental flag from Materials Project
    if theoretical is False:
        score += 55

    # ICSD provides strong crystallographic evidence
    if icsd_count > 0:
        score += 20

    # Literature references
    score += min(reference_count * 4, 20)

    # Explicit DOI evidence
    score += min(doi_count * 2, 5)

    return round(min(score, 100), 1)


def classify_evidence(
    theoretical,
    icsd_count,
    reference_count,
):
    """
    Describe what kind of provenance evidence exists.
    """

    if theoretical is False or icsd_count > 0:
        return "EXPERIMENTAL_STRUCTURE_EVIDENCE"

    if theoretical is True and reference_count > 0:
        return "COMPUTATIONAL_WITH_REFERENCES"

    if theoretical is True and reference_count == 0:
        return "COMPUTATIONAL_ONLY"

    if reference_count > 0:
        return "REFERENCED_PROVENANCE"

    return "LIMITED_PROVENANCE"


def classify_strength(score):
    """
    Convert provenance score into a simple evidence-strength label.
    """

    if score >= 75:
        return "STRONG"

    if score >= 45:
        return "MODERATE"

    return "LIMITED"


# ---------------------------------------------------------
# Materials Project query
# ---------------------------------------------------------

def query_candidate(mpr, material_id):
    """
    Query Materials Project provenance information for one material.
    """

    result = {
        "mp_formula": None,
        "theoretical": None,
        "icsd_ids": [],
        "reference_count": 0,
        "dois": [],
        "query_status": "SUCCESS",
        "query_error": "",
    }

    try:
        # -------------------------------------------------
        # Get high-level material metadata
        # -------------------------------------------------

        try:
            docs = mpr.materials.summary.search(
                material_ids=[material_id],
                fields=[
                    "material_id",
                    "formula_pretty",
                    "theoretical",
                    "database_IDs",
                ],
            )

        except Exception:
            # Fallback in case database_IDs is unavailable
            # in a particular API/schema version.
            docs = mpr.materials.summary.search(
                material_ids=[material_id],
                fields=[
                    "material_id",
                    "formula_pretty",
                    "theoretical",
                ],
            )

        if docs:
            doc = docs[0]

            result["mp_formula"] = doc.get("formula_pretty")
            result["theoretical"] = doc.get("theoretical")

            database_ids = doc.get("database_IDs", {})
            result["icsd_ids"] = extract_icsd_ids(database_ids)

        else:
            result["query_status"] = "NO_SUMMARY_DOCUMENT"

        # -------------------------------------------------
        # Get references attached to the material
        # -------------------------------------------------

        references = mpr.get_material_id_references(material_id)

        if references is None:
            references = []

        result["reference_count"] = len(references)
        result["dois"] = extract_dois(references)

    except Exception as exc:
        result["query_status"] = "QUERY_ERROR"
        result["query_error"] = str(exc)

    return result


# ---------------------------------------------------------
# Report generation
# ---------------------------------------------------------

def write_report(df):
    """
    Write a human-readable Markdown summary.
    """

    successful = df[
        df["provenance_query_status"] == "SUCCESS"
    ]

    experimental = df[
        df["provenance_class"]
        == "EXPERIMENTAL_STRUCTURE_EVIDENCE"
    ]

    computational_refs = df[
        df["provenance_class"]
        == "COMPUTATIONAL_WITH_REFERENCES"
    ]

    computational_only = df[
        df["provenance_class"]
        == "COMPUTATIONAL_ONLY"
    ]

    strong = df[
        df["provenance_strength"] == "STRONG"
    ]

    moderate = df[
        df["provenance_strength"] == "MODERATE"
    ]

    limited = df[
        df["provenance_strength"] == "LIMITED"
    ]

    lines = []

    lines.append("# MAPPS-Lite Week 6 Provenance Validation")
    lines.append("")
    lines.append(
        "This analysis evaluates the provenance and structural "
        "evidence associated with the Week 5 candidate shortlist."
    )
    lines.append("")
    lines.append(
        "**Important:** provenance evidence is not the same as "
        "evidence that a material functions as a cathode."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Candidates evaluated: {len(df)}")
    lines.append(f"- Successful API queries: {len(successful)}")
    lines.append(
        "- Experimental-structure evidence: "
        f"{len(experimental)}"
    )
    lines.append(
        "- Computational structures with references: "
        f"{len(computational_refs)}"
    )
    lines.append(
        "- Computational-only structures: "
        f"{len(computational_only)}"
    )
    lines.append("")
    lines.append("### Provenance strength")
    lines.append("")
    lines.append(f"- STRONG: {len(strong)}")
    lines.append(f"- MODERATE: {len(moderate)}")
    lines.append(f"- LIMITED: {len(limited)}")
    lines.append("")
    lines.append("## Candidate Results")
    lines.append("")

    sorted_df = df.sort_values(
        "provenance_evidence_score",
        ascending=False,
    )

    for _, row in sorted_df.iterrows():

        material_id = row["material_id"]

        formula = row.get(
            "week6_formula",
            row.get("formula", ""),
        )

        score = row["provenance_evidence_score"]

        classification = row["provenance_class"]

        strength = row["provenance_strength"]

        references = row["mp_reference_count"]

        icsd_count = row["icsd_count"]

        lines.append(
            f"### {material_id} | {formula}"
        )
        lines.append("")
        lines.append(f"- Evidence score: {score}")
        lines.append(f"- Evidence strength: {strength}")
        lines.append(f"- Classification: {classification}")
        lines.append(f"- MP references: {references}")
        lines.append(f"- ICSD records: {icsd_count}")
        lines.append("")

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("MAPPS-LITE WEEK 6")
    print("STAGE 6.1 - CANDIDATE PROVENANCE VALIDATION")
    print("=" * 70)

    # -----------------------------------------------------
    # Check input
    # -----------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find Week 5 shortlist:\n{INPUT_FILE}"
        )

    shortlist = pd.read_csv(INPUT_FILE)

    print()
    print(f"Loaded {len(shortlist)} candidates.")
    print(f"Input: {INPUT_FILE}")

    # -----------------------------------------------------
    # Detect important columns
    # -----------------------------------------------------

    material_id_column = find_column(
        shortlist,
        [
            "material_id",
            "mp_id",
            "material_id_candidate",
            "candidate_material_id",
        ],
    )

    formula_column = find_column(
        shortlist,
        [
            "formula",
            "formula_pretty",
            "pretty_formula",
            "candidate_formula",
        ],
    )

    if material_id_column is None:
        raise ValueError(
            "Could not identify a Materials Project ID column.\n"
            f"Available columns: {list(shortlist.columns)}"
        )

    print()
    print(
        f"Using material ID column: "
        f"{material_id_column}"
    )

    if formula_column:
        print(
            f"Using formula column: {formula_column}"
        )
    else:
        print(
            "No formula column detected. "
            "Materials Project formulas will be used."
        )

    # -----------------------------------------------------
    # API key
    # -----------------------------------------------------

    api_key = os.getenv("MP_API_KEY")

    if not api_key:
        raise RuntimeError(
            "MP_API_KEY is not set.\n\n"
            "In Command Prompt run:\n"
            "set MP_API_KEY=YOUR_API_KEY\n\n"
            "Then rerun this script."
        )

    # -----------------------------------------------------
    # Query Materials Project
    # -----------------------------------------------------

    records = []

    with MPRester(
        api_key,
        use_document_model=False,
        mute_progress_bars=True,
    ) as mpr:

        total = len(shortlist)

        for number, (_, row) in enumerate(
            shortlist.iterrows(),
            start=1,
        ):

            material_id = str(
                row[material_id_column]
            ).strip()

            print(
                f"[{number}/{total}] "
                f"Checking {material_id}..."
            )

            query = query_candidate(
                mpr,
                material_id,
            )

            theoretical = query["theoretical"]

            icsd_ids = query["icsd_ids"]
            reference_count = query["reference_count"]
            dois = query["dois"]

            score = calculate_evidence_score(
                theoretical=theoretical,
                icsd_count=len(icsd_ids),
                reference_count=reference_count,
                doi_count=len(dois),
            )

            provenance_class = classify_evidence(
                theoretical=theoretical,
                icsd_count=len(icsd_ids),
                reference_count=reference_count,
            )

            strength = classify_strength(score)

            if formula_column:
                original_formula = row[formula_column]
            else:
                original_formula = None

            record = row.to_dict()

            # Normalize the MP ID so Week 6 always
            # has a predictable column name.
            record["material_id"] = material_id

            record["week6_formula"] = (
                original_formula
                if pd.notna(original_formula)
                else query["mp_formula"]
            )

            record["mp_formula"] = query["mp_formula"]

            record["mp_theoretical"] = theoretical

            record["icsd_count"] = len(icsd_ids)

            record["icsd_ids"] = (
                ";".join(icsd_ids)
                if icsd_ids
                else ""
            )

            record["mp_reference_count"] = (
                reference_count
            )

            record["doi_count"] = len(dois)

            record["dois"] = (
                ";".join(dois)
                if dois
                else ""
            )

            record["provenance_class"] = (
                provenance_class
            )

            record["provenance_strength"] = strength

            record[
                "provenance_evidence_score"
            ] = score

            record[
                "provenance_query_status"
            ] = query["query_status"]

            record[
                "provenance_query_error"
            ] = query["query_error"]

            records.append(record)

    # -----------------------------------------------------
    # Save results
    # -----------------------------------------------------

    output_df = pd.DataFrame(records)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    write_report(output_df)

    # -----------------------------------------------------
    # Console summary
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("PROVENANCE VALIDATION COMPLETE")
    print("=" * 70)

    print()
    print(
        output_df["provenance_class"]
        .value_counts()
        .to_string()
    )

    print()
    print("Evidence strength:")

    print(
        output_df["provenance_strength"]
        .value_counts()
        .to_string()
    )

    print()
    print("Top provenance-supported candidates:")
    print()

    display_columns = [
        "material_id",
        "week6_formula",
        "provenance_evidence_score",
        "provenance_strength",
        "provenance_class",
        "icsd_count",
        "mp_reference_count",
    ]

    print(
        output_df[
            display_columns
        ]
        .sort_values(
            "provenance_evidence_score",
            ascending=False,
        )
        .head(15)
        .to_string(index=False)
    )

    print()
    print(f"Saved data to:")
    print(OUTPUT_FILE)

    print()
    print(f"Saved report to:")
    print(REPORT_FILE)


if __name__ == "__main__":
    main()