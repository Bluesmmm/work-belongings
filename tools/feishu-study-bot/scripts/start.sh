#!/bin/bash
# 飞书学习监督机器人启动脚本 (使用 uv)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助
show_help() {
    echo -e "${BLUE}飞书学习监督机器人启动脚本${NC}"
    echo ""
    echo "用法: ./start.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -d, --daemon        后台运行"
    echo "  --no-deps           跳过依赖安装"
    echo "  -h, --help          显示帮助"
    echo ""
    echo "示例:"
    echo "  ./start.sh              # 前台运行"
    echo "  ./start.sh -d           # 后台运行"
    echo "  ./start.sh --no-deps -d # 后台运行(跳过依赖)"
}

# 检查 uv
check_uv() {
    if ! command -v uv &> /dev/null; then
        echo -e "${YELLOW}未找到 uv，正在安装...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
}

# 检查并安装依赖
check_deps() {
    if [ "$SKIP_DEPS" != true ]; then
        echo -e "${BLUE}📦 同步依赖...${NC}"
        uv sync --all-extras
    fi
}

# 检查环境变量
check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}警告: 未找到 .env 文件，使用示例配置${NC}"
        cp .env.example .env
        echo -e "${RED}请编辑 .env 文件配置飞书应用凭证！${NC}"
        exit 1
    fi

    # 加载环境变量
    export $(grep -v '^#' .env | grep -v '^$' | xargs)

    if [ -z "$FEISHU_APP_ID" ] || [[ "$FEISHU_APP_ID" == cli_xxxxxx* ]]; then
        echo -e "${RED}错误: 请在 .env 文件中配置有效的 FEISHU_APP_ID${NC}"
        exit 1
    fi

    if [ -z "$FEISHU_APP_SECRET" ] || [[ "$FEISHU_APP_SECRET" == xxxxxxxx* ]]; then
        echo -e "${RED}错误: 请在 .env 文件中配置有效的 FEISHU_APP_SECRET${NC}"
        exit 1
    fi
}

# 初始化数据库
init_db() {
    if [ ! -f "study_bot.db" ] && [ ! -f "data/study_bot.db" ]; then
        echo -e "${BLUE}📦 初始化数据库...${NC}"
        uv run python -c "from models.database import init_db; init_db()"
        echo -e "${GREEN}✅ 数据库已初始化${NC}"
    fi
}

# 显示启动信息
show_startup_info() {
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}🤖 飞书学习监督机器人${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${BLUE}模式: HTTP 回调${NC}"
    echo -e "${BLUE}地址: http://${HOST:-0.0.0.0}:${PORT:-8000}${NC}"
    echo ""
    echo -e "${YELLOW}配置文件: .env${NC}"
    echo -e "${YELLOW}数据库: study_bot.db${NC}"
    echo ""
    echo -e "${GREEN}按 Ctrl+C 停止服务${NC}"
    echo ""
}

# 主函数
main() {
    local DAEMON=false

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--daemon)
                DAEMON=true
                shift
                ;;
            --no-deps)
                SKIP_DEPS=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}未知选项: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done

    # 检查环境
    check_uv
    check_deps
    check_env
    init_db

    # 显示启动信息
    show_startup_info

    # 启动服务
    if [ "$DAEMON" == true ]; then
        # 后台运行
        nohup uv run python app.py > logs/bot.log 2>&1 &

        PID=$!
        mkdir -p logs
        echo $PID > logs/bot.pid
        echo -e "${GREEN}✅ 服务已在后台启动 (PID: $PID)${NC}"
        echo -e "${YELLOW}日志: tail -f logs/bot.log${NC}"
        echo -e "${YELLOW}停止: kill $PID${NC}"
    else
        # 前台运行
        mkdir -p logs
        uv run python app.py
    fi
}

# 运行主函数
main "$@"
