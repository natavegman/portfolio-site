"""Measure FAQ-shortcut behaviour so FAQ_SHORTCUT_SIMILARITY is set from data,
not from a guess.

Run:  venv/bin/python tools/tune_threshold.py

Prints, for a set of hand-written visitor questions, the top retrieval hit and
its similarity. `expect` says which FAQ index should win, or None when the
question is deliberately off-topic and must NOT trigger the shortcut.
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from rag_index import load_index, search_similar
import embeddings

# (question, lang, expected FAQ question index or None for off-topic)
CASES = [
    # near-verbatim — must shortcut
    ("Какое у вас образование?",                          "ru", 10),
    ("Что такое проект MyFamilyTree?",                    "ru", 9),
    ("What is your educational background?",              "en", 10),
    # natural paraphrases — the interesting middle ground
    ("Где вы учились?",                                   "ru", 10),
    ("Расскажите про образование",                        "ru", 10),
    ("С какими технологиями вы работаете?",               "ru", 2),
    ("Какой у вас стек?",                                 "ru", 2),
    ("Делаете ли вы мульти-агентные системы?",            "ru", 4),
    ("Как у вас с безопасностью данных?",                 "ru", 7),
    ("Какие условия работы и оплаты?",                    "ru", 11),
    ("What tech stack do you use?",                       "en", 2),
    ("Can you build multi-agent systems?",                "en", 4),
    ("How do you handle data security?",                  "en", 7),
    ("Tell me about your background",                     "en", 0),
    # off-topic — must never shortcut
    ("Какая сегодня погода в Мурманске?",                 "ru", None),
    ("Сколько стоит билет на самолёт?",                   "ru", None),
    ("Do you know how to cook borscht?",                  "en", None),
    ("What is the capital of France?",                    "en", None),
]


def main():
    index, metadata = load_index()
    faq = {}
    for lang in ("ru", "en"):
        faq[lang] = [m for m in metadata if m.get("lang") == lang and m.get("source") == "faq" and m.get("vector_kind") == "question"]

    print(f"embedder: {embeddings.describe()}\n")
    print(f"{'similarity':>10}  {'src':<4} {'ok':<3} question -> top hit")
    print("-" * 100)

    rows = []
    for question, lang, expected in CASES:
        vec = embeddings.embed_query(question)
        # The shortcut only ever looks at question-only vectors, so tune on those.
        hits = search_similar(index, metadata, vec, k=1, lang=lang, kind="question")
        hit = hits[0] if hits else None
        sim = hit["similarity"] if hit else 0.0
        matched = None
        if hit:
            for i, f in enumerate(faq[lang]):
                if f["question"] == hit["question"]:
                    matched = i
                    break
        ok = (matched == expected)
        rows.append((sim, expected, matched, ok))
        print(f"{sim:>10.4f}  {(hit or {}).get('source','-'):<4} {'OK' if ok else 'XX':<3} "
              f"{question[:42]:<42} -> {(hit or {}).get('question','—')[:40]}")

    print("-" * 100)
    right = [s for s, exp, got, ok in rows if exp is not None and ok]
    wrong = [s for s, exp, got, ok in rows if exp is None or not ok]
    if right:
        print(f"correct FAQ matches:   min={min(right):.4f}  max={max(right):.4f}  n={len(right)}")
    if wrong:
        print(f"off-topic / mismatched: min={min(wrong):.4f}  max={max(wrong):.4f}  n={len(wrong)}")
    if right and wrong:
        print(f"\nSafe threshold sits above {max(wrong):.4f} (highest wrong hit).")
        print(f"At that value, {sum(1 for s in right if s > max(wrong))}/{len(right)} "
              f"correct matches would skip the LLM.")


if __name__ == "__main__":
    main()
