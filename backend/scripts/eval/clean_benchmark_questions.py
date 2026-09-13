import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


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

BACKUP_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "evaluation"
    / "questions"
    / "backups"
)

CHANGE_REPORT = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "question_cleanup_report.csv"
)


# Only remove benchmark/document-reference wording.
# Do NOT change the actual subject of the question.
LEAKAGE_PATTERNS = [
    r",?\s*according to the document",
    r",?\s*as mentioned in the document",
    r",?\s*as identified in the document",
    r",?\s*as discussed in the document",
    r",?\s*as described in the document",
    r",?\s*as explained in the document",
    r",?\s*as stated in the document",
    r",?\s*provided in the document",
    r",?\s*mentioned in the document",
    r",?\s*discussed in the document",
    r",?\s*described in the document",
    r",?\s*explained in the document",
    r",?\s*in the document",
]


def clean_question(question: str) -> str:
    original = question.strip()

    cleaned = original

    for pattern in LEAKAGE_PATTERNS:
        cleaned = re.sub(
            pattern,
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    )

    cleaned = re.sub(
        r"\s+,",
        ",",
        cleaned,
    )

    cleaned = re.sub(
        r",\s*\?",
        "?",
        cleaned,
    )

    cleaned = cleaned.strip()

    if cleaned and not cleaned.endswith("?"):
        cleaned = (
            cleaned.rstrip(".!")
            + "?"
        )

    return cleaned


def main():
    if not QUESTION_FILE.exists():
        raise FileNotFoundError(
            QUESTION_FILE
        )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CHANGE_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_file = (
        BACKUP_DIR
        / f"benchmark_questions_{timestamp}.csv"
    )

    shutil.copy2(
        QUESTION_FILE,
        backup_file,
    )

    print("=" * 72)
    print(
        "A4A Learn - Benchmark Question Cleaner"
    )
    print("=" * 72)

    print(
        f"Backup created : {backup_file}"
    )

    df = pd.read_csv(
        QUESTION_FILE,
        encoding="utf-8",
    )

    changes = []

    for index, row in df.iterrows():
        original = str(
            row["question"]
        ).strip()

        cleaned = clean_question(
            original
        )

        if cleaned != original:
            changes.append(
                {
                    "question_id":
                        row["question_id"],
                    "document_id":
                        row["document_id"],
                    "original_question":
                        original,
                    "cleaned_question":
                        cleaned,
                }
            )

            df.at[
                index,
                "question",
            ] = cleaned

    df.to_csv(
        QUESTION_FILE,
        index=False,
        encoding="utf-8",
    )

    pd.DataFrame(
        changes
    ).to_csv(
        CHANGE_REPORT,
        index=False,
        encoding="utf-8",
    )

    print(
        f"Questions modified : "
        f"{len(changes)}"
    )

    print(
        f"Total questions    : "
        f"{len(df)}"
    )

    print(
        f"Cleanup report     : "
        f"{CHANGE_REPORT}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()