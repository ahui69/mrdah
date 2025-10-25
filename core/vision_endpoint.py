
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from .response_adapter import adapt
from pathlib import Path
import os, httpx, asyncio

router = APIRouter(prefix="/api/vision", tags=["vision"])

WORKSPACE = Path(os.getenv("WORKSPACE","."))

VISION_API_KEY = os.getenv("VISION_API_KEY","") or os.getenv("REPLICATE_API_KEY","")
VISION_MODEL = os.getenv("VISION_MODEL","yorickvp/llava-13b").strip()

class VisionIn(BaseModel):
    image_url: str
    prompt: Optional[str] = None

async def _replicate_vision(image_url: str, prompt: Optional[str]) -> str:
    if not VISION_API_KEY:
        raise HTTPException(status_code=400, detail="vision_not_configured")
    headers = {"Authorization": f"Token {VISION_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": VISION_MODEL,
        "input": {
            "image": image_url,
            "prompt": prompt or "Describe the image in detail."
        }
    }
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        out = data.get("output")
        # If immediate output else poll
        if out:
            return out if isinstance(out, str) else (out[-1] if isinstance(out, list) else str(out))
        url = data.get("urls", {}).get("get") or f"https://api.replicate.com/v1/predictions/{data.get('id')}"
        for _ in range(90):
            await asyncio.sleep(1.0)
            rr = await client.get(url, headers=headers)
            rr.raise_for_status()
            dd = rr.json()
            if dd.get("status") in ("succeeded","failed","canceled"):
                if dd.get("status") != "succeeded":
                    raise HTTPException(status_code=502, detail="vision_failed")
                out2 = dd.get("output")
                return out2 if isinstance(out2, str) else (out2[-1] if isinstance(out2, list) else str(out2))
        raise HTTPException(status_code=504, detail="vision_timeout")

@router.post("/describe")
async def describe(req: Request, body: VisionIn):
    text = await _replicate_vision(body.image_url, body.prompt)
    return adapt({
        "text": text,
        "sources": [{"title":"Vision", "url": body.image_url}],
        "items": [{"name": body.image_url.split('/')[-1], "url": body.image_url, "mime":"image/*", "size": 0}]
    })


class OcrIn(BaseModel):
    image_url: str

@router.post("/ocr")
async def ocr(req: Request, body: OcrIn):
    # Prefer HuggingFace TrOCR (no server binary required)
    HF_KEY = os.getenv("HUGGINGFACE_API_KEY","")
    MODEL = os.getenv("HUGGINGFACE_OCR_MODEL","microsoft/trocr-base-printed")
    if not HF_KEY:
        raise HTTPException(status_code=400, detail="hf_ocr_not_configured")
    url = f"https://api-inference.huggingface.co/models/{MODEL}"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    async with httpx.AsyncClient(timeout=90) as client:
        # fetch image bytes
        ir = await client.get(body.image_url)
        ir.raise_for_status()
        img = ir.content
        r = await client.post(url, headers=headers, content=img)
        if r.status_code == 503:
            await asyncio.sleep(2.0)
            r = await client.post(url, headers=headers, content=img)
        r.raise_for_status()
        try:
            js = r.json()
            # TrOCR returns [{"generated_text": "..."}]
            if isinstance(js, list) and js and isinstance(js[0], dict) and "generated_text" in js[0]:
                text = js[0]["generated_text"]
            elif isinstance(js, dict) and "text" in js:
                text = js["text"]
            else:
                text = ""
        except Exception:
            text = ""
    if not text:
        raise HTTPException(status_code=502, detail="ocr_empty")
    return adapt({"text": text, "sources": [{"title":"OCR","url": body.image_url}]})
