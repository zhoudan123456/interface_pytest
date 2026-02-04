#!/bin/bash

echo "========================================"
echo "招标文件检查点验证工具 - Web版"
echo "========================================"
echo ""

# 检查环境变量
if [ ! -f .env ]; then
    echo "[错误] 未找到.env文件"
    echo "请先复制 .env.example 为 .env 并配置API密钥"
    exit 1
fi

# 启动Redis
echo "[1/4] 启动 Redis..."
redis-server --daemonize yes

# 等待Redis启动
sleep 2

# 启动Celery Worker
echo "[2/4] 启动 Celery Worker..."
cd backend
celery -A app.tasks.celery_app worker --loglevel=info &
CELERY_PID=$!

# 启动FastAPI后端
echo "[3/4] 启动 FastAPI 后端..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "[4/4] 启动前端开发服务器..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "服务已启动！"
echo "前端: http://localhost:5173"
echo "后端: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断信号
trap "kill $CELERY_PID $API_PID $FRONTEND_PID; redis-cli shutdown; exit" SIGINT SIGTERM

wait
