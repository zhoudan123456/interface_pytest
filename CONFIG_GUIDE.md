# 配置管理指南

## 📋 概述

本项目已实施三个最佳实践来管理敏感数据：
1. ✅ 使用环境变量
2. ✅ 敏感文件加入 .gitignore
3. ✅ 使用示例配置文件

---

## 🔧 快速开始

### 1. 安装依赖

```bash
# 安装 python-dotenv（推荐）
pip install python-dotenv
```

### 2. 配置环境变量

**方式一：使用 .env 文件（推荐）**

```bash
# 1. 复制示例文件
cp .env.example .env

# 2. 编辑 .env 文件，填入真实信息
```

**方式二：手动创建 .env 文件**

创建 `.env` 文件：
```ini
LOGIN_PHONE=17762546670
LOGIN_PASSWORD=your_password
API_HOST=https://test.intellibid.cn
```

### 3. 配置 YAML 数据文件

```bash
# 复制示例配置文件
cp test_data/config.example.yaml test_data/login.yaml

# 编辑 login.yaml，填入真实测试数据
```

---

## 📁 文件结构

```
project/
├── .env                          # 环境变量（不提交到Git）
├── .env.example                  # 环境变量示例（提交到Git）
├── .gitignore                    # Git忽略文件配置
├── conf/
│   └── server.ini               # 服务器配置（不提交到Git）
├── test_data/
│   ├── config.example.yaml     # 配置示例（提交到Git）
│   ├── login.yaml               # 登录配置（不提交到Git）
│   ├── extract.yaml            # 运行时数据（不提交到Git）
│   └── bid_generate.yaml       # 业务数据（不提交到Git）
└── utils/
    └── env_config.py            # 环境变量加载工具
```

---

## 🚀 在代码中使用环境变量

### 示例 1：在测试用例中使用

```python
from utils.env_config import get_env

class TestLogin:
    def test_login(self):
        # 从环境变量获取敏感信息
        phone = get_env('LOGIN_PHONE')
        password = get_env('LOGIN_PASSWORD')

        login_data = {
            'phone': phone,
            'password': password
        }
```

### 示例 2：在配置文件中使用

```python
import os
from utils.env_config import env_config

# 从环境变量读取配置
api_host = env_config.get('API_HOST', 'https://test.intellibid.cn')
login_phone = os.getenv('LOGIN_PHONE', '17762546670')
```

### 示例 3：动态加载配置

```python
from utils.env_config import EnvConfig

# 初始化配置
env = EnvConfig('.env')

# 获取配置
phone = env.get('LOGIN_PHONE')
timeout = env.get_int('TIMEOUT', default=30)
debug = env.get_bool('DEBUG', default=False)
```

---

## 🔒 安全最佳实践

### ✅ 应该做的

1. **使用环境变量** 存储敏感信息
   ```python
   password = os.getenv('DB_PASSWORD')
   ```

2. **示例文件** 只包含非敏感的示例数据
   ```yaml
   # config.example.yaml
   phone: YOUR_PHONE_NUMBER  # 示例值
   password: YOUR_PASSWORD    # 示例值
   ```

3. **.gitignore** 忽略所有敏感文件
   ```
   .env
   conf/server.ini
   test_data/*.yaml
   !test_data/*.example.yaml
   ```

### ❌ 不应该做的

1. **不要提交** 包含真实数据的文件到 Git
2. **不要在代码中硬编码** 敏感信息
   ```python
   # ❌ 错误：硬编码密码
   password = "CkwD9fqEWwxayspKWQIaQ..."

   # ✅ 正确：使用环境变量
   password = os.getenv('PASSWORD')
   ```

3. **不要在日志中输出** 敏感信息
   ```python
   # ❌ 错误
   print(f"Token: {token}")

   # ✅ 正确
   print(f"Token: {token[:10]}...")  # 只显示部分
   ```

---

## 📝 .gitignore 规则说明

```
# 环境变量文件
.env                              # 环境变量（敏感）
.env.local                        # 本地环境变量
.env.*.local                     # 其他环境

# YAML 数据文件
test_data/extract.yaml           # 运行时生成的数据
test_data/bid_generate.yaml     # 业务流程数据
test_data/*.yaml                 # 所有YAML文件
!test_data/*.example.yaml       # 除了示例文件

# 配置文件
conf/server.ini                   # 服务器配置（包含token）
```

---

## 🔄 团队协作流程

### 新成员加入项目

1. **克隆项目**
   ```bash
   git clone https://github.com/xxx/project.git
   cd project
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   pip install python-dotenv
   ```

3. **配置环境**
   ```bash
   # 复制示例配置
   cp .env.example .env
   cp test_data/config.example.yaml test_data/login.yaml

   # 编辑配置，填入真实信息
   notepad .env
   notepad test_data/login.yaml
   ```

4. **运行测试**
   ```bash
   pytest -v
   ```

---

## 🛠️ 工具函数说明

### `utils/env_config.py` 提供的函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `get_env(key, default)` | 获取字符串环境变量 | `get_env('API_HOST')` |
| `get_env_int(key, default)` | 获取整数环境变量 | `get_env_int('TIMEOUT', 30)` |
| `get_env_bool(key, default)` | 获取布尔环境变量 | `get_env_bool('DEBUG', False)` |
| `env_config.get(key)` | 面向对象方式获取 | `env_config.get('LOGIN_PHONE')` |

---

## 📚 参考资料

- [python-dotenv 文档](https://github.com/theskumar/python-dotenv)
- [Git 忽略文件配置](https://git-scm.com/docs/gitignore)
- [环境变量最佳实践](https://12factor.net/config)

---

## ❓ 常见问题

### Q1: 如何检查环境变量是否加载成功？

```python
from utils.env_config import env_config

# 打印所有环境变量（仅用于调试）
import os
print(dict(os.environ))
```

### Q2: 推送时仍然报错包含敏感信息？

```bash
# 清理 Git 历史中的敏感信息
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch test_data/extract.yaml' \
  --prune-empty HEAD

# 强制推送
git push origin main --force
```

### Q3: 如何在不同环境使用不同配置？

```bash
# 开发环境
cp .env.dev .env

# 测试环境
cp .env.test .env

# 生产环境
cp .env.prod .env
```

---

## ✅ 验证配置

运行以下命令验证配置是否正确：

```bash
# 1. 检查 .gitignore 是否生效
git check-ignore -v .env
git check-ignore -v test_data/extract.yaml

# 2. 检查哪些文件会被提交
git status

# 3. 运行测试
pytest -v
```

---

**配置完成后，请运行以下命令提交更改：**

```bash
git add .env.example test_data/config.example.yaml .gitignore utils/env_config.py utils/__init__.py
git commit -m "chore: 添加环境变量支持和配置文件管理"
git push origin main
```
