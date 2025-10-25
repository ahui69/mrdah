# Mapa Endpointów - Projekt EHH (Mordzix AI)

**Wygenerowano:** 2025-10-24  
**Cel:** Pełna mapa wszystkich endpointów API, modeli Pydantic i zależności

---

## 📋 PODSUMOWANIE

| Kategoria | Liczba Endpointów | Pliki |
|-----------|-------------------|-------|
| **Chat & Assistant** | 3 | `assistant_endpoint.py` |
| **Psyche (Psychology)** | 10 | `psyche_endpoint.py` |
| **Code Executor** | 13 | `programista_endpoint.py` |
| **Files** | 8 | `files_endpoint.py` |
| **Travel** | 6 | `travel_endpoint.py` |
| **Research** | 4 | `core/research_endpoint.py` |
| **NLP** | 8 | `nlp_endpoint.py` |
| **Writing** | 12 | `writing_endpoint.py` |
| **TTS/STT** | 3 | `tts_endpoint.py`, `stt_endpoint.py` |
| **Batch Processing** | 4 | `batch_endpoint.py` |
| **Suggestions** | 4 | `suggestions_endpoint.py` |
| **Admin** | 4 | `admin_endpoint.py` |
| **Captcha** | 2 | `captcha_endpoint.py` |
| **Prometheus** | 3 | `prometheus_endpoint.py` |
| **Internal** | 1 | `internal_endpoint.py` |
| **TOTAL** | **85** | **15 plików** |

---

## 🔵 1. ASSISTANT ENDPOINT (`assistant_endpoint.py`)

**Prefix:** `/api/chat`  
**Tag:** `chat`

### Endpointy

| Metoda | Ścieżka | Model Request | Model Response | Opis |
|--------|---------|---------------|----------------|------|
| POST | `/api/chat/assistant` | `ChatRequest` | `ChatResponse` | Główny chat z AI |
| POST | `/api/chat/assistant/stream` | `ChatRequest` | SSE Stream | Chat streaming (SSE) |
| POST | `/api/chat/auto` | `AutoLearnRequest` | `ChatResponse` | Auto-learning z internetu |

### Modele Pydantic

```python
class Message(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: str = "default"
    session_id: Optional[str] = None
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    timestamp: float
    psyche: Optional[Dict] = None

class AutoLearnRequest(BaseModel):
    topic: str
    depth: str = "medium"  # shallow | medium | deep
```

### Zależności

- `core.cognitive_engine` → `cognitive_engine()`
- `core.memory` → `_save_turn_to_memory()`, `_auto_learn_from_turn()`
- `core.research` → `autonauka()` (dla `/auto`)
- SSE: `sse_starlette.EventSourceResponse`

---

## 🧠 2. PSYCHE ENDPOINT (`psyche_endpoint.py`)

**Prefix:** `/api/psyche`  
**Tag:** `psyche`

### Endpointy

| Metoda | Ścieżka | Model Request | Model Response | Opis |
|--------|---------|---------------|----------------|------|
| GET | `/api/psyche/status` | - | Dict | Status psychiczny AI |
| POST | `/api/psyche/save` | `PsycheUpdate` | Dict | Zapisz stan psyche |
| GET | `/api/psyche/load` | - | Dict | Wczytaj stan psyche |
| POST | `/api/psyche/observe` | `ObserveText` | Dict | Obserwuj tekst (aktualizuj mood) |
| POST | `/api/psyche/episode` | `Episode` | Dict | Dodaj epizod psychologiczny |
| GET | `/api/psyche/reflect` | - | Dict | Refleksja AI (LLM) |
| GET | `/api/psyche/tune` | - | Dict | Auto-tune parametrów psyche |
| POST | `/api/psyche/reset` | - | Dict | Reset psyche do domyślnych |
| POST | `/api/psyche/analyze` | `MessageAnalysis` | Dict | Analiza wiadomości (nastrój) |
| POST | `/api/psyche/set-mode` | `PsycheModeUpdate` | Dict | Ustaw tryb psyche |
| POST | `/api/psyche/enhance-prompt` | `PromptRequest` | Dict | Wzbogać prompt o psyche |

### Modele Pydantic

