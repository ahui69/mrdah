
from fastapi import APIRouter, Request
from pydantic import BaseModel
from .response_adapter import adapt
from .lang_detect import detect_lang

router = APIRouter(prefix="/api/lang", tags=["lang"])

class In(BaseModel):
    text: str

@router.post("/detect")
async def detect(req: Request, body: In):
    code = detect_lang(body.text)
    return adapt({"text": code, "sources": []})
