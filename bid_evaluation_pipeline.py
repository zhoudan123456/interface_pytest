"""
招标文件解析评估流水线
主测试流程控制器
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from api_clients.claude_client import ClaudeClient
from api_clients.algorithm_client import AlgorithmClient
from evaluators.claude_evaluator import ClaudeEvaluator
from processors.document_processor import DocumentProcessor


class BidParserEvaluationPipeline:
    """招标文件解析评估流水线"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化评估流水线
        :param config: 配置字典,包含:
            - claude_api_key: Claude API密钥
            - algorithm_env: 算法API环境
            - output_dir: 输出目录
        """
        self.config = config or {}

        # 初始化组件
        claude_api_key = self.config.get('claude_api_key') or os.getenv('CLAUDE_API_KEY', '')
        self.claude_client = ClaudeClient(claude_api_key)
        self.algorithm_client = AlgorithmClient(
            self.config.get('algorithm_env', 'Test_Env')
        )
        self.document_processor = DocumentProcessor()
        self.evaluator = ClaudeEvaluator(self.claude_client)

        # 输出目录
        self.output_dir = Path(self.config.get('output_dir', './test_data/evaluation/output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_single_document(self, document_path: str,
                                document_id: Optional[str] = None) -> Dict:
        """
        评估单份招标文件
        :param document_path: 文档文件路径
        :param document_id: 文档ID(如果已有上传后的ID)
        :return: 评估结果
        """
        try:
            print(f"\n{'='*60}")
            print(f"开始评估文档: {document_path}")
            print(f"{'='*60}")

            # 1. 读取并预处理招标文件
            print(f"\n[1/4] 读取文档内容...")
            document_text = self.document_processor.load_and_preprocess(document_path)
            print(f"文档读取成功,内容长度: {len(document_text)} 字符")

            # 2. 调用算法模型解析
            print(f"\n[2/4] 调用算法模型解析...")
            if document_id:
                # 使用文档ID调用算法API
                algorithm_checkpoints = self.algorithm_client.parse_bid_document(document_id)
            else:
                # 如果没有文档ID,需要先上传文档获取ID
                # 这里需要根据实际API实现
                raise NotImplementedError("需要先上传文档获取ID,或提供document_id参数")

            print(f"算法解析成功,提取了 {len(algorithm_checkpoints)} 个检查点")

            # 3. 使用Claude生成参考答案
            print(f"\n[3/4] 生成参考答案...")
            reference_checkpoints = self.claude_client.generate_reference_checkpoints(document_text)
            print(f"参考答案生成成功,包含 {len(reference_checkpoints)} 个检查点")

            # 4. 使用Claude评估算法输出
            print(f"\n[4/4] 评估算法输出...")
            evaluation_result = self.evaluator.evaluate(
                document_text,
                algorithm_checkpoints,
                reference_checkpoints
            )

            # 添加元数据
            evaluation_result['metadata'] = {
                'document_path': document_path,
                'document_id': document_id,
                'algorithm_checkpoints_count': len(algorithm_checkpoints),
                'reference_checkpoints_count': len(reference_checkpoints)
            }

            # 5. 保存结果
            self._save_results(document_path, {
                'algorithm_output': algorithm_checkpoints,
                'reference_checkpoints': reference_checkpoints,
                'evaluation_result': evaluation_result
            })

            print(f"\n{'='*60}")
            print(f"评估完成!")
            print(f"总体评分: {evaluation_result.get('overall_score', 0)}")
            print(f"F1分数: {evaluation_result.get('f1_score', 0)}")
            print(f"{'='*60}\n")

            return evaluation_result

        except Exception as e:
            print(f"\n❌ 评估失败 {document_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

    def evaluate_batch(self, documents: List[Dict[str, str]],
                      max_concurrent: int = 1) -> List[Dict]:
        """
        批量评估招标文件
        :param documents: 文档列表,每个元素包含:
            - path: 文档路径
            - document_id: 文档ID(可选)
        :param max_concurrent: 最大并发数(暂不支持并发,保留参数)
        :return: 评估结果列表
        """
        print(f"\n开始批量评估 {len(documents)} 个文档...")

        results = []
        for i, doc_info in enumerate(documents, 1):
            print(f"\n处理第 {i}/{len(documents)} 个文档")
            result = self.evaluate_single_document(
                document_path=doc_info['path'],
                document_id=doc_info.get('document_id')
            )
            results.append(result)

        # 生成批量评估报告
        self._generate_batch_report(results)

        return results

    def evaluate_directory(self, directory: str, pattern: str = "*.txt",
                          document_ids: Optional[Dict[str, str]] = None) -> List[Dict]:
        """
        评估目录下的所有文档
        :param directory: 目录路径
        :param pattern: 文件匹配模式
        :param document_ids: 文档ID映射字典 {filename: document_id}
        :return: 评估结果列表
        """
        # 加载目录下的文档
        documents_data = self.document_processor.load_batch(directory, pattern)

        # 添加document_id
        for doc in documents_data:
            filename = doc['filename']
            if document_ids and filename in document_ids:
                doc['document_id'] = document_ids[filename]

        # 批量评估
        return self.evaluate_batch(documents_data)

    def _save_results(self, document_path: str, results: Dict):
        """
        保存评估结果
        :param document_path: 文档路径
        :param results: 评估结果
        """
        filename = Path(document_path).stem
        output_path = self.output_dir / f"{filename}_result.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"✅ 结果已保存到: {output_path}")

    def _generate_batch_report(self, results: List[Dict]):
        """
        生成批量评估报告
        :param results: 评估结果列表
        """
        report = self.evaluator.generate_evaluation_report(results)

        # 保存报告
        report_path = self.output_dir / "evaluation_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n{report}")
        print(f"\n✅ 批量评估报告已保存到: {report_path}")


def load_config(config_path: str) -> Dict:
    """
    加载配置文件
    :param config_path: 配置文件路径
    :return: 配置字典
    """
    import yaml
    from conf.set_conf import resolve_path

    config_file = resolve_path(config_path)
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
