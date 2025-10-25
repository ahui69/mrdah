import os, pytest
from importlib import import_module

os.environ.setdefault("MEM_DB", "data/test_mem.db")

def _client():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi.testclient unavailable")
    return TestClient(import_module("core.app").app)

def test_memory_search_and_export():
    c = _client()
    r = c.get("/api/memory/search", params={"user_id":"default","q":"test","limit":5})
    assert r.status_code == 200
    r = c.get("/api/memory/export/journal", params={"fmt":"json"})
    assert r.status_code == 200
    r = c.get("/api/memory/export/conversations", params={"fmt":"csv"})
    assert r.status_code == 200
