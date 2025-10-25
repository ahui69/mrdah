#!/bin/bash
################################################################################
# MORDZIX AI - COMPLETE DEPLOYMENT (LINUX OVH)
# Pełny deploy Angular + Backend na Ubuntu 24.04 LTS
################################################################################

set -e

echo ""
echo "═══════════════════════════════════════════════════════════"
echo " MORDZIX AI - COMPLETE DEPLOYMENT"
echo " Ubuntu 24.04 LTS + Angular 17 + FastAPI + Python 3.12"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Kolory
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORKSPACE="/workspace/mrd"

# Sprawdź czy jesteśmy na Linuxie
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}✗ BŁĄD: Ten skrypt działa TYLKO na Linuxie!${NC}"
    exit 1
fi

# Sprawdź czy jesteśmy root lub mamy sudo
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo -e "${RED}✗ BŁĄD: Potrzebne uprawnienia sudo!${NC}"
    exit 1
fi

echo -e "${GREEN}[1/8] Aktualizacja systemu...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

echo -e "${GREEN}[2/8] Instalacja Node.js 18 LTS...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
echo "  Node.js: $(node --version)"
echo "  npm: $(npm --version)"

echo -e "${GREEN}[3/8] Instalacja Python 3.12 + narzędzia...${NC}"
sudo apt-get install -y python3 python3-venv python3-dev python3-pip python3-full
echo "  Python: $(python3 --version)"

echo -e "${GREEN}[4/8] Tworzenie workspace...${NC}"
sudo mkdir -p "$WORKSPACE"
sudo chown -R $USER:$USER "$WORKSPACE"
cd "$WORKSPACE"

echo -e "${GREEN}[5/8] Build Angular frontend...${NC}"
cd "$WORKSPACE/frontend"

if [ ! -d "node_modules" ]; then
    echo "  Instalacja npm packages..."
    npm install
fi

echo "  Building production..."
npm run build:prod

if [ ! -f "dist/mordzix-ai/index.html" ]; then
    echo -e "${RED}✗ BŁĄD: Build nie utworzył dist/mordzix-ai/index.html${NC}"
    exit 1
fi

BUILD_SIZE=$(du -sh dist/mordzix-ai | cut -f1)
echo -e "${GREEN}  ✓ Build success! Size: $BUILD_SIZE${NC}"

echo -e "${GREEN}[6/8] Instalacja backend dependencies...${NC}"
cd "$WORKSPACE"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo -e "${GREEN}[7/8] Inicjalizacja bazy danych...${NC}"
if [ ! -f "mem.db" ]; then
    python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('mem.db')
c = conn.cursor()

# STM
c.execute('''CREATE TABLE IF NOT EXISTS stm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    user_id TEXT,
    role TEXT,
    content TEXT,
    timestamp REAL
)''')
c.execute('CREATE INDEX IF NOT EXISTS idx_stm_session ON stm(session_id)')
c.execute('CREATE INDEX IF NOT EXISTS idx_stm_user ON stm(user_id)')

# LTM
c.execute('''CREATE TABLE IF NOT EXISTS ltm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT UNIQUE,
    confidence REAL,
    embedding BLOB,
    created_at REAL,
    updated_at REAL
)''')
c.execute('CREATE INDEX IF NOT EXISTS idx_ltm_conf ON ltm(confidence)')

# Psyche
c.execute('''CREATE TABLE IF NOT EXISTS psyche_state (
    id INTEGER PRIMARY KEY,
    mood REAL,
    energy REAL,
    focus REAL,
    updated_at REAL
)''')

# Episodes
c.execute('''CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    summary TEXT,
    embedding BLOB,
    timestamp REAL
)''')

# Procedures
c.execute('''CREATE TABLE IF NOT EXISTS procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    steps TEXT,
    success_count INTEGER DEFAULT 0,
    created_at REAL
)''')

# Mental Models
c.execute('''CREATE TABLE IF NOT EXISTS mental_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept TEXT UNIQUE,
    relations TEXT,
    strength REAL,
    created_at REAL
)''')

conn.commit()
conn.close()
print("✓ Database initialized")
EOF
fi

echo -e "${GREEN}[8/8] Uruchamianie start_production.sh...${NC}"
if [ -f "start_production.sh" ]; then
    chmod +x start_production.sh
    sudo ./start_production.sh
else
    echo -e "${YELLOW}  start_production.sh nie znaleziony, uruchamianie ręcznie...${NC}"
    
    # Manual start
    source .venv/bin/activate
    nohup .venv/bin/python app.py > app.log 2>&1 &
    echo $! > app.pid
    
    echo -e "${GREEN}  ✓ Backend uruchomiony (PID: $(cat app.pid))${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN} ✓ DEPLOYMENT ZAKOŃCZONY!${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo -e "${YELLOW}Aplikacja dostępna na:${NC}"
echo "  https://mordxixai.xyz/"
echo "  https://mordxixai.xyz/docs"
echo ""
echo -e "${YELLOW}Sprawdź status:${NC}"
echo "  sudo supervisorctl status mordzix"
echo ""
echo -e "${YELLOW}Logi:${NC}"
echo "  sudo supervisorctl tail -f mordzix"
echo "  tail -f $WORKSPACE/logs/nginx_error.log"
echo ""
