"""
文件上传相关模型
"""
from pydantic import BaseModel
from typing import Optional


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    code: int
    message: str
    data: Optional["FileInfo"] = None


class FileInfo(BaseModel):
    """文件信息"""
    file_id: str
    filename: str
    size: int
    path: str
