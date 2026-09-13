import csv
import re
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

QUESTION_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "evaluation"
    / "questions"
    / "benchmark_questions.csv"
)

DOCUMENT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS001_Education"
    / "benchmark_100"
)

REPORT_DIR = (
    BACKEND_ROOT
    / "reports"
    / "eval"
)

QUALITY_REPORT = (
    REPORT_DIR
    / "question_quality_report.csv"
)

SIMILARITY_REPORT = (
    REPORT_DIR
    / "question_similarity_review.csv"
)

HUMAN_SAMPLE_FILE = (
    REPORT_DIR
    / "human_validation_sample.csv"
)

EXPECTED_QUESTION_COUNT = 1000
EXPECTED_DOC_COUNT = 100
EXPECTED_PER_DOC = 10

ALLOWED_TYPES = {
    "factual",
    "conceptual",
    "application",
    "comparison",
}

LEAKAGE_PATTERNS = [
    r"\bDOC\d{3}\b",
    r"according to the document",
    r"according to the passage",
    r"in the document",
    r"in the passage",
    r"in this document",
    r"in this passage",
    r"source document",
]

NEAR_DUPLICATE_THRESHOLD = 0.88


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s?]", "", text)
    return text


def load_questions():
    df = pd.read_csv(
        QUESTION_FILE,
        encoding="utf-8",
    )

    required_columns = {
        "question_id",
        "document_id",
        "question",
        "question_type",
        "validation_status",
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing)}"
        )

    return df


def structural_validation(df):
    issues = []

    if len(df) != EXPECTED_QUESTION_COUNT:
        issues.append(
            {
                "check":
                    "total_question_count",
                "status":
                    "FAIL",
                "details":
                    f"Expected 1000, "
                    f"found {len(df)}",
            }
        )
    else:
        issues.append(
            {
                "check":
                    "total_question_count",
                "status":
                    "PASS",
                "details":
                    "1000 questions",
            }
        )

    unique_ids = (
        df["question_id"]
        .nunique()
    )

    issues.append(
        {
            "check":
                "unique_question_ids",
            "status":
                "PASS"
                if unique_ids
                == EXPECTED_QUESTION_COUNT
                else "FAIL",
            "details":
                str(unique_ids),
        }
    )

    unique_questions = (
        df["question"]
        .nunique()
    )

    issues.append(
        {
            "check":
                "exact_question_uniqueness",
            "status":
                "PASS"
                if unique_questions
                == EXPECTED_QUESTION_COUNT
                else "FAIL",
            "details":
                str(unique_questions),
        }
    )

    doc_counts = (
        df.groupby("document_id")
        .size()
    )

    bad_docs = (
        doc_counts[
            doc_counts
            != EXPECTED_PER_DOC
        ]
    )

    issues.append(
        {
            "check":
                "questions_per_document",
            "status":
                "PASS"
                if len(bad_docs) == 0
                and len(doc_counts)
                == EXPECTED_DOC_COUNT
                else "FAIL",
            "details":
                (
                    "10 questions for each "
                    "of 100 documents"
                    if len(bad_docs) == 0
                    and len(doc_counts)
                    == EXPECTED_DOC_COUNT
                    else str(
                        bad_docs.to_dict()
                    )
                ),
        }
    )

    invalid_types = (
        df[
            ~df["question_type"]
            .isin(ALLOWED_TYPES)
        ]
    )

    issues.append(
        {
            "check":
                "question_types",
            "status":
                "PASS"
                if invalid_types.empty
                else "FAIL",
            "details":
                (
                    "All valid"
                    if invalid_types.empty
                    else
                    f"{len(invalid_types)} "
                    f"invalid"
                ),
        }
    )

    return issues


def content_validation(df):
    row_results = []

    for _, row in df.iterrows():
        question = str(
            row["question"]
        ).strip()

        errors = []

        word_count = len(
            question.split()
        )

        if word_count < 4:
            errors.append(
                "too_short"
            )

        if word_count > 40:
            errors.append(
                "too_long"
            )

        if not question.endswith("?"):
            errors.append(
                "missing_question_mark"
            )

        leakage = []

        for pattern in (
            LEAKAGE_PATTERNS
        ):
            if re.search(
                pattern,
                question,
                re.IGNORECASE,
            ):
                leakage.append(
                    pattern
                )

        if leakage:
            errors.append(
                "source_leakage"
            )

        row_results.append(
            {
                "question_id":
                    row["question_id"],
                "document_id":
                    row["document_id"],
                "question_type":
                    row["question_type"],
                "word_count":
                    word_count,
                "leakage":
                    "|".join(leakage),
                "issues":
                    "|".join(errors),
                "status":
                    "PASS"
                    if not errors
                    else "REVIEW",
            }
        )

    return pd.DataFrame(
        row_results
    )


