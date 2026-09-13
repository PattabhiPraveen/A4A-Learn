import csv
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

CATALOG_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "evaluation"
    / "document_catalog.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS001_Education"
    / "benchmark_100"
)


def main():

    if not CATALOG_FILE.exists():
        raise FileNotFoundError(
            f"Catalog not found: {CATALOG_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with CATALOG_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        documents = list(
            csv.DictReader(file)
        )

    if len(documents) != 100:
        raise ValueError(
            f"Expected 100 catalog records, "
            f"found {len(documents)}."
        )

    created = 0
    skipped = 0

    for document in documents:

        document_id = document[
            "document_id"
        ].strip()

        title = document[
            "title"
        ].strip()

        domain = document[
            "domain"
        ].strip()

        topic = document[
            "topic"
        ].strip()

        subtopic = document[
            "subtopic"
        ].strip()

        difficulty = document[
            "difficulty"
        ].strip()

        output_file = (
            OUTPUT_DIR
            / f"{document_id}.md"
        )

        # Protect existing populated files.
        if output_file.exists():
            skipped += 1
            continue

        content = f"""# {title}

## Metadata

- Document ID: {document_id}
- Domain: {domain}
- Topic: {topic}
- Subtopic: {subtopic}
- Difficulty: {difficulty}

## Learning Objectives

TODO

## Introduction

TODO

## Core Concepts

TODO

## Detailed Explanation

TODO

## Example

TODO

## Practical Application

TODO

## Common Misconceptions

TODO

## Key Takeaways

TODO

## Summary

TODO
"""

        output_file.write_text(
            content,
            encoding="utf-8",
        )

        created += 1

    print("=" * 70)
    print("A4A Learn - Benchmark Document Template Creation")
    print("=" * 70)
    print(f"Catalog records : {len(documents)}")
    print(f"Created         : {created}")
    print(f"Skipped         : {skipped}")
    print(f"Output          : {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()