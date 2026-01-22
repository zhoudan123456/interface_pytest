import yaml
import os
from typing import Any


class Config:
    """配置管理器，支持yaml和环境变量"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """加载配置文件"""
        self.config = {}
        # 1. 加载yaml配置
        config_files = ['config.yaml', 'config.local.yaml']
        for file in config_files:
            if os.path.exists(file):
                with open(file, 'r', encoding='utf-8') as f:
                    self.config.update(yaml.safe_load(f) or {})

        # 2. 加载环境变量（覆盖yaml配置）
        for key, value in os.environ.items():
            if key.startswith('TEST_'):
                self.config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点符号访问"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default