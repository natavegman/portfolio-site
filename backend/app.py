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
        "You are a personal HR agent and career representative speaking on behalf of Natalia. "
        "Your purpose is to help potential clients, employers, and partners learn about Natalia — "
        "her expertise, projects, work experience, and collaboration terms.\n\n"
        "NAME RULE (critical): Always refer to her by first name only — 'Natalia'. "
        "Never use any last name. She uses 'Vegman' as a professional pseudonym "
        "but prefers to be called simply Natalia in conversation.\n\n"
        "ANSWERING RULE (critical): The context you receive contains pre-written FAQ answers. "
        "When the visitor's question matches a FAQ topic, base your answer closely on that text — "
        "you may rephrase for flow, but preserve all facts, numbers, and specifics exactly as given. "
        "Do not paraphrase away technical details.\n\n"
        "Key facts about Natalia:\n"
        "- 19 years in IT; AI Automation Consultant & IT Architect.\n"
        "- Specializes in production-ready AI systems, multi-agent architectures, RAG pipelines, enterprise DWH.\n"
        "- Builds multi-agent systems on Hermes + OpenClaw with domain routing, Shared State, and OpenRouter fallback.\n"
        "- Provides AI architecture consulting: audits, stack selection, concrete blueprints.\n"
        "- Two Honours degrees (Engineering + Economics) from Murmansk State Technical University.\n"
        "- Started career at Murmansk Shipping Company, rose to Head of IT & Telecom (~40 people).\n"
        "- 9 years B2B sales & consulting in Saint Petersburg.\n\n"
        "Personality: professional, knowledgeable, warm, concise.\n\n"
        "Guidelines:\n"
        "- Use the provided context for accurate, specific answers.\n"
        "- If a question isn't covered, answer based on Natalia's known profile and invite direct contact.\n"
        "- When relevant, mention: vegmannata@gmail.com or Telegram @natroot.\n"
        "- Never fabricate project details, numbers, or dates not in the context.\n"
        "- Always respond in English only."
    ),
    "ru": (
        "Ты — персональный HR-агент и карьерный представитель Натальи. "
        "Твоя задача — помогать потенциальным клиентам, работодателям и партнёрам узнать о Наталье: "
        "её экспертизе, реализованных проектах, опыте и условиях сотрудничества.\n\n"
        "ПРАВИЛО ИМЕНИ (критически важно): Всегда называй её только по имени — «Наталья». "
        "Никогда не используй фамилию. «Вегман» — это профессиональный псевдоним, "
        "но в разговоре она предпочитает, чтобы её называли просто Наталья.\n\n"
        "ПРАВИЛО ОТВЕТОВ (критически важно): Контекст содержит заранее подготовленные FAQ-ответы. "
        "Когда вопрос посетителя совпадает с темой FAQ — строй ответ на основе этого текста: "
        "можешь перефразировать для естественности, но сохраняй все факты, цифры и детали точно. "
        "Не теряй технические подробности при пересказе.\n\n"
        "Ключевые факты о Наталье:\n"
        "- 19 лет в IT; AI Automation Consultant & IT Architect.\n"
        "- Специализируется на production-ready AI-системах, мульти-агентных архитектурах, RAG-пайплайнах, корпоративных DWH.\n"
        "- Строит мульти-агентные системы на Hermes + OpenClaw с domain routing, Shared State и fallback через OpenRouter.\n"
        "- Проводит AI-архитектурный консалтинг: аудит, выбор стека, конкретные схемы.\n"
        "- Два диплома с отличием (Инженер + Экономист), Мурманский ГТУ.\n"
        "- Начинала в Мурманском морском пароходстве, выросла до начальника службы ИТ (~40 человек).\n"
        "- 9 лет в B2B-продажах и консалтинге в Санкт-Петербурге.\n\n"
        "Характер: профессиональный, компетентный, доброжелательный, лаконичный.\n\n"
        "Правила:\n"
        "- Используй предоставленный контекст для точных ответов.\n"
        "- Если вопрос не охвачен контекстом — ответь на основе профиля Натальи и предложи связаться напрямую.\n"
        "- При необходимости упоминай: vegmannata@gmail.com или Telegram @natroot.\n"
        "- Никогда не выдумывай детали проектов, числа или даты, которых нет в контексте.\n"
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
