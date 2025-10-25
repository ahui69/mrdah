#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper functions - Utilities for text processing, HTTP, vectors, etc.
"""

import re
import json
import math
import hashlib
import hmac
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qs
from urllib.request import Request, urlopen
from collections import Counter
from dataclasses import dataclass, asdict

from .config import HTTP_TIMEOUT, LLM_API_KEY, AUTH_TOKEN


# ═══════════════════════════════════════════════════════════════════
# LOGGING UTILITIES
# ═══════════════════════════════════════════════════════════════════

def log_info(msg: str, ctx: str = ""):
    """Log info message"""
    print(f"[INFO]{('['+ctx+']') if ctx else ''} {msg}")


def log_warning(msg: str, ctx: str = ""):
    """Log warning message"""
    print(f"[WARN]{('['+ctx+']') if ctx else ''} {msg}")


def log_error(err: Exception, ctx: str = ""):
    """Log error message"""
    print(f"[ERROR]{('['+ctx+']') if ctx else ''} {err}")


# ═══════════════════════════════════════════════════════════════════
# HTTP UTILITIES
# ═══════════════════════════════════════════════════════════════════

# Default headers for HTTP requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

JSON_HEAD = {
    **HEADERS,
    "Content-Type": "application/json"
}


def http_get(url: str, headers=None, timeout=HTTP_TIMEOUT) -> str:
    """
    HTTP GET request
    
    Args:
        url: URL to request
        headers: Optional additional headers
        timeout: Request timeout in seconds
        
    Returns:
        str: Response body
    """
    h = dict(HEADERS)
    h.update(headers or {})
    req = Request(url, headers=h, method="GET")
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def http_get_json(url: str, headers=None, timeout=HTTP_TIMEOUT) -> Any:
    """
    HTTP GET request with JSON response
    
    Args:
        url: URL to request
        headers: Optional additional headers
        timeout: Request timeout in seconds
        
    Returns:
        Any: Parsed JSON response
    """
    raw = http_get(url, headers=headers, timeout=timeout)
    try:
        return json.loads(raw)
    except:
        return {"raw": raw}


def http_post_json(url: str, payload: dict, headers=None, timeout=HTTP_TIMEOUT) -> Any:
    """
    HTTP POST request with JSON payload and response
    
    Args:
        url: URL to request
        payload: JSON payload to send
        headers: Optional additional headers
        timeout: Request timeout in seconds
        
    Returns:
        Any: Parsed JSON response
    """
    h = dict(JSON_HEAD)
    h.update(headers or {})
    req = Request(url, data=json.dumps(payload).encode("utf-8"), headers=h, method="POST")
    with urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
        try:
            return json.loads(raw)
        except:
            return {"raw": raw}


# ═══════════════════════════════════════════════════════════════════
# TEXT NORMALIZATION & TOKENIZATION
# ═══════════════════════════════════════════════════════════════════

def normalize_text(s: str) -> str:
    """
    Normalize text by collapsing whitespace
    
    Args:
        s: Input text
        
    Returns:
        str: Normalized text
    """
    return re.sub(r"\s+", " ", (s or "").strip())


def make_id(s: str) -> str:
    """
    Generate SHA1 ID from normalized text
    
    Args:
        s: Input text
        
    Returns:
        str: SHA1 hex digest
    """
    return hashlib.sha1(normalize_text(s).encode("utf-8")).hexdigest()


def tokenize(s: str) -> List[str]:
    """
    Tokenize Polish text with abbreviation expansion
    
    Args:
        s: Input text
        
    Returns:
        List[str]: List of tokens (words > 2 chars, max 256 tokens)
    """
    s = (s or "").lower()
    
    # Polish abbreviations
    skroty = {
        "wg": "według", "np": "na przykład", "itd": "i tak dalej",
        "itp": "i tym podobne", "tzn": "to znaczy", "tzw": "tak zwany",
        "ok": "okej", "bd": "będzie", "jj": "jasne", "nwm": "nie wiem",
        "imo": "moim zdaniem", "tbh": "szczerze mówiąc",
        "fyi": "dla twojej informacji", "btw": "przy okazji"
    }
    
    words = s.split()
    for i, w in enumerate(words):
        cw = re.sub(r"[^\wąćęłńóśźż]", "", w)
        if cw in skroty:
            words[i] = skroty[cw]
    
    s2 = re.sub(r"[^0-9a-ząćęłńóśźż]+", " ", " ".join(words))
    return [w for w in s2.split() if len(w) > 2][:256]


def sentences_split(text: str) -> List[str]:
    """
    Split text into sentences
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of sentences (min 5 chars each)
    """
    if not text:
        return []
    raw = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in raw if len(s.strip()) >= 5]


# ═══════════════════════════════════════════════════════════════════
# TF-IDF & COSINE SIMILARITY
# ═══════════════════════════════════════════════════════════════════

def tfidf_vec(tokens: List[str], docs_tokens: List[List[str]]) -> Dict[str, float]:
    """
    Calculate TF-IDF vector for tokens given document corpus
    
    Args:
        tokens: Tokens to calculate TF-IDF for
        docs_tokens: List of tokenized documents (corpus)
        
    Returns:
        Dict[str, float]: TF-IDF vector
    """
    N = len(docs_tokens) or 1
    df: Dict[str, int] = {}
    
    for d in docs_tokens:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    
    tf = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    
    out = {}
    for t, c in tf.items():
        idf = (math.log((N + 1) / (df.get(t, 1) + 1))) ** 1.5
        bonus = (1 + 0.1 * min(max(len(t) - 3, 0), 7))
        out[t] = (c / max(1, len(tokens))) * idf * bonus
    
    return out


def tfidf_cosine(query: str, docs: List[str]) -> List[float]:
    """
    Calculate TF-IDF cosine similarity between query and documents
    
    Args:
        query: Query text
        docs: List of document texts
        
    Returns:
        List[float]: Cosine similarity scores for each document
    """
    tq = tokenize(query)
    dts = [tokenize(d) for d in docs]
    vq = tfidf_vec(tq, dts)
    
    out = []
    key_terms = set([t for t in tq if len(t) > 3])
    
    for dt in dts:
        vd = tfidf_vec(dt, dts)
        keys = set(vq.keys()) | set(vd.keys())
        num = 0.0
        
        for term in keys:
            a = vq.get(term, 0.0)
            b = vd.get(term, 0.0)
            term_bonus = 2.5 if term in key_terms else 1.0
            
            if " " in term:
                words = len(term.split())
                if words > 1:
                    term_bonus *= 1.0 + 0.5 * words
            
            boost = 1 + 0.8 * math.tanh(4 * a * b - 0.6)
            num += (a * b) * boost * term_bonus
        
        den = (sum(x * x for x in vq.values()) ** 0.5) * (sum(x * x for x in vd.values()) ** 0.5)
        score = 0.0 if den == 0 else (num / den)
        out.append(score ** 0.8)
    
    return out


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        float: Cosine similarity (0-1)
    """
    if not a or not b:
        return 0.0
    
    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    
    return s / (na * nb)


