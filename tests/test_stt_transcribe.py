import os, pytest, pathlib
from importlib import import_module

os.environ.setdefault("MEM_DB", "data/test_mem.db")
AUDIO = pathlib.Path(__file__).parent / "assets" / "silence_8k.wav"

def _client():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi.testclient unavailable")
    return TestClient(import_module("core.app").app)

def test_stt_if_present():
    c = _client()
    stt_path = None
    for r in c.app.routes:
        p = getattr(r,"path","")
        if ("/stt" in p.lower() and "trans" in p.lower()) or p.lower().endswith("/stt"):
            stt_path = p
            break
    if not stt_path:
        pytest.skip("No STT endpoint detected")
    with open(AUDIO, "rb") as f:
        files = {"file": ("silence_8k.wav", f.read(), "audio/wav")}
    r = c.post(stt_path, files=files)
    assert r.status_code in (200, 400, 415, 422)
