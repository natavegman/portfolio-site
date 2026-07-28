"""
Natalia Vegman — Personal HR Agent API
Run after building the index:
    uvicorn backend.app:app --reload --port 8000

Everything here is shaped around keeping API spend near zero: retrieval runs on
a local embedder, repeated questions come from cache, close FAQ matches skip the
LLM entirely, and both per-IP and global daily caps bound the worst case.
"""
import os, sys, re, json, time, hashlib, logging, threading
from collections import OrderedDict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI, RateLimitError, APIConnectionError, APIStatusError
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from rag_index import load_index, search_similar, DATA_DIR
import embeddings

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger("hr_agent")
logging.basicConfig(level=logging.INFO)


def _env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return int(default)


def _env_float(name, default):
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return float(default)


CHAT_MODEL      = os.getenv("CHAT_MODEL", "gpt-4o-mini")
TOP_K           = _env_int("TOP_K", 2)
MAX_TOKENS      = _env_int("MAX_TOKENS", 300)
MAX_MESSAGE_LEN = _env_int("MAX_MESSAGE_LEN", 500)

# A visitor question this close to a stored FAQ entry is answered from the
# pre-written text — no LLM call at all. Tuned via tools/tune_threshold.py:
# verbatim FAQ questions score 1.00, paraphrases 0.67–0.93, and the worst
# wrong match sits at 0.72, so 0.80 keeps a margin over it.
FAQ_SHORTCUT_SIMILARITY = _env_float("FAQ_SHORTCUT_SIMILARITY", 0.80)
# Below this, retrieval found nothing useful and an answer would be invented.
MIN_CONTEXT_SIMILARITY  = _env_float("MIN_CONTEXT_SIMILARITY", 0.30)

CACHE_TTL_SECONDS = _env_int("CACHE_TTL_SECONDS", 7 * 24 * 3600)
CACHE_MAX_ENTRIES = _env_int("CACHE_MAX_ENTRIES", 500)

IP_DAILY_LIMIT     = _env_int("IP_DAILY_LIMIT", 30)
GLOBAL_DAILY_LIMIT = _env_int("GLOBAL_DAILY_LIMIT", 500)

ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv(
        "ALLOWED_ORIGINS",
        "https://vegman.dev,https://www.vegman.dev,https://natavegman.github.io",
    ).split(",") if o.strip()
]
REQUIRE_ORIGIN = os.getenv("REQUIRE_ORIGIN", "true").lower() == "true"

_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError("OPENAI_API_KEY is not set — create a .env file")

client = OpenAI(api_key=_api_key)

try:
    _index, _metadata = load_index()
    logger.info("[RAG] Index loaded: %s vectors", _index.ntotal)
except RuntimeError as e:
    logger.warning("[RAG] %s", e)
    _index, _metadata = None, []

# An index built by a different embedder yields vectors that are numerically
# valid but semantically meaningless — fail loudly instead of serving nonsense.
_info_path = os.path.join(DATA_DIR, 'faiss_info.json')
if _index is not None and os.path.exists(_info_path):
    with open(_info_path, encoding='utf-8') as f:
        _index_info = json.load(f)
    _active = embeddings.describe()
    if _index_info.get("model") != _active["model"]:
        raise RuntimeError(
            f"Index was built with {_index_info.get('model')} but the active embedder is "
            f"{_active['model']} — rerun: python backend/build_index.py"
        )

