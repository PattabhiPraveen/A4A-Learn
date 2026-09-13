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

BACKUP_DIR = QUESTION_FILE.parent / "backups"

REPORT_FILE = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "question_finalization_report.csv"
)


REPLACEMENTS = {

    # Too long / compound question
    "Q020_10":
        "How does the continue statement affect a Python for loop?",

    # DOC018 Python Operators
    "Q018_05":
        "When would you use floor division instead of regular division in Python?",

    # DOC031 File Handling
    "Q031_09":
        "What happens to an existing file when it is opened in write mode in Python?",

    # DOC038 Data Cleaning
    "Q038_09":
        "Why should duplicate records be identified during data cleaning?",

    # DOC090 Correlation
    "Q090_06":
        "What does a negative correlation indicate about two variables?",
}


def main():

    if not QUESTION_FILE.exists():
        raise FileNotFoundError(QUESTION_FILE)

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = (
        BACKUP_DIR
        / f"benchmark_questions_pre_final_{timestamp}.csv"
    )

    shutil.copy2(
        QUESTION_FILE,
        backup,
    )

    df = pd.read_csv(
        QUESTION_FILE,
        encoding="utf-8",
    )

    changes = []

    for question_id, new_question in REPLACEMENTS.items():

        matches = df.index[
            df["question_id"] == question_id
        ].tolist()

        if len(matches) != 1:
            raise ValueError(
                f"{question_id}: expected exactly one row, "
                f"found {len(matches)}"
            )

        index = matches[0]

        old_question = str(
            df.at[index, "question"]
        )

        changes.append(
            {
                "question_id": question_id,
                "document_id":
                    df.at[index, "document_id"],
                "old_question": old_question,
                "new_question": new_question,
                "reason":
                    "targeted benchmark quality correction",
            }
        )

        df.at[
            index,
            "question"
        ] = new_question

    # Critical integrity checks
    if len(df) != 1000:
        raise ValueError(
            f"Expected 1000 questions, found {len(df)}"
        )

    if df["question_id"].nunique() != 1000:
        raise ValueError(
            "Question IDs are no longer unique."
        )

    if df["question"].nunique() != 1000:
        raise ValueError(
            "Question texts are no longer unique."
        )

    counts = (
        df.groupby("document_id")
        .size()
    )

    if len(counts) != 100:
        raise ValueError(
            "Expected 100 documents."
        )

    if not (counts == 10).all():
        raise ValueError(
            "Every document must have exactly 10 questions."
        )

    df.to_csv(
        QUESTION_FILE,
        index=False,
        encoding="utf-8",
    )

    pd.DataFrame(
        changes
    ).to_csv(
        REPORT_FILE,
        index=False,
        encoding="utf-8",
    )

    print("=" * 72)
    print("A4A Learn - Benchmark Question Finalization")
    print("=" * 72)

    print(f"Backup             : {backup}")
    print(f"Questions changed  : {len(changes)}")
    print(f"Total questions    : {len(df)}")
    print(
        f"Unique IDs         : "
        f"{df['question_id'].nunique()}"
    )
    print(
        f"Unique questions   : "
        f"{df['question'].nunique()}"
    )
    print(f"Report             : {REPORT_FILE}")

    print("=" * 72)


if __name__ == "__main__":
    main()