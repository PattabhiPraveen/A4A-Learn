from pathlib import Path

import pandas as pd


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

SAMPLE_FILE = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "human_validation_sample.csv"
)

CORPUS_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS001_Education"
    / "benchmark_100"
)

OUTPUT_FILE = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "human_validation_review.csv"
)


def read_document(document_id: str) -> str:
    path = CORPUS_DIR / f"{document_id}.md"

    if not path.exists():
        raise FileNotFoundError(
            f"Missing source document: {path}"
        )

    return path.read_text(
        encoding="utf-8"
    )


def extract_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()

        if line.startswith("# "):
            return line[2:].strip()

    return ""


def main():

    print("=" * 72)
    print("A4A Learn - Human Validation Preparation")
    print("=" * 72)

    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(
            f"Missing sample: {SAMPLE_FILE}"
        )

    sample = pd.read_csv(
        SAMPLE_FILE,
        encoding="utf-8",
    )

    if len(sample) != 300:
        raise ValueError(
            f"Expected 300 sampled questions, "
            f"found {len(sample)}"
        )

    output_rows = []

    missing_documents = []

    for _, row in sample.iterrows():

        document_id = str(
            row["document_id"]
        ).strip()

        try:
            source_text = read_document(
                document_id
            )
        except FileNotFoundError:
            missing_documents.append(
                document_id
            )
            continue

        title = extract_title(
            source_text
        )

        output_rows.append(
            {
                "question_id":
                    row["question_id"],

                "document_id":
                    document_id,

                "question":
                    row["question"],

                "question_type":
                    row["question_type"],

                "source_title":
                    title,

                # Full source is intentional for
                # human answerability validation.
                "source_content":
                    source_text,

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

    if missing_documents:
        raise ValueError(
            "Missing source documents: "
            + ", ".join(
                sorted(
                    set(missing_documents)
                )
            )
        )

    result = pd.DataFrame(
        output_rows
    )

    if len(result) != 300:
        raise ValueError(
            f"Expected 300 review rows, "
            f"created {len(result)}"
        )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"Review questions : {len(result)}"
    )

    print(
        f"Documents covered: "
        f"{result['document_id'].nunique()}"
    )

    print(
        "Questions/doc    : "
        f"{result.groupby('document_id').size().min()}"
        " - "
        f"{result.groupby('document_id').size().max()}"
    )

    print(
        f"Output           : {OUTPUT_FILE}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()