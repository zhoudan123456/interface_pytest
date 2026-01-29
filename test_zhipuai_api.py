"""
测试智谱AI API集成
"""
from zhipuai import ZhipuAI

# 初始化客户端
api_key = "cd3b673bfa3041b489b92f9188c314e4.9UAWLn2qUTdIjS8C"
client = ZhipuAI(api_key=api_key)

print("=" * 60)
print("测试智谱AI API调用")
print("=" * 60)

# 测试基本对话
print("\n1. 测试基本对话...")
try:
    response = client.chat.completions.create(
        model="glm-4.7",
        messages=[
            {
                "role": "system",
                "content": "你是一个有用的AI助手。"
            },
            {
                "role": "user",
                "content": "请用一句话介绍你自己。"
            }
        ],
        temperature=0.1,
        max_tokens=100
    )

    content = response.choices[0].message.content
    print(f"✓ API调用成功")
    print(f"响应内容: {content}")

    # 显示token使用情况
    print(f"\nToken使用情况:")
    print(f"  输入tokens: {response.usage.prompt_tokens}")
    print(f"  输出tokens: {response.usage.completion_tokens}")
    print(f"  总计tokens: {response.usage.total_tokens}")

except Exception as e:
    print(f"❌ API调用失败: {e}")

# 测试JSON格式返回
print("\n" + "=" * 60)
print("2. 测试JSON格式返回...")
try:
    prompt = """请以JSON格式返回一个招标文件检查点列表，格式如下：
{
  "checkpoints": [
    {
      "category": "形式评审",
      "content": "检查封面是否完整",
      "importance": "高"
    }
  ]
}

只返回JSON，不要其他解释。"""

    response = client.chat.completions.create(
        model="glm-4.7",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=500
    )

    content = response.choices[0].message.content
    print(f"✓ API调用成功")
    print(f"\n响应内容:")
    print(content)

    # 尝试解析JSON
    import json
    json_start = content.find('{')
    json_end = content.rfind('}') + 1

    if json_start >= 0 and json_end > json_start:
        json_str = content[json_start:json_end]
        data = json.loads(json_str)
        print(f"\n✓ JSON解析成功")
        print(f"提取了 {len(data.get('checkpoints', []))} 个检查点")
    else:
        print(f"\n⚠️ 未找到JSON格式")

except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