```python
class PsycheUpdate(BaseModel):
    mood: Optional[float] = None        # -1.0 do 1.0
    energy: Optional[float] = None      # 0.0 do 1.0
    focus: Optional[float] = None       # 0.0 do 1.0
    style: Optional[str] = None         # creative | analytical | ...
    reason: Optional[str] = None

class ObserveText(BaseModel):
    text: str

class Episode(BaseModel):
    event_type: str                     # success | failure | frustration | ...
    description: str
    intensity: float = 0.5              # 0.0 do 1.0
    timestamp: Optional[float] = None

class MessageAnalysis(BaseModel):
    text: str

class PsycheModeUpdate(BaseModel):
    mode: str  # creative | analytical | neutral | ...

class PromptRequest(BaseModel):
    prompt: str
```

### Zależności

- `core.memory` → `psy_get()`, `psy_set()`, `psy_episode()`, `psy_reflect()`, `psy_tune()`
- `core.advanced_psychology` → zaawansowana analiza psychologiczna
- `core.auth` → `check_auth()`

---

## 💻 3. PROGRAMISTA ENDPOINT (`programista_endpoint.py`)

**Prefix:** `/api/code`  
**Tag:** `code`

### Endpointy

| Metoda | Ścieżka | Model Request | Model Response | Opis |
|--------|---------|---------------|----------------|------|
| GET | `/api/code/snapshot` | - | Dict | Snapshot workspace (lista plików) |
| POST | `/api/code/exec` | `ExecRequest` | Dict | Wykonaj polecenie shell |
| POST | `/api/code/write` | `WriteFileRequest` | Dict | Zapisz plik |
| GET | `/api/code/read` | `?path=` | Dict | Odczytaj plik |
| GET | `/api/code/tree` | - | Dict | Drzewo katalogów |
| POST | `/api/code/init` | `ProjectInitRequest` | Dict | Inicjuj nowy projekt |
| POST | `/api/code/plan` | `PlanRequest` | Dict | Plan architektury projektu |
| POST | `/api/code/lint` | `LintRequest` | Dict | Lint kodu |
| POST | `/api/code/test` | `TestRequest` | Dict | Uruchom testy |
| POST | `/api/code/format` | `?path=` | Dict | Formatuj kod |
| POST | `/api/code/git` | `GitRequest` | Dict | Polecenia git |
| POST | `/api/code/docker/build` | `DockerBuildRequest` | Dict | Zbuduj obraz Docker |
| POST | `/api/code/docker/run` | `?image=&cmd=` | Dict | Uruchom kontener |
| POST | `/api/code/deps/install` | `DepsInstallRequest` | Dict | Zainstaluj zależności |

### Modele Pydantic

```python
class ExecRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout: int = 30
    shell: str = "bash"
    env: Optional[Dict[str, str]] = None

class WriteFileRequest(BaseModel):
    path: str
    content: str

class ProjectInitRequest(BaseModel):
    name: str
    template: str  # python | node | react | ...

class PlanRequest(BaseModel):
    description: str

class LintRequest(BaseModel):
    path: str
    linter: str = "auto"  # pylint | eslint | ...

class TestRequest(BaseModel):
    path: Optional[str] = None
    framework: str = "auto"  # pytest | jest | ...

class GitRequest(BaseModel):
    command: str  # pull | commit | push | ...
    args: Optional[List[str]] = None

class DockerBuildRequest(BaseModel):
    dockerfile: str = "Dockerfile"
    tag: str

class DepsInstallRequest(BaseModel):
    file: str  # requirements.txt | package.json | ...
```

### Zależności

- `core.executor` → `Programista` (główna klasa wykonawcza)
- `core.auth` → `check_auth()`
- Wymaga: `os`, `subprocess`, `pathlib`

---

## 📁 4. FILES ENDPOINT (`files_endpoint.py`)

**Prefix:** `/api/files`  
**Tag:** `files`

### Endpointy

| Metoda | Ścieżka | Model Request | Model Response | Opis |
|--------|---------|---------------|----------------|------|
| POST | `/api/files/upload` | Multipart File | Dict | Upload pliku (multipart) |
| POST | `/api/files/upload/base64` | `FileUploadBase64` | Dict | Upload pliku (base64) |
| GET | `/api/files/list` | - | Dict | Lista uploadowanych plików |
| GET | `/api/files/download` | `?filename=` | FileResponse | Pobierz plik |
| POST | `/api/files/analyze` | `FileAnalyzeRequest` | Dict | Analiza pliku (OCR/PDF/Vision) |
| POST | `/api/files/delete` | `FileDeleteRequest` | Dict | Usuń plik |
| GET | `/api/files/stats` | - | Dict | Statystyki plików |
| POST | `/api/files/batch/analyze` | List[str] | Dict | Batch analiza plików |

### Modele Pydantic

