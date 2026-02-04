# 招标文件检查点验证工具 - Web版本实现方案

## 📋 项目概述

将现有的 Python tkinter 桌面工具（bid_check_gui.py）转换为 Web 应用，让团队成员可以通过浏览器使用招标文件检查点智能验证功能。

## 🎯 核心需求

- **功能**: 上传招标文件 → 执行检查点提取 → LLM语义匹配 → 生成验证报告
- **用户规模**: 内部工具，<50人
- **时间要求**: 快速验证MVP（2-4周）
- **技术偏好**: Vue.js

## 🏗️ 推荐方案：两阶段实现策略

### 阶段1: Streamlit MVP（2-3周）✅ 推荐

**为什么选择 Streamlit？**
- ✅ 纯 Python 开发，无需学习前端框架
- ✅ 2-3周快速上线，符合时间要求
- ✅ 可直接复用现有 Python 代码（llm_matcher_zhipuai.py）
- ✅ 内置文件上传、进度条、日志显示组件
- ✅ 适合快速验证业务逻辑

**技术栈**:
```
前端: Streamlit (Python)
后端: Streamlit Server + 现有 Python 逻辑
AI: 智谱AI (glm-4-flash)
部署: Streamlit Cloud 或 内部服务器
```

**核心功能**:
1. 文件上传界面（PDF、Excel、JSON）
2. 两步验证流程：
   - 步骤1: 执行 pytest API 测试（提取检查点）
   - 步骤2: LLM 语义匹配（生成验证报告）
3. 实时日志显示
4. 报告在线预览和下载

**文件结构**:
```
web_app/
├── streamlit_app.py          # 主应用
├── pages/
│   ├── 1_文件上传.py
│   ├── 2_API测试.py
│   └── 3_LLM验证.py
├── components/
│   ├── file_uploader.py
│   ├── log_display.py
│   └── report_viewer.py
└── config/
    └── streamlit_config.toml
```

---

### 阶段2: FastAPI + Vue3（2-3周）⚡ 优化版本

**为什么选择 FastAPI + Vue3？**
- ✅ 符合用户对 Vue.js 的技术偏好
- ✅ 前后端分离，更好的用户体验
- ✅ 支持更复杂的交互和自定义UI
- ✅ 更适合生产环境和功能扩展
- ✅ **可利用 Vue Skills 确保 Vue 代码质量**

**技术栈详解**:
```
前端技术栈:
  - Vue 3.4+ (Composition API)
  - Vite 5.0+ (构建工具)
  - Element Plus (UI组件库)
  - Vue Router 4.x (路由)
  - Pinia (状态管理)
  - Axios (HTTP客户端)
  - WebSocket (实时通信)

后端技术栈:
  - FastAPI 0.110+ (异步Web框架)
  - Celery 5.3+ (异步任务队列)
  - Redis 7.x (消息代理/缓存)
  - Pydantic v2 (数据验证)
  - Uvicorn (ASGI服务器)
  - python-multipart (文件上传)

AI集成:
  - 智谱AI SDK (glm-4-flash)
  - 现有代码: llm_matcher_zhipuai.py

部署方案:
  - Docker & Docker Compose
  - Nginx (反向代理)
  - PM2 (进程管理，可选)
```

**⏱️ 时间估算优化说明**：

之前的4-6周估算是基于传统开发模式（从零编写代码）。**实际情况只需要2-3周**，因为：

1. **代码复用度高 90%**
   - 后端逻辑已完成：`llm_matcher_zhipuai.py`
   - API测试流程已存在：`test_bid_check_workflow.py`
   - 只需用FastAPI包装成REST API

2. **AI辅助开发**
   - Claude Code 自动生成代码
   - Vue Skills 确保 Vue 最佳实践
   - 减少查资料和调试时间

3. **项目规模小**
   - 内部工具，功能明确
   - 用户<50人，无需复杂权限
   - 3-4个核心页面

**实际工作量（2周全职）**：
- Week 1: 后端FastAPI + 前端Vue3框架
- Week 2: UI优化 + 部署测试

---

### 🏗️ 系统架构设计

