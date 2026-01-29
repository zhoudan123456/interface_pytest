# HAR文件到需求大纲分析框架 - 使用指南

## 📋 概述

这是一个自动化工具,可以从HAR(HTTP Archive)文件中提取用户操作流程,并使用Claude大模型生成结构化的软件需求规格大纲。

### 主要功能

- ✅ **HAR文件解析**: 自动提取用户操作序列
- ✅ **操作类型识别**: 智能识别登录、搜索、创建、更新等操作
- ✅ **API端点提取**: 自动识别和整理API接口
- ✅ **需求生成**: 使用Claude生成结构化需求文档
- ✅ **多格式导出**: 支持JSON、Markdown等多种格式
- ✅ **批量处理**: 支持批量处理多个HAR文件

## 📁 项目结构

```
interface_pytest/
├── har_processors/                          # HAR处理器模块
│   ├── __init__.py
│   ├── har_parser.py                       # HAR文件解析器
│   └── requirement_generator.py            # 需求生成器
├── test_cases/har_analysis/                # 测试用例
│   └── test_har_to_requirements.py
├── test_data/har/                          # 测试数据
│   ├── input/                             # HAR文件输入目录
│   ├── output/                            # 分析结果输出目录
│   └── har_analysis_config.yaml           # 配置文件
├── config/har_prompts/                    # 提示词模板
│   └── requirement_generation.txt         # 需求生成提示词
├── har_to_requirements_pipeline.py        # 主流程控制器
├── run_har_analysis.py                    # 快速开始脚本
└── HAR文件分析框架使用指南.md             # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install PyYAML requests
```

### 2. 配置Claude API密钥

**方式1: 环境变量(推荐)**
```bash
# Windows
set CLAUDE_API_KEY=your-api-key-here

# Linux/Mac
export CLAUDE_API_KEY=your-api-key-here
```

**方式2: 配置文件**

编辑 `test_data/har/har_analysis_config.yaml`:
```yaml
claude_api_key: "your-api-key-here"
```

### 3. 准备HAR文件

将HAR文件放入 `test_data/har/input/` 目录:
```bash
cp your_file.har test_data/har/input/
```

### 4. 运行分析

**方式1: 使用快速开始脚本**
```bash
python run_har_analysis.py
```

**方式2: 使用Python代码**
```python
from har_to_requirements_pipeline import HARToRequirementsPipeline

# 创建流程实例
pipeline = HARToRequirementsPipeline()

# 处理HAR文件
results = pipeline.process_har_file('./test_data/har/input/your_file.har')

# 导出结果
pipeline.export_results()
```

**方式3: 使用pytest测试**
```bash
# 运行所有测试
pytest test_cases/har_analysis/test_har_to_requirements.py -v

# 运行特定测试
pytest test_cases/har_analysis/test_har_to_requirements.py::TestHARProcessor -v
```

## 📊 使用示例

### 示例1: 分析单个HAR文件

```python
from har_to_requirements_pipeline import HARToRequirementsPipeline

pipeline = HARToRequirementsPipeline()

# 处理HAR文件
results = pipeline.process_har_file(
    har_file_path='./test_data/har/input/login_flow.har',
    filter_static=True  # 过滤静态资源
)

# 查看结果
print(f"操作总数: {results['actions_count']}")
print(f"API端点数: {len(results['api_endpoints'])}")

# 导出结果
pipeline.export_results()
```

### 示例2: 批量处理多个HAR文件

```python
from har_to_requirements_pipeline import HARToRequirementsPipeline

pipeline = HARToRequirementsPipeline()

# 批量处理目录下的所有HAR文件
results = pipeline.process_multiple_har_files(
    har_directory='./test_data/har/input',
    merge_requirements=True  # 合并需求
)

# 查看汇总
print(f"处理文件数: {results['summary']['total_files']}")
print(f"总操作数: {results['summary']['total_actions']}")
```

### 示例3: 自定义配置

```python
from har_to_requirements_pipeline import HARToRequirementsPipeline

config = {
    'claude_api_key': 'your-api-key',
    'output_dir': './custom_output',
    'filter_static': True,
    'export_formats': ['json', 'markdown']
}

pipeline = HARToRequirementsPipeline(config)
results = pipeline.process_har_file('./test_data/har/input/test.har')
pipeline.export_results()
```

### 示例4: 仅解析HAR,不生成需求

```python
from har_processors.har_parser import HARProcessor

# 解析HAR文件
processor = HARProcessor('./test_data/har/input/test.har')

# 提取用户操作
actions = processor.extract_user_journey(filter_static=True)

# 生成自然语言叙述
narrative = processor.generate_narrative(actions)

# 提取API端点
api_endpoints = processor.get_api_endpoints(actions)

# 导出操作数据
processor.export_actions_to_json(actions, './output/actions.json')
```

## 📄 输出文件说明

处理完成后,会在输出目录生成以下文件:

### 1. `har_analysis_results_YYYYMMDD_HHMMSS.json`
完整的分析结果,包含:
- 业务流程叙述
- 用户操作列表
- API端点清单
- 需求大纲(如果有API密钥)
- 统计报告

### 2. `requirements_YYYYMMDD_HHMMSS.json`
结构化的需求大纲(JSON格式)

