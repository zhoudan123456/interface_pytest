# 招标文件解析准确度测试框架使用说明

## 概述

这是一个基于接口自动化的招标文件解析准确度评估框架,用于评估算法模型对招标文件的解析质量。

## 架构设计

```
interface_pytest/
├── api_clients/                    # API客户端模块
│   ├── claude_client.py           # Claude API客户端
│   └── algorithm_client.py        # 算法模型API客户端
├── evaluators/                     # 评估器模块
│   └── claude_evaluator.py        # Claude评估器
├── processors/                     # 处理器模块
│   └── document_processor.py      # 文档处理器
├── test_cases/                     # 测试用例
│   └── test_bid_parser_evaluation.py
├── test_data/evaluation/           # 测试数据
│   ├── input/                     # 输入文档目录
│   ├── output/                    # 输出结果目录
│   └── evaluation_config.yaml     # 评估配置
├── config/prompts/                 # 提示词模板
│   ├── reference_generation.txt   # 参考答案生成提示词
│   └── evaluation.txt             # 评估提示词
└── bid_evaluation_pipeline.py     # 主流程控制器
```

## 核心功能

### 1. 文档处理
- 支持多种格式: TXT, PDF, DOCX
- 文本预处理和清理
- 批量文档加载

### 2. 算法解析
- 调用算法模型API解析招标文件
- 提取关键检查点信息
- 标准化输出格式

### 3. 参考答案生成
- 使用Claude生成标准参考答案
- 提取项目基本信息、资质要求、时间节点等关键信息
- 按重要程度分类

### 4. 准确度评估
- 完整性评估:是否遗漏关键信息
- 准确性评估:提取信息是否正确
- 一致性评估:与标准答案的匹配度
- 计算精确率、召回率、F1分数

## 快速开始

### 1. 安装依赖

```bash
pip install pytest PyYAML requests
pip install python-docx PyPDF2  # 可选,用于处理Word和PDF文档
```

### 2. 配置环境变量

创建 `.env` 文件或设置环境变量:

```bash
# Claude API密钥(必需)
export CLAUDE_API_KEY="your-claude-api-key"

# 或者修改配置文件 test_data/evaluation/evaluation_config.yaml
```

### 3. 准备测试文档

将待测试的招标文件放入 `test_data/evaluation/input/` 目录:

```bash
cp your_bid_file.txt test_data/evaluation/input/
```

### 4. 运行测试

#### 运行单个测试:
```bash
pytest test_cases/test_bid_parser_evaluation.py::TestBidParserEvaluation::test_document_processor_load_txt -v
```

#### 运行完整评估流程:
```bash
pytest test_cases/test_bid_parser_evaluation.py::TestBidParserEvaluationIntegration::test_full_evaluation_workflow -v
```

#### 运行所有评估测试:
```bash
pytest test_cases/test_bid_parser_evaluation.py -v
```

## 使用示例

### 示例1: 评估单个文档

```python
from bid_evaluation_pipeline import BidParserEvaluationPipeline, load_config

# 加载配置
config = load_config('./test_data/evaluation/evaluation_config.yaml')

# 创建流水线
pipeline = BidParserEvaluationPipeline(config)

# 评估单个文档
result = pipeline.evaluate_single_document(
    document_path='./test_data/evaluation/input/sample.txt',
    document_id='your-document-id'  # 从上传接口获取
)

# 查看结果
print(f"总体评分: {result['overall_score']}")
print(f"F1分数: {result['f1_score']}")
```

### 示例2: 批量评估

```python
from bid_evaluation_pipeline import BidParserEvaluationPipeline

pipeline = BidParserEvaluationPipeline()

# 准备文档列表
documents = [
    {'path': './input/doc1.txt', 'document_id': 'id1'},
    {'path': './input/doc2.txt', 'document_id': 'id2'},
    {'path': './input/doc3.txt', 'document_id': 'id3'},
]

# 批量评估
results = pipeline.evaluate_batch(documents)

# 查看报告
print(pipeline.evaluator.generate_evaluation_report(results))
```

### 示例3: 评估整个目录

```python
from bid_evaluation_pipeline import BidParserEvaluationPipeline

pipeline = BidParserEvaluationPipeline()

# 评估目录下所有文档
results = pipeline.evaluate_directory(
    directory='./test_data/evaluation/input',
    pattern='*.txt'
)

# 结果自动保存到 output 目录
```

## 测试报告

测试完成后,结果会保存在 `test_data/evaluation/output/` 目录:

- `{filename}_result.json`: 每个文档的详细评估结果
- `evaluation_report.txt`: 批量评估的总报告

### 结果文件格式

```json
{
  "algorithm_output": [
    {
      "id": "1",
      "category": "项目基本信息",
      "content": "项目名称:智慧校园建设",
      "importance": "高"
    }
  ],
  "reference_checkpoints": [...],
  "evaluation_result": {
    "overall_score": 85,
    "completeness_score": 80,
    "accuracy_score": 90,
    "consistency_score": 85,
    "precision": 88.5,
    "recall": 82.3,
    "f1_score": 85.3,
    "missing_checkpoints": [],
    "incorrect_checkpoints": [],
    "suggestions": []
  }
}
```

## 配置说明

配置文件: `test_data/evaluation/evaluation_config.yaml`

```yaml
# Claude API配置
claude_api_key: ${CLAUDE_API_KEY}

# 算法API环境
algorithm_env: Test_Env  # 或 Prod_Env

# 输出目录
output_dir: ./test_data/evaluation/output

# 评估阈值
evaluation:
  min_overall_score: 60
  min_completeness_score: 60
  min_accuracy_score: 60
```

## 注意事项

1. **API密钥**: 必须配置有效的Claude API密钥
2. **文档ID**: 需要先通过上传接口获取文档ID
3. **并发限制**: Claude API有速率限制,建议批量测试时控制并发数
4. **成本控制**: Claude API按token计费,大量测试会产生费用
5. **文件格式**: 确保文档编码为UTF-8

## 扩展功能

### 自定义评估器

可以继承 `ClaudeEvaluator` 实现自定义评估逻辑:

```python
from evaluators.claude_evaluator import ClaudeEvaluator

class CustomEvaluator(ClaudeEvaluator):
    def evaluate(self, document_text, algorithm_checkpoints, reference_checkpoints):
        # 自定义评估逻辑
        result = super().evaluate(document_text, algorithm_checkpoints, reference_checkpoints)
        # 添加额外的评估指标
        result['custom_metric'] = self._calculate_custom_metric(...)
        return result
```

### 自定义提示词

修改 `config/prompts/` 目录下的提示词模板以适应特定需求。

## 常见问题

### Q1: 如何获取Claude API密钥?
A: 访问 https://console.anthropic.com/ 注册并获取API密钥。

### Q2: 测试失败了怎么办?
A: 检查:
1. API密钥是否正确
2. 网络连接是否正常
3. 文档ID是否有效
4. 查看详细错误日志

### Q3: 如何提高评估准确度?
A:
1. 优化提示词模板
2. 调整评估阈值
3. 增加参考检查点数量
4. 使用更强大的Claude模型

## 技术支持

如有问题,请查看:
- 项目文档: `解析准确度测试.md`
- 测试用例: `test_cases/test_bid_parser_evaluation.py`
- 配置文件: `test_data/evaluation/evaluation_config.yaml`
