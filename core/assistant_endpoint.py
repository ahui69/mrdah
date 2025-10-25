#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assistant_endpoint.py - Now a lean endpoint that uses the Cognitive Engine.
"""
from .response_adapter import adapt
from fastapi import APIRouter, Request, HTTPException, Depends
from .memory_store import save_message
from .autoroute import decide
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os, json, asyncio
from dataclasses import dataclass, asdict

# --- MAIN IMPORT: THE NEW COGNITIVE ENGINE ---
from core.cognitive_engine import cognitive_engine

# Imports for memory saving (UnifiedMemorySystem)
try:
    from core.memory import get_memory_system
    memory_system = get_memory_system()
except ImportError:
    memory_system = None

# --- Pydantic Models (Unchanged) ---
class Message(BaseModel):
    role: str
    content: str
    attachments: Optional[List[Dict[str, Any]]] = []

class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: Optional[str] = "default"
    use_memory: bool = True
    use_research: bool = True
    internet_allowed: Optional[bool] = True  # Domyślnie zezwalaj na internet
    auto_learn: Optional[bool] = True  # Domyślnie włącz autonaukę
    use_batch_processing: Optional[bool] = True  # Domyślnie używaj przetwarzania wsadowego

class ChatResponse(BaseModel):
    ok: bool
    answer: str
    sources: Optional[List[Dict]] = []
    metadata: Dict[str, Any] = {}

router = APIRouter(prefix="/api/chat")

# Auth (Unchanged)
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "ssjjMijaja6969")
def _auth(req: Request):
    if (req.headers.get("Authorization","") or "").replace("Bearer ","").strip() != AUTH_TOKEN:
        raise HTTPException(401, "unauthorized")

# --- LEAN MAIN ENDPOINT (UPGRADED - auto memory integration!) ---
@router.post("/assistant", response_model=ChatResponse)
async def chat_assistant(body: ChatRequest, req: Request, _=Depends(_auth)):
    from .config import MEMORY_ENABLED
    from .memory import memory_add_conversation
    
    user_id = body.user_id or req.client.host or "default"

    # --- Memory: save last user message ---
    try:
        last_user_msg = ""
        for m in reversed(body.messages):
            if m.role == "user" and (m.content or "").strip():
                last_user_msg = m.content.strip()
                break
        if last_user_msg:
            save_message(user_id, "user", last_user_msg, tags=["chat"])
    except Exception:
        pass

    # 🔥 PRE-PROCESSING: Add conversation to memory BEFORE cognitive engine
    # This ensures memory is available during context building
    plain_last_user = next((m.content for m in reversed(body.messages) if m.role == "user"), "")
    
    # Delegate all logic to the cognitive engine (with memory context injected!)
    result = await cognitive_engine.process_message(user_id, [m.dict() for m in body.messages], req)

    # 🔥 POST-PROCESSING: Save the turn to UNIFIED MEMORY after getting response
    if MEMORY_ENABLED and plain_last_user and result.get("answer"):
        try:
            memory_add_conversation(
                user_id=user_id,
                user_msg=plain_last_user,
                assistant_msg=result["answer"],
                intent=result.get("metadata", {}).get("intent", "chat")
            )
            log_info(f"[MEMORY] Conversation saved for user {user_id}")
        except Exception as e:
            log_warning(f"⚠️ Error during unified memory save: {e}")

    return ChatResponse(
        ok=True,
        answer=result.get("answer", "Error processing response."),
        sources=result.get("sources", []),
        metadata=result.get("metadata", {})
    )

# --- LEAN STREAMING ENDPOINT (UPGRADED - auto memory integration!) ---
@router.post("/assistant/stream")
async def chat_assistant_stream(body: ChatRequest, req: Request, _=Depends(_auth)):
    from .config import MEMORY_ENABLED
    from .memory import memory_add_conversation
    
    user_id = body.user_id or req.client.host or "default"

    async def generate():
        result = await cognitive_engine.process_message(user_id, [m.dict() for m in body.messages], req)
        answer = result.get("answer", "Error processing stream.")

        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        # Simulate streaming for now
        for i in range(0, len(answer), 48):
            chunk = answer[i:i+48]
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            await asyncio.sleep(0.01)
        
        yield f"data: {json.dumps({'type': 'complete', 'answer': answer, 'metadata': result.get('metadata', {})})}\n\n"

        # 🔥 Save to UNIFIED MEMORY after stream completion
        plain_last_user = next((m.content for m in reversed(body.messages) if m.role == "user"), "")
        
        if MEMORY_ENABLED and plain_last_user and answer:
            try:
                memory_add_conversation(
                    user_id=user_id,
                    user_msg=plain_last_user,
                    assistant_msg=answer,
                    intent=result.get("metadata", {}).get("intent", "chat")
                )
                log_info(f"[MEMORY] Stream conversation saved for user {user_id}")
            except Exception as e:
                log_warning(f"⚠️ Error during unified memory save: {e}")

    return StreamingResponse(generate(), media_type="text/event-stream")

# --- AUTO-LEARN ENDPOINT ---
class AutoLearnRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default"
    force_learn: bool = True

@router.post("/auto", response_model=ChatResponse)
async def force_auto_learn(body: AutoLearnRequest, req: Request, _=Depends(_auth)):
    from core.research import autonauka
    
    user_id = body.user_id or req.client.host or "default"
    
    try:
        # Wywołaj autonauka z przekazanym zapytaniem (z integracją pamięci hierarchicznej)
        result = await autonauka(body.query, topk=8, deep_research=body.force_learn, user_id=user_id)
        
        # Przygotuj odpowiedź
        context = result.get("context", "")
        facts = result.get("facts", [])
        sources = result.get("sources", [])
        
        # Przygotuj odpowiedź tekstową
        answer = f"Wykonałem autonaukę dla zapytania: '{body.query}'\n\n"
        
        if facts:
            answer += "📚 Najważniejsze fakty:\n\n"
            for i, fact in enumerate(facts[:5], 1):
                answer += f"{i}. {fact}\n\n"
        
        if sources:
            answer += "📑 Źródła:\n\n"
            for i, source in enumerate(sources[:5], 1):
                title = source.get("title") or "Źródło"
                url = source.get("url") or "#"
                answer += f"{i}. {title} - {url}\n"
        
        # Dodaj informację o liczbie znalezionych materiałów
        answer += f"\nZnaleziono {result.get('source_count', 0)} źródeł. Wiedza została zapisana w pamięci długoterminowej."
        
        return ChatResponse(
            ok=True,
            answer=answer,
            sources=sources[:5],
            metadata={
                "auto_learned": True,
                "source_count": result.get("source_count", 0),
                "facts_count": len(facts),
                "query": body.query,
                "deep_research": body.force_learn,
                "powered_by": result.get("powered_by", "unknown"),
                "hierarchical_memory": result.get("hierarchical_memory", {}),
                "hierarchical_confidence": result.get("hierarchical_confidence", 0)
            }
        )
    except Exception as e:
        print(f"⚠️ Error during force auto-learn: {e}")
        return ChatResponse(
            ok=False,
            answer=f"Błąd podczas autonauki: {str(e)}",
            metadata={"error": str(e)}
        )
