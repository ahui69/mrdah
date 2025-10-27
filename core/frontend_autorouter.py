#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 MORDZIX AI - FRONTEND AUTOROUTER INTEGRATOR
Łączy zaawansowany AutoRouter z frontendem React
Automatyczne przekierowanie wszystkich ≈170 endpointów
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json

from .advanced_autorouter import smart_route, auto_router, EndpointCategory
from .response_adapter import adapt

router = APIRouter(prefix="/api/autoroute", tags=["autorouter"])

class AutoRouteRequest(BaseModel):
    user_input: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

class AutoRouteResponse(BaseModel):
    endpoint: str
    category: str  
    confidence: float
    reasoning: str
    params: Dict[str, Any]
    suggestions: List[str]

class ExecuteRouteRequest(BaseModel):
    user_input: str
    context: Optional[Dict[str, Any]] = None
    auto_execute: bool = True

@router.post("/analyze")
async def analyze_route(request: AutoRouteRequest):
    """
    🎯 Analizuje input użytkownika i zwraca najlepszy endpoint
    
    Usage z frontu:
    ```javascript
    const result = await fetch('/api/autoroute/analyze', {
        method: 'POST',
        body: JSON.stringify({
            user_input: "sprawdź pogodę w Warszawie",
            context: { hour: 14, recent_categories: ["research"] }
        })
    });
    ```
    """
    try:
        result = smart_route(request.user_input, request.context)
        
        # Generuj sugestie podobnych endpointów
        suggestions = _generate_suggestions(result.category)
        
        return adapt({
            "ok": True,
            "route": {
                "endpoint": result.endpoint,
                "category": result.category.value,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "params": result.params,
                "suggestions": suggestions
            }
        })
        
    except Exception as e:
        return adapt({
            "ok": False,
            "error": f"AutoRoute analysis failed: {str(e)}",
            "fallback_endpoint": "/api/chat/message"
        })

@router.post("/execute")
async def execute_route(request: ExecuteRouteRequest):
    """
    ⚡ Analizuje input I AUTOMATYCZNIE WYKONUJE odpowiedni endpoint
    
    To jest główna funkcja dla frontu - one-click routing!
    """
    try:
        # 1. Analizuj routing
        route_result = smart_route(request.user_input, request.context)
        
        if not request.auto_execute:
            return adapt({
                "ok": True,
                "analysis_only": True,
                "route": {
                    "endpoint": route_result.endpoint,
                    "category": route_result.category.value,
                    "confidence": route_result.confidence,
                    "reasoning": route_result.reasoning,
                    "params": route_result.params
                }
            })
        
        # 2. Wykonaj właściwy endpoint
        execution_result = await _execute_endpoint(
            route_result.endpoint,
            request.user_input,
            route_result.params,
            request.context
        )
        
        return adapt({
            "ok": True,
            "auto_routed": True,
            "route": {
                "endpoint": route_result.endpoint,
                "category": route_result.category.value,
                "confidence": route_result.confidence,
                "reasoning": route_result.reasoning
            },
            "result": execution_result
        })
        
    except Exception as e:
        # Fallback do chatu w przypadku błędu
        return adapt({
            "ok": False,
            "error": f"AutoRoute execution failed: {str(e)}",
            "fallback_used": True,
            "fallback_result": {
                "response": f"Przepraszam, wystąpił błąd podczas automatycznego routingu. Odpowiadam jako chat: {request.user_input}"
            }
        })

@router.get("/endpoints")
async def get_available_endpoints():
    """
    📋 Zwraca mapę wszystkich dostępnych endpointów dla frontu
    
    Przydatne do generowania UI, podpowiedzi, itp.
    """
    try:
        endpoints_map = auto_router.get_available_endpoints()
        
        # Dodaj statystyki
        total_endpoints = sum(len(eps) for eps in endpoints_map.values())
        
        return adapt({
            "ok": True,
            "total_categories": len(endpoints_map),
            "total_endpoints": total_endpoints,
            "endpoints_by_category": endpoints_map,
            "categories": [
                {
                    "id": cat.value,
                    "name": cat.value.title(),
                    "description": _get_category_description(cat),
                    "endpoint_count": len(endpoints_map.get(cat.value, []))
                }
                for cat in EndpointCategory
            ]
        })
        
    except Exception as e:
        return adapt({
            "ok": False,
            "error": f"Failed to get endpoints: {str(e)}"
        })

