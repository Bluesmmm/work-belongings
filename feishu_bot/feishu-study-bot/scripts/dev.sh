#!/bin/bash
# 开发环境启动脚本

set -e

echo "🚀 启动飞书学习机器人 (开发模式)"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "📦 正在安装 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，从 .env.example 创建..."
    cp .env.example .env
    echo "❗ 请编辑 .env 文件，填入你的飞书应用凭证"
    exit 1
fi

# 同步依赖
echo "📦 同步依赖..."
uv sync

# 初始化数据库
echo "🗄️  初始化数据库..."
uv run python -c "from models.database import init_db; init_db()"

# 启动服务
echo "🤖 启动机器人..."
uv run python app.py
