"""
HAR文件分析测试用例
"""
import json
import os
import pytest
from pathlib import Path

from har_processors.har_parser import HARProcessor, UserAction
from har_processors.requirement_generator import RequirementGenerator
from har_to_requirements_pipeline import HARToRequirementsPipeline, load_config


class TestHARProcessor:
    """HAR解析器测试"""

    @pytest.fixture
    def sample_har_data(self):
        """创建示例HAR数据"""
        return {
            "log": {
                "version": "1.2",
                "entries": [
                    {
                        "startedDateTime": "2024-01-01T10:00:00.000Z",
                        "request": {
                            "method": "POST",
                            "url": "https://example.com/api/login",
                            "headers": [
                                {"name": "Content-Type", "value": "application/json"},
                                {"name": "User-Agent", "value": "Mozilla/5.0"}
                            ],
                            "postData": {
                                "mimeType": "application/json",
                                "text": '{"username":"test","password":"123456"}'
                            }
                        },
                        "response": {
                            "status": 200,
                            "content": {
                                "mimeType": "application/json",
                                "text": '{"code":200,"message":"登录成功","data":{"token":"abc123"}}'
                            }
                        },
                        "timings": {
                            "wait": 100,
                            "receive": 50
                        }
                    },
                    {
                        "startedDateTime": "2024-01-01T10:00:01.000Z",
                        "request": {
                            "method": "GET",
                            "url": "https://example.com/api/users?page=1&size=10",
                            "headers": [
                                {"name": "Authorization", "value": "Bearer abc123"}
                            ]
                        },
                        "response": {
                            "status": 200,
                            "content": {
                                "mimeType": "application/json",
                                "text": '{"code":200,"data":{"list":[],"total":0}}'
                            }
                        },
                        "timings": {
                            "wait": 80,
                            "receive": 30
                        }
                    },
                    {
                        "startedDateTime": "2024-01-01T10:00:02.000Z",
                        "request": {
                            "method": "POST",
                            "url": "https://example.com/api/users/create",
                            "postData": {
                                "mimeType": "application/json",
                                "text": '{"name":"张三","email":"test@example.com"}'
                            }
                        },
                        "response": {
                            "status": 201,
                            "content": {
                                "mimeType": "application/json",
                                "text": '{"code":201,"message":"创建成功"}'
                            }
                        },
                        "timings": {
                            "wait": 150,
                            "receive": 40
                        }
                    }
                ]
            }
        }

    def test_har_processor_init(self, sample_har_data):
        """测试HAR处理器初始化"""
        processor = HARProcessor(har_data=sample_har_data)
        assert processor is not None
        assert len(processor.entries) == 3

    def test_extract_user_journey(self, sample_har_data):
        """测试提取用户旅程"""
        processor = HARProcessor(har_data=sample_har_data)
        actions = processor.extract_user_journey()

        assert len(actions) == 3
        assert actions[0].action_type == 'login'
        assert actions[1].action_type == 'data_fetch'
        assert actions[2].action_type == 'create'

    def test_action_type_identification(self, sample_har_data):
        """测试操作类型识别"""
        processor = HARProcessor(har_data=sample_har_data)
        actions = processor.extract_user_journey()

        # 验证登录操作
        login_action = actions[0]
        assert login_action.method == 'POST'
        assert login_action.action_type == 'login'
        assert 'username' in login_action.request_data

        # 验证数据获取操作
        fetch_action = actions[1]
        assert fetch_action.method == 'GET'
        assert fetch_action.action_type == 'data_fetch'
        assert 'page' in fetch_action.request_data

    def test_generate_narrative(self, sample_har_data):
        """测试生成自然语言叙述"""
        processor = HARProcessor(har_data=sample_har_data)
        actions = processor.extract_user_journey()
        narrative = processor.generate_narrative(actions)

        assert '业务流程记录' in narrative
        assert '操作总数: 3' in narrative
        assert 'login' in narrative or '登录' in narrative
        assert len(narrative) > 100

    def test_get_api_endpoints(self, sample_har_data):
        """测试提取API端点"""
        processor = HARProcessor(har_data=sample_har_data)
        actions = processor.extract_user_journey()
        endpoints = processor.get_api_endpoints(actions)

        assert len(endpoints) >= 2
        assert any(ep['path'] == '/api/login' for ep in endpoints)
        assert any(ep['path'] == '/api/users' for ep in endpoints)

    def test_static_resource_filtering(self, sample_har_data):
        """测试静态资源过滤"""
        # 添加静态资源请求
        sample_har_data['log']['entries'].append({
            "startedDateTime": "2024-01-01T10:00:03.000Z",
            "request": {
                "method": "GET",
                "url": "https://example.com/static/app.js"
            },
            "response": {"status": 200},
            "timings": {"wait": 10, "receive": 5}
        })

        processor = HARProcessor(har_data=sample_har_data)

        # 不过滤静态资源
        actions_all = processor.extract_user_journey(filter_static=False)
        assert len(actions_all) == 4

        # 过滤静态资源
        actions_filtered = processor.extract_user_journey(filter_static=True)
        assert len(actions_filtered) == 3


