# Security hardening

- Middleware: rate-limit per IP/tenant (minute buckets), optional Proof-of-Work (POW_DIFFICULTY), origin check.
- Sensitive paths protected: chat stream, upload, TTS, STT, psyche, memory search.
- Uploads: size limit (MAX_FILE_SIZE) and MIME whitelist (image/*, video/*, audio/*, application/pdf, text/plain, application/zip).
- UI computes PoW header automatically if difficulty>0.

## ENV
RATE_LIMIT_IP_PER_MIN=60
RATE_LIMIT_TENANT_PER_MIN=240
RATE_BURST=40
POW_DIFFICULTY=0
ALLOWED_ORIGINS=*

## Status endpoint
GET /api/security/status -> { config: { pow_difficulty, rate_ip_per_min, ... } }
