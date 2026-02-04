"""
Celery应用配置
"""
from celery import Celery
from app.config import settings

# 创建Celery应用
celery_app = Celery(
    "bid_check_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.llm_tasks"]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.TASK_TIMEOUT,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)
