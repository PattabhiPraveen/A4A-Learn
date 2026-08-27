import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.rag.generation.rag_service import (
    RAGService,
    INSUFFICIENT_CONTEXT_MESSAGE,
)


TEST_CASES = [
    {
        "id": "Q01",
        "question": "What is Indian Sign Language?",
        "expected": "accept",
        "expected_source": "lesson_01",
    },
    {
        "id": "Q02",
        "question": "How should a learner begin learning Indian Sign Language?",
        "expected": "accept",
        "expected_source": "lesson_02",
    },
    {
        "id": "Q03",
        "question": "Why is visual observation important when learning signs?",
        "expected": "accept",
        "expected_source": "lesson_02",
    },
    {
        "id": "Q04",
        "question": "How does sign language communicate information?",
        "expected": "accept",
        "expected_source": "lesson_01",
    },
    {
        "id": "Q05",
        "question": "What can make digital learning accessible for deaf learners?",
        "expected": "accept",
        "expected_source": "lesson_03",
    },

    # Out-of-domain questions
    {
        "id": "Q06",
        "question": "Explain the architecture of a nuclear reactor.",
        "expected": "reject",
        "expected_source": None,
    },
    {
        "id": "Q07",
        "question": "How does PostgreSQL replication work?",
        "expected": "reject",
        "expected_source": None,
    },
    {
        "id": "Q08",
        "question": "How does an aircraft engine generate thrust?",
        "expected": "reject",
        "expected_source": None,
    },
    {
        "id": "Q09",
        "question": "Explain blockchain consensus mechanisms.",
        "expected": "reject",
        "expected_source": None,
    },
    {
        "id": "Q10",
        "question": "What is quantum entanglement?",
        "expected": "reject",
        "expected_source": None,
    },
]


def source_matches(
    sources,
    expected_source,
):
    if expected_source is None:
        return len(sources) == 0

    return any(
        expected_source.lower()
        in source.source.lower()
        for source in sources
    )


def main():

    service = RAGService(
        top_k=3,
        max_distance=0.90,
    )

    passed = 0

    print()
    print("=" * 78)
    print("A4A Learn - T17 Groundedness / Hallucination Evaluation")
    print("=" * 78)

    for test in TEST_CASES:

        result = service.ask(
            test["question"]
        )

        refused = (
            result.answer
            == INSUFFICIENT_CONTEXT_MESSAGE
        )

        if test["expected"] == "accept":

            behaviour_ok = (
                not refused
                and len(result.sources) > 0
            )

            source_ok = source_matches(
                result.sources,
                test["expected_source"],
            )

            test_pass = (
                behaviour_ok
                and source_ok
            )

        else:

            behaviour_ok = (
                refused
                and len(result.sources) == 0
            )

            source_ok = (
                len(result.sources) == 0
            )

            test_pass = behaviour_ok

        if test_pass:
            passed += 1

        print()
        print("-" * 78)

        print(
            f"{test['id']} | "
            f"Expected: {test['expected'].upper()}"
        )

        print(
            f"Question: {test['question']}"
        )

        print(
            f"Decision: "
            f"{'REJECT' if refused else 'ACCEPT'}"
        )

        print(
            f"Source count: "
            f"{len(result.sources)}"
        )

        for index, source in enumerate(
            result.sources,
            start=1,
        ):
            print(
                f"  Source {index}: "
                f"{source.source}"
            )

            print(
                f"  Distance : "
                f"{source.distance:.4f}"
            )

        print(
            f"Expected source: "
            f"{test['expected_source']}"
        )

        print(
            f"Source check: "
            f"{'PASS' if source_ok else 'FAIL'}"
        )

        print()
        print("Answer:")
        print(result.answer)

        print()
        print(
            f"RESULT: "
            f"{'PASS' if test_pass else 'FAIL'}"
        )

    total = len(TEST_CASES)

    accuracy = (
        passed / total * 100
        if total
        else 0
    )

    print()
    print("=" * 78)
    print("T17 SUMMARY")
    print("=" * 78)

    print(
        f"Total tests : {total}"
    )

    print(
        f"Passed      : {passed}"
    )

    print(
        f"Failed      : {total - passed}"
    )

    print(
        f"Accuracy    : {accuracy:.2f}%"
    )

    print(
        "T17 STATUS  : "
        + (
            "PASS"
            if passed == total
            else "REVIEW REQUIRED"
        )
    )


if __name__ == "__main__":
    main()