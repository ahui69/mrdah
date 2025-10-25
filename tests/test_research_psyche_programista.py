import os, pytest
from importlib import import_module
os.environ.setdefault("MEM_DB", "data/test_mem.db")

def _client():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi.testclient unavailable")
    return TestClient(import_module("core.app").app)

def _maybe_call(c, prefix, body):
    target = None
    for r in c.app.routes:
        p = getattr(r,"path","")
        if p.startswith(prefix):
            target = p
            break
    if not target:
        pytest.skip(f"No endpoint with prefix {prefix}")
    res = c.post(target, json=body)
    assert res.status_code in (200, 400, 422), f"{target} -> {res.status_code}"
    return res

def test_research_minimal():
    c = _client()
    _maybe_call(c, "/api/research", {"query":"AI memory","mode":"fast"})

def test_psyche_minimal():
    c = _client()
    _maybe_call(c, "/api/psyche", {"message":"hej","user_id":"test"})

def test_programista_minimal():
    c = _client()
    _maybe_call(c, "/api/programista", {"code":"print('hi')","tool":"ruff"})