```python
class FileUploadBase64(BaseModel):
    filename: str
    content: str  # base64
    analyze: bool = False

class FileAnalyzeRequest(BaseModel):
    filename: str
    mode: str = "auto"  # ocr | pdf | vision

class FileDeleteRequest(BaseModel):
    filename: str
```

### Zależności

- `vision_provider` → analiza obrazów (GPT-4 Vision)
- `PyPDF2` → ekstrakcja tekstu z PDF
- `pytesseract` → OCR (Tesseract)
- `PIL (Pillow)` → przetwarzanie obrazów
- `core.auth` → autoryzacja

---

## ✈️ 5. TRAVEL ENDPOINT (`travel_endpoint.py`)

**Prefix:** `/api/travel`  
**Tag:** `travel`

### Endpointy

| Metoda | Ścieżka | Query Params | Opis |
|--------|---------|--------------|------|
| GET | `/api/travel/search` | `query`, `type` | Wyszukiwanie (hotele/restauracje/atrakcje) |
| GET | `/api/travel/geocode` | `city` | Geocoding (współrzędne miasta) |
| GET | `/api/travel/attractions/{city}` | - | Atrakcje w mieście |
| GET | `/api/travel/hotels/{city}` | - | Hotele w mieście |
| GET | `/api/travel/restaurants/{city}` | - | Restauracje w mieście |
| GET | `/api/travel/trip-plan` | `destination`, `days` | Plan podróży |

### Zależności

- `core.research` → `travel_search()`, `otm_geoname()`, `serp_maps()`
- `core.auth` → `check_auth()`
- API: OpenTripMap, SERP API

---

## 🔍 6. RESEARCH ENDPOINT (`research_endpoint.py`)

**Prefix:** `/api/research`  
**Tag:** `research`

### Endpointy

| Metoda | Ścieżka | Model Request | Model Response | Opis |
|--------|---------|---------------|----------------|------|
| POST | `/api/research/search` | `WebSearchRequest` | Dict | Wyszukiwanie web (multi-source) |
| POST | `/api/research/autonauka` | `AutonaukaRequest` | Dict | Auto-learning (Google + scraping) |
| GET | `/api/research/sources` | - | Dict | Dostępne źródła wyszukiwania |
| GET | `/api/research/test` | - | Dict | Test konfiguracji API |

### Modele Pydantic

```python
class WebSearchRequest(BaseModel):
    query: str
    sources: List[str] = ["duckduckgo", "wikipedia"]  # duckduckgo, wikipedia, serpapi
    max_results: int = 5
    lang: str = "pl"

class AutonaukaRequest(BaseModel):
    topic: str
    depth: str = "medium"  # shallow | medium | deep
    sources: List[str] = ["google", "wikipedia"]
```

### Zależności

- `core.research` → `autonauka()` (główna funkcja research)
- `core.config` → `SERPAPI_KEY`, `FIRECRAWL_API_KEY`
- `core.helpers` → `log_info()`, `log_error()`

---

## 📝 7. NLP ENDPOINT (`nlp_endpoint.py`)

**Prefix:** `/api/nlp`  
**Tag:** `nlp`

### Endpointy

| Metoda | Ścieżka | Model Request | Model Response | Opis |
|--------|---------|---------------|----------------|------|
| POST | `/api/nlp/analyze` | `TextAnalysisRequest` | `NLPAnalysisResponse` | Pełna analiza NLP |
| POST | `/api/nlp/batch-analyze` | `BatchAnalysisRequest` | `BatchAnalysisResponse` | Batch analiza |
| POST | `/api/nlp/extract-topics` | `TopicExtractionRequest` | `TopicExtractionResponse` | Ekstrakcja tematów |
| GET | `/api/nlp/stats` | - | `NLPStatsResponse` | Statystyki NLP |
| POST | `/api/nlp/entities` | `{"text": str}` | Dict | Ekstrakcja encji (NER) |
| POST | `/api/nlp/sentiment` | `{"text": str}` | Dict | Analiza sentymentu |
| POST | `/api/nlp/key-phrases` | `{"text": str}` | Dict | Kluczowe frazy |
| POST | `/api/nlp/readability` | `{"text": str}` | Dict | Analiza czytelności |

### Modele Pydantic

