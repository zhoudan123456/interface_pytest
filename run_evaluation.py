"""
快速开始:运行招标文件解析准确度评估
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from bid_evaluation_pipeline import BidParserEvaluationPipeline, load_config


def main():
    """主函数"""
    print("=" * 60)
    print("招标文件解析准确度评估框架")
    print("=" * 60)

    # 检查环境变量
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    if not claude_api_key:
        print("\n❌ 错误: 未设置CLAUDE_API_KEY环境变量")
        print("\n请设置环境变量:")
        print("  Windows: set CLAUDE_API_KEY=your-api-key")
        print("  Linux/Mac: export CLAUDE_API_KEY=your-api-key")
        print("\n或者修改配置文件: test_data/evaluation/evaluation_config.yaml")
        return

    print(f"\n✅ Claude API密钥已配置")

    # 加载配置
    config_path = './test_data/evaluation/evaluation_config.yaml'
    try:
        config = load_config(config_path)
        print(f"✅ 配置文件加载成功: {config_path}")
    except FileNotFoundError:
        print(f"⚠️  配置文件不存在,使用默认配置")
        config = {
            'claude_api_key': claude_api_key,
            'algorithm_env': 'Test_Env',
            'output_dir': './test_data/evaluation/output'
        }

    # 创建流水线
    pipeline = BidParserEvaluationPipeline(config)

    # 检查输入目录
    input_dir = Path('./test_data/evaluation/input')
    if not input_dir.exists():
        print(f"\n❌ 错误: 输入目录不存在: {input_dir}")
        print(f"\n请创建输入目录并放入待测试的文档:")
        print(f"  mkdir -p {input_dir}")
        print(f"  cp your_document.txt {input_dir}/")
        return

    # 查找测试文档
    test_files = list(input_dir.glob("*.txt")) + \
                 list(input_dir.glob("*.pdf")) + \
                 list(input_dir.glob("*.docx"))

    if not test_files:
        print(f"\n⚠️  警告: 输入目录中没有找到测试文档")
        print(f"\n支持的格式: .txt, .pdf, .docx")
        print(f"请将待测试的文档放入: {input_dir}")
        return

    print(f"\n找到 {len(test_files)} 个测试文档:")
    for f in test_files:
        print(f"  - {f.name}")

    # 询问是否继续
    print("\n" + "=" * 60)
    response = input(f"\n是否开始评估这 {len(test_files)} 个文档? (y/n): ")

    if response.lower() != 'y':
        print("已取消评估")
        return

    # 检查是否有document_id
    from conf.set_conf import read_conf
    document_id = read_conf('data', 'document_id')

    if document_id:
        print(f"\n✅ 找到文档ID: {document_id}")
        use_document_id = True
    else:
        print(f"\n⚠️  未找到文档ID")
        print(f"\n注意: 算法API需要文档ID才能解析")
        print(f"请先运行上传测试获取文档ID:")
        print(f"  pytest test_cases/workflows/test_bid_workflow.py::TestBidGenerateWorkflow::test_01_upload_document -v")
        use_document_id = False

    # 开始评估
    print("\n" + "=" * 60)
    print("开始评估...")
    print("=" * 60)

    results = []
    for i, test_file in enumerate(test_files, 1):
        print(f"\n[{i}/{len(test_files)}] 评估文档: {test_file.name}")

        if use_document_id:
            # 使用相同的document_id(适用于单个文档的多次测试)
            result = pipeline.evaluate_single_document(
                document_path=str(test_file),
                document_id=document_id
            )
        else:
            # 仅进行文档处理测试,不调用算法API
            print("  跳过算法解析(需要document_id)")
            continue

        results.append(result)

    # 生成报告
    if results:
        print("\n" + "=" * 60)
        print("评估完成!生成报告...")
        print("=" * 60)

        report = pipeline.evaluator.generate_evaluation_report(results)
        print(report)

        print(f"\n✅ 详细结果已保存到: {pipeline.output_dir}")
    else:
        print("\n⚠️  没有完成任何评估")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断评估")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
