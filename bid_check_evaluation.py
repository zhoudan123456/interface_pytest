"""
招标文件检查工作流评估框架
对比算法解析结果与大模型评估结果，计算准确度
"""
import json
import os
import yaml
from datetime import datetime
from typing import Dict, List, Any
from api_clients.claude_client import ClaudeClient


class BidCheckEvaluator:
    """招标文件检查评估器"""

    def __init__(self, config_path: str = './test_data/evaluation/evaluation_config.yaml'):
        """初始化评估器"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.claude_client = ClaudeClient(api_key=config['claude_api_key'])
        self.output_dir = './test_data/evaluation/results'
        os.makedirs(self.output_dir, exist_ok=True)

    def evaluate_check_points(self, algorithm_result: Dict, task_name: str) -> Dict:
        """
        评估检查点准确性

        Args:
            algorithm_result: test_05_check_check_point的响应结果
            task_name: 任务名称

        Returns:
            评估结果字典
        """
        print("\n" + "=" * 60)
        print("开始评估检查点准确性")
        print("=" * 60)

        # 提取算法结果
        algorithm_check_points = self._extract_algorithm_check_points(algorithm_result)

        # 生成Claude参考答案
        print("\n正在生成Claude参考答案...")
        claude_check_points = self._generate_claude_check_points(task_name)

        # 对比评估
        print("\n正在对比评估...")
        evaluation_result = self._compare_check_points(
            algorithm_check_points,
            claude_check_points
        )

        # 保存结果
        self._save_evaluation_result(
            task_name,
            "check_points",
            algorithm_check_points,
            claude_check_points,
            evaluation_result
        )

        return evaluation_result

    def evaluate_bid_info(self, algorithm_result: Dict, task_name: str) -> Dict:
        """
        评估投标信息准确性

        Args:
            algorithm_result: test_06_get_bid_info的响应结果
            task_name: 任务名称

        Returns:
            评估结果字典
        """
        print("\n" + "=" * 60)
        print("开始评估投标信息准确性")
        print("=" * 60)

        # 提取算法结果
        algorithm_bid_info = self._extract_algorithm_bid_info(algorithm_result)

        # 生成Claude参考答案
        print("\n正在生成Claude参考答案...")
        claude_bid_info = self._generate_claude_bid_info(task_name)

        # 对比评估
        print("\n正在对比评估...")
        evaluation_result = self._compare_bid_info(
            algorithm_bid_info,
            claude_bid_info
        )

        # 保存结果
        self._save_evaluation_result(
            task_name,
            "bid_info",
            algorithm_bid_info,
            claude_bid_info,
            evaluation_result
        )

        return evaluation_result

    def _extract_algorithm_check_points(self, algorithm_result: Dict) -> List[Dict]:
        """从算法结果中提取检查点"""
        check_points = []

        if algorithm_result.get('code') == 200:
            data = algorithm_result.get('data', {})

            # 根据实际API响应结构调整
            if isinstance(data, dict):
                # 假设检查点在checkPoints字段中
                raw_check_points = data.get('checkPoints', [])

                for item in raw_check_points:
                    check_points.append({
                        'category': item.get('category', ''),
                        'check_point': item.get('checkPoint', ''),
                        'requirement': item.get('requirement', ''),
                        'result': item.get('result', ''),
                        'is_compliant': item.get('isCompliant', False)
                    })

            elif isinstance(data, list):
                for item in data:
                    check_points.append({
                        'category': item.get('category', ''),
                        'check_point': item.get('checkPoint', ''),
                        'requirement': item.get('requirement', ''),
                        'result': item.get('result', ''),
                        'is_compliant': item.get('isCompliant', False)
                    })

        print(f"✓ 提取到 {len(check_points)} 个算法检查点")
        return check_points

    def _extract_algorithm_bid_info(self, algorithm_result: Dict) -> Dict:
        """从算法结果中提取投标信息"""
        bid_info = {}

        if algorithm_result.get('code') == 200:
            data = algorithm_result.get('data', {})

            # 根据实际API响应结构调整
            bid_info = {
                'company_name': data.get('companyName', ''),
                'bid_amount': data.get('bidAmount', ''),
                'bid_validity': data.get('bidValidity', ''),
                'project_period': data.get('projectPeriod', ''),
                'qualifications': data.get('qualifications', []),
                'key_personnel': data.get('keyPersonnel', []),
                'technical_proposal': data.get('technicalProposal', ''),
                'commercial_proposal': data.get('commercialProposal', '')
            }

        print(f"✓ 提取到投标信息")
        return bid_info

    def _generate_claude_check_points(self, task_name: str) -> List[Dict]:
        """使用Claude生成检查点参考答案"""
        prompt = self._get_check_point_prompt()

        try:
            response = self.claude_client.generate_response(prompt)
            return self._parse_claude_check_points(response)
        except Exception as e:
            print(f"⚠ Claude生成检查点失败: {e}")
            return []

    def _generate_claude_bid_info(self, task_name: str) -> Dict:
        """使用Claude生成投标信息参考答案"""
        prompt = self._get_bid_info_prompt()

        try:
            response = self.claude_client.generate_response(prompt)
            return self._parse_claude_bid_info(response)
        except Exception as e:
            print(f"⚠ Claude生成投标信息失败: {e}")
            return {}

    def _get_check_point_prompt(self) -> str:
        """获取检查点生成的Prompt"""
        # 这里应该读取招标文件内容，让Claude分析
        # 简化版本，实际需要从文件中读取内容
        return """请根据招标文件内容，分析并列出所有关键检查点，包括：