# ═══════════════════════════════════════════════════════════════════
# EMBEDDINGS WITH CACHE
# ═══════════════════════════════════════════════════════════════════

_EMBED_CACHE = {}
_EMBED_CACHE_HITS = 0
_EMBED_CACHE_MISSES = 0

# Embedding configuration (loaded from env if available)
# 🔥 UPGRADED: all-mpnet-base-v2 (768 dim) - było all-MiniLM-L6-v2 (384 dim)
EMBED_URL = "https://api.deepinfra.com/v1/openai/embeddings"
EMBED_MODEL = "sentence-transformers/all-mpnet-base-v2"


def embed_many(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts with caching
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    global _EMBED_CACHE, _EMBED_CACHE_HITS, _EMBED_CACHE_MISSES
    
    if not EMBED_URL or not EMBED_MODEL or not LLM_API_KEY:
        return []
    
    result = []
    texts_to_embed = []
    indices = []
    
    # Check cache for each text
    for i, text in enumerate(texts):
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in _EMBED_CACHE:
            result.append(_EMBED_CACHE[text_hash])
            _EMBED_CACHE_HITS += 1
        else:
            result.append(None)  # placeholder
            texts_to_embed.append(text)
            indices.append(i)
            _EMBED_CACHE_MISSES += 1
    
    # If everything from cache, return
    if not texts_to_embed:
        return result
    
    # Otherwise, generate embeddings for new texts
    payload = {"model": EMBED_MODEL, "input": texts_to_embed}
    
    try:
        req = Request(
            EMBED_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urlopen(req, timeout=HTTP_TIMEOUT) as r:
            j = json.loads(r.read().decode("utf-8", "replace"))
        
        embeddings = [d.get("embedding") for d in j.get("data", []) if d.get("embedding")]
        
        # Update cache and results
        for i, (text, embedding) in enumerate(zip(texts_to_embed, embeddings)):
            if embedding:
                text_hash = hashlib.md5(text.encode()).hexdigest()
                _EMBED_CACHE[text_hash] = embedding
                result[indices[i]] = embedding
        
        # If cache too large, remove oldest entries
        if len(_EMBED_CACHE) > 1000:
            for k in list(_EMBED_CACHE.keys())[:200]:
                del _EMBED_CACHE[k]
                
    except Exception as e:
        log_error(e, "EMBED")
    
    # Replace remaining None with empty lists
    for i in range(len(result)):
        if result[i] is None:
            result[i] = []
    
    return result


def get_embed_cache_stats() -> Dict[str, int]:
    """
    Get embedding cache statistics
    
    Returns:
        Dict with hits, misses, size
    """
    return {
        "hits": _EMBED_CACHE_HITS,
        "misses": _EMBED_CACHE_MISSES,
        "size": len(_EMBED_CACHE),
        "hit_rate": _EMBED_CACHE_HITS / max(1, _EMBED_CACHE_HITS + _EMBED_CACHE_MISSES)
    }


# Alias for backward compatibility with memory.py
def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Alias for embed_many() - for backward compatibility
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    return embed_many(texts)


# ═══════════════════════════════════════════════════════════════════
# NER / PII DETECTION
# ═══════════════════════════════════════════════════════════════════

# Regex patterns for PII and profile extraction
_PROFILE_PATS = {
    "age": re.compile(r"\b(?:mam|skończyłe[mn]|posiadam)\s*(\d{1,2})\s*(?:lat|lata|wiosen)\b", re.I),
    "email": re.compile(r"\b[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}\b", re.I),
    "phone": re.compile(r"\b(?:\+?48[-\s]?)?(?:\d{3}[-\s]?\d{3}[-\s]?\d{3})\b", re.I),
}

_LANG_PAT = re.compile(r"\b(?:mówię|znam|używam|uczę się)\s+(po\s+)?(polsku|angielsku|niemiecku|hiszpańsku|francusku|rosyjsku|ukraińsku|włosku)\b", re.I)
_TECH_PAT = re.compile(r"\b(Python|JS|Java|TypeScript|C\+\+|C#|Go|Rust|PHP|SQL|HTML|CSS)\b", re.I)
_NEGATION_PAT = re.compile(r"\b(nie|nie\s+bardzo|żadn[eyoa])\b", re.I)
_LINK_PAT = re.compile(r"\bhttps?://\S+\b", re.I)


def tag_pii(text: str) -> Tuple[str, List[str]]:
    """
    Detect PII (Personally Identifiable Information) in text
    
    Args:
        text: Input text
        
    Returns:
        Tuple[str, List[str]]: (text, list of PII tags)
    """
    tags = []
    
    if _PROFILE_PATS["email"].search(text):
        tags.append("pii:email")
    if _PROFILE_PATS["phone"].search(text):
        tags.append("pii:phone")
    if _LINK_PAT.search(text):
        tags.append("pii:link")
    
    return text, sorted(set(tags))


def extract_profile_info(text: str) -> Dict[str, Any]:
    """
    Extract profile information from text
    
    Args:
        text: Input text
        
    Returns:
        Dict with extracted profile info
    """
    info = {}
    
    # Age
    age_match = _PROFILE_PATS["age"].search(text)
    if age_match:
        info["age"] = int(age_match.group(1))
    
    # Email
    email_match = _PROFILE_PATS["email"].search(text)
    if email_match:
        info["email"] = email_match.group(0)
    
    # Phone
    phone_match = _PROFILE_PATS["phone"].search(text)
    if phone_match:
        info["phone"] = phone_match.group(0)
    
    # Languages
    lang_matches = _LANG_PAT.findall(text)
    if lang_matches:
        info["languages"] = [lang[1].lower() for lang in lang_matches]
    
    # Tech skills
    tech_matches = set(t.group(0) for t in _TECH_PAT.finditer(text))
    if tech_matches:
        info["tech_skills"] = list(tech_matches)
    
    return info


# ═══════════════════════════════════════════════════════════════════
# WSGI UTILITIES (Legacy compatibility)
# ═══════════════════════════════════════════════════════════════════

def parse_query_string(env: Dict[str, Any]) -> Dict[str, str]:
    """Parse WSGI query string"""
    q = parse_qs(env.get("QUERY_STRING", ""), keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in q.items()}


def read_json_body(env: Dict[str, Any]) -> Dict[str, Any]:
    """Read JSON from WSGI request body"""
    try:
        ln = int(env.get("CONTENT_LENGTH") or 0)
    except:
        ln = 0
    
    raw = env["wsgi.input"].read(ln) if ln > 0 else b""
    if not raw:
        return {}
    
    try:
        return json.loads(raw.decode("utf-8"))
    except:
        return {}


def get_cors_headers() -> List[Tuple[str, str]]:
    """Get CORS headers for responses"""
    from .config import ALLOWED_ORIGINS
    return [
        ("Access-Control-Allow-Origin", ALLOWED_ORIGINS),
        ("Access-Control-Allow-Headers", "Authorization, Content-Type"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE, PUT"),
    ]


def json_response(obj: Any, code: int = 200):
    """Create JSON response for WSGI"""
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    return (
        f"{code} OK",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(data)))
        ] + get_cors_headers(),
        [data]
    )


def error_response(msg: str, code: int = 400):
    """Create error JSON response"""
    return json_response({"ok": False, "error": msg}, code)
