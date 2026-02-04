"""
FastAPI应用配置
"""
import os
from pathlib import Path
from typing import Optional

# 加载.env文件（在读取环境变量之前）
from dotenv import load_dotenv
# 项目根目录的.env文件（从 backend/app/config.py 向上三级）
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
# 项目根目录（interface_pytest）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# API配置
API_V1_PREFIX = "/api/v1"

# 项目信息
PROJECT_NAME = "招标文件检查点验证工具"
VERSION = "1.0.0"
DESCRIPTION = "基于智谱AI的智能验证系统"

# CORS配置
CORS_ORIGINS = [
    "http://localhost:5173",  # Vue开发服务器
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:3000",
]

# 文件上传配置
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".xlsx", ".json", ".pdf", ".docx"}

# Redis配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery配置
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# 智谱AI配置
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
ZHIPUAI_MODEL = "glm-4-flash"

# 任务配置
TASK_TIMEOUT = 3600  # 1小时
TASK_MAX_RETRIES = 3
TASK_RETRY_DELAY = 60  # 秒

# 确保目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# 创建settings类供导入使用
class Settings:
    """应用配置类"""
    PROJECT_NAME = PROJECT_NAME
    VERSION = VERSION
    DESCRIPTION = DESCRIPTION
    API_V1_PREFIX = API_V1_PREFIX
    CORS_ORIGINS = CORS_ORIGINS
    BASE_DIR = BASE_DIR
    PROJECT_ROOT = PROJECT_ROOT
    UPLOAD_DIR = UPLOAD_DIR
    OUTPUT_DIR = OUTPUT_DIR
    MAX_FILE_SIZE = MAX_FILE_SIZE
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    ZHIPUAI_API_KEY = ZHIPUAI_API_KEY
    REDIS_URL = REDIS_URL
    CELERY_BROKER_URL = CELERY_BROKER_URL
    CELERY_RESULT_BACKEND = CELERY_RESULT_BACKEND
    TASK_TIMEOUT = TASK_TIMEOUT
    TASK_MAX_RETRIES = TASK_MAX_RETRIES
    TASK_RETRY_DELAY = TASK_RETRY_DELAY


settings = Settings()