**整体架构图**:
```
┌─────────────────────────────────────────────────┐
│              用户浏览器 (Nginx:80)               │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌────────────────┐      ┌────────────────┐
│  Vue 3 前端     │      │  FastAPI 后端  │
│  (静态文件)     │◄────►│  (Port:8000)   │
│                │ API  │                │
│  - 文件上传    │      │  - 文件处理    │
│  - 进度显示    │ WS   │  - 任务调度    │
│  - 报告预览    │      │  - LLM调用     │
└────────────────┘      └────────┬───────┘
                                 │
         ┌───────────────────────┼────────────────┐
         ▼                       ▼                ▼
┌────────────────┐     ┌────────────────┐  ┌──────────────┐
│   Redis        │     │   Celery       │  │  智谱AI API  │
│   (Port:6379)  │◄────►│   Worker       │  │  (外部服务)  │
│                │     │  (异步任务)    │◄─┤              │
│  - 任务队列    │     │                │  └──────────────┘
│  - 任务状态    │     │  - LLM匹配     │
│  - 结果缓存    │     │  - 报告生成    │
└────────────────┘     └────────────────┘
```

**数据流向图**:
```
1. 文件上传流程:
   用户 → Vue前端 → FastAPI → 保存到临时目录 → 返回task_id

2. LLM验证流程:
   Vue前端 → FastAPI → Celery队列 → Worker执行 → 调用智谱AI
                                                        ↓
   Redis状态更新 ←─────────────────────────────────────┘
        ↓
   WebSocket推送 ← FastAPI ← Redis轮询
        ↓
   Vue前端实时显示进度

3. 报告下载流程:
   Vue前端 → FastAPI → 读取生成的报告 → 返回文件流
```

---

### 📁 项目文件结构

**后端结构** (backend/):
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置文件
│   ├── dependencies.py         # 依赖注入
│   │
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py       # 文件上传API
│   │   │   ├── tasks.py        # 任务管理API
│   │   │   ├── reports.py      # 报告下载API
│   │   │   └── websocket.py    # WebSocket连接
│   │   └── deps.py             # API依赖
│   │
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── file_handler.py     # 文件处理服务
│   │   ├── llm_matcher.py      # LLM匹配服务（复用现有代码）
│   │   └── report_generator.py # 报告生成服务
│   │
│   ├── tasks/                  # Celery异步任务
│   │   ├── __init__.py
│   │   ├── celery_app.py       # Celery配置
│   │   └── llm_tasks.py        # LLM相关任务
│   │
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── task.py             # 任务模型
│   │   └── report.py           # 报告模型
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── file_utils.py       # 文件工具
│       └── encoding_helper.py  # 编码处理（复用现有代码）
│
├── uploads/                    # 上传文件临时目录
├── outputs/                    # 生成的报告目录
├── tests/                      # 测试文件
├── requirements.txt            # Python依赖
├── Dockerfile                  # Docker镜像配置
└── .env.example                # 环境变量示例
```

**前端结构** (frontend/):
```
frontend/
├── src/
│   ├── main.ts                 # 应用入口
│   ├── App.vue                 # 根组件
│   │
│   ├── api/                    # API调用
│   │   ├── index.ts            # Axios配置
│   │   ├── upload.ts           # 上传API
│   │   ├── tasks.ts            # 任务API
│   │   └── websocket.ts        # WebSocket封装
│   │
│   ├── components/             # 通用组件
│   │   ├── FileUploader.vue    # 文件上传组件
│   │   ├── ProgressBar.vue     # 进度条组件
│   │   ├── LogViewer.vue       # 日志查看器
│   │   ├── ReportViewer.vue    # 报告预览组件
│   │   └── TaskStatus.vue      # 任务状态组件
│   │
│   ├── views/                  # 页面视图
│   │   ├── Home.vue            # 首页
│   │   ├── Upload.vue          # 文件上传页
│   │   ├── Processing.vue      # 处理进度页
│   │   ├── Report.vue          # 报告查看页
│   │   └── History.vue         # 历史记录页
│   │
│   ├── stores/                 # Pinia状态管理
│   │   ├── task.ts             # 任务状态
│   │   └── user.ts             # 用户状态
│   │
│   ├── router/                 # 路由配置
│   │   └── index.ts
│   │
│   ├── types/                  # TypeScript类型
│   │   ├── task.ts
│   │   └── api.ts
│   │
│   └── assets/                 # 静态资源
│       └── styles/
│           └── main.css
│
├── public/
│   └── favicon.ico
├── index.html
├── vite.config.ts              # Vite配置
├── tsconfig.json               # TypeScript配置
├── package.json                # Node依赖
└── Dockerfile                  # Docker镜像配置
```

**部署配置** (根目录):
```
root/
├── docker-compose.yml          # Docker Compose配置
├── nginx/
│   └── nginx.conf              # Nginx配置
├── .env                        # 环境变量（不提交）
├── .env.example                # 环境变量示例
└── README.md                   # 部署文档
```

---

### 🔌 API端点设计

**RESTful API规范**:

```python
# 1. 文件上传
POST /api/v1/upload
Content-Type: multipart/form-data
Request:
  - file: <binary> (上传的文件)
  - type: str (文件类型: pdf/excel/json)
