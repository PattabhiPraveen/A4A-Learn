import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.ingestion.scanner import scan_documents


# ---------------------------------------------------------
# Project root
# inspect_documents.py
#   -> rag
#   -> scripts
#   -> backend
#   -> A4A-Learn
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASET_PATH = PROJECT_ROOT / "datasets" / "raw"


def main():

    print()
    print("=" * 60)
    print("A4A Learn - RAG Dataset Inspection")
    print("=" * 60)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Dataset path : {DATASET_PATH}")
    print(f"Exists       : {DATASET_PATH.exists()}")

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset path does not exist: {DATASET_PATH}"
        )

    documents = scan_documents(
        str(DATASET_PATH)
    )

    print()
    print(f"Documents discovered: {len(documents)}")

    for document in documents:

        print()
        print(f"ID         : {document.document_id}")
        print(f"Title      : {document.title}")
        print(f"Source     : {document.source}")
        print(f"Characters : {len(document.content)}")

        preview = (
            document.content[:300]
            .replace("\n", " ")
        )

        print(f"Preview    : {preview}")

    print()
    print("=" * 60)
    print("Dataset inspection completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()