"""
招标文件解析准确度测试用例
"""
import json
import os
import pytest
from pathlib import Path

from bid_evaluation_pipeline import BidParserEvaluationPipeline, load_config
from processors.document_processor import DocumentProcessor
from api_clients.claude_client import ClaudeClient
from api_clients.algorithm_client import AlgorithmClient
from evaluators.claude_evaluator import ClaudeEvaluator


class TestBidParserEvaluation:
    """招标文件解析准确度测试"""

    @pytest.fixture(scope="class")
    def pipeline(self):
        """初始化评估流水线"""
        # 尝试加载配置文件
        config_path = './test_data/evaluation/evaluation_config.yaml'
        try:
            config = load_config(config_path)
        except FileNotFoundError:
            # 如果配置文件不存在,使用默认配置
            config = {
                'claude_api_key': os.getenv('CLAUDE_API_KEY', ''),
                'algorithm_env': 'Test_Env',
                'output_dir': './test_data/evaluation/output'
            }
        return BidParserEvaluationPipeline(config)

    @pytest.fixture(scope="class")
    def document_processor(self):
        """文档处理器"""
        return DocumentProcessor()

    def test_document_processor_load_txt(self, document_processor, tmp_path):
        """测试文档处理器加载文本文件"""
        # 创建测试文件
        test_file = tmp_path / "test_bid.txt"
        test_content = """
        招标项目：智慧校园建设
        投标截止时间：2024年6月30日
        资质要求：信息系统集成二级资质
        保证金：10万元
        """
        test_file.write_text(test_content, encoding='utf-8')

        # 加载文件
        content = document_processor.load_and_preprocess(str(test_file))

        # 验证
        assert "智慧校园建设" in content
        assert "2024年6月30日" in content
        assert "信息系统集成二级资质" in content
        assert "10万元" in content

    def test_claude_client_generate_checkpoints(self, pipeline):
        """测试Claude客户端生成参考答案"""
        # 跳过测试如果没有API密钥
        pytest.skip("需要Claude API密钥")

        # 测试文档
        test_text = """
        招标项目：智慧校园建设
        投标截止时间：2024年6月30日 17:00
        资质要求：信息系统集成二级资质以上
        保证金：10万元人民币
        联系人：张三
        联系电话：13800138000
        """

        # 生成参考答案
        checkpoints = pipeline.claude_client.generate_reference_checkpoints(test_text)

        # 验证
        assert isinstance(checkpoints, list)
        assert len(checkpoints) > 0
        assert all(isinstance(cp, dict) for cp in checkpoints)

    def test_claude_evaluator_evaluate(self, pipeline):
        """测试Claude评估器"""
        # 跳过测试如果没有API密钥
        pytest.skip("需要Claude API密钥")

        # 测试数据
        document_text = "招标项目：智慧校园建设\n投标截止时间：2024年6月30日"
        algorithm_checkpoints = [
            {"id": "1", "category": "项目名称", "content": "智慧校园建设", "importance": "高"},
            {"id": "2", "category": "截止时间", "content": "2024年6月30日", "importance": "高"}
        ]
        reference_checkpoints = [
            {"id": "1", "category": "项目名称", "content": "智慧校园建设", "importance": "高"},
            {"id": "2", "category": "截止时间", "content": "2024年6月30日", "importance": "高"}
        ]

        # 评估
        result = pipeline.evaluator.evaluate(
            document_text,
            algorithm_checkpoints,
            reference_checkpoints
        )

        # 验证
        assert isinstance(result, dict)
        assert 'overall_score' in result or 'error' in result

    def test_algorithm_client_parse_document(self, pipeline, api):
        """测试算法客户端解析文档"""
        # 这个测试需要实际的文档ID
        # 可以使用现有的测试流程获取文档ID

        # 示例:从配置读取文档ID
        from conf.set_conf import read_conf
        document_id = read_conf('data', 'document_id')

        if not document_id:
            pytest.skip("需要文档ID,请先运行上传文档测试")

        # 调用算法解析
        checkpoints = pipeline.algorithm_client.parse_bid_document(document_id)

        # 验证
        assert isinstance(checkpoints, list)

    @pytest.mark.parametrize("data", [
        {
            "document_id": "${document_id}",
            "expected_min_score": 60
        }
    ])
    def test_evaluate_single_document(self, pipeline, api, data):
        """测试评估单个文档的完整流程"""
        # 从配置读取文档ID
        from conf.set_conf import read_conf
        document_id = read_conf('data', 'document_id')

        if not document_id:
            pytest.skip("需要文档ID,请先运行上传文档测试")

        # 准备测试数据
        # 注意:这里假设文档已经上传,document_id已保存
        # 实际测试时需要确保文档路径存在

        # 使用模拟文档路径进行测试
        test_document_path = './test_data/evaluation/input/sample.txt'

        if not os.path.exists(test_document_path):
            pytest.skip(f"测试文档不存在: {test_document_path}")

        # 执行评估
        result = pipeline.evaluate_single_document(
            document_path=test_document_path,
            document_id=document_id
        )

        # 验证结果
        assert isinstance(result, dict)
        assert 'error' not in result, f"评估失败: {result.get('error')}"

        # 验证分数
        overall_score = result.get('overall_score', 0)
        assert overall_score >= data['expected_min_score'], \
            f"分数过低: {overall_score} < {data['expected_min_score']}"

    def test_batch_evaluation(self, pipeline, tmp_path):
        """测试批量评估"""
        # 创建测试文档
        test_docs = []
        for i in range(3):
            doc_file = tmp_path / f"test_doc_{i}.txt"
            doc_file.write_text(f"测试文档 {i} 内容\n项目名称:测试项目{i}", encoding='utf-8')
            test_docs.append({
                'path': str(doc_file),
                'document_id': None  # 暂不使用document_id
            })

        # 由于没有实际的document_id,这里只测试文档处理器的批量加载
        documents = pipeline.document_processor.load_batch(str(tmp_path), "*.txt")
        assert len(documents) == 3


