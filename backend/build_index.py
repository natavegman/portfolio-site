"""
Build the FAISS vector index from FAQ and CV data files.
Run once before starting the backend:
    python backend/build_index.py
"""
import os, sys, json, re
import numpy as np
import faiss
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

sys.path.insert(0, os.path.dirname(__file__))
import embeddings

DATA_DIR   = os.path.join(os.path.dirname(__file__), '..', 'data')
INDEX_PATH = os.path.join(DATA_DIR, 'faiss_index.bin')
META_PATH  = os.path.join(DATA_DIR, 'faiss_metadata.npy')
INFO_PATH  = os.path.join(DATA_DIR, 'faiss_info.json')


def load_faq(filename, lang):
    with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
        items = json.load(f)
    return [
        {"question": it["question"], "answer": it["answer"], "lang": lang, "source": "faq"}
        for it in items
    ]


def load_cv_chunks(filename, lang):
    with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = []
    # Split at every markdown heading
    parts = re.split(r'\n(?=#{1,3} )', content.strip())
    for part in parts:
        lines = part.strip().split('\n')
        title = lines[0].lstrip('#').strip()
        body  = '\n'.join(lines[1:]).strip()
        if title and body:
            chunks.append({
                "question": title,
                "answer":   body,
                "lang":     lang,
                "source":   "cv"
            })
    return chunks


def embed_batch(texts):
    return embeddings.embed_texts(texts)


def main():
    items = (
        load_faq('faq_en.json', 'en') +
        load_faq('faq_ru.json', 'ru') +
        load_cv_chunks('cv_en.md', 'en') +
        load_cv_chunks('cv_ru.md', 'ru')
    )
    # Every item is indexed twice: once as question+answer (good context for the
    # LLM) and once as the bare question. The question-only vector is what makes
    # the FAQ shortcut possible — matching a visitor's short question against a
    # long question+answer chunk tops out around 0.4 similarity, far too low to
    # separate a real hit from a near miss.
    items = [it | {"vector_kind": "full"} for it in items] + [
        it | {"vector_kind": "question"} for it in items if it["source"] == "faq"
    ]
    print(f"Loaded {len(items)} vectors "
          f"({sum(1 for i in items if i['vector_kind'] == 'question')} question-only)")

    texts = [
        it["question"] if it["vector_kind"] == "question"
        else f"{it['question']}\n\n{it['answer']}"
        for it in items
    ]

    batches = []
    batch_size = 50
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Embedding {i+1}–{i+len(batch)}...")
        batches.append(embed_batch(batch))

    mat = np.vstack(batches).astype(np.float32)
    dim = mat.shape[1]

    idx = faiss.IndexFlatL2(dim)
    idx.add(mat)

    faiss.write_index(idx, INDEX_PATH)
    np.save(META_PATH, np.array(items, dtype=object))

    # Lets the API refuse to serve an index built by a different embedder —
    # mismatched vectors would silently return nonsense instead of failing.
    info = embeddings.describe() | {"dim": dim, "vectors": len(items)}
    with open(INFO_PATH, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(items)} vectors, dim={dim}, backend={info['backend']} ({info['model']})")
    print(f"  Index → {INDEX_PATH}")
    print(f"  Meta  → {META_PATH}")
    print(f"  Info  → {INFO_PATH}")


if __name__ == '__main__':
    main()
