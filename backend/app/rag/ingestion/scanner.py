from pathlib import Path

from app.rag.ingestion.loader import (
    SUPPORTED_EXTENSIONS,
    load_document,
)


def scan_documents(
    dataset_path: str,
):
   # dataset_path = Path("datasets/raw")

    root = Path(dataset_path)

    if not root.exists():
        raise FileNotFoundError(
            f"Dataset path does not exist: {root}"
        )

    documents = []

    for path in root.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            document = load_document(path)

            if document.content.strip():
                documents.append(document)

        except Exception as exc:
            print(
                f"Skipping {path}: {exc}"
            )

    return documents