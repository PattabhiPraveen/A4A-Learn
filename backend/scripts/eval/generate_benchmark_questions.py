import csv
import json
import re
import time
from pathlib import Path

import requests


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

DOCUMENT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS001_Education"
    / "benchmark_100"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "evaluation"
    / "questions"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "benchmark_questions.csv"
)

LOG_FILE = (
    OUTPUT_DIR
    / "question_generation_log.csv"
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

QUESTIONS_PER_DOCUMENT = 10


def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.4,
            "top_p": 0.9,
        },
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300,
    )

    response.raise_for_status()

    data = response.json()

    return data["response"].strip()


def build_prompt(
    document_id: str,
    document_text: str,
) -> str:
    return f"""
You are creating retrieval-evaluation questions
for an educational semantic-search benchmark.

SOURCE DOCUMENT ID:
{document_id}

SOURCE DOCUMENT:
----------------
{document_text}
----------------

Create exactly {QUESTIONS_PER_DOCUMENT}
different questions whose answers can be found
from this source document.

Question design requirements:

1. Questions must be answerable from the source.
2. Do not invent facts beyond the source.
3. Do not mention the document ID.
4. Do not use phrases such as:
   "according to the document"
   or
   "in the passage".
5. Questions must sound like natural learner queries.
6. Avoid yes/no questions.
7. Avoid duplicate questions.
8. Avoid simply copying section headings.
9. Include a mixture of:
   - factual questions
   - conceptual questions
   - application questions
   - comparison questions
10. Each question should primarily retrieve
    this source document.

Return ONLY valid JSON in exactly this structure:

{{
  "questions": [
    {{
      "question": "Question text",
      "question_type": "factual"
    }}
  ]
}}

Allowed question_type values:

factual
conceptual
application
comparison

Return exactly 10 questions.
"""


def normalize_question(text: str) -> str:
    text = text.lower().strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def load_existing_questions():
    if not OUTPUT_FILE.exists():
        return []

    with OUTPUT_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def write_questions(rows):
    fieldnames = [
        "question_id",
        "document_id",
        "question",
        "question_type",
        "validation_status",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def load_log():
    if not LOG_FILE.exists():
        return {}

    with LOG_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    return {
        row["document_id"]: row
        for row in rows
    }


def write_log(log_rows):
    fieldnames = [
        "document_id",
        "status",
        "question_count",
        "attempts",
        "message",
    ]

    with LOG_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            log_rows.values()
        )


