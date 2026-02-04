"""
依赖注入
"""
import os
from fastapi import Header, HTTPException
from app.config import settings

async def get_api_key(x_api_key: str = Header(...)):
    """验证API密钥（可选）"""
    # 如果需要API密钥认证，取消下面的注释
    # api_key = os.getenv("API_KEY")
    # if x_api_key != api_key:
    #     raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key
