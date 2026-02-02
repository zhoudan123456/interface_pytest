"""
使用大模型API进行检查点语义匹配
优势：
1. 理解语义，而不仅仅是字面匹配
2. 可以处理措辞变化、同义词等问题
3. 对格式差异更鲁棒
"""

import json
import pandas as pd
import requests
from datetime import datetime
import time


class LLMMatcher:
    """使用大模型进行检查点匹配"""

    def __init__(self, api_key, api_base="https://api.openai.com/v1", model="gpt-4o-mini"):
        """
        初始化大模型匹配器

        Args:
            api_key: OpenAI API key
            api_base: API base URL（支持兼容OpenAI格式的其他服务）
            model: 使用的模型名称
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model

    def check_if_contained(self, checkpoint_text, algorithm_output, algo_id):
        """
        使用大模型判断检查点是否包含在算法输出中

        Args:
            checkpoint_text: 人工标注的检查点文本
            algorithm_output: 算法输出的文本（可能包含多个检查点）
            algo_id: 算法输出的ID

        Returns:
            dict: 包含是否匹配、置信度、推理过程
        """
        prompt = f"""你是一个招标文件检查点匹配专家。请判断以下人工标注的检查点是否包含在算法输出中。

【人工标注的检查点】
{checkpoint_text}

【算法输出】（可能包含多个检查点）
{algorithm_output}

【任务】
判断算法输出中是否包含了人工标注的检查点。考虑以下几点：
1. 语义是否相同（不要求字面完全一致）
2. 允许措辞差异、同义词替换
3. 允许算法输出包含更多信息
4. 只要核心要求一致就认为匹配

【输出格式】（严格按照JSON格式输出）
{{
    "is_contained": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "简短说明判断理由",
    "matched_segment": "算法输出中对应的片段（如果匹配）"
}}

