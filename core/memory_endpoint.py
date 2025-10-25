
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .response_adapter import adapt
from .memory_store import add_memory, search_memory, memory_export, memory_import, memory_optimize
import os, time, json

router = APIRouter(prefix="/api/memory", tags=["memory"])

def _tenant(req: Request) -> str:
    t = (req.headers.get("X-Tenant-ID") or "default").strip() or "default"
    safe = "".join(ch for ch in t if ch.isalnum() or ch in "-_").lower()
    return safe or "default"

class AddIn(BaseModel):
    text: str
    meta: Optional[Dict[str, Any]] = None
    conf: Optional[float] = 0.6
    lang: Optional[str] = None
    source: Optional[str] = None

class SearchIn(BaseModel):
    q: str
    topk: Optional[int] = 8

class ImportIn(BaseModel):
    items: List[Dict[str, Any]]

@router.post("/add")
async def add(req: Request, body: AddIn):
    ten = _tenant(req)
    rid = add_memory(ten, body.text, meta=body.meta or {}, conf=float(body.conf or 0.6), lang=body.lang, source=body.source)
    return adapt({"text": "OK", "sources": [], "item": rid})

@router.post("/search")
async def search(req: Request, body: SearchIn):
    ten = _tenant(req)
    items = search_memory(ten, body.q, topk=int(body.topk or 8))
    return adapt({"text": f"Znaleziono {len(items)} wpisów.", "sources": [], "items": items})

@router.get("/export")
async def export(req: Request):
    ten = _tenant(req)
    data = memory_export(ten)
    return adapt({"text": f"Eksport: {data['count']} wpisów.", "sources": [], "items": data["items"]})

@router.post("/import")
async def import_(req: Request, body: ImportIn):
    ten = _tenant(req)
    n = memory_import(ten, body.items or [])
    return adapt({"text": f"Zaimportowano {n} wpisów.", "sources": []})

@router.post("/optimize")
async def optimize(req: Request):
    memory_optimize()
    return adapt({"text": "Pamięć zoptymalizowana.", "sources": []})
