import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.rag.generation.rag_service import RAGService


def print_result(
    title: str,
    question: str,
    service: RAGService,
):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    result = service.ask(
        question
    )

    print(f"Question: {result.question}")

    print()
    print("Answer:")
    print(result.answer)

    print()
    print(
        f"Sources: {len(result.sources)}"
    )

    for index, source in enumerate(
        result.sources,
        start=1,
    ):
        print(
            f"{index}. {source.source} "
            f"(distance={source.distance:.4f})"
        )


def main():

    service = RAGService(
        top_k=3,
        max_distance=0.85,
    )

    print_result(
        title="TEST 1 - GROUNDED QUESTION",
        question=(
            "How can deaf students "
            "learn Indian Sign Language?"
        ),
        service=service,
    )

    print_result(
        title="TEST 2 - OUT-OF-KNOWLEDGE QUESTION",
        question=(
            "Explain the architecture "
            "of a nuclear reactor."
        ),
        service=service,
    )


if __name__ == "__main__":
    main()