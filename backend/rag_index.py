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


def search_similar(index, metadata, query_vec, k=3, lang=None):
    vec = np.array([query_vec], dtype=np.float32)
    # Fetch extra candidates so filtering by lang still returns k results
    search_k = min(k * 6, index.ntotal)
    distances, indices = index.search(vec, search_k)

    results = []
    for idx in indices[0]:
        if idx < 0 or idx >= len(metadata):
            continue
        item = metadata[idx]
        if lang and item.get('lang') != lang:
            continue
        results.append(item)
        if len(results) >= k:
            break
    return results
