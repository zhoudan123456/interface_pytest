"""
Claude评估器
用于评估算法模型输出的准确性
"""
import json
from typing import Dict, List
from api_clients.claude_client import ClaudeClient


class ClaudeEvaluator:
    """使用Claude进行评估的评估器"""

    def __init__(self, claude_client: ClaudeClient):
        """
        初始化评估器
        :param claude_client: Claude API客户端实例
        """
        self.claude_client = claude_client

    def evaluate(self, document_text: str,
                algorithm_checkpoints: List[Dict],
                reference_checkpoints: List[Dict]) -> Dict:
        """
        评估算法输出
        :param document_text: 招标文件文本
        :param algorithm_checkpoints: 算法模型输出的检查点
        :param reference_checkpoints: 参考检查点
        :return: 评估结果
        """
        print(f"开始评估: 算法输出{len(algorithm_checkpoints)}个检查点, 参考{len(reference_checkpoints)}个检查点")

        # 调用Claude进行评估
        evaluation_result = self.claude_client.evaluate_checkpoints(
            document_text=document_text,
            algorithm_output=algorithm_checkpoints,
            reference_checkpoints=reference_checkpoints
        )

        # 添加额外的统计分析
        evaluation_result.update(self._calculate_statistics(
            algorithm_checkpoints,
            reference_checkpoints
        ))

        return evaluation_result

    def evaluate_batch(self, documents_data: List[Dict]) -> List[Dict]:
        """
        批量评估多个文档
        :param documents_data: 文档数据列表,每个元素包含:
            - document_text: 文档文本
            - algorithm_checkpoints: 算法输出
            - reference_checkpoints: 参考答案
        :return: 评估结果列表
        """
        results = []
        for i, doc_data in enumerate(documents_data):
            print(f"正在评估第{i+1}/{len(documents_data)}个文档")
            result = self.evaluate(
                document_text=doc_data['document_text'],
                algorithm_checkpoints=doc_data['algorithm_checkpoints'],
                reference_checkpoints=doc_data['reference_checkpoints']
            )
            results.append(result)
        return results

    def _calculate_statistics(self, algorithm_checkpoints: List[Dict],
                            reference_checkpoints: List[Dict]) -> Dict:
        """
        计算统计指标
        :param algorithm_checkpoints: 算法检查点
        :param reference_checkpoints: 参考检查点
        :return: 统计数据
        """
        # 基于内容的简单匹配统计
        algorithm_contents = set()
        for cp in algorithm_checkpoints:
            content = cp.get('content', '')
            if content:
                algorithm_contents.add(content.lower().strip())

        reference_contents = set()
        for cp in reference_checkpoints:
            content = cp.get('content', '')
            if content:
                reference_contents.add(content.lower().strip())

        # 计算匹配的检查点
        matched = algorithm_contents & reference_contents

        # 计算指标
        total_reference = len(reference_contents)
        total_algorithm = len(algorithm_contents)
        total_matched = len(matched)

        precision = total_matched / total_algorithm if total_algorithm > 0 else 0
        recall = total_matched / total_reference if total_reference > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            'total_reference_checkpoints': total_reference,
            'total_algorithm_checkpoints': total_algorithm,
            'matched_checkpoints': total_matched,
            'precision': round(precision * 100, 2),
            'recall': round(recall * 100, 2),
            'f1_score': round(f1_score * 100, 2)
        }

    def generate_evaluation_report(self, evaluation_results: List[Dict]) -> str:
        """
        生成评估报告
        :param evaluation_results: 评估结果列表
        :return: 报告文本
        """
        total_docs = len(evaluation_results)

        # 计算平均分数
        avg_overall = sum(r.get('overall_score', 0) for r in evaluation_results) / total_docs
        avg_completeness = sum(r.get('completeness_score', 0) for r in evaluation_results) / total_docs
        avg_accuracy = sum(r.get('accuracy_score', 0) for r in evaluation_results) / total_docs
        avg_consistency = sum(r.get('consistency_score', 0) for r in evaluation_results) / total_docs
        avg_f1 = sum(r.get('f1_score', 0) for r in evaluation_results) / total_docs

        report = f"""
=== 招标文件解析准确度评估报告 ===

评估文档数量: {total_docs}

=== 平均分数 ===
总体评分: {avg_overall:.2f}
完整性: {avg_completeness:.2f}
准确性: {avg_accuracy:.2f}
一致性: {avg_consistency:.2f}
F1分数: {avg_f1:.2f}

=== 详细结果 ===
"""
        for i, result in enumerate(evaluation_results, 1):
            report += f"\n文档 {i}:\n"
            report += f"  总体评分: {result.get('overall_score', 0)}\n"
            report += f"  完整性: {result.get('completeness_score', 0)}\n"
            report += f"  准确性: {result.get('accuracy_score', 0)}\n"
            report += f"  一致性: {result.get('consistency_score', 0)}\n"
            report += f"  F1分数: {result.get('f1_score', 0)}\n"

            if result.get('missing_checkpoints'):
                report += f"  缺失检查点: {len(result['missing_checkpoints'])}\n"
            if result.get('incorrect_checkpoints'):
                report += f"  错误检查点: {len(result['incorrect_checkpoints'])}\n"

        return report
