#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASHION ENDPOINT - AI Fashion Manager Integration
Generowanie stylizacji, analiza trendów, rozpoznawanie marek
"""

from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from typing import List, Dict, Any, Optional
import json
import base64
from pydantic import BaseModel

from core.auth import verify_token
from core.ai_fashion import AIFashionManager
from core.helpers import log_info, log_error

# Utwórz router
router = APIRouter(
    prefix="/api/fashion",
    tags=["AI Fashion"],
    responses={404: {"description": "Not found"}},
)

# Globalna instancja AI Fashion Manager
fashion_manager = AIFashionManager()

# Pydantic Models
class OutfitRequest(BaseModel):
    occasion: str
    weather: str
    style_preferences: Dict[str, Any]
    user_id: Optional[str] = "default"

class TrendRequest(BaseModel):
    category: str
    timeframe: str
    region: str = "global"
    user_id: Optional[str] = "default"

class BrandDetectionRequest(BaseModel):
    description: Optional[str] = None
    user_id: Optional[str] = "default"

@router.on_event("startup")
async def startup_fashion():
    """Initialize AI Fashion Manager on startup"""
    try:
        await fashion_manager.initialize()
        log_info("AI Fashion Manager initialized successfully")
    except Exception as e:
        log_error(f"Failed to initialize AI Fashion Manager: {e}")

@router.post("/generate-outfit", summary="Generuje stylizację na podstawie okazji i pogody")
async def generate_outfit(
    request: OutfitRequest,
    auth=Depends(verify_token)
):
    """
    Generuje stylizację na podstawie okazji, pogody i preferencji stylu.
    
    Args:
        request: Zawiera occasion, weather, style_preferences, user_id
        
    Returns:
        Pełną stylizację z rekomendacjami
    """
    try:
        result = await fashion_manager.generate_outfit(
            occasion=request.occasion,
            weather=request.weather,
            style_preferences=request.style_preferences,
            user_id=request.user_id
        )
        
        return {
            "ok": True,
            "result": result,
            "message": f"Wygenerowano stylizację na okazję: {request.occasion}"
        }
        
    except Exception as e:
        log_error(f"Outfit generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forecast-trends", summary="Prognozuje trendy modowe")
async def forecast_trends(
    request: TrendRequest,
    auth=Depends(verify_token)
):
    """
    Prognozuje trendy modowe dla danej kategorii i okresu.
    
    Args:
        request: Zawiera category, timeframe, region, user_id
        
    Returns:
        Prognozy trendów z poziomem pewności
    """
    try:
        result = await fashion_manager.forecast_trends(
            category=request.category,
            timeframe=request.timeframe,
            region=request.region,
            user_id=request.user_id
        )
        
        return {
            "ok": True,
            "result": result,
            "message": f"Prognoza trendów dla kategorii: {request.category}"
        }
        
    except Exception as e:
        log_error(f"Trend forecasting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-brand", summary="Rozpoznaje markę z obrazu")
async def detect_brand(
    request: BrandDetectionRequest,
    image: UploadFile = File(...),
    auth=Depends(verify_token)
):
    """
    Rozpoznaje markę modową z przesłanego obrazu.
    
    Args:
        request: Zawiera description (opcjonalne), user_id
        image: Przesłany obraz do analizy
        
    Returns:
        Rozpoznaną markę z prawdopodobieństwem
    """
    try:
        # Przeczytaj obraz i zakoduj w base64
        image_data = await image.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Zapisz tymczasowo obraz (w produkcji lepiej użyć storage)
        temp_filename = f"/tmp/fashion_image_{request.user_id}_{int(time.time())}.jpg"
        with open(temp_filename, "wb") as f:
            f.write(image_data)
        
        result = await fashion_manager.detect_brand(
            image_file=temp_filename,
            description=request.description,
            user_id=request.user_id
        )
        
        # Usuń tymczasowy plik
        import os
        os.unlink(temp_filename)
        
        return {
            "ok": True,
            "result": result,
            "message": "Rozpoznano markę z obrazu"
        }
        
    except Exception as e:
        log_error(f"Brand detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories", summary="Pobiera dostępne kategorie mody")
async def get_fashion_categories(auth=Depends(verify_token)):
    """
    Pobiera listę dostępnych kategorii mody.
    
    Returns:
        Lista kategorii modowych
    """
    try:
        categories = [
            "casualwear", "formalwear", "sportswear", "streetwear",
            "vintage", "bohemian", "minimalist", "luxury",
            "accessories", "footwear", "outerwear", "underwear"
        ]
        
        return {
            "ok": True,
            "categories": categories,
            "message": "Lista kategorii mody"
        }
        
    except Exception as e:
        log_error(f"Categories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/occasions", summary="Pobiera dostępne okazje")
async def get_occasions(auth=Depends(verify_token)):
    """
    Pobiera listę dostępnych okazji do stylizacji.
    
    Returns:
        Lista okazji
    """
    try:
        occasions = [
            "work", "casual", "party", "date", "wedding",
            "interview", "travel", "gym", "beach", "formal",
            "business", "weekend", "evening", "brunch"
        ]
        
        return {
            "ok": True,
            "occasions": occasions,
            "message": "Lista okazji do stylizacji"
        }
        
    except Exception as e:
        log_error(f"Occasions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather-types", summary="Pobiera typy pogody")
async def get_weather_types(auth=Depends(verify_token)):
    """
    Pobiera listę typów pogody do stylizacji.
    
    Returns:
        Lista typów pogody
    """
    try:
        weather_types = [
            "sunny", "rainy", "cloudy", "snowy", "windy",
            "hot", "cold", "mild", "humid", "dry"
        ]
        
        return {
            "ok": True,
            "weather_types": weather_types,
            "message": "Lista typów pogody"
        }
        
    except Exception as e:
        log_error(f"Weather types error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", summary="Pobiera statystyki AI Fashion")
async def get_fashion_stats(auth=Depends(verify_token)):
    """
    Pobiera statystyki użycia AI Fashion Manager.
    
    Returns:
        Statystyki systemu mody
    """
    try:
        stats = {
            "outfits_generated": len(fashion_manager.outfits_db),
            "trends_analyzed": len(fashion_manager.trends_db),
            "brands_detected": len(fashion_manager.brands_db),
            "fashion_data_size": len(fashion_manager.fashion_data)
        }
        
        return {
            "ok": True,
            "stats": stats,
            "message": "Statystyki AI Fashion Manager"
        }
        
    except Exception as e:
        log_error(f"Fashion stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))