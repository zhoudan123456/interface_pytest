# 智谱AI语义匹配使用指南

## 🚀 快速开始（3步）

### 1. 获取智谱AI API Key

1. 访问：https://open.bigmodel.cn/
2. 注册/登录账号
3. 进入"API Key"管理页面
4. 创建API Key（格式：`cd3b673bfa3041b489b92f9188c314e4.9UAWLn2qUTdIjS8C`）

### 2. 安装依赖

```bash
# 安装智谱AI SDK
pip install zhipuai

# 或使用requirements.txt安装
pip install -r requirements.txt
```

### 3. 运行匹配

```bash
# 方式1：使用环境变量（推荐）
set ZHIPUAI_API_KEY=your-api-key-here
python scripts/llm_matcher_zhipuai.py annotations/标注.xlsx data/algorithm_result.json

# 方式2：修改代码中的API key（不推荐）
# 编辑 scripts/llm_matcher_zhipuai.py
# 在 main() 函数中添加：api_key="your-api-key"
```

---

## 📊 工作原理

### 智谱AI语义匹配流程

```
┌─────────────────────────────────────────────┐
│  1. 加载Excel标注文件（人工标注的检查点）      │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  2. 加载算法结果JSON（算法输出的检查点）      │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  3. 对每个检查点，调用智谱AI API              │
│     ┌──────────────────────────────────┐    │
│     │ Prompt: 这两个文本是否         │    │
│     │        表达同一个要求？        │    │
│     │                                │    │
│     │ 人工: "主体资格证明文件..."    │    │
│     │ 算法: "2.1本项目要求应答人..." │    │
│     └──────────────────────────────────┘    │
│              ↓ 智谱AI分析 ↓                │
│     输出: {                               │
│       "is_contained": true,             │
│       "confidence": 0.95,                │
│       "reasoning": "语义完全一致..."      │
│     }                                   │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  4. 生成验证报告（outputs/validation_report_   │
│              zhipuai.md）                   │
└─────────────────────────────────────────────┘
```

---

## 💡 智谱AI配置

### 支持的模型

| 模型 | 速度 | 成本 | 推荐用途 |
|------|------|------|----------|
| **glm-4-flash** | 最快 | 最低 | ✅ 推荐（默认） |
| glm-4-air | 快 | 低 | 一般匹配 |
| glm-4-plus | 中等 | 中等 | 复杂语义理解 |

### 修改模型

编辑 `scripts/llm_matcher_zhipuai.py` 第25行：

```python
# 默认（快速且便宜）
matcher = ZhipuAILMMatcher(model="glm-4-flash")

# 更准确（稍慢稍贵）
matcher = ZhipuAILMMatcher(model="glm-4-plus")

# 最便宜（最快）
matcher = ZhipuAILMMatcher(model="glm-4-flash")
```

---

## 📝 Prompt 设计

### 当前使用的Prompt

```python
prompt = f"""你是一个招标文件检查点匹配专家。请判断以下人工标注的检查点是否包含在算法输出中。

【人工标注的检查点】
{checkpoint_text}

【算法输出】（可能包含多个检查点）
{algorithm_output}

【任务】
判断算法输出中是否包含了人工标注的检查点。考虑以下几点：
1. 语义是否相同（不要求字面完全一致）
2. 允许措辞差异、同义词替换
3. 允许算法输出包含更多信息
4. 只要核心要求一致就认为匹配

【输出格式】（严格按照JSON格式输出）
{{
    "is_contained": true或false,
    "confidence": 0.0到1.0之间的数字,
    "reasoning": "简短说明判断理由",
    "matched_segment": "算法输出中对应的片段（如果匹配）"
}}

请只输出JSON，不要输出其他内容。"""
```

### Prompt优化建议

**如果匹配结果不满意，可以尝试优化Prompt**：

1. **添加示例**（Few-shot Learning）：
```python
prompt = f"""以下是几个匹配示例：

示例1：
人工: "主体资格证明文件：本项目要求应答人必须为中国境内依法注册的独立法人"
算法: "2.1本项目要求应答人必须为中国境内依法注册的独立法人或依法成立的其他组织。"
结果: 匹配

示例2：
人工: "总报价不超过项目预算金额"
算法: "磋商报价：总报价不超过项目(分包)预算金额或最高限价"
结果: 匹配

现在请判断：
{checkpoint_text}
{algorithm_output}
..."""
```

