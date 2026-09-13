import json
import time
from pathlib import Path

import pandas as pd
import requests


BACKEND_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "human_validation_review.csv"
)

OUTPUT_FILE = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "human_validation_assisted.csv"
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"

TIMEOUT = 300
MAX_ATTEMPTS = 3


def build_prompt(question, source_content):
    return f"""
You are assisting a HUMAN reviewer who is validating an
educational retrieval benchmark.

You are NOT making the final approval decision.

Evaluate the learner question ONLY against the supplied
source document.

SOURCE DOCUMENT:
----------------
{source_content}

LEARNER QUESTION:
----------------
{question}

Evaluate these criteria:

1. answerable_from_source
   Can the question be answered using the source?

2. correct_source
   Is this source document relevant enough to be the
   expected retrieval document?

3. natural_question
   Does this resemble a reasonable learner question?

4. factually_safe
   Does the question avoid an obviously false,
   misleading, or unsupported premise?

Return ONLY valid JSON:

{{
  "answerable_from_source": "yes|no|uncertain",
  "correct_source": "yes|no|uncertain",
  "natural_question": "yes|no|uncertain",
  "factually_safe": "yes|no|uncertain",
  "suggested_status": "validated|review|reject",
  "reason": "short explanation"
}}
""".strip()


def call_ollama(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.0,
            "top_p": 0.9,
        },
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    result = response.json()

    return json.loads(
        result["response"]
    )


def validate_response(result):
    required = {
        "answerable_from_source",
        "correct_source",
        "natural_question",
        "factually_safe",
        "suggested_status",
        "reason",
    }

    if not required.issubset(result):
        return False

    ynu = {"yes", "no", "uncertain"}

    for field in [
        "answerable_from_source",
        "correct_source",
        "natural_question",
        "factually_safe",
    ]:
        if (
            str(result[field]).lower()
            not in ynu
        ):
            return False

    if (
        str(result["suggested_status"]).lower()
        not in {"validated", "review", "reject"}
    ):
        return False

    return True


def derive_risk(result):
    values = [
        str(result["answerable_from_source"]).lower(),
        str(result["correct_source"]).lower(),
        str(result["natural_question"]).lower(),
        str(result["factually_safe"]).lower(),
    ]

    if "no" in values:
        return "HIGH"

    if "uncertain" in values:
        return "MEDIUM"

    return "LOW"


def main():
    print("=" * 72)
    print("A4A Learn - Assisted Human Validation")
    print("=" * 72)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing review file: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    print(f"Questions loaded : {len(df)}")
    print(f"Model            : {MODEL}")
    print()

    output_rows = []

    for index, row in df.iterrows():

        question_id = row["question_id"]

        print(
            f"[{index + 1:03d}/{len(df)}] "
            f"{question_id}"
        )

        prompt = build_prompt(
            str(row["question"]),
            str(row["source_content"]),
        )

        result = None
        last_error = ""

        for attempt in range(
            1,
            MAX_ATTEMPTS + 1,
        ):
            try:
                candidate = call_ollama(
                    prompt
                )

                if validate_response(
                    candidate
                ):
                    result = candidate
                    break

                last_error = (
                    "Invalid response schema"
                )

            except Exception as exc:
                last_error = str(exc)

            print(
                f"  attempt {attempt} failed: "
                f"{last_error}"
            )

            time.sleep(1)

        output = row.to_dict()

        if result:

            output[
                "ai_answerable_from_source"
            ] = result[
                "answerable_from_source"
            ]

            output[
                "ai_correct_source"
            ] = result[
                "correct_source"
            ]

            output[
                "ai_natural_question"
            ] = result[
                "natural_question"
            ]

            output[
                "ai_factually_safe"
            ] = result[
                "factually_safe"
            ]

            output[
                "ai_suggested_status"
            ] = result[
                "suggested_status"
            ]

            output[
                "ai_review_reason"
            ] = result[
                "reason"
            ]

            output[
                "review_risk"
            ] = derive_risk(
                result
            )

            print(
                "  -> "
                f"{result['suggested_status']} "
                f"[{output['review_risk']}]"
            )

        else:

            output[
                "ai_answerable_from_source"
            ] = "ERROR"

            output[
                "ai_correct_source"
            ] = "ERROR"

            output[
                "ai_natural_question"
            ] = "ERROR"

            output[
                "ai_factually_safe"
            ] = "ERROR"

            output[
                "ai_suggested_status"
            ] = "review"

            output[
                "ai_review_reason"
            ] = last_error

            output[
                "review_risk"
            ] = "HIGH"

        output_rows.append(
            output
        )

        # Checkpoint after every question.
        pd.DataFrame(
            output_rows
        ).to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig",
        )

    result_df = pd.DataFrame(
        output_rows
    )

    print()
    print("=" * 72)
    print("ASSISTED REVIEW SUMMARY")
    print("=" * 72)

    print(
        result_df[
            "ai_suggested_status"
        ].value_counts(
            dropna=False
        )
    )

    print()
    print("RISK DISTRIBUTION")

    print(
        result_df[
            "review_risk"
        ].value_counts(
            dropna=False
        )
    )

    print()
    print(
        f"Output: {OUTPUT_FILE}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()