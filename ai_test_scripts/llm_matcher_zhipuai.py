"""
使用大模型API进行语义匹配（支持智谱AI）
优势：理解语义，处理措辞差异，对格式差异鲁棒
"""

import json
import pandas as pd
import os
from datetime import datetime


class ZhipuAILMMatcher:
    """使用智谱AI进行检查点匹配"""

    def __init__(self, api_key=None, model="glm-4-flash"):
        """
        初始化智谱AI匹配器

        Args:
            api_key: 智谱AI API key（如果不提供，从环境变量ZHIPUAI_API_KEY或.env文件读取）
            model: 模型名称（默认：glm-4-flash，快速且便宜）
        """
        # 尝试从 .env 文件加载环境变量
        try:
            from dotenv import load_dotenv
            # 查找项目根目录的 .env 文件
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_file = os.path.join(script_dir, '.env')
            print(f"[DEBUG] Looking for .env at: {env_file}")
            if os.path.exists(env_file):
                load_dotenv(env_file, override=True)  # override=True 确保覆盖已存在的变量
                print(f"[OK] Loaded environment variables from .env file")
            else:
                print(f"[WARNING] .env file not found at: {env_file}")
        except ImportError:
            print("[WARNING] python-dotenv not installed")
            pass  # 如果没有安装 python-dotenv，跳过

        # 获取API key
        if not api_key:
            api_key = os.getenv('ZHIPUAI_API_KEY')
            print(f"[DEBUG] ZHIPUAI_API_KEY from env: {'Found' if api_key else 'Not found'}")

        if not api_key:
            raise ValueError("API key not found. Please set ZHIPUAI_API_KEY environment variable or provide api_key parameter")

        self.api_key = api_key
        self.model = model

        # 导入智谱AI SDK
        try:
            from zhipuai import ZhipuAI
            self.client = ZhipuAI(api_key=api_key)
            print(f"[OK] 智谱AI客户端初始化成功，模型: {model}")
        except ImportError:
            raise ImportError("请安装智谱AI SDK: pip install zhipuai")

    def check_if_contained(self, checkpoint_text, algorithm_output, algo_id):
        """
        使用智谱AI判断检查点是否包含在算法输出中

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

【输出格式】（严格按照JSON格式输出，不要输出其他内容）
{{
    "is_contained": true或false,
    "confidence": 0.0到1.0之间的数字,
    "reasoning": "简短说明判断理由",
    "matched_segment": "算法输出中对应的片段（如果匹配）"
}}

请只输出JSON，不要输出其他内容。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,  # glm-4-flash (快速且便宜)
                messages=[
                    {"role": "system", "content": "你是一个招标文件检查点匹配专家，擅长语义理解和文本匹配。只输出JSON格式。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # 使用低温度以获得稳定结果
                max_tokens=500
            )

            # 提取响应
            content = response.choices[0].message.content.strip()

            # 尝试解析JSON
            # 移除可能的markdown代码块标记
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()

            # 处理可能的JSON格式问题
            content = content.replace('true', 'true').replace('false', 'false')

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

    def match_all_checkpoints(self, annotation_file, algorithm_result_file, output_file=None):
        """
        匹配所有检查点

        Args:
            annotation_file: Excel标注文件路径
            algorithm_result_file: 算法结果JSON文件路径
            output_file: 输出报告路径（可选，默认自动生成）
        """
        # 自动生成输出文件名
        if output_file is None:
            import pathlib
            excel_basename = pathlib.Path(annotation_file).stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'outputs/{excel_basename}_validation_{timestamp}.md'

        # 确保 outputs 目录存在
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

        print("="*80)
        print("智谱AI语义匹配 - 检查点匹配验证")
        print("="*80)
        print()

        # 1. 加载数据
        print("[1/4] Loading data...")
        print(f"  [DEBUG] Annotation file: {annotation_file}")
        print(f"  [DEBUG] Algorithm result file: {algorithm_result_file}")
        print(f"  [DEBUG] Output file: {output_file}")
        print(f"  [DEBUG] Annotation file exists: {os.path.exists(annotation_file)}")
        print(f"  [DEBUG] Algorithm file exists: {os.path.exists(algorithm_result_file)}")

        try:
            df = pd.read_excel(annotation_file, sheet_name='检查点标注', engine='openpyxl')
            df = df[df['检查点文本'].notna()]
            checkpoints = df.to_dict('records')
            print(f"  Loaded {len(checkpoints)} checkpoints from annotation")
        except Exception as e:
            print(f"  Error loading annotation: {e}")
            import traceback
            traceback.print_exc()
            return False

        try:
            with open(algorithm_result_file, 'r', encoding='utf-8') as f:
                algo_data = json.load(f)

            # 构建类别到节点的映射（基于层级的智能匹配）
            def build_category_mapping(node_list, category_path=""):
                """
                递归构建类别映射（使用顶级类别）
                返回: {top_level_category: [nodes_with_id]}

                Args:
                    node_list: 节点列表
                    category_path: 当前的类别路径（如 "资格评审 > 资格要求"）
                """
                category_map = {}

                for node in node_list:
                    current_label = node.get('label', '')

                    # 构建当前节点的完整路径
                    if category_path:
                        current_path = f"{category_path} > {current_label}" if current_label else category_path
                    else:
                        current_path = current_label

                    # 当前节点有id，是叶子节点（实际检查点）
                    if node.get('id') is not None:
                        # 提取顶级类别（路径的第一级）
                        if ' > ' in current_path:
                            top_level_category = current_path.split(' > ')[0]
                        else:
                            top_level_category = current_path

                        if top_level_category not in category_map:
                            category_map[top_level_category] = []

                        category_map[top_level_category].append({
                            'id': node['id'],
                            'value': node['value'],
                            'label': node['label'],
                            'top_level_category': top_level_category
                        })

                    # 递归处理子节点
                    if node.get('children'):
                        child_map = build_category_mapping(node['children'], current_path)

                        # 合并类别映射
                        for cat, nodes in child_map.items():
                            if cat not in category_map:
                                category_map[cat] = []
                            category_map[cat].extend(nodes)

                return category_map

            # 构建类别映射
            category_mapping = build_category_mapping(algo_data.get('data', []))

            # 提取所有节点（用于误报检测）
            def extract_all_nodes(node_list):
                results = []
                for node in node_list:
                    if node.get('id') is not None:
                        results.append({
                            'id': node['id'],
                            'value': node['value'],
                            'label': node['label']
                        })
                    if node.get('children'):
                        results.extend(extract_all_nodes(node['children']))
                return results

            all_algo_nodes = extract_all_nodes(algo_data.get('data', []))

            # 打印类别统计
            print(f"  Loaded {len(all_algo_nodes)} checkpoints from algorithm")
            print(f"  Found {len(category_mapping)} categories:")
            for cat, nodes in category_mapping.items():
                print(f"    - '{cat}': {len(nodes)} nodes")

        except Exception as e:
            print(f"  Error loading algorithm result: {e}")
            import traceback
            traceback.print_exc()
            return False

        print()

        # 2. 使用智谱AI进行匹配（基于类别）
        print("[2/4] Matching checkpoints with 智谱AI...")
        print(f"  Model: {self.model}")
        print(f"  Total checkpoints to match: {len(checkpoints)}")
        print(f"  Matching strategy: Category-based matching")
        print()

        tp = []  # True Positives
        fp = []  # False Positives
        fn = []  # False Negatives
        matched_algo_ids = set()

        for i, checkpoint in enumerate(checkpoints, 1):
            checkpoint_id = checkpoint['检查点ID']
            checkpoint_text = checkpoint['检查点文本']
            category = checkpoint.get('类别', '')  # 从Excel读取的类别

            print(f"[{i}/{len(checkpoints)}] Processing {checkpoint_id}")
            print(f"  Category: {category}")
            print(f"  Text: {checkpoint_text[:60]}...")

            # 获取该类别下的所有算法节点
            category_nodes = category_mapping.get(category, [])

            if not category_nodes:
                print(f"  [WARNING] No nodes found for category '{category}', will search all nodes")
                category_nodes = all_algo_nodes

            print(f"  Searching in {len(category_nodes)} nodes under category '{category}'...")

            # 对该类别下的节点进行匹配检查
            is_matched = False
            best_match = None

            for algo_checkpoint in category_nodes:
                algo_id = algo_checkpoint['id']
                algo_text = algo_checkpoint['value']

                # 调用智谱AI进行判断
                print(f"    Checking algo #{algo_id}...", end=" ")
                result = self.check_if_contained(checkpoint_text, algo_text, algo_id)

                if result['is_contained']:
                    is_matched = True
                    best_match = {
                        'checkpoint_id': checkpoint_id,
                        'checkpoint_text': checkpoint_text,
                        'category': category,
                        'algo_id': algo_id,
                        'algo_text': algo_text,
                        'confidence': result['confidence'],
                        'reasoning': result['reasoning'],
                        'matched_segment': result['matched_segment']
                    }
                    # 记录匹配关系（用于统计）
                    matched_algo_ids.add(algo_id)
                    print(f"[OK] MATCHED (confidence: {result['confidence']:.2f})")
                    print(f"  Reason: {result['reasoning']}")
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
        for algo_checkpoint in all_algo_nodes:
            algo_id = algo_checkpoint['id']
            if algo_id not in matched_algo_ids:
                fp.append({
                    'algo_id': algo_id,
                    'algo_label': algo_checkpoint['label'],
                    'algo_text': algo_checkpoint['value']
                })

        print(f"  Found {len(fp)} false positives")
        print()

        # 4. 生成报告
        print("[4/4] Generating report...")
        self._generate_report(tp, fp, fn, output_file)

        return output_file  # 返回最终的输出文件路径

    def _generate_report(self, tp, fp, fn, output_file):
        """生成匹配报告"""
        tp_count = len(tp)
        fp_count = len(fp)
        fn_count = len(fn)

        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
        recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        miss_rate = fn_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0

        report = f"""# 招标文件检查点解析验证报告（智谱AI语义匹配）

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**匹配方法**: 智谱AI语义匹配（{self.model}）

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
            category = item.get('category', 'N/A')
            report += f"""
### TP-{i:03d}
- **人工标注**: {item['checkpoint_id']}
- **类别**: {category}
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
   - **基于类别的智能匹配**: 根据Excel中的"类别"字段，只在JSON对应的分类下查找
   - **语义理解**: 使用智谱AI理解语义，而非字面匹配
   - **处理粒度差异**: 可以处理算法输出（粗粒度）vs 人工标注（细粒度）的情况
   - **措辞鲁棒性**: 允许同义词、句式变化等

2. **成本与效率**
   - 模型：{self.model}（快速且便宜）
   - 匹配策略：类别过滤 + LLM判断，减少不必要的API调用
   - 预估成本：每100个检查点约¥0.01

3. **下一步行动**
   - 扩大测试样本验证效果
   - 根据匹配结果优化提示词
   - 考虑使用更大的模型（如glm-4-plus）提高准确率

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
    if len(sys.argv) < 3:
        print("Usage: python scripts/llm_matcher_zhipuai.py <annotation.xlsx> <algorithm_result.json> [output.md]")
        print()
        print("Environment variables (alternative):")
        print("  set ZHIPUAI_API_KEY=your-api-key")
        print("  python scripts/llm_matcher_zhipuai.py annotations/标注.xlsx data/algorithm.json")
        print()
        print("Note: If output file is not specified, it will be auto-generated")
        print("      Format: {Excel_filename}_validation_{timestamp}.md")
        print()
        print("Get API key from: https://open.bigmodel.cn/")
        return

    annotation_file = sys.argv[1]
    algorithm_result_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None  # None = auto-generate filename

    # 创建匹配器
    try:
        matcher = ZhipuAILMMatcher()
    except ValueError as e:
        print(f"Error: {e}")
        print()
        print("Please get API key from: https://open.bigmodel.cn/")
        print("And set environment variable:")
        print("  set ZHIPUAI_API_KEY=your-api-key")
        return

    # 执行匹配
    result_file = matcher.match_all_checkpoints(annotation_file, algorithm_result_file, output_file)

    if result_file:
        print(f"\nValidation completed! Report saved to: {result_file}")
    else:
        print("\nValidation failed!")


if __name__ == '__main__':
    main()