请只输出JSON，不要输出其他内容："""

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个招标文件检查点匹配专家，擅长语义理解和文本匹配。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.0,  # 使用低温度以获得稳定结果
                    "max_tokens": 500
                },
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # 提取LLM的回复
            content = result['choices'][0]['message']['content'].strip()

            # 尝试解析JSON
            # 移除可能的markdown代码块标记
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()

            match_result = json.loads(content)

            return {
                'is_contained': match_result.get('is_contained', False),
                'confidence': match_result.get('confidence', 0.0),
                'reasoning': match_result.get('reasoning', ''),
                'matched_segment': match_result.get('matched_segment', ''),
                'algo_id': algo_id
            }

        except Exception as e:
            print(f"  API Error: {e}")
            return {
                'is_contained': False,
                'confidence': 0.0,
                'reasoning': f"API调用失败: {str(e)}",
                'matched_segment': '',
                'algo_id': algo_id
            }

    def match_all_checkpoints(self, annotation_file, algorithm_result_file, output_file):
        """
        匹配所有检查点

        Args:
            annotation_file: Excel标注文件路径
            algorithm_result_file: 算法结果JSON文件路径
            output_file: 输出报告路径
        """
        print("="*80)
        print("LLM-Based Checkpoint Matching")
        print("="*80)
        print()

        # 1. 加载数据
        print("[1/4] Loading data...")
        try:
            df = pd.read_excel(annotation_file, sheet_name='检查点标注')
            df = df[df['检查点文本'].notna()]
            checkpoints = df.to_dict('records')
            print(f"  Loaded {len(checkpoints)} checkpoints from annotation")
        except Exception as e:
            print(f"  Error loading annotation: {e}")
            return False

        try:
            with open(algorithm_result_file, 'r', encoding='utf-8') as f:
                algo_data = json.load(f)

            # 提取所有算法检查点
            def extract_all_nodes(node_list, parent_label=""):
                results = []
                for node in node_list:
                    if node.get('id'):
                        results.append({
                            'id': node['id'],
                            'value': node['value'],
                            'label': node['label']
                        })
                    if node.get('children'):
                        results.extend(extract_all_nodes(node['children'], node.get('label', '')))
                return results

            algo_checkpoints = extract_all_nodes(algo_data.get('data', []))
            print(f"  Loaded {len(algo_checkpoints)} checkpoints from algorithm")
        except Exception as e:
            print(f"  Error loading algorithm result: {e}")
            return False

        print()

        # 2. 使用LLM进行匹配
        print("[2/4] Matching checkpoints with LLM...")
        print(f"  Model: {self.model}")
        print(f"  Total checkpoints to match: {len(checkpoints)}")
        print()

        tp = []  # True Positives
        fp = []  # False Positives
        fn = []  # False Negatives
        matched_algo_indices = set()

        for i, checkpoint in enumerate(checkpoints, 1):
            checkpoint_id = checkpoint['检查点ID']
            checkpoint_text = checkpoint['检查点文本']
            category = checkpoint['类别']

            print(f"[{i}/{len(checkpoints)}] Processing {checkpoint_id}")
            print(f"  Text: {checkpoint_text[:60]}...")

            # 对每个算法检查点进行匹配检查
            is_matched = False
            best_match = None

            for j, algo_checkpoint in enumerate(algo_checkpoints):
                if j in matched_algo_indices:
                    continue  # 跳过已匹配的

                algo_text = algo_checkpoint['value']

                # 调用LLM进行判断
                print(f"  Checking against algo #{j}...", end=" ")
                result = self.check_if_contained(checkpoint_text, algo_text, algo_checkpoint['id'])

                if result['is_contained']:
                    is_matched = True
                    best_match = {
                        'checkpoint_id': checkpoint_id,
                        'checkpoint_text': checkpoint_text,
                        'algo_id': algo_checkpoint['id'],
                        'algo_text': algo_text,
                        'confidence': result['confidence'],
                        'reasoning': result['reasoning'],
                        'matched_segment': result['matched_segment']
                    }
                    matched_algo_indices.add(j)
                    print(f"[OK] MATCHED (confidence: {result['confidence']:.2f})")
                    break
                else:
                    print(f"[X] Not matched")

            if is_matched:
                tp.append(best_match)
            else:
                fn.append({
                    'checkpoint_id': checkpoint_id,
                    'checkpoint_text': checkpoint_text,
                    'category': category
                })

            print()

        # 3. 找出误报
        print("[3/4] Finding false positives...")
        for j, algo_checkpoint in enumerate(algo_checkpoints):
            if j not in matched_algo_indices:
                fp.append({
                    'algo_id': algo_checkpoint['id'],
                    'algo_label': algo_checkpoint['label'],
                    'algo_text': algo_checkpoint['value']
                })

        print(f"  Found {len(fp)} false positives")
        print()

        # 4. 生成报告
        print("[4/4] Generating report...")
        self._generate_report(tp, fp, fn, output_file)

        return True

    def _generate_report(self, tp, fp, fn, output_file):
        """生成匹配报告"""
        tp_count = len(tp)
        fp_count = len(fp)
        fn_count = len(fn)

        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
        recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        miss_rate = fn_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0

        report = f"""# 招标文件检查点解析验证报告（LLM语义匹配）

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**匹配方法**: 大模型语义匹配（{self.model}）

---

## 一、测试概要

| 项目 | 数值 |
|------|------|
| 人工标注检查点数 | {tp_count + fn_count} 个 |
| 算法识别检查点数 | {tp_count + fp_count} 个 |
| 正确识别数 | {tp_count} 个 |
| 遗漏数 | {fn_count} 个 |
| 误报数 | {fp_count} 个 |

---

## 二、核心指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **遗漏率 (Miss Rate)** | **{miss_rate:.1%}** | {fn_count}个检查点未被识别 |
| 召回率 (Recall) | {recall:.1%} | 正确识别 {tp_count}/{tp_count + fn_count} 个 |
| 精确率 (Precision) | {precision:.1%} | {fp_count}个误报 |
| F1-Score | {f1:.1%} | 综合评估指标 |

---

## 三、正确识别的检查点 (True Positives: {tp_count}个)

"""

        # 添加TP详情
        for i, item in enumerate(tp, 1):
            report += f"""
### TP-{i:03d}
- **人工标注**: {item['checkpoint_id']}
- **人工文本**: {item['checkpoint_text']}
- **算法ID**: {item['algo_id']}
- **算法文本**: {item['algo_text'][:200]}...
- **置信度**: {item['confidence']:.1%}
- **推理**: {item['reasoning']}
"""

        # 添加FN详情
        report += f"""
