import html
import math
import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_provenance_validation.csv"
)

SUMMARY_OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_literature_validation.csv"
)

HITS_OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "week6_literature_hits.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "week6_literature_validation.md"
)


# =========================================================
# CROSSREF SETTINGS
# =========================================================

CROSSREF_URL = "https://api.crossref.org/works"

RESULTS_PER_QUERY = 25

REQUEST_DELAY = 0.25


# =========================================================
# KEYWORDS
# =========================================================

CATHODE_KEYWORDS = [
    "cathode",
    "cathode material",
    "cathode materials",
    "positive electrode",
    "positive-electrode",
    "positive electrode material",
]

BATTERY_KEYWORDS = [
    "battery",
    "batteries",
    "lithium ion",
    "lithium-ion",
    "li ion",
    "li-ion",
    "electrochemical",
    "electrochemistry",
    "intercalation",
    "deintercalation",
    "lithiation",
    "delithiation",
    "charge discharge",
    "charge-discharge",
    "charge/discharge",
    "specific capacity",
    "rechargeable lithium",
    "energy storage",
]

SUBSCRIPT_TRANSLATION = str.maketrans(
    "₀₁₂₃₄₅₆₇₈₉",
    "0123456789",
)


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(value):
    """
    Convert Crossref text into normalized plain text.
    """

    if value is None:
        return ""

    value = str(value)

    value = html.unescape(value)

    # Remove HTML tags such as <sub>
    value = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    # Convert Unicode subscripts to normal numbers
    value = value.translate(
        SUBSCRIPT_TRANSLATION
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def compact_chemical_text(value):
    """
    Normalize chemical formulas for comparison.

    Example:

    Li3V2(PO4)3
          ->
    li3v2po43
    """

    value = clean_text(value).lower()

    return re.sub(
        r"[^a-z0-9]",
        "",
        value,
    )


def formula_in_text(formula, text):
    """
    Check whether the exact candidate formula appears
    somewhere in article metadata.

    This is intentionally conservative.
    """

    formula_normalized = compact_chemical_text(
        formula
    )

    text_normalized = compact_chemical_text(
        text
    )

    if len(formula_normalized) < 4:
        return False

    return (
        formula_normalized
        in text_normalized
    )


def contains_keyword(text, keywords):
    """
    Check whether text contains any keyword.
    """

    text = clean_text(text).lower()

    return any(
        keyword in text
        for keyword in keywords
    )


# =========================================================
# CROSSREF HELPERS
# =========================================================

def extract_title(item):
    titles = item.get("title", [])

    if not titles:
        return ""

    return clean_text(titles[0])


def extract_abstract(item):
    return clean_text(
        item.get("abstract", "")
    )


def extract_journal(item):
    containers = item.get(
        "container-title",
        [],
    )

    if not containers:
        return ""

    return clean_text(containers[0])


def extract_year(item):
    """
    Try several Crossref date fields.
    """

    date_fields = [
        "published-print",
        "published-online",
        "published",
        "issued",
        "created",
    ]

    for field in date_fields:

        value = item.get(field)

        if not isinstance(value, dict):
            continue

        date_parts = value.get(
            "date-parts",
            [],
        )

        if (
            date_parts
            and date_parts[0]
            and date_parts[0][0]
        ):
            try:
                return int(
                    date_parts[0][0]
                )
            except Exception:
                pass

    return None


def crossref_search(query):
    """
    Search Crossref for scholarly works.

    CROSSREF_MAILTO is optional.
    """

    parameters = {
        "query.bibliographic": query,
        "rows": RESULTS_PER_QUERY,
    }

    mailto = os.getenv(
        "CROSSREF_MAILTO"
    )

    if mailto:
        parameters["mailto"] = mailto

    url = (
        CROSSREF_URL
        + "?"
        + urlencode(parameters)
    )

    user_agent = "MAPPS-Lite/1.0"

    if mailto:
        user_agent += f" (mailto:{mailto})"

    request = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
    )

    try:

        with urlopen(
            request,
            timeout=30,
        ) as response:

            data = response.read()

        import json

        payload = json.loads(
            data.decode("utf-8")
        )

        return (
            payload
            .get("message", {})
            .get("items", [])
        ), ""

    except HTTPError as exc:
        return [], (
            f"HTTP {exc.code}: "
            f"{exc.reason}"
        )

    except URLError as exc:
        return [], (
            f"URL error: "
            f"{exc.reason}"
        )

    except Exception as exc:
        return [], str(exc)


