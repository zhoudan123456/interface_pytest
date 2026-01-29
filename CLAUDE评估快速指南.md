# 招标文件检查点评估 - 快速指南

## 🎯 功能说明

使用Claude AI作为"评标专家"，对招标文件进行分析并提取检查点，然后与算法提取的检查点进行对比评估。

## 📦 安装依赖

```bash
# 安装PDF读取库
pip install PyPDF2

# 如果使用国内镜像
pip install PyPDF2 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## ⚙️ 配置API密钥

### 方法1: 环境变量（推荐）
```bash
# Windows PowerShell
$env:CLAUDE_API_KEY="your-api-key-here"

# Windows CMD
set CLAUDE_API_KEY=your-api-key-here

# Linux/Mac
export CLAUDE_API_KEY="your-api-key-here"
```

### 方法2: 配置文件
编辑 `./test_data/evaluation/evaluation_config.yaml`:
```yaml
claude_api_key: "your-api-key-here"
```

## 🚀 使用步骤

### 步骤1: 运行测试工作流（生成算法响应）
```bash
pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_07_full_workflow_polling -v -s
```

这会自动保存算法响应到 `./test_data/evaluation/responses/`

### 步骤2: 运行Claude评估
```bash
python evaluate_checkpoints_with_claude.py
```

## 📊 输出说明

### 执行流程
```
1. 读取招标文件PDF → 提取文本内容
2. 调用Claude API → 模拟评标专家提取检查点
3. 加载算法结果 → 从保存的响应中提取
4. 对比分析 → 计算覆盖率和召回率
5. 保存结果 → JSON格式详细报告
```

### 评估指标

**覆盖率 (Coverage)**
- 定义: Claude的检查点有多少被算法提取到
- 公式: 匹配数 / Claude检查点数 × 100%
- 含义: 覆盖率越高，说明算法越完整

**召回率 (Recall)**
- 定义: 算法提取的检查点有多少是正确的
- 公式: 匹配数 / 算法检查点数 × 100%
- 含义: 召回率越高，说明算法越准确

### 结果文件
保存在 `./test_data/evaluation/results/claude_comparison_YYYYMMDD_HHMMSS.json`

包含：
- `algorithm_checkpoints`: 算法提取的所有检查点
- `claude_checkpoints`: Claude提取的所有检查点
- `comparison`: 对比分析结果

## 📝 示例输出

```
============================================================
            招标文件检查评估 - Claude参考答案生成
============================================================
正在读取PDF文件: ./test_data/files/test_zb_document.pdf
  已处理 10/36 页
  已处理 20/36 页
  已处理 30/36 页
✓ 提取完成，共 36 页

正在调用Claude API...
使用模型: claude-3-5-sonnet-20241022
✓ Claude API调用成功
✓ Claude提取了 25 个检查点

✓ 加载算法响应: check_point_response_20260129_152013.json

============================================================
                        检查点对比分析
============================================================

算法提取: 45 个检查点
Claude提取: 25 个检查点

--- 算法提取的检查点 ---
1. [形式评审] (1)是否按招标文件封面要求
2. [形式评审] (2)封面项目名称、项目编号、投标人名称、投标日期是否正确
...

--- Claude提取的检查点 ---
1. [形式评审] 检查封面是否完整
2. [资格评审] 检查营业执照是否有效
...

--- 匹配分析 ---
匹配检查点: 18/25
覆盖率 (Claude中有多少被算法提取): 72.0%
召回率 (算法中有多少在Claude中): 40.0%

✓ 评估结果已保存: ./test_data/evaluation/results/claude_comparison_20260129_152045.json

============================================================
                        评估总结
============================================================
算法提取检查点: 45 个
Claude提取检查点: 25 个
匹配检查点: 18 个

📊 评估指标:
  - 覆盖率: 72.0% (Claude的检查点有多少被算法提取到)
  - 召回率: 40.0% (算法提取的检查点有多少是正确的)

💡 建议:
  - 如果覆盖率低: 说明算法遗漏了一些重要检查点
  - 如果召回率低: 说明算法提取了一些不相关的内容
  - 查看详细结果文件了解具体差异
```

## 🔧 故障排查

### 问题1: "未安装PyPDF2"
**解决**:
```bash
pip install PyPDF2
```

### 问题2: "未找到Claude API密钥"
**解决**:
```bash
# 设置环境变量
$env:CLAUDE_API_KEY="sk-ant-..."

# 或在配置文件中设置
# ./test_data/evaluation/evaluation_config.yaml
```

### 问题3: "招标文件不存在"
**解决**:
```bash
# 检查文件路径
ls ./test_data/files/test_zb_document.pdf

# 或在bid_check_workflow.yaml中配置正确路径
```

### 问题4: "未找到算法响应文件"
**解决**:
```bash
# 先运行测试工作流
pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_05_check_check_point -v -s
```

### 问题5: Claude API调用失败
**可能原因**:
- API密钥无效
- 网络连接问题
- API配额不足
- 请求过大

**解决方法**:
1. 检查API密钥是否正确
2. 检查网络连接
3. 查看账户余额
4. 减小prompt中的文本长度

## 📚 进阶用法

### 自定义Prompt

编辑 `evaluate_checkpoints_with_claude.py` 中的 `prompt` 变量，定制检查点提取规则：

```python
prompt = f"""你是招标评审专家。请从以下角度分析：
1. 法律合规性检查点
2. 资质要求检查点
3. 技术标准检查点
4. 商务条款检查点

招标文件:
{document_text}

请返回JSON格式的检查点...
"""
```

### 批量评估

```python
# 评估多个PDF文件
pdf_files = [
    './test_data/files/file1.pdf',
    './test_data/files/file2.pdf'
]

for pdf_file in pdf_files:
    print(f"\n评估文件: {pdf_file}")
    # 调用评估函数...
```

### 与CI/CD集成

```bash
# 在CI/CD中运行
pytest test_cases/workflows/test_bid_check_workflow.py -v -s
python evaluate_checkpoints_with_claude.py

# 检查评估结果
python -c "import json; data=json.load(open('./test_data/evaluation/results/claude_comparison_latest.json')); print(f\"覆盖率: {data['comparison']['coverage']}%\")"
```

## 💡 最佳实践

1. **定期评估**: 每次算法更新后运行一次评估
2. **保存历史**: 保留不同版本的评估结果，对比改进情况
3. **人工审核**: Claude的检查点也需要人工抽查验证
4. **Prompt优化**: 根据评估结果持续优化Prompt
5. **成本控制**: Claude API有费用，注意控制调用频率

## 📖 相关文档

- [Claude API文档](https://docs.anthropic.com/)
- [PyPDF2文档](https://pypdf2.readthedocs.io/)
- [招标文件检查评估框架使用指南](./招标文件检查评估框架使用指南.md)
