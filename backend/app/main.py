"""
FastAPI主应用入口
"""
from dotenv import load_dotenv
from pathlib import Path

# 加载.env文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.v1 import upload, tasks, reports, websocket, batch, batch_ws

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router, prefix=settings.API_V1_PREFIX, tags=["upload"])
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX, tags=["tasks"])
app.include_router(reports.router, prefix=settings.API_V1_PREFIX + "/reports", tags=["reports"])
app.include_router(websocket.router, prefix=settings.API_V1_PREFIX, tags=["websocket"])
app.include_router(batch.router, prefix=settings.API_V1_PREFIX, tags=["batch"])

# 注册批量任务WebSocket路由
app.add_websocket_route(
    f"{settings.API_V1_PREFIX}/batch/ws/{{task_id}}",
    batch_ws.batch_websocket_endpoint
)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "招标文件检查点验证工具 API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器错误: {str(exc)}",
            "data": None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
