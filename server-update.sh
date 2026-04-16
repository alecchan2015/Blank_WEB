#!/bin/bash
# ================================================================
# Brand Consultant — Server Update Script
# Run this on the Tencent Cloud server to sync with GitHub main.
#
# First-time setup:
#   bash server-update.sh init
#
# Subsequent updates (after git push from local):
#   bash server-update.sh
# ================================================================

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="docker compose"
command -v docker-compose >/dev/null 2>&1 && COMPOSE="docker-compose"

echo -e "${GREEN}=== Brand Consultant — Server Update ===${NC}"
echo "Dir : $REPO_DIR"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"

cd "$REPO_DIR"

# ── Init mode: first-time setup ──────────────────────────────────
if [ "$1" = "init" ]; then
    echo -e "${YELLOW}>>> Init: creating data dirs${NC}"
    mkdir -p data/uploads

    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}>>> Generating .env${NC}"
        SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
        cat > .env <<EOF
SECRET_KEY=$SECRET
PPT_PROVIDER=local
PPT_FALLBACK=local
EOF
        echo -e "${GREEN}.env created with random SECRET_KEY${NC}"
    else
        echo ".env already exists — skipping"
    fi

    echo -e "${YELLOW}>>> Building & starting containers${NC}"
    $COMPOSE -f docker-compose.server.yml up -d --build

    echo -e "${GREEN}=== Init complete ===${NC}"
    echo "Frontend : http://$(curl -s ifconfig.me 2>/dev/null || echo '<server-ip>'):8090"
    echo "API docs : http://$(curl -s ifconfig.me 2>/dev/null || echo '<server-ip>'):8001/docs"
    echo "Admin    : admin / Admin@123  ← change this immediately"
    exit 0
fi

# ── Update mode: pull + rebuild changed images ───────────────────
echo -e "${YELLOW}>>> Pulling latest code from GitHub${NC}"
git pull origin main

echo -e "${YELLOW}>>> Rebuilding & restarting containers (zero-downtime)${NC}"
$COMPOSE -f docker-compose.server.yml up -d --build

echo -e "${YELLOW}>>> Removing dangling images${NC}"
docker image prune -f

echo -e "${GREEN}=== Update complete ===${NC}"
$COMPOSE -f docker-compose.server.yml ps
