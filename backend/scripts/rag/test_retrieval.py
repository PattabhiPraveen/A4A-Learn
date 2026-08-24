import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.rag.retrieval.retriever import Retriever


def main():

    retriever = Retriever(
        top_k=3
    )

    query = (
        "How can deaf students "
        "learn Indian Sign Language?"
    )

    results = retriever.retrieve(
        query
    )

    print()
    print("=" * 70)
    print("A4A Learn - Retrieval Test")
    print("=" * 70)

    print(
        f"Query: {query}"
    )

    print(
        f"Results: {len(results)}"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        print()
        print(
            f"--- Result {index} ---"
        )

        print(
            f"Distance: "
            f"{result['distance']}"
        )

        print(
            f"Source: "
            f"{result['metadata'].get('source')}"
        )

        print(
            f"Text: "
            f"{result['text'][:500]}"
        )


if __name__ == "__main__":
    main()