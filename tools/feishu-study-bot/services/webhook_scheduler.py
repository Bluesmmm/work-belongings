"""Webhook 定时任务调度器"""
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import SessionLocal, WeeklyPlan, Deliverable
from utils.date_utils import date_utils
from utils.webhook_client import webhook_client


class WebhookScheduler:
    """基于 Webhook 的定时任务调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self):
        """启动调度器"""
        # 每日学习提醒 (9:00)
        self.scheduler.add_job(
            self.daily_reminder,
            CronTrigger(hour=9, minute=0),
            id="daily_reminder",
            replace_existing=True
        )

        # 打卡提醒 (21:00)
        self.scheduler.add_job(
            self.checkin_reminder,
            CronTrigger(hour=21, minute=0),
            id="checkin_reminder",
            replace_existing=True
        )

        # 周报生成 (周日 20:00)
        self.scheduler.add_job(
            self.weekly_report,
            CronTrigger(day_of_week=6, hour=20, minute=0),  # 6=周日
            id="weekly_report",
            replace_existing=True
        )

        self.scheduler.start()
        print("✅ Webhook 定时任务已启动")
        print(f"   - 每日提醒: 09:00")
        print(f"   - 打卡提醒: 21:00")
        print(f"   - 周报生成: 周日 20:00")

    def daily_reminder(self):
        """每日学习提醒"""
        print(f"[{datetime.now()}] 发送每日提醒")

        db = SessionLocal()
        try:
            week = db.query(WeeklyPlan).filter(
                WeeklyPlan.week_num == date_utils.get_current_week_info()[0]
            ).first()

            if not week:
                webhook_client.send_text("📚 本周暂无学习计划")
                return

            # 获取交付物
            deliverables = db.query(Deliverable).filter(
                Deliverable.week_id == week.id
            ).all()

            # 构建消息（必须包含关键词 "今日"）
            deliv_list = "\n".join([
                f"  {'✅' if d.is_completed else '⏳'} {d.name}"
                for d in deliverables[:5]
            ])

            message = f"""📚 今日学习计划 (第{week.week_num}周)
━━━━━━━━━━━━━━━━━━━━
🎯 阶段: {week.stage}
📌 主题: {week.theme}

📝 今日重点:
{week.focus}

📦 本周交付物:
{deliv_list}

💡 Tips: {week.risks if week.risks else '坚持打卡，积跬步以至千里！'}
━━━━━━━━━━━━━━━━━━━━"""

            webhook_client.send_text(message)

        finally:
            db.close()

    def checkin_reminder(self):
        """打卡提醒"""
        print(f"[{datetime.now()}] 发送打卡提醒")

        message = """⏰ 今日学习打卡提醒
━━━━━━━━━━━━━━━━━━━━
今天的学习结束了吗？
快来记录一下你的进度吧！

💡 提示:
• 回顾今天完成的学习任务
• 记录投入时长
• 总结遇到的问题
━━━━━━━━━━━━━━━━━━━━"""

        webhook_client.send_text(message)

    def weekly_report(self):
        """周报生成"""
        print(f"[{datetime.now()}] 生成周报")

        db = SessionLocal()
        try:
            current_week, _, _ = date_utils.get_current_week_info()
            report_week = current_week - 1 if current_week > 1 else 1

            week = db.query(WeeklyPlan).filter(
                WeeklyPlan.week_num == report_week
            ).first()

            if not week:
                webhook_client.send_text(f"📊 第{report_week}周暂无数据")
                return

            # 获取交付物
            deliverables = db.query(Deliverable).filter(
                Deliverable.week_id == week.id
            ).all()

            total = len(deliverables)
            completed = sum(1 for d in deliverables if d.is_completed)
            progress = int((completed / total * 100)) if total > 0 else 0

            # 交付物状态
            deliv_list = "\n".join([
                f"  {'✅' if d.is_completed else '⏳'} {d.name}"
                for d in deliverables[:6]
            ])

            message = f"""📊 第{report_week}周学习周报
━━━━━━━━━━━━━━━━━━━━
🎯 阶段: {week.stage}
📌 主题: {week.theme}

📈 完成度: {progress}%
{'█' * (progress // 5)}{'░' * ((100 - progress) // 5)}

📦 交付物进度:
{deliv_list}

🔥 下周预告: 第{report_week + 1}周
━━━━━━━━━━━━━━━━━━━━"""

            webhook_client.send_text(message)

        finally:
            db.close()

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        print("✅ Webhook 定时任务已关闭")
