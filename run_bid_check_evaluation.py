"""
招标文件检查工作流评估运行脚本
从测试工作流响应中提取数据并运行评估
"""
import json
import os
import sys
import yaml
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bid_check_evaluation import BidCheckEvaluator


def load_test_workflow_config():
    """加载测试工作流配置"""
    config_path = './test_data/bid_check_workflow.yaml'

    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        print("请先运行测试工作流生成配置文件")
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def find_latest_response(response_type: str) -> dict:
    """
    查找最新的响应文件

    Args:
        response_type: 'check_point' 或 'bid_info'

    Returns:
        响应数据字典
    """
    responses_dir = './test_data/evaluation/responses'

    if not os.path.exists(responses_dir):
        print(f"❌ 响应目录不存在: {responses_dir}")
        print("请先运行测试并保存响应数据")
        return None

    # 查找匹配的文件
    files = [
        f for f in os.listdir(responses_dir)
        if f.startswith(f'{response_type}_response_') and f.endswith('.json')
    ]

    if not files:
        print(f"❌ 未找到 {response_type} 响应文件")
        test_num = 5 if response_type == "check_point" else 6
        print(f"请运行test_0{test_num}_* 并保存响应")
        return None

    # 按时间排序，取最新的
    files.sort(reverse=True)
    latest_file = os.path.join(responses_dir, files[0])

    print(f"✓ 找到最新响应文件: {files[0]}")

    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_evaluation_demo():
    """运行评估演示"""
    print("\n" + "=" * 80)
    print("招标文件检查工作流评估".center(80))
    print("=" * 80)

    # 加载配置
    config = load_test_workflow_config()
    if not config:
        return

    task_name = config.get('zb_file_name', 'unknown_task')
    print(f"\n📋 任务名称: {task_name}")
    print(f"📅 评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 初始化评估器
    try:
        evaluator = BidCheckEvaluator()
    except Exception as e:
        print(f"\n❌ 初始化评估器失败: {e}")
        print("请检查 evaluation_config.yaml 配置文件")
        return

    # 评估检查点
    print("\n" + "-" * 80)
    print("评估1: 检查点准确性".center(80))
    print("-" * 80)

    check_point_response = find_latest_response('check_point')
    if check_point_response:
        try:
            check_point_result = evaluator.evaluate_check_points(
                check_point_response,
                task_name
            )
            print(f"\n✓ 检查点评估完成")
            print(f"  准确率: {check_point_result['accuracy_rate']}%")
            print(f"  召回率: {check_point_result['recall_rate']}%")
        except Exception as e:
            print(f"\n❌ 检查点评估失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n⚠️ 跳过检查点评估")

    # 评估投标信息
    print("\n" + "-" * 80)
    print("评估2: 投标信息准确性".center(80))
    print("-" * 80)

    bid_info_response = find_latest_response('bid_info')
    if bid_info_response:
        try:
            bid_info_result = evaluator.evaluate_bid_info(
                bid_info_response,
                task_name
            )
            print(f"\n✓ 投标信息评估完成")
            print(f"  准确率: {bid_info_result['accuracy_rate']}%")
        except Exception as e:
            print(f"\n❌ 投标信息评估失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n⚠️ 跳过投标信息评估")

    # 生成总结报告
    print("\n" + "=" * 80)
    print("评估总结".center(80))
    print("=" * 80)

    if check_point_response and bid_info_response:
        print(f"""
✓ 评估完成！

📊 评估结果:
  - 检查点准确率: {check_point_result.get('accuracy_rate', 'N/A')}%
  - 检查点召回率: {check_point_result.get('recall_rate', 'N/A')}%
  - 投标信息准确率: {bid_info_result.get('accuracy_rate', 'N/A')}%

📁 详细结果已保存到: ./test_data/evaluation/results/
        """)

        # 生成整体评估等级
        cp_acc = check_point_result.get('accuracy_rate', 0)
        bi_acc = bid_info_result.get('accuracy_rate', 0)
        avg_acc = (cp_acc + bi_acc) / 2

        if avg_acc >= 80:
            grade = "优秀 ⭐⭐⭐⭐⭐"
        elif avg_acc >= 70:
            grade = "良好 ⭐⭐⭐⭐"
        elif avg_acc >= 60:
            grade = "及格 ⭐⭐⭐"
        else:
            grade = "需改进 ⭐⭐"

        print(f"🎯 整体评级: {grade}")

    else:
        print("""
⚠️ 评估未完成

提示:
  1. 请先运行测试工作流: pytest test_cases/workflows/test_bid_check_workflow.py -v -s
  2. 确保test_05和test_06已执行并有响应数据
  3. 响应数据会自动保存到 ./test_data/evaluation/responses/
  4. 然后重新运行此评估脚本
        """)


def save_response_from_test():
    """
    从测试工作流保存响应的辅助函数
    在test_bid_check_workflow.py中调用
    """
    def save_response(response_type: str, response_data: dict):
        """保存响应数据"""
        import json
        from datetime import datetime

        output_dir = './test_data/evaluation/responses'
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{response_type}_response_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 响应已保存到: {filepath}")
        return filepath

    return save_response


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           招标文件检查工作流评估框架 v1.0                                    ║
║                                                                              ║
║   功能: 对比算法解析结果与Claude大模型参考答案，评估准确性                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    print("\n使用方法:")
    print("1. 运行测试工作流并保存响应:")
    print("   pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_07_full_workflow_polling -v -s")
    print("\n2. 运行此脚本进行评估:")
    print("   python run_bid_check_evaluation.py")
    print("\n" + "=" * 80)

    # 运行评估
    run_evaluation_demo()

    print("\n" + "=" * 80)
    print("评估结束".center(80))
    print("=" * 80 + "\n")
