
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import os, time, uuid, httpx, asyncio, base64, mimetypes

from .response_adapter import adapt

router = APIRouter(prefix="/api/image", tags=["image"])

WORKSPACE = Path(os.getenv("WORKSPACE","."))
OUT = WORKSPACE / "out" / "images"
OUT.mkdir(parents=True, exist_ok=True)

# Providers / keys
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY","")
STABILITY_ENGINE = os.getenv("STABILITY_ENGINE","stable-diffusion-xl-1024-v1-0")
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY","")
REPLICATE_IMG_MODEL = os.getenv("REPLICATE_IMG_MODEL","stability-ai/sdxl")
REPLICATE_IMG_VERSION = os.getenv("REPLICATE_IMG_VERSION","")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY","")
HUGGINGFACE_IMG_MODEL = os.getenv("HUGGINGFACE_IMG_MODEL","stabilityai/stable-diffusion-2")

def _tenant(req: Request) -> str:
    t = (req.headers.get("X-Tenant-ID") or "default").strip() or "default"
    safe = "".join(ch for ch in t if ch.isalnum() or ch in "-_").lower()
    return safe or "default"

class ImgIn(BaseModel):
    prompt: str
    negative: Optional[str] = None
    width: Optional[int] = 1024
    height: Optional[int] = 1024
    steps: Optional[int] = 30
    provider: Optional[str] = None  # stability | replicate | hf | auto

async def _stability_text2img(prompt: str, *, negative: Optional[str], width: int, height: int, steps: int) -> bytes:
    if not STABILITY_API_KEY:
        raise HTTPException(status_code=400, detail="stability_not_configured")
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    body = {
        "text_prompts": [{"text": prompt, "weight": 1.0}],
        "cfg_scale": 7,
        "samples": 1,
        "steps": steps or 30,
        "width": width or 1024,
        "height": height or 1024
    }
    if negative:
        body["text_prompts"].append({"text": negative, "weight": -1.0})
    url = f"https://api.stability.ai/v1/generation/{STABILITY_ENGINE}/text-to-image"
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        js = r.json()
        if not js.get("artifacts"):
            raise HTTPException(status_code=502, detail="stability_empty")
        art = js["artifacts"][0]
        if "base64" in art:
            return base64.b64decode(art["base64"])
        raise HTTPException(status_code=502, detail="stability_no_b64")

async def _replicate_text2img(prompt: str, *, negative: Optional[str], width: int, height: int, steps: int) -> bytes:
    if not REPLICATE_API_KEY:
        raise HTTPException(status_code=400, detail="replicate_not_configured")
    headers = {"Authorization": f"Token {REPLICATE_API_KEY}", "Content-Type": "application/json"}
    payload = {"input": {"prompt": prompt, "width": width, "height": height, "num_inference_steps": steps}}
    if negative:
        payload["input"]["negative_prompt"] = negative
    if REPLICATE_IMG_MODEL: payload["model"] = REPLICATE_IMG_MODEL
    if REPLICATE_IMG_VERSION: payload["version"] = REPLICATE_IMG_VERSION
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        out = data.get("output")
        if out and isinstance(out, list) and out:
            # download the first image
            img_url = out[0]
            rr = await client.get(img_url)
            rr.raise_for_status()
            return rr.content
        # poll if not immediate
        url = data.get("urls", {}).get("get") or f"https://api.replicate.com/v1/predictions/{data.get('id')}"
        for _ in range(180):
            await asyncio.sleep(1.0)
            dd = await client.get(url, headers=headers)
            dd.raise_for_status()
            dj = dd.json()
            if dj.get("status") in ("succeeded","failed","canceled"):
                if dj.get("status") != "succeeded":
                    raise HTTPException(status_code=502, detail="replicate_failed")
                out2 = dj.get("output")
                if not out2 or not isinstance(out2, list):
                    raise HTTPException(status_code=502, detail="replicate_empty")
                img_url = out2[0]
                rr = await client.get(img_url)
                rr.raise_for_status()
                return rr.content
        raise HTTPException(status_code=504, detail="replicate_timeout")

async def _hf_text2img(prompt: str, *, negative: Optional[str], width: int, height: int, steps: int) -> bytes:
    if not HUGGINGFACE_API_KEY:
        raise HTTPException(status_code=400, detail="hf_not_configured")
    url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_IMG_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    # HF text-to-image usually takes prompt in JSON or as raw prompt; we'll use JSON if supported
    payload = {"inputs": prompt}
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code == 503:
            await asyncio.sleep(2.0)
            r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.content

@router.post("/generate")
async def generate(req: Request, body: ImgIn):
    tenant = _tenant(req)
    ts = time.strftime("%Y%m%d-%H%M%S")
    name = f"{ts}-{uuid.uuid4().hex}.png"
    out = OUT / tenant
    out.mkdir(parents=True, exist_ok=True)

    provider = (body.provider or "auto").lower()
    img_bytes = None

    # order: stability -> replicate -> hf for 'auto'
    try_order = []
    if provider == "stability": try_order = ["stability"]
    elif provider == "replicate": try_order = ["replicate"]
    elif provider == "hf": try_order = ["hf"]
    else: try_order = ["stability","replicate","hf"]

    for p in try_order:
        try:
            if p == "stability":
                img_bytes = await _stability_text2img(body.prompt, negative=body.negative, width=body.width or 1024, height=body.height or 1024, steps=body.steps or 30)
                break
            if p == "replicate":
                img_bytes = await _replicate_text2img(body.prompt, negative=body.negative, width=body.width or 1024, height=body.height or 1024, steps=body.steps or 30)
                break
            if p == "hf":
                img_bytes = await _hf_text2img(body.prompt, negative=body.negative, width=body.width or 1024, height=body.height or 1024, steps=body.steps or 30)
                break
        except Exception as e:
            last_err = str(e)
            continue

    if not img_bytes:
        raise HTTPException(status_code=500, detail="image_generation_failed")

    fp = (out / name)
    with fp.open("wb") as f:
        f.write(img_bytes)

    return adapt({"text": "Wygenerowano obraz.", "sources": [], "items": [{"name": name, "url": f"/api/image/file/{tenant}/{name}", "mime":"image/png", "size": fp.stat().st_size}]})

@router.get("/file/{tenant}/{name}")
async def image_file(tenant: str, name: str):
    fp = OUT / tenant / name
    if not fp.exists():
        raise HTTPException(status_code=404, detail="not_found")
    from fastapi.responses import FileResponse
    return FileResponse(fp, media_type="image/png", filename=name)
