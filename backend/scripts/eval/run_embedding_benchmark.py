import argparse
import math
import statistics
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

BENCHMARK_ROOT = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "evaluation"
    / "retrieval_v1"
)

CORPUS_DIR = BENCHMARK_ROOT / "corpus"

QUESTION_FILE = (
    BENCHMARK_ROOT
    / "benchmark_questions_v1.csv"
)

REPORT_DIR = (
    BACKEND_ROOT
    / "reports"
    / "eval"
    / "embedding_benchmark"
)


# ----------------------------------------------------------------------
# Frozen benchmark methodology
# ----------------------------------------------------------------------

CHUNK_SIZE_WORDS = 500
CHUNK_OVERLAP_WORDS = 75
TOP_K_CHUNKS = 20
TOP_K_DOCS = 5


MODEL_MAP = {
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
    "multiqa": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
    "bge": "BAAI/bge-small-en-v1.5",
    "bge_instructed": "BAAI/bge-small-en-v1.5",
    "e5": "intfloat/e5-small-v2",
}


def chunk_text(text, chunk_size, overlap):
    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = min(
            start + chunk_size,
            len(words),
        )

        chunks.append(
            " ".join(words[start:end])
        )

        if end == len(words):
            break

        start = end - overlap

    return chunks


def load_corpus():
    rows = []

    for file in sorted(
        CORPUS_DIR.glob("DOC*.md")
    ):
        doc_id = file.stem

        text = file.read_text(
            encoding="utf-8"
        )

        chunks = chunk_text(
            text,
            CHUNK_SIZE_WORDS,
            CHUNK_OVERLAP_WORDS,
        )

        for index, chunk in enumerate(chunks):
            rows.append(
                {
                    "document_id": doc_id,
                    "chunk_id": (
                        f"{doc_id}_C{index + 1:03d}"
                    ),
                    "text": chunk,
                }
            )

    return pd.DataFrame(rows)


def prepare_text(
    text,
    model_key,
    is_query=False,
):
    # E5 retrieval convention:
    # query text receives "query:" and
    # corpus text receives "passage:".
    if model_key == "e5":
        prefix = (
            "query: "
            if is_query
            else "passage: "
        )
        return prefix + text

    # BGE instructed-query experiment.
    # Corpus passages remain unchanged.
    if (
        model_key == "bge_instructed"
        and is_query
    ):
        return (
            "Represent this sentence for searching "
            "relevant passages: "
            + text
        )

    return text


def cosine_scores(
    query_vector,
    corpus_matrix,
):
    query_norm = np.linalg.norm(
        query_vector
    )

    corpus_norms = np.linalg.norm(
        corpus_matrix,
        axis=1,
    )

    denominator = (
        corpus_norms * query_norm
    )

    denominator[
        denominator == 0
    ] = 1e-12

    return (
        corpus_matrix @ query_vector
    ) / denominator


def deduplicate_to_documents(
    scores,
    corpus_df,
):
    order = np.argsort(
        scores
    )[::-1]

    results = []
    seen = set()

    # Preserve the methodology used for the
    # original five benchmark runs.
    for index in order[:TOP_K_CHUNKS]:
        doc_id = corpus_df.iloc[
            index
        ]["document_id"]

        if doc_id in seen:
            continue

        seen.add(doc_id)

        results.append(
            {
                "document_id": doc_id,
                "score": float(
                    scores[index]
                ),
            }
        )

        if len(results) >= TOP_K_DOCS:
            break

    return results


def reciprocal_rank(
    ranked_docs,
    expected_doc,
):
    for rank, doc in enumerate(
        ranked_docs,
        start=1,
    ):
        if doc == expected_doc:
            return 1.0 / rank

    return 0.0


def ndcg_at_k(
    ranked_docs,
    expected_doc,
    k,
):
    for rank, doc in enumerate(
        ranked_docs[:k],
        start=1,
    ):
        if doc == expected_doc:
            return 1.0 / math.log2(
                rank + 1
            )

    return 0.0


