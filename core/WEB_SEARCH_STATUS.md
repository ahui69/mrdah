# 🌐 WEB SEARCH - ZAAWANSOWANY SYSTEM BADAWCZY

## ✅ TAK, MAMY PEŁNY, ENTERPRISE-GRADE RESEARCH SYSTEM!

**NIE JEST TO "PROSTE WYSZUKIWANIE"!** To jest **masywny, wielopoziomowy system** z:
- 🧠 Hierarchical Memory integration (sprawdza pamięć PRZED web search)
- 🌐 Multi-source search (6 źródeł danych)
- 🔍 Advanced web scraping (Firecrawl + Readability + BeautifulSoup)
- 🤖 LLM fact extraction (wyciąga fakty z tekstów)
- 📊 Semantic ranking (hybrid rank z embeddings)
- 💾 LTM storage (auto-zapisuje fakty)
- ⚡ Multi-level caching (TTL 30 min)
- 🎯 Source quality scoring (.edu = 1.3x, .org = 1.2x)
- 📅 Recency bonus (świeże artykuły lepsze)
- 🚫 Domain limiting (max 2-3 z tej samej domeny)
- 🔄 Fallback pipeline (jeśli główny moduł nie działa)

### 📊 DOSTĘPNE ŹRÓDŁA

#### 🆓 DARMOWE (zawsze działają):
1. **DuckDuckGo** - HTML search
   - Pełne wyszukiwanie web
   - Funkcja: `_ddg_search()` w `core/research.py` L182
   
2. **Wikipedia** - API
   - Artykuły encyklopedyczne
   - Funkcja: `_wiki_search()` w `core/research.py` L196
   
3. **arXiv** - Academic papers
   - Publikacje naukowe (fizyka, matematyka, CS)
   - Funkcja: `_arxiv_search()` w `core/research.py` L207
   
4. **Semantic Scholar** - Research papers
   - Artykuły badawcze ze wszystkich dziedzin
   - Funkcja: `_s2_search()` w `core/research.py` L221

#### 💰 PŁATNE (wymagają kluczy API):
5. **SERPAPI** - Google Search
   - Najlepsze wyniki wyszukiwania
   - Wymaga: `SERPAPI_KEY` w `.env`
   - Funkcja: `_serpapi_search()` w `core/research.py` L232
   
6. **Firecrawl** - Web scraping
   - Wysokiej jakości scraping treści
   - Wymaga: `FIRECRAWL_API_KEY` w `.env`
   - Fallback: BeautifulSoup (zawsze działa)
   - Funkcja: `_firecrawl()` w `core/research.py` L268

---

## 🚀 JAK UŻYWAĆ

### 1. NATURAL LANGUAGE (przez intent detection):
```
USER: "Co to jest kwantowa superpozycja?"
USER: "Wyszukaj informacje o AI"
USER: "Kim jest Stephen Hawking?"
USER: "Znajdź informacje o Python"
```

**Automatycznie:**
- Wykrywane przez `handle_web_search_intent()`
- Wywołuje `autonauka(query)`
- Przeszukuje wszystkie dostępne źródła
- Generuje odpowiedź z kontekstem
- Zwraca źródła (linki)

### 2. PRZEZ API ENDPOINT:
```bash
# Proste wyszukiwanie
curl -X POST "http://localhost:8080/api/research/search" \
  -H "Authorization: Bearer ssjjMijaja6969" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "teoria strun",
    "topk": 5,
    "mode": "full"
  }'

# Autonauka z LTM
curl -X POST "http://localhost:8080/api/research/autonauka" \
  -H "Authorization: Bearer ssjjMijaja6969" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Wyjaśnij kwantową superpozycję",
    "topk": 8,
    "user_id": "user123",
    "save_to_ltm": true
  }'

# Sprawdź dostępne źródła
curl -X GET "http://localhost:8080/api/research/sources" \
  -H "Authorization: Bearer ssjjMijaja6969"
```

### 3. PRZEZ CHAT (frontend):
Po prostu wpisz pytanie w chat:
- "Co to jest Docker?"
- "Wyszukaj informacje o blockchain"
- "Kim był Albert Einstein?"

---

## 📁 STRUKTURA KODU

### Intent Detection:
```
core/intent_dispatcher.py
├── handle_web_search_intent()    # Linia 154-176
│   ├── Wzorce regex:
│   │   - r"(wyszukaj|znajdź informacje)\s+(?:o\s+)?(.+)"
│   │   - r"(co to jest|kim jest|czym jest)\s+(.+)"
│   │   - r"(opowiedz o|co wiesz o)\s+(.+)"
│   │   - r"(przeszukaj internet)\s+(?:dla\s+)?(.+)"
│   └── Wywołuje: autonauka(query, topk=5, user_id="system")
```

