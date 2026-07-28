"""Embedding backend for the HR agent.

Defaults to a local ONNX model: it removes one network call from every request
and, more importantly, keeps retrieval working when the OpenAI quota is gone —
FAQ questions can then still be answered without touching the API at all.
Set EMBEDDINGS_BACKEND=openai to go back to text-embedding-3-small.

Vectors are always L2-normalised here, so the squared distance FAISS reports
converts to cosine similarity as cos = 1 - d/2 (see rag_index.search_similar).
"""
import os
import numpy as np

BACKEND       = os.getenv("EMBEDDINGS_BACKEND", "local").lower()
LOCAL_MODEL   = os.getenv(
    "EMBEDDINGS_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
OPENAI_MODEL  = os.getenv("EMBEDDINGS_OPENAI_MODEL", "text-embedding-3-small")
LOCAL_THREADS = int(os.getenv("EMBEDDINGS_THREADS", "1"))

_local_model  = None
_openai_client = None


def _get_local():
    global _local_model
    if _local_model is None:
        from fastembed import TextEmbedding
        _local_model = TextEmbedding(LOCAL_MODEL, threads=LOCAL_THREADS)
    return _local_model


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai_client


def _normalise(vectors) -> np.ndarray:
    arr = np.asarray(vectors, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts. Returns an (n, dim) float32 array, unit-normed."""
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)
    if BACKEND == "local":
        return _normalise(list(_get_local().embed(texts)))
    resp = _get_openai().embeddings.create(input=texts, model=OPENAI_MODEL)
    return _normalise([d.embedding for d in resp.data])


def embed_query(text: str) -> list[float]:
    """Embed one query string, ready to hand to FAISS."""
    return embed_texts([text])[0].tolist()


def describe() -> dict:
    """Identify the active backend so a stale index can be detected on startup."""
    return {
        "backend": BACKEND,
        "model": LOCAL_MODEL if BACKEND == "local" else OPENAI_MODEL,
    }