# =========================================================
# PAPER CLASSIFICATION
# =========================================================

def classify_paper(
    formula,
    title,
    abstract,
):
    """
    Determine what kind of literature evidence
    a paper provides.

    We require the chemical formula to actually
    appear in the title or abstract.
    """

    title_match = formula_in_text(
        formula,
        title,
    )

    abstract_match = formula_in_text(
        formula,
        abstract,
    )

    exact_formula_match = (
        title_match
        or abstract_match
    )

    if not exact_formula_match:
        return None

    combined_text = (
        title
        + " "
        + abstract
    )

    cathode_related = contains_keyword(
        combined_text,
        CATHODE_KEYWORDS,
    )

    battery_related = contains_keyword(
        combined_text,
        BATTERY_KEYWORDS,
    )

    if cathode_related:
        return "DIRECT_CATHODE"

    if battery_related:
        return "BATTERY_RELATED"

    return "CHEMISTRY_ONLY"


def paper_priority(
    classification,
):
    """
    Used to determine the most relevant article.
    """

    priorities = {
        "DIRECT_CATHODE": 3,
        "BATTERY_RELATED": 2,
        "CHEMISTRY_ONLY": 1,
    }

    return priorities.get(
        classification,
        0,
    )


# =========================================================
# CANDIDATE CLASSIFICATION
# =========================================================

def calculate_literature_score(
    direct_count,
    battery_count,
    chemistry_count,
    citation_count,
):
    """
    Literature evidence score from 0-100.

    IMPORTANT:
    High score means strong published evidence.

    It does NOT necessarily mean the material is
    more scientifically interesting.
    """

    score = 0.0

    score += min(
        direct_count * 20,
        60,
    )

    score += min(
        battery_count * 10,
        20,
    )

    score += min(
        chemistry_count * 2,
        10,
    )

    if citation_count > 0:

        citation_score = (
            math.log10(
                citation_count + 1
            )
            * 5
        )

        score += min(
            citation_score,
            10,
        )

    return round(
        min(score, 100),
        1,
    )


def classify_candidate(
    direct_count,
    battery_count,
    chemistry_count,
):
    """
    Describe the strongest literature evidence found.
    """

    if direct_count >= 3:
        return (
            "ESTABLISHED_CATHODE_EVIDENCE"
        )

    if direct_count >= 1:
        return (
            "DIRECT_CATHODE_EVIDENCE"
        )

    if battery_count >= 1:
        return (
            "BATTERY_RELATED_EVIDENCE"
        )

    if chemistry_count >= 1:
        return (
            "CHEMISTRY_ONLY_EVIDENCE"
        )

    return "NO_EXACT_MATCH_FOUND"


def classify_novelty_signal(
    direct_count,
    battery_count,
    chemistry_count,
):
    """
    Produce a conservative novelty / exploration signal.

    This does NOT claim true scientific novelty.

    It only describes what this automated
    literature search found.
    """

    if direct_count >= 3:
        return (
            "WELL_STUDIED_CATHODE"
        )

    if direct_count >= 1:
        return (
            "LIMITED_CATHODE_LITERATURE"
        )

    if battery_count >= 1:
        return (
            "BATTERY_STUDIED_NO_DIRECT_CATHODE_SIGNAL"
        )

    if chemistry_count >= 1:
        return (
            "UNDEREXPLORED_CATHODE_SIGNAL"
        )

    return (
        "INCONCLUSIVE_NO_EXACT_MATCH"
    )