```python
class TextAnalysisRequest(BaseModel):
    text: str
    lang: str = "pl"

class BatchAnalysisRequest(BaseModel):
    texts: List[str]
    lang: str = "pl"

class TopicExtractionRequest(BaseModel):
    text: str
    num_topics: int = 5

class NLPAnalysisResponse(BaseModel):
    text: str
    lang: str
    entities: List[Dict]
    sentiment: Dict
    key_phrases: List[str]
    topics: List[str]
    readability: Dict
    pos_tags: List[Dict]

class BatchAnalysisResponse(BaseModel):
    results: List[NLPAnalysisResponse]
    total: int

class TopicExtractionResponse(BaseModel):
    topics: List[Dict]
    total: int

class NLPStatsResponse(BaseModel):
    total_processed: int
    avg_processing_time: float
```

### Zależności

- `core.nlp_processor` → `get_nlp_processor()` (spaCy)
- `core.config` → `AUTH_TOKEN`
- `core.helpers` → `log_info()`, `log_error()`
- Wymaga: `spacy`, model `pl_core_news_sm`

---

## ✍️ 8. WRITING ENDPOINT (`writing_endpoint.py`)

**Prefix:** `/api/writing`  
**Tag:** `writing`

### Endpointy

| Metoda | Ścieżka | Model Request | Model Response | Opis |
|--------|---------|---------------|----------------|------|
| POST | `/api/writing/creative` | `CreativeRequest` | `CreativeResponse` | Kreatywne pisanie (ogólne) |
| POST | `/api/writing/vinted` | `VintedRequest` | `CreativeResponse` | Opis produktu Vinted |
| POST | `/api/writing/social` | `SocialRequest` | `CreativeResponse` | Post social media |
| POST | `/api/writing/auction` | `AuctionRequest` | `CreativeResponse` | Opis aukcji (Allegro) |
| POST | `/api/writing/auction/pro` | `AuctionProRequest` | `CreativeResponse` | Opis aukcji PRO (zaawansowany) |
| POST | `/api/writing/fashion/analyze` | `FashionAnalysisRequest` | Dict | Analiza mody (vision) |
| POST | `/api/writing/auction/suggest-tags` | `{"title": str}` | Dict | Sugestie tagów |
| POST | `/api/writing/auction/kb/learn` | `AuctionKBLearnRequest` | Dict | Ucz bazę wiedzy aukcyjnej |
| GET | `/api/writing/auction/kb/fetch` | - | Dict | Pobierz bazę wiedzy |
| POST | `/api/writing/masterpiece/article` | `MasterpieceArticleRequest` | `CreativeResponse` | Artykuł (najwyższej jakości) |
| POST | `/api/writing/masterpiece/sales` | `SalesMasterpieceRequest` | `CreativeResponse` | Tekst sprzedażowy PRO |
| POST | `/api/writing/masterpiece/technical` | `TechnicalMasterpieceRequest` | `CreativeResponse` | Tekst techniczny PRO |

### Modele Pydantic

```python
class CreativeRequest(BaseModel):
    prompt: str
    style: str = "creative"
    length: str = "medium"  # short | medium | long

class CreativeResponse(BaseModel):
    text: str
    metadata: Optional[Dict] = None

class VintedRequest(BaseModel):
    item_name: str
    brand: Optional[str] = None
    size: Optional[str] = None
    condition: str = "very_good"

class SocialRequest(BaseModel):
    topic: str
    platform: str = "facebook"  # facebook | instagram | twitter
    tone: str = "casual"
    hashtags: bool = True

class AuctionRequest(BaseModel):
    title: str
    category: str
    features: List[str]

class AuctionProRequest(BaseModel):
    title: str
    category: str
    features: List[str]
    target_audience: str
    seo_keywords: List[str]

class FashionAnalysisRequest(BaseModel):
    image_url: str

class AuctionKBLearnRequest(BaseModel):
    data: Dict

class MasterpieceArticleRequest(BaseModel):
    topic: str
    keywords: List[str]
    tone: str = "professional"

class SalesMasterpieceRequest(BaseModel):
    product: str
    benefits: List[str]

class TechnicalMasterpieceRequest(BaseModel):
    topic: str
    technical_level: str = "intermediate"
```

### Zależności

- `core.writing` → funkcje generowania tekstów (LLM)
- `vision_provider` → analiza obrazów mody
- `core.memory` → baza wiedzy aukcyjnej

---

## 🎤 9. TTS/STT ENDPOINTS

### TTS (`tts_endpoint.py`)

**Prefix:** `/api/tts`

| Metoda | Ścieżka | Model Request | Opis |
|--------|---------|---------------|------|
| POST | `/api/tts/speak` | `TTSRequest` | Text-to-Speech (ElevenLabs) |
| GET | `/api/tts/voices` | - | Lista dostępnych głosów |

