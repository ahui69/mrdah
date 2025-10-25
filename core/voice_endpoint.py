
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import os, time, uuid, httpx, asyncio, json, mimetypes

from .response_adapter import adapt
from .memory_store import get_pref_lang

async def _tts_elevenlabs(text: str, *, voice_id: str|None=None) -> bytes:
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=400, detail="elevenlabs_not_configured")
    vid = voice_id or ELEVENLABS_VOICE_ID
    if not vid:
        raise HTTPException(status_code=400, detail="elevenlabs_voice_missing")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "optimize_streaming_latency": 0, "output_format": "mp3_44100_128"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.content

router = APIRouter(prefix="/api/voice", tags=["voice"]) 
from pathlib import Path as _P
import json as _J

def _resolve_voice_preset(tenant: str, name: str|None) -> str|None:
    if not name: return None
    try:
        p = _P(os.getenv('WORKSPACE','.')) / 'tenants' / tenant / 'voices.json'
        if p.exists():
            mp = _J.loads(p.read_text(encoding='utf-8'))
            if name in mp: return str(mp[name])
    except Exception:
        pass
    return name


WORKSPACE = Path(os.getenv("WORKSPACE", "."))
OUTDIR = WORKSPACE / "out" / "tts"
OUTDIR.mkdir(parents=True, exist_ok=True)

REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
REPLICATE_TTS_MODEL = os.getenv("REPLICATE_TTS_MODEL", "").strip()  # e.g. 'lucataco/xtts-v2'
REPLICATE_TTS_VERSION = os.getenv("REPLICATE_TTS_VERSION", "").strip()  # version hash if needed
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HUGGINGFACE_TTS_MODEL = os.getenv("HUGGINGFACE_TTS_MODEL", "").strip()  # optional fallback

def _tenant(req: Request) -> str:
    t = (req.headers.get("X-Tenant-ID") or "default").strip() or "default"
    safe = "".join(ch for ch in t if ch.isalnum() or ch in "-_").lower()
    return safe or "default"

class TTSIn(BaseModel):
    text: str
    lang: Optional[str] = "pl"
    voice: Optional[str] = None
    provider: Optional[str] = None  # 'replicate'|'hf' or auto

async def _download(client: httpx.AsyncClient, url: str, dst: Path) -> Path:
    r = await client.get(url, timeout=60)
    r.raise_for_status()
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("wb") as f:
        f.write(r.content)
    return dst

async def _tts_replicate(text: str, *, lang: str, voice: Optional[str]) -> bytes | str:
    """Return bytes (audio) if available, else a URL string to audio."""
    headers = {"Authorization": f"Token {REPLICATE_API_KEY}", "Content-Type": "application/json"}
    payload = {"input": {"text": text}}
    if lang: payload["input"]["language"] = lang
    if voice: payload["input"]["voice"] = voice
    # new API requires 'model' or 'version'
    if REPLICATE_TTS_VERSION:
        payload["version"] = REPLICATE_TTS_VERSION
    if REPLICATE_TTS_MODEL:
        payload["model"] = REPLICATE_TTS_MODEL
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        id_ = data.get("id")
        status = data.get("status")
        out = data.get("output")
        # If output is already present and is a URL/list, return
        if out:
            return out[-1] if isinstance(out, list) else out
        # poll
        url = data.get("urls", {}).get("get") or f"https://api.replicate.com/v1/predictions/{id_}"
        for _ in range(60):
            await asyncio.sleep(1.0)
            rr = await client.get(url, headers=headers)
            rr.raise_for_status()
            dd = rr.json()
            if dd.get("status") in ("succeeded","failed","canceled"):
                if dd.get("status") != "succeeded":
                    raise HTTPException(status_code=502, detail="replicate_tts_failed")
                out2 = dd.get("output")
                return out2[-1] if isinstance(out2, list) else out2
        raise HTTPException(status_code=504, detail="replicate_tts_timeout")

async def _tts_hf(text: str) -> bytes:
    if not HUGGINGFACE_API_KEY or not HUGGINGFACE_TTS_MODEL:
        raise HTTPException(status_code=400, detail="hf_tts_not_configured")
    url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_TTS_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, data=text.encode("utf-8"))
        if r.status_code == 503:
            # warmup
            await asyncio.sleep(2.0)
            r = await client.post(url, headers=headers, data=text.encode("utf-8"))
        r.raise_for_status()
        return r.content

@router.post("/tts")
async def tts(req: Request, body: TTSIn):
    provider = (body.provider or "").lower()
    tenant = _tenant(req)
    # apply preset mapping
    body.voice = _resolve_voice_preset(tenant, body.voice)
    # default lang from prefs if missing
    if not body.lang:
        try:
            body.lang = get_pref_lang(tenant) or 'pl'
        except Exception:
            body.lang = 'pl'
    ts = time.strftime("%Y%m%d-%H%M%S")
    base = OUTDIR / tenant / ts
    base.parent.mkdir(parents=True, exist_ok=True)

    # prefer replicate if configured or requested
    audio_bytes = None
    audio_url = None
    if (provider in ("", "elevenlabs")) and ELEVENLABS_API_KEY:
        try:
            audio_bytes = await _tts_elevenlabs(body.text, voice_id=body.voice)
        except Exception as e:
            if provider == "elevenlabs":
                raise
    if (audio_bytes is None) and (provider in ("", "replicate")) and REPLICATE_API_KEY and (REPLICATE_TTS_MODEL or REPLICATE_TTS_VERSION):
        try:
            res = await _tts_replicate(body.text, lang=body.lang or "pl", voice=body.voice)
            if isinstance(res, (bytes, bytearray)):
                audio_bytes = bytes(res)
            else:
                audio_url = str(res)
        except Exception as e:
            # fallback to hf if configured
            if provider == "replicate":
                raise
    if audio_bytes is None and audio_url is None and (provider in ("", "hf")) and HUGGINGFACE_API_KEY and HUGGINGFACE_TTS_MODEL:
        audio_bytes = await _tts_hf(body.text)

    # save
    items = []
    if audio_bytes:
        fp = base.with_suffix(".wav")
        with fp.open("wb") as f:
            f.write(audio_bytes)
        items.append({"name": fp.name, "url": f"/api/voice/file/{tenant}/{fp.name}", "mime": "audio/wav", "size": fp.stat().st_size})
    if audio_url:
        # download URL into our storage as mp3 if possible
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                fp = base.with_suffix(".mp3")
                await _download(client, audio_url, fp)
                items.append({"name": fp.name, "url": f"/api/voice/file/{tenant}/{fp.name}", "mime": "audio/mpeg", "size": fp.stat().st_size})
            except Exception:
                items.append({"name": "remote_audio", "url": audio_url, "mime": "audio/mpeg", "size": 0})

    if not items:
        raise HTTPException(status_code=500, detail="tts_no_output")

    return adapt({"text": f"Gotowe TTS ({len(items)} plik).", "sources": [], "items": items})

@router.get("/file/{tenant}/{name}")
async def voice_file(tenant: str, name: str):
    fp = OUTDIR / tenant / name
    if not fp.exists():
        raise HTTPException(status_code=404, detail="not_found")
    mt, _ = mimetypes.guess_type(str(fp))
    return FileResponse(fp, media_type=mt or "application/octet-stream", filename=name)