---

## 四、遗漏的检查点 (False Negatives: {fn_count}个)

"""

        if fn:
            for i, item in enumerate(fn, 1):
                report += f"""
### FN-{i:03d}
- **人工标注**: {item['checkpoint_id']}
- **检查点文本**: {item['checkpoint_text']}
- **类别**: {item['category']}
- **可能原因**: 算法未识别出此检查点
"""
        else:
            report += "\n无遗漏！\n"

        # 添加FP详情
        report += f"""
---

## 五、误报的检查点 (False Positives: {fp_count}个)

"""

        if fp:
            for i, item in enumerate(fp, 1):
                report += f"""
### FP-{i:03d}
- **算法ID**: {item['algo_id']}
- **算法标签**: {item['algo_label']}
- **检查点文本**: {item['algo_text'][:200]}...
- **可能原因**: 算法误识别或人工未标注
"""
        else:
            report += "\n无误报！\n"

        # 添加结论
        report += f"""
---

## 六、结论与建议

### 6.1 验证结论
"""
        if miss_rate <= 0.1:
            report += f"- 遗漏率为 {miss_rate:.1%}，表现优秀（≤10%）\n"
        elif miss_rate <= 0.2:
            report += f"- 遗漏率为 {miss_rate:.1%}，表现良好（10%-20%）\n"
        else:
            report += f"- 遗漏率为 {miss_rate:.1%}，需要优化（>20%）\n"

        if precision >= 0.9:
            report += f"- 精确率为 {precision:.1%}，误报率低\n"
        elif precision >= 0.7:
            report += f"- 精确率为 {precision:.1%}，误报率可接受\n"
        else:
            report += f"- 精确率为 {precision:.1%}，误报率较高\n"

        report += f"""
### 6.2 改进建议

1. **本方法优势**
   - 使用大模型进行语义理解，而非字面匹配
   - 可以处理措辞差异、格式变化等问题
   - 匹配更加智能和准确

2. **成本与效率**
   - 每个检查点需要调用一次LLM API
   - 建议批量处理以降低成本
   - 可考虑使用更小的模型（如gpt-4o-mini）

3. **下一步行动**
   - 扩大测试样本验证效果
   - 根据匹配结果优化提示词
   - 考虑缓存常见匹配模式

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"  Report saved to: {output_file}")
        print()
        print("="*80)
        print(f"Validation completed!")
        print(f"  Miss Rate: {miss_rate:.1%}")
        print(f"  Recall: {recall:.1%}")
        print(f"  Precision: {precision:.1%}")
        print(f"  F1-Score: {f1:.1%}")
        print("="*80)


def main():
    """使用示例"""
    import sys

    # 检查命令行参数
    if len(sys.argv) < 4:
        print("Usage: python scripts/llm_matcher.py <api_key> <annotation.xlsx> <algorithm_result.json> [output.md]")
        print()
        print("Example:")
        print("  python scripts/llm_matcher.py sk-xxx annotations/标注.xlsx data/algorithm.json outputs/report.md")
        print()
        print("Environment variables (alternative):")
        print("  set OPENAI_API_KEY=sk-xxx")
        print("  python scripts/llm_matcher.py annotations/标注.xlsx data/algorithm.json")
        return

    # 获取API key
    api_key = sys.argv[1]

    # 检查第一个参数是否是文件路径（如果包含.xlsx或.json）
    if '.xlsx' in api_key or '.json' in api_key:
        # 第一个参数是文件路径，从环境变量获取API key
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        annotation_file = sys.argv[1]
        algorithm_result_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else 'outputs/validation_report_llm.md'
    else:
        # 第一个参数是API key
        annotation_file = sys.argv[2]
        algorithm_result_file = sys.argv[3]
        output_file = sys.argv[4] if len(sys.argv) > 4 else 'outputs/validation_report_llm.md'

    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        print("Please set environment variable or provide as first argument")
        return

    # 创建匹配器
    matcher = LLMMatcher(api_key=api_key)

    # 执行匹配
    matcher.match_all_checkpoints(annotation_file, algorithm_result_file, output_file)


if __name__ == '__main__':
    main()
