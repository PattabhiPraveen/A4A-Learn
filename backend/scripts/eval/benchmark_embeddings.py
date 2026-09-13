import json
import math
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

DOCUMENT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS001_Education"
    / "mvp_test"
)

GOLD_FILE = (
    BACKEND_ROOT
    / "tests"
    / "eval"
    / "rag_gold_queries.json"
)

OUTPUT_DIR = (
    BACKEND_ROOT
    / "reports"
    / "eval"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


MODELS = {
    "all-MiniLM-L6-v2":
        "sentence-transformers/all-MiniLM-L6-v2",

    "all-mpnet-base-v2":
        "sentence-transformers/all-mpnet-base-v2",

    "multi-qa-MiniLM-L6-cos-v1":
        "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",

    "BGE-small-en-v1.5":
        "BAAI/bge-small-en-v1.5",

    "E5-small-v2":
        "intfloat/e5-small-v2",
}


TOP_K = 3


def load_documents():

    documents = []

    for path in sorted(
        DOCUMENT_DIR.glob("*.md")
    ):

        documents.append(
            {
                "id": path.stem,
                "text": path.read_text(
                    encoding="utf-8"
                ),
            }
        )

    if not documents:
        raise RuntimeError(
            f"No documents found in {DOCUMENT_DIR}"
        )

    return documents


def load_gold_queries():

    with GOLD_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def cosine_similarity(
    query_vector,
    document_vectors,
):

    query_vector = (
        query_vector
        / np.linalg.norm(query_vector)
    )

    document_vectors = (
        document_vectors
        / np.linalg.norm(
            document_vectors,
            axis=1,
            keepdims=True,
        )
    )

    return np.dot(
        document_vectors,
        query_vector,
    )


def dcg_at_k(relevances, k):

    score = 0.0

    for index, relevance in enumerate(
        relevances[:k],
        start=1,
    ):

        score += relevance / math.log2(
            index + 1
        )

    return score


def evaluate_model(
    model_name,
    model_id,
    documents,
    gold_queries,
):

    print()
    print("=" * 70)
    print(f"Benchmarking: {model_name}")
    print("=" * 70)

    load_start = time.perf_counter()

    model = SentenceTransformer(
        model_id
    )

    load_seconds = (
        time.perf_counter()
        - load_start
    )

    document_texts = [
        document["text"]
        for document in documents
    ]

    document_ids = [
        document["id"]
        for document in documents
    ]

    corpus_start = time.perf_counter()

    document_embeddings = model.encode(
        document_texts,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    corpus_embedding_seconds = (
        time.perf_counter()
        - corpus_start
    )

    query_records = []

    latencies = []

    recall_1_values = []
    recall_3_values = []

    precision_1_values = []
    precision_3_values = []

    reciprocal_ranks = []
    ndcg_3_values = []

    for item in gold_queries:

        query = item["query"]
        expected = item[
            "expected_document"
        ]

        start = time.perf_counter()

        query_embedding = model.encode(
            query,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        similarities = cosine_similarity(
            query_embedding,
            document_embeddings,
        )

        ranked_indices = np.argsort(
            similarities
        )[::-1]

        latency_ms = (
            time.perf_counter()
            - start
        ) * 1000

        latencies.append(
            latency_ms
        )

        ranked_documents = [
            document_ids[index]
            for index in ranked_indices
        ]

        rank = None

        if expected in ranked_documents:
            rank = (
                ranked_documents.index(
                    expected
                )
                + 1
            )

        recall_1 = (
            1.0
            if rank is not None
            and rank <= 1
            else 0.0
        )

        recall_3 = (
            1.0
            if rank is not None
            and rank <= 3
            else 0.0
        )

        # One relevant document per query.
        precision_1 = recall_1

        precision_3 = (
            1.0 / TOP_K
            if rank is not None
            and rank <= TOP_K
            else 0.0
        )

        reciprocal_rank = (
            1.0 / rank
            if rank is not None
            else 0.0
        )

        relevances = [
            1 if document_id == expected else 0
            for document_id
            in ranked_documents
        ]

        actual_dcg = dcg_at_k(
            relevances,
            TOP_K,
        )

        ideal_dcg = dcg_at_k(
            [1],
            TOP_K,
        )

        ndcg = (
            actual_dcg / ideal_dcg
            if ideal_dcg > 0
            else 0.0
        )

        recall_1_values.append(
            recall_1
        )

        recall_3_values.append(
            recall_3
        )

        precision_1_values.append(
            precision_1
        )

        precision_3_values.append(
            precision_3
        )

        reciprocal_ranks.append(
            reciprocal_rank
        )

        ndcg_3_values.append(
            ndcg
        )

        query_records.append(
            {
                "model": model_name,
                "query_id": item["id"],
                "query": query,
                "expected_document": expected,
                "rank": rank,
                "top_1": ranked_documents[0],
                "top_3": " | ".join(
                    ranked_documents[:TOP_K]
                ),
                "latency_ms": round(
                    latency_ms,
                    2,
                ),
            }
        )

    result = {
        "model": model_name,

        "recall_at_1": np.mean(
            recall_1_values
        ),

        "recall_at_3": np.mean(
            recall_3_values
        ),

        "precision_at_1": np.mean(
            precision_1_values
        ),

        "precision_at_3": np.mean(
            precision_3_values
        ),

        "mrr": np.mean(
            reciprocal_ranks
        ),

        "ndcg_at_3": np.mean(
            ndcg_3_values
        ),

        "avg_latency_ms": np.mean(
            latencies
        ),

        "model_load_seconds": (
            load_seconds
        ),

        "corpus_embedding_seconds": (
            corpus_embedding_seconds
        ),
    }

    return result, query_records


def main():

    print("=" * 70)
    print("A4A Learn - Embedding Retrieval Benchmark")
    print("=" * 70)

    documents = load_documents()
    gold_queries = load_gold_queries()

    print(
        f"Documents : {len(documents)}"
    )

    print(
        f"Queries   : {len(gold_queries)}"
    )

    print(
        f"Models    : {len(MODELS)}"
    )

    results = []
    details = []

    for model_name, model_id in MODELS.items():

        try:

            result, records = evaluate_model(
                model_name,
                model_id,
                documents,
                gold_queries,
            )

            results.append(
                result
            )

            details.extend(
                records
            )

        except Exception as exc:

            print()
            print(
                f"FAILED: {model_name}"
            )

            print(
                f"Reason: {exc}"
            )

    if not results:
        raise RuntimeError(
            "No embedding model completed successfully."
        )

    results_df = pd.DataFrame(
        results
    )

    results_df = results_df.sort_values(
        [
            "mrr",
            "ndcg_at_3",
            "avg_latency_ms",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    )

    details_df = pd.DataFrame(
        details
    )

    summary_path = (
        OUTPUT_DIR
        / "embedding_benchmark.csv"
    )

    details_path = (
        OUTPUT_DIR
        / "embedding_query_details.csv"
    )

    results_df.to_csv(
        summary_path,
        index=False,
    )

    details_df.to_csv(
        details_path,
        index=False,
    )

    print()
    print("=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    display_columns = [
        "model",
        "recall_at_1",
        "recall_at_3",
        "precision_at_1",
        "precision_at_3",
        "mrr",
        "ndcg_at_3",
        "avg_latency_ms",
    ]

    print(
        results_df[
            display_columns
        ].to_string(
            index=False
        )
    )

    print()
    print(
        f"Summary : {summary_path}"
    )

    print(
        f"Details : {details_path}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()