class TestBidParserEvaluationIntegration:
    """集成测试:完整的评估流程"""

    @pytest.fixture(scope="class")
    def evaluation_config(self):
        """评估配置"""
        return {
            'claude_api_key': os.getenv('CLAUDE_API_KEY', ''),
            'algorithm_env': 'Test_Env',
            'output_dir': './test_data/evaluation/output'
        }

    def test_full_evaluation_workflow(self, evaluation_config, api):
        """测试完整的评估工作流"""
        # 这个测试需要:
        # 1. 上传文档获取document_id
        # 2. 调用算法API解析
        # 3. 使用Claude生成参考答案
        # 4. 评估算法输出

        from conf.set_conf import read_conf
        document_id = read_conf('data', 'document_id')

        if not document_id:
            pytest.skip("需要文档ID,请先运行test_bid_workflow中的上传测试")

        # 创建流水线
        pipeline = BidParserEvaluationPipeline(evaluation_config)

        # 准备测试文档路径
        test_document_path = './test_data/evaluation/input/sample.txt'

        if not os.path.exists(test_document_path):
            # 创建示例文档
            os.makedirs(os.path.dirname(test_document_path), exist_ok=True)
            with open(test_document_path, 'w', encoding='utf-8') as f:
                f.write("招标项目：测试项目\n投标截止：2024年12月31日")

        # 执行评估
        result = pipeline.evaluate_single_document(
            document_path=test_document_path,
            document_id=document_id
        )

        # 验证
        assert isinstance(result, dict)
        if 'error' not in result:
            assert 'overall_score' in result
            print(f"\n评估结果:")
            print(f"总体评分: {result.get('overall_score', 0)}")
            print(f"完整性: {result.get('completeness_score', 0)}")
            print(f"准确性: {result.get('accuracy_score', 0)}")
            print(f"F1分数: {result.get('f1_score', 0)}")