### 3. `requirements_YYYYMMDD_HHMMSS.md`
Markdown格式的需求文档

### 4. `narrative_YYYYMMDD_HHMMSS.md`
业务流程自然语言描述

### 5. `api_endpoints_YYYYMMDD_HHMMSS.json`
API端点清单

## 🔧 配置说明

配置文件: `test_data/har/har_analysis_config.yaml`

```yaml
# Claude API配置
claude_api_key: ${CLAUDE_API_KEY}

# 输出配置
output_dir: ./test_data/har/output
export_formats:
  - json
  - markdown

# HAR解析配置
har_processing:
  filter_static: true          # 过滤静态资源
  min_action_count: 1          # 最少操作数量
  max_actions_to_save: 100     # 保存的最大操作数

# 需求生成配置
requirement_generation:
  claude_model: claude-3-5-sonnet-20241022
  max_narrative_length: 8000
  temperature: 0.3

# 业务关键词配置
business_keywords:
  login: [login, signin, auth, token]
  logout: [logout, signout]
  search: [search, query, filter]
  # ... 更多关键词
```

## 🎯 支持的操作类型

框架可以自动识别以下操作类型:

| 操作类型 | 关键词 | 说明 |
|---------|--------|------|
| login | login, signin, auth, token | 用户登录 |
| logout | logout, signout | 用户登出 |
| register | register, signup | 用户注册 |
| search | search, query, filter, list | 搜索查询 |
| add | add, create, new, save | 添加创建 |
| edit | edit, update, modify | 编辑更新 |
| delete | delete, remove, destroy | 删除 |
| view | view, detail, info, get | 查看详情 |
| download | download, export, csv, excel | 下载导出 |
| upload | upload, import, file, attachment | 上传导入 |
| submit | submit, approve, confirm | 提交审批 |
| check | check, validate, verify | 验证检查 |

## 🧪 测试

### 运行单元测试

```bash
# 测试HAR解析器
pytest test_cases/har_analysis/test_har_to_requirements.py::TestHARProcessor -v

# 测试需求生成器
pytest test_cases/har_analysis/test_har_to_requirements.py::TestRequirementGenerator -v

# 测试完整流程
pytest test_cases/har_analysis/test_har_to_requirements.py::TestHARToRequirementsPipeline -v
```

### 运行集成测试(需要API密钥)

```bash
pytest test_cases/har_analysis/test_har_to_requirements.py::TestHARAnalysisIntegration -v
```

## ⚠️ 注意事项

### 1. API密钥
- 必须配置有效的Claude API密钥才能生成需求大纲
- 没有API密钥时仍可解析HAR文件和提取操作

### 2. 文件大小
- HAR文件过大可能导致处理缓慢
- 建议预先清理不必要的数据
- 可以设置 `filter_static=true` 过滤静态资源

### 3. 成本控制
- Claude API按token计费
- 大量HAR文件会产生API调用费用
- 建议先用小文件测试

### 4. 隐私保护
- HAR文件可能包含敏感信息
- 处理前请确保数据脱敏
- 不要上传包含真实密码的HAR文件

## 🔍 故障排除

### 问题1: API调用失败
```
❌ 生成需求失败: 401 Unauthorized
```
**解决方案**: 检查API密钥是否正确配置

### 问题2: HAR文件解析失败
```
❌ 处理失败: Expecting value: line 1 column 1 (char 0)
```
**解决方案**: 确保HAR文件格式正确,可以尝试用文本编辑器打开查看

### 问题3: 生成的需求不完整
```
⚠️  需求大纲可能不完整,请手动审核
```
**解决方案**:
- 检查HAR文件是否包含完整的业务流程
- 增加业务关键词配置
- 手动调整提示词模板

### 问题4: 内存不足
```
MemoryError: Unable to allocate array
```
**解决方案**:
- 减少处理的HAR文件大小
- 设置 `max_actions_to_save` 限制保存的操作数
- 分批处理多个文件

## 📚 扩展开发

### 自定义操作类型识别

```python
from har_processors.har_parser import HARProcessor

class CustomHARProcessor(HARProcessor):
    def _identify_action_type(self, request, response):
        # 自定义识别逻辑
        url = request.get('url', '').lower()

        if 'custom_action' in url:
            return 'custom_type'

        # 调用父类方法
        return super()._identify_action_type(request, response)
```

### 自定义需求生成

```python
from har_processors.requirement_generator import RequirementGenerator

class CustomRequirementGenerator(RequirementGenerator):
    def generate_requirements(self, narrative):
        # 自定义需求生成逻辑
        # ...
        return custom_requirements
```

## 📞 技术支持

如有问题,请查看:
1. 本使用指南
2. 测试用例: `test_cases/har_analysis/test_har_to_requirements.py`
3. 配置文件: `test_data/har/har_analysis_config.yaml`

## 🎉 最佳实践

1. **预处理HAR文件**: 清理测试数据,合并相似操作
2. **定制关键词**: 根据业务特点配置业务关键词
3. **人工审核**: 大模型生成的需求需要人工验证
4. **迭代优化**: 收集反馈,持续优化提示词
5. **版本控制**: 保存HAR文件和生成的需求文档

---

**祝您使用愉快!** 🚀
