#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HYBRID SEARCH ENDPOINT - Zaawansowane wyszukiwanie w pamięci
Łączy FTS5, Semantic Search i Fuzzy Matching z wizualizacją wyników
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
from .memory import ltm_search_hybrid

router = APIRouter(prefix="/api/search")

# ═══════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════

AUTH_TOKEN = os.getenv("AUTH_TOKEN", "ssjjMijaja6969")

def _auth(req: Request):
    """Autoryzacja przez Bearer token"""
    auth_header = req.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ═══════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════

class HybridSearchRequest(BaseModel):
    query: str
    limit: int = 10
    user_id: str = "default"
    show_breakdown: bool = True  # Czy zwracać breakdown score'ów
    min_score: float = 0.0  # Minimalny score do zwrócenia

class HybridSearchResponse(BaseModel):
    ok: bool
    query: str
    total_results: int
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(body: HybridSearchRequest, req: Request, _=Depends(_auth)):
    """
    🔥 ZAAWANSOWANE WYSZUKIWANIE HYBRYDOWE 🔥
    
    Łączy 3 metody:
    - FTS5 Full-Text Search (40%)
    - Semantic Vector Search (35%)
    - Fuzzy String Matching (25%)
    
    Zwraca najlepsze wyniki z breakdown score'ów i timestamp.
    """
    try:
        # Wykonaj hybrid search
        results = ltm_search_hybrid(
            query=body.query,
            limit=body.limit,
            user_id=body.user_id
        )
        
        # Filtruj po minimalnym score
        if body.min_score > 0.0:
            results = [r for r in results if r.get("score", 0.0) >= body.min_score]
        
        # Opcjonalnie usuń breakdown jeśli nie jest potrzebny
        if not body.show_breakdown:
            for r in results:
                r.pop("fts_score", None)
                r.pop("semantic_score", None)
                r.pop("fuzzy_score", None)
        
        # Metadata o wyszukiwaniu
        metadata = {
            "search_method": "hybrid_advanced",
            "methods_used": ["fts5", "semantic", "fuzzy"],
            "weights": {
                "fts5": 0.40,
                "semantic": 0.35,
                "fuzzy": 0.25,
                "recency_boost": 0.10
            },
            "total_found": len(results),
            "filtered_by_min_score": body.min_score > 0.0
        }
        
        return HybridSearchResponse(
            ok=True,
            query=body.query,
            total_results=len(results),
            results=results,
            metadata=metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/test")
async def test_search(
    q: str = "test",
    limit: int = 5,
    user_id: str = "default",
    _=Depends(_auth)
):
    """
    Quick test endpoint - GET request dla łatwego testowania
    
    Example: /api/search/test?q=python&limit=10
    """
    results = ltm_search_hybrid(query=q, limit=limit, user_id=user_id)
    
    return {
        "ok": True,
        "query": q,
        "total": len(results),
        "results": results,
        "tip": "Use POST /api/search/hybrid for full control"
    }


@router.get("/stats")
async def search_stats(user_id: str = "default", _=Depends(_auth)):
    """
    Statystyki pamięci użytkownika
    """
    try:
        from .memory import get_memory_system
        
        system = get_memory_system()
        con = system._connect()
        cur = con.cursor()
        
        # Count total conversations
        cur.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
        total_conversations = cur.fetchone()[0]
        
        # Get date range
        cur.execute("""
            SELECT MIN(timestamp), MAX(timestamp) 
            FROM conversations 
            WHERE user_id = ?
        """, (user_id,))
        min_ts, max_ts = cur.fetchone()
        
        # Count by role
        cur.execute("""
            SELECT role, COUNT(*) 
            FROM conversations 
            WHERE user_id = ? 
            GROUP BY role
        """, (user_id,))
        role_counts = dict(cur.fetchall())
        
        con.close()
        
        return {
            "ok": True,
            "user_id": user_id,
            "total_conversations": total_conversations,
            "role_breakdown": role_counts,
            "date_range": {
                "oldest": min_ts,
                "newest": max_ts
            },
            "search_capabilities": {
                "fts5": "enabled",
                "semantic": "enabled",
                "fuzzy": "enabled",
                "hybrid": "enabled"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")


@router.post("/compare")
async def compare_methods(
    query: str,
    limit: int = 5,
    user_id: str = "default",
    _=Depends(_auth)
):
    """
    🔬 PORÓWNANIE METOD WYSZUKIWANIA
    
    Wykonuje wyszukiwanie wszystkimi 3 metodami oddzielnie
    i pokazuje różnice w wynikach.
    """
    try:
        from .memory import get_memory_system
        
        system = get_memory_system()
        
        # === METHOD 1: FTS5 Only ===
        fts_results = []
        try:
            con = system._connect()
            cur = con.cursor()
            cur.execute("""
                SELECT content, rank 
                FROM conversations_fts 
                WHERE conversations_fts MATCH ? 
                ORDER BY rank 
                LIMIT ?
            """, (query, limit))
            
            for content, rank in cur.fetchall():
                fts_results.append({
                    "content": content,
                    "score": 1.0 / (1.0 + abs(rank))
                })
            con.close()
        except:
            pass
        
        # === METHOD 2: Semantic Only ===
        semantic_results = []
        try:
            sem_hits = system.search(query=query, user_id=user_id, limit=limit)
            semantic_results = [
                {"content": h.get("content", ""), "score": h.get("score", 0.0)}
                for h in sem_hits
            ]
        except:
            pass
        
        # === METHOD 3: Hybrid (All Combined) ===
        hybrid_results = ltm_search_hybrid(query=query, limit=limit, user_id=user_id)
        
        return {
            "ok": True,
            "query": query,
            "comparison": {
                "fts5_only": {
                    "method": "Full-Text Search (BM25)",
                    "weight": "40%",
                    "results": fts_results[:limit],
                    "count": len(fts_results)
                },
                "semantic_only": {
                    "method": "Vector Similarity",
                    "weight": "35%",
                    "results": semantic_results[:limit],
                    "count": len(semantic_results)
                },
                "hybrid": {
                    "method": "FTS5 + Semantic + Fuzzy",
                    "weight": "100% (weighted combination)",
                    "results": hybrid_results[:limit],
                    "count": len(hybrid_results)
                }
            },
            "explanation": {
                "fts5": "Best for exact phrase matching and keyword search",
                "semantic": "Best for understanding context and meaning",
                "fuzzy": "Best for typo tolerance and partial matches",
                "hybrid": "Combines all three for maximum accuracy"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# FRONTEND WIDGET HTML
# ═══════════════════════════════════════════════════════════════════

@router.get("/widget", response_class=__import__("fastapi.responses", fromlist=["HTMLResponse"]).HTMLResponse)
async def search_widget():
    """
    🎨 FRONTEND WIDGET - Interaktywny interfejs do testowania hybrid search
    """
    html = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 Hybrid Search - MORDZIX AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #667eea;
            border-radius: 10px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s;
        }
        
        input[type="text"]:focus {
            border-color: #764ba2;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .methods {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .method-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 10px 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
        }
        
        .results {
            margin-top: 30px;
        }
        
        .result-item {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        
        .result-item:hover {
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }
        
        .result-content {
            color: #333;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        
        .scores {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .score-badge {
            padding: 5px 12px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .score-hybrid {
            background: #667eea;
            color: white;
        }
        
        .score-fts {
            background: #f093fb;
            color: white;
        }
        
        .score-semantic {
            background: #4facfe;
            color: white;
        }
        
        .score-fuzzy {
            background: #43e97b;
            color: white;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #667eea;
            font-size: 1.2em;
        }
        
        .stats {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            color: white;
        }
        
        .stats h3 {
            margin-bottom: 10px;
        }
        
        .error {
            background: #fee140;
            border-left: 4px solid #fa709a;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 Hybrid Search</h1>
        <p class="subtitle">FTS5 + Semantic + Fuzzy Matching</p>
        
        <div class="methods">
            <div class="method-badge">📝 FTS5 (40%)</div>
            <div class="method-badge">🧠 Semantic (35%)</div>
            <div class="method-badge">🔍 Fuzzy (25%)</div>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Wpisz zapytanie..." value="python">
            <button onclick="search()">Szukaj</button>
            <button onclick="compare()">Porównaj Metody</button>
        </div>
        
        <div id="stats"></div>
        <div id="results"></div>
    </div>
    
    <script>
        const AUTH_TOKEN = 'ssjjMijaja6969';
        
        async function search() {
            const query = document.getElementById('searchInput').value;
            const resultsDiv = document.getElementById('results');
            
            resultsDiv.innerHTML = '<div class="loading">⏳ Wyszukiwanie...</div>';
            
            try {
                const response = await fetch('/api/search/hybrid', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${AUTH_TOKEN}`
                    },
                    body: JSON.stringify({
                        query: query,
                        limit: 10,
                        user_id: 'default',
                        show_breakdown: true,
                        min_score: 0.0
                    })
                });
                
                const data = await response.json();
                
                if (data.ok) {
                    let html = `<h2>Wyniki (${data.total_results})</h2>`;
                    
                    data.results.forEach((r, i) => {
                        html += `
                            <div class="result-item">
                                <div class="result-content">
                                    <strong>#${i + 1}</strong> ${r.content || 'Brak treści'}
                                </div>
                                <div class="scores">
                                    <span class="score-badge score-hybrid">
                                        FINAL: ${(r.score * 100).toFixed(1)}%
                                    </span>
                                    ${r.fts_score !== undefined ? `
                                        <span class="score-badge score-fts">
                                            FTS: ${(r.fts_score * 100).toFixed(1)}%
                                        </span>
                                    ` : ''}
                                    ${r.semantic_score !== undefined ? `
                                        <span class="score-badge score-semantic">
                                            SEM: ${(r.semantic_score * 100).toFixed(1)}%
                                        </span>
                                    ` : ''}
                                    ${r.fuzzy_score !== undefined ? `
                                        <span class="score-badge score-fuzzy">
                                            FUZ: ${(r.fuzzy_score * 100).toFixed(1)}%
                                        </span>
                                    ` : ''}
                                </div>
                            </div>
                        `;
                    });
                    
                    resultsDiv.innerHTML = html;
                } else {
                    resultsDiv.innerHTML = '<div class="error">❌ Błąd wyszukiwania</div>';
                }
            } catch (err) {
                resultsDiv.innerHTML = `<div class="error">❌ ${err.message}</div>`;
            }
        }
        
        async function compare() {
            const query = document.getElementById('searchInput').value;
            const resultsDiv = document.getElementById('results');
            
            resultsDiv.innerHTML = '<div class="loading">⏳ Porównywanie metod...</div>';
            
            try {
                const response = await fetch(`/api/search/compare?query=${encodeURIComponent(query)}&limit=5`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${AUTH_TOKEN}`
                    }
                });
                
                const data = await response.json();
                
                if (data.ok) {
                    let html = '<h2>🔬 Porównanie Metod</h2>';
                    
                    ['fts5_only', 'semantic_only', 'hybrid'].forEach(method => {
                        const m = data.comparison[method];
                        html += `
                            <div class="stats">
                                <h3>${m.method} (${m.weight})</h3>
                                <p>Znaleziono: ${m.count} wyników</p>
                            </div>
                        `;
                        
                        m.results.slice(0, 3).forEach((r, i) => {
                            html += `
                                <div class="result-item">
                                    <div class="result-content">
                                        <strong>#${i + 1}</strong> ${r.content || 'Brak treści'}
                                    </div>
                                    <div class="scores">
                                        <span class="score-badge score-hybrid">
                                            Score: ${(r.score * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                </div>
                            `;
                        });
                    });
                    
                    resultsDiv.innerHTML = html;
                } else {
                    resultsDiv.innerHTML = '<div class="error">❌ Błąd porównania</div>';
                }
            } catch (err) {
                resultsDiv.innerHTML = `<div class="error">❌ ${err.message}</div>`;
            }
        }
        
        // Load stats on page load
        async function loadStats() {
            try {
                const response = await fetch('/api/search/stats?user_id=default', {
                    headers: {
                        'Authorization': `Bearer ${AUTH_TOKEN}`
                    }
                });
                
                const data = await response.json();
                
                if (data.ok) {
                    document.getElementById('stats').innerHTML = `
                        <div class="stats">
                            <h3>📊 Statystyki Pamięci</h3>
                            <p>Łącznie konwersacji: ${data.total_conversations}</p>
                            <p>Możliwości: FTS5 ✓ Semantic ✓ Fuzzy ✓ Hybrid ✓</p>
                        </div>
                    `;
                }
            } catch (err) {
                console.error('Stats error:', err);
            }
        }
        
        loadStats();
        
        // Enter key to search
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                search();
            }
        });
        
        // Auto-search on load
        setTimeout(search, 500);
    </script>
</body>
</html>
    """
    
    return html
