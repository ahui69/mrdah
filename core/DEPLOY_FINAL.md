# 🚀 MORDZIX AI - DEPLOYMENT GUIDE (LINUX ONLY!)

## ⚠️ WAŻNE: TO JEST APLIKACJA LINUXOWA!

**NIE MA ŻADNEGO WINDOWSA!** Wszystko działa na serwerze Linux OVH.

---

## 📋 WYMAGANIA

- **Serwer**: Ubuntu 24.04 LTS (OVH VPS)
- **IP**: 162.19.220.29
- **Domena**: mordxixai.xyz
- **SSH Key**: `~/.ssh/id_ed25519_ovh`
- **User**: ubuntu

---

## 🎯 SZYBKI START (3 KROKI)

### 1️⃣ Upload plików (z Windows - tylko raz!)

```powershell
# Utwórz workspace
ssh -i C:\Users\48501\.ssh\id_ed25519_ovh ubuntu@162.19.220.29 "sudo mkdir -p /workspace/mrd && sudo chown -R ubuntu:ubuntu /workspace"

# Prześlij pliki
scp -i C:\Users\48501\.ssh\id_ed25519_ovh -r C:\Users\48501\Desktop\mrd\* ubuntu@162.19.220.29:/workspace/mrd/
```

### 2️⃣ SSH do serwera

```bash
ssh -i ~/.ssh/id_ed25519_ovh ubuntu@162.19.220.29
```

### 3️⃣ Uruchom deployment (na serwerze Linux)

```bash
cd /workspace/mrd
chmod +x deploy_complete.sh
./deploy_complete.sh
```

**GOTOWE!** Aplikacja dostępna: **https://mordxixai.xyz/**

---

## 📁 CO ZOSTAŁO WDROŻONE

```
/workspace/mrd/
├── frontend/               # Angular 17 SPA
│   ├── src/               # Kod źródłowy
│   ├── dist/mordzix-ai/   # Build produkcyjny
│   └── package.json       # Node.js dependencies
├── core/                  # Backend logic
│   ├── config.py
│   ├── llm.py
│   ├── memory.py
│   └── ...
├── app.py                 # FastAPI application
├── start_production.sh    # Automatyczny deployment
├── update_frontend.sh     # Update tylko frontendu
├── deploy_complete.sh     # Pełny deploy (wszystko)
├── mem.db                 # SQLite database
├── .env                   # Environment variables
└── requirements.txt       # Python dependencies
```

---

## 🔧 KOMENDY ZARZĄDZANIA

### Status aplikacji
```bash
sudo supervisorctl status mordzix
```

### Restart aplikacji
```bash
sudo supervisorctl restart mordzix
```

### Logi
```bash
# Backend
sudo supervisorctl tail -f mordzix

# Nginx
tail -f /workspace/mrd/logs/nginx_access.log
tail -f /workspace/mrd/logs/nginx_error.log

# Gunicorn
tail -f /workspace/mrd/logs/gunicorn_error.log
```

### Update frontendu
```bash
cd /workspace/mrd
./update_frontend.sh
```

### Pełny restart (backend + frontend)
```bash
cd /workspace/mrd
./deploy_complete.sh
```

---

## 🌐 DOSTĘPNE ENDPOINTY

Po deploy aplikacja dostępna:

- **Frontend**: https://mordxixai.xyz/
- **API Docs**: https://mordxixai.xyz/docs
- **Health**: https://mordxixai.xyz/health
- **Chat API**: https://mordxixai.xyz/api/chat/assistant

---

## 🛠️ ARCHITEKTURA

```
Browser → Nginx (443) → Gunicorn (8080) → FastAPI
                                            ├── Angular SPA (frontend/dist/)
                                            ├── API Endpoints (14 routers)
                                            └── SQLite (mem.db)
```

### Stack technologiczny:
- **Frontend**: Angular 17, TypeScript, SCSS
- **Backend**: Python 3.12, FastAPI, Gunicorn
- **Database**: SQLite (mem.db)
- **LLM**: DeepInfra (GLM-4.5)
- **Web Server**: Nginx + Let's Encrypt SSL
- **Process Manager**: Supervisor
- **OS**: Ubuntu 24.04 LTS

