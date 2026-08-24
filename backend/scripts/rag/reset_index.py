import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


import chromadb

from app.rag.retrieval.chroma_store import (
    CHROMA_PATH,
    COLLECTION_NAME,
)


def main():

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    try:
        client.delete_collection(
            COLLECTION_NAME
        )

        print(
            f"Deleted collection: "
            f"{COLLECTION_NAME}"
        )

    except Exception:
        print(
            "Collection does not exist. "
            "Nothing to delete."
        )


if __name__ == "__main__":
    main()