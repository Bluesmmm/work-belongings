#!/bin/bash
# 远程服务器一键部署脚本
# 用法: ./scripts/deploy_remote.sh [server-alias]
# 默认: seeta

set -e

SERVER="${1:-seeta}"
PROJECT_DIR="vllm-delivery-template"
REMOTE_WORK_DIR="/root/$PROJECT_DIR"

echo "=========================================="
echo "  vLLM 远程服务器部署脚本"
echo "  目标服务器: $SERVER"
echo "=========================================="
echo ""

# 1. 检查本地文件
echo "📋 检查本地项目文件..."
if [ ! -f "serving/launch.py" ] || [ ! -f "serving/config.yaml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi
echo "✅ 本地文件检查完成"
echo ""

# 2. 测试 SSH 连接
echo "🔌 测试 SSH 连接..."
if ! ssh -o ConnectTimeout=5 "$SERVER" "echo '连接成功'" > /dev/null 2>&1; then
    echo "❌ 无法连接到服务器: $SERVER"
    exit 1
fi
echo "✅ SSH 连接正常"
echo ""

# 3. 检查远程服务器环境
echo "🔍 检查远程服务器环境..."
ssh "$SERVER" << 'ENDSSH'
echo "--- 系统信息 ---"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Python: $(python3 --version)"
echo ""
echo "--- GPU 信息 ---"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo ""

# 检查 CUDA
if command -v nvcc &> /dev/null; then
    echo "CUDA: $(nvcc --version | grep release | awk '{print $5}' | cut -d',' -f1)"
else
    echo "⚠️  CUDA 工具未在 PATH 中"
fi
ENDSSH
echo ""

# 4. 上传项目文件
echo "📦 上传项目文件到服务器..."
# 创建远程目录
ssh "$SERVER" "mkdir -p $REMOTE_WORK_DIR"

# 同步文件（排除 .venv, __pycache__, .git 等）
rsync -avz --progress \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.pytest_cache' \
    --exclude='*.log' \
    ./ "$SERVER:$REMOTE_WORK_DIR/"

echo "✅ 文件上传完成"
echo ""

# 5. 远程安装和配置
echo "🔧 远程安装依赖..."
ssh "$SERVER" << 'ENDSSH'
set -e
cd /root/vllm-delivery-template

echo "--- 安装 uv 包管理器 ---"
if ! command -v uv &> /dev/null; then
    echo "正在安装 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "uv 版本: $(uv --version)"
echo ""

echo "--- 创建虚拟环境 ---"
if [ ! -d ".venv" ]; then
    uv venv
fi
echo ""

echo "--- 激活虚拟环境并安装依赖 ---"
source .venv/bin/activate
uv pip install -e .
echo ""

echo "--- 配置 HuggingFace 镜像（加速模型下载）---"
mkdir -p ~/.huggingface
cat > ~/.huggingface/endpoints.json << 'EOF'
{
  "hf_endpoint": "https://hf-mirror.com"
}
EOF

echo "--- 验证安装 ---"
python3 -c "import vllm; print(f'vLLM 版本: {vllm.__version__}')"
echo ""

echo "✅ 依赖安装完成"
ENDSSH
echo ""

# 6. 创建启动脚本（包含完整 CUDA 环境变量）
echo "📝 创建远程启动脚本..."
ssh "$SERVER" << 'ENDSSH'
cat > /root/vllm-delivery-template/start_vllm.sh << 'STARTSCRIPT'
#!/bin/bash
# vLLM 启动脚本 - 完整环境变量配置
# 这是让 V1 engine 正常编译和运行的关键配置

# CUDA 路径（gcc 编译需要）
export PATH=/usr/local/cuda-12.4/bin:$PATH
export CUDA_HOME=/usr/local/cuda-12.4
export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH
export CPATH=/usr/local/cuda-12.4/include:$CPATH
export LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LIBRARY_PATH

# Triton 缓存（放在数据盘）
export TRITON_CACHE_DIR=/root/autodl-tmp/triton_cache
mkdir -p $TRITON_CACHE_DIR

# HuggingFace 配置
export HF_HOME=/root/autodl-tmp/hf_cache
export HF_ENDPOINT=https://hf-mirror.com

# 项目目录
cd /root/vllm-delivery-template

# 激活虚拟环境
source .venv/bin/activate

# 启动 vLLM
echo "=== vLLM 环境配置 ==="
echo "CUDA_HOME: $CUDA_HOME"
echo "TRITON_CACHE_DIR: $TRITON_CACHE_DIR"
echo "HF_HOME: $HF_HOME"
echo "========================"
echo ""

exec vllm serve Qwen/Qwen2.5-3B-Instruct --port 8000 "$@"
STARTSCRIPT

chmod +x /root/vllm-delivery-template/start_vllm.sh
echo "✅ 启动脚本已创建: start_vllm.sh"
ENDSSH
echo ""

# 7. 创建 systemd 服务文件（可选）
echo "📝 创建 systemd 服务配置..."
ssh "$SERVER" << 'ENDSSH'
sudo tee /etc/systemd/system/vllm.service > /dev/null << 'EOF'
[Unit]
Description=vLLM Inference Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/vllm-delivery-template
Environment="PATH=/root/vllm-delivery-template/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HF_ENDPOINT=https://hf-mirror.com"
ExecStart=/root/vllm-delivery-template/.venv/bin/python serving/launch.py
Restart=always
RestartSec=10
StandardOutput=append:/root/vllm-delivery-template/logs/vllm-service.log
StandardError=append:/root/vllm-delivery-template/logs/vllm-service-error.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemd 服务文件已创建"
echo "   启用命令: sudo systemctl enable vllm"
echo "   启动命令: sudo systemctl start vllm"
echo "   状态查看: sudo systemctl status vllm"
ENDSSH
echo ""

# 8. 完成
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "📌 后续操作："
echo ""
echo "方式一: 使用 tmux 保持会话（推荐开发时使用）"
echo "  ssh $SERVER"
echo "  tmux new -s vllm"
echo "  cd $REMOTE_WORK_DIR && ./start_vllm.sh"
echo "  # Ctrl+B, D 分离会话"
echo "  # tmux attach -t vllm 重新连接"
echo ""
echo "方式二: 使用 systemd 服务（推荐生产环境）"
echo "  ssh $SERVER"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable vllm"
echo "  sudo systemctl start vllm"
echo "  sudo journalctl -u vllm -f  # 查看日志"
echo ""
echo "方式三: 手动启动（使用完整环境变量）"
echo "  ssh $SERVER"
echo "  cd $REMOTE_WORK_DIR"
echo "  ./start_vllm.sh"
echo ""
echo "方式四: 直接运行 vllm 命令（需要手动设置环境变量）"
echo "  ssh $SERVER"
echo "  cd $REMOTE_WORK_DIR"
echo "  source .venv/bin/activate"
echo "  vllm serve Qwen/Qwen2.5-3B-Instruct --port 8000"
echo ""
echo "🔍 健康检查："
echo "  curl http://$(ssh $SERVER 'hostname -I | awk \"{print \\$1}\"'):8000/health"
echo ""
echo "📊 GPU 监控："
echo "  ssh $SERVER 'watch -n 1 nvidia-smi'"
echo ""
