"""
招标文件检查评估脚本 - 优化版
改进Prompt工程，提升智谱AI提取准确性
"""
import json
import os
import time
from datetime import datetime

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    print("[WARNING] 未安装PyPDF2")


def extract_pdf_text(pdf_path: str, max_chars: int = 15000) -> str:
    """从PDF文件中提取文本（增加长度限制）"""
    if not HAS_PDF:
        raise ImportError("请先安装PyPDF2")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")

    print(f"正在读取PDF文件: {pdf_path}")

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        total_pages = len(reader.pages)

        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            text += page_text

            if len(text) >= max_chars:
                text = text[:max_chars]
                print(f"  已处理 {i + 1}/{total_pages} 页（文本长度已达上限）")
                break

            if (i + 1) % 10 == 0:
                print(f"  已处理 {i + 1}/{total_pages} 页")

        print(f"[OK] 提取完成，共 {total_pages} 页，文本长度: {len(text)} 字符")
        return text


def call_zhipuai_api_with_retry(api_key: str, prompt: str, model: str = "glm-4.7", max_retries: int = 3) -> dict:
    """调用智谱AI API（带重试机制）"""
    from zhipuai import ZhipuAI

    print("\n正在调用智谱AI API...")
    print(f"使用模型: {model}")

    client = ZhipuAI(api_key=api_key)

    for retry in range(max_retries):
        try:
            print(f"尝试连接... (第{retry + 1}次)")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=8000
            )

            print("[OK] 智谱AI API调用成功")

            return {
                "content": [
                    {
                        "text": response.choices[0].message.content
                    }
                ],
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            error_str = str(e)
            print(f"[WARNING] API调用错误: {error_str[:100]}")

            if retry < max_retries - 1:
                wait_time = (retry + 1) * 3
                print(f"  等待{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] 智谱AI API调用失败")
            continue

    return None


def parse_zhipuai_checkpoints(response: dict) -> list:
    """解析智谱AI返回的检查点"""
    try:
        content = response.get("content", [{}])[0].get("text", "")

        # 尝试提取JSON部分
        json_start = content.find('{')
        json_end = content.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            data = json.loads(json_str)
            return data.get("checkpoints", [])
        else:
            print("[WARNING] 未找到JSON格式的检查点")
            return []
    except Exception as e:
        print(f"[ERROR] 解析响应失败: {e}")
        return []


def extract_algorithm_checkpoints(response_file: str) -> list:
    """从算法响应中提取检查点"""
    with open(response_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    checkpoints = []

    def extract_recursive(items, parent_category=""):
        for item in items:
            if item.get('id'):
                checkpoints.append({
                    'id': item['id'],
                    'category': parent_category,
                    'label': item.get('label', ''),
                    'value': item.get('value', ''),
                    'location': item.get('location'),
                    'resultConclusion': item.get('resultConclusion')
                })

            if item.get('children'):
                current_category = item.get('label', parent_category)
                extract_recursive(item['children'], current_category)

    if data.get('code') == 200:
        extract_recursive(data.get('data', []))

    return checkpoints


def calculate_text_similarity(text1: str, text2: str) -> float:
    """计算文本相似度（基于余弦相似度）"""
    from collections import Counter

    # 简单的词频向量
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    # Jaccard相似度
    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def compare_checkpoints_improved(algorithm_checkpoints: list, zhipuai_checkpoints: list) -> dict:
    """改进的检查点对比算法"""
    print("\n" + "=" * 60)
    print("检查点对比分析（改进版）")
    print("=" * 60)

    algo_count = len(algorithm_checkpoints)
    zhipuai_count = len(zhipuai_checkpoints)

    print(f"\n[STATS] 统计信息:")
    print(f"  算法提取: {algo_count} 个检查点")
    print(f"  智谱AI提取: {zhipuai_count} 个检查点")

    # 显示算法检查点
    print(f"\n[INFO] 算法提取的检查点:")
    for i, cp in enumerate(algorithm_checkpoints[:5], 1):
        category = cp.get('category', 'N/A')
        label = cp.get('label', 'N/A')[:60]
        print(f"  {i}. [{category}] {label}")
    if algo_count > 5:
        print(f"  ... 还有 {algo_count - 5} 个")

    # 显示智谱AI检查点
    print(f"\n[AI] 智谱AI提取的检查点:")
    for i, cp in enumerate(zhipuai_checkpoints[:5], 1):
        category = cp.get('category', 'N/A')
        content = cp.get('content', 'N/A')[:60]
        print(f"  {i}. [{category}] {content}")
    if zhipuai_count > 5:
        print(f"  ... 还有 {zhipuai_count - 5} 个")

    # 改进的匹配算法
    print(f"\n[SEARCH] 相似度分析:")

    matched_pairs = []
    threshold = 0.3  # 相似度阈值

    for algo_cp in algorithm_checkpoints:
        algo_label = algo_cp.get('label', '')
        algo_value = algo_cp.get('value', '')
        algo_text = f"{algo_label} {algo_value}".lower()

        best_match = None
        best_similarity = 0.0

        for zhipuai_cp in zhipuai_checkpoints:
            zhipuai_content = zhipuai_cp.get('content', '').lower()
            zhipuai_category = zhipuai_cp.get('category', '').lower()

            # 计算相似度
            similarity = calculate_text_similarity(algo_text, zhipuai_content)

            # 类别匹配加分
            algo_category = algo_cp.get('category', '').lower()
            if algo_category and zhipuai_category:
                if algo_category in zhipuai_content or zhipuai_category in algo_text:
                    similarity += 0.1

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = zhipuai_cp

        if best_similarity >= threshold and best_match:
            matched_pairs.append({
                'algorithm': algo_cp,
                'zhipuai': best_match,
                'similarity': best_similarity
            })

    # 详细显示匹配结果
    if matched_pairs:
        print(f"\n  匹配对 (阈值={threshold}):")
        for i, pair in enumerate(matched_pairs[:5], 1):
            algo_label = pair['algorithm']['label'][:50]
            zhipuai_content = pair['zhipuai']['content'][:50]
            similarity = pair['similarity']
            print(f"  {i}. 相似度={similarity:.2f}")
            print(f"     算法: {algo_label}")
            print(f"     AI:   {zhipuai_content}")
        if len(matched_pairs) > 5:
            print(f"  ... 还有 {len(matched_pairs) - 5} 个")

    matched = len(matched_pairs)
    coverage = (matched / zhipuai_count * 100) if zhipuai_count > 0 else 0
    recall = (matched / algo_count * 100) if algo_count > 0 else 0

    print(f"\n  总匹配对: {matched}")
    print(f"  覆盖率: {coverage:.1f}%")
    print(f"  召回率: {recall:.1f}%")

    return {
        'algorithm_count': algo_count,
        'claude_count': zhipuai_count,
        'matched': matched,
        'coverage': coverage,
        'recall': recall,
        'matched_pairs': matched_pairs
    }


def main():
    """主函数"""
    print("=" * 80)
    print("招标文件检查评估 - 智谱AI（优化Prompt）".center(80))
    print("=" * 80)

    # 1. 读取配置
    try:
        import yaml
        with open('./test_data/evaluation/evaluation_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        api_key = config.get('zhipuai_api_key', '') or config.get('claude_api_key', '')
    except:
        api_key = os.getenv('ZHIPUAI_API_KEY', '') or os.getenv('CLAUDE_API_KEY', '')

    if not api_key:
        print("\n[ERROR] 未找到智谱AI API密钥")
        return

    # 2. 读取招标文件
    try:
        import yaml
        with open('./test_data/bid_check_workflow.yaml', 'r', encoding='utf-8') as f:
            workflow_config = yaml.safe_load(f)

        pdf_path = workflow_config.get('zb_upload', {}).get('files', {}).get('file', '')

        if not pdf_path or not os.path.exists(pdf_path):
            print(f"\n[ERROR] 招标文件不存在: {pdf_path}")
            return

        document_text = extract_pdf_text(pdf_path, max_chars=15000)

    except Exception as e:
        print(f"\n[ERROR] 读取PDF失败: {e}")
        return

    # 3. 改进的Prompt
    prompt = f"""你是一个招标文件评审专家。请仔细分析以下招标文件内容，提取所有具体的检查点和评审要求。

招标文件内容（前15000字符）：
```
{document_text}
```

请以JSON格式返回检查点，格式如下：
```json
{{
  "checkpoints": [
    {{
      "id": "唯一编号",
      "category": "具体分类名称（如：封面检查、资格要求、人员要求(6分)、企业业绩(8分)、技术方案等）",
      "label": "检查项的简短描述（保持原文表述）",
      "content": "详细的检查要求说明",
      "importance": "高/中/低",
      "score": "分值（如果有）"
    }}
  ]
}}
```

**提取要求：**
1. **细粒度提取**：尽量保持原文的具体表述，不要过度概括
2. **保留原文术语**：使用招标文件中的原始术语和分类名称
3. **提取所有评分项**：包括形式评审、资格评审、技术评审、商务评审等各个部分
4. **包含分值信息**：如果检查项有分值，请标注
5. **数量控制**：提取主要检查点（10-20个）
6. **只返回JSON**：不要其他解释文字

**分类参考**：
- 封面检查、签字盖章
- 报价唯一性、资格要求
- 人员要求、企业业绩、企业资质
- 技术方案、服务承诺
- 履约能力、财务状况等

请开始提取："""

    zhipuai_response = call_zhipuai_api_with_retry(api_key, prompt)

    if not zhipuai_response:
        print("\n[TIP] API调用失败")
        return

    zhipuai_checkpoints = parse_zhipuai_checkpoints(zhipuai_response)

    if not zhipuai_checkpoints:
        print("\n[WARNING] 未能提取到检查点")
        return

    print(f"\n[OK] 智谱AI提取了 {len(zhipuai_checkpoints)} 个检查点")

    # 4. 加载算法结果
    responses_dir = './test_data/evaluation/responses'
    files = [f for f in os.listdir(responses_dir) if f.startswith('check_point_response_')]

    if not files:
        print("\n[WARNING] 未找到算法响应文件")
        return

    files.sort(reverse=True)
    latest_file = os.path.join(responses_dir, files[0])

    print(f"\n[OK] 加载算法响应: {files[0]}")
    algorithm_checkpoints = extract_algorithm_checkpoints(latest_file)

    # 5. 改进的对比分析
    result = compare_checkpoints_improved(algorithm_checkpoints, zhipuai_checkpoints)

    # 6. 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f'./test_data/evaluation/results/claude_comparison_v2_{timestamp}.json'

    os.makedirs(os.path.dirname(result_file), exist_ok=True)

    output = {
        'timestamp': timestamp,
        'algorithm_checkpoints': algorithm_checkpoints,
        'zhipuai_checkpoints': zhipuai_checkpoints,
        'comparison': result
    }

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 评估结果已保存: {result_file}")

    # 7. 总结
    print("\n" + "=" * 80)
    print("评估总结".center(80))
    print("=" * 80)
    print(f"""
[STATS] 评估结果:
  - 算法提取: {result['algorithm_count']} 个
  - 智谱AI提取: {result['claude_count']} 个
  - 匹配检查点: {result['matched']} 个
  - 覆盖率: {result['coverage']:.1f}%
  - 召回率: {result['recall']:.1f}%

[FILE] 详细结果: {result_file}
    """)


if __name__ == '__main__':
    main()