def duplicate_screen(df):
    questions = (
        df["question"]
        .fillna("")
        .astype(str)
        .tolist()
    )

    normalized = [
        normalize_text(q)
        for q in questions
    ]

    vectorizer = (
        TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=50000,
        )
    )

    matrix = (
        vectorizer
        .fit_transform(normalized)
    )

    similarities = (
        cosine_similarity(matrix)
    )

    pairs = []

    for i in range(
        len(df)
    ):
        for j in range(
            i + 1,
            len(df),
        ):
            score = (
                similarities[i, j]
            )

            if (
                score
                >= NEAR_DUPLICATE_THRESHOLD
            ):
                pairs.append(
                    {
                        "question_id_1":
                            df.iloc[i][
                                "question_id"
                            ],
                        "document_id_1":
                            df.iloc[i][
                                "document_id"
                            ],
                        "question_1":
                            df.iloc[i][
                                "question"
                            ],
                        "question_id_2":
                            df.iloc[j][
                                "question_id"
                            ],
                        "document_id_2":
                            df.iloc[j][
                                "document_id"
                            ],
                        "question_2":
                            df.iloc[j][
                                "question"
                            ],
                        "similarity":
                            round(
                                float(score),
                                4,
                            ),
                    }
                )

    return pd.DataFrame(
        pairs
    )


def create_human_sample(
    df,
    sample_per_doc=3,
):
    samples = []

    for document_id, group in (
        df.groupby(
            "document_id"
        )
    ):
        n = min(
            sample_per_doc,
            len(group),
        )

        sampled = (
            group.sample(
                n=n,
                random_state=42,
            )
        )

        for _, row in (
            sampled.iterrows()
        ):
            samples.append(
                {
                    "question_id":
                        row[
                            "question_id"
                        ],
                    "document_id":
                        row[
                            "document_id"
                        ],
                    "question":
                        row[
                            "question"
                        ],
                    "question_type":
                        row[
                            "question_type"
                        ],
                    "answerable_from_source":
                        "",
                    "correct_source":
                        "",
                    "natural_question":
                        "",
                    "factually_safe":
                        "",
                    "reviewer_comments":
                        "",
                    "human_validation_status":
                        "pending",
                }
            )

    return pd.DataFrame(
        samples
    )


def main():
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 72)
    print(
        "A4A Learn - Question Quality Validator"
    )
    print("=" * 72)

    df = load_questions()

    print(
        f"Questions loaded : "
        f"{len(df)}"
    )

    print(
        f"Documents        : "
        f"{df['document_id'].nunique()}"
    )

    structural = (
        structural_validation(df)
    )

    structural_df = (
        pd.DataFrame(
            structural
        )
    )

    content_df = (
        content_validation(df)
    )

    quality_output = (
        content_df.merge(
            df[
                [
                    "question_id",
                    "question",
                    "validation_status",
                ]
            ],
            on="question_id",
            how="left",
            suffixes=(
                "",
                "_original",
            ),
        )
    )

    quality_output.to_csv(
        QUALITY_REPORT,
        index=False,
        encoding="utf-8",
    )

    similarity_df = (
        duplicate_screen(df)
    )

    similarity_df.to_csv(
        SIMILARITY_REPORT,
        index=False,
        encoding="utf-8",
    )

    human_df = (
        create_human_sample(
            df,
            sample_per_doc=3,
        )
    )

    human_df.to_csv(
        HUMAN_SAMPLE_FILE,
        index=False,
        encoding="utf-8",
    )

    review_count = (
        (
            content_df[
                "status"
            ]
            == "REVIEW"
        )
        .sum()
    )

    near_duplicate_count = (
        len(similarity_df)
    )

    type_counts = (
        Counter(
            df[
                "question_type"
            ]
        )
    )

    print()
    print(
        "STRUCTURAL VALIDATION"
    )
    print("-" * 72)

    for item in structural:
        print(
            f"{item['check']:<30} "
            f"{item['status']:<8} "
            f"{item['details']}"
        )

    print()
    print(
        "QUESTION QUALITY"
    )
    print("-" * 72)

    print(
        f"Questions requiring review : "
        f"{review_count}"
    )

    print(
        f"Near-duplicate pairs >= "
        f"{NEAR_DUPLICATE_THRESHOLD} : "
        f"{near_duplicate_count}"
    )

    print()
    print(
        "QUESTION TYPE DISTRIBUTION"
    )
    print("-" * 72)

    for key in sorted(
        type_counts
    ):
        print(
            f"{key:<15}: "
            f"{type_counts[key]}"
        )

    print()
    print(
        "HUMAN VALIDATION SAMPLE"
    )
    print("-" * 72)

    print(
        f"Sample size : "
        f"{len(human_df)}"
    )

    structural_pass = all(
        item["status"]
        == "PASS"
        for item in structural
    )

    automated_pass = (
        structural_pass
        and review_count == 0
    )

    print()
    print("=" * 72)

    print(
        "STRUCTURAL VALIDATION: "
        + (
            "PASS"
            if structural_pass
            else "FAIL"
        )
    )

    print(
        "AUTOMATED QUESTION QUALITY: "
        + (
            "PASS"
            if automated_pass
            else "REVIEW REQUIRED"
        )
    )

    print(
        "SEMANTIC DUPLICATE SCREEN: "
        + (
            "PASS"
            if near_duplicate_count
            == 0
            else "REVIEW REQUIRED"
        )
    )

    print(
        f"Quality report    : "
        f"{QUALITY_REPORT}"
    )

    print(
        f"Similarity report : "
        f"{SIMILARITY_REPORT}"
    )

    print(
        f"Human sample      : "
        f"{HUMAN_SAMPLE_FILE}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()