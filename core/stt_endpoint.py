
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os, time, uuid, httpx, asyncio, json, mimetypes, shutil

from .response_adapter import adapt
from .memory_store import set_pref_lang
from .lang_detect import detect_lang


async def _openai_asr(bytes_data: bytes) -> str:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="openai_asr_not_configured")
    import aiohttp
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
        data = aiohttp.FormData()
        data.add_field('file', bytes_data, filename='audio.webm', content_type='audio/webm')
        data.add_field('model', OPENAI_STT_MODEL)
        async with session.post(url, headers=headers, data=data) as r:
            if r.status != 200:
                raise HTTPException(status_code=502, detail="openai_asr_failed")
            js = await r.json()
            return js.get("text","")
router = APIRouter(prefix="/api/stt", tags=["stt"]) 
import re as _re

def _guess_lang(text: str) -> str:
    t = text.strip()
    if not t: return 'und'
    # simple heuristic: diacritics for PL, common words
    if _re.search(r'[ąćęłńóśźż]', t.lower()): return 'pl'
    if _re.search(r'\b(the|and|you|are|is|this|that)\b', t.lower()): return 'en'
    return 'pl' if len(t) and sum(c in 'ąćęłńóśźż' for c in t.lower())>0 else 'en'


WORKSPACE = Path(os.getenv("WORKSPACE", "."))
INBOX = WORKSPACE / "out" / "stt"
INBOX.mkdir(parents=True, exist_ok=True)

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
HUGGINGFACE_STT_MODEL = os.getenv("HUGGINGFACE_STT_MODEL", "openai/whisper-large-v3")

def _tenant(req: Request) -> str:
    t = (req.headers.get("X-Tenant-ID") or "default").strip() or "default"
    safe = "".join(ch for ch in t if ch.isalnum() or ch in "-_").lower()
    return safe or "default"

async def _hf_asr(bytes_data: bytes) -> str:
    if not HUGGINGFACE_API_KEY:
        raise HTTPException(status_code=400, detail="hf_asr_not_configured")
    url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_STT_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(url, headers=headers, content=bytes_data)
        if r.status_code == 503:
            await asyncio.sleep(2.0)
            r = await client.post(url, headers=headers, content=bytes_data)
        r.raise_for_status()
        try:
            js = r.json()
            if isinstance(js, dict) and "text" in js:
                return js["text"]
        except Exception:
            pass
        return ""

@router.post("/transcribe")
async def transcribe(req: Request, file: UploadFile = File(...)):
    tenant = _tenant(req)
    ts = time.strftime("%Y%m%d-%H%M%S")
    ext = os.path.splitext(file.filename or "")[1].lower() or ".wav"
    outdir = INBOX / tenant
    outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / f"{ts}-{uuid.uuid4().hex}{ext}"
    with fp.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    text = await (_openai_asr(fp.read_bytes()) if OPENAI_API_KEY else _hf_asr(fp.read_bytes()))
    lang = detect_lang(text)
    if not text:
        raise HTTPException(status_code=502, detail="stt_empty_result")

    set_pref_lang(tenant, lang)
    return adapt({"text": text, "sources": [], "language": lang, "items": [{"name": fp.name, "url": f"/api/stt/file/{tenant}/{fp.name}", "mime":"audio/*", "size": fp.stat().st_size}]})

@router.get("/file/{tenant}/{name}")
async def stt_file(tenant: str, name: str):
    fp = INBOX / tenant / name
    if not fp.exists():
        raise HTTPException(status_code=404, detail="not_found")
    mt, _ = mimetypes.guess_type(str(fp))
    from fastapi.responses import FileResponse
    return FileResponse(fp, media_type=mt or "application/octet-stream", filename=name)
