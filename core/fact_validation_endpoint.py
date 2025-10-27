#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FACT VALIDATION ENDPOINT - Multi-Source Fact Checking
Cross-check web facts, voting system, anti-hallucination
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel

from core.auth import verify_token
from core.fact_validation import (
    validate_fact_across_sources, batch_validate_facts,
    FactValidationResult, get_source_reliability
)
from core.helpers import log_info, log_error

# Utwórz router
router = APIRouter(
    prefix="/api/facts",
    tags=["Fact Validation"],
    responses={404: {"description": "Not found"}},
)


class FactValidationRequest(BaseModel):
    fact: str
    sources: List[str]
    min_sources: int = 3


class BatchFactValidationRequest(BaseModel):
    facts: List[str]
    min_sources: int = 3
    max_validation_time: float = 30.0


class SourceReliabilityRequest(BaseModel):
    url: str


@router.post("/validate", summary="Waliduje pojedynczy fakt")
async def validate_fact(
    request: FactValidationRequest,
    auth=Depends(verify_token)
):
    """
    Waliduje pojedynczy fakt przez cross-check z wieloma źródłami.
    Voting system: 2/3 sources must agree = valid.
    
    Args:
        request: fact, sources, min_sources
        
    Returns:
        Validation result z confidence score
    """
    try:
        # Konwersja sources na tuples (fact, source)
        facts_with_sources = [(request.fact, source) for source in request.sources]
        
        result = validate_fact_across_sources(
            fact=request.fact,
            all_facts_with_sources=facts_with_sources,
            min_sources=request.min_sources
        )
        
        return {
            "ok": True,
            "validation": {
                "fact": request.fact,
                "is_valid": result.is_valid,
                "confidence": result.confidence,
                "agreement_score": result.agreement_score,
                "supporting_sources": result.supporting_sources,
                "conflicting_sources": result.conflicting_sources,
                "source_count": result.source_count,
                "validation_time": result.validation_time
            },
            "message": f"Fakt {'zwalidowany' if result.is_valid else 'odrzucony'} z {result.confidence:.2f} confidence"
        }
        
    except Exception as e:
        log_error(f"Fact validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-batch", summary="Waliduje wiele faktów wsadowo")
async def validate_facts_batch(
    request: BatchFactValidationRequest,
    auth=Depends(verify_token)
):
    """
    Waliduje wiele faktów równocześnie (batch processing).
    Optymalizowane dla dużych list faktów.
    
    Args:
        request: facts[], min_sources, max_validation_time
        
    Returns:
        Batch validation results
    """
    try:
        results = batch_validate_facts(
            facts=request.facts,
            min_sources=request.min_sources,
            max_validation_time=request.max_validation_time
        )
        
        validated_count = sum(1 for r in results if r.is_valid)
        rejected_count = len(results) - validated_count
        
        return {
            "ok": True,
            "batch_results": [
                {
                    "fact": r.fact,
                    "is_valid": r.is_valid,
                    "confidence": r.confidence,
                    "agreement_score": r.agreement_score,
                    "source_count": r.source_count
                }
                for r in results
            ],
            "summary": {
                "total_facts": len(request.facts),
                "validated": validated_count,
                "rejected": rejected_count,
                "validation_rate": validated_count / len(request.facts) if request.facts else 0
            },
            "message": f"Batch validation: {validated_count}/{len(request.facts)} faktów zwalidowanych"
        }
        
    except Exception as e:
        log_error(f"Batch fact validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/source-reliability", summary="Sprawdza wiarygodność źródła")
async def check_source_reliability(
    request: SourceReliabilityRequest,
    auth=Depends(verify_token)
):
    """
    Sprawdza wiarygodność źródła na podstawie domeny.
    
    Args:
        request: url do sprawdzenia
        
    Returns:
        Reliability score (0.0 - 1.0)
    """
    try:
        reliability = get_source_reliability(request.url)
        
        # Określ kategorię wiarygodności
        if reliability >= 0.9:
            category = "Very High"
        elif reliability >= 0.8:
            category = "High"
        elif reliability >= 0.7:
            category = "Medium"
        elif reliability >= 0.6:
            category = "Low"
        else:
            category = "Very Low"
        
        return {
            "ok": True,
            "source": request.url,
            "reliability_score": reliability,
            "category": category,
            "message": f"Źródło ma {category.lower()} wiarygodność ({reliability:.2f})"
        }
        
    except Exception as e:
        log_error(f"Source reliability error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reliability-weights", summary="Pobiera wagi wiarygodności źródeł")
async def get_reliability_weights(auth=Depends(verify_token)):
    """
    Pobiera kompletną listę wag wiarygodności dla różnych domen.
    
    Returns:
        Dictionary z wagami źródeł
    """
    try:
        from core.fact_validation import SOURCE_RELIABILITY
        
        # Sortuj według wiarygodności (malejąco)
        sorted_sources = sorted(
            SOURCE_RELIABILITY.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            "ok": True,
            "source_weights": dict(sorted_sources),
            "high_reliability": [domain for domain, weight in sorted_sources if weight >= 0.9],
            "medium_reliability": [domain for domain, weight in sorted_sources if 0.7 <= weight < 0.9],
            "low_reliability": [domain for domain, weight in sorted_sources if weight < 0.7],
            "message": f"Wagi wiarygodności dla {len(SOURCE_RELIABILITY)} domen"
        }
        
    except Exception as e:
        log_error(f"Reliability weights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validation-stats", summary="Statystyki walidacji faktów")
async def get_validation_stats(auth=Depends(verify_token)):
    """
    Pobiera statystyki procesu walidacji faktów.
    
    Returns:
        Validation statistics i metrics
    """
    try:
        # W pełnej implementacji byłyby to rzeczywiste statystyki z bazy
        stats = {
            "total_validations": 0,  # Placeholder
            "validated_facts": 0,
            "rejected_facts": 0,
            "average_confidence": 0.0,
            "most_reliable_sources": [
                "wikipedia.org",
                "britannica.com", 
                "scholar.google.com"
            ],
            "validation_time_avg_ms": 0.0,
            "anti_hallucination_saves": 0
        }
        
        return {
            "ok": True,
            "stats": stats,
            "message": "Statystyki walidacji faktów"
        }
        
    except Exception as e:
        log_error(f"Validation stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))