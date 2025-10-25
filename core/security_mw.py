
import os, time, sqlite3, hashlib
from pathlib import Path
from typing import Set
from fastapi import Request, HTTPException

WORKSPACE = Path(os.getenv("WORKSPACE","."))
DB = WORKSPACE / "data" / "security.db"
DB.parent.mkdir(parents=True, exist_ok=True)

RATE_IP = int(os.getenv("RATE_LIMIT_IP_PER_MIN", "60"))
RATE_TENANT = int(os.getenv("RATE_LIMIT_TENANT_PER_MIN", "240"))
BURST = int(os.getenv("RATE_BURST", "40"))
POW_DIFFICULTY = int(os.getenv("POW_DIFFICULTY", "0"))  # hex zeros (nibbles); 0 disables
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
ALLOWED_ORIGINS = [s.strip() for s in str(os.getenv("ALLOWED_ORIGINS","*")).split(",") if s.strip()]


HONEYPOT_FIELD = os.getenv("HONEYPOT_FIELD", "hp_field")
MIN_FORM_TIME = int(os.getenv("MIN_FORM_TIME", "3"))  # seconds

def _tenant_file(tenant: str, name: str) -> Path:
    return (WORKSPACE / "tenants" / tenant / name)

def _deny_for(tenant: str):
    cfg = {"ips": [], "ua": []}
    p = _tenant_file(tenant, "denylist.json")
    try:
        if p.exists():
            import json
            data = json.loads(p.read_text(encoding="utf-8"))
            cfg["ips"] = [str(x) for x in (data.get("ips") or [])]
            cfg["ua"] = [str(x).lower() for x in (data.get("ua") or [])]
    except Exception:
        pass
    return cfg

def _blocked_by_deny(req: Request, tenant: str) -> bool:
    ip = req.client.host if req.client else ""
    ua = (req.headers.get("User-Agent") or "").lower()
    cfg = _deny_for(tenant)
    if ip and ip in cfg["ips"]:
        return True
    for bad in cfg["ua"]:
        if bad and bad in ua:
            return True
    return False

def _ts_ok(req: Request) -> bool:
    if MIN_FORM_TIME <= 0:
        return True
    try:
        # Allow both header and JSON field
        start = req.headers.get("X-Form-Start") or ""
        if not start and req.method in ("POST","PUT"):
            # try read from scope (body will be parsed by route; here only hint from header is reliable)
            start = ""
        if not start:
            return True  # fail-open to not break external clients; PoW+rate still protect
        start = float(start)
        return (time.time() - start) >= MIN_FORM_TIME
    except Exception:
        return True

SENSITIVE_PATHS: Set[str] = {
    "/api/chat/assistant/stream",
    "/api/files/upload",
    "/api/voice/tts",
    "/api/stt/transcribe",
    "/api/psyche",
    "/api/memory/search",
}

def _con():
    con = sqlite3.connect(str(DB))
    con.execute("PRAGMA journal_mode=WAL;")
    return con

def _bucket(ts=None):  # minute bucket
    return int((ts or time.time()) // 60)

def _tenant(req: Request) -> str:
    t = (req.headers.get("X-Tenant-ID") or "default").strip() or "default"
    safe = "".join(ch for ch in t if ch.isalnum() or ch in "-_").lower()
    return safe or "default"

def _origin_ok(req: Request) -> bool:
    if "*" in ALLOWED_ORIGINS:
        return True
    origin = req.headers.get("Origin") or req.headers.get("Referer") or ""
    if not origin:
        return True  # allow PWA/file contexts
    return any(origin.startswith(o) for o in ALLOWED_ORIGINS)

def _rate_hit(key: str, limit: int) -> bool:
    b = _bucket()
    con = _con()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS hits(
        key TEXT NOT NULL, bucket INTEGER NOT NULL, count INTEGER NOT NULL,
        PRIMARY KEY(key, bucket)
    )""")
    cur.execute("INSERT OR IGNORE INTO hits(key,bucket,count) VALUES(?,?,0)", (key,b))
    cur.execute("UPDATE hits SET count = count + 1 WHERE key=? AND bucket=?", (key,b))
    cur.execute("SELECT count FROM hits WHERE key=? AND bucket=?", (key,b))
    cnt = cur.fetchone()[0]
    con.commit()
    con.close()
    return cnt <= (limit + BURST)

def _verify_pow(req: Request) -> bool:
    if POW_DIFFICULTY <= 0 or not AUTH_TOKEN:
        return True
    nonce = (req.headers.get("X-PoW") or "").strip()
    if not nonce:
        return False
    path = req.url.path
    minute = str(_bucket())
    msg = f"{nonce}|{path}|{minute}|{AUTH_TOKEN}".encode("utf-8")
    h = hashlib.sha256(msg).hexdigest()
    needed = "0"*POW_DIFFICULTY
    return h.startswith(needed)

async def guard(request: Request):
    # origin
    if not _origin_ok(request):
        raise HTTPException(status_code=403, detail="origin_forbidden")
    # scope
    p = request.url.path
    if p not in SENSITIVE_PATHS:
        return
    # denylist
    if _blocked_by_deny(request, ten):
        raise HTTPException(status_code=403, detail="denylist_block")
    # rate
    ip = request.client.host if request.client else "0.0.0.0"
    ten = _tenant(request)
    if not _rate_hit(f"ip:{ip}", RATE_IP):
        raise HTTPException(status_code=429, detail="rate_ip_exceeded")
    if not _rate_hit(f"tenant:{ten}", RATE_TENANT):
        raise HTTPException(status_code=429, detail="rate_tenant_exceeded")
    # pow
    if request.method in ("POST","PUT","DELETE"):
        # Honeypot & time-to-submit
        if (request.headers.get('X-Honeypot') or '').strip():
            raise HTTPException(status_code=403, detail='bot_detected')
        if not _ts_ok(request):
            raise HTTPException(status_code=429, detail='too_fast_form_submit')
        # PoW
        if not _verify_pow(request):
            raise HTTPException(status_code=428, detail="pow_required")

def status_payload():
    return {
        "pow_difficulty": POW_DIFFICULTY,
        "rate_ip_per_min": RATE_IP,
        "rate_tenant_per_min": RATE_TENANT,
        "burst": BURST,
    }
