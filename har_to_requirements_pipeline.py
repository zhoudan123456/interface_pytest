"""
HAR到需求的完整处理流程
主流程控制器
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from har_processors.har_parser import HARProcessor
from har_processors.requirement_generator import RequirementGenerator


class HARToRequirementsPipeline:
    """HAR文件到需求大纲的完整流程"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化处理流程
        :param config: 配置字典
        """
        self.config = config or self._load_default_config()
        self.results = {}

        # 初始化组件
        self.requirement_generator = RequirementGenerator(
            api_key=self.config.get('claude_api_key')
        )

    def _load_default_config(self) -> Dict:
        """加载默认配置"""
        return {
            'claude_api_key': os.getenv('CLAUDE_API_KEY', ''),
            'output_dir': './test_data/har/output',
            'filter_static': True,
            'export_formats': ['json', 'markdown']
        }

    def process_har_file(self, har_file_path: str,
                        filter_static: bool = True) -> Dict:
        """
        处理HAR文件
        :param har_file_path: HAR文件路径
        :param filter_static: 是否过滤静态资源
        :return: 处理结果
        """
        print(f"\n{'='*60}")
        print(f"开始处理HAR文件: {har_file_path}")
        print(f"{'='*60}\n")

        try:
            # 步骤1: 解析HAR文件
            print("[1/4] 解析HAR文件...")
            har_processor = HARProcessor(har_file_path)
            actions = har_processor.extract_user_journey(filter_static=filter_static)
            print(f"✓ 提取到 {len(actions)} 个用户操作")

            # 步骤2: 生成自然语言叙述
            print("\n[2/4] 生成自然语言描述...")
            narrative = har_processor.generate_narrative(actions)
            self.results['narrative'] = narrative
            self.results['actions_count'] = len(actions)
            self.results['actions'] = [a.to_dict() for a in actions[:50]]  # 保存前50个操作
            print(f"✓ 生成业务流程叙述成功")

            # 步骤3: 提取API端点
            print("\n[3/4] 提取API端点...")
            api_endpoints = har_processor.get_api_endpoints(actions)
            self.results['api_endpoints'] = api_endpoints
            print(f"✓ 识别出 {len(api_endpoints)} 个API端点")

            # 步骤4: 生成需求大纲
            print("\n[4/4] 生成需求大纲...")
            print("  (这可能需要1-2分钟,请耐心等待...)")
            requirements = self.requirement_generator.generate_requirements(narrative)
            self.results['requirements'] = requirements
            print(f"✓ 需求大纲生成完成")

            # 生成统计报告
            print("\n生成统计报告...")
            report = self._generate_report(actions, requirements, api_endpoints)
            self.results['report'] = report

            # 显示摘要
            self._print_summary(report)

            return self.results

        except Exception as e:
            print(f"\n❌ 处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def process_multiple_har_files(self, har_directory: str,
                                  merge_requirements: bool = False) -> Dict:
        """
        批量处理多个HAR文件
        :param har_directory: HAR文件目录
        :param merge_requirements: 是否合并需求
        :return: 处理结果
        """
        har_dir = Path(har_directory)
        if not har_dir.exists():
            raise FileNotFoundError(f"目录不存在: {har_directory}")

        # 查找所有HAR文件
        har_files = list(har_dir.glob("*.har")) + list(har_dir.glob("*.HAR"))

        if not har_files:
            raise ValueError(f"目录中没有找到HAR文件: {har_directory}")

        print(f"\n找到 {len(har_files)} 个HAR文件")

        all_results = {}
        for i, har_file in enumerate(har_files, 1):
            print(f"\n{'='*60}")
            print(f"处理文件 [{i}/{len(har_files)}]: {har_file.name}")
            print(f"{'='*60}")

            result = self.process_har_file(str(har_file))
            all_results[har_file.name] = result

        if merge_requirements:
            print("\n合并需求大纲...")
            merged_requirements = self._merge_requirements(all_results)
            all_results['merged_requirements'] = merged_requirements

        all_results['summary'] = {
            'total_files': len(har_files),
            'total_actions': sum(r.get('actions_count', 0) for r in all_results.values()),
            'successful_files': sum(1 for r in all_results.values() if 'error' not in r)
        }

        return all_results

    def _generate_report(self, actions: List, requirements: Dict,
                        api_endpoints: List[Dict]) -> Dict:
        """生成详细报告"""
        report = {
            "summary": {
                "processing_time": datetime.now().isoformat(),
                "total_actions": len(actions),
                "successful_actions": sum(1 for a in actions if a.success),
                "failed_actions": sum(1 for a in actions if not a.success),
                "total_endpoints": len(api_endpoints),
                "total_modules": self._count_modules(requirements)
            },
            "action_analysis": {
                "by_type": self._group_actions_by_type(actions),
                "by_status": {
                    "success": sum(1 for a in actions if a.success),
                    "failed": sum(1 for a in actions if not a.success)
                },
                "avg_response_time": sum(a.wait_time for a in actions) / len(actions) if actions else 0
            },
            "api_analysis": {
                "total_endpoints": len(api_endpoints),
                "endpoints_by_method": self._group_endpoints_by_method(api_endpoints),
                "endpoints_by_type": self._group_endpoints_by_type(api_endpoints)
            },
            "requirements_analysis": {
                "total_modules": self._count_modules(requirements),
                "total_features": self._count_features(requirements),
                "features_by_priority": self._group_features_by_priority(requirements)
            }
        }

        return report

    def _count_modules(self, requirements: Dict) -> int:
        """统计模块数量"""
        try:
            modules = requirements.get('functional_requirements', {}).get('modules', [])
            return len(modules)
        except:
            return 0

    def _count_features(self, requirements: Dict) -> int:
        """统计功能数量"""
        try:
            modules = requirements.get('functional_requirements', {}).get('modules', [])
            return sum(len(m.get('features', [])) for m in modules)
        except:
            return 0

    def _group_actions_by_type(self, actions: List) -> Dict:
        """按类型分组操作"""
        groups = {}
        for action in actions:
            action_type = action.action_type if hasattr(action, 'action_type') else action.get('action_type', 'unknown')
            groups[action_type] = groups.get(action_type, 0) + 1
        return dict(sorted(groups.items(), key=lambda x: x[1], reverse=True))

    def _group_endpoints_by_method(self, endpoints: List) -> Dict:
        """按HTTP方法分组端点"""
        groups = {}
        for ep in endpoints:
            method = ep.get('method', 'UNKNOWN')
            groups[method] = groups.get(method, 0) + 1
        return groups

    def _group_endpoints_by_type(self, endpoints: List) -> Dict:
        """按操作类型分组端点"""
        groups = {}
        for ep in endpoints:
            action_type = ep.get('action_type', 'unknown')
            groups[action_type] = groups.get(action_type, 0) + 1
        return dict(sorted(groups.items(), key=lambda x: x[1], reverse=True))

    def _group_features_by_priority(self, requirements: Dict) -> Dict:
        """按优先级分组功能"""
        priorities = {"High": 0, "Medium": 0, "Low": 0}

        try:
            modules = requirements.get('functional_requirements', {}).get('modules', [])
            for module in modules:
                features = module.get('features', [])
                for feature in features:
                    priority = feature.get('priority', 'Medium')
                    if priority in priorities:
                        priorities[priority] += 1
        except:
            pass

        return priorities

    def _print_summary(self, report: Dict):
        """打印摘要信息"""
        print("\n" + "="*60)
        print("处理完成! 结果摘要:")
        print("="*60)

        summary = report.get('summary', {})
        print(f"\n用户操作:")
        print(f"  - 总操作数: {summary.get('total_actions', 0)}")
        print(f"  - 成功: {summary.get('successful_actions', 0)}")
        print(f"  - 失败: {summary.get('failed_actions', 0)}")

        print(f"\nAPI端点:")
        print(f"  - 总端点数: {summary.get('total_endpoints', 0)}")

        req_analysis = report.get('requirements_analysis', {})
        print(f"\n需求分析:")
        print(f"  - 功能模块: {req_analysis.get('total_modules', 0)}")
        print(f"  - 功能点: {req_analysis.get('total_features', 0)}")

        features_by_priority = req_analysis.get('features_by_priority', {})
        print(f"  - 高优先级: {features_by_priority.get('High', 0)}")
        print(f"  - 中优先级: {features_by_priority.get('Medium', 0)}")
        print(f"  - 低优先级: {features_by_priority.get('Low', 0)}")

        print("\n" + "="*60)

    def export_results(self, output_dir: str = None, formats: List[str] = None):
        """导出结果"""
        output_dir = output_dir or self.config.get('output_dir', './test_data/har/output')
        formats = formats or self.config.get('export_formats', ['json', 'markdown'])

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 导出完整结果(JSON)
        if 'json' in formats:
            results_file = output_path / f"har_analysis_results_{timestamp}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"✓ 完整结果已导出: {results_file}")

        # 导出需求大纲(JSON)
        if 'requirements' in self.results and 'json' in formats:
            req_file = output_path / f"requirements_{timestamp}.json"
            with open(req_file, 'w', encoding='utf-8') as f:
                json.dump(self.results['requirements'], f, ensure_ascii=False, indent=2)
            print(f"✓ 需求大纲已导出: {req_file}")

        # 导出需求大纲(Markdown)
        if 'requirements' in self.results and 'markdown' in formats:
            md_file = output_path / f"requirements_{timestamp}.md"
            self.requirement_generator.export_requirements_to_markdown(
                self.results['requirements'],
                str(md_file)
            )

        # 导出业务流程叙述
        if 'narrative' in self.results:
            narrative_file = output_path / f"narrative_{timestamp}.md"
            with open(narrative_file, 'w', encoding='utf-8') as f:
                f.write(self.results['narrative'])
            print(f"✓ 业务流程叙述已导出: {narrative_file}")

        # 导出API端点清单
        if 'api_endpoints' in self.results:
            api_file = output_path / f"api_endpoints_{timestamp}.json"
            with open(api_file, 'w', encoding='utf-8') as f:
                json.dump(self.results['api_endpoints'], f, ensure_ascii=False, indent=2)
            print(f"✓ API端点清单已导出: {api_file}")

        print(f"\n所有结果已导出到目录: {output_path}")

    def _merge_requirements(self, all_results: Dict) -> Dict:
        """合并多个文件的需求"""
        # 简化的合并逻辑
        merged = {
            'project_overview': {
                'background': '合并多个HAR文件生成的需求',
                'sources': list(all_results.keys())
            },
            'functional_requirements': {
                'modules': []
            }
        }

        all_modules = []
        for file_name, result in all_results.items():
            if 'requirements' in result and 'functional_requirements' in result['requirements']:
                modules = result['requirements']['functional_requirements'].get('modules', [])
                for module in modules:
                    module['source_file'] = file_name
                    all_modules.append(module)

        merged['functional_requirements']['modules'] = all_modules

        return merged


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    import yaml
    from conf.set_conf import resolve_path

    config_file = resolve_path(config_path)
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
