import os, pytest
from importlib import import_module

def test_basic_routes_exist():
    os.environ.setdefault("MEM_DB", "data/test_mem.db")
    m = import_module("core.app")
    app = m.app
    paths = {r.path for r in app.routes}
    # health & docs
    assert "/health" in paths or any("/health" in p for p in paths)
    assert "/docs" in paths