# =========================================================
# SEARCH ONE MATERIAL
# =========================================================

def search_material_literature(
    material_id,
    formula,
):
    """
    Search several query variants for one candidate.
    """

    queries = [
        formula,
        f"{formula} cathode battery",
        (
            f"{formula} lithium ion "
            f"electrochemical"
        ),
    ]

    unique_papers = {}

    raw_results_seen = 0
    errors = []

    for query in queries:

        results, error = (
            crossref_search(query)
        )

        if error:
            errors.append(
                f"{query}: {error}"
            )

        raw_results_seen += len(
            results
        )

        for item in results:

            title = extract_title(
                item
            )

            abstract = extract_abstract(
                item
            )

            classification = (
                classify_paper(
                    formula,
                    title,
                    abstract,
                )
            )

            # Ignore fuzzy Crossref results
            # where the exact candidate formula
            # does not appear.
            if classification is None:
                continue

            doi = clean_text(
                item.get("DOI", "")
            ).lower()

            journal = extract_journal(
                item
            )

            year = extract_year(
                item
            )

            citations = (
                item.get(
                    "is-referenced-by-count",
                    0,
                )
                or 0
            )

            url = clean_text(
                item.get("URL", "")
            )

            if doi:
                unique_key = (
                    "doi:"
                    + doi
                )

            else:
                unique_key = (
                    "title:"
                    + compact_chemical_text(
                        title
                    )
                )

            paper_record = {
                "material_id": material_id,
                "formula": formula,
                "literature_class": (
                    classification
                ),
                "title": title,
                "year": year,
                "journal": journal,
                "doi": doi,
                "citation_count": citations,
                "url": url,
            }

            existing = (
                unique_papers.get(
                    unique_key
                )
            )

            if existing is None:

                unique_papers[
                    unique_key
                ] = paper_record

            else:

                old_priority = (
                    paper_priority(
                        existing[
                            "literature_class"
                        ]
                    )
                )

                new_priority = (
                    paper_priority(
                        classification
                    )
                )

                if (
                    new_priority
                    > old_priority
                ):
                    unique_papers[
                        unique_key
                    ] = paper_record

        time.sleep(
            REQUEST_DELAY
        )

    papers = list(
        unique_papers.values()
    )

    return {
        "papers": papers,
        "raw_results_seen": (
            raw_results_seen
        ),
        "errors": errors,
    }


# =========================================================
# MARKDOWN REPORT
# =========================================================