Response:
{
  "code": 200,
  "message": "success",
  "data": {
    "file_id": "uuid",
    "filename": "example.xlsx",
    "size": 12345,
    "path": "/uploads/uuid.xlsx"
  }
}

# 2. 创建LLM验证任务
POST /api/v1/tasks/match
Content-Type: application/json
Request:
{
  "excel_file_id": "uuid-1",
  "json_file_id": "uuid-2"
}
Response:
{
  "code": 200,
  "message": "Task created",
  "data": {
    "task_id": "task-uuid",
    "status": "pending",
    "created_at": "2024-01-30T10:00:00Z"
  }
}

# 3. 查询任务状态
GET /api/v1/tasks/{task_id}
Response:
{
  "code": 200,
  "data": {
    "task_id": "task-uuid",
    "status": "processing",  # pending/processing/completed/failed
    "progress": 45,           # 0-100
    "current_step": "正在调用智谱AI进行语义匹配...",
    "created_at": "2024-01-30T10:00:00Z",
    "updated_at": "2024-01-30T10:05:00Z",
    "result": null
  }
}

# 4. 下载验证报告
GET /api/v1/reports/{task_id}
Response: Markdown file (Content-Type: text/markdown)

# 5. 获取历史任务列表
GET /api/v1/tasks?page=1&page_size=10
Response:
{
  "code": 200,
  "data": {
    "total": 100,
    "items": [
      {
        "task_id": "task-uuid",
        "status": "completed",
        "created_at": "2024-01-30T10:00:00Z"
      }
    ]
  }
}

# 6. WebSocket实时推送
WS /api/v1/ws/{task_id}
Message:
{
  "type": "progress",
  "data": {
    "progress": 50,
    "message": "正在处理检查点 3/10...",
    "log": "[INFO] Checkpoint CP-003 matched"
  }
}
```

**WebSocket事件类型**:

```typescript
// 服务端 → 客户端
{
  type: "progress",     // 进度更新
  data: { progress: 50, message: "..." }
}

{
  type: "log",          // 日志输出
  data: { level: "info", message: "..." }
}

{
  type: "error",        // 错误通知
  data: { message: "..." }
}

{
  type: "completed",    // 任务完成
  data: { task_id: "...", report_url: "..." }
}

// 客户端 → 服务端
{
  type: "subscribe",    // 订阅任务
  data: { task_id: "..." }
}

{
  type: "unsubscribe"   // 取消订阅
}
```

---

### 🔧 核心代码实现示例

**后端：FastAPI主应用** ([backend/app/main.py](backend/app/main.py)):
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import upload, tasks, reports, websocket
from app.config import settings

app = FastAPI(
    title="招标文件检查点验证工具",
    description="基于智谱AI的智能验证系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["websocket"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

**后端：LLM匹配服务** ([backend/app/services/llm_matcher.py](backend/app/services/llm_matcher.py)):
```python
from ai_test_scripts.llm_matcher_zhipuai import LLMMatcher
from app.tasks.celery_app import celery_app
from app.models.task import Task
import os

