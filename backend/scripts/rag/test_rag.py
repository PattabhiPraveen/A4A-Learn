import sys
from pathlib import Path


# Make backend available for imports
BACKEND_ROOT = Path(__file__).resolve().parents[2]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.rag.service import RAGService


def run_test(question: str) -> None:
    """
    Run one end-to-end grounded RAG test.
    """

    rag = RAGService()

    result = rag.answer(question)

    print()
    print("=" * 70)
    print("A4A Learn - Grounded RAG Test")
    print("=" * 70)

    print()
    print(f"Question : {result['question']}")
    print(f"Grounded : {result['grounded']}")

    print()
    print("Answer:")
    print(result["answer"])

    print()
    print("Sources:")

    sources = result.get("sources", [])

    if not sources:
        print("None")
    else:
        for source in sources:
            print(
                f"- {source['title']} "
                f"(distance={source['distance']})"
            )

    print()
    print("=" * 70)


def main() -> None:

    question = (
        "How should a beginner learn Indian Sign Language?"
    )

    run_test(question)


if __name__ == "__main__":
    main()