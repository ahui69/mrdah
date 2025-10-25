#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main ASGI – scala całość i serwuje webui"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ścieżki
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# ENV defaults (pierwszy run)
os.environ.setdefault("WORKSPACE", str(BASE_DIR))
os.environ.setdefault("MEM_DB", str(BASE_DIR / "data" / "mem.db"))
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080")
os.environ.setdefault("AUTH_TOKEN", "changeme")  # dev fallback; w prod ustaw JWT

# Import core app
from core.app import app as core_app

app = core_app

# Static WebUI: /webui/*
WEB_DIR = BASE_DIR / "webui"
if WEB_DIR.exists():
    app.mount("/webui", StaticFiles(directory=str(WEB_DIR), html=True), name="webui")

# Landing na / -> /webui
@app.get("/", include_in_schema=False)
async def _root():
    index = WEB_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"ok": True, "msg": "Mordzix API – brak webui (zob. /docs)"}

# Health alias
@app.get("/healthz", include_in_schema=False)
async def _hz():
    return {"status":"ok"}

if __name__ == "__main__":
    import uvicorn
    print("="*70)
    print("🚀 Mordzix – start")
    print("📁 Workspace:", os.getenv("WORKSPACE"))
    print("💾 MEM_DB   :", os.getenv("MEM_DB"))
    print("🖥️  WebUI   : /webui")
    print("="*70)
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=False)