def validate_questions(items):
    errors = []

    if len(items) != QUESTIONS_PER_DOCUMENT:
        errors.append(
            f"Expected 10 questions, "
            f"found {len(items)}"
        )

        return errors

    allowed_types = {
        "factual",
        "conceptual",
        "application",
        "comparison",
    }

    type_aliases = {
        "comparison/explanation": "comparison",
        "explanation": "conceptual",
        "compare": "comparison",
        "comparative": "comparison",
    }

    normalized = []

    for index, item in enumerate(
        items,
        start=1,
    ):
        question = (
            item.get("question", "")
            .strip()
        )

        question_type = (
            item.get(
                "question_type",
                "",
            )
            .strip()
            .lower()
        )

        # -----------------------------------------
        # Normalize harmless formatting variations
        # -----------------------------------------

        if question and not question.endswith("?"):
            question = (
                question.rstrip(".!")
                + "?"
            )

            item["question"] = question

        question_type = type_aliases.get(
            question_type,
            question_type,
        )

        item["question_type"] = (
            question_type
        )

        # -----------------------------------------
        # Validation
        # -----------------------------------------

        if not question:
            errors.append(
                f"Question {index} is empty"
            )

        if len(question.split()) < 4:
            errors.append(
                f"Question {index} too short"
            )

        if not question.endswith("?"):
            errors.append(
                f"Question {index} "
                f"does not end with ?"
            )

        if (
            question_type
            not in allowed_types
        ):
            errors.append(
                f"Question {index} "
                f"invalid type: "
                f"{question_type}"
            )

        normalized.append(
            normalize_question(question)
        )

    if (
        len(set(normalized))
        != len(normalized)
    ):
        errors.append(
            "Duplicate questions detected "
            "within document"
        )

    return errors


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = sorted(
        DOCUMENT_DIR.glob("DOC*.md")
    )

    if len(files) != 100:
        raise ValueError(
            f"Expected 100 documents, "
            f"found {len(files)}"
        )

    all_questions = (
        load_existing_questions()
    )

    log_rows = load_log()

    print("=" * 70)
    print(
        "A4A Learn - Benchmark Question Generator"
    )
    print("=" * 70)

    completed = 0
    skipped = 0
    failed = 0

    for index, path in enumerate(
        files,
        start=1,
    ):
        document_id = path.stem

        print()
        print(
            f"[{index}/100] "
            f"{document_id}"
        )

        existing_log = log_rows.get(
            document_id
        )

        existing_count = sum(
            1
            for row in all_questions
            if row["document_id"]
            == document_id
        )

        # -----------------------------------------
        # Checkpoint / resume logic
        # -----------------------------------------

        if (
            existing_log
            and existing_log.get("status")
            == "PASS"
            and existing_count
            == QUESTIONS_PER_DOCUMENT
        ):
            print(
                "SKIP - already generated"
            )

            skipped += 1
            continue

        document_text = (
            path.read_text(
                encoding="utf-8"
            )
        )

        success = False
        validation_errors = []
        items = []

        # -----------------------------------------
        # Retry generation up to 3 times
        # -----------------------------------------

        for attempt in range(
            1,
            4,
        ):
            print(
                f"Attempt {attempt}/3"
            )

            try:
                prompt = build_prompt(
                    document_id,
                    document_text,
                )

                response = call_ollama(
                    prompt
                )

                parsed = json.loads(
                    response
                )

                items = parsed.get(
                    "questions",
                    [],
                )

                validation_errors = (
                    validate_questions(
                        items
                    )
                )

                if not validation_errors:
                    success = True
                    break

                print(
                    "Validation issues:"
                )

                for error in (
                    validation_errors
                ):
                    print(
                        f"  - {error}"
                    )

            except Exception as exc:
                validation_errors = [
                    str(exc)
                ]

                print(
                    f"Generation error: "
                    f"{exc}"
                )

            time.sleep(1)

        # -----------------------------------------
        # Remove any old failed questions for this
        # document before replacement
        # -----------------------------------------

        all_questions = [
            row
            for row in all_questions
            if row["document_id"]
            != document_id
        ]

        # -----------------------------------------
        # Save successful questions
        # -----------------------------------------

        if success:
            for number, item in enumerate(
                items,
                start=1,
            ):
                question_id = (
                    f"Q{document_id[3:]}"
                    f"_{number:02d}"
                )

                all_questions.append(
                    {
                        "question_id":
                            question_id,
                        "document_id":
                            document_id,
                        "question":
                            item[
                                "question"
                            ].strip(),
                        "question_type":
                            item[
                                "question_type"
                            ]
                            .strip()
                            .lower(),
                        "validation_status":
                            "pending",
                    }
                )

            log_rows[
                document_id
            ] = {
                "document_id":
                    document_id,
                "status":
                    "PASS",
                "question_count":
                    10,
                "attempts":
                    attempt,
                "message":
                    "",
            }

            completed += 1

            print(
                "PASS - 10 questions"
            )

        else:
            log_rows[
                document_id
            ] = {
                "document_id":
                    document_id,
                "status":
                    "FAIL",
                "question_count":
                    0,
                "attempts":
                    3,
                "message":
                    " | ".join(
                        validation_errors
                    ),
            }

            failed += 1

            print(
                "FAIL"
            )

        # -----------------------------------------
        # Checkpoint after every document
        # -----------------------------------------

        write_questions(
            all_questions
        )

        write_log(
            log_rows
        )

    print()
    print("=" * 70)
    print(
        "GENERATION SUMMARY"
    )
    print("=" * 70)

    print(
        f"Completed documents : "
        f"{completed}"
    )

    print(
        f"Skipped documents   : "
        f"{skipped}"
    )

    print(
        f"Failed documents    : "
        f"{failed}"
    )

    print(
        f"Total questions     : "
        f"{len(all_questions)}"
    )

    print(
        f"Output              : "
        f"{OUTPUT_FILE}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()