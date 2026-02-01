#!/usr/bin/env python3
"""
飞书学习监督机器人主入口
"""
import os
import sys
import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from lark_oapi import Client
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
from lark_oapi.card.builder import CardActionHandler, CardAction

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from models.database import init_db
from bot.handlers import message_handler, card_callback_handler
from services.scheduler import StudyScheduler
from utils.feishu_client import feishu_client


# 全局调度器
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global scheduler
    
    # 启动时初始化
    print("🚀 正在启动学习监督机器人...")
    
    # 初始化数据库
    init_db()
    print("✅ 数据库已初始化")
    
    # 启动定时任务
    if settings.default_chat_id:
        scheduler = StudyScheduler(settings.default_chat_id)
        scheduler.start()
        print(f"✅ 定时任务已启动")
        print(f"   - 每日提醒: {settings.daily_reminder_hour:02d}:{settings.daily_reminder_minute:02d}")
        print(f"   - 打卡提醒: {settings.checkin_reminder_hour:02d}:{settings.checkin_reminder_minute:02d}")
        print(f"   - 周报生成: 每周{settings.weekly_report_day} {settings.weekly_report_hour:02d}:{settings.weekly_report_minute:02d}")
    else:
        print("⚠️ 未配置默认聊天ID，跳过启动定时任务")
    
    yield
    
    # 关闭时清理
    if scheduler:
        scheduler.shutdown()
        print("✅ 定时任务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="飞书学习监督机器人",
    description="为你的学习计划提供监督、打卡和汇报",
    version="1.0.0",
    lifespan=lifespan
)


def verify_signature(request: Request) -> bool:
    """验证飞书请求签名（可选）"""
    if not settings.feishu_encrypt_key:
        return True
    
    # 这里简化处理，实际应该根据飞书文档验证签名
    # https://open.feishu.cn/document/server-docs/event-subscription-guide/event-subscription-configure-/encrypt-key
    return True


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "study-bot"}


@app.post("/webhook/event")
async def handle_event(request: Request):
    """处理飞书事件推送"""
    body = await request.body()
    data = json.loads(body)
    
    # 处理URL验证
    if data.get("type") == "url_verification":
        challenge = data.get("challenge")
        return JSONResponse(content={"challenge": challenge})
    
    # 验证Token
    token = data.get("token")
    if settings.feishu_verification_token and token != settings.feishu_verification_token:
        return Response(status_code=403)
    
    # 处理事件
    event_type = data.get("header", {}).get("event_type")
    
    if event_type == "im.message.receive_v1":
        # 处理消息事件
        event_data = P2ImMessageReceiveV1.from_dict(data)
        await message_handler.handle_message(event_data)
    
    return Response(status_code=200)


@app.post("/webhook/card")
async def handle_card_action(request: Request):
    """处理卡片交互回调"""
    body = await request.body()
    data = json.loads(body)
    
    # 处理URL验证
    if data.get("type") == "url_verification":
        challenge = data.get("challenge")
        return JSONResponse(content={"challenge": challenge})
    
    # 解析卡片动作
    action_data = data.get("action", {})
    user_id = data.get("open_id", "")
    message_id = data.get("open_message_id", "")
    
    callback_data = {
        "action": action_data.get("value", {}).get("action"),
        "user_id": user_id,
        "message_id": message_id,
        **action_data.get("value", {}),
        **action_data.get("form_value", {})
    }
    
    # 处理回调
    await card_callback_handler.handle_callback(callback_data)
    
    return Response(status_code=200)


@app.get("/api/stats")
async def get_stats():
    """获取统计数据API"""
    from models.database import SessionLocal
    from services.checkin_service import CheckInService
    from services.plan_service import PlanService
    
    db = SessionLocal()
    try:
        checkin_service = CheckInService(db)
        plan_service = PlanService(db)
        
        stats = checkin_service.get_overall_stats("default_user")
        milestones = plan_service.get_all_milestones()
        
        return {
            "stats": stats,
            "milestones": [
                {
                    "name": m.name,
                    "target_week": m.target_week,
                    "completed": m.is_completed
                }
                for m in milestones
            ]
        }
    finally:
        db.close()


@app.post("/api/trigger/reminder")
async def trigger_reminder():
    """手动触发每日提醒（测试用）"""
    if scheduler:
        await scheduler.daily_reminder()
        return {"status": "ok", "message": "提醒已发送"}
    return {"status": "error", "message": "调度器未启动"}


@app.post("/api/trigger/report")
async def trigger_report():
    """手动触发周报生成（测试用）"""
    if scheduler:
        await scheduler.weekly_report()
        return {"status": "ok", "message": "周报已生成"}
    return {"status": "error", "message": "调度器未启动"}


def main():
    """主函数"""
    import uvicorn
    
    # 检查必要配置
    if not settings.feishu_app_id or not settings.feishu_app_secret:
        print("❌ 错误: 请在 .env 文件中配置飞书应用凭证")
        print("   FEISHU_APP_ID=your_app_id")
        print("   FEISHU_APP_SECRET=your_app_secret")
        sys.exit(1)
    
    print(f"🤖 学习监督机器人启动中...")
    print(f"   服务地址: http://{settings.host}:{settings.port}")
    print(f"   调试模式: {settings.debug}")
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )


if __name__ == "__main__":
    main()
