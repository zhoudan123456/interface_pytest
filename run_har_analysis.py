"""
HAR文件分析快速开始脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from har_to_requirements_pipeline import HARToRequirementsPipeline, load_config


def main():
    """主函数"""
    print("=" * 70)
    print("HAR文件到需求大纲分析工具")
    print("=" * 70)

    # 加载配置
    config_path = './test_data/har/har_analysis_config.yaml'
    try:
        config = load_config(config_path)
        claude_api_key = config.get('claude_api_key', '')
        print(f"✅ 配置文件加载成功")
    except FileNotFoundError:
        print(f"⚠️  配置文件不存在,使用默认配置")
        claude_api_key = os.getenv('CLAUDE_API_KEY', '')
        config = {
            'claude_api_key': claude_api_key,
            'output_dir': './test_data/har/output',
            'filter_static': True
        }

    # 检查API密钥
    if not config.get('claude_api_key'):
        print("\n⚠️  警告: 未配置CLAUDE_API_KEY")
        print("\n请通过以下方式之一配置:")
        print("  方式1 - 环境变量:")
        print("    Windows: set CLAUDE_API_KEY=your-api-key")
        print("    Linux/Mac: export CLAUDE_API_KEY=your-api-key")
        print("  方式2 - 配置文件:")
        print("    修改 test_data/har/har_analysis_config.yaml")
        print("    设置 claude_api_key: \"your-api-key\"")

        response = input("\n是否继续? (部分功能将不可用) (y/n): ")
        if response.lower() != 'y':
            print("已取消")
            return

    print(f"\n✅ 环境准备完成")

    # 选择模式
    print("\n" + "=" * 70)
    print("请选择处理模式:")
    print("  1. 处理单个HAR文件")
    print("  2. 批量处理HAR文件")
    print("=" * 70)

    mode = input("\n请输入选项 (1/2): ").strip()

    pipeline = HARToRequirementsPipeline(config)

    if mode == '1':
        # 单文件处理模式
        har_file = input("\n请输入HAR文件路径: ").strip()

        if not os.path.exists(har_file):
            print(f"❌ 文件不存在: {har_file}")
            return

        filter_static = input("是否过滤静态资源? (y/n, 默认y): ").strip().lower()
        filter_static = filter_static != 'n'

        # 处理HAR文件
        results = pipeline.process_har_file(har_file, filter_static=filter_static)

        # 导出结果
        export = input("\n是否导出结果? (y/n, 默认y): ").strip().lower()
        if export != 'n':
            pipeline.export_results()

    elif mode == '2':
        # 批量处理模式
        har_dir = input("\n请输入HAR文件目录路径: ").strip()

        if not os.path.exists(har_dir):
            print(f"❌ 目录不存在: {har_dir}")
            return

        merge = input("是否合并多个文件的需求? (y/n, 默认n): ").strip().lower()
        merge_requirements = merge == 'y'

        # 批量处理
        results = pipeline.process_multiple_har_files(har_dir, merge_requirements)

        # 导出结果
        export = input("\n是否导出结果? (y/n, 默认y): ").strip().lower()
        if export != 'n':
            output_dir = input("请输入输出目录 (默认: ./test_data/har/output): ").strip()
            output_dir = output_dir or './test_data/har/output'
            pipeline.export_results(output_dir)

    else:
        print("❌ 无效的选项")
        return

    print("\n✅ 处理完成!")


def analyze_har_file(har_file_path: str, output_dir: str = None):
    """
    便捷函数: 分析单个HAR文件
    :param har_file_path: HAR文件路径
    :param output_dir: 输出目录
    """
    config = {
        'claude_api_key': os.getenv('CLAUDE_API_KEY', ''),
        'output_dir': output_dir or './test_data/har/output'
    }

    pipeline = HARToRequirementsPipeline(config)
    results = pipeline.process_har_file(har_file_path)
    pipeline.export_results()

    return results


def analyze_har_directory(har_directory: str, merge: bool = False, output_dir: str = None):
    """
    便捷函数: 批量分析HAR文件
    :param har_directory: HAR文件目录
    :param merge: 是否合并需求
    :param output_dir: 输出目录
    """
    config = {
        'claude_api_key': os.getenv('CLAUDE_API_KEY', ''),
        'output_dir': output_dir or './test_data/har/output'
    }

    pipeline = HARToRequirementsPipeline(config)
    results = pipeline.process_multiple_har_files(har_directory, merge_requirements=merge)
    pipeline.export_results()

    return results


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
