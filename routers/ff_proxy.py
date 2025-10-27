from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import os, httpx, re, json

router = APIRouter(prefix="/api/ff", tags=["ff-proxy"])

FF_GATEWAY_SECRET = os.getenv("FF_GATEWAY_SECRET", "").strip()
ALLOWED_PREFIXES = [p.strip() for p in os.getenv("FF_ALLOWED_PREFIXES", "/api/").split(",") if p.strip()]
DENY_PATTERNS = [r"^/api/ff/.*", r"^/docs$", r"^/redoc$", r"^/openapi\.json$"]

class ProxyReq(BaseModel):
    method: str = Field(..., examples=["GET","POST","PUT","DELETE","PATCH"])
    path: str   = Field(..., examples=["/api/memory/add","/api/memory/search"])
    query: Optional[Dict[str, Any]] = None
    body:  Optional[Any] = None
    headers: Optional[Dict[str,str]] = None

def check_gateway_token(req: Request):
    if FF_GATEWAY_SECRET:
        token = req.headers.get("X-FF-GW", "")
        if token != FF_GATEWAY_SECRET:
            raise HTTPException(status_code=401, detail="bad gateway token")
    return True

def is_allowed_path(path: str) -> bool:
    for pat in DENY_PATTERNS:
        if re.match(pat, path):
            return False
    for pref in ALLOWED_PREFIXES:
        if path.startswith(pref):
            return True
    return False

@router.post("/proxy")
async def ff_proxy(data: ProxyReq, req: Request, _=Depends(check_gateway_token)):
    method = data.method.upper()
    path   = data.path
    if not is_allowed_path(path):
        raise HTTPException(403, f"path not allowed: {path}")

    base_url = os.getenv("INTERNAL_BASE_URL", "http://127.0.0.1:8080")
    url = f"{base_url}{path}"

    fwd_headers: Dict[str,str] = {}
    auth = req.headers.get("authorization")
    if auth:
        fwd_headers["authorization"] = auth
    if data.headers:
        fwd_headers.update(data.headers)

    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if method in ("GET","DELETE"):
            r = await client.request(method, url, headers=fwd_headers, params=data.query or {})
        elif method in ("POST","PUT","PATCH"):
            json_body = None
            content   = None
            if isinstance(data.body, (dict, list)) or data.body is None:
                json_body = data.body
            elif isinstance(data.body, str):
                try:
                    json_body = json.loads(data.body)
                except Exception:
                    content = data.body.encode("utf-8")
            r = await client.request(method, url, headers=fwd_headers,
                                     params=data.query or {}, json=json_body, content=content)
        else:
            raise HTTPException(405, f"Method {method} not allowed")

    ctype = (r.headers.get("content-type") or "").lower()
    try:
        payload = r.json() if "application/json" in ctype else r.text
    except Exception:
        payload = r.text
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=payload)
    return payload