@celery_app.task
def run_llm_match_task(task_id: str, excel_path: str, json_path: str):
    """Celery异步任务：执行LLM匹配"""
    try:
        # 更新任务状态
        task = Task.get(task_id)
        task.update_status("processing", progress=10, message="开始LLM匹配...")

        # 调用现有的LLM匹配逻辑
        api_key = os.getenv("ZHIPUAI_API_KEY")
        matcher = LLMMatcher(api_key)

        task.update_message("正在调用智谱AI进行语义匹配...")
        result_path = matcher.match_all_checkpoints(excel_path, json_path)

        # 任务完成
        task.update_status(
            "completed",
            progress=100,
            message="验证完成",
            result={"report_path": result_path}
        )

        return {"task_id": task_id, "status": "completed"}

    except Exception as e:
        task.update_status("failed", message=f"验证失败: {str(e)}")
        raise
```

**前端：Vue主应用** ([frontend/src/App.vue](frontend/src/App.vue)):
```vue
<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1>招标文件检查点验证工具</h1>
    </el-header>

    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ElContainer, ElHeader, ElMain } from 'element-plus'
</script>

<style scoped>
.app-container {
  height: 100vh;
}
.app-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
}
</style>
```

**前端：文件上传组件** ([frontend/src/components/FileUploader.vue](frontend/src/components/FileUploader.vue)):
```vue
<template>
  <div class="upload-container">
    <el-upload
      drag
      :action="uploadUrl"
      :on-success="handleSuccess"
      :on-error="handleError"
      :before-upload="beforeUpload"
      :data="{ type: fileType }"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        拖拽文件到此处或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 .xlsx, .json 格式文件，文件大小不超过 50MB
        </div>
      </template>
    </el-upload>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElUpload, ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  fileType: 'excel' | 'json'
}>()

const emit = defineEmits<{
  uploaded: [fileId: string, filename: string]
}>()

const uploadUrl = ref('/api/v1/upload')

const beforeUpload = (file: File) => {
  const isValid = props.fileType === 'excel'
    ? file.name.endsWith('.xlsx')
    : file.name.endsWith('.json')

  const isLt50M = file.size / 1024 / 1024 < 50

  if (!isValid) {
    ElMessage.error(`请上传 ${props.fileType === 'excel' ? '.xlsx' : '.json'} 格式文件`)
    return false
  }
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

const handleSuccess = (response: any) => {
  if (response.code === 200) {
    ElMessage.success('上传成功')
    emit('uploaded', response.data.file_id, response.data.filename)
  }
}

const handleError = () => {
  ElMessage.error('上传失败')
}
</script>
```

**前端：WebSocket实时进度** ([frontend/src/api/websocket.ts](frontend/src/api/websocket.ts)):
```typescript
export class TaskWebSocket {
  private ws: WebSocket | null = null
  private taskId: string
  private handlers: Map<string, (data: any) => void>

  constructor(taskId: string) {
    this.taskId = taskId
    this.handlers = new Map()
  }

  connect() {
    const wsUrl = `ws://localhost:8000/api/v1/ws/${this.taskId}`
    this.ws = new WebSocket(wsUrl)

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      const handler = this.handlers.get(message.type)
      if (handler) {
        handler(message.data)
      }
    }

    this.ws.onerror = () => {
      console.error('WebSocket error')
    }

    this.ws.onclose = () => {
      console.log('WebSocket closed')
    }
  }

  on(event: string, handler: (data: any) => void) {
    this.handlers.set(event, handler)
  }

  disconnect() {
    this.ws?.close()
  }
}
```

---

### 🚀 部署配置详解

**Docker Compose配置** ([docker-compose.yml](docker-compose.yml)):
```yaml
version: '3.8'

