# 招标文件检查点解析测试项目

## 📁 项目结构

```
ai_test/
├── README.md                           # 本文件
├── QUICK_START_GUIDE.md                # 快速验证指南（2小时MVP）
├── 招标文件检查点解析测试方案.md       # 完整测试方案文档
│
├── scripts/                            # 脚本目录
│   ├── create_annotation_template.py   # 生成标注Excel模板
│   └── quick_verify.py                 # 快速验证脚本
│
├── templates/                          # 模板目录
│   └── checkpoint_annotation_template_simple.xlsx  # 标注模板
│
├── data/                               # 数据目录
│   ├── samples/                        # 招标文件样本
│   ├── annotations/                    # 人工标注数据
│   └── results/                        # 算法解析结果
│
└── outputs/                            # 输出目录
    └── validation_report.md            # 验证报告
```

---

## 🚀 快速开始（2小时验证）

### 最简单的验证方式

```bash
# 1. 生成标注模板
python scripts/create_annotation_template.py

# 2. 运行快速验证（使用示例数据）
python scripts/quick_verify.py

# 3. 查看验证报告
start outputs/validation_report.md
```

### 使用真实数据验证

```bash
# 1. 生成并填写标注模板
python scripts/create_annotation_template.py
# 打开 templates/checkpoint_annotation_template_simple.xlsx
# 填写你的标注数据

# 2. 修改 scripts/quick_verify.py 中的文件路径
# verifier = QuickVerifier(
#     annotation_file='你的标注文件.xlsx',
#     algorithm_result_file='你的算法结果.json'
# )

# 3. 运行验证
python scripts/quick_verify.py

# 4. 查看报告
# outputs/validation_report.md
```

---

## 📚 文档说明

| 文档 | 用途 | 阅读时间 |
|------|------|----------|
| **QUICK_START_GUIDE.md** | 2小时快速验证指南 | 10分钟 |
| **招标文件检查点解析测试方案.md** | 完整测试方案（包含标注方案详细设计） | 30分钟 |

---

## 🎯 核心功能

### 1. 标注模板生成
```bash
python scripts/create_annotation_template.py
```

生成包含以下工作表的Excel模板:
- **检查点标注**: 主标注表
- **文件信息**: 文件元数据
- **类别说明**: 检查点分类说明

### 2. 快速验证工具
```bash
python scripts/quick_verify.py
```

功能:
- ✅ 加载Excel标注数据
- ✅ 加载算法JSON结果
- ✅ 自动匹配检查点（使用模糊匹配算法）
- ✅ 计算核心指标（遗漏率、召回率、精确率、F1分数）
- ✅ 生成详细验证报告

---

## 📊 验证指标说明

| 指标 | 公式 | 说明 |
|------|------|------|
| **遗漏率 (Miss Rate)** | FN / (TP + FN) | 核心关注指标 |
| **召回率 (Recall)** | TP / (TP + FN) | 正确识别的比例 |
| **精确率 (Precision)** | TP / (TP + FP) | 识别结果中正确的比例 |
| **F1-Score** | 2×P×R / (P+R) | 综合评估指标 |

其中:
- **TP (True Positive)**: 正确识别的检查点
- **FP (False Positive)**: 误报的检查点
- **FN (False Negative)**: 遗漏的检查点

---

## 💡 使用建议

### MVP阶段（第1周）
1. 使用示例数据快速走通流程
2. 选择1-2份真实招标文件进行标注
3. 运行验证脚本，查看结果
4. 识别主要问题和改进方向

### 扩展阶段（第2-3周）
1. 扩大到10-15份文件标注
2. 建立标注质量控制流程
3. 实现自动化测试流程
4. 生成详细分析报告

### 生产阶段（第4周+）
1. 建立50+份文件的标注数据集
2. 实现持续监控和回归测试
3. 优化算法识别准确率
4. 建立标注规范文档库

---

## 🔧 依赖安装

```bash
# 必需依赖
pip install pandas openpyxl rapidfuzz

# 可选依赖（用于生成图表）
pip install matplotlib plotly

# 可选依赖（用于Web界面）
pip install fastapi uvicorn
```

---

## 📝 快速验证检查清单

### 准备阶段
- [ ] 已安装Python依赖
- [ ] 已生成标注模板
- [ ] 已选择测试用招标文件
- [ ] 已准备好算法结果JSON

### 标注阶段
- [ ] 已通读招标文件
- [ ] 已标注所有检查点
- [ ] 已检查标注完整性
- [ ] 已保存标注文件

### 验证阶段
- [ ] 已运行验证脚本
- [ ] 已查看生成的报告
- [ ] 已分析遗漏和误报
- [ ] 已记录核心指标

### 结论阶段
- [ ] 已判断方案可行性
- [ ] 已制定改进计划
- [ ] 已决定下一步行动

---

## 🎓 标注要点

### 检查点识别标准

**必须是检查点**:
- ✅ 不满足会导致废标或扣分的要求
- ✅ 需要投标人提供证明材料的要求
- ✅ 评分标准中的明确要求
- ✅ 资格审查条件

**不是检查点**:
- ❌ 一般性的说明文字
- ❌ 流程性描述
- ❌ 解释性内容

### 标注质量要求

**完整性**:
- 检查所有关键章节（第2、3、4、6章）
- 重点关注表格、列表、脚注
- 不遗漏任何实质性要求

**准确性**:
- 检查点文本与原文一致
- 分类准确
- 页码正确

**一致性**:
- 使用统一的ID命名规则
- 使用统一的类别分类
- 遵循标注规范

---

## 📞 获取帮助

### 遇到问题?

1. **查看文档**
   - [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - 快速验证指南
   - [招标文件检查点解析测试方案.md](招标文件检查点解析测试方案.md) - 完整方案

2. **检查数据**
   - 确认标注数据格式正确
   - 确认算法结果JSON格式正确
   - 查看验证报告中的详细分析

3. **常见问题**
   - 见 QUICK_START_GUIDE.md 中的FAQ部分

---

## 📊 验证结果示例

### 优秀示例
```
遗漏率: 8.3%   ✅
召回率: 91.7%  ✅
精确率: 100%   ✅
F1-Score: 95.7% ✅

结论: 方案可行，进入详细测试阶段
```

### 需要改进示例
```
遗漏率: 25.0%  ⚠️
召回率: 75.0%  ⚠️
精确率: 85.7%  ✅
F1-Score: 80.0% ⚠️

结论: 基本可行，需要优化遗漏问题
```

---

## 🎉 开始验证

```bash
# 一键开始
python scripts/quick_verify.py
```

**祝验证顺利！** 🚀