---

## 📊 WERYFIKACJA PO DEPLOY

```bash
# 1. Health check
curl https://mordxixai.xyz/health
# Oczekiwane: {"status":"healthy"}

# 2. Frontend
curl -I https://mordxixai.xyz/
# Oczekiwane: HTTP/1.1 200 OK

# 3. API
curl https://mordxixai.xyz/api
# Oczekiwane: {"message":"Mordzix AI API v5.0.0"}

# 4. Test chatu
curl -X POST https://mordxixai.xyz/api/chat/assistant \
  -H "Authorization: Bearer ssjjMijaja6969" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"user_id":"test","use_memory":false}'
# Oczekiwane: {"response":"..."}
```

---

## 🔄 UPDATE WORKFLOW

### Tylko frontend (Angular):
```bash
ssh -i ~/.ssh/id_ed25519_ovh ubuntu@162.19.220.29
cd /workspace/mrd
./update_frontend.sh
```

### Tylko backend (Python):
```bash
ssh -i ~/.ssh/id_ed25519_ovh ubuntu@162.19.220.29
cd /workspace/mrd
source .venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart mordzix
```

### Wszystko (full redeploy):
```bash
ssh -i ~/.ssh/id_ed25519_ovh ubuntu@162.19.220.29
cd /workspace/mrd
./deploy_complete.sh
```

---

## 🚨 TROUBLESHOOTING

### Problem: Frontend nie ładuje się

```bash
# Sprawdź czy dist/ istnieje
ls -la /workspace/mrd/frontend/dist/mordzix-ai/

# Rebuild
cd /workspace/mrd/frontend
npm run build:prod

# Restart
sudo supervisorctl restart mordzix
```

### Problem: Backend offline

```bash
# Status
sudo supervisorctl status mordzix

# Logi
sudo supervisorctl tail mordzix

# Restart
sudo supervisorctl restart mordzix
```

### Problem: Nginx error

```bash
# Test config
sudo nginx -t

# Sprawdź logi
tail -f /workspace/mrd/logs/nginx_error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Problem: Brak Node.js

```bash
# Zainstaluj Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Sprawdź
node --version
npm --version
```

---

## 📚 DOKUMENTACJA

- **DEPLOY_LINUX_ONLY.md** - Szczegółowa instrukcja deployment
- **ANGULAR_QUICK_START.md** - Quick reference dla frontendu
- **frontend/README.md** - Dokumentacja Angular app
- **DEPLOY_ANGULAR.md** - Pełny guide Angular (deprec - użyj DEPLOY_LINUX_ONLY.md)

---

## 🔐 CREDENTIALS

**Auth Token**: `ssjjMijaja6969` (w `.env` i frontendzie)

**SSH**: 
- Key: `~/.ssh/id_ed25519_ovh`
- User: `ubuntu`
- Host: `162.19.220.29` (mordxixai.xyz)

**Email**: gajewa2014@gmail.com

---

## ✅ CHECKLIST DEPLOY

- [ ] Ubuntu 24.04 LTS zainstalowany
- [ ] SSH key dodany w OVH panel
- [ ] Pliki przesłane na serwer (`scp`)
- [ ] Node.js 18+ zainstalowany
- [ ] Python 3.12 zainstalowany
- [ ] Frontend zbudowany (`npm run build:prod`)
- [ ] Backend uruchomiony (`./start_production.sh`)
- [ ] Nginx skonfigurowany + SSL
- [ ] Supervisor aktywny
- [ ] Domena wskazuje na IP serwera
- [ ] Health check działa (`curl https://mordxixai.xyz/health`)
- [ ] Frontend ładuje się w przeglądarce

---

## 🎯 QUICK COMMANDS

```bash
# SSH
ssh -i ~/.ssh/id_ed25519_ovh ubuntu@162.19.220.29

# Status
sudo supervisorctl status

# Restart
sudo supervisorctl restart mordzix

# Logi
sudo supervisorctl tail -f mordzix

# Update frontend
cd /workspace/mrd && ./update_frontend.sh

# Full redeploy
cd /workspace/mrd && ./deploy_complete.sh
```

---

**TYLKO LINUX! NIE MA WINDOWSA!** 🐧