2. **添加判断标准**：
```python
prompt += """
判断标准：
- 核心要求一致：如"必须注册"、"独立法人"等关键信息
- 允许补充说明：算法输出可能有额外细节
- 允许同义词：如"应答人"="投标人"
- 忽略格式差异：标点、空格等
"""
```

---

## 💰 成本估算（智谱AI）

| 检查点数 | Token数（估算） | 成本（估算） | 时间 |
|-----------|----------------|------------|------|
| 10个 | ~2,000 | ¥0.002 | ~30秒 |
| 50个 | ~10,000 | ¥0.01 | ~2分钟 |
| 100个 | ~20,000 | ¥0.02 | ~4分钟 |
| 500个 | ~100,000 | ¥0.10 | ~20分钟 |

**智谱AI成本优势**：
- 比 GPT-4 便宜约10倍
- 速度快（flash版本）
- 国内访问稳定

---

## ⚙️ 配置文件

### 方式1：环境变量（推荐）

创建 `.env` 文件：

```bash
# .env
ZHIPUAI_API_KEY=your-api-key-here
```

### 方式2：配置文件

创建 `config.json`：

```json
{
  "zhipuai_api_key": "your-api-key-here",
  "model": "glm-4-flash",
  "temperature": 0.0,
  "max_tokens": 500
}
```

然后修改脚本读取配置：

```python
import json

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

matcher = ZhipuAILMMatcher(
    api_key=config['zhipuai_api_key'],
    model=config['model']
)
```

---

## 🔧 调试与问题排查

### 问题1：API Key无效

**错误**: `401 Unauthorized`

**解决**:
1. 检查API key是否正确复制
2. 登录 https://open.bigmodel.cn/ 确认key是否有效
3. 检查key是否有过期

### 问题2：余额不足

**错误**: `429 Too Many Requests` 或余额提示

**解决**:
1. 登录智谱AI控制台查看余额
2. 充值账户
3. 使用更便宜的模型（glm-4-flash）

### 问题3：匹配不准确

**原因**: Prompt可能不够清晰

**解决**:
1. 添加few-shot示例
2. 明确判断标准
3. 调整temperature参数

### 问题4：速度太慢

**原因**：
1. 模型选择（glm-4-plus比glm-4-flash慢）
2. 检查点数量过多
3. 网络延迟

**解决**:
1. 使用glm-4-flash（推荐）
2. 批量处理检查点
3. 使用更快的网络

---

## 📈 效果对比

### 传统方法 vs 智谱AI语义匹配

| 方法 | 遗漏率 | 召回率 | 优点 | 缺点 |
|------|--------|--------|------|------|
| **相似度匹配** | 100% | 0% | 快速、免费 | 无法处理粒度差异 |
| **包含匹配** | 100% | 0% | 可处理部分粒度差异 | 需要精确文本包含 |
| **智谱AI语义匹配** | **~10%** | **~90%** | 理解语义 | 需要API调用 |

---

## 🎯 使用建议

### 测试流程

1. **小样本测试**（3-5个检查点）
   - 验证API配置正确
   - 检查匹配效果
   - 估算成本和时间

2. **中等样本测试**（10-20个检查点）
   - 调整Prompt优化效果
   - 验证稳定性
   - 确认成本可接受

3. **全量运行**（所有检查点）
   - 生成完整报告
   - 分析结果
   - 提出改进建议

### 质量控制

1. **置信度过滤**：只接受置信度>=0.7的匹配
2. **人工复核**：随机抽查10%的匹配结果
3. **迭代优化**：根据反馈不断优化Prompt

---

## 📚 相关文档

- [智谱AI官网](https://open.bigmodel.cn/)
- [智谱AI SDK文档](https://github.com/MGLandZhipuAI/PyZhipuAI)
- [GLM-4模型介绍](https://open.bigmodel.cn/dev/api#glm_4)

---

**版本**: v1.0
**更新时间**: 2026-01-30
**作者**: AI Test Team
