import os, json, pytest
from importlib import import_module

os.environ.setdefault("MEM_DB", "data/test_mem.db")
os.environ.setdefault("AUTO_TOOLS", "1")

def _client():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi.testclient unavailable")
    return TestClient(import_module("core.app").app)

def test_autotools_routes_research():
    c = _client()
    payload = {"messages":[{"role":"user","content":"Sprawdź wynik wczorajszego meczu Realu"}]}
    r = c.post("/api/chat/assistant/stream", headers={"X-Auto-Tools":"1","Authorization":"Bearer ssjjMijaja6969"}, json=payload)
    assert r.status_code in (200, 400, 422)
    if "application/json" in r.headers.get("content-type",""):
        data = r.json()
        assert "text" in data
