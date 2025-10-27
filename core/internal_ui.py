from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import os, json

router = APIRouter(prefix="/api/internal")

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), 'endpoints-manifest.json')

def _is_local_request(req: Request) -> bool:
    client = req.client.host if req.client else ''
    return client in ('127.0.0.1', '::1', 'localhost')

@router.get('/ui')
async def ui_info(req: Request):
    """Return manifest and optionally token for UI. Token is returned only if env UI_EXPOSE_TOKEN=1 or request is local."""
    manifest = None
    try:
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except Exception:
        manifest = {"ok": False, "error": "manifest not available"}

    expose_token = os.getenv('UI_EXPOSE_TOKEN', '0') == '1' or _is_local_request(req)
    token = None
    if expose_token:
        token = os.getenv('AUTH_TOKEN') or os.getenv('AUTH')

    return JSONResponse({
        'ok': True,
        'manifest': manifest,
        'token': token if token else None,
        'expose_token': bool(token)
    })
