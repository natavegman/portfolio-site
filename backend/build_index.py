"""
Build the FAISS vector index from FAQ and CV data files.
Run once before starting the backend:
    python backend/build_index.py
"""
import os, json, re
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

DATA_DIR   = os.path.join(os.path.dirname(__file__), '..', 'data')
INDEX_PATH = os.path.join(DATA_DIR, 'faiss_index.bin')
META_PATH  = os.path.join(DATA_DIR, 'faiss_metadata.npy')


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
    resp = client.embeddings.create(input=texts, model="text-embedding-3-small")
    return [d.embedding for d in resp.data]


def main():
    items = (
        load_faq('faq_en.json', 'en') +
        load_faq('faq_ru.json', 'ru') +
        load_cv_chunks('cv_en.md', 'en') +
        load_cv_chunks('cv_ru.md', 'ru')
    )
    print(f"Loaded {len(items)} items total")

    texts = [f"{it['question']}\n\n{it['answer']}" for it in items]

    all_embeddings = []
    batch_size = 50
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Embedding {i+1}–{i+len(batch)}...")
        all_embeddings.extend(embed_batch(batch))

    dim = len(all_embeddings[0])
    mat = np.array(all_embeddings, dtype=np.float32)

    idx = faiss.IndexFlatL2(dim)
    idx.add(mat)

    faiss.write_index(idx, INDEX_PATH)
    np.save(META_PATH, np.array(items, dtype=object))

    print(f"\nDone! {len(items)} vectors, dim={dim}")
    print(f"  Index → {INDEX_PATH}")
    print(f"  Meta  → {META_PATH}")


if __name__ == '__main__':
    main()
