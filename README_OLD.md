# 🔥 Mordzix AI - Superinteligentny Asystent

> Full-stack aplikacja AI z auto-learningiem, pamięcią długoterminową i zaawansowaną psychiką.

---

## 📂 Struktura Projektu

```
/workspace/mrd/
├── 📄 app.py                      # Main FastAPI application
├── 📄 assistant_endpoint.py       # Chat assistant (10 intents + auto-learning)
├── 📄 assistant_auto.py           # Auto-learning mechanisms
├── 📄 monolit.py                  # Core utilities (legacy)
├── 📄 prompt.py                   # Mordzix system prompt
│
├── 📡 ENDPOINTS:
│   ├── travel_endpoint.py         # Travel & maps (hotels, restaurants, trip planning)
│   ├── psyche_endpoint.py         # Psyche system (mood, energy, episodes)
│   ├── files_endpoint.py          # File management (upload, analyze, OCR)
│   ├── admin_endpoint.py          # Admin tools (cache, stats)
│   ├── programista_endpoint.py    # Code executor (shell, git, docker)
│   ├── graphics_endpoint.py       # Image generation (Stability AI)
│   ├── tools_endpoint.py          # Web tools (news, sport, search)
│   └── writer_endpoint.py         # Writing tools (Vinted, SEO, social)
│
├── 🧠 core/
│   ├── memory.py                  # STM/LTM + psyche functions
│   ├── config.py                  # Configuration & env vars
│   ├── models.py                  # Pydantic models
│   ├── llm.py                     # LLM API client
│   ├── embeddings.py              # Embedding generator
│   ├── semantic.py                # Semantic analysis
│   ├── writer.py                  # Writing utilities
│   ├── travel.py                  # Travel search functions
│   ├── graphics.py                # Graphics generation
│   ├── tools.py                   # Web scraping tools
│   └── programista.py             # Code execution class
│
├── 🎨 chat.html                   # Frontend (PWA, streaming, speech)
│
├── ⚙️  CONFIG:
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Environment variables template
│   ├── .env                       # Your API keys (DO NOT COMMIT!)
│   └── start.sh                   # Production launcher
│
├── 🐳 DOCKER:
│   ├── Dockerfile                 # Multi-stage build
│   ├── docker-compose.yml         # Compose config
│   └── .dockerignore              # Docker ignore rules
│
├── 📁 DATA DIRECTORIES:
│   ├── uploads/                   # Uploaded files
│   ├── out/images/                # Generated images
│   ├── data/mem/                  # Memory database
│   └── logs/                      # Application logs
│
└── 📚 DOCS:
    ├── README.md                  # This file
    ├── INSTALLATION.md            # Installation guide
    └── README_START.md            # Quick start
```

---

## 🚀 Szybki Start

### 1️⃣ Konfiguracja

```bash
# 1. Skopiuj i wypełnij .env
cp .env.example .env
nano .env  # Dodaj swoje API keys

# 2. Uruchom (auto-install wszystkiego)
./start.sh

# 3. Otwórz w przeglądarce
http://localhost:8080
```

### 2️⃣ Skrypty Uruchomieniowe

Projekt zawiera automatyczne skrypty startowe dla różnych systemów operacyjnych:

#### Linux / macOS
```bash
# Jednorazowo: nadaj prawa wykonania
chmod +x start.sh

# Uruchom aplikację (tworzy venv, instaluje zależności, ładuje .env, zabija stare procesy)
./start.sh
```

#### Windows (PowerShell)
```powershell
# Uruchom w PowerShell (może wymagać uruchomienia jako Administrator)
.\start_full_windows.ps1 -Port 8080

# Lub z domyślnym portem
.\start_full_windows.ps1
```

#### Diagnostyka Zależności
```bash
# Sprawdź kompletność requirements.txt względem importów w kodzie
python scripts/check_requirements.py --root .

# Spróbuj automatycznie zainstalować brakujące pakiety
python scripts/check_requirements.py --root . --install
```

**Co robią skrypty startowe:**
- Tworzą/aktywują virtual environment (venv)
- Instalują wszystkie zależności z `requirements.txt`
- Sprawdzają kompletność `requirements.txt` (raportują brakujące pakiety)
- Ładują zmienne środowiskowe z pliku `.env`
- Zabijają poprzednie procesy na porcie 8080
- Uruchamiają aplikację FastAPI z uvicorn w trybie reload

### 3️⃣ Wymagania

