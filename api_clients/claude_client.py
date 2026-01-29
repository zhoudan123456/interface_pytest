"""
Claude API 客户端封装
用于生成参考答案和评估算法输出
"""
import json
import os
from typing import Dict, List, Optional
from requests import Session


class ClaudeClient:
    """Claude API客户端"""

    def __init__(self, api_key: str = None, base_url: str = "https://api.anthropic.com"):
        """
        初始化Claude客户端
        :param api_key: Claude API密钥(从环境变量读取)
        :param base_url: API基础URL
        """
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY', '')
        self.base_url = base_url
        self.session = Session()
        self.session.headers.update({
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        })

    def generate_reference_checkpoints(self, document_text: str, model: str = "claude-3-5-sonnet-20241022") -> List[Dict]:
        """
        生成参考答案检查点
        :param document_text: 招标文件文本内容
        :param model: Claude模型名称
        :return: 参考检查点列表
        """
        from conf.set_conf import read_yaml
        import pathlib

        # 读取提示词模板
        prompt_file = pathlib.Path(__file__).parents[1] / 'config' / 'prompts' / 'reference_generation.txt'
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            # 如果模板文件不存在,使用默认提示词
            template = """请分析以下招标文件，提取关键检查点（checkpoints）。

招标文件内容：
{document_text}

请以JSON格式返回检查点列表，每个检查点包含：
- id: 检查点ID
- category: 分类（如：资质要求、投标截止时间、保证金等）
- content: 检查点内容
- importance: 重要程度（高/中/低）

返回格式：
{{
  "checkpoints": [
    {{
      "id": "1",
      "category": "分类",
      "content": "具体内容",
      "importance": "高"
    }}
  ]
}}"""

        prompt = template.format(
            document_text=document_text[:6000]  # 限制长度
        )

        payload = {
            "model": model,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1  # 低温度确保稳定性
        }

        try:
            response = self.session.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return self._parse_checkpoints_response(result)
        except Exception as e:
            print(f"调用Claude API失败: {str(e)}")
            return []

    def evaluate_checkpoints(self, document_text: str,
                            algorithm_output: List[Dict],
                            reference_checkpoints: List[Dict],
                            model: str = "claude-3-5-sonnet-20241022") -> Dict:
        """
        评估算法输出
        :param document_text: 招标文件文本
        :param algorithm_output: 算法模型输出的检查点
        :param reference_checkpoints: 参考检查点
        :param model: Claude模型名称
        :return: 评估结果
        """
        import pathlib

        # 读取评估提示词模板
        prompt_file = pathlib.Path(__file__).parents[1] / 'config' / 'prompts' / 'evaluation.txt'
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            # 如果模板文件不存在,使用默认提示词
            template = """请评估以下招标文件解析算法的输出质量。

招标文件预览：
{document_preview}

算法输出：
{algorithm_output}

参考检查点：
{reference_checkpoints}

请从以下维度进行评估：
1. 完整性：是否提取了所有关键信息
2. 准确性：提取的信息是否正确
3. 一致性：与参考答案的匹配度

请以JSON格式返回评估结果：
{{
  "overall_score": 85,
  "completeness_score": 80,
  "accuracy_score": 90,
  "consistency_score": 85,
  "missing_checkpoints": [],
  "incorrect_checkpoints": [],
  "suggestions": []
}}"""

        prompt = template.format(
            document_preview=document_text[:2000],
            algorithm_output=json.dumps(algorithm_output, ensure_ascii=False, indent=2),
            reference_checkpoints=json.dumps(reference_checkpoints, ensure_ascii=False, indent=2)
        )

        payload = {
            "model": model,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }

        try:
            response = self.session.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return self._parse_evaluation_response(result)
        except Exception as e:
            print(f"评估Claude API失败: {str(e)}")
            return {
                "error": str(e),
                "overall_score": 0,
                "completeness_score": 0,
                "accuracy_score": 0,
                "consistency_score": 0
            }

    def _parse_checkpoints_response(self, response: Dict) -> List[Dict]:
        """
        解析Claude的检查点响应
        :param response: API响应
        :return: 检查点列表
        """
        try:
            content = response.get("content", [{}])[0].get("text", "{}")
            # 提取JSON部分（Claude可能返回带解释的文本）
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)
                return data.get("checkpoints", [])
        except Exception as e:
            print(f"解析参考答案失败: {e}")
            return []

    def _parse_evaluation_response(self, response: Dict) -> Dict:
        """
        解析评估响应
        :param response: API响应
        :return: 评估结果字典
        """
        try:
            content = response.get("content", [{}])[0].get("text", "{}")
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"解析评估结果失败: {e}")
            return {"error": "解析失败"}
