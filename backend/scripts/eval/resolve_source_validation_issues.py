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
    / "source_validation_corrections.csv"
)


CORRECTIONS = {
    "Q011_09": {
        "new_question":
            "How are captions synchronized with video or audio content?",
        "reason":
            "Original question asked for two main types of captioning "
            "tools, a classification not supported by DOC011.",
    },

    "Q080_06": {
        "new_question":
            "What are the three main components of an operating system?",
        "reason":
            "DOC080 mentions GUI and CLI but does not explain their "
            "differences. The replacement is explicitly supported.",
    },
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

    backup_file = (
        BACKUP_DIR
        / f"benchmark_questions_pre_source_fix_{timestamp}.csv"
    )

    shutil.copy2(
        QUESTION_FILE,
        backup_file,
    )

    df = pd.read_csv(
        QUESTION_FILE,
        encoding="utf-8",
    )

    changes = []

    for question_id, correction in CORRECTIONS.items():

        matches = df.index[
            df["question_id"] == question_id
        ].tolist()

        if len(matches) != 1:
            raise ValueError(
                f"{question_id}: expected 1 row, "
                f"found {len(matches)}"
            )

        index = matches[0]

        old_question = str(
            df.at[index, "question"]
        )

        new_question = correction[
            "new_question"
        ]

        changes.append(
            {
                "question_id": question_id,
                "document_id":
                    df.at[index, "document_id"],
                "old_question": old_question,
                "new_question": new_question,
                "reason":
                    correction["reason"],
            }
        )

        df.at[
            index,
            "question"
        ] = new_question

    # Benchmark integrity gates
    if len(df) != 1000:
        raise ValueError(
            f"Expected 1000 questions, found {len(df)}"
        )

    if df["question_id"].nunique() != 1000:
        raise ValueError(
            "Question IDs must remain unique."
        )

    if df["question"].nunique() != 1000:
        raise ValueError(
            "Question text must remain unique."
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
            "Each document must retain exactly 10 questions."
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
    print("A4A Learn - Source Validation Corrections")
    print("=" * 72)

    print(f"Backup            : {backup_file}")
    print(f"Corrections       : {len(changes)}")
    print(f"Questions         : {len(df)}")
    print(
        f"Unique IDs        : "
        f"{df['question_id'].nunique()}"
    )
    print(
        f"Unique questions  : "
        f"{df['question'].nunique()}"
    )
    print(f"Report            : {REPORT_FILE}")

    print("=" * 72)


if __name__ == "__main__":
    main()