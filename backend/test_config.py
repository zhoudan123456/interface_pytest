"""测试配置是否正确加载"""
import sys
from pathlib import Path

# 添加backend到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.config import settings

print("=" * 60)
print("后端配置检查")
print("=" * 60)
print(f"ALLOWED_EXTENSIONS: {settings.ALLOWED_EXTENSIONS}")
print()

if ".docx" in settings.ALLOWED_EXTENSIONS:
    print("✅ .docx 格式已正确添加到允许列表")
else:
    print("❌ .docx 格式未添加到允许列表")

print()
print("当前支持的文件格式:")
for ext in sorted(settings.ALLOWED_EXTENSIONS):
    print(f"  - {ext}")
print("=" * 60)
