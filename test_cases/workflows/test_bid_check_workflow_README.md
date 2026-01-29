# 招标文件检查工作流测试说明

## 📋 测试概述

这个测试套件实现了招标文件检查的完整业务流程，包含以下6个步骤：

1. **上传文件** - `POST /prod-api/backend/bidCheck/upload`
2. **刷新Token** - `POST /prod-api/auth/refresh`
3. **启动检查任务** - `POST /prod-api/check/check/task/start`
4. **检查检查点** - `POST /prod-api/check/check/task/check/point`
5. **查询分析状态** - `POST /prod-api/check/check/task/analysis/status`（带轮询）
6. **获取投标信息** - `POST /prod-api/check/check/task/bid/info`

## 📁 文件结构

```
test_cases/
└── workflows/
    └── test_bid_check_workflow.py    # 测试用例

test_data/
├── bid_check_workflow.yaml           # 测试数据配置
└── files/
    └── test_bid_document.pdf         # 测试用招标文件（需要准备）
```

## 🚀 使用方法

### 方法1: 运行单个测试步骤

```bash
# 步骤1: 测试上传文件
pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_01_upload_document -v -s

# 步骤2: 测试刷新Token
pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_02_refresh_token -v -s

# 步骤3: 测试启动检查任务
pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_03_start_check_task -v -s

# 步骤4: 测试检查检查点
pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_04_check_check_point -v -s

# 步骤5: 测试查询分析状态
pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_05_query_analysis_status -v -s

# 步骤6: 测试获取投标信息
pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_06_get_bid_info -v -s
```

### 方法2: 运行完整工作流（推荐）

完整工作流会自动执行所有步骤，并包含状态轮询功能：

```bash
pytest test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_07_full_workflow_polling -v -s
```

这个测试会：
1. ✅ 上传文件获取 uploadUrl
2. ✅ 刷新Token
3. ✅ 启动检查任务获取 taskId
4. ✅ 检查检查点
5. ✅ 轮询分析状态（最多30次，每次间隔2秒）
6. ✅ 获取投标信息

### 方法3: 运行所有测试

```bash
pytest test_cases/workflows/test_bid_check_workflow.py -v -s
```

## 📝 测试数据配置

### 修改测试文件路径

编辑 `test_data/bid_check_workflow.yaml`:

```yaml
upload:
  method: POST
  path: /prod-api/backend/bidCheck/upload
  data:
    type: 1
  files:
    file: ./test_data/files/your_test_file.pdf  # 修改为你的测试文件路径
```

### 修改文件类型

根据实际需求修改 `type` 参数：
- `type: 1` - PDF文件
- `type: 2` - Word文档
- 其他类型根据API文档定义

## 🔍 测试说明

### 数据流转

```
步骤1: 上传文件
    ↓
    返回: fileName, uploadUrl
    ↓
步骤2: 刷新Token
    ↓
    返回: code, data
    ↓
步骤3: 启动检查任务 (需要 uploadUrl 作为 documentId)
    ↓
    返回: taskId
    ↓
步骤4: 检查检查点 (需要taskId)
    ↓
步骤5: 查询分析状态 (需要taskId)
    ↓
    返回: parseProgress (轮询直到为 100.0)
    ↓
步骤6: 获取投标信息 (需要taskId)
```

### 状态轮询逻辑

**test_04 查询分析状态（独立轮询）：**
- 最多轮询 30 次
- 每次间隔 60 秒
- 总计最多等待 30 分钟（1800秒）
- 当 `parseProgress` 为 `100.0` 时停止轮询
- 显示详细的进度信息（解析进度、检查状态、重复状态、解析状态）

**test_06 完整工作流测试（带轮询）：**
- 最多轮询 30 次
- 每次间隔 2 秒
- 总计最多等待 60 秒
- 当状态为 `completed`, `finished`, `done`, `success` 时停止轮询
- 如果状态为 `failed`, `error` 则测试失败

### 常见状态值

根据实际接口响应，返回的数据结构：
```json
{
  "code": 200,
  "data": {
    "checkStatus": null,
    "repeatStatus": null,
    "parseProgress": 100.0,  // 解析进度（0-100）
    "taskId": "xxx",
    "parseStatus": null
  }
}
```

- `parseProgress` - 解析进度（0-100），达到 100.0 时表示完成
- `checkStatus` - 检查状态
- `repeatStatus` - 重复状态
- `parseStatus` - 解析状态

## ⚠️ 注意事项

1. **测试文件准备**
   - 需要准备一个有效的招标文件（PDF格式）
   - 放置在 `test_data/files/` 目录下
   - 修改 `bid_check_workflow.yaml` 中的文件路径

2. **执行顺序**
   - 单独测试时必须按顺序执行：1 → 2 → 3 → 4 → 5 → 6
   - 每个步骤依赖前一步骤返回的ID
   - 或者直接运行完整工作流测试 `test_07`

3. **数据持久化**
   - 测试数据会保存在 `test_data/bid_check_workflow.yaml`
   - 包括：`document_id`（实际上是 upload_url）, `file_name`, `upload_url`, `task_id`
   - 每次运行前可以手动清空该文件重新开始

4. **接口依赖**
   - 需要先登录获取token（conftest.py中的auto_login会自动执行）
   - 确保API服务地址配置正确

## 🐛 故障排除

### 问题1: File not found

```
File not found: ./test_data/files/test_bid_document.pdf
```

**解决方案**:
```bash
# 创建测试文件目录
mkdir -p test_data/files

# 复制你的测试文件到该目录
# 或者修改 bid_check_workflow.yaml 中的文件路径
```

### 问题2: Document ID not found

```
Document ID not found. Please run upload test first.
```

**解决方案**:
- 按顺序执行测试，或
- 运行完整工作流测试 `test_06_full_workflow_polling`

### 问题3: Task ID not found

```
Task ID not found. Please run start task test first.
```

**解决方案**:
- 确保已执行步骤1和步骤2
- 或运行完整工作流测试

### 问题4: 轮询超时

```
⚠ 轮询超时（60秒），继续执行后续步骤
```

**解决方案**:
- 这是正常情况，分析可能需要更长时间
- 可以增加轮询次数或间隔时间
- 或者手动检查任务状态

## 📊 测试报告

测试运行后会生成Allure报告：

```bash
# 生成Allure报告
pytest test_cases/workflows/test_bid_check_workflow.py --alluredir=./allure-results
allure serve ./allure-results
```

## 🔧 自定义配置

### 修改轮询参数

编辑 `test_bid_check_workflow.py` 中的轮询逻辑：

```python
# 在 test_06_full_workflow_polling 方法中
max_polls = 30        # 最多轮询次数
poll_interval = 2     # 每次间隔（秒）
```

### 添加更多断言

根据实际业务需求添加验证：

```python
# 验证响应数据
assert 'data' in response_json
assert response_json['data'].get('status') is not None
```

## 📚 相关文档

- HAR分析结果: `test_data/har/output/har_analysis_results_*.json`
- 现有工作流参考: `test_cases/workflows/test_bid_workflow.py`
- 项目配置: `conf/server.ini`

---

**祝你测试顺利！** 🎉
