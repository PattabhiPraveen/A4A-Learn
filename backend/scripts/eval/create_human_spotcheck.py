from pathlib import Path

import pandas as pd


BACKEND_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "human_validation_assisted.csv"
)

OUTPUT_FILE = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "human_spotcheck_30.csv"
)

SAMPLE_SIZE = 30
RANDOM_SEED = 42


def main():

    print("=" * 72)
    print("A4A Learn - Human Spot Check")
    print("=" * 72)

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    low = df[
        df["review_risk"].str.upper()
        == "LOW"
    ].copy()

    print(
        f"LOW-risk candidates : {len(low)}"
    )

    if len(low) < SAMPLE_SIZE:
        raise ValueError(
            "Insufficient LOW-risk questions."
        )

    # Sort first so sampling remains
    # reproducible.
    low = low.sort_values(
        by=["document_id", "question_id"]
    )

    sample = low.sample(
        n=SAMPLE_SIZE,
        random_state=RANDOM_SEED,
    ).copy()

    sample = sample.sort_values(
        by=["document_id", "question_id"]
    )

    # AI output remains visible as supporting
    # evidence, but human decision is separate.
    sample[
        "human_answerable_from_source"
    ] = ""

    sample[
        "human_correct_source"
    ] = ""

    sample[
        "human_natural_question"
    ] = ""

    sample[
        "human_factually_safe"
    ] = ""

    sample[
        "human_comments"
    ] = ""

    sample[
        "human_final_status"
    ] = "pending"

    sample.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"Spot-check size     : {len(sample)}"
    )

    print(
        f"Documents represented: "
        f"{sample['document_id'].nunique()}"
    )

    print(
        f"Output              : "
        f"{OUTPUT_FILE}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()