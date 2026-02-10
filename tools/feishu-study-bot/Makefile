.PHONY: help dev install build up down restart logs clean test db-init

# 默认目标
help:
	@echo "飞书学习机器人 - 常用命令"
	@echo ""
	@echo "开发命令:"
	@echo "  make install     - 安装依赖 (使用 uv)"
	@echo "  make dev         - 启动开发服务器"
	@echo "  make db-init     - 初始化数据库"
	@echo "  make test        - 运行测试"
	@echo ""
	@echo "Docker 命令:"
	@echo "  make build       - 构建 Docker 镜像"
	@echo "  make up          - 启动服务"
	@echo "  make down        - 停止服务"
	@echo "  make restart     - 重启服务"
	@echo "  make logs        - 查看日志"
	@echo "  make clean       - 清理容器和镜像"

# 安装依赖
install:
	@echo "📦 安装依赖..."
	uv sync --all-extras

# 开发模式启动
dev:
	@echo "🚀 启动开发服务器..."
	uv run python app.py

# 初始化数据库
db-init:
	@echo "🗄️  初始化数据库..."
	uv run python -c "from models.database import init_db; init_db()"

# 运行测试
test:
	@echo "🧪 运行测试..."
	uv run pytest -v

# Docker 构建
build:
	@echo "🏗️  构建 Docker 镜像..."
	docker-compose build

# Docker 启动
up:
	@echo "🚀 启动服务..."
	docker-compose up -d

# Docker 停止
down:
	@echo "🛑 停止服务..."
	docker-compose down

# Docker 重启
restart:
	@echo "🔄 重启服务..."
	docker-compose restart

# 查看日志
logs:
	docker-compose logs -f

# 清理
clean:
	@echo "🧹 清理..."
	docker-compose down -v --remove-orphans
	docker image rm feishu-study-bot:latest 2>/dev/null || true
