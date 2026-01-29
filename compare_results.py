"""
对比优化前后的效果
"""
import json
import os
from pathlib import Path

def load_latest_results():
    """加载最新的两次评估结果"""
    results_dir = Path('./test_data/evaluation/results')

    # 获取所有评估文件
    files = list(results_dir.glob('claude_comparison_*.json'))
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    if len(files) < 1:
        print("[ERROR] 未找到评估结果文件")
        return None, None

    # 加载最新的结果（可能是V1或V2）
    latest_file = files[0]
    with open(latest_file, 'r', encoding='utf-8') as f:
        latest = json.load(f)

    # 尝试找到另一个版本的文件
    second_file = None
    for f in files[1:]:
        if 'v2' in f.name and 'v2' not in latest_file.name:
            second_file = f
            break
        elif 'v2' not in f.name and 'v2' in latest_file.name:
            second_file = f
            break

    if second_file:
        with open(second_file, 'r', encoding='utf-8') as f:
            second = json.load(f)
        return latest, second

    return latest, None


def display_comparison(result1, result2):
    """显示对比结果"""

    print("=" * 80)
    print("评估结果对比".center(80))
    print("=" * 80)

    # 确定版本
    if result1 and 'v2' in str(result1.get('timestamp', '')):
        v2_result = result1
        v1_result = result2
    elif result2 and 'v2' in str(result2.get('timestamp', '')):
        v2_result = result2
        v1_result = result1
    else:
        v1_result = result1
        v2_result = None

    # 显示V1结果
    if v1_result:
        comp1 = v1_result.get('comparison', {})
        print("\n[原版 V1] 评估结果:")
        print(f"  算法提取: {comp1.get('algorithm_count', 0)} 个")
        print(f"  智谱AI提取: {comp1.get('claude_count', 0)} 个")
        print(f"  匹配检查点: {comp1.get('matched', 0)} 个")
        print(f"  覆盖率: {comp1.get('coverage', 0):.1f}%")
        print(f"  召回率: {comp1.get('recall', 0):.1f}%")

    # 显示V2结果
    if v2_result:
        comp2 = v2_result.get('comparison', {})
        print("\n[优化版 V2] 评估结果:")
        print(f"  算法提取: {comp2.get('algorithm_count', 0)} 个")
        print(f"  智谱AI提取: {comp2.get('claude_count', 0)} 个")
        print(f"  匹配检查点: {comp2.get('matched', 0)} 个")
        print(f"  覆盖率: {comp2.get('coverage', 0):.1f}%")
        print(f"  召回率: {comp2.get('recall', 0):.1f}%")

    # 计算改进
    if v1_result and v2_result:
        comp1 = v1_result.get('comparison', {})
        comp2 = v2_result.get('comparison', {})

        print("\n" + "=" * 80)
        print("改进效果".center(80))
        print("=" * 80)

        matched_improvement = comp2.get('matched', 0) - comp1.get('matched', 0)
        coverage_improvement = comp2.get('coverage', 0) - comp1.get('coverage', 0)
        recall_improvement = comp2.get('recall', 0) - comp1.get('recall', 0)

        print(f"\n匹配检查点: {comp1.get('matched', 0)} → {comp2.get('matched', 0)} "
              f"({matched_improvement:+d}个)")

        print(f"覆盖率: {comp1.get('coverage', 0):.1f}% → {comp2.get('coverage', 0):.1f}% "
              f"({coverage_improvement:+.1f}%)")

        print(f"召回率: {comp1.get('recall', 0):.1f}% → {comp2.get('recall', 0):.1f}% "
              f"({recall_improvement:+.1f}%)")

        # 评估改进等级
        if coverage_improvement > 50:
            rating = "⭐⭐⭐⭐⭐ 显著提升"
        elif coverage_improvement > 30:
            rating = "⭐⭐⭐⭐ 很大提升"
        elif coverage_improvement > 10:
            rating = "⭐⭐⭐ 明显提升"
        elif coverage_improvement > 0:
            rating = "⭐⭐ 有所提升"
        else:
            rating = "⭐ 需要进一步优化"

        print(f"\n改进评级: {rating}")

    # 显示匹配详情（如果有）
    if v2_result and 'matched_pairs' in v2_result.get('comparison', {}):
        print("\n" + "=" * 80)
        print("匹配详情（V2）".center(80))
        print("=" * 80)

        pairs = v2_result['comparison']['matched_pairs']
        if pairs:
            print(f"\n共 {len(pairs)} 个匹配对:\n")
            for i, pair in enumerate(pairs[:10], 1):
                algo = pair['algorithm']
                ai = pair['zhipuai']
                sim = pair['similarity']

                print(f"{i}. 相似度: {sim:.2f}")
                print(f"   算法: [{algo.get('category', 'N/A')}] {algo.get('label', '')[:50]}")
                print(f"   AI:   [{ai.get('category', 'N/A')}] {ai.get('content', '')[:50]}")
                print()

            if len(pairs) > 10:
                print(f"... 还有 {len(pairs) - 10} 个匹配对")
        else:
            print("\n[WARNING] 没有找到匹配对")
            print("建议:")
            print("  1. 降低相似度阈值（当前：0.3）")
            print("  2. 添加Few-Shot示例")
            print("  3. 使用更强模型（glm-4-plus）")

    print("\n" + "=" * 80)


def main():
    print("\n正在加载评估结果...")

    result1, result2 = load_latest_results()

    if not result1:
        return

    display_comparison(result1, result2)


if __name__ == '__main__':
    main()