def percentile(
    values,
    percentile_value,
):
    return float(
        np.percentile(
            values,
            percentile_value,
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "A4A Learn embedding retrieval benchmark"
        )
    )

    parser.add_argument(
        "--model",
        required=True,
        choices=MODEL_MAP.keys(),
    )

    args = parser.parse_args()

    model_key = args.model
    model_name = MODEL_MAP[
        model_key
    ]

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 72)
    print(
        "A4A Learn - Embedding Benchmark"
    )
    print("=" * 72)
    print(f"Model : {model_name}")

    corpus_df = load_corpus()

    if corpus_df.empty:
        raise RuntimeError(
            f"No corpus files found in: "
            f"{CORPUS_DIR}"
        )

    if not QUESTION_FILE.exists():
        raise FileNotFoundError(
            f"Question file not found: "
            f"{QUESTION_FILE}"
        )

    questions_df = pd.read_csv(
        QUESTION_FILE,
        encoding="utf-8",
    )

    print(
        f"Documents : "
        f"{corpus_df['document_id'].nunique()}"
    )

    print(
        f"Chunks    : {len(corpus_df)}"
    )

    print(
        f"Questions : {len(questions_df)}"
    )

    print()
    print("Loading model...")

    model = SentenceTransformer(
        model_name
    )

    # Warm-up before latency measurement.
    _ = model.encode(
        [
            prepare_text(
                "warm up query",
                model_key,
                is_query=True,
            )
        ],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    print("Embedding corpus...")

    corpus_texts = [
        prepare_text(
            text,
            model_key,
            is_query=False,
        )
        for text in corpus_df["text"]
    ]

    corpus_start = time.perf_counter()

    corpus_embeddings = model.encode(
        corpus_texts,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    corpus_embedding_seconds = (
        time.perf_counter()
        - corpus_start
    )

    dimensions = (
        corpus_embeddings.shape[1]
    )

    rows = []

    query_latencies = []
    retrieval_latencies = []

    print()
    print(
        f"Running {len(questions_df)} queries..."
    )

    for number, row in enumerate(
        questions_df.itertuples(
            index=False
        ),
        start=1,
    ):
        query_text = prepare_text(
            row.question,
            model_key,
            is_query=True,
        )

        start = time.perf_counter()

        query_embedding = model.encode(
            [query_text],
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )[0]

        query_ms = (
            time.perf_counter()
            - start
        ) * 1000

        query_latencies.append(
            query_ms
        )

        start = time.perf_counter()

        scores = cosine_scores(
            query_embedding,
            corpus_embeddings,
        )

        ranked = (
            deduplicate_to_documents(
                scores,
                corpus_df,
            )
        )

        retrieval_ms = (
            time.perf_counter()
            - start
        ) * 1000

        retrieval_latencies.append(
            retrieval_ms
        )

        ranked_docs = [
            item["document_id"]
            for item in ranked
        ]

        expected = row.document_id

        rank = None

        if expected in ranked_docs:
            rank = (
                ranked_docs.index(
                    expected
                )
                + 1
            )

        rows.append(
            {
                "question_id":
                    row.question_id,
                "expected_document":
                    expected,
                "rank":
                    rank,
                "top1":
                    (
                        ranked_docs[0]
                        if ranked_docs
                        else ""
                    ),
                "top3":
                    "|".join(
                        ranked_docs[:3]
                    ),
                "top5":
                    "|".join(
                        ranked_docs[:5]
                    ),
                "recall_at_1":
                    int(
                        expected
                        in ranked_docs[:1]
                    ),
                "recall_at_3":
                    int(
                        expected
                        in ranked_docs[:3]
                    ),
                "recall_at_5":
                    int(
                        expected
                        in ranked_docs[:5]
                    ),
                "precision_at_1":
                    (
                        1.0
                        if expected
                        in ranked_docs[:1]
                        else 0.0
                    ),
                "precision_at_3":
                    (
                        1.0 / 3.0
                        if expected
                        in ranked_docs[:3]
                        else 0.0
                    ),
                "precision_at_5":
                    (
                        1.0 / 5.0
                        if expected
                        in ranked_docs[:5]
                        else 0.0
                    ),
                "mrr":
                    reciprocal_rank(
                        ranked_docs,
                        expected,
                    ),
                "ndcg_at_3":
                    ndcg_at_k(
                        ranked_docs,
                        expected,
                        3,
                    ),
                "ndcg_at_5":
                    ndcg_at_k(
                        ranked_docs,
                        expected,
                        5,
                    ),
                "query_latency_ms":
                    query_ms,
                "retrieval_latency_ms":
                    retrieval_ms,
            }
        )

        if (
            number % 100 == 0
            or number == 1
        ):
            print(
                f"{number:04d}/"
                f"{len(questions_df)}"
            )

    result_df = pd.DataFrame(
        rows
    )

    detail_file = (
        REPORT_DIR
        / f"{model_key}_details.csv"
    )

    result_df.to_csv(
        detail_file,
        index=False,
        encoding="utf-8",
    )

    summary = {
        "model_key":
            model_key,
        "model_name":
            model_name,
        "documents":
            int(
                corpus_df[
                    "document_id"
                ].nunique()
            ),
        "chunks":
            len(corpus_df),
        "questions":
            len(questions_df),
        "embedding_dimension":
            dimensions,
        "chunk_size_words":
            CHUNK_SIZE_WORDS,
        "chunk_overlap_words":
            CHUNK_OVERLAP_WORDS,
        "recall_at_1":
            result_df[
                "recall_at_1"
            ].mean(),
        "recall_at_3":
            result_df[
                "recall_at_3"
            ].mean(),
        "recall_at_5":
            result_df[
                "recall_at_5"
            ].mean(),
        "precision_at_1":
            result_df[
                "precision_at_1"
            ].mean(),
        "precision_at_3":
            result_df[
                "precision_at_3"
            ].mean(),
        "precision_at_5":
            result_df[
                "precision_at_5"
            ].mean(),
        "mrr":
            result_df[
                "mrr"
            ].mean(),
        "ndcg_at_3":
            result_df[
                "ndcg_at_3"
            ].mean(),
        "ndcg_at_5":
            result_df[
                "ndcg_at_5"
            ].mean(),
        "query_latency_avg_ms":
            statistics.mean(
                query_latencies
            ),
        "query_latency_p50_ms":
            percentile(
                query_latencies,
                50,
            ),
        "query_latency_p95_ms":
            percentile(
                query_latencies,
                95,
            ),
        "retrieval_latency_avg_ms":
            statistics.mean(
                retrieval_latencies
            ),
        "retrieval_latency_p50_ms":
            percentile(
                retrieval_latencies,
                50,
            ),
        "retrieval_latency_p95_ms":
            percentile(
                retrieval_latencies,
                95,
            ),
        "corpus_embedding_seconds":
            corpus_embedding_seconds,
    }

    summary_df = pd.DataFrame(
        [summary]
    )

    summary_file = (
        REPORT_DIR
        / f"{model_key}_summary.csv"
    )

    summary_df.to_csv(
        summary_file,
        index=False,
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("BENCHMARK RESULT")
    print("=" * 72)

    print(
        f"Recall@1     : "
        f"{summary['recall_at_1']:.4f}"
    )

    print(
        f"Recall@3     : "
        f"{summary['recall_at_3']:.4f}"
    )

    print(
        f"Recall@5     : "
        f"{summary['recall_at_5']:.4f}"
    )

    print(
        f"MRR          : "
        f"{summary['mrr']:.4f}"
    )

    print(
        f"NDCG@3       : "
        f"{summary['ndcg_at_3']:.4f}"
    )

    print(
        f"NDCG@5       : "
        f"{summary['ndcg_at_5']:.4f}"
    )

    print(
        f"Query P50 ms : "
        f"{summary['query_latency_p50_ms']:.2f}"
    )

    print(
        f"Query P95 ms : "
        f"{summary['query_latency_p95_ms']:.2f}"
    )

    print(
        f"Search P50 ms: "
        f"{summary['retrieval_latency_p50_ms']:.2f}"
    )

    print(
        f"Search P95 ms: "
        f"{summary['retrieval_latency_p95_ms']:.2f}"
    )

    print(
        f"Dimension    : {dimensions}"
    )

    print(
        f"Details      : {detail_file}"
    )

    print(
        f"Summary      : {summary_file}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()