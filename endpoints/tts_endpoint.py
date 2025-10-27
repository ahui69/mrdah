#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Endpoint - text-to-speech z ElevenLabs
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from tts_elevenlabs import text_to_speech, POLISH_VOICES

router = APIRouter(prefix="/api/tts", tags=["tts"])

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "rachel"

@router.post("/speak")
async def speak(req: TTSRequest):
    """
    Generuje audio z tekstu
    
    Body:
        {
            "text": "Tekst do wypowiedzenia",
            "voice": "rachel"  // opcjonalnie: rachel, antoni, adam, bella
        }
    
    Returns:
        audio/mpeg (MP3)
    """
    
    if not req.text or len(req.text) > 5000:
        raise HTTPException(400, "Tekst musi mieć 1-5000 znaków")
    
    # Get voice ID
    voice_id = POLISH_VOICES.get(req.voice.lower(), POLISH_VOICES["rachel"])
    
    # Generate audio
    audio_bytes = await text_to_speech(req.text, voice_id)
    
    if not audio_bytes:
        raise HTTPException(500, "Błąd generowania audio")
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename=speech.mp3"
        }
    )

@router.get("/voices")
async def list_voices():
    """Lista dostępnych głosów"""
    return {
        "voices": list(POLISH_VOICES.keys()),
        "default": "rachel"
    }