services:
  # FastAPI后端
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ZHIPUAI_API_KEY=${ZHIPUAI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/outputs:/app/outputs
    depends_on:
      - redis

  # Celery Worker
  celery:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      - ZHIPUAI_API_KEY=${ZHIPUAI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/outputs:/app/outputs
    depends_on:
      - redis

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend

volumes:
  redis_data:
```

**Nginx配置** ([nginx/nginx.conf](nginx/nginx.conf)):
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API代理
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # WebSocket代理
        location /api/v1/ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

---

### 📊 核心功能实现流程

**1. LLM验证完整流程**:

```
用户操作:
  1. 上传Excel标注文件 → 获得file_id_1
  2. 上传JSON算法结果 → 获得file_id_2
  3. 点击"开始验证"按钮

前端处理:
  4. 调用 POST /api/v1/tasks/match
  5. 获得 task_id
  6. 建立WebSocket连接
  7. 跳转到进度页面

后端处理:
  8. FastAPI接收请求
  9. 创建任务记录 (status=pending)
  10. 提交Celery异步任务

Celery Worker执行:
  11. 从Redis读取任务
  12. 更新状态为 processing
  13. 读取上传的文件
  14. 调用 LLMMatcher (复用现有代码)
  15. 逐个处理检查点
  16. 实时推送进度到Redis
  17. 生成Markdown报告
  18. 更新状态为 completed

前端实时显示:
  19. WebSocket接收进度更新
  20. 更新进度条 (45% → "正在处理检查点 3/10...")
  21. 显示实时日志
  22. 完成后显示"查看报告"按钮

用户查看报告:
  23. 点击"查看报告"
  24. 调用 GET /api/v1/reports/{task_id}
  25. 下载或预览Markdown文件
```

**2. 错误处理机制**:

```python
# 后端统一异常处理
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器错误: {str(exc)}",
            "data": None
        }
    )

# Celery任务错误处理
@celery_app.task(bind=True)
def run_llm_match_task(self, task_id: str, excel_path: str, json_path: str):
    try:
        # 任务逻辑
        pass
    except Exception as exc:
        # 自动重试（最多3次）
        raise self.retry(exc=exc, countdown=60, max_retries=3)
```

---

### 🔐 安全性考虑

**1. API密钥管理**:
```bash
# .env文件（不提交到git）
ZHIPUAI_API_KEY=your_api_key_here
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your_secret_key_here
```

**2. 文件安全**:
- 限制文件大小（50MB）
- 限制文件类型（.xlsx, .json）
- 文件名UUID化，避免路径遍历攻击
- 定期清理临时文件

**3. 访问控制**:
```python
# 添加API密钥认证（可选）
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
```

---

## 📝 详细实施计划

### Phase 1: Streamlit MVP（2-3周）

#### Week 1: 基础搭建
- [ ] 安装 Streamlit 和依赖
- [ ] 创建 streamlit_app.py 主框架
- [ ] 设计多页面结构（文件上传、API测试、LLM验证）
- [ ] 集成现有 Python 代码

#### Week 2: 核心功能
- [ ] 实现文件上传组件（支持拖拽）
- [ ] 集成 pytest API 测试流程
- [ ] 集成 LLM 匹配验证逻辑
- [ ] 添加实时日志显示

#### Week 3: 优化部署
- [ ] 添加报告预览和下载功能
- [ ] 优化UI和用户体验
- [ ] 本地测试和bug修复
- [ ] 部署到服务器或 Streamlit Cloud

**核心代码示例**:
```python
# streamlit_app.py
import streamlit as st
from ai_test_scripts.llm_matcher_zhipuai import LLMMatcher

st.title("招标文件检查点验证工具")

# 侧边栏配置
with st.sidebar:
    st.header("配置")
    api_key = st.text_input("智谱AI API Key", type="password")

# 两步骤验证流程
tab1, tab2 = st.tabs(["API测试", "LLM验证"])

with tab1:
    uploaded_file = st.file_uploader("上传招标文件PDF", type=['pdf'])
    if st.button("执行API测试"):
        # 调用现有pytest逻辑
        st.write("测试执行中...")