- **Python 3.10+**
- **Klucze API:**
  - DeepInfra (LLM) - [deepinfra.com](https://deepinfra.com)
  - SERPAPI (optional) - [serpapi.com](https://serpapi.com)
  - Firecrawl (optional) - [firecrawl.dev](https://firecrawl.dev)
  - OpenTripMap (optional) - [opentripmap.com](https://opentripmap.com)

---

## 🔥 Funkcje

### 🧠 Auto-Learning
- ✅ **Auto STM→LTM** - Automatyczny transfer ważnych wiadomości
- ✅ **Web Research** - Automatyczne wyszukiwanie w internecie
- ✅ **Metamemory** - Profil użytkownika z preferencjami
- ✅ **Question Prediction** - Przewidywanie pytań followup
- ✅ **Feedback Learning** - Uczenie się z feedbacku

### 🎯 Intents (Natural Language)
1. **Travel** - "Znajdź hotel w Warszawie"
2. **Files** - "Przeanalizuj plik xyz.pdf"
3. **Psyche** - "Jakie masz samopoczucie?"
4. **Writing** - "Napisz opis Vinted"
5. **Programmer** - "Wykonaj: ls -la"
6. **Graphics** - "Wygeneruj obrazek kota"
7. **Tools** - "Co w wiadomościach?"
8. **Memory** - "Zapamiętaj że lubię pizzę"
9. **Feedback** - "👍 Świetna odpowiedź"
10. **Admin** - "Wyczyść cache"

### 🎨 Frontend
- ✅ **Streaming** - Real-time typing
- ✅ **Speech Recognition** - Mikrofon
- ✅ **File Upload** - Drag & drop
- ✅ **Sidebar** - Historia rozmów
- ✅ **iOS Optimized** - PWA ready
- ✅ **Dark Theme** - Modern UI

### 🔧 API Endpoints (53 total)
```
POST   /api/chat/assistant          # Chat (non-streaming)
POST   /api/chat/assistant/stream   # Chat (streaming)
GET    /api/chat/history            # Get conversation history

POST   /api/travel/hotels           # Search hotels
POST   /api/travel/restaurants      # Search restaurants
POST   /api/travel/trip-plan        # Plan trip
POST   /api/travel/geocode          # Get coordinates

POST   /api/files/upload            # Upload file
GET    /api/files/list              # List files
POST   /api/files/analyze           # Analyze file
POST   /api/files/batch/analyze     # Batch analyze
GET    /api/files/stats             # File statistics

GET    /api/psyche/status           # Get psyche state
POST   /api/psyche/update           # Update psyche
POST   /api/psyche/reset            # Reset psyche
POST   /api/psyche/observe          # Auto sentiment analysis
POST   /api/psyche/episode          # Add episode
POST   /api/psyche/reflect          # Reflect on state

... (47 więcej - zobacz /docs)
```

---

## 📊 Konfiguracja (.env)

```bash
# Authentication
AUTH_TOKEN=your_secret_token

# LLM (REQUIRED)
LLM_BASE_URL=https://api.deepinfra.com/v1/openai
LLM_API_KEY=your_deepinfra_key
LLM_MODEL=zai-org/GLM-4.5

# Paths
WORKSPACE=/workspace/mrd
MEM_DB=/workspace/mrd/mem.db

# External APIs (OPTIONAL)
SERPAPI_KEY=your_serpapi_key
FIRECRAWL_API_KEY=your_firecrawl_key
OTM_API_KEY=your_opentripmap_key

# Features (1=enabled, 0=disabled)
ENABLE_SEMANTIC=1
ENABLE_RESEARCH=1
ENABLE_PSYCHE=1
ENABLE_TRAVEL=1
ENABLE_WRITER=1

# Rate Limiting
RATE_LIMIT_PER_MINUTE=160
RL_DISABLE=0
```

---

## 🐳 Docker

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 🧪 Testowanie

```bash
# Health check
curl http://localhost:8080/health

# Chat (non-streaming)
curl -X POST http://localhost:8080/api/chat/assistant \
  -H "Content-Type: application/json" \
  -d '{"message": "Cześć!", "conversation_id": "test-123"}'

# Chat (streaming)
curl -N -X POST http://localhost:8080/api/chat/assistant/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Opowiedz mi żart", "conversation_id": "test-123"}'
```

---

## 📈 Architektura

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (PWA)                      │
│  chat.html (Vanilla JS + Web Speech API)               │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/SSE
┌──────────────────▼──────────────────────────────────────┐
│                  FASTAPI APP (app.py)                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │      assistant_endpoint.py (Main Chat)          │   │
│  │  • 10 Intent Handlers                           │   │
│  │  • Auto-learning (STM→LTM, web research)        │   │
│  │  • Context injection (LTM, user profile)        │   │
│  │  • Psyche influence on responses                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │   travel_    │ │   psyche_    │ │   files_     │   │
│  │  endpoint    │ │  endpoint    │ │  endpoint    │   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ programista_ │ │  graphics_   │ │   tools_     │   │
│  │  endpoint    │ │  endpoint    │ │  endpoint    │   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
│  ┌──────────────┐ ┌──────────────┐                    │
│  │   writer_    │ │   admin_     │                    │
│  │  endpoint    │ │  endpoint    │                    │
│  └──────────────┘ └──────────────┘                    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                   CORE MODULES                          │
│  • memory.py (STM/LTM/Psyche)                          │
│  • llm.py (OpenAI-compatible API)                      │
│  • embeddings.py (Semantic search)                     │
│  • semantic.py (Context analysis)                      │
│  • config.py (Environment vars)                        │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                  EXTERNAL APIs                          │
│  • DeepInfra (LLM)                                     │
│  • SERPAPI (Google Search)                             │
│  • Firecrawl (Web Scraping)                            │
│  • OpenTripMap (Travel)                                │
│  • Stability AI (Image Generation)                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run in dev mode (auto-reload)
uvicorn app:app --reload --host 0.0.0.0 --port 8080

# Run tests
pytest tests/

# Lint
flake8 .
black .
```

---

## 📝 Licencja

Proprietary - All rights reserved

---

## 👨‍💻 Author

**Mordzix AI Team**
- GitHub: [ahui69/aktywmrd](https://github.com/ahui69/aktywmrd)
- Version: 3.3.0

---

## 🆘 Support

1. Sprawdź `/docs` - Swagger UI
2. Zobacz logi: `tail -f logs/mordzix.log`
3. Debug: `docker-compose logs -f`

---

**🔥 Built with ❤️ for maximum intelligence and automation**
