#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Captcha solving endpoint - 2captcha integration
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import asyncio

router = APIRouter()

class CaptchaSolveRequest(BaseModel):
    site_key: str
    page_url: str
    captcha_type: str = "recaptchav2"  # recaptchav2, recaptchav3, hcaptcha

class CaptchaSolveResponse(BaseModel):
    ok: bool
    solution: Optional[str] = None
    error: Optional[str] = None

@router.post("/solve", response_model=CaptchaSolveResponse)
async def solve_captcha(body: CaptchaSolveRequest):
    """Rozwiąż captcha przez 2captcha API"""
    
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    if not api_key:
        return CaptchaSolveResponse(ok=False, error="Brak TWOCAPTCHA_API_KEY w .env")
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Submit captcha
            submit_resp = await client.get(
                "http://2captcha.com/in.php",
                params={
                    "key": api_key,
                    "method": body.captcha_type,
                    "googlekey": body.site_key,
                    "pageurl": body.page_url,
                    "json": 1
                }
            )
            
            submit_data = submit_resp.json()
            if submit_data.get("status") != 1:
                return CaptchaSolveResponse(ok=False, error=submit_data.get("request"))
            
            captcha_id = submit_data.get("request")
            
            # Poll for result (max 60s)
            for i in range(30):
                await asyncio.sleep(2)
                
                result_resp = await client.get(
                    "http://2captcha.com/res.php",
                    params={
                        "key": api_key,
                        "action": "get",
                        "id": captcha_id,
                        "json": 1
                    }
                )
                
                result_data = result_resp.json()
                if result_data.get("status") == 1:
                    return CaptchaSolveResponse(ok=True, solution=result_data.get("request"))
                elif result_data.get("request") != "CAPCHA_NOT_READY":
                    return CaptchaSolveResponse(ok=False, error=result_data.get("request"))
            
            return CaptchaSolveResponse(ok=False, error="Timeout - captcha nie została rozwiązana w 60s")
            
    except Exception as e:
        return CaptchaSolveResponse(ok=False, error=str(e))

@router.get("/balance")
async def get_balance():
    """Sprawdź saldo 2captcha"""
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    if not api_key:
        raise HTTPException(status_code=400, detail="Brak TWOCAPTCHA_API_KEY")
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "http://2captcha.com/res.php",
                params={"key": api_key, "action": "getbalance"}
            )
            return {"balance": float(resp.text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