with tab2:
    excel_file = st.file_uploader("上传标注文件", type=['xlsx'])
    json_file = st.file_uploader("上传算法结果", type=['json'])
    if st.button("执行LLM验证"):
        matcher = LLMMatcher(api_key)
        result = matcher.match_all_checkpoints(excel_file, json_file)
        st.success(f"验证完成！报告: {result}")
```

---

### Phase 2: FastAPI + Vue3（2-3周，优化版）

#### Week 1: 核心功能开发

**Day 1-2: FastAPI 后端**
- [ ] 搭建 FastAPI 项目结构（0.5天）
- [ ] 实现文件上传API（1天）
- [ ] 集成现有LLM匹配逻辑（1天）

**Day 3-4: Vue3 前端**
- [ ] 初始化 Vue 3 + Vite 项目（0.5天）
- [ ] 安装 Element Plus UI组件库（0.5天）
- [ ] 实现文件上传界面（1天）
- [ ] 实现报告展示页面（1天）

**Day 5: 异步任务与联调**
- [ ] 集成 Celery 异步任务（0.5天）
- [ ] 前后端联调（0.5天）

#### Week 2: 优化与部署

**Day 6-7: UI/UX 优化**
- [ ] 添加实时进度显示（WebSocket）（0.5天）
- [ ] 添加实时日志显示（0.5天）
- [ ] 优化界面交互体验（1天）

**Day 8-9: 稳定性提升**
- [ ] 异常处理和错误提示（1天）
- [ ] 性能测试和优化（1天）

**Day 10: 部署上线**
- [ ] Docker容器化（0.5天）
- [ ] 生产环境部署（0.5天）

**时间对比**：
- 传统开发：4-6周（从零编写）
- AI辅助开发：2-3周（代码复用90% + Vue Skills）
- **推荐节奏：每天3-4小时，2周完成**

**前端代码示例**:
```vue
<!-- src/components/FileUploader.vue -->
<template>
  <el-upload
    drag
    action="/api/v1/upload"
    @success="handleSuccess"
  >
    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
    <div class="el-upload__text">拖拽文件到此处或<em>点击上传</em></div>
  </el-upload>
</template>
```

**后端代码示例**:
```python
# main.py
from fastapi import FastAPI, UploadFile
from celery import Celery

app = FastAPI()
celery = Celery('tasks', broker='redis://localhost:6379')

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile):
    task = extract_checkpoints.delay(file.filename)
    return {"task_id": task.id}

@celery.task
def extract_checkpoints(file_path):
    # 调用现有pytest逻辑
    pass
```

---

## 🔄 开发路径建议

```
FastAPI + Vue3 (Week 1-2) ⭐ 推荐直接采用
       ↓
   MVP可用版本
       ↓
   完善优化部署
       ↓
   生产环境上线
```

**为什么直接采用 FastAPI + Vue3？**
- ✅ 时间成本相同（AI辅助后都是2-3周）
- ✅ 用户体验更优，可充分利用Vue Skills
- ✅ 符合技术偏好，利于长期维护
- ✅ 可扩展性强，支持未来功能扩展

---

## 📦 文件复用策略

**可直接复用的代码**:
- ✅ `ai_test_scripts/llm_matcher_zhipuai.py` - LLM匹配核心逻辑
- ✅ `test_cases/workflows/test_bid_check_workflow.py` - API测试流程
- ✅ `api_clients/algorithm_client.py` - API客户端
- ✅ `utils/encoding_helper.py` - 编码处理工具

**需要适配的部分**:
- 🔄 `bid_check_gui.py` - 从tkinter改为Web组件
- 🔄 文件路径处理（从本地路径到上传文件对象）

---

## 🚀 部署方案

### Streamlit 部署（最简单）
```bash
# 方案1: Streamlit Cloud
# 1. 推送代码到GitHub
# 2. 在 Streamlit Cloud 导入仓库
# 3. 配置环境变量（智谱AI API Key）
# 4. 一键部署

# 方案2: 内部服务器
pip install streamlit
streamlit run web_app/streamlit_app.py --server.port 8501
```

### FastAPI + Vue3 部署（生产级）
```bash
# Docker Compose 一键部署
docker-compose up -d