app = FastAPI(title="Natalia Vegman HR Agent API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

SYSTEM_PROMPTS = {
    "en": (
        "You are a personal HR agent representing Natalia. You speak ABOUT her, never AS her: "
        "always third person ('Natalia does...', 'she specializes in...'), never 'I' or 'my'. "
        "You help potential clients, employers and partners learn about her expertise, "
        "projects, experience and collaboration terms.\n\n"
        "NAME RULE (critical): refer to her by first name only — 'Natalia'. Never use a last name; "
        "'Vegman' is a professional pseudonym.\n\n"
        "ANSWERING RULE (critical): the context contains pre-written FAQ answers. When the question "
        "matches one, base your answer closely on that text — rephrase for flow, but keep every fact, "
        "number and technical detail exactly as given.\n\n"
        "Background: 19 years in IT; AI Automation Consultant & IT Architect; production-ready AI "
        "systems, multi-agent architectures, RAG pipelines, enterprise DWH; two Honours degrees "
        "(Engineering + Economics); grew from Murmansk Shipping Company to Head of IT & Telecom "
        "(~40 people); 9 years B2B sales and consulting in Saint Petersburg.\n\n"
        "Be professional, warm and concise. Never invent projects, numbers or dates absent from the "
        "context — if something isn't covered, say so and invite direct contact: vegmannata@gmail.com "
        "or Telegram @natroot. Respond in English only."
    ),
    "ru": (
        "Ты — персональный HR-агент, представляющий Наталью. Ты говоришь О НЕЙ, а не ОТ ЕЁ ИМЕНИ: "
        "всегда третье лицо («Наталья делает...», «она специализируется...»), никогда «я» или «мой». "
        "Ты помогаешь клиентам, работодателям и партнёрам узнать о её экспертизе, проектах, "
        "опыте и условиях сотрудничества.\n\n"
        "ПРАВИЛО ИМЕНИ (критично): называй её только по имени — «Наталья». Фамилию не используй; "
        "«Вегман» — профессиональный псевдоним.\n\n"
        "ПРАВИЛО ОТВЕТОВ (критично): контекст содержит готовые FAQ-ответы. Если вопрос совпадает "
        "с темой — строй ответ на этом тексте: перефразируй для естественности, но сохраняй все "
        "факты, цифры и технические детали точно.\n\n"
        "Справка: 19 лет в ИТ; AI Automation Consultant & IT Architect; production-ready AI-системы, "
        "мульти-агентные архитектуры, RAG-пайплайны, корпоративные DWH; два диплома с отличием "
        "(инженер + экономист); прошла путь от Мурманского морского пароходства до начальника службы "
        "ИТ (~40 человек); 9 лет в B2B-продажах и консалтинге в Санкт-Петербурге.\n\n"
        "Будь профессиональной, доброжелательной и лаконичной. Не выдумывай проекты, числа и даты, "
        "которых нет в контексте — если вопрос не охвачен, скажи об этом и предложи связаться "
        "напрямую: vegmannata@gmail.com или Telegram @natroot. Отвечай только на русском."
    ),
}

UNAVAILABLE = {
    "en": "Service is temporarily unavailable. Please contact Natalia directly: vegmannata@gmail.com",
    "ru": "Сервис временно недоступен. Напишите Наталье напрямую: vegmannata@gmail.com",
}
RATE_LIMITED = {
    "en": "You've reached today's question limit. Please contact Natalia directly: vegmannata@gmail.com",
    "ru": "Достигнут дневной лимит вопросов. Напишите Наталье напрямую: vegmannata@gmail.com",
}

# ── Rate limiting ────────────────────────────────────────────────────────────
# Counts LLM-backed answers only: cache hits and FAQ shortcuts cost nothing, so
# there is no reason to spend a visitor's allowance on them.
_counter_lock = threading.Lock()
_ip_counts: dict[str, int] = {}
_global_count = 0
_counter_day = ""


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _budget_available(ip: str) -> bool:
    """Check the caps without consuming anything."""
    global _counter_day, _global_count
    with _counter_lock:
        if _counter_day != _today():
            _counter_day, _global_count = _today(), 0
            _ip_counts.clear()
        return _ip_counts.get(ip, 0) < IP_DAILY_LIMIT and _global_count < GLOBAL_DAILY_LIMIT


def _consume_budget(ip: str) -> None:
    global _global_count
    with _counter_lock:
        _ip_counts[ip] = _ip_counts.get(ip, 0) + 1
        _global_count += 1


# ── Answer cache ─────────────────────────────────────────────────────────────
_cache_lock = threading.Lock()
_cache: "OrderedDict[str, tuple[float, str, list[dict]]]" = OrderedDict()


def _cache_key(message: str, lang: str) -> str:
    normalised = re.sub(r"\s+", " ", message.strip().lower()).rstrip("?!. ")
    return hashlib.sha256(f"{lang}|{normalised}".encode()).hexdigest()


def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if not entry:
            return None
        stored_at, answer, context = entry
        if time.time() - stored_at > CACHE_TTL_SECONDS:
            del _cache[key]
            return None
        _cache.move_to_end(key)
        return answer, context


def _cache_put(key: str, answer: str, context: list[dict]) -> None:
    with _cache_lock:
        _cache[key] = (time.time(), answer, context)
        _cache.move_to_end(key)
        while len(_cache) > CACHE_MAX_ENTRIES:
            _cache.popitem(last=False)


# ── API ──────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LEN)
    lang: str = "en"
    top_k: int = Field(default=TOP_K, ge=1, le=5)


class ChatResponse(BaseModel):
    answer: str
    context: list[dict]
    source: str


def _public_context(results: list[dict]) -> list[dict]:
    """Only what the widget could plausibly show — never the stored answers."""
    return [
        {"question": r.get("question", ""), "source": r.get("source", ""),
         "similarity": r.get("similarity", 0)}
        for r in results
    ]


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    if _index is None:
        raise HTTPException(
            status_code=503,
            detail="Index not built. Run: python backend/build_index.py",
        )

    origin = request.headers.get("origin")
    if REQUIRE_ORIGIN and origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Origin not allowed")

    lang = req.lang if req.lang in ("en", "ru") else "en"
    ip = _client_ip(request)

    key = _cache_key(req.message, lang)
    cached = _cache_get(key)
    if cached:
        answer, context = cached
        return ChatResponse(answer=answer, context=context, source="cache")

    try:
        query_vec = embeddings.embed_query(req.message)
    except Exception:
        logger.exception("Embedding failed")
        raise HTTPException(status_code=503, detail=UNAVAILABLE[lang])

    results = search_similar(_index, _metadata, query_vec, k=req.top_k, lang=lang, kind="full")
    public = _public_context(results)

    # Near-exact FAQ match: the stored answer is human-written and already the
    # best possible response, so paying for a paraphrase adds nothing. Compared
    # against the question-only vectors — see build_index.
    faq_hits = search_similar(_index, _metadata, query_vec, k=1, lang=lang, kind="question")
    if faq_hits and faq_hits[0]["similarity"] >= FAQ_SHORTCUT_SIMILARITY:
        answer = faq_hits[0]["answer"]
        _cache_put(key, answer, public)
        logger.info("faq-shortcut sim=%.3f ip=%s", faq_hits[0]["similarity"], ip)
        return ChatResponse(answer=answer, context=public, source="faq")

    if not _budget_available(ip):
        logger.warning("rate limit hit ip=%s", ip)
        raise HTTPException(status_code=429, detail=RATE_LIMITED[lang])

    usable = [r for r in results if r["similarity"] >= MIN_CONTEXT_SIMILARITY]
    context_str = "\n\n---\n\n".join(
        f"[{item.get('source','').upper()}] {item['question']}\n{item['answer']}"
        for item in usable
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

    try:
        completion = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=MAX_TOKENS,
        )
    except (RateLimitError, APIConnectionError, APIStatusError) as exc:
        # Retrieval still works without the API, so a decent hit beats an error page.
        if results and results[0]["similarity"] >= MIN_CONTEXT_SIMILARITY:
            logger.warning("LLM unavailable (%s) — serving retrieval fallback", type(exc).__name__)
            return ChatResponse(answer=results[0]["answer"], context=public, source="fallback")
        logger.error("LLM unavailable (%s) and no usable context", type(exc).__name__)
        raise HTTPException(status_code=503, detail=UNAVAILABLE[lang])
    except Exception:
        logger.exception("Unexpected LLM error")
        raise HTTPException(status_code=503, detail=UNAVAILABLE[lang])

    _consume_budget(ip)
    answer = completion.choices[0].message.content
    _cache_put(key, answer, public)
    return ChatResponse(answer=answer, context=public, source="llm")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "index_loaded": _index is not None,
        "vectors": getattr(_index, "ntotal", 0),
        "embeddings": embeddings.describe(),
        "chat_model": CHAT_MODEL,
        "cache_entries": len(_cache),
        "llm_calls_today": _global_count,
        "global_daily_limit": GLOBAL_DAILY_LIMIT,
    }
