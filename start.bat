@echo off
echo ========================================
echo 招标文件检查点验证工具 - Web版
echo ========================================
echo.

REM 检查环境变量
if not exist .env (
    echo [错误] 未找到.env文件
    echo 请先复制 .env.example 为 .env 并配置API密钥
    pause
    exit /b 1
)

echo [1/4] 启动 Redis...
start cmd /k "redis-server"

echo [2/4] 等待 Redis 启动...
timeout /t 3 /nobreak > nul

echo [3/4] 启动 FastAPI 后端...
start cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [4/4] 等待后端启动...
timeout /t 5 /nobreak > nul

echo [完成] 启动前端开发服务器...
cd frontend
start cmd /k "npm run dev"

echo.
echo ========================================
echo 服务已启动！
echo 前端: http://localhost:5173
echo 后端: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo ========================================
echo.
echo 按任意键关闭此窗口...
pause > nul
