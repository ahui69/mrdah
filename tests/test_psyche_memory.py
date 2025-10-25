import os, json, pytest
from importlib import import_module

os.environ.setdefault("MEM_DB", "data/test_mem.db")

def _client():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi.testclient unavailable")
    return TestClient(import_module("core.app").app)

def test_psyche_flow():
    c = _client()
    # reset
    r = c.post("/api/psyche/reset", params={"user_id":"t"})
    assert r.status_code == 200
    # analyze positive
    r = c.post("/api/psyche", json={"message":"Jest super, ekstra motywacja i relaks.", "user_id":"t"})
    assert r.status_code == 200
    data = r.json()
    assert "text" in data
    # state should be reachable
    r = c.get("/api/psyche/state", params={"user_id":"t"})
    assert r.status_code == 200
    s = r.json()
    assert "text" in s
    # history
    r = c.get("/api/psyche/history", params={"user_id":"t","limit":5})
    assert r.status_code == 200
    h = r.json()
    assert "text" in h
