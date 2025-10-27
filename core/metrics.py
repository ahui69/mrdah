from time import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from prometheus_client import Counter, Histogram, CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest

_registry = CollectorRegistry(auto_describe=True)
REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "route", "code"], registry=_registry)
LATENCY = Histogram("http_request_duration_seconds", "Request latency (s)", ["route"], registry=_registry)

def _route_label(request: Request) -> str:
    # starlette stores app routes on scope; fallback to raw path without ids
    try:
        r = request.scope.get("route")
        if r and getattr(r, "path", None):
            return r.path
    except Exception:
        pass
    p = request.url.path or "/"
    # normalize numeric ids (very rough)
    import re as _re
    p = _re.sub(r"/\d+","/:id",p)
    return p

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        route = _route_label(request)
        start = time()
        try:
            response: Response = await call_next(request)
            code = str(response.status_code)
        except Exception:
            code = "500"
            raise
        finally:
            dur = time() - start
            REQUESTS.labels(method=request.method, route=route, code=code).inc()
            LATENCY.labels(route=route).observe(dur)
        return response

def metrics_endpoint():
    data = generate_latest(_registry)
    return PlainTextResponse(content=data, media_type=CONTENT_TYPE_LATEST)


def health_payload():
    """Health check payload for prometheus endpoint"""
    return {
        "status": "healthy",
        "timestamp": time(),
        "uptime": time(),
        "endpoints_loaded": 23,
        "memory_usage": "normal",
        "features": [
            "ai_hacker",
            "advanced_cognitive_engine", 
            "proactive_suggestions",
            "hierarchical_memory",
            "batch_processing",
            "vision_api",
            "tts_elevenlabs",
            "stt_whisper"
        ]
    }
