# 🚀 MORDZIX AI - Advanced AI System

**Wersja:** 5.0.0  
**Status:** Production Ready  
**Stack:** FastAPI + React + TypeScript + SQLite + Redis  
**Endpointy:** 177 API endpoints across 25 routers

## 📋 Spis Treści

1. [Architektura](#architektura)
2. [Funkcje](#funkcje)
3. [Instalacja](#instalacja)
4. [Deployment](#deployment)
5. [API Documentation](#api-documentation)
6. [Konfiguracja](#konfiguracja)
7. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architektura

```
EHH/
├── app.py                    # Main application entry point
├── start.sh                  # All-in-one startup script (RECOMMENDED)
├── requirements.txt          # Python dependencies (full list)
│
├── ROOT ENDPOINTS (17 files):
│   ├── assistant_endpoint.py    # /api/chat/* (main chat)
│   ├── admin_endpoint.py        # /api/admin/* (stats, cache)
│   ├── nlp_endpoint.py          # /api/nlp/* (spaCy, NER, sentiment)
│   ├── cognitive_endpoint.py    # /api/cognitive/* (self-reflection)
│   ├── suggestions_endpoint.py  # /api/suggestions/* (proactive)
│   ├── programista_endpoint.py  # /api/code/* (code execution)
│   ├── captcha_endpoint.py      # /api/captcha/* (captcha solver)
│   ├── tts_endpoint.py          # /api/tts/* (text-to-speech)
│   ├── research_endpoint.py     # /api/research/* (web search)
│   ├── psyche_endpoint.py       # /api/psyche/* (AI emotions)
│   ├── files_endpoint.py        # /api/files/* (upload, OCR, PDF)
│   ├── prometheus_endpoint.py   # /api/prometheus/* (metrics)
│   ├── batch_endpoint.py        # /api/batch/* (queue processing)
│   ├── internal_endpoint.py     # /api/internal/* (system info)
│   ├── travel_endpoint.py       # /api/travel/* (hotels, restaurants)
│   ├── writing_endpoint.py      # /api/writing/* (creative writing)
│   └── stt_endpoint.py          # /api/stt/* (speech-to-text)
│
├── core/                     # Backend modules
│   ├── app.py               # FastAPI app with all routers mounted
│   ├── assistant_endpoint.py # (duplicate in core)
│   ├── cognitive_endpoint.py # (duplicate in core)
│   ├── memory_endpoint.py    # /api/memory/* (STM/LTM system)
│   ├── research_endpoint.py  # (duplicate in core)
│   ├── batch_endpoint.py     # (duplicate in core)
│   ├── psyche_endpoint.py    # (duplicate in core)
│   ├── suggestions_endpoint.py # (duplicate in core)
│   ├── prometheus_endpoint.py # (duplicate in core)
│   ├── advanced_memory.py    # Memory management (STM→LTM)
│   ├── advanced_llm.py       # LLM integration
│   └── metrics.py            # Prometheus metrics
│
└── frontend/                 # React + TypeScript UI
    ├── src/
    │   ├── App.tsx           # Main application
    │   ├── components/       # ChatArea, Sidebar, SettingsPanel
    │   │   ├── ChatArea.tsx  # Chat interface (ChatGPT-style)
    │   │   ├── Sidebar.tsx   # Conversation list
    │   │   └── SettingsPanel.tsx # Settings
    │   ├── services/api.ts   # API integration
    │   ├── store/chatStore.ts # Zustand state management
    │   └── types/index.ts    # TypeScript types
    └── dist/mordzix-ai/      # Production build
```

### Backend Stack

- **FastAPI 0.114.1** - High-performance async web framework
- **SQLite** - Local memory database (STM/LTM/Facts/Psyche)
- **Redis 5.2.0** - Caching layer (optional)
- **spaCy 3.7.5** - NLP processing (Polish + English models)
- **Sentence Transformers 3.0.1** - Semantic embeddings
- **OpenAI 1.35.0** - LLM integration
- **SQLAlchemy 2.0.35** - ORM
- **Pydantic 2.9.2** - Data validation

### Frontend Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite 5.4.21** - Build tool
- **Tailwind CSS** - Styling (professional gray/neutral palette, NO BLUE SHIT)
- **Zustand** - State management (lightweight)
- **Marked + DOMPurify** - Markdown rendering with XSS protection

---

## ✨ Funkcje

### 🧠 Core Features

1. **Advanced Memory System** (`/api/memory/*`)
   - **Short-Term Memory (STM)** → **Long-Term Memory (LTM)** auto-transfer
   - **Hierarchical facts database** with FTS5 full-text search
   - **Semantic embeddings** for context-aware retrieval
   - **User-specific memory** isolation
   - **Meta-memory** - learned preferences, habits, facts

2. **Cognitive Engine** (`/api/cognitive/*`)
   - Self-reflection and meta-cognition
   - Proactive suggestion generation
   - Multi-agent collaboration
   - **Psychological state tracking** (mood, energy, focus)
   - Personality styles (rzeczowy, kreatywny, empatyczny)

3. **Web Research** (`/api/research/*`)
   - **DuckDuckGo** search
   - **Wikipedia** integration
   - **arXiv** scientific papers
   - **Semantic Scholar** academic search
   - Auto-learning from search results
   - Document caching with FTS5

4. **Batch Processing** (`/api/batch/*`)
   - Queue-based task execution
   - Progress tracking
   - Parallel processing support
   - Job status monitoring

5. **File Analysis** (`/api/files/*`)
   - **PDF** text extraction (PyPDF2)
   - **Image OCR** (Tesseract)
   - Document upload & storage
   - Multi-file processing

6. **NLP Processing** (`/api/nlp/*`)
   - **spaCy** Polish + English models
   - **Named Entity Recognition (NER)**
   - **Sentiment analysis**
   - **Keyword extraction**
   - Part-of-speech tagging

7. **Code Execution** (`/api/code/*`)
   - Shell command execution
   - Git operations
   - Docker build/run
   - Python/Node.js execution
   - **Security:** Manual approval for dangerous operations

8. **Speech & Audio** (`/api/tts/*`, `/api/stt/*`)
   - **Text-to-Speech** (ElevenLabs integration)
   - **Speech-to-Text** (Whisper planned)
   - Voice synthesis

9. **Creative Writing** (`/api/writing/*`)
   - Blog post generation
   - Article writing
   - Content optimization
   - SEO suggestions

10. **Travel Search** (`/api/travel/*`)
    - Hotel recommendations
    - Restaurant search
    - Attractions & activities
    - Location-based suggestions

### 🎨 Frontend Features

- **ChatGPT-style Interface** - Clean, professional gray design (NO FUCKING BLUE)
- **Real-time Streaming** - SSE-based response streaming
- **Conversation Management** - Save, load, delete conversations
- **Export/Import** - JSON-based data portability
- **Dark/Light Mode** - System preference aware
- **Settings Panel** - Temperature, max tokens, feature toggles
- **File Upload** - Drag-drop interface with preview
- **Voice Input** - Speech-to-text (planned)
- **Markdown Support** - Rich text rendering with code syntax highlighting
- **Auto-create Conversation** - No more empty state on load

---

## 🛠️ Instalacja

### Wymagania

- **Python 3.10+**
- **Node.js 18+**
- **npm 9+**
- **Git**
- **Optional:** Redis, Tesseract OCR, ffmpeg

### Quick Start (One-Command Deploy)

```bash
git clone https://github.com/ahui69/EHH.git
cd EHH
bash start.sh
```

**Start.sh robi WSZYSTKO:**
1. ✅ Sprawdza Python 3 + Node.js
2. ✅ Zabija stare procesy na porcie 8080
3. ✅ Buduje frontend (React + Vite → production)
4. ✅ Tworzy venv i instaluje ALL dependencies
5. ✅ Inicjalizuje bazę danych SQLite (13 tabel)
6. ✅ Instaluje modele spaCy (pl_core_news_sm + en_core_web_sm)
7. ✅ Instaluje Tesseract OCR + ffmpeg (jeśli apt-get dostępne)
8. ✅ Uruchamia serwer uvicorn na 0.0.0.0:8080
9. ✅ Auto-restart na crash

### Manual Installation

#### Backend

```bash
# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip wheel
pip install -r requirements.txt

# Install spaCy models
python -m spacy download pl_core_news_sm
python -m spacy download en_core_web_sm

# Initialize database (creates 13 tables)
python <<EOF
from core.advanced_memory import _init_db
_init_db()
EOF
```

#### Frontend

```bash
cd frontend
npm ci --no-audit
npm run build  # or: npm run build:prod
```

#### Run

```bash
# Development (auto-reload)
uvicorn app:app --reload --port 8080

# Production (single worker for memory consistency)
uvicorn app:app --host 0.0.0.0 --port 8080 --workers 1
```

---

## 🚀 Deployment

### OVH VPS (Ubuntu 22.04) - 162.19.220.29

#### 1. Clone Repository

```bash
ssh ubuntu@162.19.220.29
cd ~
git clone https://github.com/ahui69/EHH.git
cd EHH
```

#### 2. Install System Dependencies

```bash
# System packages
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm tesseract-ocr ffmpeg

# Node.js 18 (if not installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### 3. Configure Environment

```bash
# Create .env file
cat > .env <<EOF
AUTH_TOKEN=ssjjMijaja6969
MEM_DB=/home/ubuntu/EHH/mem.db
OPENAI_API_KEY=your_key_here
WORKSPACE=/home/ubuntu/EHH
UPLOAD_DIR=/home/ubuntu/EHH/uploads
EOF
```

#### 4. Deploy (ONE COMMAND)

```bash
bash start.sh
```

#### 5. Systemd Service (Production)

```bash
sudo tee /etc/systemd/system/mordzix.service > /dev/null <<EOF
[Unit]
Description=Mordzix AI Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/EHH
ExecStart=/home/ubuntu/EHH/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3
Environment="PATH=/home/ubuntu/EHH/.venv/bin:/usr/bin"
Environment="MEM_DB=/home/ubuntu/EHH/mem.db"
Environment="AUTH_TOKEN=ssjjMijaja6969"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mordzix
sudo systemctl start mordzix
sudo systemctl status mordzix
```

#### 6. Nginx Reverse Proxy (Optional)

```bash
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/mordzix <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/mordzix /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📚 API Documentation

### 🔐 Authentication

```bash
# Set AUTH_TOKEN in .env or environment
export AUTH_TOKEN=ssjjMijaja6969

# Use in requests (Header or Query)
curl -H "Authorization: Bearer ssjjMijaja6969" http://localhost:8080/api/chat/assistant
# OR
curl "http://localhost:8080/api/admin/stats?auth=ssjjMijaja6969"
```

### 📡 Endpoints Overview (177 total)

**25 Routers:**
- `/api/chat/*` - Main AI assistant (streaming, completions)
- `/api/memory/*` - Memory system (STM/LTM/facts)
- `/api/cognitive/*` - Cognitive engine (reflection, planning)
- `/api/research/*` - Web search (DuckDuckGo, Wikipedia, arXiv)
- `/api/batch/*` - Batch processing queue
- `/api/psyche/*` - AI psychological state
- `/api/suggestions/*` - Proactive suggestions
- `/api/nlp/*` - NLP processing (spaCy, NER, sentiment)
- `/api/code/*` - Code execution (shell, git, docker)
- `/api/files/*` - File upload/analysis (PDF, OCR)
- `/api/writing/*` - Creative writing generator
- `/api/travel/*` - Travel search (hotels, restaurants)
- `/api/tts/*` - Text-to-speech
- `/api/stt/*` - Speech-to-text
- `/api/admin/*` - Admin panel (stats, cache)
- `/api/internal/*` - Internal UI manifest
- `/api/captcha/*` - Captcha solver
- `/api/prometheus/*` - Metrics endpoint

### 🎯 Key Endpoints

#### 1. Chat (Main AI Assistant)

**POST** `/api/chat/assistant`

```json
{
  "messages": [
    {"role": "user", "content": "Czym jest kwantowa teoria pola?"}
  ],
  "user_id": "user123",
  "use_memory": true,
  "use_research": true,
  "internet_allowed": true,
  "auto_learn": true,
  "use_batch_processing": false
}
```

**Response:**

```json
{
  "ok": true,
  "answer": "Kwantowa teoria pola (QFT) to...",
  "sources": [...],
  "metadata": {
    "psyche_state": {...},
    "memory_used": true,
    "research_performed": true,
    "tokens_used": 1234
  }
}
```

**POST** `/api/chat/assistant/stream` - SSE streaming response

#### 2. Memory System

**GET** `/api/memory/stats?user_id=user123`

```json
{
  "ok": true,
  "stm_count": 42,
  "ltm_count": 18,
  "facts_count": 156,
  "embeddings_count": 24,
  "total_tokens": 50000
}
```

**POST** `/api/memory/search` - Semantic search in LTM

```json
{
  "query": "sztuczna inteligencja",
  "user_id": "user123",
  "limit": 10,
  "use_embeddings": true
}
```

**POST** `/api/memory/add_fact` - Add fact to knowledge base

**GET** `/api/memory/facts?user_id=user123&deleted=false` - List facts

**DELETE** `/api/memory/clear?user_id=user123` - Clear user memory

#### 3. Research (Web Search)

**GET** `/api/research/search?q=quantum computing&engines=duckduckgo,wikipedia&max_results=10`

```json
{
  "ok": true,
  "query": "quantum computing",
  "engines": ["duckduckgo", "wikipedia"],
  "results": [
    {
      "title": "Quantum Computing",
      "url": "https://...",
      "snippet": "...",
      "source": "wikipedia",
      "relevance": 0.95
    }
  ],
  "total": 10
}
```

**Supported engines:**
- `duckduckgo` - General web search
- `wikipedia` - Encyclopedia
- `arxiv` - Scientific papers
- `scholar` - Semantic Scholar (academic)

#### 4. Batch Processing

**POST** `/api/batch/submit`

```json
{
  "tasks": [
    {"query": "Task 1", "user_id": "user123"},
    {"query": "Task 2", "user_id": "user123"}
  ],
  "mode": "parallel"
}
```

**Response:**

```json
{
  "ok": true,
  "job_id": "batch_1730000000",
  "task_count": 2,
  "status": "queued"
}
```

**GET** `/api/batch/status/{job_id}` - Check job status

```json
{
  "ok": true,
  "job_id": "batch_1730000000",
  "status": "completed",
  "progress": 100,
  "completed": 2,
  "failed": 0,
  "results": [...]
}
```

#### 5. Psyche (AI Psychological State)

**GET** `/api/psyche/status`

```json
{
  "ok": true,
  "mood": 0.2,
  "energy": 0.6,
  "focus": 0.7,
  "openness": 0.55,
  "directness": 0.62,
  "agreeableness": 0.55,
  "conscientiousness": 0.63,
  "neuroticism": 0.44,
  "style": "rzeczowy",
  "updated": 1730000000.0
}
```

**POST** `/api/psyche/event` - Log emotional event

```json
{
  "user_id": "user123",
  "kind": "success",
  "valence": 1.0,
  "intensity": 0.8,
  "tags": "problem_solving,programming",
  "note": "User solved complex algorithm"
}
```

#### 6. NLP Processing

**POST** `/api/nlp/analyze`

```json
{
  "text": "To jest przykładowy tekst do analizy.",
  "tasks": ["ner", "sentiment", "keywords", "pos"]
}
```

**Response:**

```json
{
  "ok": true,
  "text": "To jest przykładowy tekst...",
  "language": "pl",
  "entities": [...],
  "sentiment": {"label": "positive", "score": 0.85},
  "keywords": ["przykładowy", "tekst", "analiza"],
  "pos_tags": [...]
}
```

#### 7. Code Execution

**POST** `/api/code/exec`

```json
{
  "command": "ls -la",
  "cwd": "/workspace",
  "timeout": 30
}
```

**⚠️ Security:** Requires manual approval for dangerous operations (git, docker, file write)

#### 8. File Upload

**POST** `/api/files/upload` - Multipart form-data

**POST** `/api/files/analyze` - Extract text from PDF/Image (OCR)

```json
{
  "file_path": "/uploads/document.pdf",
  "extract_text": true,
  "ocr": true
}
```

### Full API Docs

Visit: **http://localhost:8080/docs** (Swagger UI)  
Or: **http://localhost:8080/redoc** (ReDoc)

**GET** `/api/endpoints/list` - List all 177 endpoints

---

## ⚙️ Konfiguracja

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_TOKEN` | `ssjjMijaja6969` | API authentication token |
| `MEM_DB` | `./mem.db` | SQLite database path |
| `WORKSPACE` | `./` | Working directory |
| `UPLOAD_DIR` | `./uploads` | File upload directory |
| `OPENAI_API_KEY` | - | OpenAI API key (required for LLM) |
| `REDIS_URL` | - | Redis connection URL (optional) |
| `FAST_START` | `0` | Skip heavy init (1=yes, faster startup) |
| `MORDZIX_SUPPRESS_STARTUP_LOGS` | `0` | Suppress startup logs (1=quiet) |
| `SKIP_FRONTEND_BUILD` | `0` | Skip frontend build in start.sh |
| `SKIP_FRONTEND_INSTALL` | `0` | Skip npm ci in start.sh |

### Frontend Settings (Zustand Store)

Located in `frontend/src/store/chatStore.ts`:

```typescript
settings: {
  theme: 'dark',           // 'light' | 'dark'
  temperature: 0.7,        // 0.0 - 2.0 (LLM creativity)
  maxTokens: 2000,         // Max response tokens
  model: 'gpt-4-turbo-preview',
  userId: 'default',       // User identifier for memory
  useMemory: true,         // Enable LTM injection
  useResearch: true,       // Enable web search
  autoLearn: true,         // Auto-save facts to knowledge base
  internetAccess: false,   // Allow real-time web access
  useBatchProcessing: false // Use batch queue for long tasks
}
```

### Database Schema (SQLite)

**13 Tables:**

1. `memory` - Short-term memory (recent messages)
2. `memory_long` - Long-term memory (summaries, consolidated knowledge)
3. `meta_memory` - User metadata (preferences, learned facts)
4. `facts` - Knowledge base (facts, definitions, learned info)
5. `facts_fts` - FTS5 full-text search index for facts
6. `mem_embed` - Semantic embeddings (vector storage)
7. `docs` - Scraped web documents (research cache)
8. `docs_fts` - FTS5 index for documents
9. `cache` - API response cache (web search, LLM responses)
10. `psy_state` - AI psychological state (mood, energy, focus, personality)
11. `psy_episode` - Emotional events log (success, failure, frustration, joy)
12. `batch_jobs` - Batch processing queue (planned)
13. `sessions` - User sessions (planned)

**Indexes:**
- `idx_facts_deleted` - Soft delete filter
- `idx_facts_created` - Sort by creation time
- `idx_facts_tags` - Tag-based search
- `idx_memory_user_ts` - User + timestamp for STM
- `idx_memory_long_user_ts` - User + timestamp for LTM
- `idx_cache_ts` - Cache expiration
- `idx_psy_episode_user_ts` - Episode search
- `idx_psy_episode_ts` - Timeline view

---

## 🐛 Troubleshooting

### Port 8080 Already in Use

```bash
# Kill existing process
sudo lsof -ti:8080 | xargs kill -9

# Or use fuser
fuser -k 8080/tcp

# Or use start.sh (auto-kills old processes)
bash start.sh
```

### Frontend Not Loading / Blue Colors Visible

```bash
# Rebuild frontend with CORRECT gray palette
cd frontend
rm -rf dist node_modules
npm install
npm run build

# Check dist structure
ls -la frontend/dist/mordzix-ai/
# Should contain: index.html, assets/*.js, assets/*.css

# Verify Tailwind config uses gray (NOT sky-blue)
grep -A 15 "colors:" frontend/tailwind.config.js
# Should show: primary: { 50-900 with GRAY values }
```

### Database Locked

```bash
# Stop all processes
pkill -9 -f "uvicorn.*app:app"
pkill -9 -f "python.*app.py"

# Delete lock files
rm -f mem.db-wal mem.db-shm

# Restart
bash start.sh
```

### Import Errors (core.*, cannot import X)

```bash
# Ensure you're in project root
cd /path/to/EHH

# Check PYTHONPATH (should include project root)
export PYTHONPATH=/path/to/EHH:$PYTHONPATH

# Or run via module (Python adds CWD to path)
python -m uvicorn app:app --port 8080

# Verify core/ is importable
python -c "from core.app import app; print('OK')"
```

### spaCy Models Missing

```bash
# Install Polish model
python -m spacy download pl_core_news_sm

# Install English model
python -m spacy download en_core_web_sm

# Verify installation
python -c "import spacy; nlp = spacy.load('pl_core_news_sm'); print('PL OK')"
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('EN OK')"

# Check models path
python -m spacy info
```

### React Not Mounting (Empty #root div)

```bash
# Check browser console for errors
curl http://localhost:8080/ | grep '<div id="root">'
# Should show: <div id="root"></div>

# Check assets loading
curl -I http://localhost:8080/assets/index-*.js
# Should return: HTTP 200 OK

# Verify API base URL in frontend
grep -r "localhost:8080" frontend/src/
# Should proxy via vite.config.ts: proxy: { '/api': 'http://localhost:8080' }

# Force browser cache clear
# Add ?v=random to assets (start.sh does this automatically via cache buster)
```

### Memory Not Persisting / Facts Not Saving

```bash
# Check database exists and is writable
ls -la mem.db
chmod 664 mem.db

# Initialize database (creates all 13 tables)
python <<EOF
from core.advanced_memory import _init_db
_init_db()
EOF

# Verify tables exist
sqlite3 mem.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
# Should list: cache, docs, docs_fts, facts, facts_fts, mem_embed, memory, memory_long, meta_memory, psy_episode, psy_state

# Test memory write
sqlite3 mem.db "INSERT INTO facts(id,text,tags,conf,created) VALUES('test1','test fact','test',1.0,$(date +%s)); SELECT * FROM facts WHERE id='test1';"
```

### 177 Endpoints Not Loading

```bash
# Check which routers are mounted
curl http://localhost:8080/api/endpoints/list | python -m json.tool | grep -c '"path"'
# Should show: 177

# Check startup logs
python app.py 2>&1 | grep "✓"
# Should show 17-25 lines like: "✓ Assistant endpoint /api/chat/*"

# Verify app.py imports all routers
grep "app.include_router" app.py | wc -l
# Should show: 17+ (root routers) + 8 (core routers) = 25 total
```

### Cognitive/Memory Endpoints 404

```bash
# Check if cognitive_endpoint.py and memory_endpoint.py are in core/
ls -la core/*_endpoint.py
# Should include: cognitive_endpoint.py, memory_endpoint.py

# Verify they're imported in core/app.py
grep -A 5 "cognitive_endpoint\|memory_endpoint" core/app.py
# Should show: import cognitive_endpoint + app.include_router(cognitive_endpoint.router)

# Test directly
curl http://localhost:8080/api/cognitive/health
curl http://localhost:8080/api/memory/stats?user_id=test
```

---

## 📊 Performance

- **Startup time:** ~3-5s (with DB init + spaCy models)
- **Response time:** 200-500ms (without LLM call), 2-5s (with OpenAI)
- **Memory usage:** ~300MB (idle), ~800MB (active with NLP models)
- **Concurrent users:** 10-50 (single worker), 100+ (with multi-worker + Redis)
- **Database size:** ~10MB per 10k messages, ~50MB per 100k facts
- **Frontend bundle:** ~256KB JS + ~17KB CSS (gzipped: ~85KB JS + ~4KB CSS)

---

## 🔒 Security

- ✅ **CORS** enabled (configurable origins)
- ✅ **Token-based auth** (Bearer token in headers)
- ✅ **Input validation** (Pydantic models)
- ✅ **SQL injection prevention** (parameterized queries)
- ✅ **XSS prevention** (DOMPurify in frontend)
- ✅ **Manual approval** for dangerous code operations (git, docker, file write)
- ⚠️ **Production:** Use HTTPS + strong AUTH_TOKEN (not default)
- ⚠️ **Production:** Rate limiting recommended (nginx limit_req)
- ⚠️ **Production:** Firewall rules (allow only 80/443)

---

## 📝 License

MIT License - See LICENSE file

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

**Code Style:**
- Python: PEP 8, type hints
- TypeScript: ESLint, Prettier
- Commits: Conventional Commits (feat:, fix:, docs:)

---

## 📞 Support

- **GitHub Issues:** https://github.com/ahui69/EHH/issues
- **API Docs:** http://localhost:8080/docs
- **Health Check:** http://localhost:8080/health
- **Endpoints List:** http://localhost:8080/api/endpoints/list

---

## 🎯 Roadmap

### In Progress
- [x] 177 API endpoints (DONE)
- [x] ChatGPT-style UI (gray palette, DONE)
- [x] Memory system (STM→LTM, DONE)
- [x] Web research (DuckDuckGo, Wikipedia, DONE)
- [x] Batch processing (DONE)
- [ ] Voice input/output (Whisper + ElevenLabs integration)

### Planned
- [ ] Multi-user authentication (JWT + user roles)
- [ ] WebSocket real-time sync
- [ ] Plugin system (custom tools)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Multi-language UI (i18n)
- [ ] Vector database (Pinecone/Weaviate)
- [ ] Fine-tuned models (local LLM)

---

**Made with ❤️ (and a lot of frustration) by ahui69**  
**Last updated:** October 25, 2025  
**Version:** 5.0.0 - Production Ready


---

## Licencja
Projekt udostępniany na licencji **MIT** (zob. plik `LICENSE`).  
Przy sprzedaży całości praw użyj dokumentu `TRANSFER_OF_RIGHTS.md` (szablon).

## Bezpieczeństwo
Zobacz `SECURITY.md`. W produkcji ustaw:
- `CORS_ORIGINS` (lista dozwolonych domen),
- `JWT_SECRET` / `JWT_ALG` (JWT w panelu admin),
- mocny `AUTH_TOKEN` (fallback lub do środowiska dev).


> **CI:** Skonfigurowane GitHub Actions (`.github/workflows/ci.yml`).  
> Badge (podmień `owner/repo`):  
> `![CI](https://github.com/owner/repo/actions/workflows/ci.yml/badge.svg)`


### Kontrakt odpowiedzi
Zobacz `docs/USAGE.md` – jak budować odpowiedzi `{ text, sources[] }` dla WebUI.


### WebUI
Otwórz `http://localhost:8080/webui` i wklej Bearer/JWT w pasku u góry. Komendy: `/r`, `/psy`, `/code`, drag&drop plików, 🎤 STT.
