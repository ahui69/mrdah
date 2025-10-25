import os, io, pytest
from importlib import import_module

os.environ.setdefault("MEM_DB", "data/test_mem.db")
def _client():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi.testclient unavailable")
    return TestClient(import_module("core.app").app)

def test_upload_if_present():
    c = _client()
    upload_path = None
    for r in c.app.routes:
        p = getattr(r,"path", "")
        if "upload" in p.lower():
            upload_path = p
            break
    if not upload_path:
        pytest.skip("No upload endpoint detected")
    files = {"file": ("test.txt", b"hello world", "text/plain")}
    r = c.post(upload_path, files=files)
    assert r.status_code in (200, 201, 202, 400, 415, 422)
