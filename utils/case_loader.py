import yaml
import os
from typing import Dict, List


class CaseLoader:
    """测试用例加载器"""

    @staticmethod
    def load_case(file_path: str) -> Dict:
        """加载YAML测试用例"""
        with open(file_path, 'r', encoding='utf-8') as f:
            case = yaml.safe_load(f)

        # 注入文件路径
        case['__file__'] = os.path.abspath(file_path)

        # 确保必要的字段存在
        case.setdefault('teststeps', [])
        case.setdefault('variables', {})

        return case

    @staticmethod
    def discover_cases(case_dir: str = 'test_cases',
                       pattern: str = '*.yaml') -> List[Dict]:
        """发现并加载所有测试用例"""
        cases = []
        for root, _, files in os.walk(case_dir):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    case_path = os.path.join(root, file)
                    try:
                        cases.append(CaseLoader.load_case(case_path))
                    except Exception as e:
                        print(f"⚠️ 加载用例失败 {case_path}: {e}")
        return cases