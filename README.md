# 招标文件检查点验证工具 - Web版

基于 FastAPI + Vue3 + 智谱AI 的招标文件检查点智能验证系统

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- Node.js 20+
- Redis 7.x
- Docker & Docker Compose（可选）

### 2. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的智谱AI API密钥：

```bash
ZHIPUAI_API_KEY=your_api_key_here
```

### 3. 使用 Docker Compose 启动（推荐）

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务启动后：
- 前端: http://localhost
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 4. 本地开发

#### 后端开发

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

#### 启动 Celery Worker

```bash
cd backend

# 启动Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info
```

#### 启动Redis

```bash
# Windows
redis-server

# Linux/Mac
redis-server /usr/local/etc/redis.conf
```

## 📖 使用说明

### 验证流程

1. **上传文件**
   - 点击"开始验证"按钮
   - 上传Excel标注文件（.xlsx格式）
   - 上传JSON算法结果（.json格式）

2. **AI验证**
   - 点击"开始验证"按钮
   - 系统自动调用智谱AI进行语义匹配
   - 实时显示处理进度

3. **查看报告**
   - 验证完成后自动跳转到报告页面
   - 可在线预览或下载Markdown格式报告

### 功能特点

- ✅ **AI语义匹配**: 基于智谱AI的深度语义理解
- ✅ **实时进度**: WebSocket实时推送处理进度
- ✅ **准确率高**: 智能判断检查点是否匹配
- ✅ **详细报告**: 生成包含完整分析结果的验证报告

## 🏗️ 项目结构

```
.
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   ├── tasks/         # Celery任务
│   │   └── main.py        # 应用入口
│   ├── uploads/           # 上传文件目录
│   ├── outputs/           # 生成报告目录
│   └── requirements.txt   # Python依赖
│
├── frontend/               # Vue3前端
│   ├── src/
│   │   ├── api/          # API调用
│   │   ├── components/   # Vue组件
│   │   ├── views/        # 页面视图
│   │   ├── stores/       # Pinia状态管理
│   │   └── router/       # 路由配置
│   ├── package.json      # Node依赖
│   └── vite.config.ts    # Vite配置
│
├── docker-compose.yml     # Docker编排配置
└── README.md             # 本文档
```

## 🔧 API文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的API文档。

### 主要API端点

- `POST /api/v1/upload` - 上传文件
- `POST /api/v1/tasks/match` - 创建验证任务
- `GET /api/v1/tasks/{task_id}` - 查询任务状态
- `GET /api/v1/reports/{task_id}` - 下载验证报告
- `WS /api/v1/ws/{task_id}` - WebSocket实时推送

## 🔐 安全说明

- API密钥通过环境变量配置，不要提交到代码仓库
- 上传文件限制最大50MB
- 支持的文件类型：.xlsx, .json, .pdf
- 定期清理临时文件

## 📝 技术栈

- **后端**: FastAPI 0.110 + Celery + Redis
- **前端**: Vue 3 + Vite + Element Plus + Pinia
- **AI**: 智谱AI glm-4-flash
- **部署**: Docker + Nginx

## 🐛 故障排查

### 后端无法启动

1. 检查环境变量是否正确配置
2. 确保Redis服务正常运行
3. 查看日志: `docker-compose logs backend`

### 前端无法连接后端

1. 确认后端服务已启动: http://localhost:8000/health
2. 检查CORS配置
3. 查看浏览器控制台错误信息

### Celery任务不执行

1. 确认Celery Worker已启动
2. 检查Redis连接
3. 查看Worker日志: `docker-compose logs celery`

## 📄 许可证

本项目仅供内部使用。

## 🤝 贡献

欢迎提交问题和改进建议。
