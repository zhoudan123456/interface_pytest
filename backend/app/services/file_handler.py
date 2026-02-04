"""
文件处理服务
"""
import os
import uuid
import json
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings


class FileHandlerService:
    """文件处理服务"""

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.metadata_dir = self.upload_dir / "_metadata"
        self.metadata_dir.mkdir(exist_ok=True)

    async def save_upload_file(
        self,
        file: UploadFile,
        file_type: str = "unknown"
    ) -> dict:
        """保存上传的文件

        Args:
            file: 上传的文件
            file_type: 文件类型标识

        Returns:
            文件信息字典
        """
        # 验证文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。允许的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        save_filename = f"{file_id}{file_ext}"
        file_path = self.upload_dir / save_filename

        # 保存文件
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"文件保存失败: {str(e)}"
            )

        # 获取文件大小
        file_size = file_path.stat().st_size

        # 保存元数据
        metadata = {
            "file_id": file_id,
            "original_filename": file.filename,
            "size": file_size,
            "file_type": file_type
        }
        metadata_path = self.metadata_dir / f"{file_id}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": file_size,
            "path": str(file_path)
        }

    def get_file_path(self, file_id: str) -> Optional[Path]:
        """根据文件ID获取文件路径

        Args:
            file_id: 文件ID

        Returns:
            文件路径，如果不存在返回None
        """
        # 搜索上传目录中的文件
        for file_path in self.upload_dir.glob(f"{file_id}.*"):
            if file_path.is_file() and not file_path.name.startswith('_'):
                return file_path
        return None

    def get_file_by_id(self, file_id: str) -> Optional[dict]:
        """根据文件ID获取文件信息

        Args:
            file_id: 文件ID

        Returns:
            文件信息字典，如果不存在返回None
        """
        # 先读取元数据
        metadata_path = self.metadata_dir / f"{file_id}.json"
        original_filename = None

        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    original_filename = metadata.get('original_filename')
            except Exception:
                pass

        # 搜索上传目录中的文件
        for file_path in self.upload_dir.glob(f"{file_id}.*"):
            if file_path.is_file() and not file_path.name.startswith('_'):
                return {
                    "file_id": file_id,
                    "filename": original_filename or file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size
                }
        return None

    def delete_file(self, file_path: str) -> bool:
        """删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功删除
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                # 同时删除元数据
                file_id = path.stem
                metadata_path = self.metadata_dir / f"{file_id}.json"
                if metadata_path.exists():
                    metadata_path.unlink()
                return True
            return False
        except Exception:
            return False
