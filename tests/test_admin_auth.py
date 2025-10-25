import os, pytest
from importlib import import_module

@pytest.mark.parametrize("token", ["", "wrong"])
def test_admin_requires_auth(token):
    os.environ.setdefault("MEM_DB", "data/test_mem.db")
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi.testclient not available in this environment")
    app = import_module("core.app").app
    c = TestClient(app)
    r = c.post("/api/admin/cache/clear", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code in (401, 403)
