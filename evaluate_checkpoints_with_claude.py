"""
招标文件检查评估脚本 - 改进版
使用智谱AI API提取检查点并与算法结果对比
"""
import json
import os
import time
from datetime import datetime

# 尝试导入PyPDF2读取PDF
try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    print("[WARNING] 未安装PyPDF2，请运行: pip install PyPDF2")


def extract_pdf_text(pdf_path: str, max_chars: int = 10000) -> str:
    """从PDF文件中提取文本（限制长度）"""
    if not HAS_PDF:
        raise ImportError("请先安装PyPDF2: pip install PyPDF2")

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

            # 检查是否达到最大长度
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

    # 初始化客户端
    client = ZhipuAI(api_key=api_key)

    for retry in range(max_retries):
        try:
            print(f"尝试连接... (第{retry + 1}次)")

            # 调用API
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

            # 返回标准化的响应格式（兼容原有代码）
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
                print(f"[ERROR] 智谱AI API调用失败，已重试{max_retries}次")
            continue

    return None


# 保留旧函数名以保持向后兼容
def call_claude_api_with_retry(api_key: str, prompt: str, model: str = "glm-4.7", max_retries: int = 3) -> dict:
    """调用智谱AI API（带重试机制）- 已废弃，请使用 call_zhipuai_api_with_retry"""
    return call_zhipuai_api_with_retry(api_key, prompt, model, max_retries)


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
            print("\n智谱AI响应预览:")
            print(content[:500] + "...")
            return []
    except Exception as e:
        print(f"[ERROR] 解析智谱AI响应失败: {e}")
        return []


# 保留旧函数名以保持向后兼容
def parse_claude_checkpoints(response: dict) -> list:
    """解析智谱AI返回的检查点 - 已废弃，请使用 parse_zhipuai_checkpoints"""
    return parse_zhipuai_checkpoints(response)