```python
class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    model: str = "eleven_multilingual_v2"
```

### STT (`stt_endpoint.py`)

**Prefix:** `/api/stt`

| Metoda | Ścieżka | Model Response | Opis |
|--------|---------|----------------|------|
| POST | `/api/stt/transcribe` | `STTResponse` | Speech-to-Text (Whisper) |
| GET | `/api/stt/providers` | Dict | Dostępni providerzy STT |

```python
class STTResponse(BaseModel):
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
```

### Zależności

- `tts_elevenlabs` → ElevenLabs API
- OpenAI Whisper (dla STT)

---

## 🔄 10. BATCH ENDPOINT (`batch_endpoint.py`)

**Prefix:** `/api/batch`  
**Tag:** `batch`

### Endpointy

| Metoda | Ścieżka | Opis |
|--------|---------|------|
| POST | `/api/batch/process` | Przetwarzanie wsadowe zapytań LLM |
| POST | `/api/batch/submit` | Dodaj zapytanie do kolejki |
| GET | `/api/batch/metrics` | Metryki procesora wsadowego |
| POST | `/api/batch/shutdown` | Zatrzymaj procesor |

### Zależności

- `core.batch_processing` → BatchProcessor
- `core.auth` → `auth_dependency` / `verify_token`

---

## 💡 11. SUGGESTIONS ENDPOINT (`suggestions_endpoint.py`)

**Prefix:** `/api/suggestions`  
**Tag:** `suggestions`

### Endpointy

| Metoda | Ścieżka | Opis |
|--------|---------|------|
| POST | `/api/suggestions/generate` | Generuj proaktywne sugestie |
| POST | `/api/suggestions/inject` | Wstrzyknij sugestie do promptu |
| GET | `/api/suggestions/stats` | Statystyki sugestii |
| POST | `/api/suggestions/analyze` | Analiza wiadomości (bez generowania) |

### Zależności

- `advanced_proactive` → `generate_proactive_suggestions()`, `inject_suggestions()`
- `core.auth` → `auth_dependency` / `verify_token`

---

## 🔧 12. ADMIN ENDPOINT (`admin_endpoint.py`)

**Prefix:** `/api/admin`  
**Tag:** `admin`

### Endpointy

| Metoda | Ścieżka | Opis |
|--------|---------|------|
| GET | `/api/admin/cache/stats` | Statystyki cache |
| POST | `/api/admin/cache/clear` | Wyczyść cache |
| GET | `/api/admin/ratelimit/usage/{user_id}` | Użycie rate-limit |
| GET | `/api/admin/ratelimit/config` | Konfiguracja rate-limit |

### Zależności

- `core.memory` → `LTM_FACTS_CACHE`
- Wymaga autoryzacji admin

---

## 🔐 13. CAPTCHA ENDPOINT (`captcha_endpoint.py`)

**Prefix:** `/api/captcha`

### Endpointy

| Metoda | Ścieżka | Model Request | Model Response | Opis |
|--------|---------|---------------|----------------|------|
| POST | `/api/captcha/solve` | `CaptchaSolveRequest` | `CaptchaSolveResponse` | Rozwiąż captcha |
| GET | `/api/captcha/balance` | - | Dict | Saldo konta 2Captcha |

```python
class CaptchaSolveRequest(BaseModel):
    site_key: str
    page_url: str
    type: str = "recaptcha_v2"

class CaptchaSolveResponse(BaseModel):
    solution: str
    task_id: Optional[str] = None
```

### Zależności

- `captcha_solver` → 2Captcha API

---

## 📊 14. PROMETHEUS ENDPOINT (`prometheus_endpoint.py`)

**Prefix:** `/api/prometheus`

### Endpointy

| Metoda | Ścieżka | Opis |
|--------|---------|------|
| GET | `/api/prometheus/metrics` | Metryki Prometheus (format tekst) |
| GET | `/api/prometheus/health` | Health check |
| GET | `/api/prometheus/stats` | Statystyki (JSON) |

### Zależności

- `core.metrics` → Prometheus client
- `prometheus_client` → metryki

---

## 🔑 15. INTERNAL ENDPOINT (`internal_endpoint.py`)

**Prefix:** `/api/internal`

### Endpointy

| Metoda | Ścieżka | Opis |
|--------|---------|------|
| GET | `/api/internal/ui_token` | Token dla UI (opcjonalny) |

---

## 📦 DUPLIKATY (core/ vs root)

