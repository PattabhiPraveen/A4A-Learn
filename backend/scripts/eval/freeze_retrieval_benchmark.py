import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

EVAL_ROOT = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "evaluation"
)

CORPUS_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS001_Education"
    / "benchmark_100"
)

CATALOG_FILE = (
    EVAL_ROOT
    / "document_catalog.csv"
)

QUESTION_FILE = (
    EVAL_ROOT
    / "questions"
    / "benchmark_questions.csv"
)

SPOTCHECK_FILE = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "human_spotcheck_30.csv"
)

QUALITY_REPORT = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "question_quality_report.csv"
)

SIMILARITY_REPORT = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "question_similarity_review.csv"
)

FREEZE_DIR = (
    EVAL_ROOT
    / "retrieval_v1"
)

FROZEN_CORPUS_DIR = (
    FREEZE_DIR
    / "corpus"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def validate_source_files():
    required = [
        CATALOG_FILE,
        QUESTION_FILE,
        SPOTCHECK_FILE,
    ]

    missing = [
        str(path)
        for path in required
        if not path.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing required files:\n"
            + "\n".join(missing)
        )


def validate_questions():
    df = pd.read_csv(
        QUESTION_FILE,
        encoding="utf-8",
    )

    if len(df) != 1000:
        raise ValueError(
            f"Expected 1000 questions, found {len(df)}"
        )

    if df["question_id"].nunique() != 1000:
        raise ValueError(
            "Question IDs are not unique."
        )

    if df["question"].nunique() != 1000:
        raise ValueError(
            "Question text is not unique."
        )

    counts = (
        df.groupby("document_id")
        .size()
    )

    if len(counts) != 100:
        raise ValueError(
            f"Expected 100 documents, found {len(counts)}"
        )

    if not (counts == 10).all():
        raise ValueError(
            "Every document must have exactly "
            "10 questions."
        )

    return df


def validate_catalog():
    df = pd.read_csv(
        CATALOG_FILE,
        encoding="utf-8"
    )

    if len(df) != 100:
        raise ValueError(
            f"Expected 100 catalog records, found {len(df)}"
        )

    if df["document_id"].nunique() != 100:
        raise ValueError(
            "Catalog document IDs are not unique."
        )

    return df


def validate_corpus():
    files = sorted(
        CORPUS_DIR.glob("DOC*.md")
    )

    if len(files) != 100:
        raise ValueError(
            f"Expected 100 corpus files, found {len(files)}"
        )

    expected = {
        f"DOC{i:03d}.md"
        for i in range(1, 101)
    }

    actual = {
        path.name
        for path in files
    }

    missing = expected - actual
    unexpected = actual - expected

    if missing or unexpected:
        raise ValueError(
            f"Corpus mismatch. "
            f"Missing={sorted(missing)}, "
            f"Unexpected={sorted(unexpected)}"
        )

    return files


def validate_human_spotcheck():
    df = pd.read_csv(
        SPOTCHECK_FILE,
        encoding="utf-8-sig",
    )

    if len(df) != 30:
        raise ValueError(
            f"Expected 30 human-reviewed rows, found {len(df)}"
        )

    if "human_final_status" not in df.columns:
        raise ValueError(
            "human_final_status column missing."
        )

    statuses = (
        df["human_final_status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    status_counts = (
        statuses
        .value_counts()
        .to_dict()
    )

    invalid = df[
        statuses != "validated"
    ]

    if not invalid.empty:
        print()
        print("HUMAN VALIDATION GATE FAILED")
        print("-" * 72)

        print(
            invalid[
                [
                    "question_id",
                    "document_id",
                    "human_final_status",
                ]
            ].to_string(index=False)
        )

        raise ValueError(
            "Benchmark cannot be frozen until all "
            "30 human spot-check questions are "
            "validated."
        )

    return df, status_counts


def copy_optional_report(
    source: Path,
    destination_name: str,
):
    if source.exists():
        shutil.copy2(
            source,
            FREEZE_DIR / destination_name,
        )


def main():
    print("=" * 72)
    print("A4A Learn - Retrieval Benchmark Freeze")
    print("=" * 72)

    validate_source_files()

    question_df = validate_questions()
    catalog_df = validate_catalog()
    corpus_files = validate_corpus()

    human_df, status_counts = (
        validate_human_spotcheck()
    )

    print("Pre-freeze gates")
    print("-" * 72)
    print(f"Documents             : {len(catalog_df)}")
    print(f"Corpus files          : {len(corpus_files)}")
    print(f"Questions             : {len(question_df)}")
    print(
        f"Human spot-check      : "
        f"{len(human_df)}"
    )
    print(
        f"Human status          : "
        f"{status_counts}"
    )
    print()

    if FREEZE_DIR.exists():
        raise FileExistsError(
            f"Freeze directory already exists:\n"
            f"{FREEZE_DIR}\n\n"
            "Do not overwrite a frozen benchmark."
        )

    FREEZE_DIR.mkdir(
        parents=True,
        exist_ok=False,
    )

    FROZEN_CORPUS_DIR.mkdir(
        parents=True,
        exist_ok=False,
    )

    # Freeze primary artifacts.
    shutil.copy2(
        CATALOG_FILE,
        FREEZE_DIR
        / "document_catalog_v1.csv",
    )

    shutil.copy2(
        QUESTION_FILE,
        FREEZE_DIR
        / "benchmark_questions_v1.csv",
    )

    shutil.copy2(
        SPOTCHECK_FILE,
        FREEZE_DIR
        / "human_spotcheck_v1.csv",
    )

    for corpus_file in corpus_files:
        shutil.copy2(
            corpus_file,
            FROZEN_CORPUS_DIR
            / corpus_file.name,
        )

    copy_optional_report(
        QUALITY_REPORT,
        "question_quality_report_v1.csv",
    )

    copy_optional_report(
        SIMILARITY_REPORT,
        "question_similarity_review_v1.csv",
    )

    # Create manifest.
    frozen_files = sorted(
        [
            path
            for path in FREEZE_DIR.rglob("*")
            if path.is_file()
        ]
    )

    hashes = {}

    for path in frozen_files:
        relative = str(
            path.relative_to(FREEZE_DIR)
        ).replace("\\", "/")

        hashes[relative] = sha256_file(
            path
        )

    manifest = {
        "benchmark_name":
            "A4A Learn Retrieval Evaluation Set",
        "version":
            "1.0",
        "created_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "documents":
            100,
        "questions":
            1000,
        "questions_per_document":
            10,
        "human_spotcheck_questions":
            30,
        "human_spotcheck_status":
            "validated",
        "gold_relevance_unit":
            "document_id",
        "synthetic_corpus":
            True,
        "question_generation":
            "LLM-assisted with automated quality "
            "validation and human spot-check",
        "semantic_duplicate_screen":
            "PASS WITH REVIEW",
        "exact_question_duplicates":
            0,
        "corpus_format":
            "Markdown",
        "integrity_algorithm":
            "SHA-256",
        "files":
            hashes,
    }

    manifest_file = (
        FREEZE_DIR
        / "benchmark_manifest_v1.json"
    )

    manifest_file.write_text(
        json.dumps(
            manifest,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Hash manifest itself separately.
    manifest_hash = sha256_file(
        manifest_file
    )

    checksum_file = (
        FREEZE_DIR
        / "benchmark_manifest_v1.sha256"
    )

    checksum_file.write_text(
        f"{manifest_hash}  "
        f"benchmark_manifest_v1.json\n",
        encoding="utf-8",
    )

    readme = """# A4A Learn Retrieval Evaluation Set v1.0

## Purpose

Controlled evaluation dataset for comparing retrieval
embedding models used by the A4A Learn RAG pipeline.

## Composition

- 100 educational source documents
- 1,000 learner questions
- 10 questions per document
- Gold relevance defined at document level
- 30-question human spot-check
- Automated structural and quality validation

## Methodology

The corpus and questions were generated with LLM assistance
and subjected to automated structural, semantic, quality,
and human-review controls.

Synthetic educational content must not be described as an
authoritative external knowledge source.

## Evaluation Principle

For a learner query, retrieval is successful when the
expected source document appears within the evaluated
Top-K results.

The benchmark is frozen before comparative embedding-model
experiments begin.

## Integrity

SHA-256 hashes are stored in the benchmark manifest.

Do not modify frozen v1.0 artifacts. Any future corrections
must create a new benchmark version.
"""

    (
        FREEZE_DIR
        / "README.md"
    ).write_text(
        readme,
        encoding="utf-8",
    )

    print("=" * 72)
    print("BENCHMARK FREEZE: PASS")
    print("=" * 72)

    print(
        f"Frozen directory : {FREEZE_DIR}"
    )

    print(
        f"Documents        : {len(corpus_files)}"
    )

    print(
        f"Questions        : {len(question_df)}"
    )

    print(
        f"Human validated  : {len(human_df)}"
    )

    print(
        f"Manifest         : {manifest_file}"
    )

    print(
        f"Manifest SHA-256 : {manifest_hash}"
    )

    print()
    print(
        "Retrieval Evaluation Set v1.0 "
        "is now immutable."
    )

    print("=" * 72)


if __name__ == "__main__":
    main()