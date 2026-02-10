"""消息处理器"""
import json
from typing import Dict, Any
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
from models.database import get_db
from services.plan_service import PlanService
from services.checkin_service import CheckInService
from services.report_service import ReportService
from cards.templates import CardBuilder
from utils.feishu_client import feishu_client
from utils.date_utils import date_utils


class MessageHandler:
    """消息处理器"""
    
    def __init__(self):
        self.card_builder = CardBuilder()
    
    async def handle_message(self, data: P2ImMessageReceiveV1) -> None:
        """处理收到的消息"""
        message = data.event.message
        user_id = data.event.sender.sender_id.user_id
        content = json.loads(message.content)
        text = content.get("text", "").strip()

        print(f"收到消息 from {user_id}: {text}")

        # 自定义关键词映射（无斜杠触发）
        keyword_map = {
            "今日": "/今日",
            "今天": "/今日",
            "今日计划": "/今日",
            "学习计划": "/今日",
            "打卡": "/打卡",
            "我要打卡": "/打卡",
            "学习打卡": "/打卡",
            "进度": "/进度",
            "学习进度": "/进度",
            "里程碑": "/里程碑",
            "周报": "/周报",
            "帮助": "/帮助",
        }

        # 检查是否匹配关键词
        for keyword, command in keyword_map.items():
            if text == keyword or text.startswith(keyword):
                await self._handle_command(user_id, message, command)
                return

        # 命令路由（斜杠开头）
        if text.startswith("/") or text.startswith("／"):
            await self._handle_command(user_id, message, text)
        else:
            # 普通消息，回复帮助
            await self._send_help(message)
    
    async def _handle_command(self, user_id: str, message, text: str):
        """处理命令"""
        command = text[1:].split()[0].lower()
        
        command_map = {
            "今日": self._cmd_today,
            "今天": self._cmd_today,
            "打卡": self._cmd_checkin,
            "进度": self._cmd_progress,
            "里程碑": self._cmd_milestones,
            "周报": self._cmd_weekly_report,
            "帮助": self._cmd_help,
            "help": self._cmd_help,
        }
        
        handler = command_map.get(command, self._cmd_unknown)
        await handler(user_id, message)
    
    async def _cmd_today(self, user_id: str, message):
        """今日计划命令"""
        db = next(get_db())
        try:
            plan_service = PlanService(db)
            week = plan_service.get_current_week()
            
            if not week:
                await feishu_client.reply_text(message.message_id, "未找到当前周计划")
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
                tips=week.risks
            )
            
            await feishu_client.reply_card(message.message_id, card)
            
        finally:
            db.close()
    
    async def _cmd_checkin(self, user_id: str, message):
        """打卡命令"""
        db = next(get_db())
        try:
            plan_service = PlanService(db)
            week = plan_service.get_current_week()
            
            if not week:
                await feishu_client.reply_text(message.message_id, "未找到当前周计划")
                return
            
            # 检查今日是否已打卡
            checkin_service = CheckInService(db)
            today_checkin = checkin_service.get_today_checkin(user_id)
            
            if today_checkin:
                # 已打卡，显示今日记录
                card = self.card_builder.checkin_success(
                    week_num=week.week_num,
                    hours=today_checkin.hours_spent,
                    satisfaction=today_checkin.satisfaction
                )
                await feishu_client.reply_card(message.message_id, card)
                return
            
            # 显示打卡表单
            deliverables = plan_service.get_week_deliverables(week.id)
            card = self.card_builder.checkin_form(
                week_num=week.week_num,
                deliverables=[
                    {"id": d.id, "name": d.name, "done": d.is_completed}
                    for d in deliverables
                ]
            )
            
            await feishu_client.reply_card(message.message_id, card)
            
        finally:
            db.close()
    
    async def _cmd_progress(self, user_id: str, message):
        """进度命令"""
        db = next(get_db())
        try:
            plan_service = PlanService(db)
            checkin_service = CheckInService(db)
            
            current_week, _, _ = date_utils.get_current_week_info()
            milestones = plan_service.get_all_milestones()
            overall_stats = checkin_service.get_overall_stats(user_id)
            
            card = self.card_builder.overall_progress(
                current_week=current_week,
                milestones=[
                    {
                        "id": m.id,
                        "name": m.name,
                        "target_week": m.target_week,
                        "done": m.is_completed
                    }
                    for m in milestones
                ],
                recent_stats=overall_stats
            )
            
            await feishu_client.reply_card(message.message_id, card)
            
        finally:
            db.close()
    
    async def _cmd_milestones(self, user_id: str, message):
        """里程碑命令"""
        db = next(get_db())
        try:
            plan_service = PlanService(db)
            milestones = plan_service.get_all_milestones()
            
            text = "**📍 里程碑进度**\n\n"
            for m in milestones:
                status = "✅" if m.is_completed else "⏳"
                text += f"{status} **{m.name}** (目标W{m.target_week})\n"
                if m.is_completed:
                    text += f"   已完成\n"
                text += "\n"
            
            await feishu_client.reply_text(message.message_id, text)
            
        finally:
            db.close()
    
    async def _cmd_weekly_report(self, user_id: str, message):
        """周报命令"""
        db = next(get_db())
        try:
            # 解析参数，支持 /周报 12 查看第12周
            text = json.loads(message.content).get("text", "")
            parts = text.split()
            
            if len(parts) > 1 and parts[1].isdigit():
                week_num = int(parts[1])
            else:
                current_week, _, _ = date_utils.get_current_week_info()
                week_num = current_week - 1 if current_week > 1 else 1
            
            plan_service = PlanService(db)
            report_service = ReportService(db)
            
            # 获取或生成周报
            report = report_service.get_report(week_num)
            if not report:
                report = report_service.generate_weekly_report(user_id, week_num)
            
            if not report:
                await feishu_client.reply_text(message.message_id, f"无法生成第{week_num}周报告")
                return
            
            # 解析报告内容
            content = json.loads(report.card_content)
            week = plan_service.get_week_by_num(week_num)
            deliverables = plan_service.get_week_deliverables(week.id)
            
            highlights = json.loads(report.highlights) if report.highlights else []
            risks = json.loads(report.risks) if report.risks else []
            next_week = json.loads(report.next_week_preview) if report.next_week_preview else {}
            
            card = self.card_builder.weekly_report(
                week_num=week_num,
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
            
            await feishu_client.reply_card(message.message_id, card)
            
        finally:
            db.close()
    
    async def _cmd_help(self, user_id: str, message):
        """帮助命令"""
        help_text = """**📖 学习助手使用指南**

**常用命令：**
• `/今日` 或 `/今天` - 查看今日学习计划
• `/打卡` - 记录今日学习进度
• `/进度` - 查看整体学习进度和里程碑
• `/周报` - 生成本周/上周学习报告
• `/周报 5` - 查看第5周报告
• `/里程碑` - 查看所有里程碑进度
• `/帮助` - 显示本帮助信息

**自动提醒：**
• ☀️ 每天 9:00 发送今日学习提醒
• ⏰ 每天 21:00 发送打卡提醒
• 📊 每周日 20:00 自动生成周报

开始你的学习之旅吧！🚀"""
        
        await feishu_client.reply_text(message.message_id, help_text)
    
    async def _cmd_unknown(self, user_id: str, message):
        """未知命令"""
        await feishu_client.reply_text(
            message.message_id, 
            "未知命令，发送 `/帮助` 查看可用命令"
        )
    
    async def _send_help(self, message):
        """发送帮助信息"""
        await self._cmd_help("", message)


class CardCallbackHandler:
    """卡片回调处理器"""
    
    def __init__(self):
        self.card_builder = CardBuilder()
    
    async def handle_callback(self, data: Dict[str, Any]) -> None:
        """处理卡片回调"""
        action = data.get("action")
        user_id = data.get("user_id")
        message_id = data.get("message_id")
        
        print(f"卡片回调: action={action}, user={user_id}")
        
        if action == "submit_checkin":
            await self._handle_checkin_submit(user_id, data, message_id)
        elif action == "checkin":
            # 重新显示打卡表单
            await self._show_checkin_form(user_id, message_id)
        # 其他回调处理...
    
    async def _handle_checkin_submit(self, user_id: str, data: Dict, message_id: str):
        """处理打卡提交"""
        db = next(get_db())
        try:
            week_num = int(data.get("week", 1))
            hours = float(data.get("hours_spent", 0))
            satisfaction = int(data.get("satisfaction", 3))
            completed_tasks = data.get("completed_tasks", [])
            blockers = data.get("blockers", "")
            notes = data.get("notes", "")
            
            # 确保 completed_tasks 是列表
            if isinstance(completed_tasks, str):
                completed_tasks = [completed_tasks]
            
            # 创建打卡记录
            checkin_service = CheckInService(db)
            checkin = checkin_service.create_checkin(
                user_id=user_id,
                week_num=week_num,
                hours_spent=hours,
                satisfaction=satisfaction,
                completed_tasks=completed_tasks,
                blockers=blockers,
                notes=notes
            )
            
            # 发送成功反馈
            card = self.card_builder.checkin_success(
                week_num=week_num,
                hours=hours,
                satisfaction=satisfaction
            )
            
            await feishu_client.update_card(message_id, card)
            
        except Exception as e:
            print(f"打卡失败: {e}")
            await feishu_client.update_card(
                message_id,
                {
                    "config": {"wide_screen_mode": True},
                    "header": {
                        "template": "red",
                        "title": {"tag": "plain_text", "content": "打卡失败"}
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"提交打卡时出错：{str(e)}\n请重试。"
                            }
                        }
                    ]
                }
            )
        finally:
            db.close()
    
    async def _show_checkin_form(self, user_id: str, message_id: str):
        """显示打卡表单"""
        db = next(get_db())
        try:
            plan_service = PlanService(db)
            week = plan_service.get_current_week()
            
            if week:
                deliverables = plan_service.get_week_deliverables(week.id)
                card = self.card_builder.checkin_form(
                    week_num=week.week_num,
                    deliverables=[
                        {"id": d.id, "name": d.name, "done": d.is_completed}
                        for d in deliverables
                    ]
                )
                await feishu_client.update_card(message_id, card)
            
        finally:
            db.close()


# 全局处理器实例
message_handler = MessageHandler()
card_callback_handler = CardCallbackHandler()
