import os, json, pytest
from importlib import import_module

os.environ.setdefault("MEM_DB", "data/test_mem.db")
os.environ.setdefault("AUTH_TOKEN", "test-token")

def _iter_routes():
    m = import_module("core.app")
    app = m.app
    for r in app.routes:
        path = getattr(r, "path", None) or getattr(r, "path_regex", None)
        methods = list(getattr(r, "methods", []) or [])
        if not path or path.startswith(("/openapi.json","/static")):
            continue
        yield path, methods

def test_routes_respond_basic():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi.testclient unavailable")
    app = import_module("core.app").app
    c = TestClient(app)
    ok = set()
    for path, methods in _iter_routes():
        if "{" in path or "}" in path:
            continue
        method = "GET" if "GET" in methods else next(iter(methods), "GET")
        headers = {}
        if path.startswith("/api/admin"):
            headers["Authorization"] = "Bearer test-token"
        if method == "GET":
            r = c.get(path, headers=headers)
        elif method == "POST":
            r = c.post(path, headers=headers, json={"query":"test","mode":"fast"})
        elif method == "DELETE":
            r = c.delete(path, headers=headers)
        elif method == "PUT":
            r = c.put(path, headers=headers, json={})
        elif method == "PATCH":
            r = c.patch(path, headers=headers, json={})
        else:
            continue
        assert r.status_code in (200, 201, 202, 204, 400, 401, 403, 404, 415, 422), f"{path} returned {r.status_code}"
        ok.add((path, r.status_code))
    assert ok, "No routes tested"