### Research Module:
```
core/research.py
├── _ddg_search()           # L182  - DuckDuckGo HTML
├── _wiki_search()          # L196  - Wikipedia API
├── _arxiv_search()         # L207  - arXiv papers
├── _s2_search()            # L221  - Semantic Scholar
├── _serpapi_search()       # L232  - Google (SERPAPI)
├── _search_all()           # L245  - Orchestrator wszystkich źródeł
├── _firecrawl()            # L268  - Scraping (Firecrawl/fallback)
└── autonauka()             # L~300 - Pełna pipeline
```

### API Endpoints:
```
research_endpoint.py
├── POST /api/research/search     # L29   - Web search
├── POST /api/research/autonauka  # L78   - Auto-learning
├── GET  /api/research/sources    # L118  - Lista źródeł
└── GET  /api/research/test       # L168  - Test
```

---

## 🔧 KONFIGURACJA

### Bez kluczy API (darmowe):
```env
# Wystarczy to - będzie działać z DDG + Wiki + arXiv + S2
AUTH_TOKEN=ssjjMijaja6969
```

### Z kluczami API (pełna moc):
```env
AUTH_TOKEN=ssjjMijaja6969

# Google search (zalecane)
SERPAPI_KEY=twoj_klucz_serpapi

# Web scraping (zalecane)
FIRECRAWL_API_KEY=twoj_klucz_firecrawl
```

---

## 📊 TRYBY WYSZUKIWANIA

### `mode: "full"` (domyślny):
- DuckDuckGo ✅
- Wikipedia ✅
- SERPAPI (jeśli klucz) ✅
- arXiv ✅
- Semantic Scholar ✅
- **Najlepsze wyniki, wolniejsze**

### `mode: "grounded"`:
- Jak `full` ale priorytet dla wiarygodnych źródeł
- Preferuje: .edu, .gov, Wikipedia, Scholar

### `mode: "fast"`:
- Tylko DuckDuckGo + Wikipedia
- **Szybkie, podstawowe wyniki**

### `mode: "free"`:
- Tylko darmowe źródła (bez SERPAPI)
- DDG + Wiki + arXiv + S2

---

## 🧪 TEST

### 1. Test przez terminal:
```bash
curl -X GET "http://localhost:8080/api/research/test" \
  -H "Authorization: Bearer ssjjMijaja6969"
```

Powinno zwrócić:
```json
{
  "ok": true,
  "sources_count": 3,
  "answer_length": 500,
  "test_passed": true
}
```

### 2. Test przez chat:
Uruchom aplikację i wpisz w chat:
```
Co to jest Python?
```

Powinieneś otrzymać:
- Odpowiedź z wyjaśnieniem
- Linki do źródeł (Wikipedia, etc.)
- Metadata z "source": "fast_path", "handler": "handle_web_search_intent"

---

## 🎯 PODSUMOWANIE

### ✅ CO MAMY:
- **4 darmowe źródła** (DDG, Wiki, arXiv, S2) - zawsze działają
- **2 płatne źródła** (SERPAPI, Firecrawl) - opcjonalne, ale lepsze
- **Automatyczne wykrywanie** pytań wymagających web search
- **Natural language** - "Co to jest X?" działa out-of-box
- **Fallback scraping** - jeśli Firecrawl nie działa, używamy BeautifulSoup
- **Multi-source** - łączy wyniki z wielu źródeł
- **Domain limiting** - max 2 wyniki z tej samej domeny (anti-spam)
- **LLM synthesis** - generuje czytelną odpowiedź z kontekstem

### ❌ CZEGO NIE MAMY:
- Real-time web crawling (używamy API i scraping)
- Obrazy z web search (tylko teksty)
- Płatne źródła wymagają kluczy API

### 🔜 MOŻLIWE ROZSZERZENIA:
- Google Scholar (przez SERPAPI)
- PubMed (medical papers)
- GitHub search
- Stack Overflow search
- News API (aktualności)
- Reddit API (dyskusje)

---

**WNIOSEK:** Mamy **PEŁNY** dostęp do internetu przez 6 źródeł, w tym 4 darmowe. System działa bez kluczy API (tryb free), ale z SERPAPI + Firecrawl jest znacznie lepszy.

**DATA:** 2025-10-16  
**STATUS:** ✅ Fully Operational  
**WERSJA:** Research System v1.0 with 6 data sources