**Uwaga:** Niektóre endpointy mają duplikaty w `core/`:

- `assistant_endpoint.py` (root i `core/`)
- `psyche_endpoint.py` (root i `core/`)
- `research_endpoint.py` (root i `core/`)
- `batch_endpoint.py` (root i `core/`)
- `suggestions_endpoint.py` (root i `core/`)
- `prometheus_endpoint.py` (root i `core/`)

**Rekomendacja:** Wybrać jedną wersję (najlepiej `core/`) i usunąć duplikaty.

---

## 🔗 WSPÓLNE ZALEŻNOŚCI (cross-module)

### Moduły Core

```python
core/
├── auth.py              # check_auth(), verify_token(), auth_dependency
├── cognitive_engine.py  # cognitive_engine() - główny silnik AI
├── memory.py            # _save_turn_to_memory(), psy_get(), psy_set(), LTM
├── research.py          # autonauka(), travel_search(), web search
├── executor.py          # Programista (code execution)
├── writing.py           # Funkcje generowania tekstów
├── nlp_processor.py     # get_nlp_processor() (spaCy)
├── config.py            # AUTH_TOKEN, SERPAPI_KEY, FIRECRAWL_API_KEY, ...
├── helpers.py           # log_info(), log_error()
├── metrics.py           # Prometheus metrics
├── batch_processing.py  # BatchProcessor
└── advanced_psychology.py  # Zaawansowana analiza psychologiczna
```

### Moduły Root

```python
advanced_proactive.py   # Proaktywne sugestie
vision_provider.py      # GPT-4 Vision API
captcha_solver.py       # 2Captcha integration
tts_elevenlabs.py       # ElevenLabs TTS
```

---

## 🛠️ WYMAGANE ZMIENNE ŚRODOWISKOWE (.env)

```bash
# Auth
AUTH_TOKEN=your_secret_token

# OpenAI
OPENAI_API_KEY=sk-...

# Research APIs
SERPAPI_KEY=...
FIRECRAWL_API_KEY=...

# ElevenLabs (TTS)
ELEVENLABS_API_KEY=...

# 2Captcha
TWOCAPTCHA_API_KEY=...

# Database
MEM_DB=./mem.db
WORKSPACE=./

# LLM Config
LLM_MODEL=gpt-4-turbo-preview  # lub gpt-4, gpt-3.5-turbo
TEMPERATURE=0.7
MAX_TOKENS=2000
```

---

## ✅ KRYTERIA AKCEPTACJI (zgodne z PIPELINE)

### Krok 1: ✅ **analysis/endpoints_map.md**
- [x] Pełna mapa wszystkich endpointów
- [x] Modele Pydantic
- [x] Zależności między modułami
- [x] Podsumowanie: **85 endpointów, 15 plików**

### Krok 2: **app.py** (do zrobienia)
- [ ] Wszystkie routery zaimportowane
- [ ] JWT + RBAC
- [ ] Error handlers (ujednolicony JSON)
- [ ] CORS + CSP
- [ ] `/healthz`, `/metrics`, `/docs`
- [ ] Uploady (multipart)
- [ ] `.env` support

### Krok 3: **Frontend** (do zrobienia)
- [ ] ChatGPT-style UI
- [ ] Lista rozmów (lewy sidebar)
- [ ] Chat (SSE/WebSocket)
- [ ] Settings (prawa kolumna)
- [ ] Auth JWT
- [ ] Historia, eksport/import
- [ ] Dark mode

### Krok 4: **Testy** (do zrobienia)
- [ ] pytest (backend)
- [ ] Playwright (frontend e2e)

### Krok 5: **Docker + CI/CD** (do zrobienia)
- [ ] `docker-compose.yml`
- [ ] `.github/workflows/ci.yml`
- [ ] Deploy: nginx + systemd
- [ ] Sanity-check

---

## 🚀 NASTĘPNE KROKI

1. ✅ **DONE:** `analysis/endpoints_map.md`
2. **TODO:** Zunifikować `app.py` (usunąć duplikaty, jeden router na moduł)
3. **TODO:** Frontend od zera (React/Vue/Angular)
4. **TODO:** `.env.example`
5. **TODO:** `docker-compose.yml`
6. **TODO:** Testy
7. **TODO:** Deploy na serwer `ubuntu@162.19.220.29`

---

## 🧠 MODUŁY POMOCNICZE (Core Utils - bez HTTP endpoints)

