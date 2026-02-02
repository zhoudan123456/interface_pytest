"""
招标文件检查点解析快速验证脚本
用途：2小时内验证整个测试方案的可行性

使用方法：
1. 使用示例数据（演示模式）：
   python scripts/quick_verify.py

2. 使用自己的数据：
   python scripts/quick_verify.py <annotation.xlsx> <algorithm_result.json>

3. 指定输出文件：
   python scripts/quick_verify.py <annotation.xlsx> <algorithm_result.json> <output.md>
"""
import json
import sys
import os
import pandas as pd
from rapidfuzz import fuzz, process
from datetime import datetime

class QuickVerifier:
    """快速验证工具"""

    def __init__(self, annotation_file, algorithm_result_file):
        """
        初始化验证工具

        Args:
            annotation_file: Excel标注文件路径
            algorithm_result_file: 算法结果JSON文件路径
        """
        self.annotation_file = annotation_file
        self.algorithm_result_file = algorithm_result_file
        self.ground_truth = []
        self.algorithm_result = []

    def load_annotation(self):
        """加载Excel标注数据"""
        print("[1/4] Loading annotation data...")

        try:
            df = pd.read_excel(self.annotation_file, sheet_name='检查点标注')
            df = df[df['检查点文本'].notna()]  # 过滤空行

            self.ground_truth = []
            for idx, row in df.iterrows():
                self.ground_truth.append({
                    'checkpoint_id': row['检查点ID'],
                    'text': row['检查点文本'],
                    'category': row['类别'],
                    'page': row['页码'],
                    'is_required': row['是否必需']
                })

            print(f"  Loaded {len(self.ground_truth)} checkpoints from annotation")
            return True
        except Exception as e:
            print(f"  Error loading annotation: {e}")
            return False

    def load_algorithm_result(self):
        """加载算法结果"""
        print("[2/4] Loading algorithm result...")

        try:
            with open(self.algorithm_result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 提取所有检查点（递归遍历树形结构）
            def extract_checkpoints(node_list, parent_label=""):
                checkpoints = []
                for node in node_list:
                    if node.get('id'):  # 有ID的是叶子节点
                        checkpoints.append({
                            'id': node['id'],
                            'value': node['value'],
                            'label': node['label'],
                            'category': parent_label
                        })
                    if node.get('children'):
                        checkpoints.extend(
                            extract_checkpoints(node['children'], node.get('label', ''))
                        )
                return checkpoints

            self.algorithm_result = extract_checkpoints(data.get('data', []))
            print(f"  Loaded {len(self.algorithm_result)} checkpoints from algorithm")
            return True
        except Exception as e:
            print(f"  Error loading algorithm result: {e}")
            return False

    def match_checkpoints(self, threshold=0.85, use_containment=True):
        """匹配检查点

        Args:
            threshold: 文本相似度阈值 (0-1)
            use_containment: 是否使用包含关系匹配（处理粒度不一致问题）
        """
        print("[3/4] Matching checkpoints...")
        if use_containment:
            print("  Mode: Hierarchical matching (similarity + containment)")

        tp = []  # True Positive
        fp = []  # False Positive
        fn = []  # False Negative

        matched_algo = set()

        # 对每个人工标注的检查点，在算法结果中寻找最佳匹配
        for gt_checkpoint in self.ground_truth:
            gt_text = gt_checkpoint['text']
            gt_id = gt_checkpoint['checkpoint_id']

            # 使用模糊匹配
            matches = process.extract(
                gt_text,
                [algo['value'] for algo in self.algorithm_result],
                scorer=fuzz.token_sort_ratio,
                limit=1
            )

            is_matched = False
            match_type = None
            similarity_score = 0

            # 方法1: 高相似度匹配（完全一致）
            if matches and matches[0][1] >= threshold * 100:
                is_matched = True
                match_type = 'exact'
                similarity_score = matches[0][1]
                best_match_idx = matches[0][2]
                matched_checkpoint = self.algorithm_result[best_match_idx]

            # 方法2: 包含关系匹配（处理粒度不一致）
            elif use_containment:
                for idx, algo_checkpoint in enumerate(self.algorithm_result):
                    algo_text = algo_checkpoint['value']

                    # 检查人工标注是否包含在算法输出中（粗→细）
                    if gt_text in algo_text:
                        # 计算包含度
                        containment_ratio = len(gt_text) / len(algo_text)
                        if containment_ratio <= 0.8:  # 人工标注明显较短，是算法输出的子集
                            is_matched = True
                            match_type = 'contained'
                            similarity_score = 100  # 包含关系视为100%匹配
                            best_match_idx = idx
                            matched_checkpoint = algo_checkpoint
                            break

                    # 检查算法输出是否包含在人工标注中（细→粗）
                    elif algo_text in gt_text:
                        is_matched = True
                        match_type = 'contains'
                        similarity_score = 100
                        best_match_idx = idx
                        matched_checkpoint = algo_checkpoint
                        break

            if is_matched:
                tp.append({
                    'gt_id': gt_id,
                    'gt_text': gt_text,
                    'algo_text': matched_checkpoint['value'],
                    'similarity': similarity_score / 100,
                    'match_type': match_type
                })
                matched_algo.add(best_match_idx)
                print(f"  Matched: {gt_id} (type: {match_type}, similarity: {similarity_score:.1f}%)")
            else:
                fn.append({
                    'gt_id': gt_id,
                    'gt_text': gt_text,
                    'category': gt_checkpoint['category']
                })
                print(f"  Missed: {gt_id}")

        # 算法识别出但人工没有标注的 = 误报
        for i, algo_checkpoint in enumerate(self.algorithm_result):
            if i not in matched_algo:
                fp.append({
                    'algo_text': algo_checkpoint['value'],
                    'algo_label': algo_checkpoint['label']
                })

        # 计算指标
        tp_count = len(tp)
        fp_count = len(fp)
        fn_count = len(fn)

        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
        recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        miss_rate = fn_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0

        metrics = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'miss_rate': miss_rate,
            'tp': tp_count,
            'fp': fp_count,
            'fn': fn_count,
            'total_gt': tp_count + fn_count,
            'total_algo': tp_count + fp_count
        }

        return tp, fp, fn, metrics

    def generate_report(self, tp, fp, fn, metrics, output_file):
        """生成测试报告"""
        print("[4/4] Generating report...")

        report = f"""# 招标文件检查点解析快速验证报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、测试概要

| 项目 | 数值 |
|------|------|
| 人工标注检查点数 | {metrics['total_gt']} 个 |
| 算法识别检查点数 | {metrics['total_algo']} 个 |
| 正确识别数 | {metrics['tp']} 个 |
| 遗漏数 | {metrics['fn']} 个 |
| 误报数 | {metrics['fp']} 个 |

---

## 二、核心指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **遗漏率 (Miss Rate)** | **{metrics['miss_rate']:.1%}** | {metrics['fn']}个检查点未被识别 |
| 召回率 (Recall) | {metrics['recall']:.1%} | 正确识别 {metrics['tp']}/{metrics['total_gt']} 个 |
| 精确率 (Precision) | {metrics['precision']:.1%} | {metrics['fp']}个误报 |
| F1-Score | {metrics['f1_score']:.1%} | 综合评估指标 |

---

## 三、正确识别的检查点 (True Positives: {len(tp)}个)

"""

        # 添加TP详情
        for i, item in enumerate(tp, 1):
            match_type_zh = {
                'exact': '完全匹配',
                'contained': '包含匹配（算法包含人工）',
                'contains': '包含匹配（人工包含算法）'
            }.get(item.get('match_type', 'exact'), '未知')

            report += f"""
### TP-{i:03d}
- **人工标注**: {item['gt_id']}
- **人工文本**: {item['gt_text']}
- **算法文本**: {item['algo_text']}
- **匹配类型**: {match_type_zh}
- **相似度**: {item['similarity']:.1%}
"""

        # 添加FN详情
        report += f"\n---\n\n## 四、遗漏的检查点 (False Negatives: {len(fn)}个)\n"

        if fn:
            for i, item in enumerate(fn, 1):
                report += f"""
### FN-{i:03d}
- **人工标注**: {item['gt_id']}
- **检查点文本**: {item['gt_text']}
- **类别**: {item['category']}
- **可能原因**: 算法未识别出此检查点
"""
        else:
            report += "\n无遗漏！\n"

        # 添加FP详情
        report += f"\n---\n\n## 五、误报的检查点 (False Positives: {len(fp)}个)\n"

        if fp:
            for i, item in enumerate(fp, 1):
                report += f"""
### FP-{i:03d}
- **算法识别**: {item['algo_label']}
- **检查点文本**: {item['algo_text']}
- **可能原因**: 算法误识别或人工未标注
"""
        else:
            report += "\n无误报！\n"

        # 添加结论和建议
        report += f"""

---

## 六、结论与建议

### 6.1 验证结论
"""

        if metrics['miss_rate'] <= 0.1:
            report += f"- 遗漏率为 {metrics['miss_rate']:.1%}，表现优秀（≤10%）\n"
        elif metrics['miss_rate'] <= 0.2:
            report += f"- 遗漏率为 {metrics['miss_rate']:.1%}，表现良好（10%-20%）\n"
        else:
            report += f"- 遗漏率为 {metrics['miss_rate']:.1%}，需要优化（>20%）\n"

        if metrics['precision'] >= 0.9:
            report += f"- 精确率为 {metrics['precision']:.1%}，误报率低\n"
        elif metrics['precision'] >= 0.7:
            report += f"- 精确率为 {metrics['precision']:.1%}，误报率可接受\n"
        else:
            report += f"- 精确率为 {metrics['precision']:.1%}，误报率较高\n"

        report += f"""
### 6.2 改进建议
"""

        if fn:
            report += f"""
1. **减少遗漏**（优先级最高）
   - 分析遗漏的 {len(fn)} 个检查点的共同特征
   - 补充相应的识别规则或训练样本
   - 重点关注的类别: {', '.join(set([item['category'] for item in fn]))}
"""

        if fp:
            report += f"""
2. **降低误报**
   - 分析误报的 {len(fp)} 个检查点，判断是否为真实检查点
   - 如果是误报，调整识别算法阈值
   - 如果是人工遗漏，补充到标注数据中
"""

        report += f"""
3. **下一步行动**
   - 扩大测试样本到 10-20 份文件
   - 细化检查点分类体系
   - 建立标注质量检查流程
   - 实现自动化测试流程

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"  Report saved to: {output_file}")
        print(f"\n{'='*60}")
        print(f"Validation completed!")
        print(f"  Miss Rate: {metrics['miss_rate']:.1%}")
        print(f"  Recall: {metrics['recall']:.1%}")
        print(f"  Precision: {metrics['precision']:.1%}")
        print(f"  F1-Score: {metrics['f1_score']:.1%}")
        print(f"{'='*60}\n")

        return True

    def run(self, output_file='validation_report.md'):
        """执行完整验证流程"""
        print("\n" + "="*60)
        print("Quick Verification Tool for Checkpoint Parsing")
        print("="*60 + "\n")

        # 加载数据
        if not self.load_annotation():
            return False

        if not self.load_algorithm_result():
            return False

        # 匹配检查点
        tp, fp, fn, metrics = self.match_checkpoints()

        # 生成报告
        return self.generate_report(tp, fp, fn, metrics, output_file)


def main():
    """主函数 - 支持命令行参数"""

    # 检查是否提供了命令行参数
    if len(sys.argv) >= 3:
        # 使用用户提供的数据
        annotation_file = sys.argv[1]
        algorithm_result_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) >= 4 else 'outputs/validation_report.md'

        print(f"Using your data:")
        print(f"  Annotation: {annotation_file}")
        print(f"  Algorithm result: {algorithm_result_file}")
        print()

        verifier = QuickVerifier(annotation_file, algorithm_result_file)
        verifier.run(output_file)

        return

    # 没有提供参数 - 使用示例数据（演示模式）
    print("="*60)
    print("Demo Mode: Using sample data")
    print("="*60)
    print("\nTo use your own data, run:")
    print("  python scripts/quick_verify.py <annotation.xlsx> <algorithm_result.json>")
    print()

    # 1. 创建示例标注数据（如果没有真实标注）
    print("Creating sample annotation data...")

    annotation_data = {
        '检查点标注': [
            {'序号': 1, '检查点ID': 'CP-001', '检查点文本': '投标文件未按磋商文件要求盖章或签字(签章)',
             '类别': '响应性评审', '页码': 29, '是否必需': '是', '备注': ''},
            {'序号': 2, '检查点ID': 'CP-002', '检查点文本': '总报价不超过项目(分包)预算金额或最高限价',
             '类别': '响应性评审', '页码': 29, '是否必需': '是', '备注': ''},
            {'序号': 3, '检查点ID': 'CP-003', '检查点文本': '满足《中华人民共和国政府采购法》第二十二条规定',
             '类别': '资格评审', '页码': 4, '是否必需': '是', '备注': ''},
        ]
    }

    df = pd.DataFrame(annotation_data['检查点标注'])
    df.to_excel('d:/python_project/ai_test/data/sample_annotation.xlsx', index=False, sheet_name='检查点标注')
    print("  Sample annotation saved to: data/sample_annotation.xlsx")

    # 2. 创建示例算法结果（基于你提供的JSON）
    print("\nCreating sample algorithm result...")
    algorithm_result = {
        "code": 200,
        "msg": None,
        "data": [
            {
                "id": None,
                "label": "响应性评审",
                "value": "响应性评审",
                "location": None,
                "resultConclusion": None,
                "children": [
                    {
                        "id": None,
                        "label": "符合性检查",
                        "value": "符合性检查",
                        "children": [
                            {"id": 4353, "label": "响应文件编制：未按磋商文件要求盖章或签字(签章)",
                             "value": "响应文件编制：未按磋商文件要求盖章或签字(签章)",
                             "location": "{}", "resultConclusion": None, "children": []},
                            {"id": 4350, "label": "磋商报价：报价不存在缺项、漏项",
                             "value": "磋商报价：报价不存在缺项、漏项",
                             "location": "{}", "resultConclusion": None, "children": []},
                            {"id": 4349, "label": "磋商报价：总报价不超过项目(分包)预算金额或最高限价",
                             "value": "磋商报价：总报价不超过项目(分包)预算金额或最高限价",
                             "location": "{}", "resultConclusion": None, "children": []},
                        ]
                    }
                ]
            },
            {
                "id": None,
                "label": "资格评审",
                "value": "资格评审",
                "children": [
                    {
                        "id": None,
                        "label": "资格审查",
                        "value": "资格审查",
                        "children": [
                            {"id": 4343, "label": "满足《中华人民共和国政府采购法》第二十二条规定：提供孝昌县政府采购供应商资格信用承诺函（格式详见第六章）。",
                             "value": "满足《中华人民共和国政府采购法》第二十二条规定：提供孝昌县政府采购供应商资格信用承诺函（格式详见第六章）。",
                             "location": "{}", "resultConclusion": None, "children": []},
                        ]
                    }
                ]
            }
        ]
    }

    with open('d:/python_project/ai_test/data/sample_algorithm_result.json', 'w', encoding='utf-8') as f:
        json.dump(algorithm_result, f, ensure_ascii=False, indent=2)
    print("  Sample algorithm result saved to: data/sample_algorithm_result.json")

    # 3. 执行验证
    print("\n" + "="*60)
    print("Starting validation with sample data...")
    print("="*60 + "\n")

    verifier = QuickVerifier(
        annotation_file='d:/python_project/ai_test/data/sample_annotation.xlsx',
        algorithm_result_file='d:/python_project/ai_test/data/sample_algorithm_result.json'
    )

    verifier.run(output_file='d:/python_project/ai_test/outputs/validation_report.md')

    print("\nNext steps:")
    print("1. Review the validation report: outputs/validation_report.md")
    print("2. Replace sample data with your real annotation")
    print("3. Run again with your data")
    print("\nTo use with your own data:")
    print("  python scripts/quick_verify.py <annotation.xlsx> <algorithm_result.json>")


if __name__ == '__main__':
    main()
