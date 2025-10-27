
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Psyche Endpoint – stan psychiki + pamięć (SQLite+FTS)
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi import status
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import re

from core.response_adapter import adapt
from core.memory_store import init_db, save_message, recent_messages, search_messages, get_state, update_state, apply_delta, journal
from core.auth import verify_token as _auth  # jeśli masz auth, zostawiamy import (nie jest wymagany do poniższych tras)

router = APIRouter(prefix="/api/psyche", tags=["psyche"])

# --- Simple PL sentiment/rule engine (bez zewn. bibliotek) ---
_POS = set("dobrze super świetnie wspaniale cudownie kocham lubię ekstra spoko wygrywam wygrana sukces dziękuję szczęśliwy zadowolony relaks luz spokojny skoncentrowany energia motywacja".split())
_NEG = set("źle słabo fatalnie smutny smutno nienawidzę wkurzony zły przegrana porażka stres zmęczony zmęczenie bezsilny lęk panika ból frustracja dołek depresyjnie martwię martwie martwi".split())

def analyze_sentiment(text: str) -> Dict[str, Any]:
    tokens = re.findall(r"\\w+", (text or "").lower(), flags=re.UNICODE)
    pos = sum(1 for t in tokens if t in _POS)
    neg = sum(1 for t in tokens if t in _NEG)
    score = (pos - neg)
    # clamp and scale to -1..1
    if pos+neg > 0:
        norm = max(-1.0, min(1.0, score / (pos+neg)))
    else:
        norm = 0.0
    label = "positive" if norm > 0.15 else "negative" if norm < -0.15 else "neutral"
    # Proposed deltas
    mood_delta = norm * 0.35
    energy_delta = (pos*0.05) - (neg*0.05)
    stress_delta = (-pos*0.03) + (neg*0.06)
    focus_delta = (0.05 if "koncentr" in text.lower() or "skup" in text.lower() else 0.0)
    return {
        "label": label,
        "score": round(norm, 3),
        "delta": {
            "mood": mood_delta,
            "energy": energy_delta,
            "stress": stress_delta,
            "focus": focus_delta
        }
    }

class PsyRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"
    recall: Optional[int] = 5
    search: Optional[str] = None  # dodatkowe zapytanie FTS (opcjonalnie)

class PsyStateUpdate(BaseModel):
    user_id: Optional[str] = "default"
    mood: Optional[float] = None
    energy: Optional[float] = None
    stress: Optional[float] = None
    focus: Optional[float] = None

@router.post("", summary="Analiza wiadomości i aktualizacja stanu")
async def psyche_analyze(body: PsyRequest) -> Dict[str, Any]:
    init_db()
    uid = body.user_id or "default"
    # Zapisz wiadomość użytkownika do pamięci
    save_message(uid, "user", body.message, tags=["psyche"])
    state_before = get_state(uid)
    # Analiza
    res = analyze_sentiment(body.message)
    sdelta = res["delta"]
    state_after = apply_delta(uid, **sdelta)
    # stwórz notatkę i wpis do journala
    note = f"sentiment={res['label']} score={res['score']} delta={sdelta}"
    journal(uid, res["label"], sdelta.get("mood",0.0), note)
    # recall (recent + optional search)
    recent = recent_messages(uid, limit=max(1, int(body.recall or 5)))
    hits = []
    if body.search and body.search.strip():
        try:
            hits = search_messages(uid, body.search.strip(), limit=5)
        except Exception:
            hits = []
    # odpowiedź (asystenta)
    advice = {
        "positive": "Brzmi pozytywnie. Podbijaj to, co działa. Utrzymaj rytm i krótkie przerwy na oddech.",
        "negative": "Słyszę ciężar. Zrób mały krok: 10-min spacer, oddechy 4-7-8, albo pomodoro 15 min. Małe zwycięstwo dziś wystarczy.",
        "neutral":  "Zapisane. Mogę zaproponować mikro-plan na dziś w 2 krokach."
    }[res["label"]]
    asst_text = (
        f"🧠 **Analiza**: {res['label']} (score {res['score']}).\\n"
        f"• moodΔ={sdelta['mood']:+.2f}  energyΔ={sdelta['energy']:+.2f}  stressΔ={sdelta['stress']:+.2f}  focusΔ={sdelta['focus']:+.2f}\\n"
        f"**Stan** → mood={state_after['mood']:.2f}, energy={state_after['energy']:.2f}, stress={state_after['stress']:.2f}, focus={state_after['focus']:.2f}\\n\\n"
        f"{advice}"
    )
    save_message(uid, "assistant", asst_text, tags=["psyche","analysis"])
    payload = {
        "text": asst_text,
        "sources": [{"title":"Psyche journal", "url":"about:psyche"}],
        "state_before": state_before,
        "state_after": state_after,
        "recent_context": recent,
        "search_hits": hits
    }
    return adapt(payload)

@router.get("/state", summary="Pobierz bieżący stan")
async def psyche_state(user_id: str = "default") -> Dict[str, Any]:
    s = get_state(user_id or "default")
    return adapt({"text": f"Stan {user_id}: mood={s['mood']:.2f}, energy={s['energy']:.2f}, stress={s['stress']:.2f}, focus={s['focus']:.2f}", "sources": []})

@router.post("/state", summary="Ustaw stan")
async def psyche_state_set(body: PsyStateUpdate) -> Dict[str, Any]:
    uid = body.user_id or "default"
    s = update_state(uid, mood=body.mood, energy=body.energy, stress=body.stress, focus=body.focus)
    return adapt({"text": f"Ustawiono stan {uid}: mood={s['mood']:.2f}, energy={s['energy']:.2f}, stress={s['stress']:.2f}, focus={s['focus']:.2f}", "sources": []})

@router.post("/reset", summary="Reset stanu")
async def psyche_reset(user_id: str = "default") -> Dict[str, Any]:
    # reset na zero
    s = update_state(user_id or "default", mood=0.0, energy=0.0, stress=0.0, focus=0.0)
    return adapt({"text": f"Zresetowano stan {user_id}.", "sources": []})

@router.get("/history", summary="Ostatnie wiadomości")
async def psyche_history(user_id: str = "default", limit: int = 10) -> Dict[str, Any]:
    rec = recent_messages(user_id or "default", limit=max(1,int(limit)))
    return adapt({"text": f"Ostatnie {len(rec)} wpisów.", "sources": [{"title":"history","url":"about:psyche/history"}], "items": rec})