### 16. Advanced Proactive (`core/advanced_proactive.py`)
**Funkcje:**
- `ConversationAnalyzer` - analiza kontekstu rozmowy
- `generate_proactive_suggestions()` - proaktywne sugestie
- Analiza tematów, intencji, wzorców użytkownika
- Predykcja potrzeb na podstawie historii

### 17. Advanced Psychology (`core/advanced_psychology.py`)
**Funkcje:**
- `EmotionalState` - symulacja emocji AI
- `get_psyche_state()` - stan psychologiczny
- `process_user_message()` - analiza emocji użytkownika
- Plutchik's emotions, PAD model (valence/arousal/dominance)

### 18. Advanced Cognitive Engine (`core/advanced_cognitive_engine.py`)
**Funkcje:**
- `AdvancedCognitiveEngine` - orkiestracja 5 systemów kognitywnych
- `process_with_full_cognition()` - pełna pipeline
- Integracja: self-reflection, knowledge compression, multi-agent, future prediction, inner language

### 19. Self Reflection (`core/self_reflection.py`)
**Funkcje:**
- `SelfReflectionEngine` - auto-ewaluacja odpowiedzi
- `reflect_on_response()` - cykl refleksji (5 poziomów głębokości)
- Meta-analiza, improvement loop, insights extraction

### 20. Knowledge Compression (`core/knowledge_compression.py`)
**Funkcje:**
- Kompresja długich tekstów do esencji
- Transfer learning między domenami
- Hierarchiczna destylacja wiedzy

### 21. Multi-Agent Orchestrator (`core/multi_agent_orchestrator.py`)
**Funkcje:**
- `MultiAgentOrchestrator` - zarządzanie wieloma agentami AI
- `multi_agent_response()` - konsensus wielu perspektyw
- Role: Analityk, Kreatywny, Pragmatyczny, Krytyczny, Syntetyczny

### 22. Future Predictor (`core/future_predictor.py`)
**Funkcje:**
- Predykcja przyszłych pytań/potrzeb
- Analiza trendów w konwersacji
- Proaktywne przygotowanie kontekstu

### 23. Inner Language (`core/inner_language.py`)
**Funkcje:**
- `InnerLanguageProcessor` - wewnętrzny język semantyczny AI
- Kompresja myśli do symboli wysokiego poziomu
- Szybsza komunikacja między modułami

### 24. Tools Registry (`core/tools_registry.py`)
**Funkcje:**
- `get_all_tools()` - lista wszystkich narzędzi (85+ tools)
- `get_tool_by_name()`, `get_tools_by_category()`
- `format_for_openai()` - konwersja do OpenAI format
- Kategorie: search, news, crypto, travel, code, writing, vision, etc.

### 25. Tools (`core/tools.py`)
**Funkcje:**
- `InternetSearcher` - wyszukiwarka web (DDG, SERP)
- `AdvancedRecommendationEngine` - rekomendacje
- `AdvancedCryptoAnalyzer` - analiza krypto
- `AdvancedCodeReviewer` - review kodu
- `AdvancedWorkflowEngine` - workflow automation
- Handlery: `tools_time_handler()`, `tools_search_handler()`, `tools_news_handler()`, `tools_sports_handler()`

### 26. Semantic (`core/semantic.py`)
**Funkcje:**
- `SemanticAnalyzer` - analiza semantyczna tekstu
- `embed_text()` - embeddingi (sentence-transformers)
- `cosine_similarity()` - podobieństwo wektorowe
- `semantic_analyze()`, `semantic_enhance_response()`
- Ekstrakcja: encje, relacje, koncepty, sentiment

### 27. Research (`core/research.py`)
**Funkcje:**
- `autonauka()` - auto-learning z web research
- `web_learn()` - pełna pipeline: search → scrape → analyze → LLM
- Wyszukiwanie: DuckDuckGo, Wikipedia, arXiv, Semantic Scholar, SERPAPI
- Scraping: Firecrawl fallback, BeautifulSoup
- Ranking: BM25 + hybrydowy (cosine hash + Jaccard)
- `serpapi_search()`, `firecrawl_scrape()`, `wiki_search()`

### 28. NLP Processor (`core/nlp_processor.py`)
**Funkcje:**
- `NLPProcessor` - zaawansowane przetwarzanie NLP
- Analiza: sentiment, encje (NER), POS tagging, dependency parsing
- Ekstrakcja: keywords, phrases, relations
- spaCy (pl_core_news_sm), NLTK

