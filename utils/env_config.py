"""
环境变量配置管理
"""
import os
from pathlib import Path
from typing import Optional

# 尝试导入 python-dotenv（如果没有安装，提供回退方案）
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


class EnvConfig:
    """环境变量配置类"""

    def __init__(self, env_file: str = '.env'):
        """
        初始化环境配置

        Args:
            env_file: .env 文件路径
        """
        self.env_file = Path(env_file)
        self._load_env()

    def _load_env(self):
        """加载环境变量"""
        if HAS_DOTENV:
            # 使用 python-dotenv 加载
            load_dotenv(self.env_file)
        else:
            # 回退方案：手动解析 .env 文件
            self._load_env_manually()

    def _load_env_manually(self):
        """手动解析 .env 文件"""
        if not self.env_file.exists():
            return

        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                # 解析 KEY=VALUE 格式
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取环境变量

        Args:
            key: 环境变量名
            default: 默认值

        Returns:
            环境变量值
        """
        return os.environ.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数类型的环境变量"""
        value = self.get(key)
        if value:
            try:
                return int(value)
            except ValueError:
                return default
        return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔类型的环境变量"""
        value = self.get(key)
        if value:
            return value.lower() in ('true', '1', 'yes', 'on')
        return default


# 创建全局配置实例
env_config = EnvConfig()


# 便捷函数
def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """获取环境变量"""
    return env_config.get(key, default)


def get_env_int(key: str, default: int = 0) -> int:
    """获取整数类型的环境变量"""
    return env_config.get_int(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """获取布尔类型的环境变量"""
    return env_config.get_bool(key, default)
