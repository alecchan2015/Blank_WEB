#!/bin/bash
# ================================================================
# Blank_WEB - CentOS Deployment Script
# Usage: bash deploy.sh [dev|prod]
# ================================================================

set -e
MODE=${1:-dev}
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${GREEN}=== Blank_WEB 部署脚本 ===${NC}"
echo -e "模式: ${YELLOW}${MODE}${NC}"

# --- Check prerequisites ---
check_cmd() { command -v "$1" >/dev/null 2>&1 || { echo -e "${RED}缺少依赖: $1${NC}"; exit 1; }; }

if [ "$MODE" = "prod" ]; then
    check_cmd docker
    check_cmd docker-compose 2>/dev/null || check_cmd "docker compose"
    echo -e "${GREEN}>>> 生产模式: 使用 Docker Compose${NC}"
    mkdir -p uploads
    docker-compose up -d --build
    echo -e "${GREEN}=== 部署完成 ===${NC}"
    echo "前台地址: http://localhost:80"
    echo "API地址:  http://localhost:8000"
    echo "默认管理员: admin / Admin@123"
    exit 0
fi

# --- Dev mode ---
echo -e "${GREEN}>>> 开发模式${NC}"

# Check Python
check_cmd python3
PY=$(python3 --version)
echo "Python: $PY"

# Check Node
check_cmd node
NODE=$(node --version)
echo "Node: $NODE"

# Install system deps on CentOS
if command -v yum >/dev/null 2>&1; then
    echo -e "${YELLOW}检测到 CentOS，安装系统依赖...${NC}"
    sudo yum install -y python3-pip nodejs npm gcc libjpeg-turbo-devel zlib-devel 2>/dev/null || true
    # Chinese fonts
    sudo yum install -y wqy-microhei-fonts 2>/dev/null || \
        sudo yum install -y google-noto-cjk-fonts 2>/dev/null || \
        echo "字体包安装失败，PDF中文可能显示异常"
fi

# Backend setup
echo -e "${GREEN}>>> 设置后端${NC}"
cd backend
[ ! -d ".venv" ] && python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -q
[ ! -f ".env" ] && cp .env.example .env && echo "已创建 .env，请根据需要修改"
mkdir -p uploads

# Start backend in background
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"
cd ..

# Frontend setup
echo -e "${GREEN}>>> 设置前端${NC}"
cd frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"
cd ..

echo ""
echo -e "${GREEN}=== 启动完成 ===${NC}"
echo "前台地址: http://localhost:3000"
echo "API地址:  http://localhost:8000"
echo "API文档:  http://localhost:8000/docs"
echo "默认管理员: admin / Admin@123"
echo ""
echo "停止服务: kill $BACKEND_PID $FRONTEND_PID"

wait
