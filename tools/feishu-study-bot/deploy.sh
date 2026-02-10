#!/bin/bash
# 飞书学习机器人 - 远程部署脚本

set -e

SERVER="user@your-server.com"  # 修改为你的服务器
APP_DIR="/opt/feishu-study-bot"

echo "📦 开始部署..."

# 1. 上传代码
echo "📤 上传代码..."
rsync -avz --exclude='*.pyc' --exclude='.venv' --exclude='__pycache__' \
  --exclude='study_bot.db' --exclude='.git' \
  ./ $SERVER:$APP_DIR/

# 2. 远程安装依赖并重启
echo "🔧 远程配置..."
ssh $SERVER << 'ENDSSH'
cd $APP_DIR

# 安装 uv（如果没有）
command -v uv >/dev/null 2>&1 || { 
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
}

# 安装依赖
uv sync

# 重启服务
sudo systemctl restart feishu-bot
sudo systemctl status feishu-bot
ENDSSH

echo "✅ 部署完成！"
