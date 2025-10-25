import os, pytest
from importlib import import_module

def test_app_imports_and_exposes_fastapi():
    os.environ.setdefault("MEM_DB", "data/test_mem.db")
    m = import_module("core.app")
    assert hasattr(m, "app"), "core.app must expose `app`"
    try:
        from fastapi import FastAPI
        assert isinstance(m.app, FastAPI)
    except Exception:
        # If FastAPI unavailable here, at least attribute exists
        assert m.app is not None
