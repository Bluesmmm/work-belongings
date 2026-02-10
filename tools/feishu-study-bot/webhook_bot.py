#!/usr/bin/env python3
"""
飞书学习监督机器人 - Webhook 模式
使用飞书自定义机器人 Webhook 发送定时提醒
"""
import os
import sys
import time
import threading
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import init_db
from services.webhook_scheduler import WebhookScheduler


def main():
    """主函数"""
    print("=" * 50)
    print("🤖 飞书学习监督机器人 (Webhook 模式)")
    print("=" * 50)
    print()

    # 初始化数据库
    print("📦 初始化数据库...")
    init_db()
    print("✅ 数据库已就绪")
    print()

    # 启动定时任务
    print("⏰ 启动定时任务...")
    scheduler = WebhookScheduler()
    scheduler.start()
    print()

    print("=" * 50)
    print("✅ 机器人已启动！")
    print()
    print("📋 定时任务:")
    print("   • 每日学习提醒: 09:00")
    print("   • 打卡提醒: 21:00")
    print("   • 周报生成: 周日 20:00")
    print()
    print("💡 提示:")
    print("   • 按 Ctrl+C 停止服务")
    print("   • 消息将发送到配置的 Webhook 群聊")
    print("=" * 50)
    print()

    # 保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("🛑 正在停止服务...")
        scheduler.shutdown()
        print("✅ 服务已停止")


if __name__ == "__main__":
    main()