class TestRequirementGenerator:
    """需求生成器测试"""

    @pytest.fixture
    def requirement_generator(self):
        """创建需求生成器"""
        # 注意:如果没有配置API密钥,相关测试会跳过
        api_key = os.getenv('CLAUDE_API_KEY', '')
        return RequirementGenerator(api_key=api_key)

    def test_load_prompt(self, requirement_generator):
        """测试加载提示词"""
        prompt = requirement_generator._load_requirement_prompt()
        assert prompt is not None
        assert '业务流程记录' in prompt or 'user journey' in prompt.lower()
        assert len(prompt) > 100

    def test_parse_requirements_response(self, requirement_generator):
        """测试解析需求响应"""
        # 模拟Claude响应
        mock_response = '''
        这是一个需求文档的引言部分。
        {
            "project_overview": {
                "background": "测试项目",
                "objectives": ["目标1", "目标2"]
            },
            "functional_requirements": {
                "modules": []
            }
        }
        后续说明文字...
        '''

        result = requirement_generator._parse_requirements_response(mock_response)

        assert 'project_overview' in result
        assert result['project_overview']['background'] == '测试项目'
        assert len(result['project_overview']['objectives']) == 2

    def test_extract_user_stories(self, requirement_generator):
        """测试提取用户故事"""
        mock_requirements = {
            "functional_requirements": {
                "modules": [
                    {
                        "name": "用户管理",
                        "features": [
                            {
                                "name": "用户登录",
                                "user_story": "作为用户,我想要登录系统",
                                "priority": "High",
                                "acceptance_criteria": ["输入正确凭证", "跳转到首页"]
                            }
                        ]
                    }
                ]
            }
        }

        user_stories = requirement_generator.extract_user_stories(mock_requirements)

        assert len(user_stories) == 1
        assert user_stories[0]['module'] == '用户管理'
        assert user_stories[0]['feature'] == '用户登录'

    def test_generate_test_scenarios(self, requirement_generator):
        """测试生成测试场景"""
        mock_requirements = {
            "functional_requirements": {
                "modules": [
                    {
                        "name": "用户管理",
                        "features": [
                            {
                                "name": "用户登录"
                            }
                        ]
                    }
                ]
            }
        }

        scenarios = requirement_generator.generate_test_scenarios(mock_requirements)

        # 应该生成正向和负向测试场景
        assert len(scenarios) == 2
        assert any(s['type'] == 'positive' for s in scenarios)
        assert any(s['type'] == 'negative' for s in scenarios)

    @pytest.mark.skipif(not os.getenv('CLAUDE_API_KEY'), reason="需要CLAUDE_API_KEY")
    def test_generate_requirements_with_api(self, requirement_generator):
        """测试使用API生成需求(需要API密钥)"""
        sample_narrative = """
        # 业务流程记录

        ## 步骤1: 用户登录系统
        **操作类型**: login
        **请求方法**: POST
        **请求路径**: `/api/login`
        **请求参数**: username, password

        ## 步骤2: 查看用户列表
        **操作类型**: data_fetch
        **请求方法**: GET
        **请求路径**: `/api/users`

        ## 步骤3: 创建新用户
        **操作类型**: create
        **请求方法**: POST
        **请求路径**: `/api/users/create`
        """

        requirements = requirement_generator.generate_requirements(sample_narrative)

        assert 'error' not in requirements
        assert 'project_overview' in requirements or 'raw_text' in requirements


