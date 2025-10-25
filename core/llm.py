#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM module - Language Model interaction with retry logic and fallback
"""

import time
import httpx
import hashlib
import json
from typing import List, Dict, Any, Optional

from .config import (
    LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_FALLBACK_MODEL,
    LLM_TIMEOUT, LLM_RETRIES, LLM_BACKOFF_S
)
from .helpers import log_error, log_warning, log_info

# Import Redis cache
try:
    from .redis_middleware import get_redis
    REDIS_AVAILABLE = True
except Exception as e:
    log_warning(f"Redis cache not available: {e}")
    REDIS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════
# CACHE UTILITIES
# ═══════════════════════════════════════════════════════════════════

def _generate_cache_key(messages: List[dict], model: str, **opts) -> str:
    """Generate cache key from LLM request parameters"""
    cache_data = {
        "model": model,
        "messages": messages,
        "temperature": opts.get("temperature"),
        "max_tokens": opts.get("max_tokens")
    }
    cache_string = json.dumps(cache_data, sort_keys=True)
    return f"llm:{hashlib.sha256(cache_string.encode()).hexdigest()}"


# ═══════════════════════════════════════════════════════════════════
# LLM REQUEST FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _llm_request(messages: List[dict], model: str, **opts) -> str:
    """
    Send request to DeepInfra with retry/backoff and shorter timeout
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model identifier
        **opts: Optional parameters:
            - temperature: float (0.0-1.0)
            - max_tokens: int
            - timeout_s: float (timeout in seconds)
            
    Returns:
        str: LLM response content
        
    Raises:
        Exception: If all retries fail
    """
    url = f"{LLM_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {"model": model, "messages": messages}
    
    # Add optional parameters
    if "temperature" in opts and opts.get("temperature") is not None:
        payload["temperature"] = float(opts.get("temperature"))
    
    if "max_tokens" in opts and opts.get("max_tokens") is not None:
        try:
            payload["max_tokens"] = int(opts.get("max_tokens"))
        except Exception:
            pass
    
    # Retry logic
    retries = opts.get("retries", LLM_RETRIES)
    backoff_s = opts.get("backoff_s", LLM_BACKOFF_S)
    last_exc: Optional[Exception] = None
    
    for attempt in range(1, retries + 1):
        try:
            timeout_s = float(opts.get("timeout_s", LLM_TIMEOUT))
            
            with httpx.Client(timeout=timeout_s) as client:
                r = client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
                
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if attempt > 1:
                    log_info(f"LLM request succeeded on attempt {attempt}", "LLM")
                
                return content
                
        except Exception as e:
            last_exc = e
            
            if attempt < retries:
                sleep_time = backoff_s * attempt
                log_warning(f"LLM request failed (attempt {attempt}/{retries}), retrying in {sleep_time}s: {e}", "LLM")
                time.sleep(sleep_time)
            else:
                log_error(e, "LLM_REQUEST")
                raise
    
    # Should not reach here, but just in case
    raise last_exc if last_exc else Exception("Unknown LLM error")


def call_llm(messages: List[dict], **opts) -> str:
    """
    Call LLM with fallback mechanism + Redis cache
    
    1️⃣ Check Redis cache
    2️⃣ If miss → Try main model (LLM_MODEL)
    3️⃣ If fails → try fallback model (LLM_FALLBACK_MODEL)
    4️⃣ Store result in Redis cache
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        **opts: Optional parameters:
            - temperature: float (0.0-1.0)
            - max_tokens: int
            - timeout_s: float
            - skip_cache: bool (default: False) - skip Redis cache
            - cache_ttl: int (default: 3600) - cache TTL in seconds
        
    Returns:
        str: LLM response content (or error message if both fail)
    """
    # Check if cache should be used
    skip_cache = opts.pop("skip_cache", False)
    cache_ttl = opts.pop("cache_ttl", 3600)  # 1 hour default
    
    # Try Redis cache first (unless skip_cache=True)
    if REDIS_AVAILABLE and not skip_cache:
        try:
            redis = get_redis()
            cache_key = _generate_cache_key(messages, LLM_MODEL, **opts)
            
            cached_result = redis.get(cache_key)
            if cached_result is not None:
                log_info(f"[CACHE HIT] LLM response from Redis", "LLM")
                return cached_result
            
            log_info(f"[CACHE MISS] Calling LLM API", "LLM")
        except Exception as e:
            log_warning(f"Redis cache check failed: {e}", "LLM")
    
    # Try main model
    try:
        result = _llm_request(messages, LLM_MODEL, **opts)
        
        # Store in Redis cache
        if REDIS_AVAILABLE and not skip_cache:
            try:
                redis = get_redis()
                cache_key = _generate_cache_key(messages, LLM_MODEL, **opts)
                redis.set(cache_key, result, ttl=cache_ttl)
                log_info(f"[CACHE STORE] Saved LLM response to Redis (TTL: {cache_ttl}s)", "LLM")
            except Exception as e:
                log_warning(f"Redis cache store failed: {e}", "LLM")
        
        return result
        
    except Exception as e1:
        log_warning(f"Main model failed: {e1} — trying fallback {LLM_FALLBACK_MODEL}", "LLM")
        
        # Try fallback model
        try:
            result = _llm_request(messages, LLM_FALLBACK_MODEL, **opts)
            
            # Store fallback result in cache with shorter TTL
            if REDIS_AVAILABLE and not skip_cache:
                try:
                    redis = get_redis()
                    cache_key = _generate_cache_key(messages, LLM_FALLBACK_MODEL, **opts)
                    redis.set(cache_key, result, ttl=cache_ttl // 2)  # Half TTL for fallback
                except Exception:
                    pass
            
            return result
            
        except Exception as e2:
            log_error(e2, "LLM_FALLBACK")
            return f"[LLM-FAIL] Main: {str(e1)[:100]}... Fallback: {str(e2)[:100]}"


def call_llm_once(prompt: str, temperature: float = 0.8, **opts) -> str:
    """
    Call LLM with a single user prompt (convenience function)
    
    Args:
        prompt: User prompt text
        temperature: Temperature setting (0.0-1.0)
        **opts: Additional options
        
    Returns:
        str: LLM response
    """
    messages = [{"role": "user", "content": prompt}]
    return call_llm(messages, temperature=temperature, max_tokens=None, **opts)


# ═══════════════════════════════════════════════════════════════════
# STREAMING SUPPORT (for future use)
# ═══════════════════════════════════════════════════════════════════

async def call_llm_stream(messages: List[dict], **opts):
    """
    Call LLM with streaming response (async generator)
    
    Args:
        messages: List of message dicts
        **opts: Optional parameters
        
    Yields:
        str: Chunks of response text
    """
    url = f"{LLM_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": opts.get("model", LLM_MODEL),
        "messages": messages,
        "stream": True
    }
    
    if "temperature" in opts:
        payload["temperature"] = float(opts["temperature"])
    if "max_tokens" in opts:
        payload["max_tokens"] = int(opts["max_tokens"])
    
    timeout_s = float(opts.get("timeout_s", LLM_TIMEOUT))
    
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            import json
                            data = json.loads(data_str)
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            
                            if content:
                                yield content
                        except:
                            continue
                            
    except Exception as e:
        log_error(e, "LLM_STREAM")
        yield f"[STREAM-ERROR] {str(e)}"


# ═══════════════════════════════════════════════════════════════════
# PROMPT HELPERS
# ═══════════════════════════════════════════════════════════════════

def build_chat_messages(system_prompt: str, user_message: str, context: Optional[str] = None) -> List[dict]:
    """
    Build messages array for LLM chat
    
    Args:
        system_prompt: System instruction
        user_message: User's message
        context: Optional context to inject
        
    Returns:
        List[dict]: Messages array for LLM
    """
    messages = [{"role": "system", "content": system_prompt}]
    
    if context:
        messages.append({
            "role": "system",
            "content": f"Context:\n{context}"
        })
    
    messages.append({"role": "user", "content": user_message})
    
    return messages


def truncate_messages(messages: List[dict], max_tokens: int = 4000) -> List[dict]:
    """
    Truncate messages to fit within token limit (rough estimation)
    
    Args:
        messages: List of messages
        max_tokens: Maximum token count (rough estimate: 1 token ≈ 4 chars)
        
    Returns:
        List[dict]: Truncated messages
    """
    # Rough estimation: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    
    # Always keep system message
    if not messages or messages[0].get("role") != "system":
        return messages
    
    result = [messages[0]]  # Keep system message
    current_chars = len(messages[0].get("content", ""))
    
    # Add messages from end (most recent first)
    for msg in reversed(messages[1:]):
        content = msg.get("content", "")
        msg_chars = len(content)
        
        if current_chars + msg_chars > max_chars:
            break
        
        result.insert(1, msg)  # Insert after system message
        current_chars += msg_chars
    
    return result


def sanitize_llm_response(text: str) -> str:
    """
    Sanitize LLM response (remove unwanted patterns, etc.)
    
    Args:
        text: LLM response text
        
    Returns:
        str: Sanitized text
    """
    # Remove common LLM artifacts
    text = text.strip()
    
    # Remove multiple consecutive newlines
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing ellipsis at the end (incomplete responses)
    if text.endswith("...") and len(text) > 10:
        text = text[:-3].strip()
    
    return text


# ═══════════════════════════════════════════════════════════════════
# DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════

def get_llm_config() -> Dict[str, Any]:
    """
    Get current LLM configuration
    
    Returns:
        Dict with LLM config info
    """
    return {
        "base_url": LLM_BASE_URL,
        "model": LLM_MODEL,
        "fallback_model": LLM_FALLBACK_MODEL,
        "timeout": LLM_TIMEOUT,
        "retries": LLM_RETRIES,
        "backoff": LLM_BACKOFF_S,
        "api_key_set": bool(LLM_API_KEY)
    }


# ═══════════════════════════════════════════════════════════════════
# COMPATIBILITY - Legacy LLM Client Interface
# ═══════════════════════════════════════════════════════════════════

class LLMClient:
    """
    Kompatybilność wsteczna dla starych modułów używających get_llm_client()
    Używa call_llm() jako backend
    """
    
    async def chat_completion(self, messages: List[dict], **opts) -> str:
        """Async wrapper dla call_llm"""
        return call_llm(messages, **opts)
    
    def chat_completion_sync(self, messages: List[dict], **opts) -> str:
        """Sync wrapper dla call_llm"""
        return call_llm(messages, **opts)


def get_llm_client() -> LLMClient:
    """
    Zwraca LLM client dla kompatybilności wstecznej
    
    Returns:
        LLMClient instance
    """
    return LLMClient()


# Alias dla kompatybilności
call_llm_raw = call_llm