@router.get("/stats")
async def get_routing_stats():
    """
    📊 Statystyki routingu dla dashboardu admina
    """
    # W rzeczywistej implementacji dane z Redis/DB
    return adapt({
        "ok": True,
        "stats": {
            "total_routes_today": 1247,
            "most_used_category": "research",
            "average_confidence": 0.87,
            "success_rate": 0.94,
            "top_endpoints": [
                {"endpoint": "/api/research/search", "count": 234},
                {"endpoint": "/api/chat/message", "count": 189},
                {"endpoint": "/api/code/exec", "count": 156},
                {"endpoint": "/api/writing/generate", "count": 98}
            ]
        }
    })

async def _execute_endpoint(endpoint: str, user_input: str, params: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    🚀 Wewnętrzna funkcja wykonywania endpointów
    
    Mapuje endpoint na właściwą funkcję i wykonuje ją
    """
    import httpx
    
    # Przygotuj payload
    payload = {
        "input": user_input,
        "params": params,
        "context": context or {}
    }
    
    # W rzeczywistej implementacji - wywołania wewnętrzne
    # Tu przykład HTTP call dla demonstracji
    try:
        async with httpx.AsyncClient() as client:
            # Localhost call do naszego serwera
            response = await client.post(
                f"http://localhost:8000{endpoint}",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Endpoint returned {response.status_code}",
                    "details": response.text[:200]
                }
                
    except Exception as e:
        return {
            "error": f"Failed to execute endpoint {endpoint}",
            "details": str(e)
        }

def _generate_suggestions(category: EndpointCategory) -> List[str]:
    """Generuj sugestie podobnych endpointów"""
    suggestions_map = {
        EndpointCategory.RESEARCH: [
            "Sprawdź aktualne wiadomości",
            "Wyszukaj informacje o...",
            "Znajdź definicję słowa",
            "Pobierz dane z Wikipedii"
        ],
        EndpointCategory.CODING: [
            "Napisz kod Python",
            "Debuguj błąd",
            "Stwórz aplikację",
            "Wykonaj skrypt"
        ],
        EndpointCategory.WRITING: [
            "Napisz artykuł o...",
            "Stwórz post na social media",
            "Napisz email marketingowy",
            "Popraw gramatykę tekstu"
        ],
        EndpointCategory.CHAT: [
            "Pogadajmy o...",
            "Opowiedz mi o...",
            "Co myślisz o...",
            "Wyjaśnij mi..."
        ]
    }
    
    return suggestions_map.get(category, ["Zadaj pytanie", "Poproś o pomoc"])

def _get_category_description(category: EndpointCategory) -> str:
    """Opisy kategorii dla frontu"""
    descriptions = {
        EndpointCategory.RESEARCH: "Wyszukiwanie informacji, aktualne dane, Wikipedia",
        EndpointCategory.CODING: "Programowanie, wykonywanie kodu, debugging",
        EndpointCategory.WRITING: "Tworzenie treści, artykuły, copywriting",
        EndpointCategory.FILES: "Operacje na plikach, upload, zarządzanie",
        EndpointCategory.MEMORY: "Zapamiętywanie, historia, kontekst",
        EndpointCategory.PSYCHE: "Personalność AI, nastroje, emocje",
        EndpointCategory.AUDIO: "Mowa, dźwięk, TTS, STT",
        EndpointCategory.TRAVEL: "Podróże, rezerwacje, planowanie",
        EndpointCategory.ADMIN: "Administracja, zarządzanie systemem",
        EndpointCategory.COGNITIVE: "Zaawansowana analiza, myślenie",
        EndpointCategory.SUGGESTIONS: "Rekomendacje, pomysły",
        EndpointCategory.CHAT: "Ogólna konwersacja, domyślny tryb"
    }
    
    return descriptions.get(category, "Funkcjonalność AI")

# Funkcje pomocnicze dla frontu
def get_smart_suggestions(user_input: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Generuj smart suggestions dla autocomplete"""
    route_result = smart_route(user_input)
    
    suggestions = []
    if route_result.confidence > 0.7:
        category_suggestions = _generate_suggestions(route_result.category)
        for i, suggestion in enumerate(category_suggestions[:limit]):
            suggestions.append({
                "text": suggestion,
                "category": route_result.category.value,
                "confidence": max(0.5, route_result.confidence - i * 0.1)
            })
    
    return suggestions