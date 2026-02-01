"""报告服务"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import WeeklyReport, WeeklyPlan, CheckIn, Deliverable, Milestone
from utils.date_utils import date_utils


class ReportService:
    """报告服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_weekly_report(self, user_id: str, week_num: int) -> Optional[WeeklyReport]:
        """生成周报"""
        
        # 获取周计划
        week = self.db.query(WeeklyPlan).filter(WeeklyPlan.week_num == week_num).first()
        if not week:
            return None
        
        # 获取打卡记录
        checkins = self.db.query(CheckIn).filter(
            CheckIn.user_id == user_id,
            CheckIn.week_id == week.id
        ).all()
        
        # 获取交付物
        deliverables = self.db.query(Deliverable).filter(
            Deliverable.week_id == week.id
        ).all()
        
        # 计算统计
        stats = self._calculate_week_stats(checkins)
        progress = self._calculate_progress(deliverables)
        
        # 生成亮点
        highlights = self._generate_highlights(checkins, deliverables)
        
        # 识别风险
        risks = self._identify_risks(stats, deliverables)
        
        # 下周预览
        next_week = self.db.query(WeeklyPlan).filter(
            WeeklyPlan.week_num == week_num + 1
        ).first()
        
        next_week_info = {
            "theme": next_week.theme if next_week else "TBD",
            "stage": next_week.stage if next_week else "TBD"
        }
        
        # 构建报告内容
        report_content = {
            "week_num": week_num,
            "stage": week.stage,
            "theme": week.theme,
            "progress": progress,
            "stats": stats,
            "deliverables": [
                {
                    "id": d.id,
                    "name": d.name,
                    "done": d.is_completed
                }
                for d in deliverables
            ],
            "highlights": highlights,
            "risks": risks,
            "next_week": next_week_info
        }
        
        # 保存报告
        report = WeeklyReport(
            week_id=week.id,
            summary=self._generate_summary(week, stats, progress),
            highlights=json.dumps(highlights, ensure_ascii=False),
            risks=json.dumps(risks, ensure_ascii=False),
            next_week_preview=json.dumps(next_week_info, ensure_ascii=False),
            card_content=json.dumps(report_content, ensure_ascii=False)
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report
    
    def _calculate_week_stats(self, checkins: List[CheckIn]) -> Dict[str, Any]:
        """计算周统计"""
        if not checkins:
            return {
                "hours": 0,
                "target_hours": 28,
                "checkin_days": 0,
                "avg_satisfaction": 0
            }
        
        total_hours = sum(c.hours_spent for c in checkins)
        avg_satisfaction = sum(c.satisfaction for c in checkins) / len(checkins)
        
        return {
            "hours": round(total_hours, 1),
            "target_hours": 28,
            "checkin_days": len(checkins),
            "avg_satisfaction": round(avg_satisfaction, 1)
        }
    
    def _calculate_progress(self, deliverables: List[Deliverable]) -> int:
        """计算进度百分比"""
        if not deliverables:
            return 0
        
        completed = sum(1 for d in deliverables if d.is_completed)
        return int((completed / len(deliverables)) * 100)
    
    def _generate_highlights(self, checkins: List[CheckIn], 
                            deliverables: List[Deliverable]) -> List[str]:
        """生成本周亮点"""
        highlights = []
        
        # 完成的重要交付物
        completed = [d for d in deliverables if d.is_completed]
        for d in completed[:2]:
            highlights.append(f"完成交付物：{d.name}")
        
        # 高投入天数
        high_effort_days = [c for c in checkins if c.hours_spent >= 4]
        if len(high_effort_days) >= 3:
            highlights.append(f"本周有 {len(high_effort_days)} 天高效学习（≥4小时）")
        
        # 高满意度
        high_satisfaction = [c for c in checkins if c.satisfaction >= 4]
        if len(high_satisfaction) >= 5:
            highlights.append("本周学习状态极佳，保持！")
        
        # 如果没有亮点，添加默认
        if not highlights and checkins:
            highlights.append(f"本周坚持打卡 {len(checkins)} 天")
        
        return highlights
    
    def _identify_risks(self, stats: Dict[str, Any], 
                       deliverables: List[Deliverable]) -> List[Dict[str, str]]:
        """识别风险"""
        risks = []
        
        # 投入不足
        if stats.get("hours", 0) < stats.get("target_hours", 28) * 0.7:
            risks.append({
                "type": "time",
                "desc": f"本周投入 {stats['hours']}h，低于目标 {stats['target_hours']}h"
            })
        
        # 交付物延迟
        pending = [d for d in deliverables if not d.is_completed]
        if len(pending) > len(deliverables) * 0.5:
            risks.append({
                "type": "progress",
                "desc": f"有 {len(pending)} 个交付物待完成，可能影响里程碑"
            })
        
        return risks
    
    def _generate_summary(self, week: WeeklyPlan, stats: Dict, progress: int) -> str:
        """生成文字总结"""
        return (
            f"第{week.week_num}周（{week.stage}）学习总结："
            f"投入{stats.get('hours', 0)}小时，完成度{progress}%。"
        )
    
    def get_report(self, week_num: int) -> Optional[WeeklyReport]:
        """获取周报"""
        week = self.db.query(WeeklyPlan).filter(WeeklyPlan.week_num == week_num).first()
        if not week:
            return None
        
        return self.db.query(WeeklyReport).filter(
            WeeklyReport.week_id == week.id
        ).order_by(WeeklyReport.generated_at.desc()).first()
    
    def get_milestone_report(self, milestone_id: int) -> Optional[Dict[str, Any]]:
        """获取里程碑报告"""
        milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            return None
        
        # 计算从里程碑目标周开始到现在的统计
        # 这里简化处理，实际可以计算具体时间段
        return {
            "milestone": {
                "id": milestone.id,
                "name": milestone.name,
                "target_week": milestone.target_week,
                "completed": milestone.is_completed
            },
            "stats": {
                "total_hours": 0,  # 实际需要查询
                "total_checkins": 0
            }
        }
