import csv
import hashlib
import re
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

DOCUMENT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS001_Education"
    / "benchmark_100"
)

CATALOG_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "evaluation"
    / "document_catalog.csv"
)

REPORT_DIR = (
    BACKEND_ROOT
    / "reports"
    / "eval"
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REQUIRED_HEADINGS = [
    "## Metadata",
    "## Learning Objectives",
    "## Introduction",
    "## Core Concepts",
    "## Detailed Explanation",
    "## Example",
    "## Practical Application",
    "## Common Misconceptions",
    "## Key Takeaways",
    "## Summary",
]

MIN_WORDS = 600
MAX_WORDS = 1300

# This is a screening threshold, not a universal
# definition of semantic duplication.
SIMILARITY_REVIEW_THRESHOLD = 0.75


def normalize_text(text):

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def word_count(text):

    return len(
        text.split()
    )


def main():

    print("=" * 70)
    print("A4A Learn - Benchmark Corpus Quality Validator")
    print("=" * 70)

    catalog = pd.read_csv(
        CATALOG_FILE
    )

    expected_ids = set(
        catalog["document_id"]
        .astype(str)
        .str.strip()
    )

    files = sorted(
        DOCUMENT_DIR.glob("DOC*.md")
    )

    print(
        f"Catalog documents : {len(expected_ids)}"
    )

    print(
        f"Corpus files      : {len(files)}"
    )

    records = []
    texts = []
    ids = []
    hashes = []

    for path in files:

        document_id = path.stem

        text = path.read_text(
            encoding="utf-8"
        )

        normalized = normalize_text(
            text
        )

        count = word_count(
            text
        )

        missing_headings = [
            heading
            for heading in REQUIRED_HEADINGS
            if heading not in text
        ]

        contains_todo = (
            "TODO" in text
        )

        content_hash = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        records.append(
            {
                "document_id": document_id,
                "word_count": count,
                "length_valid": (
                    MIN_WORDS
                    <= count
                    <= MAX_WORDS
                ),
                "missing_headings": (
                    " | ".join(
                        missing_headings
                    )
                ),
                "contains_todo": contains_todo,
                "sha256": content_hash,
            }
        )

        ids.append(
            document_id
        )

        texts.append(
            normalized
        )

        hashes.append(
            content_hash
        )

    actual_ids = set(ids)

    missing_files = sorted(
        expected_ids - actual_ids
    )

    unexpected_files = sorted(
        actual_ids - expected_ids
    )

    exact_duplicate_count = (
        len(hashes)
        - len(set(hashes))
    )

    # --------------------------------------------------
    # Near-duplicate screening
    # --------------------------------------------------

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=30000,
    )

    matrix = vectorizer.fit_transform(
        texts
    )

    similarity_matrix = cosine_similarity(
        matrix
    )

    similarity_records = []

    for i in range(
        len(ids)
    ):

        for j in range(
            i + 1,
            len(ids),
        ):

            score = float(
                similarity_matrix[i, j]
            )

            if (
                score
                >= SIMILARITY_REVIEW_THRESHOLD
            ):

                similarity_records.append(
                    {
                        "document_1": ids[i],
                        "document_2": ids[j],
                        "similarity": round(
                            score,
                            4,
                        ),
                    }
                )

    similarity_records.sort(
        key=lambda row: row[
            "similarity"
        ],
        reverse=True,
    )

    quality_df = pd.DataFrame(
        records
    )

    similarity_df = pd.DataFrame(
        similarity_records,
        columns=[
            "document_1",
            "document_2",
            "similarity",
        ],
    )

    quality_file = (
        REPORT_DIR
        / "corpus_quality_report.csv"
    )

    similarity_file = (
        REPORT_DIR
        / "corpus_similarity_review.csv"
    )

    quality_df.to_csv(
        quality_file,
        index=False,
    )

    similarity_df.to_csv(
        similarity_file,
        index=False,
    )

    invalid_length = quality_df[
        ~quality_df["length_valid"]
    ]

    missing_structure = quality_df[
        quality_df[
            "missing_headings"
        ] != ""
    ]

    todo_documents = quality_df[
        quality_df[
            "contains_todo"
        ]
    ]

    print()
    print("STRUCTURAL QUALITY")
    print("-" * 70)

    print(
        f"Missing files       : "
        f"{len(missing_files)}"
    )

    print(
        f"Unexpected files    : "
        f"{len(unexpected_files)}"
    )

    print(
        f"Invalid length      : "
        f"{len(invalid_length)}"
    )

    print(
        f"Missing headings    : "
        f"{len(missing_structure)}"
    )

    print(
        f"TODO placeholders   : "
        f"{len(todo_documents)}"
    )

    print(
        f"Exact duplicates    : "
        f"{exact_duplicate_count}"
    )

    print(
        f"Near-duplicate pairs: "
        f"{len(similarity_records)}"
    )

    print()
    print("CORPUS STATISTICS")
    print("-" * 70)

    print(
        f"Minimum words : "
        f"{quality_df['word_count'].min()}"
    )

    print(
        f"Maximum words : "
        f"{quality_df['word_count'].max()}"
    )

    print(
        f"Average words : "
        f"{quality_df['word_count'].mean():.2f}"
    )

    print(
        f"Total words   : "
        f"{quality_df['word_count'].sum()}"
    )

    if similarity_records:

        print()
        print("TOP SIMILARITY PAIRS")
        print("-" * 70)

        for row in (
            similarity_records[:10]
        ):

            print(
                f"{row['document_1']} "
                f"<-> "
                f"{row['document_2']} : "
                f"{row['similarity']:.4f}"
            )

    structural_pass = (
        len(files) == 100
        and not missing_files
        and not unexpected_files
        and len(invalid_length) == 0
        and len(missing_structure) == 0
        and len(todo_documents) == 0
        and exact_duplicate_count == 0
    )

    print()
    print("=" * 70)

    print(
        "STRUCTURAL VALIDATION:",
        (
            "PASS"
            if structural_pass
            else "FAIL"
        ),
    )

    print(
        "SEMANTIC REVIEW:",
        (
            "REVIEW REQUIRED"
            if similarity_records
            else "PASS"
        ),
    )

    print(
        f"Quality report    : "
        f"{quality_file}"
    )

    print(
        f"Similarity report : "
        f"{similarity_file}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()