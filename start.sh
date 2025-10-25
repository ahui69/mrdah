#!/usr/bin/env bash
set -Eeuo pipefail

# ──────────────────────────────────────────────────────────
# MORDZIX • START (LIGHT) — zdalny LLM przez DeepInfra
#  - żadnego GPU/Torch/Transformers
#  - tylko to, co trzeba: ffmpeg, venv, klucze, STT/TTS, CLD3/fastText
# ──────────────────────────────────────────────────────────

log() { printf "\033[1;96m[INFO]\033[0m %s\n" "$*"; }
err() { printf "\033[1;91m[ERR ]\033[0m %s\n" "$*"; exit 1; }
have(){ command -v "$1" >/dev/null 2>&1; }

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# 1) ENV
if [[ ! -f .env && -f .env.example ]]; then cp .env.example .env; fi
if [[ -f .env ]]; then set -a; source .env; set +a; fi

BACKEND_PORT="${BACKEND_PORT:-8080}"
WORKSPACE="${WORKSPACE:-/workspace/mrd}"
UPLOAD_DIR="${UPLOAD_DIR:-$WORKSPACE/out/uploads}"
FASTTEXT_MODEL="${FASTTEXT_MODEL:-workspace/mrd/models/lid.176.bin}"
SEED_ON_START="${SEED_ON_START:-0}"

# 2) System deps (ma być szybko, ale solidnie)
if have apt-get; then
  sudo apt-get update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-venv python3-dev build-essential swig pkg-config \
    ffmpeg sqlite3 git wget curl ca-certificates \
    libsndfile1 fonts-dejavu-core fonts-noto-cjk
fi

# 3) Venv
[[ -d .venv ]] || python3 -m venv .venv
source .venv/bin/activate
python -V
pip install --upgrade pip wheel setuptools

# 4) Python deps (LIGHT: bez torch/transformers)
if [[ -f requirements.txt ]]; then
  pip install --no-cache-dir -r requirements.txt
else
  err "Brak requirements.txt"
fi

# 5) Katalogi + model fastText (opcjonalny)
mkdir -p "$WORKSPACE" "$UPLOAD_DIR" "$(dirname "$FASTTEXT_MODEL")"
if [[ ! -f "$FASTTEXT_MODEL" ]]; then
  echo "[INFO] Pobieram fastText lid.176.bin (detekcja języka)…"
  wget -q https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin -O "$FASTTEXT_MODEL" || true
fi
export FASTTEXT_MODEL

# 6) Seed (opcjonalnie)
if [[ "$SEED_ON_START" == "1" && -f "seed_facts.jsonl" ]]; then
  python - <<'PY'
import json
from pathlib import Path
try:
    from core.memory_store import add_memory
    p = Path("seed_facts.jsonl")
    n=0
    if p.exists():
        for line in p.open(encoding="utf-8"):
            try:
                it = json.loads(line)
                txt = (it.get("text") or "").strip()
                meta = it.get("meta") or {}
                if txt:
                    add_memory("default", txt, meta=meta, conf=float(meta.get("conf", 0.8)))
                    n += 1
            except Exception:
                pass
    print(f"[SEED] Zaimportowano {n} wpisów.")
except Exception as e:
    print("[SEED] Pomiń import:", e)
PY
fi

# 7) Start Uvicorn
APP_MODULE=""
if [[ -f core/app.py ]]; then APP_MODULE="core.app:app"; elif [[ -f app.py ]]; then APP_MODULE="app:app"; else err "Nie ma core/app.py ani app.py"; fi

exec python -m uvicorn "$APP_MODULE" --host 0.0.0.0 --port "$BACKEND_PORT"
