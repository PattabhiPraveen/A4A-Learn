import json
import sys
from pathlib import Path

# ---------------------------------------------------------
# Ensure backend root is available for "app.*" imports
# ---------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parents[2]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.service import RAGService


BANK = (
    BACKEND_ROOT
    / "tests"
    / "evaluation"
    / "data"
    / "python_rag_evaluation_v1.json"
)


def load_bank():
    if not BANK.exists():
        raise FileNotFoundError(
            f"Evaluation bank not found: {BANK}"
        )

    with BANK.open(
        "r",
        encoding="utf-8",
    ) as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError(
            "Evaluation bank must contain a JSON list."
        )

    return data


def main():
    print("=" * 80)
    print("A4A LEARN — PYTHON RAG EVALUATION")
    print("=" * 80)
    print(f"Evaluation bank : {BANK}")
    print()

    cases = load_bank()

    print(f"Total questions : {len(cases)}")
    print()

    service = RAGService()

    passed = 0
    failed = 0

    results = []

    for index, case in enumerate(cases, 1):
        test_id = case["test_id"]
        question = case["question"]

        print(
            f"[{index:03d}/{len(cases):03d}] "
            f"{test_id} | {question}"
        )

        try:
            result = service.answer(question)

            grounded = bool(
                result.get("grounded")
            )

            sources = result.get(
                "sources",
                [],
            )

            answer = (
                result.get("answer")
                or ""
            ).strip()

            expected_grounding = bool(
                case.get(
                    "expected_grounding",
                    True,
                )
            )

            citation_required = bool(
                case.get(
                    "citation_required",
                    False,
                )
            )

            citation_present = (
                "[External Source"
                in answer
                or bool(
                    sources
                )
            )

            grounding_ok = (
                grounded
                == expected_grounding
            )

            citation_ok = (
                not citation_required
                or citation_present
            )

            test_passed = (
                grounding_ok
                and citation_ok
                and bool(answer)
            )

            if test_passed:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"

            print(
                f"       {status} | "
                f"grounded={grounded} | "
                f"sources={len(sources)}"
            )

            if not test_passed:
                print(
                    f"       answer={answer[:300]!r}"
                )

            results.append(
                {
                    "test_id": test_id,
                    "category": case.get(
                        "category"
                    ),
                    "question": question,
                    "expected_grounding":
                        expected_grounding,
                    "grounded": grounded,
                    "sources": len(sources),
                    "citation_required":
                        citation_required,
                    "citation_present":
                        citation_present,
                    "passed": test_passed,
                    "answer": answer,
                }
            )

        except Exception as exc:
            failed += 1

            print(
                "       FAIL | "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            results.append(
                {
                    "test_id": test_id,
                    "category": case.get(
                        "category"
                    ),
                    "question": question,
                    "passed": False,
                    "error_type":
                        type(exc).__name__,
                    "error": str(exc),
                }
            )

    print()
    print("=" * 80)
    print("PYTHON RAG EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total : {len(cases)}")
    print(f"PASS  : {passed}")
    print(f"FAIL  : {failed}")

    if cases:
        accuracy = (
            passed
            / len(cases)
            * 100
        )
    else:
        accuracy = 0.0

    print(
        f"Pass rate : {accuracy:.2f}%"
    )

    print()

    failed_results = [
        item
        for item in results
        if not item.get("passed", False)
    ]

    if failed_results:
        print("FAILED TESTS")
        print("-" * 80)

        for item in failed_results:
            print(
                f"{item['test_id']} | "
                f"{item['question']}"
            )

            if "error" in item:
                print(
                    f"  ERROR: "
                    f"{item['error_type']}: "
                    f"{item['error']}"
                )
            else:
                print(
                    f"  grounded="
                    f"{item.get('grounded')}, "
                    f"sources="
                    f"{item.get('sources')}, "
                    f"citation="
                    f"{item.get('citation_present')}"
                )

                print(
                    f"  answer="
                    f"{item.get('answer', '')[:300]!r}"
                )

            print()

    output_path = (
        BACKEND_ROOT
        / "tests"
        / "evaluation"
        / "python_rag_eval_results.json"
    )

    output_path.write_text(
        json.dumps(
            {
                "total": len(cases),
                "passed": passed,
                "failed": failed,
                "pass_rate_percent":
                    round(
                        accuracy,
                        2,
                    ),
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Results written to: "
        f"{output_path}"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()
