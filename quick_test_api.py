"""
快速测试智谱AI API密钥是否有效
"""
import os
from zhipuai import ZhipuAI

# 从环境变量或手动设置API密钥
API_KEY = os.getenv('ZHIPUAI_API_KEY', 'cd3b673bfa3041b489b92f9188c314e4.9UAWLn2qUTdIjS8C')

print("=" * 60)
print("ZhipuAI API Key Test")
print("=" * 60)
print(f"\nAPI Key: {API_KEY[:20]}...{API_KEY[-10:]}")

# 初始化客户端
try:
    client = ZhipuAI(api_key=API_KEY)
    print("[OK] Client initialized successfully")
except Exception as e:
    print(f"[ERROR] Client initialization failed: {e}")
    exit(1)

# 测试API调用
print("\nTesting API call...")
try:
    response = client.chat.completions.create(
        model="glm-4.7",
        messages=[
            {
                "role": "user",
                "content": "Hello, please reply with one sentence: API test successful"
            }
        ],
        temperature=0.1,
        max_tokens=50
    )

    content = response.choices[0].message.content
    print("[OK] API call successful!")
    print(f"\nAI Response: {content}")
    print(f"\nToken Usage: {response.usage.total_tokens} tokens")

    print("\n" + "=" * 60)
    print("API key validation successful! Ready to use.")
    print("=" * 60)

except Exception as e:
    error_msg = str(e)
    print(f"[ERROR] API call failed!")

    if "401" in error_msg:
        print("\nReason: API key is invalid or expired")
        print("\nSolution:")
        print("  1. Visit https://open.bigmodel.cn/")
        print("  2. Login and go to 'API Key' management")
        print("  3. Create a new API key")
        print("  4. Update config file or environment variable")
    elif "429" in error_msg:
        print("\nReason: Rate limit or insufficient balance")
        print("\nSolution:")
        print("  1. Reduce request frequency")
        print("  2. Check account balance")
        print("  3. Try again later")
    else:
        print(f"\nError Details: {error_msg}")
        print("\nSuggestions:")
        print("  1. Check network connection")
        print("  2. Verify API key format")
        print("  3. Check ZhipuAI service status")

    print("\n" + "=" * 60)
    print("API key validation failed! Please update the key.")
    print("=" * 60)
