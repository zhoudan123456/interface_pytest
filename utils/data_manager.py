"""
智能数据管理器
统一管理静态配置和动态生成数据
"""
import os
import yaml
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
import copy


@dataclass
class DataSource:
    """数据源定义"""
    name: str
    path: Path
    is_static: bool
    description: str = ""
    last_modified: float = 0.0
    checksum: str = ""


class DataManager:
    """智能数据管理器"""

    # 单例模式
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_dir: str = None):
        if self._initialized:
            return

        # 设置基础目录
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent / "test_data"

        # 初始化目录
        self.static_dir = self.base_dir / "static"
        self.dynamic_dir = self.base_dir / "dynamic"
        self.template_dir = self.base_dir / "templates"

        # 确保目录存在
        for directory in [self.static_dir, self.dynamic_dir, self.template_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # 数据缓存
        self._cache = {}
        self._data_sources = {}
        self._session_data = {}

        # 加载所有数据源
        self._discover_data_sources()

        self._initialized = True

    def _discover_data_sources(self):
        """发现所有数据源"""
        # 静态数据源
        for file_path in self.static_dir.glob("**/*.yaml"):
            rel_path = file_path.relative_to(self.base_dir)
            source = DataSource(
                name=f"static_{file_path.stem}",
                path=file_path,
                is_static=True,
                last_modified=file_path.stat().st_mtime
            )
            self._data_sources[source.name] = source

        # 动态数据源
        for file_path in self.dynamic_dir.glob("**/*.yaml"):
            rel_path = file_path.relative_to(self.base_dir)
            source = DataSource(
                name=f"dynamic_{file_path.stem}",
                path=file_path,
                is_static=False,
                last_modified=file_path.stat().st_mtime
            )
            self._data_sources[source.name] = source

    def get_static(self, key: str, default: Any = None) -> Any:
        """
        获取静态配置数据
        支持点符号访问，如 'api.login.url'
        """
        return self._get_data("static", key, default)

    def get_dynamic(self, key: str, default: Any = None) -> Any:
        """获取动态数据"""
        return self._get_data("dynamic", key, default)

    def get_session(self, key: str, default: Any = None) -> Any:
        """获取会话数据（内存中）"""
        return self._session_data.get(key, default)

    def _get_data(self, data_type: str, key: str, default: Any) -> Any:
        """内部数据获取方法"""
        if '.' in key:
            # 点符号访问，如 'api.login.url'
            parts = key.split('.')
            filename = f"{data_type}_{parts[0]}.yaml"
            data_key = '.'.join(parts[1:])
        else:
            filename = f"{data_type}_{key}.yaml"
            data_key = None

        # 构建文件路径
        if data_type == "static":
            file_path = self.static_dir / filename
        else:
            file_path = self.dynamic_dir / filename

        # 检查缓存
        cache_key = str(file_path)
        if cache_key in self._cache:
            data = self._cache[cache_key]
        else:
            # 从文件加载
            data = self._load_yaml_file(file_path)
            self._cache[cache_key] = data

        # 根据key提取数据
        if data_key:
            return self._extract_nested_value(data, data_key, default)
        else:
            return data if data is not None else default

    def _load_yaml_file(self, file_path: Path) -> Optional[Dict]:
        """加载YAML文件"""
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # 处理变量替换
                content = self._replace_variables(content)

                data = yaml.safe_load(content)
                return data if data is not None else {}
        except Exception as e:
            print(f"❌ 加载YAML文件失败 {file_path}: {e}")
            return None

    def _replace_variables(self, content: str) -> str:
        """替换内容中的变量"""
        import re

        def replace_match(match):
            var_name = match.group(1)

            # 1. 尝试从环境变量获取
            env_value = os.getenv(var_name)
            if env_value:
                return env_value

            # 2. 尝试从会话数据获取
            session_value = self.get_session(var_name)
            if session_value:
                return str(session_value)

            # 3. 返回原始占位符
            return match.group(0)

        # 替换 ${VAR} 格式的变量
        return re.sub(r'\$\{(\w+)\}', replace_match, content)

    def _extract_nested_value(self, data: Dict, path: str, default: Any) -> Any:
        """从嵌套字典中提取值"""
        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def set_dynamic(self, key: str, value: Any, persist: bool = True):
        """
        设置动态数据

        Args:
            key: 数据键，可以是点符号
            value: 数据值
            persist: 是否持久化到文件
        """
        # 更新会话数据
        self._session_data[key] = value

        if persist:
            # 持久化到文件
            if '.' in key:
                # 对于点符号，需要更新嵌套结构
                filename = f"dynamic_session.yaml"
                file_path = self.dynamic_dir / filename

                # 加载现有数据
                existing_data = self._load_yaml_file(file_path) or {}

                # 更新嵌套值
                self._set_nested_value(existing_data, key, value)

                # 保存
                self._save_yaml_file(file_path, existing_data)
            else:
                # 简单键，直接保存到对应文件
                filename = f"dynamic_{key}.yaml"
                file_path = self.dynamic_dir / filename
                self._save_yaml_file(file_path, {key: value})

    def _set_nested_value(self, data: Dict, path: str, value: Any):
        """设置嵌套字典的值"""
        keys = path.split('.')
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _save_yaml_file(self, file_path: Path, data: Dict):
        """保存数据到YAML文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

            # 更新缓存
            self._cache[str(file_path)] = data

        except Exception as e:
            print(f"❌ 保存YAML文件失败 {file_path}: {e}")

    def save_from_response(self, response_data: Dict, mapping: Dict[str, str]):
        """
        从API响应保存数据

        Args:
            response_data: API响应数据
            mapping: 字段映射，如 {'document_id': 'data.id'}
        """
        for target_key, source_path in mapping.items():
            value = self._extract_from_response(response_data, source_path)
            if value is not None:
                self.set_dynamic(target_key, value)
                print(f"💾 保存动态数据: {target_key} = {value}")

    def _extract_from_response(self, data: Dict, path: str) -> Any:
        """从响应数据中提取值"""
        # 支持JSONPath语法简版
        if path.startswith('$.'):
            # JSONPath格式，如 '$.data.id'
            keys = path[2:].split('.')
        else:
            keys = path.split('.')

        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def clear_dynamic_data(self, pattern: str = None):
        """清除动态数据"""
        if pattern:
            # 清除特定模式的动态数据
            for key in list(self._session_data.keys()):
                if pattern in key:
                    del self._session_data[key]
        else:
            # 清除所有动态数据
            self._session_data.clear()

            # 删除动态数据文件
            for file_path in self.dynamic_dir.glob("*.yaml"):
                try:
                    file_path.unlink()
                except:
                    pass

        # 清除缓存
        self._cache.clear()

    def create_test_data(self, template_name: str, **kwargs) -> Dict:
        """基于模板创建测试数据"""
        template_file = self.template_dir / f"{template_name}.yaml"

        if not template_file.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_file}")

        # 加载模板
        with open(template_file, 'r', encoding='utf-8') as f:
            template = yaml.safe_load(f)

        # 深拷贝模板
        data = copy.deepcopy(template)

        # 应用参数
        def apply_params(obj, params):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                        param_name = value[2:-2].strip()
                        if param_name in params:
                            obj[key] = params[param_name]
                    else:
                        apply_params(value, params)
            elif isinstance(obj, list):
                for item in obj:
                    apply_params(item, params)

        apply_params(data, kwargs)

        # 注入动态变量
        data_str = yaml.dump(data, default_flow_style=False)
        data_str = self._replace_variables(data_str)

        return yaml.safe_load(data_str)

    def get_data_summary(self) -> Dict:
        """获取数据摘要"""
        return {
            "static_sources": len([s for s in self._data_sources.values() if s.is_static]),
            "dynamic_files": len(list(self.dynamic_dir.glob("*.yaml"))),
            "session_keys": len(self._session_data),
            "cache_entries": len(self._cache)
        }


# 全局实例
data_manager = DataManager()