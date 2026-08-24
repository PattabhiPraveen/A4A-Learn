import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.rag.ingestion.scanner import scan_documents
from app.rag.ingestion.processor import process_document


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
    print("A4A Learn - RAG Chunk Inspection")
    print("=" * 70)

    print(f"Dataset path: {DATASET_PATH}")
    print(f"Exists: {DATASET_PATH.exists()}")

    documents = scan_documents(
        str(DATASET_PATH)
    )

    print(
        f"Documents discovered: {len(documents)}"
    )

    total_chunks = 0

    for document in documents:

        chunks = process_document(
            document
        )

        total_chunks += len(chunks)

        print()
        print("-" * 70)
        print(f"Document : {document.title}")
        print(f"Chunks   : {len(chunks)}")

        for chunk in chunks[:2]:

            print()
            print(f"Chunk ID : {chunk.chunk_id}")
            print(f"Length   : {len(chunk.text)}")

            print(
                f"Hash     : "
                f"{chunk.metadata.get('content_hash')}"
            )

            print(
                f"Preview  : "
                f"{chunk.text[:250]}"
                .replace("\n", " ")
            )

    print()
    print("=" * 70)
    print(
        f"Total chunks generated: {total_chunks}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()