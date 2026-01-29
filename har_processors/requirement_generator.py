"""
需求大纲生成器
使用Claude大模型从HAR文件中生成结构化需求
"""
import json
import os
from typing import Dict, List, Optional
from pathlib import Path

from api_clients.claude_client import ClaudeClient


class RequirementGenerator:
    """需求大纲生成器"""

    def __init__(self, claude_client: ClaudeClient = None, api_key: str = None):
        """
        初始化需求生成器
        :param claude_client: Claude客户端实例
        :param api_key: Claude API密钥
        """
        if claude_client:
            self.claude_client = claude_client
        elif api_key:
            self.claude_client = ClaudeClient(api_key)
        else:
            # 尝试从环境变量获取
            self.claude_client = ClaudeClient(os.getenv('CLAUDE_API_KEY', ''))

    def generate_requirements(self, narrative: str,
                            model: str = "claude-3-5-sonnet-20241022") -> Dict:
        """
        生成需求大纲
        :param narrative: 自然语言叙述的业务流程
        :param model: Claude模型名称
        :return: 结构化需求字典
        """
        # 读取提示词模板
        prompt = self._load_requirement_prompt()

        # 格式化提示词
        formatted_prompt = prompt.format(narrative=narrative[:8000])  # 限制长度

        # 调用Claude生成需求
        print("正在调用Claude生成需求大纲...")
        try:
            response_text = self._call_claude(formatted_prompt, model)
            requirements = self._parse_requirements_response(response_text)
            return requirements
        except Exception as e:
            print(f"生成需求失败: {str(e)}")
            return {"error": str(e), "raw_response": response_text if 'response_text' in locals() else ""}

    def _load_requirement_prompt(self) -> str:
        """加载需求生成提示词模板"""
        prompt_file = Path(__file__).parents[1] / 'config' / 'har_prompts' / 'requirement_generation.txt'
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # 默认提示词
            return """你是一个资深的业务分析师和需求工程师。请分析以下用户操作流程，生成结构化的软件需求大纲。

# 业务流程记录
{narrative}

请生成完整的软件需求规格大纲，包括以下内容：

## 1. 项目概述
- 项目背景
- 业务目标
- 项目范围

## 2. 用户角色与权限
- 主要用户角色
- 权限矩阵

## 3. 业务需求
### 3.1 核心业务流程
[按场景详细描述]

### 3.2 业务规则
[规则列表]

## 4. 功能需求
### 4.1 功能模块清单
[列出所有功能模块]

### 4.2 详细功能说明
每个功能包括：
- 功能描述
- 用户故事
- 验收标准
- 优先级

## 5. 非功能需求
- 性能需求
- 安全性需求
- 可用性需求
- 兼容性需求

## 6. 数据需求
- 数据实体
- 数据流

## 7. 接口需求
- API接口清单
- 接口说明

请使用JSON格式输出，结构如下：
{{
    "project_overview": {{
        "background": "...",
        "objectives": ["..."],
        "scope": "..."
    }},
    "user_roles": [...],
    "business_requirements": {{
        "core_processes": [...],
        "business_rules": [...]
    }},
    "functional_requirements": {{
        "modules": [
            {{
                "name": "模块名称",
                "description": "描述",
                "features": [
                    {{
                        "name": "功能名称",
                        "description": "功能描述",
                        "user_story": "作为...我想要...以便...",
                        "acceptance_criteria": ["标准1", "标准2"],
                        "priority": "High/Medium/Low"
                    }}
                ]
            }}
        ]
    }},
    "non_functional_requirements": {{
        "performance": [...],
        "security": [...],
        "usability": [...]
    }},
    "data_requirements": {{
        "entities": [...],
        "data_flow": "..."
    }},
    "api_requirements": {{
        "endpoints": [...]
    }}
}}

注意：
1. 只返回JSON格式，不要添加其他解释性文字
2. 确保JSON格式正确
3. 所有字段都要填写完整
4. 优先级使用High/Medium/Low
"""

    def _call_claude(self, prompt: str, model: str) -> str:
        """调用Claude API"""
        payload = {
            "model": model,
            "max_tokens": 6000,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }

        response = self.claude_client.session.post(
            f"{self.claude_client.base_url}/v1/messages",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result.get("content", [{}])[0].get("text", "")

    def _parse_requirements_response(self, response_text: str) -> Dict:
        """解析Claude的响应"""
        import re

        try:
            # 尝试提取JSON部分
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # 如果找不到JSON,返回原始文本
                return {"raw_text": response_text}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"raw_text": response_text, "parse_error": str(e)}

    def extract_user_stories(self, requirements: Dict) -> List[Dict]:
        """从需求中提取用户故事"""
        user_stories = []

        functional_reqs = requirements.get('functional_requirements', {})
        modules = functional_reqs.get('modules', [])

        for module in modules:
            features = module.get('features', [])
            for feature in features:
                user_stories.append({
                    'module': module.get('name', ''),
                    'feature': feature.get('name', ''),
                    'user_story': feature.get('user_story', ''),
                    'priority': feature.get('priority', 'Medium'),
                    'acceptance_criteria': feature.get('acceptance_criteria', [])
                })

        return user_stories

    def generate_test_scenarios(self, requirements: Dict) -> List[Dict]:
        """基于需求生成测试场景"""
        test_scenarios = []

        functional_reqs = requirements.get('functional_requirements', {})
        modules = functional_reqs.get('modules', [])

        for module in modules:
            features = module.get('features', [])
            for feature in features:
                # 为每个功能生成正向和负向测试场景
                test_scenarios.append({
                    'module': module.get('name'),
                    'feature': feature.get('name'),
                    'scenario': f'正常{feature.get("name")}功能',
                    'type': 'positive',
                    'steps': self._generate_test_steps(feature, 'positive')
                })

                test_scenarios.append({
                    'module': module.get('name'),
                    'feature': feature.get('name'),
                    'scenario': f'异常{feature.get("name")}功能',
                    'type': 'negative',
                    'steps': self._generate_test_steps(feature, 'negative')
                })

        return test_scenarios

    def _generate_test_steps(self, feature: Dict, scenario_type: str) -> List[str]:
        """生成测试步骤"""
        steps = []
        feature_name = feature.get('name', '该功能')

        if scenario_type == 'positive':
            steps = [
                f"1. 打开系统",
                f"2. 导航到{feature_name}页面",
                f"3. 输入有效测试数据",
                f"4. 执行{feature_name}操作",
                f"5. 验证操作成功完成",
                f"6. 检查结果符合预期"
            ]
        else:
            steps = [
                f"1. 打开系统",
                f"2. 导航到{feature_name}页面",
                f"3. 输入无效/异常测试数据",
                f"4. 尝试执行{feature_name}操作",
                f"5. 验证系统正确处理错误",
                f"6. 检查错误提示信息"
            ]

        return steps

    def export_requirements_to_markdown(self, requirements: Dict, output_path: str):
        """导出需求为Markdown文档"""
        markdown = self._convert_to_markdown(requirements)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"需求文档已导出到: {output_path}")

    def _convert_to_markdown(self, data: Dict, level: int = 1) -> str:
        """将数据转换为Markdown格式"""
        md = ""

        if isinstance(data, dict):
            for key, value in data.items():
                header = "#" * min(level + 1, 6)
                md += f"{header} {key}\n\n"

                if isinstance(value, (dict, list)):
                    md += self._convert_to_markdown(value, level + 1)
                else:
                    md += f"{value}\n\n"
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    md += self._convert_to_markdown(item, level)
                else:
                    md += f"- {item}\n"
            md += "\n"
        else:
            md = f"{data}\n\n"

        return md
