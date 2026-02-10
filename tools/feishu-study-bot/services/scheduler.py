"""定时任务调度器"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config.settings import settings
from models.database import get_db
from services.plan_service import PlanService
from services.checkin_service import CheckInService
from services.report_service import ReportService
from cards.templates import CardBuilder
from utils.feishu_client import feishu_client
from utils.date_utils import date_utils


class StudyScheduler:
    """学习提醒调度器"""
    
    def __init__(self, chat_id: str = None):
        self.scheduler = AsyncIOScheduler()
        self.chat_id = chat_id or settings.default_chat_id
        self.card_builder = CardBuilder()
    
    def start(self):
        """启动调度器"""
        # 每日学习提醒
        self.scheduler.add_job(
            self.daily_reminder,
            CronTrigger(
                hour=settings.daily_reminder_hour,
                minute=settings.daily_reminder_minute
            ),
            id="daily_reminder",
            replace_existing=True
        )
        
        # 打卡提醒
        self.scheduler.add_job(
            self.checkin_reminder,
            CronTrigger(
                hour=settings.checkin_reminder_hour,
                minute=settings.checkin_reminder_minute
            ),
            id="checkin_reminder",
            replace_existing=True
        )
        
        # 周报生成
        day_map = {
            "mon": 0, "tue": 1, "wed": 2, "thu": 3, 
            "fri": 4, "sat": 5, "sun": 6
        }
        self.scheduler.add_job(
            self.weekly_report,
            CronTrigger(
                day_of_week=day_map.get(settings.weekly_report_day, 6),
                hour=settings.weekly_report_hour,
                minute=settings.weekly_report_minute
            ),
            id="weekly_report",
            replace_existing=True
        )
        
        self.scheduler.start()
        print("定时任务已启动")
    
    async def daily_reminder(self):
        """每日学习提醒"""
        print(f"[{datetime.now()}] 发送每日提醒")
        
        db = next(get_db())
        try:
            plan_service = PlanService(db)
            week = plan_service.get_current_week()
            
            if not week:
                print("未找到当前周计划")
                return
            
            deliverables = plan_service.get_week_deliverables(week.id)
            
            card = self.card_builder.daily_reminder(
                week_num=week.week_num,
                stage=week.stage,
                theme=week.theme,
                focus=week.focus,
                deliverables=[
                    {"id": d.id, "name": d.name, "done": d.is_completed}
                    for d in deliverables
                ],
                tips=week.risks if week.risks else ""
            )
            
            await feishu_client.send_card(self.chat_id, card)
            
        finally:
            db.close()
    
    async def checkin_reminder(self):
        """打卡提醒"""
        print(f"[{datetime.now()}] 发送打卡提醒")
        
        # 检查今天是否已经打卡
        db = next(get_db())
        try:
            # 这里简化处理，实际应该检查特定用户
            message = (
                "⏰ **今日打卡提醒**\n\n"
                "今天的学习结束了吗？快来记录一下你的进度吧！\n\n"
                "使用命令：`/打卡` 或直接点击卡片"
            )
            
            # 发送提醒卡片
            card = {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": "orange",
                    "title": {"tag": "plain_text", "content": "⏰ 打卡提醒"}
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "今天的学习结束了吗？快来记录一下你的进度吧！"
                        }
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "📝 去打卡"},
                                "type": "primary",
                                "value": {"action": "checkin"}
                            }
                        ]
                    }
                ]
            }
            
            await feishu_client.send_card(self.chat_id, card)
            
        finally:
            db.close()
    
    async def weekly_report(self):
        """生成并发送周报"""
        print(f"[{datetime.now()}] 生成周报")
        
        db = next(get_db())
        try:
            # 获取上周（因为周报是周日发送，总结的是刚结束的一周）
            current_week, _, _ = date_utils.get_current_week_info()
            report_week = current_week - 1 if current_week > 1 else 1
            
            plan_service = PlanService(db)
            report_service = ReportService(db)
            
            # 生成周报
            report = report_service.generate_weekly_report(
                user_id="default_user",  # 实际应该使用真实用户ID
                week_num=report_week
            )
            
            if not report:
                print(f"生成第{report_week}周报告失败")
                return
            
            # 解析报告内容
            import json
            content = json.loads(report.card_content)
            
            # 构建卡片
            week = plan_service.get_week_by_num(report_week)
            deliverables = plan_service.get_week_deliverables(week.id)
            
            highlights = json.loads(report.highlights) if report.highlights else []
            risks = json.loads(report.risks) if report.risks else []
            next_week = json.loads(report.next_week_preview) if report.next_week_preview else {}
            
            card = self.card_builder.weekly_report(
                week_num=report_week,
                stage=content.get("stage", ""),
                theme=content.get("theme", ""),
                progress=content.get("progress", 0),
                stats=content.get("stats", {}),
                deliverables=[
                    {"id": d.id, "name": d.name, "done": d.is_completed}
                    for d in deliverables
                ],
                highlights=highlights,
                risks=risks,
                next_week=next_week
            )
            
            await feishu_client.send_card(self.chat_id, card)
            
            # 标记已发送
            report.sent_to_chat = True
            db.commit()
            
        finally:
            db.close()
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
