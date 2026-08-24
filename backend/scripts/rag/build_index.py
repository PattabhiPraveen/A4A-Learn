import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.rag.ingestion.scanner import scan_documents
from app.rag.ingestion.processor import process_document
from app.rag.retrieval.chroma_store import ChromaStore


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASET_PATH = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS001_Education"
    / "mvp_test"
)


def main():

    print()
    print("=" * 70)
    print("A4A Learn - Build RAG Vector Index")
    print("=" * 70)

    documents = scan_documents(
        str(DATASET_PATH)
    )

    print(
        f"Documents discovered: {len(documents)}"
    )

    all_chunks = []

    for document in documents:

        chunks = process_document(
            document
        )

        all_chunks.extend(chunks)

        print(
            f"Processed: {document.title} "
            f"→ {len(chunks)} chunks"
        )

    print()
    print(
        f"Total chunks: {len(all_chunks)}"
    )

    store = ChromaStore()

    inserted = store.add_chunks(
        all_chunks
    )

    print(
        f"Chunks indexed: {inserted}"
    )

    print(
        f"ChromaDB collection count: "
        f"{store.count()}"
    )

    print()
    print("=" * 70)
    print("Vector indexing completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()