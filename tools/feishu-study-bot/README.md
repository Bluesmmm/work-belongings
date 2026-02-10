# 飞书学习监督机器人

> 为你的学习计划提供监督、打卡和汇报

基于 [FastAPI](https://fastapi.tiangolo.com/) + [uv](https://github.com/astral-sh/uv) 构建的飞书学习监督机器人，支持每日提醒、学习打卡、进度统计和周报生成。

## 特性

- 📚 **每日学习提醒** - 定时推送今日学习计划和重点
- ✅ **学习打卡** - 记录每日学习时长、完成度和满意度
- 📊 **进度统计** - 实时查看学习进度和里程碑完成情况
- 📈 **周报生成** - 自动生成每周学习报告
- 🤖 **飞书卡片交互** - 丰富的交互式卡片体验
- 🐳 **Docker 部署** - 一键部署到容器环境

## 目录结构

```
feishu-study-bot/
├── app.py                  # 应用入口
├── pyproject.toml          # 项目配置与依赖
├── Makefile                # 常用命令
├── Dockerfile              # Docker 镜像
├── docker-compose.yml      # Docker 编排
├── .env.example            # 环境变量示例
├── bot/                    # 机器人逻辑
│   └── handlers.py         # 消息和回调处理
├── cards/                  # 卡片模板
│   └── templates.py        # 飞书卡片构建器
├── config/                 # 配置文件
│   ├── settings.py         # 应用配置
│   └── schemas/            # 数据 schema
├── models/                 # 数据库模型
│   └── database.py         # SQLAlchemy 模型
├── services/               # 业务服务
│   ├── plan_service.py     # 计划管理
│   ├── checkin_service.py  # 打卡服务
│   ├── report_service.py   # 报告生成
│   └── scheduler.py        # 定时任务
├── utils/                  # 工具函数
│   ├── feishu_client.py    # 飞书 API 封装
│   └── date_utils.py       # 日期工具
└── scripts/                # 脚本文件
    ├── start.sh            # 启动脚本
    └── dev.sh              # 开发启动
```

## 快速开始

### 1. 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 配置环境

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env，填入飞书应用凭证
nano .env
```

必填环境变量：

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `FEISHU_APP_ID` | 飞书应用 ID | [飞书开放平台](https://open.feishu.cn/app) |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | 同上 |
| `DEFAULT_CHAT_ID` | 默认群聊 ID | 将机器人拉入群后获取 |

### 3. 启动服务

```bash
# 方式一：使用 Makefile（推荐）
make install
make dev

# 方式二：使用脚本
./scripts/start.sh

# 方式三：直接使用 uv
uv sync
uv run python app.py
```

### 4. 初始化数据库

首次运行会自动初始化数据库，或手动执行：

```bash
make db-init
# 或
uv run python -c "from models.database import init_db; init_db()"
```

## Docker 部署

```bash
# 构建并启动
make build
make up

# 查看日志
make logs

# 停止服务
make down
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `make install` | 安装依赖 |
| `make dev` | 启动开发服务器 |
| `make db-init` | 初始化数据库 |
| `make test` | 运行测试 |
| `make build` | 构建 Docker 镜像 |
| `make up` | 启动 Docker 服务 |
| `make down` | 停止 Docker 服务 |
| `make logs` | 查看 Docker 日志 |

## 机器人命令

在飞书中与机器人交互：

| 命令 | 说明 |
|------|------|
| `/今日` 或 `/今天` | 查看今日学习计划 |
| `/打卡` | 记录今日学习进度 |
| `/进度` | 查看整体学习进度 |
| `/里程碑` | 查看所有里程碑进度 |
| `/周报 [周数]` | 生成本周/指定周报告 |
| `/帮助` | 显示帮助信息 |

## 飞书应用配置

### 1. 创建应用

访问 [飞书开放平台](https://open.feishu.cn/app)，创建自建应用。

### 2. 配置权限

在应用权限管理中开通以下权限：

- `im:message` - 发送消息
- `im:message:group_at_msg` - 接收群消息
- `im:chat` - 访问群信息

### 3. 配置事件订阅

在事件订阅中添加请求地址：

```
事件订阅: https://your-domain.com/webhook/event
卡片回调: https://your-domain.com/webhook/card
```

订阅事件：
- `im.message.receive_v1` - 接收消息

### 4. 发布版本

配置完成后，发布应用版本即可使用。

## 开发

### 代码规范

项目使用 [Ruff](https://github.com/astral-sh/ruff) 进行代码检查：

```bash
# 检查代码
uv run ruff check .

# 格式化代码
uv run ruff format .
```

### 运行测试

```bash
make test
# 或
uv run pytest -v
```

## 配置说明

### 提醒时间配置

在 `.env` 中配置定时任务时间：

```bash
# 每日学习提醒
DAILY_REMINDER_HOUR=9
DAILY_REMINDER_MINUTE=0

# 每日打卡提醒
CHECKIN_REMINDER_HOUR=21
CHECKIN_REMINDER_MINUTE=0

# 周报生成
WEEKLY_REPORT_HOUR=20
WEEKLY_REPORT_MINUTE=0
WEEKLY_REPORT_DAY=sun  # mon, tue, wed, thu, fri, sat, sun
```

### 数据库配置

默认使用 SQLite，数据文件位于 `data/study_bot.db`（Docker 环境）或 `study_bot.db`（本地环境）。

## 技术栈

- **Web 框架**: [FastAPI](https://fastapi.tiangolo.com/)
- **包管理**: [uv](https://github.com/astral-sh/uv)
- **数据库**: [SQLAlchemy](https://www.sqlalchemy.org/) + SQLite
- **任务调度**: [APScheduler](https://github.com/agronholm/apscheduler)
- **飞书 SDK**: [lark-oapi](https://github.com/larksuite/oapi-sdk-python)

## 故障排查

### 服务启动失败

检查 `.env` 文件配置是否正确，特别是 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`。

### 定时任务不生效

确保配置了 `DEFAULT_CHAT_ID`，机器人需要知道向哪个群发送消息。

### Docker 构建失败

```bash
# 清理缓存重新构建
docker-compose down
docker system prune -a
docker-compose build --no-cache
```

## License

MIT License