1. 资质要求检查点
2. 技术要求检查点
3. 商务要求检查点
4. 法律合规检查点

请以JSON格式返回，格式如下：
```json
{
  "check_points": [
    {
      "category": "资质要求",
      "check_point": "检查点描述",
      "requirement": "具体要求",
      "expected_result": "期望结果"
    }
  ]
}
```

请基于招标文件内容，尽可能全面地列出所有检查点。"""

    def _get_bid_info_prompt(self) -> str:
        """获取投标信息生成的Prompt"""
        return """请根据投标文件内容，提取以下关键信息：

1. 公司名称
2. 投标金额
3. 投标有效期
4. 项目周期
5. 资质证书
6. 关键人员
7. 技术方案摘要
8. 商务方案摘要

请以JSON格式返回：
```json
{
  "company_name": "公司全称",
  "bid_amount": "投标金额",
  "bid_validity": "有效期",
  "project_period": "项目周期",
  "qualifications": ["资质1", "资质2"],
  "key_personnel": ["人员1", "人员2"],
  "technical_proposal": "技术方案摘要",
  "commercial_proposal": "商务方案摘要"
}
```
"""

    def _parse_claude_check_points(self, response: str) -> List[Dict]:
        """解析Claude返回的检查点"""
        try:
            # 提取JSON部分
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response

            data = json.loads(json_str)
            check_points = data.get('check_points', [])

            print(f"✓ Claude生成了 {len(check_points)} 个检查点")
            return check_points

        except Exception as e:
            print(f"⚠ 解析Claude检查点失败: {e}")
            return []

    def _parse_claude_bid_info(self, response: str) -> Dict:
        """解析Claude返回的投标信息"""
        try:
            # 提取JSON部分
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response

            bid_info = json.loads(json_str)
            print(f"✓ Claude生成了投标信息")
            return bid_info

        except Exception as e:
            print(f"⚠ 解析Claude投标信息失败: {e}")
            return {}

    def _compare_check_points(
        self,
        algorithm_check_points: List[Dict],
        claude_check_points: List[Dict]
    ) -> Dict:
        """对比检查点结果"""
        total_algorithm = len(algorithm_check_points)
        total_claude = len(claude_check_points)

        # 计算匹配度
        matched = 0
        partial_matched = 0

        for algo_cp in algorithm_check_points:
            for claude_cp in claude_check_points:
                similarity = self._calculate_similarity(
                    algo_cp.get('check_point', ''),
                    claude_cp.get('check_point', '')
                )

                if similarity > 0.8:
                    matched += 1
                    break
                elif similarity > 0.5:
                    partial_matched += 1
                    break

        accuracy_rate = (matched / total_claude * 100) if total_claude > 0 else 0
        recall_rate = (matched / total_algorithm * 100) if total_algorithm > 0 else 0

        result = {
            'total_algorithm_check_points': total_algorithm,
            'total_claude_check_points': total_claude,
            'matched': matched,
            'partial_matched': partial_matched,
            'accuracy_rate': round(accuracy_rate, 2),
            'recall_rate': round(recall_rate, 2),
            'details': []
        }

        print(f"\n✓ 评估完成:")
        print(f"  - 算法检查点数: {total_algorithm}")
        print(f"  - Claude检查点数: {total_claude}")
        print(f"  - 完全匹配: {matched}")
        print(f"  - 部分匹配: {partial_matched}")
        print(f"  - 准确率: {accuracy_rate:.2f}%")
        print(f"  - 召回率: {recall_rate:.2f}%")

        return result

    def _compare_bid_info(
        self,
        algorithm_bid_info: Dict,
        claude_bid_info: Dict
    ) -> Dict:
        """对比投标信息结果"""
        fields = [
            'company_name', 'bid_amount', 'bid_validity', 'project_period',
            'technical_proposal', 'commercial_proposal'
        ]

        matched_fields = 0
        details = []

        for field in fields:
            algo_value = algorithm_bid_info.get(field, '')
            claude_value = claude_bid_info.get(field, '')

            similarity = self._calculate_similarity(algo_value, claude_value)
            is_match = similarity > 0.8

            if is_match:
                matched_fields += 1

            details.append({
                'field': field,
                'algorithm_value': algo_value,
                'claude_value': claude_value,
                'similarity': round(similarity, 2),
                'is_match': is_match
            })

        accuracy_rate = (matched_fields / len(fields) * 100) if fields else 0

        result = {
            'total_fields': len(fields),
            'matched_fields': matched_fields,
            'accuracy_rate': round(accuracy_rate, 2),
            'details': details
        }

        print(f"\n✓ 评估完成:")
        print(f"  - 总字段数: {len(fields)}")
        print(f"  - 匹配字段数: {matched_fields}")
        print(f"  - 准确率: {accuracy_rate:.2f}%")

        return result

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版本）"""
        if not text1 or not text2:
            return 0.0

        # 简单的相似度计算（实际可以使用更复杂的算法）
        text1_words = set(text1.lower().split())
        text2_words = set(text2.lower().split())

        if not text1_words or not text2_words:
            return 0.0

        intersection = text1_words & text2_words
        union = text1_words | text2_words

        return len(intersection) / len(union) if union else 0.0

    def _save_evaluation_result(
        self,
        task_name: str,
        evaluation_type: str,
        algorithm_result: Any,
        claude_result: Any,
        evaluation_result: Dict
    ):
        """保存评估结果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{task_name}_{evaluation_type}_evaluation_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        output = {
            'task_name': task_name,
            'evaluation_type': evaluation_type,
            'timestamp': timestamp,
            'algorithm_result': algorithm_result,
            'claude_reference': claude_result,
            'evaluation_metrics': evaluation_result
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n✓ 评估结果已保存到: {filepath}")


def run_evaluation_from_test_results():
    """
    从测试工作流的响应结果运行评估
    """
    print("=" * 60)
    print("招标文件检查工作流评估")
    print("=" * 60)

    # 加载测试工作流配置
    with open('./test_data/bid_check_workflow.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    task_name = config.get('zb_file_name', 'unknown_task')

    # 初始化评估器
    evaluator = BidCheckEvaluator()

    # 这里需要从实际的测试响应中获取数据
    # 可以通过以下方式：
    # 1. 运行test_05和test_06并捕获响应
    # 2. 从保存的响应文件中读取
    # 3. 手动传入响应数据

    print("\n提示：请确保已经运行过test_05和test_06，并且有响应数据")
    print("评估器将从API响应中提取数据并与Claude参考答案对比")

    # 示例：如果有保存的响应数据
    # check_point_response = load_response('check_point_response.json')
    # evaluator.evaluate_check_points(check_point_response, task_name)

    # bid_info_response = load_response('bid_info_response.json')
    # evaluator.evaluate_bid_info(bid_info_response, task_name)


if __name__ == '__main__':
    run_evaluation_from_test_results()
