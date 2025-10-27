from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
import json, os, time, uuid
from core.licensing import require_license_dep
from core.llm_proxy import call_llm

router = APIRouter(
    prefix="/v1",
    tags=["openai-compat"],
    dependencies=[Depends(require_license_dep(os.getenv("MIN_TIER_PROXY","pro")))]
)

@router.get("/models")
async def list_models():
    return {"data": [{"id": os.getenv("DEFAULT_MODEL","gpt-4o-mini"), "object":"model"}]}

@router.post("/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()
    messages = body.get("messages", [])
    model = body.get("model", os.getenv("DEFAULT_MODEL","gpt-4o-mini"))
    stream = body.get("stream", False)

    if stream:
        async def sse():
            async for part in await call_llm(messages=messages, model=model, stream=True):
                chunk = {
                    "id": f"cmpl-{uuid.uuid4()}",
                    "object": "chat.completion.chunk",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": part},
                        "finish_reason": None
                    }],
                    "model": model
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(sse(), media_type="text/event-stream")
    else:
        text = await call_llm(messages=messages, model=model, stream=False)
        resp = {
            "id": f"cmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {"role":"assistant","content": text},
                "finish_reason": "stop"
            }],
            "created": int(time.time()),
            "model": model
        }
        return JSONResponse(resp)
