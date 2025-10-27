#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MORDZIX AI - Unified Application
Wersja 5.0.0 - Zunifikowana architektura z pełną automatyzacją
"""

import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


# Helper function for CORS origins
def _get_cors_origins() -> list[str]:
    import os
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return ["http://localhost:5173"]
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or ["http://localhost:5173"]


# Najpierw tworzymy app!
app = FastAPI(
    title="Mordzix AI",
    version="5.0.0",
    description="Zaawansowany system AI z pamięcią, uczeniem i pełną automatyzacją",
    docs_url="/docs",
    redoc_url="/redoc"
)

def _req_id_from(request: Request) -> str:
    rid = request.headers.get("X-Request-ID") or request.state.__dict__.get("request_id") if hasattr(request, "state") else None
    return rid or "n/a"

def _json_error(status: int, code: str, detail, request_id: str):
    payload = {"error": code, "code": status, "detail": detail, "request_id": request_id}
    return JSONResponse(status_code=status, content=payload)

@app.exception_handler(StarletteHTTPException)
async def http_exc_handler(request: Request, exc: StarletteHTTPException):
    return _json_error(exc.status_code, "http_error", exc.detail, _req_id_from(request))

@app.exception_handler(RequestValidationError)
async def validation_exc_handler(request: Request, exc: RequestValidationError):
    return _json_error(422, "validation_error", exc.errors(), _req_id_from(request))

@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    # Do not leak internals; return generic message and attach type for debugging
    return _json_error(500, "internal_error", {"type": type(exc).__name__}, _req_id_from(request))

from fastapi.middleware.cors import CORSMiddleware
from .metrics import MetricsMiddleware, metrics_endpoint

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi.middleware.gzip import GZipMiddleware
import time, uuid, os
from .config import RATE_LIMIT_ENABLED, RATE_LIMIT_PER_MINUTE

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.time()
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time"] = f"{(time.time()-start)*1000:.1f}ms"
        return response

# naive in-memory limiter (per process)
_RATE_BUCKETS = {}
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)
        try:
            ip = request.client.host if request.client else "unknown"
        except Exception:
            ip = "unknown"
        key = f"{ip}:{request.url.path}"
        now = time.time()
        window = int(now // 60)  # per-minute window
        count, win = _RATE_BUCKETS.get(key, (0, window))
        if win != window:
            count, win = 0, window
        count += 1
        _RATE_BUCKETS[key] = (count, win)
        if count > RATE_LIMIT_PER_MINUTE:
            return Response(status_code=429, content='{"error":"rate_limit","detail":"Too Many Requests"}', media_type="application/json")
        return await call_next(request)
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

try:
    from core.metrics import MetricsMiddleware, metrics_endpoint
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    MetricsMiddleware = None
    metrics_endpoint = None

try:
    import uvicorn  # type: ignore[import]
except ImportError:  # pragma: no cover - fallback dla środowisk bez uvicorn
    uvicorn = None

# ═══════════════════════════════════════════════════════════════════
# KONFIGURACJA ŚRODOWISKA
# ═══════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent.absolute()
os.environ.setdefault("AUTH_TOKEN", "ssjjMijaja6969")
os.environ.setdefault("WORKSPACE", str(BASE_DIR))
os.environ.setdefault("MEM_DB", str(BASE_DIR / "mem.db"))

# Lista endpointów wymagających ręcznej akceptacji (spójna z frontendem)
MANUAL_TOOL_ENDPOINTS: List[Dict[str, str]] = [
    {
        "name": "code_write",
        "endpoint": "POST /api/code/write",
        "reason": "Zapisuje pliki w repozytorium i wymaga świadomego potwierdzenia."
    },
    {
        "name": "code_deps_install",
        "endpoint": "POST /api/code/deps/install",
        "reason": "Instaluje zależności i modyfikuje środowisko uruchomieniowe."
    },
    {
        "name": "code_docker_build",
        "endpoint": "POST /api/code/docker/build",
        "reason": "Buduje obraz Dockera – operacja zasobożerna."
    },
    {
        "name": "code_docker_run",
        "endpoint": "POST /api/code/docker/run",
        "reason": "Uruchamia kontener Dockera, wymaga nadzoru operatora."
    },
    {
        "name": "code_git",
        "endpoint": "POST /api/code/git",
        "reason": "Wysyła polecenia git zmieniające historię repozytorium."
    },
    {
        "name": "code_init",
        "endpoint": "POST /api/code/init",
        "reason": "Tworzy nową strukturę projektu na dysku i może nadpisać pliki."
    },
]

_AUTOMATION_SUMMARY_CACHE: Dict[str, Any] = {}
_AUTOMATION_SUMMARY_TS: float = 0.0

# Czy logować podczas importu (przy np. narzędziach CLI ustawiamy flagę by wyciszyć)
_SUPPRESS_IMPORT_LOGS = os.environ.get("MORDZIX_SUPPRESS_STARTUP_LOGS") == "1"

# ═══════════════════════════════════════════════════════════════════
# AUTOMATION SUMMARY HELPERS
# ═══════════════════════════════════════════════════════════════════


def _load_fast_path_handlers() -> Dict[str, Any]:
    """Zwróć listę nazw handlerów fast path (bezpośrednie regexy)."""

    try:
        from core.intent_dispatcher import FAST_PATH_HANDLERS  # type: ignore[import]

        handlers = [handler.__name__ for handler in FAST_PATH_HANDLERS]
        return {
            "available": True,
            "handlers": handlers,
            "count": len(handlers)
        }
    except Exception as exc:  # pragma: no cover - środowiska bez modułu
        if not _SUPPRESS_IMPORT_LOGS:
            print(f"[WARN] Fast path handlers unavailable: {exc}")
        return {
            "available": True,
            "handlers": [],
            "count": 0,
            "error": str(exc)
        }


def _load_tool_registry() -> Dict[str, Any]:
    """Zwróć listę narzędzi routera LLM."""

    try:
        from core.tools_registry import get_all_tools  # type: ignore[import]

        tools = get_all_tools()
        tool_names = [tool.get("name", "") for tool in tools if tool.get("name")]
        categories_counter = Counter(
            name.split("_", 1)[0] if "_" in name else name for name in tool_names
        )
        categories = [
            {"name": key, "count": categories_counter[key]}
            for key in sorted(categories_counter, key=lambda item: (-categories_counter[item], item))
        ]

        return {
            "available": True,
            "count": len(tools),
            "tools": tools,
            "names": tool_names,
            "categories": categories
        }
    except Exception as exc:  # pragma: no cover
        if not _SUPPRESS_IMPORT_LOGS:
            print(f"[WARN] Tool registry unavailable: {exc}")
        return {
            "available": True,
            "count": 0,
            "tools": [],
            "names": [],
            "categories": [],
            "error": str(exc)
        }


def _build_automation_summary() -> Dict[str, Any]:
    """Zbuduj podsumowanie automatyzacji (fast path + router)."""

    fast_path = _load_fast_path_handlers()
    tools = _load_tool_registry()

    fast_count = fast_path.get("count", 0)
    tool_count = tools.get("count", 0)
    manual_count = len(MANUAL_TOOL_ENDPOINTS)

    totals_automations = fast_count + tool_count
    totals_automatic = max(totals_automations - manual_count, 0)

    return {
        "generated_at": time.time(),
        "fast_path": fast_path,
        "tools": {
            "available": tools.get("available", True),
            "count": tool_count,
            "categories": tools.get("categories", []),
            "sample": tools.get("names", [])[:15],
        },
        "manual": {
            "count": manual_count,
            "endpoints": MANUAL_TOOL_ENDPOINTS
        },
        "totals": {
            "automations": totals_automations,
            "automatic": totals_automatic
        }
    }


def get_automation_summary(refresh: bool = False) -> Dict[str, Any]:
    """Pobierz (opcjonalnie odśwież) cache z podsumowaniem automatyzacji."""

    global _AUTOMATION_SUMMARY_CACHE, _AUTOMATION_SUMMARY_TS

    if refresh or not _AUTOMATION_SUMMARY_CACHE:
        _AUTOMATION_SUMMARY_CACHE = _build_automation_summary()
        _AUTOMATION_SUMMARY_TS = _AUTOMATION_SUMMARY_CACHE.get("generated_at", time.time())
    else:
        # Dołącz timestamp do cache (może być potrzebny przy monitoringu)
        _AUTOMATION_SUMMARY_CACHE["generated_at"] = _AUTOMATION_SUMMARY_TS

    return _AUTOMATION_SUMMARY_CACHE

# Prometheus middleware korzysta z core.metrics (jeśli dostępne)

# ═══════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION (już zdefiniowana wyżej)
# ═══════════════════════════════════════════════════════════════════

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus middleware
if PROMETHEUS_AVAILABLE:
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        start_time = time.time()
        endpoint = request.url.path
        method = request.method
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code

            return response
        except Exception as exc:
            status_code = getattr(exc, "status_code", 500)
            # error_label = exc.__class__.__name__
            # record_error(error_label, endpoint)  # Disabled for now
            raise
        finally:
            duration = time.time() - start_time
            # record_request(method, endpoint, status_code, duration)  # Disabled

# ═══════════════════════════════════════════════════════════════════
# INCLUDE ROUTERS - Wszystkie endpointy
# ═══════════════════════════════════════════════════════════════════

if not _SUPPRESS_IMPORT_LOGS:
    print("\n" + "="*70)
    print("MORDZIX AI - INICJALIZACJA ENDPOINTÓW")
    print("="*70 + "\n")

# 1. ASSISTANT (główny chat z AI)
try:
    from core import assistant_endpoint
    app.include_router(assistant_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Assistant endpoint      /api/chat/assistant")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Assistant endpoint: {e}")

# 2. PSYCHE (stan psychiczny AI)
try:
    import psyche_endpoint
    app.include_router(psyche_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Psyche endpoint         /api/psyche/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Psyche endpoint: {e}")

# 3. PROGRAMISTA (wykonywanie kodu)
try:
    import programista_endpoint
    app.include_router(programista_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Programista endpoint    /api/code/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Programista endpoint: {e}")

# 4. FILES (upload, analiza plików)
try:
    import files_endpoint
    app.include_router(files_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Files endpoint          /api/files/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Files endpoint: {e}")

# 5. TRAVEL (wyszukiwanie podróży)
try:
    from core import travel_endpoint
    app.include_router(travel_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Travel endpoint         /api/travel/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Travel endpoint: {e}")

# 6. ADMIN (statystyki, cache)
try:
    import admin_endpoint
    app.include_router(admin_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Admin endpoint          /api/admin/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Admin endpoint: {e}")

# 7. CAPTCHA (rozwiązywanie captcha)
try:
    import captcha_endpoint
    app.include_router(captcha_endpoint.router, prefix="/api/captcha", tags=["captcha"])
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Captcha endpoint        /api/captcha/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Captcha endpoint: {e}")

# 8. PROMETHEUS (metryki)
try:
    import prometheus_endpoint
    app.include_router(prometheus_endpoint.router, prefix="/api/prometheus", tags=["monitoring"])
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Prometheus endpoint     /api/prometheus/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Prometheus endpoint: {e}")

# 9. TTS (text-to-speech)
try:
    import tts_endpoint
    app.include_router(tts_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ TTS endpoint            /api/tts/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ TTS endpoint: {e}")

# 10. STT (speech-to-text)
try:
    import stt_endpoint
    app.include_router(stt_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ STT endpoint            /api/stt/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ STT endpoint: {e}")

# 11. WRITING (generowanie tekstów)
try:
    import writing_endpoint
    app.include_router(writing_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Writing endpoint        /api/writing/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Writing endpoint: {e}")

# 12. SUGGESTIONS (proaktywne sugestie)
try:
    import suggestions_endpoint
    app.include_router(suggestions_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Suggestions endpoint    /api/suggestions/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Suggestions endpoint: {e}")

# 13. BATCH (przetwarzanie wsadowe)
try:
    import batch_endpoint
    app.include_router(batch_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Batch endpoint          /api/batch/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Batch endpoint: {e}")

# 14. RESEARCH (web search - DuckDuckGo, Wikipedia, SERPAPI)
try:
    import research_endpoint
    app.include_router(research_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Research endpoint       /api/research/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Research endpoint: {e}")

# 15. COGNITIVE (cognitive engine - zaawansowane przetwarzanie)
try:
    import cognitive_endpoint
    app.include_router(cognitive_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Cognitive endpoint      /api/cognitive/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Cognitive endpoint: {e}")

# 16. MEMORY (hierarchical memory system)
try:
    from core import memory_endpoint
    app.include_router(memory_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Memory endpoint         /api/memory/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Memory endpoint: {e}")

# ═══════ 🔥 NOWE ZAAWANSOWANE ENDPOINTY 🔥 ═══════

# 17. AI FASHION (stylizacje, trendy, marki)
try:
    import fashion_endpoint
    app.include_router(fashion_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ AI Fashion endpoint     /api/fashion/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ AI Fashion endpoint: {e}")

# 18. ML PREDICTIONS (95% accuracy suggestions)
try:
    import ml_endpoint
    app.include_router(ml_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ ML Predictions endpoint /api/ml/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ ML Predictions endpoint: {e}")

# 19. FACT VALIDATION (multi-source fact checking)
try:
    import fact_validation_endpoint
    app.include_router(fact_validation_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Fact Validation endpoint /api/facts/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Fact Validation endpoint: {e}")

# 20. VISION (image description, OCR)
try:
    from core import vision_endpoint
    app.include_router(vision_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Vision endpoint         /api/vision/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Vision endpoint: {e}")

# 21. VOICE (TTS, audio processing)
try:
    from core import voice_endpoint
    app.include_router(voice_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Voice endpoint          /api/voice/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Voice endpoint: {e}")

# 22. SELF-REFLECTION (dynamiczna rekurencja umysłowa)
try:
    import reflection_endpoint
    app.include_router(reflection_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Self-Reflection endpoint /api/reflection/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Self-Reflection endpoint: {e}")

# 23. AI HACKER (pentesting & security tools)
try:
    import hacker_endpoint
    app.include_router(hacker_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ AI Hacker endpoint      /api/hacker/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ AI Hacker endpoint: {e}")

# 24. IMAGE (generowanie obrazów)
try:
    from core import image_endpoint
    app.include_router(image_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Image endpoint          /api/image/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Image endpoint: {e}")

# 25. NLP (zaawansowana analiza językowa)
try:
    import nlp_endpoint
    app.include_router(nlp_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ NLP endpoint            /api/nlp/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ NLP endpoint: {e}")

# 26. AUTOROUTER (frontend auto-routing)
try:
    from core import frontend_autorouter
    app.include_router(frontend_autorouter.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ AutoRouter endpoint     /api/autoroute/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ AutoRouter endpoint: {e}")

# 27. LANG (detekcja języka)
try:
    from core import lang_endpoint
    app.include_router(lang_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Lang endpoint           /api/lang/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Lang endpoint: {e}")

# 28. INTERNAL (wewnętrzne API)
try:
    import internal_endpoint
    app.include_router(internal_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Internal endpoint       /api/internal/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Internal endpoint: {e}")

# 29. INTERNAL UI (interfejs wewnętrzny)
try:
    import internal_ui
    app.include_router(internal_ui.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Internal UI endpoint    /api/internal/ui")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Internal UI endpoint: {e}")

# 30. HYBRID SEARCH (zaawansowane wyszukiwanie FTS5+Semantic+Fuzzy)
try:
    from core import hybrid_search_endpoint
    app.include_router(hybrid_search_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Hybrid Search endpoint  /api/search/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Hybrid Search endpoint: {e}")

# 
#  PREMIUM ENDPOINTS (31-35)
# 

# 31. LICENSING & MONETIZATION
try:
    from endpoints import licensing_endpoint
    app.include_router(licensing_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print(" Licensing endpoint /api/license/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f" Licensing: {e}")

# 32. WHITE LABEL
try:
    from endpoints import white_label_endpoint
    app.include_router(white_label_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print(" White Label endpoint /api/whitelabel/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f" White Label: {e}")

# 33. AI MARKETPLACE
try:
    from endpoints import ai_marketplace_endpoint
    app.include_router(ai_marketplace_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print(" AI Marketplace /api/marketplace/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f" AI Marketplace: {e}")

# 34. AI TRAINING
try:
    from endpoints import ai_training_endpoint
    app.include_router(ai_training_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print(" AI Training Platform /api/training/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f" AI Training: {e}")

# 35. ANALYTICS
try:
    from endpoints import analytics_dashboard_endpoint
    app.include_router(analytics_dashboard_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print(" Analytics Dashboard /api/analytics/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f" Analytics: {e}")

if not _SUPPRESS_IMPORT_LOGS:
    print("\n" + "="*70)
    print("🔥 WSZYSTKIE ENDPOINTY ZAŁADOWANE (35 TOTAL) 🔥")
    print("="*70 + "\n")
    print("✅ AI Fashion Manager")
    print("✅ Advanced LLM Integration")
    print("✅ ML Proactive Suggestions (95% accuracy)")
    print("✅ Multi-Source Fact Validation")
    print("✅ Context Awareness Engine")
    print("✅ Vision Processing (OCR + Image Analysis)")
    print("✅ Voice Processing (TTS Multi-Provider)")
    print("✅ Self-Reflection Engine (5 poziomów głębokości)")
    print("✅ AI Hacker Toolkit (Port Scan, SQLi, Recon)")
    print("\n" + "="*70 + "\n")

# ═══════════════════════════════════════════════════════════════════
# BASIC ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.get("/api")
@app.get("/status")
async def api_status():
    """Status API"""
    return {
        "ok": True,
        "app": "Mordzix AI",
        "version": "5.0.0",
        "features": {
            "auto_stm_to_ltm": True,
            "auto_learning": True,
            "context_injection": True,
            "psyche_system": True,
            "travel_search": True,
            "code_executor": True,
            "tts_stt": True,
            "file_analysis": True
        },
        "endpoints": {
            "chat": "/api/chat/assistant",
            "chat_stream": "/api/chat/assistant/stream",
            "psyche": "/api/psyche/status",
            "travel": "/api/travel/search",
            "code": "/api/code/exec",
            "files": "/api/files/upload",
            "admin": "/api/admin/stats",
            "tts": "/api/tts/speak",
            "stt": "/api/stt/transcribe"
        },
        "automation": get_automation_summary()
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/api/endpoints/list")
async def list_endpoints():
    """Lista wszystkich endpointów API"""
    endpoints = []
    seen = set()
    
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api"):
            methods = sorted([m for m in route.methods if m not in {"HEAD", "OPTIONS"}])
            identifier = (route.path, tuple(methods))
            
            if identifier not in seen:
                endpoints.append({
                    "path": route.path,
                    "methods": methods,
                    "name": route.name,
                    "tags": list(route.tags) if route.tags else [],
                    "summary": route.summary or ""
                })
                seen.add(identifier)
    
    endpoints.sort(key=lambda e: (e["path"], ",".join(e["methods"])))
    return {"ok": True, "count": len(endpoints), "endpoints": endpoints}


@app.get("/api/automation/status")
async def automation_status():
    """Podsumowanie automatycznych narzędzi i fast path."""

    summary = get_automation_summary()
    return {"ok": True, **summary}

# ═══════════════════════════════════════════════════════════════════
# FRONTEND ROUTES - ANGULAR APP
# ═══════════════════════════════════════════════════════════════════

# POPRAWKA: BASE_DIR z config.py może być błędne gdy importuje z core/
# Używamy Path(__file__).parent.parent.resolve() aby dostać /home/ubuntu/mrd
from pathlib import Path as _Path
_APP_ROOT = _Path(__file__).parent.parent.resolve()
FRONTEND_DIST = _APP_ROOT / "frontend" / "dist" / "mordzix-ai"

# Serwowanie statycznych plików z Angular dist/ (tylko jeśli istnieją)
assets_dir = FRONTEND_DIST / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

print("[INIT] Registering serve_frontend for routes: /, /app, /chat")
@app.get("/", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
@app.get("/chat", response_class=HTMLResponse)
async def serve_frontend():
    """Główny interfejs czatu - Angular SPA lub WebUI"""
    print("[REQUEST] serve_frontend() called!")
    print(f"[DEBUG] _APP_ROOT={_APP_ROOT}")
    print(f"[DEBUG] FRONTEND_DIST={FRONTEND_DIST}")
    # 1. Próbujemy załadować Angular dist
    angular_index = FRONTEND_DIST / "index.html"
    print(f"[DEBUG] Angular: {angular_index} exists={angular_index.exists()}")
    if angular_index.exists():
        print("[INFO] Serving Angular")
        return HTMLResponse(content=angular_index.read_text(encoding="utf-8"))
    
    # 2. Mobile-optimized chat (frontend/dist/mordzix-ai/index.html)
    mobile_index = _APP_ROOT / "frontend" / "dist" / "mordzix-ai" / "index.html"
    print(f"[DEBUG] Mobile: {mobile_index} exists={mobile_index.exists()}")
    if mobile_index.exists():
        print(f"[INFO] ✅ Serving Mobile Chat from {mobile_index}")
        content = mobile_index.read_text(encoding="utf-8")
        print(f"[DEBUG] Mobile content length: {len(content)}")
        return HTMLResponse(content=content)
    
    # 3. Fallback: stary index.html (dla dev bez builda)
    fallback_index = _APP_ROOT / "index.html"
    if fallback_index.exists():
        return HTMLResponse(content=fallback_index.read_text(encoding="utf-8"))
    
    # Brak frontendu
    return HTMLResponse(
        content="""
        <h1>�🔥🔥 TESTING - THIS IS NEW CODE 🔥🔥🔥</h1>
        <p>If you see this, the code is loaded correctly!</p>
        <p>Run: <code>cd frontend && npm install && npm run build:prod</code></p>
        <p>Or use API directly: <a href="/docs">/docs</a></p>
        """,
        status_code=404
    )

# Catch-all dla Angular routing (musi być na końcu!)
@app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
async def angular_catch_all(full_path: str):
    """Przekieruj wszystkie nieznane ścieżki do Angular SPA (dla routingu)"""
    # Ignoruj ścieżki API
    if full_path.startswith("api/") or full_path.startswith("health"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Zwróć Angular index.html (SPA obsłuży routing)
    angular_index = FRONTEND_DIST / "index.html"
    if angular_index.exists():
        return HTMLResponse(content=angular_index.read_text(encoding="utf-8"))
    
    raise HTTPException(status_code=404, detail="Frontend not found")

# PWA Assets
@app.get("/sw.js", include_in_schema=False)
@app.get("/ngsw-worker.js", include_in_schema=False)
async def serve_service_worker(request: Request):
    """Service worker (Angular PWA lub legacy)."""
    candidates = [
        FRONTEND_DIST / "ngsw-worker.js",
        FRONTEND_DIST / "sw.js",
        BASE_DIR / "dist" / "ngsw-worker.js",
        BASE_DIR / "dist" / "sw.js",
        BASE_DIR / "ngsw-worker.js",
        BASE_DIR / "sw.js",
    ]
    for path in candidates:
        if path.exists():
            return FileResponse(path, media_type="application/javascript")
    return HTMLResponse(status_code=404, content="service worker not found")

@app.get("/manifest.webmanifest", include_in_schema=False)
async def serve_manifest():
    """Web App Manifest"""
    candidates = [
        FRONTEND_DIST / "manifest.webmanifest",
        FRONTEND_DIST / "assets" / "manifest.webmanifest",
        BASE_DIR / "dist" / "manifest.webmanifest",
        BASE_DIR / "manifest.webmanifest",
    ]
    for path in candidates:
        if path.exists():
            return FileResponse(path, media_type="application/manifest+json")
    return HTMLResponse(status_code=404, content="manifest not found")

@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    """Favicon"""
    paths = [
        FRONTEND_DIST / "favicon.ico",
        BASE_DIR / "dist" / "favicon.ico",
        BASE_DIR / "favicon.ico",
        BASE_DIR / "icons" / "favicon.ico"
    ]
    for path in paths:
        if path.exists():
            return FileResponse(path, media_type="image/x-icon")
    return HTMLResponse(status_code=404)

# Static files (assets, icons, webui)
if (BASE_DIR / "icons").exists():
    app.mount("/icons", StaticFiles(directory=str(BASE_DIR / "icons")), name="icons")

# WebUI - Alternatywny frontend (vanilla JS PWA)
webui_dir = BASE_DIR.parent / "webui"  # Katalog główny projektu
if webui_dir.exists():
    # Mount bez html=True żeby nie konfliktowal z routing
    app.mount("/webui", StaticFiles(directory=str(webui_dir)),
              name="webui")
    print("✓ WebUI Frontend mounted at /webui/")
    
    # Handler dla /webui/ -> index.html
    @app.get("/webui/", include_in_schema=False)
    async def webui_index():
        return FileResponse(str(webui_dir / "index.html"))
        
else:
    print(f"✗ WebUI directory not found at {webui_dir}")


# ═══════════════════════════════════════════════════════════════════
# STARTUP & SHUTDOWN
# ═══════════════════════════════════════════════════════════════════


@app.on_event("startup")
async def startup_event():
    """Inicjalizacja przy starcie"""
    print("\n" + "="*70)
    print("MORDZIX AI - STARTED")
    print("="*70)
    print("\n[INFO] Funkcje:")
    print("  ✓ Auto STM→LTM transfer")
    print("  ✓ Auto-learning (Google + scraping)")
    print("  ✓ Context injection (LTM w prompt)")
    print("  ✓ Psyche system (nastrój AI)")
    print("  ✓ Travel (hotele/restauracje/atrakcje)")
    print("  ✓ Code executor (shell/git/docker)")
    print("  ✓ TTS/STT (ElevenLabs + Whisper)")
    print("\n[INFO] Endpoints:")
    print("  [API] Chat:      POST /api/chat/assistant")
    print("  [API] Stream:    POST /api/chat/assistant/stream")
    print("  [API] Psyche:    GET  /api/psyche/status")
    print("  [API] Travel:    GET  /api/travel/search")
    print("  [API] Code:      POST /api/code/exec")
    print("  [API] Files:     POST /api/files/upload")
    print("  [API] TTS:       POST /api/tts/speak")
    print("  [API] STT:       POST /api/stt/transcribe")
    print("\n[INFO] Interfejs:")
    print("  [WEB] Frontend:  http://localhost:8080/")
    print("  [WEB] Docs:      http://localhost:8080/docs")
    print("\n" + "="*70 + "\n")

    summary = get_automation_summary(refresh=True)
    fast_count = summary.get("fast_path", {}).get("count", 0)
    tool_count = summary.get("tools", {}).get("count", 0)
    manual_count = summary.get("manual", {}).get("count", 0)
    automatic_total = summary.get("totals", {}).get("automatic", 0)

    print("[INFO] Automatyzacja:")
    print(f"  ✓ Fast path handlers : {fast_count}")
    print(f"  ✓ Router tools       : {tool_count}")
    print(f"  ✓ Manual approvals   : {manual_count}")
    print(f"  ✓ Auto executables   : {automatic_total}")
    
    # Inicjalizacja bazy danych i pamięci
    try:
        from core.memory import _init_db, load_ltm_to_memory
        _init_db()
        load_ltm_to_memory()
        print("[OK] Pamięć LTM załadowana")
    except Exception as e:
        print(f"[WARN] Błąd inicjalizacji pamięci: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup przy wyłączeniu"""
    print("\n[INFO] Shutting down Mordzix AI...")

# ═══════════════════════════════════════════════════════════════════
# MAIN - Uruchomienie serwera
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    if uvicorn is None:
        raise RuntimeError("Uvicorn nie jest zainstalowany. Uruchom 'pip install uvicorn' w środowisku aplikacji.")
    
    parser = argparse.ArgumentParser(description='Mordzix AI Server')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port (default: 8080)')
    parser.add_argument('-H', '--host', default="0.0.0.0", help='Host (default: 0.0.0.0)')
    parser.add_argument('--reload', action='store_true', help='Auto-reload on code changes')
    args = parser.parse_args()
    
    print(f"\n[INFO] Starting server on http://{args.host}:{args.port}")
    print(f"[INFO] API Docs: http://localhost:{args.port}/docs")
    print(f"[INFO] Frontend: http://localhost:{args.port}/\n")
    
    uvicorn.run(
        "core.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


@app.get('/metrics', include_in_schema=False)
def _metrics():
    return metrics_endpoint()

