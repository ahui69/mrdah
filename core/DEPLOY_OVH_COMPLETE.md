# 🚀 MORDZIX AI - KOMPLETNY DEPLOY NA OVH (Ubuntu)

## 📋 **SPIS TREŚCI**
1. [Przygotowanie serwera](#1-przygotowanie-serwera)
2. [Instalacja zależności](#2-instalacja-zależności)
3. [Setup projektu](#3-setup-projektu)
4. [Konfiguracja Nginx](#4-konfiguracja-nginx)
5. [SSL Certbot](#5-ssl-certbot)
6. [Supervisor (auto-restart)](#6-supervisor-auto-restart)
7. [Testy i monitoring](#7-testy-i-monitoring)

---

## 1. PRZYGOTOWANIE SERWERA

### **Logowanie przez SSH:**
```bash
ssh root@51.83.131.142
# Hasło: Pedalroman123
```

### **Aktualizacja systemu:**
```bash
apt-get update && apt-get upgrade -y
```

### **Utwórz użytkownika (opcjonalnie):**
```bash
adduser mordzix
usermod -aG sudo mordzix
su - mordzix
```

---

## 2. INSTALACJA ZALEŻNOŚCI

### **Python 3.11:**
```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
```

### **Narzędzia systemowe:**
```bash
sudo apt-get install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    wget \
    build-essential \
    sqlite3 \
    ffmpeg \
    supervisor
```

### **Sprawdź instalację:**
```bash
python3.11 --version  # Python 3.11.x
nginx -v              # nginx/1.x
certbot --version     # certbot 2.x
```

---

## 3. SETUP PROJEKTU

### **Katalog workspace:**
```bash
sudo mkdir -p /workspace/mrd
sudo chown -R $USER:$USER /workspace/mrd
cd /workspace/mrd
```

### **Upload plików projektu:**

**Opcja A: Git (jeśli masz repo):**
```bash
git clone https://github.com/TWOJ_REPO/mordzix-ai.git .
```

**Opcja B: SCP (z lokalnego):**
```bash
# Na LOKALNYM komputerze (Windows PowerShell):
scp -r C:\Users\48501\Desktop\mrd\* root@51.83.131.142:/workspace/mrd/
```

**Opcja C: Manual upload (FileZilla/WinSCP):**
- Host: `sftp://51.83.131.142`
- User: `root`
- Port: `22`
- Upload całego folderu `mrd` do `/workspace/mrd/`

### **Struktura katalogów:**
```bash
mkdir -p /workspace/mrd/logs
mkdir -p /workspace/mrd/out/uploads
mkdir -p /workspace/mrd/data
chmod -R 755 /workspace/mrd
```

### **Python virtual environment:**
```bash
cd /workspace/mrd
python3.11 -m venv .venv
source .venv/bin/activate
```

### **Instalacja pakietów:**
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Jeśli brak requirements.txt:
pip install \
    fastapi[all] \
    uvicorn[standard] \
    gunicorn \
    httpx \
    pydantic \
    python-multipart \
    beautifulsoup4 \
    readability-lxml \
    scikit-learn \
    numpy \
    python-dotenv \
    prometheus-client
```

---

## 4. KONFIGURACJA BAZY DANYCH

### **Utwórz SQLite z tabelami:**
```bash
cd /workspace/mrd
sqlite3 mem.db << 'EOF'
-- STM (Short-term Memory)
CREATE TABLE IF NOT EXISTS stm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp REAL NOT NULL,
    ttl INTEGER DEFAULT 1800
);
CREATE INDEX idx_stm_user ON stm(user_id);
CREATE INDEX idx_stm_timestamp ON stm(timestamp);

-- LTM (Long-term Memory)
CREATE TABLE IF NOT EXISTS ltm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT NOT NULL UNIQUE,
    source TEXT,
    confidence REAL DEFAULT 0.8,
    importance REAL DEFAULT 0.5,
    category TEXT,
    tags TEXT,
    embedding BLOB,
    created_at REAL NOT NULL,
    last_accessed REAL,
    access_count INTEGER DEFAULT 0
);
CREATE INDEX idx_ltm_fact ON ltm(fact);
CREATE INDEX idx_ltm_category ON ltm(category);

-- Psyche State
CREATE TABLE IF NOT EXISTS psyche_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    mood TEXT,
    energy REAL,
    creativity REAL,
    confidence REAL,
    emotions TEXT,
    cognitive_load REAL,
    timestamp REAL NOT NULL
);
CREATE INDEX idx_psyche_user ON psyche_state(user_id);

-- Episodes (Hierarchical Memory L1)
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    content TEXT,
    importance REAL DEFAULT 0.5,
    embedding BLOB,
    created_at REAL NOT NULL,
    consolidated INTEGER DEFAULT 0
);
CREATE INDEX idx_episodes_user ON episodes(user_id);

-- Procedures (Hierarchical Memory L3)
CREATE TABLE IF NOT EXISTS procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    steps TEXT,
    success_rate REAL DEFAULT 0.5,
    times_used INTEGER DEFAULT 0,
    created_at REAL NOT NULL
);

.quit
EOF

chmod 644 mem.db
```

### **Sprawdź tabele:**
```bash
sqlite3 mem.db "SELECT name FROM sqlite_master WHERE type='table';"
# Powinno pokazać: stm, ltm, psyche_state, episodes, procedures
```

---

## 5. KONFIGURACJA .ENV

```bash
cat > /workspace/mrd/.env << 'EOF'
# Mordzix AI - Production Configuration
AUTH_TOKEN=ssjjMijaja6969
WORKSPACE=/workspace/mrd
MEM_DB=/workspace/mrd/mem.db
UPLOAD_DIR=/workspace/mrd/out/uploads

# LLM Configuration (UZUPEŁNIJ KLUCZE!)
LLM_BASE_URL=https://api.deepinfra.com/v1/openai
LLM_API_KEY=your_deepinfra_key_here
LLM_MODEL=Qwen/QwQ-32B-Preview
LLM_TIMEOUT=60
LLM_RETRIES=3

# Embeddings
LLM_EMBED_URL=https://api.deepinfra.com/v1/openai
LLM_EMBED_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2

# Memory
STM_MAX_TURNS=400
STM_KEEP_TAIL=100
LTM_MIN_CONF=0.35
MAX_LTM_FACTS=2000000

# Learning
LEARN_ENABLE_OPEN=1
AUTO_TOPK=8
AUTON_SAVE_LTM=1

# Rate Limiting
RATE_LIMIT_PER_MINUTE=160
EOF

chmod 600 .env
```

**⚠️ WAŻNE: Edytuj `.env` i uzupełnij klucze API!**

```bash
nano /workspace/mrd/.env
# Zmień: LLM_API_KEY=TWOJ_PRAWDZIWY_KLUCZ
# Ctrl+O (save), Ctrl+X (exit)
```

---

## 6. KONFIGURACJA NGINX

### **Usuń domyślną konfigurację:**
```bash
sudo rm -f /etc/nginx/sites-enabled/default
```

### **Utwórz nową konfigurację:**
```bash
sudo tee /etc/nginx/sites-available/mordzix << 'EOF'
server {
    listen 80;
    listen [::]:80;
    
    server_name mordxixai.xyz www.mordxixai.xyz;
    
    # Logi
    access_log /workspace/mrd/logs/nginx_access.log;
    error_log /workspace/mrd/logs/nginx_error.log;
    
    # Maksymalne rozmiary
    client_max_body_size 100M;
    client_body_timeout 120s;
    
    # Proxy do Gunicorn (port 8080)
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support (streaming)
    location /api/chat/assistant/stream {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        access_log off;
    }
}
EOF
```

### **Aktywuj konfigurację:**
```bash
sudo ln -sf /etc/nginx/sites-available/mordzix /etc/nginx/sites-enabled/
sudo nginx -t  # Test konfiguracji
sudo systemctl reload nginx
sudo systemctl enable nginx
```

### **Sprawdź status:**
```bash
sudo systemctl status nginx
# Powinno być: active (running)
```

---

## 7. SSL CERTBOT (Let's Encrypt)

### **Pobierz certyfikat:**
```bash
sudo certbot --nginx \
    -d mordxixai.xyz \
    -d www.mordxixai.xyz \
    --non-interactive \
    --agree-tos \
    --email admin@mordxixai.xyz \
    --redirect
```

### **Test auto-renewal:**
```bash
sudo certbot renew --dry-run
```

### **Sprawdź certyfikat:**
```bash
sudo ls -la /etc/letsencrypt/live/mordxixai.xyz/
# Powinny być: cert.pem, chain.pem, fullchain.pem, privkey.pem
```

---

## 8. SUPERVISOR (Auto-restart)

### **Utwórz konfigurację:**
```bash
sudo tee /etc/supervisor/conf.d/mordzix.conf << 'EOF'
[program:mordzix]
directory=/workspace/mrd
command=/workspace/mrd/.venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8080 --timeout 120 --access-logfile /workspace/mrd/logs/gunicorn_access.log --error-logfile /workspace/mrd/logs/gunicorn_error.log app:app
autostart=true
autorestart=true
stderr_logfile=/workspace/mrd/logs/supervisor_error.log
stdout_logfile=/workspace/mrd/logs/supervisor_out.log
user=root
environment=PATH="/workspace/mrd/.venv/bin"
EOF
```

### **Załaduj i uruchom:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start mordzix
```

### **Sprawdź status:**
```bash
sudo supervisorctl status mordzix
# Powinno być: mordzix RUNNING pid 12345, uptime 0:00:05
```

---

## 9. TESTY I MONITORING

### **Test lokalny (z serwera):**
```bash
curl http://localhost:8080/health
# Oczekiwany: {"status":"healthy","timestamp":...}

curl http://localhost:8080/api
# Oczekiwany: {"ok":true,"app":"Mordzix AI",...}
```

### **Test publiczny (z przeglądarki):**
```
✅ https://mordxixai.xyz/health
✅ https://mordxixai.xyz/api
✅ https://mordxixai.xyz/docs
✅ https://mordxixai.xyz/chat_pro_clean.html
```

### **Monitorowanie logów:**
```bash
# Real-time logs (wszystkie)
sudo supervisorctl tail -f mordzix

# Nginx access
tail -f /workspace/mrd/logs/nginx_access.log

# Nginx errors
tail -f /workspace/mrd/logs/nginx_error.log

# Gunicorn
tail -f /workspace/mrd/logs/gunicorn_error.log

# Supervisor
tail -f /workspace/mrd/logs/supervisor_error.log
```

---

## 10. KOMENDY ZARZĄDZANIA

### **Restart aplikacji:**
```bash
sudo supervisorctl restart mordzix
```

### **Stop aplikacji:**
```bash
sudo supervisorctl stop mordzix
```

### **Status:**
```bash
sudo supervisorctl status
```

### **Reload Nginx (po zmianach w config):**
```bash
sudo nginx -t && sudo systemctl reload nginx
```

### **Restart Nginx:**
```bash
sudo systemctl restart nginx
```

### **Odnów SSL (manual):**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## 11. TROUBLESHOOTING

### **Problem: Aplikacja nie startuje**
```bash
# Sprawdź logi
sudo supervisorctl tail -f mordzix stderr

# Sprawdź czy port 8080 wolny
sudo lsof -i :8080

# Ręcznie uruchom i zobacz błędy
cd /workspace/mrd
source .venv/bin/activate
python app.py
```

### **Problem: Nginx 502 Bad Gateway**
```bash
# Sprawdź czy Gunicorn działa
sudo supervisorctl status mordzix

# Sprawdź logi Nginx
tail -f /workspace/mrd/logs/nginx_error.log

# Restart obu
sudo supervisorctl restart mordzix
sudo systemctl restart nginx
```

### **Problem: SSL nie działa**
```bash
# Sprawdź certyfikat
sudo certbot certificates

# Odnów manual
sudo certbot renew --force-renewal

# Restart Nginx
sudo systemctl restart nginx
```

### **Problem: Brak dostępu przez HTTP**
```bash
# Sprawdź firewall (OVH)
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# Sprawdź czy Nginx słucha
sudo netstat -tulpn | grep nginx
```

---

## 12. CHECKLIST PRZED URUCHOMIENIEM

- [ ] Python 3.11+ zainstalowany
- [ ] Nginx zainstalowany i działa
- [ ] Certbot SSL skonfigurowany
- [ ] Pliki projektu w `/workspace/mrd/`
- [ ] Virtual environment utworzony
- [ ] Wszystkie pakiety zainstalowane (`pip install -r requirements.txt`)
- [ ] Baza danych `mem.db` utworzona z tabelami
- [ ] Plik `.env` skonfigurowany (KLUCZE API!)
- [ ] Nginx config w `/etc/nginx/sites-available/mordzix`
- [ ] Supervisor config w `/etc/supervisor/conf.d/mordzix.conf`
- [ ] Aplikacja uruchomiona przez Supervisor
- [ ] Test: `curl http://localhost:8080/health` zwraca 200
- [ ] Test: `https://mordxixai.xyz/` otwiera się w przeglądarce

---

## 13. ADRESY KOŃCOWE

Po zakończeniu deployu, dostępne są:

```
🌐 GŁÓWNY:     https://mordxixai.xyz/
📱 UI:         https://mordxixai.xyz/chat_pro_clean.html
📚 API DOCS:   https://mordxixai.xyz/docs
📊 HEALTH:     https://mordxixai.xyz/health
📈 METRICS:    https://mordxixai.xyz/metrics
🔍 ENDPOINTS:  https://mordxixai.xyz/api/endpoints/list
```

---

## 14. SZYBKI ONE-LINER (całość)

Jeśli masz już wszystkie pliki na serwerze, uruchom skrypt `start_production.sh`:

```bash
cd /workspace/mrd
chmod +x start_production.sh
sudo ./start_production.sh
```

**To zrobi WSZYSTKO automatycznie!** ✨

---

# ✅ GOTOWE! TWOJA APLIKACJA DZIAŁA NA HTTPS! 🚀