def write_report(
    summary_df,
    hits_df,
):
    lines = []

    lines.append(
        "# MAPPS-Lite Week 6 "
        "Battery Literature Validation"
    )

    lines.append("")

    lines.append(
        "This stage searches scholarly "
        "metadata for evidence that each "
        "candidate has previously been "
        "investigated as a cathode, battery "
        "material, or chemical compound."
    )

    lines.append("")

    lines.append(
        "**Important:** absence of a match "
        "does not prove scientific novelty. "
        "The result is a literature-search "
        "signal that must later be manually "
        "validated."
    )

    lines.append("")

    lines.append("## Summary")
    lines.append("")

    lines.append(
        f"- Candidates evaluated: "
        f"{len(summary_df)}"
    )

    classification_counts = (
        summary_df[
            "battery_literature_class"
        ]
        .value_counts()
    )

    for classification, count in (
        classification_counts.items()
    ):

        lines.append(
            f"- {classification}: {count}"
        )

    lines.append("")
    lines.append(
        "## Novelty / Exploration Signals"
    )
    lines.append("")

    novelty_counts = (
        summary_df[
            "literature_novelty_signal"
        ]
        .value_counts()
    )

    for classification, count in (
        novelty_counts.items()
    ):

        lines.append(
            f"- {classification}: {count}"
        )

    lines.append("")
    lines.append(
        "## Candidate Results"
    )
    lines.append("")

    sorted_df = summary_df.sort_values(
        [
            "direct_cathode_papers",
            "battery_related_papers",
            "literature_evidence_score",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    )

    for _, row in (
        sorted_df.iterrows()
    ):

        lines.append(
            f"### {row['material_id']} | "
            f"{row['week6_formula']}"
        )

        lines.append("")

        lines.append(
            "- Literature class: "
            f"{row['battery_literature_class']}"
        )

        lines.append(
            "- Novelty signal: "
            f"{row['literature_novelty_signal']}"
        )

        lines.append(
            "- Direct cathode papers: "
            f"{row['direct_cathode_papers']}"
        )

        lines.append(
            "- Battery-related papers: "
            f"{row['battery_related_papers']}"
        )

        lines.append(
            "- Chemistry-only papers: "
            f"{row['chemistry_only_papers']}"
        )

        lines.append(
            "- Literature evidence score: "
            f"{row['literature_evidence_score']}"
        )

        best_title = row.get(
            "best_literature_title",
            "",
        )

        if (
            isinstance(best_title, str)
            and best_title
        ):
            lines.append(
                "- Best matching paper: "
                f"{best_title}"
            )

        lines.append("")

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 72)
    print("MAPPS-LITE WEEK 6")
    print(
        "STAGE 6.2 - "
        "BATTERY LITERATURE VALIDATION"
    )
    print("=" * 72)

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "Could not find Stage 6.1 output:\n"
            f"{INPUT_FILE}"
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

    if "material_id" not in df.columns:

        raise ValueError(
            "material_id column not found."
        )

    formula_column = None

    for candidate in [
        "week6_formula",
        "formula",
        "mp_formula",
    ]:

        if candidate in df.columns:
            formula_column = candidate
            break

    if formula_column is None:

        raise ValueError(
            "Could not identify formula column."
        )

    print()
    print(
        f"Using formula column: "
        f"{formula_column}"
    )

    print()
    print(
        "Searching Crossref literature..."
    )
    print()

    summary_records = []
    all_hit_records = []

    total = len(df)

    for number, (_, row) in enumerate(
        df.iterrows(),
        start=1,
    ):

        material_id = str(
            row["material_id"]
        ).strip()

        formula = str(
            row[formula_column]
        ).strip()

        print(
            f"[{number}/{total}] "
            f"{material_id} | "
            f"{formula}"
        )

        result = (
            search_material_literature(
                material_id,
                formula,
            )
        )

        papers = result[
            "papers"
        ]

        all_hit_records.extend(
            papers
        )

        direct = [
            paper
            for paper in papers
            if paper[
                "literature_class"
            ]
            == "DIRECT_CATHODE"
        ]

        battery = [
            paper
            for paper in papers
            if paper[
                "literature_class"
            ]
            == "BATTERY_RELATED"
        ]

        chemistry = [
            paper
            for paper in papers
            if paper[
                "literature_class"
            ]
            == "CHEMISTRY_ONLY"
        ]

        citation_count = sum(
            int(
                paper[
                    "citation_count"
                ]
                or 0
            )
            for paper in papers
        )

        evidence_score = (
            calculate_literature_score(
                direct_count=len(direct),
                battery_count=len(battery),
                chemistry_count=len(
                    chemistry
                ),
                citation_count=(
                    citation_count
                ),
            )
        )

        literature_class = (
            classify_candidate(
                direct_count=len(direct),
                battery_count=len(battery),
                chemistry_count=len(
                    chemistry
                ),
            )
        )

        novelty_signal = (
            classify_novelty_signal(
                direct_count=len(direct),
                battery_count=len(battery),
                chemistry_count=len(
                    chemistry
                ),
            )
        )

        best_paper = None

        if papers:

            best_paper = sorted(
                papers,
                key=lambda paper: (
                    paper_priority(
                        paper[
                            "literature_class"
                        ]
                    ),
                    int(
                        paper[
                            "citation_count"
                        ]
                        or 0
                    ),
                ),
                reverse=True,
            )[0]

        record = row.to_dict()

        record[
            "week6_formula"
        ] = formula

        record[
            "exact_formula_papers"
        ] = len(papers)

        record[
            "direct_cathode_papers"
        ] = len(direct)

        record[
            "battery_related_papers"
        ] = len(battery)

        record[
            "chemistry_only_papers"
        ] = len(chemistry)

        record[
            "literature_total_citations"
        ] = citation_count

        record[
            "literature_evidence_score"
        ] = evidence_score

        record[
            "battery_literature_class"
        ] = literature_class

        record[
            "literature_novelty_signal"
        ] = novelty_signal

        record[
            "crossref_raw_results_seen"
        ] = result[
            "raw_results_seen"
        ]

        record[
            "crossref_error_count"
        ] = len(
            result["errors"]
        )

        record[
            "crossref_errors"
        ] = " | ".join(
            result["errors"]
        )

        if best_paper:

            record[
                "best_literature_title"
            ] = best_paper[
                "title"
            ]

            record[
                "best_literature_doi"
            ] = best_paper[
                "doi"
            ]

            record[
                "best_literature_year"
            ] = best_paper[
                "year"
            ]

            record[
                "best_literature_class"
            ] = best_paper[
                "literature_class"
            ]

        else:

            record[
                "best_literature_title"
            ] = ""

            record[
                "best_literature_doi"
            ] = ""

            record[
                "best_literature_year"
            ] = ""

            record[
                "best_literature_class"
            ] = ""

        summary_records.append(
            record
        )

        print(
            "    "
            f"cathode={len(direct)}, "
            f"battery={len(battery)}, "
            f"chemistry={len(chemistry)}, "
            f"signal={novelty_signal}"
        )

    # -----------------------------------------------------
    # SAVE DATA
    # -----------------------------------------------------

    summary_df = pd.DataFrame(
        summary_records
    )

    hits_df = pd.DataFrame(
        all_hit_records
    )

    SUMMARY_OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_df.to_csv(
        SUMMARY_OUTPUT_FILE,
        index=False,
    )

    if hits_df.empty:

        hits_df = pd.DataFrame(
            columns=[
                "material_id",
                "formula",
                "literature_class",
                "title",
                "year",
                "journal",
                "doi",
                "citation_count",
                "url",
            ]
        )

    hits_df.to_csv(
        HITS_OUTPUT_FILE,
        index=False,
    )

    write_report(
        summary_df,
        hits_df,
    )

    # -----------------------------------------------------
    # FINAL SUMMARY
    # -----------------------------------------------------

    print()
    print("=" * 72)
    print(
        "BATTERY LITERATURE "
        "VALIDATION COMPLETE"
    )
    print("=" * 72)

    print()
    print(
        "Literature classifications:"
    )

    print(
        summary_df[
            "battery_literature_class"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Novelty / exploration signals:"
    )

    print(
        summary_df[
            "literature_novelty_signal"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Candidate literature results:"
    )
    print()

    display_columns = [
        "material_id",
        "week6_formula",
        "direct_cathode_papers",
        "battery_related_papers",
        "chemistry_only_papers",
        "literature_evidence_score",
        "literature_novelty_signal",
    ]

    print(
        summary_df[
            display_columns
        ]
        .sort_values(
            [
                "direct_cathode_papers",
                "battery_related_papers",
                "literature_evidence_score",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
        .to_string(
            index=False
        )
    )

    print()
    print("Saved candidate summary:")
    print(
        SUMMARY_OUTPUT_FILE
    )

    print()
    print("Saved literature hits:")
    print(
        HITS_OUTPUT_FILE
    )

    print()
    print("Saved report:")
    print(
        REPORT_FILE
    )


if __name__ == "__main__":
    main()