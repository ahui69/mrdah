set -e

echo "═══════════════════════════════════════════════════════════════"
echo "MORDZIX AI - Production Deployment Script"
echo "═══════════════════════════════════════════════════════════════"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}✗ Do not run this script as root${NC}"
   exit 1
fi

echo -e "${YELLOW}[1/8] Updating code from git...${NC}"
git pull origin main

echo -e "${YELLOW}[2/8] Checking .env file...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found! Copy .env.example to .env and configure it.${NC}"
    exit 1
fi

echo -e "${YELLOW}[3/8] Installing system dependencies...${NC}"
sudo apt-get update
sudo apt-get install -y docker.io docker-compose python3-pip nginx

echo -e "${YELLOW}[4/8] Stopping old services...${NC}"
docker-compose down || true
sudo systemctl stop mordzix || true

echo -e "${YELLOW}[5/8] Building Docker images...${NC}"
docker-compose build --no-cache

echo -e "${YELLOW}[6/8] Starting services...${NC}"
docker-compose up -d

echo -e "${YELLOW}[7/8] Waiting for services to be healthy...${NC}"
sleep 10

echo -e "${YELLOW}[8/8] Running sanity checks...${NC}"
# Health check
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend health check passed${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    docker-compose logs backend
    exit 1
fi

# API check
if curl -f http://localhost:8080/api > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API endpoint check passed${NC}"
else
    echo -e "${RED}✗ API endpoint check failed${NC}"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ DEPLOYMENT SUCCESSFUL\exit{NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Services running:"
docker-compose ps
echo ""
echo "Logs: docker-compose logs -f"
echo "Stop: docker-compose down"
echo "Restart: docker-compose restart"
echo ""