# 包含：
# - Nginx (反向代理)
# - Vue 3 前端
# - FastAPI 后端
# - Celery Worker
# - Redis (消息队列)
```

---

## 🎯 推荐行动方案

### 方案对比总结

| 特性 | Streamlit MVP | FastAPI + Vue3 |
|------|--------------|----------------|
| 开发时间 | 2-3周 | **2-3周（优化后）** |
| 技术难度 | 低（纯Python） | 中（需要前端知识）|
| 用户体验 | 基础可用 | **优秀（自定义UI）**|
| 并发支持 | 单用户/小团队 | **多用户** |
| 可扩展性 | 有限 | **优秀** |
| 部署复杂度 | 简单 | 中等 |
| 符合Vue偏好 | ❌ | ✅ |
| 符合时间要求 | ✅ | ✅ |
| **Vue Skills支持** | ❌ | ✅ |

### 最终推荐：直接采用 FastAPI + Vue3

**理由**：
1. **时间相同**：AI辅助后，两者都是2-3周
2. **体验更好**：Vue3可充分利用Vue Skills，代码质量有保障
3. **技术符合偏好**：满足Vue.js技术栈要求
4. **可扩展性强**：适合未来功能扩展

### 渐进式开发策略（2周）

**Week 1: MVP可用版本**
- 最简化的FastAPI后端
- 基础的Vue3前端
- 核心功能：文件上传 → LLM验证 → 下载报告
- **目标：这周就能让团队使用起来**

**Week 2: 完善优化**
- 添加WebSocket实时进度
- 优化UI/UX体验
- Docker部署
- 文档编写

### 开始步骤
1. **今天**: 搭建FastAPI项目结构
2. **明天**: 实现文件上传API
3. **第3天**: Vue3前端框架
4. **第4-5天**: 核心功能联调
5. **第2周**: 优化和部署

---

## 📊 成功标准

- [ ] 用户可通过浏览器访问工具
- [ ] 支持文件上传（PDF、Excel、JSON）
- [ ] 完整的两步验证流程
- [ ] 实时显示处理进度
- [ ] 在线预览和下载验证报告
- [ ] 支持多用户并发访问
- [ ] 响应时间 < 5秒（UI操作）
- [ ] LLM匹配准确率 > 85%

---

## ⚠️ 注意事项

1. **API密钥管理**:
   - 使用环境变量存储智谱AI API密钥
   - 不要在代码中硬编码

2. **文件安全**:
   - 上传文件存储在临时目录
   - 处理完成后自动清理
   - 限制文件大小（< 50MB）

3. **并发处理**:
   - Streamlit: 单用户模式（适合小团队）
   - FastAPI + Celery: 支持多用户并发

4. **错误处理**:
   - API调用失败重试机制
   - LLM超时处理
   - 友好的错误提示

---

## 🔗 相关资源

- **Streamlit文档**: https://docs.streamlit.io
- **FastAPI文档**: https://fastapi.tiangolo.com
- **Vue 3文档**: https://cn.vuejs.org
- **智谱AI文档**: https://open.bigmodel.cn

---

## 📋 方案对比总结

| 特性 | Streamlit MVP | FastAPI + Vue3 |
|------|--------------|----------------|
| 开发时间 | 2-3周 | **2-3周（优化后）** |
| 技术难度 | 低（纯Python） | 中（需要前端知识）|
| 用户体验 | 基础可用 | **优秀（自定义UI）**|
| 并发支持 | 单用户/小团队 | **多用户** |
| 可扩展性 | 有限 | **优秀** |
| 部署复杂度 | 简单 | 中等 |
| 符合Vue偏好 | ❌ | ✅ |
| 符合时间要求 | ✅ | ✅ |
| **Vue Skills支持** | ❌ | ✅ |

**最终推荐**: 直接采用 FastAPI + Vue3 方案

**优势总结**：
- ✅ 开发时间相同（都是2-3周）
- ✅ 用户体验更优
- ✅ 充分利用Vue Skills确保代码质量
- ✅ 符合技术偏好和长期规划
- ✅ 可扩展性强，适合未来功能扩展