### 29. Parallel Processing (`core/parallel.py`)
**Funkcje:**
- `AsyncTaskPool` - pool asynchronicznych tasków
- `parallel_map()` - równoległe przetwarzanie list
- `priority_parallel_map()` - z priorytetami
- `batch_process()` - batch processing
- `process_with_fallback()` - retry z fallback

### 30. Memory (`core/memory.py`)
**Funkcje:**
- `ltm_search_hybrid()` - wyszukiwanie w LTM (Long-Term Memory)
- `stm_get_context()` - STM (Short-Term Memory) context
- `psy_get()`, `psy_set()` - psyche state persistence
- SQLite backend (mem.db)

### 31. Batch Processing (`core/batch_processing.py`)
**Funkcje:**
- `LLMBatchProcessor` - batch processing dla LLM calls
- `process_batch()` - równoległe wywołania LLM
- `call_llm_batch()` - wrapper dla batch calls
- Metryki: throughput, latency, errors

### 32. Advanced LLM (`core/advanced_llm.py`)
**Funkcje:**
- `adaptive_llm_call()` - adaptacyjne wywołania LLM
- `batch_multiple_prompts()` - batch prompts
- `optimize_prompt()` - optymalizacja promptów
- `enhanced_cognitive_llm_call()` - z cognitive pipeline
- `estimate_tokens()`, `extract_key_information()`

### 33. Cognitive Engine (`core/cognitive_engine.py`)
**Funkcje:**
- `CognitiveEngine` - podstawowy silnik kognitywny
- Intent detection, context analysis
- Integration z memory, research, tools

### 34. AI Vision (`core/ai_vision.py`)
**Funkcje:**
- `AIVisionManager` - zarządzanie vision models
- Analiza obrazów (OCR, object detection, description)
- Integration z OpenAI Vision, local models

### 35. AI Fashion (`core/ai_fashion.py`)
**Funkcje:**
- Analiza mody z obrazów
- Rekomendacje stylizacji
- Trend prediction

### 36. AI Auction (`core/ai_auction.py`)
**Funkcje:**
- Automatyczne generowanie opisów aukcji
- SEO optimization dla aukcji
- Pricing recommendations

### 37. User Model (`core/user_model.py`)
**Funkcje:**
- `UserModel` - model użytkownika
- Profiling: preferencje, historia, wzorce
- Personalizacja odpowiedzi

### 38. Intent Dispatcher (`core/intent_dispatcher.py`)
**Funkcje:**
- `analyze_intent_and_select_tools()` - detekcja intencji + wybór narzędzi
- `execute_selected_tools()` - wykonanie narzędzi
- Auto-routing do odpowiednich endpointów

### 39. Executor (`core/executor.py`)
**Funkcje:**
- `Programista` - wykonywanie kodu (Python, Bash, Node.js, etc.)
- `_run()` - shell command execution
- Sandboxing, timeout, bezpieczeństwo

### 40. Auth (`core/auth.py`)
**Funkcje:**
- `check_auth()` - weryfikacja tokena
- `auth_dependency()` - FastAPI dependency
- `extract_token()`, `get_ip_address()`

### 41. Middleware (`core/middleware.py`)
**Funkcje:**
- `LLMCACHE` - cache dla LLM responses
- `SearchCache` - cache dla search results
- `RateLimiter` - rate limiting per user/IP

### 42. Metrics (`core/metrics.py`)
**Funkcje:**
- Prometheus metrics collection
- `record_request()`, `record_error()`
- LLM cache stats, DB stats

### 43. Hierarchical Memory (`core/hierarchical_memory.py`)
**Funkcje:**
- 3-poziomowa pamięć: L1 (epizody), L2 (fakty semantyczne), L3 (meta-knowledge)
- `store_episode()`, `store_semantic_fact()`, `consolidate_to_meta()`

### 44. Prompt Templates (`core/prompt.py`)
**Funkcje:**
- Szablony promptów dla różnych zadań
- System prompts, user prompts
- Formatowanie kontekstu

---

## 📊 STATYSTYKI FINALNE

- **Endpointy HTTP:** 85 (15 plików)
- **Moduły pomocnicze:** 29 (core/)
- **Główne funkcje:** 200+
- **Klasy:** 50+
- **Integracje:** OpenAI, DeepInfra, Qwen3, SERPAPI, Firecrawl, DuckDuckGo, Wikipedia, arXiv, Semantic Scholar
- **Bazy danych:** SQLite (mem.db, psyche, LTM)
- **AI Models:** LLM (Qwen3), Embeddings (sentence-transformers), spaCy, Vision

---

**Koniec mapy endpointów i modułów.**
