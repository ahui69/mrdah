import os, pytest
from importlib import import_module
os.environ.setdefault("MEM_DB", "data/test_mem.db")

def _client():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi.testclient unavailable")
    return TestClient(import_module("core.app").app)

def test_health_docs_metrics():
    c = _client()
    r = c.get("/health")
    assert r.status_code in (200, 204)
    r = c.get("/docs")
    assert r.status_code in (200, 404)
    r = c.get("/metrics")
    assert r.status_code in (200, 404)
