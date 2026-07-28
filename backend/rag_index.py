import os
import faiss
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
INDEX_PATH = os.path.join(DATA_DIR, 'faiss_index.bin')
META_PATH  = os.path.join(DATA_DIR, 'faiss_metadata.npy')


def load_index():
    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        raise RuntimeError(
            "FAISS index not found. Run: python backend/build_index.py"
        )
    index    = faiss.read_index(INDEX_PATH)
    metadata = np.load(META_PATH, allow_pickle=True).tolist()
    return index, metadata


def search_similar(index, metadata, query_vec, k=3, lang=None, kind=None):
    """Return the k closest items, each carrying a `similarity` field in [0, 1].

    Vectors are unit-normalised, so the squared L2 distance FAISS reports maps
    back to cosine similarity as cos = 1 - d/2. Callers use it to decide whether
    a hit is close enough to answer from directly, without asking the LLM.

    `kind` filters on how the item was embedded: 'full' (question + answer, the
    right context to hand the LLM) or 'question' (bare question, which is what
    the FAQ shortcut compares against). None searches both.
    """
    vec = np.array([query_vec], dtype=np.float32)
    # Fetch extra candidates so filtering by lang/kind still returns k results
    search_k = min(k * 12, index.ntotal)
    distances, indices = index.search(vec, search_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        item = metadata[idx]
        if lang and item.get('lang') != lang:
            continue
        if kind and item.get('vector_kind', 'full') != kind:
            continue
        hit = dict(item)
        hit['similarity'] = round(float(1.0 - dist / 2.0), 4)
        results.append(hit)
        if len(results) >= k:
            break
    return results