class TestHARToRequirementsPipeline:
    """完整流程测试"""

    @pytest.fixture
    def sample_har_file(self, tmp_path):
        """创建示例HAR文件"""
        har_data = {
            "log": {
                "entries": [
                    {
                        "startedDateTime": "2024-01-01T10:00:00.000Z",
                        "request": {
                            "method": "POST",
                            "url": "https://example.com/api/login",
                            "postData": {
                                "mimeType": "application/json",
                                "text": '{"username":"test","password":"123456"}'
                            }
                        },
                        "response": {"status": 200},
                        "timings": {"wait": 100, "receive": 50}
                    }
                ]
            }
        }

        har_file = tmp_path / "test.har"
        with open(har_file, 'w', encoding='utf-8') as f:
            json.dump(har_data, f)

        return str(har_file)

    def test_pipeline_init(self):
        """测试流程初始化"""
        pipeline = HARToRequirementsPipeline()
        assert pipeline is not None
        assert pipeline.requirement_generator is not None

    def test_process_har_file(self, sample_har_file):
        """测试处理HAR文件(不包含需求生成)"""
        pipeline = HARToRequirementsPipeline()

        # 处理HAR文件(不调用API生成需求)
        results = pipeline.process_har_file(sample_har_file)

        # 验证结果(由于没有API密钥,requirements可能为空)
        assert 'narrative' in results
        assert 'api_endpoints' in results
        assert 'actions_count' in results
        assert results['actions_count'] == 1

    def test_export_results(self, sample_har_file, tmp_path):
        """测试导出结果"""
        pipeline = HARToRequirementsPipeline()
        pipeline.process_har_file(sample_har_file)

        # 导出到临时目录
        output_dir = tmp_path / "output"
        pipeline.export_results(str(output_dir), formats=['json'])

        # 验证文件已创建
        assert output_dir.exists()
        result_files = list(output_path.glob("*.json") for output_path in [output_dir])
        assert len(result_files) > 0


class TestHARAnalysisIntegration:
    """集成测试"""

    @pytest.mark.skipif(not os.getenv('CLAUDE_API_KEY'), reason="需要CLAUDE_API_KEY")
    def test_full_workflow_with_api(self, tmp_path):
        """测试完整工作流(需要API密钥)"""
        # 创建示例HAR文件
        har_data = {
            "log": {
                "entries": [
                    {
                        "startedDateTime": "2024-01-01T10:00:00.000Z",
                        "request": {
                            "method": "POST",
                            "url": "https://example.com/api/login",
                            "postData": {
                                "mimeType": "application/json",
                                "text": '{"username":"admin","password":"123456"}'
                            }
                        },
                        "response": {
                            "status": 200,
                            "content": {
                                "mimeType": "application/json",
                                "text": '{"code":200,"message":"登录成功"}'
                            }
                        },
                        "timings": {"wait": 100, "receive": 50}
                    },
                    {
                        "startedDateTime": "2024-01-01T10:00:02.000Z",
                        "request": {
                            "method": "GET",
                            "url": "https://example.com/api/users"
                        },
                        "response": {
                            "status": 200,
                            "content": {
                                "mimeType": "application/json",
                                "text": '{"code":200,"data":{"list":[1,2,3]}}'
                            }
                        },
                        "timings": {"wait": 80, "receive": 30}
                    }
                ]
            }
        }

        har_file = tmp_path / "test.har"
        with open(har_file, 'w', encoding='utf-8') as f:
            json.dump(har_data, f)

        # 执行完整流程
        pipeline = HARToRequirementsPipeline()
        results = pipeline.process_har_file(str(har_file))

        # 验证结果
        assert 'narrative' in results
        assert 'api_endpoints' in results
        assert 'report' in results

        # 如果成功生成需求
        if 'requirements' in results and 'error' not in results.get('requirements', {}):
            requirements = results['requirements']
            assert 'project_overview' in requirements or 'raw_text' in requirements

        # 导出结果
        output_dir = tmp_path / "output"
        pipeline.export_results(str(output_dir))

        # 验证文件已创建
        assert output_dir.exists()
        files = list(output_dir.glob("*"))
        assert len(files) >= 2  # 至少有narrative和results
