"""
Natalia Vegman — Personal HR Agent API
Run after building the index:
    uvicorn backend.app:app --reload --port 8000
"""
import os, sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from rag_index import load_index, search_similar

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError("OPENAI_API_KEY is not set — create a .env file")

client = OpenAI(api_key=_api_key)

try:
    _index, _metadata = load_index()
    print(f"[RAG] Index loaded: {_index.ntotal} vectors")
except RuntimeError as e:
    print(f"[RAG] WARNING: {e}")
    _index, _metadata = None, []

app = FastAPI(title="Natalia Vegman HR Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

SYSTEM_PROMPTS = {
    "en": (
        "You are Natalia Vegman's personal HR agent and career representative. "
        "Your purpose is to help potential clients, employers, and partners learn about Natalia — "
        "her technical expertise, completed projects, work experience, and collaboration terms.\n\n"
        "Personality: professional, knowledgeable, warm, and concise. "
        "You speak confidently about Natalia's capabilities.\n\n"
        "Guidelines:\n"
        "- Use the provided context to give accurate, specific answers.\n"
        "- If a question isn't fully covered by the context, give a helpful answer based on "
        "Natalia's known profile and invite them to contact her directly.\n"
        "- When relevant, mention contact: vegmannata@gmail.com or Telegram @natroot.\n"
        "- Never fabricate specific project details, numbers, or dates not present in context.\n"
        "- Always respond in English only."
    ),
    "ru": (
        "Ты — персональный HR-агент и карьерный представитель Натальи Вегман. "
        "Твоя задача — помогать потенциальным клиентам, работодателям и партнёрам узнать о Наталье: "
        "её технической экспертизе, реализованных проектах, опыте и условиях сотрудничества.\n\n"
        "Характер: профессиональный, компетентный, доброжелательный, лаконичный. "
        "Ты уверенно рассказываешь о возможностях Натальи.\n\n"
        "Правила:\n"
        "- Используй предоставленный контекст для точных ответов.\n"
        "- Если вопрос не полностью охвачен контекстом — ответь на основе профиля Натальи "
        "и предложи связаться напрямую.\n"
        "- При необходимости упоминай контакты: vegmannata@gmail.com или Telegram @natroot.\n"
        "- Никогда не выдумывай конкретные детали проектов, числа или даты, которых нет в контексте.\n"
        "- Отвечай только на русском языке."
    ),
}


class ChatRequest(BaseModel):
    message: str
    lang: str = "en"
    top_k: int = 3


class ChatResponse(BaseModel):
    answer: str
    context: list[dict]


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if _index is None:
        raise HTTPException(
            status_code=503,
            detail="Index not built. Run: python backend/build_index.py",
        )

    lang = req.lang if req.lang in ("en", "ru") else "en"

    emb = client.embeddings.create(input=req.message, model="text-embedding-3-small")
    query_vec = emb.data[0].embedding

    results = search_similar(_index, _metadata, query_vec, k=req.top_k, lang=lang)

    context_str = "\n\n---\n\n".join(
        f"[{item.get('source','').upper()}] {item['question']}\n{item['answer']}"
        for item in results
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[lang]},
        {
            "role": "user",
            "content": (
                f"Context about Natalia:\n\n{context_str}\n\n"
                f"---\n\nVisitor's question: {req.message}"
            ),
        },
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
        max_tokens=500,
    )

    return ChatResponse(
        answer=completion.choices[0].message.content,
        context=results,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "index_loaded": _index is not None, "vectors": getattr(_index, "ntotal", 0)}