def extract_algorithm_checkpoints(response_file: str) -> list:
    """从算法响应中提取检查点"""
    with open(response_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    checkpoints = []

    def extract_recursive(items, parent_category=""):
        """递归提取检查点"""
        for item in items:
            if item.get('id'):  # 有ID的是具体检查点
                checkpoints.append({
                    'id': item['id'],
                    'category': parent_category,
                    'label': item.get('label', ''),
                    'value': item.get('value', ''),
                    'location': item.get('location'),
                    'resultConclusion': item.get('resultConclusion')
                })

            # 递归处理子项
            if item.get('children'):
                current_category = item.get('label', parent_category)
                extract_recursive(item['children'], current_category)

    if data.get('code') == 200:
        extract_recursive(data.get('data', []))

    return checkpoints


def compare_checkpoints_simple(algorithm_checkpoints: list, zhipuai_checkpoints: list) -> dict:
    """简化的检查点对比（基于关键词匹配）"""
    print("\n" + "=" * 60)
    print("检查点对比分析")
    print("=" * 60)

    algo_count = len(algorithm_checkpoints)
    zhipuai_count = len(zhipuai_checkpoints)

    print(f"\n[STATS] 统计信息:")
    print(f"  算法提取: {algo_count} 个检查点")
    print(f"  智谱AI提取: {zhipuai_count} 个检查点")

    # 显示算法检查点（前5个）
    print(f"\n[INFO] 算法提取的检查点 (显示前5个):")
    for i, cp in enumerate(algorithm_checkpoints[:5], 1):
        category = cp.get('category', 'N/A')
        label = cp.get('label', 'N/A')[:50]
        print(f"  {i}. [{category}] {label}")

    if algo_count > 5:
        print(f"  ... 还有 {algo_count - 5} 个")

    # 显示智谱AI检查点（前5个）
    print(f"\n[AI] 智谱AI提取的检查点 (显示前5个):")
    for i, cp in enumerate(zhipuai_checkpoints[:5], 1):
        category = cp.get('category', 'N/A')
        content = cp.get('content', cp.get('label', 'N/A'))[:50]
        print(f"  {i}. [{category}] {content}")

    if zhipuai_count > 5:
        print(f"  ... 还有 {zhipuai_count - 5} 个")

    # 简单匹配分析
    print(f"\n[SEARCH] 匹配分析:")
    matched = 0
    for algo_cp in algorithm_checkpoints:
        algo_label = algo_cp.get('label', '').lower()

        for zhipuai_cp in zhipuai_checkpoints:
            zhipuai_content = zhipuai_cp.get('content', zhipuai_cp.get('label', '')).lower()

            # 提取关键词进行匹配
            algo_words = set(algo_label.split())
            zhipuai_words = set(zhipuai_content.split())

            # 如果有2个以上共同词，认为匹配
            common_words = algo_words & zhipuai_words
            if len(common_words) >= 2:
                matched += 1
                break

    coverage = (matched / zhipuai_count * 100) if zhipuai_count > 0 else 0
    recall = (matched / algo_count * 100) if algo_count > 0 else 0

    print(f"  匹配检查点: {matched}")
    print(f"  覆盖率 (智谱AI中有多少被算法提取): {coverage:.1f}%")
    print(f"  召回率 (算法中有多少在智谱AI中): {recall:.1f}%")

    return {
        'algorithm_count': algo_count,
        'claude_count': zhipuai_count,  # 保持字段名兼容性
        'matched': matched,
        'coverage': coverage,
        'recall': recall
    }


def main():
    """主函数"""
    print("=" * 80)
    print("招标文件检查评估 - 智谱AI参考答案生成".center(80))
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
        print("\n请配置API密钥:")
        print("  方法1: 设置环境变量")
        print("    $env:ZHIPUAI_API_KEY=\"your-api-key\"")
        print("  方法2: 在配置文件中设置")
        print("    ./test_data/evaluation/evaluation_config.yaml")
        print("    配置项: zhipuai_api_key")
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

        # 限制文本长度为10000字符
        document_text = extract_pdf_text(pdf_path, max_chars=10000)

    except Exception as e:
        print(f"\n[ERROR] 读取PDF失败: {e}")
        print("\n[TIP] 提示: 请安装 PyPDF2: pip install PyPDF2")
        return

    # 3. 生成智谱AI检查点
    prompt = f"""你是招标文件评审专家。请分析以下招标文件内容，提取所有关键检查点。

招标文件内容（前10000字符）：
```
{document_text}
```

请以JSON格式返回检查点，格式如下：
```json
{{
  "checkpoints": [
    {{
      "category": "形式评审",
      "content": "检查封面是否完整",
      "importance": "高"
    }}
  ]
}}
```

要求：
1. 只返回JSON，不要其他解释文字
2. 提取主要的检查点（5-15个即可）
3. 按类别分组（形式评审、资格评审、技术评审等）"""

    zhipuai_response = call_zhipuai_api_with_retry(api_key, prompt)

    if not zhipuai_response:
        print("\n[TIP] 建议:")
        print("  1. 检查网络连接")
        print("  2. 验证API密钥是否正确")
        print("  3. 确认API账户有余额")
        print("  4. 可以尝试使用代理或VPN")
        return

    zhipuai_checkpoints = parse_zhipuai_checkpoints(zhipuai_response)

    if not zhipuai_checkpoints:
        print("\n[WARNING] 未能提取到智谱AI检查点，评估终止")
        return

    print(f"\n[OK] 智谱AI提取了 {len(zhipuai_checkpoints)} 个检查点")

    # 4. 加载算法结果
    responses_dir = './test_data/evaluation/responses'
    files = [f for f in os.listdir(responses_dir) if f.startswith('check_point_response_')]

    if not files:
        print("\n[WARNING] 未找到算法响应文件，跳过对比")
        print("[TIP] 请先运行: pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_05_check_check_point -v -s")
        return

    files.sort(reverse=True)
    latest_file = os.path.join(responses_dir, files[0])

    print(f"\n[OK] 加载算法响应: {files[0]}")
    algorithm_checkpoints = extract_algorithm_checkpoints(latest_file)

    # 5. 对比分析
    result = compare_checkpoints_simple(algorithm_checkpoints, zhipuai_checkpoints)

    # 6. 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f'./test_data/evaluation/results/claude_comparison_{timestamp}.json'

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
  - 算法提取检查点: {result['algorithm_count']} 个
  - 智谱AI提取检查点: {result['claude_count']} 个
  - 匹配检查点: {result['matched']} 个
  - 覆盖率: {result['coverage']:.1f}%
  - 召回率: {result['recall']:.1f}%

[TIP] 评估建议:
  - 覆盖率 > 80%: 算法完整性很好
  - 覆盖率 60-80%: 算法基本完整，可能有少量遗漏
  - 覆盖率 < 60%: 算法需要改进，遗漏了重要检查点

  - 召回率 > 80%: 算法提取很准确
  - 召回率 60-80%: 算法基本准确，有少量冗余
  - 召回率 < 60%: 算法提取了较多不相关内容

[FILE] 详细结果: {result_file}
    """)


if __name__ == '__main__':
    main()
