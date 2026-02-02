"""
直接运行LLM匹配的脚本
避免GUI的编码问题
"""
import sys
import os
import pathlib

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    project_root = pathlib.Path(__file__).parent.resolve()
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"[OK] 已加载环境变量: {env_file}")
except ImportError:
    pass

# 导入匹配器
from ai_test_scripts.llm_matcher_zhipuai import ZhipuAILMMatcher

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python run_llm_matcher.py <Excel文件> <JSON文件> [输出文件]")
        print()
        print("示例:")
        print("  python run_llm_matcher.py test.xlsx result.json")
        print("  python run_llm_matcher.py test.xlsx result.json output.md")
        print()
        print("注意：如果不指定输出文件，将自动生成（格式: {Excel文件名}_validation_{时间戳}.md）")
        sys.exit(1)

    excel_file = sys.argv[1]
    json_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None  # None 表示自动生成

    print(f"Excel文件: {excel_file}")
    print(f"JSON文件: {json_file}")
    if output_file:
        print(f"输出文件: {output_file}")
    else:
        print(f"输出文件: 自动生成（基于Excel文件名和时间戳）")
    print()

    # 创建匹配器
    try:
        matcher = ZhipuAILMMatcher()
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)

    # 执行匹配
    result_file = matcher.match_all_checkpoints(excel_file, json_file, output_file)

    if result_file:
        print(f"\n匹配完成！报告已保存到: {result_file}")
    else:
        print("\n匹配失败！")
        sys.exit(1)
