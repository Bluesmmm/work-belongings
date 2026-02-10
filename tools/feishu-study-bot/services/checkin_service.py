"""打卡服务"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.database import CheckIn, WeeklyPlan, Deliverable
from utils.date_utils import date_utils


class CheckInService:
    """打卡服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_checkin(self, user_id: str, week_num: int, 
                       hours_spent: float, satisfaction: int,
                       completed_tasks: List[str] = None,
                       blockers: str = "", notes: str = "") -> CheckIn:
        """创建打卡记录"""
        
        week = self.db.query(WeeklyPlan).filter(WeeklyPlan.week_num == week_num).first()
        if not week:
            raise ValueError(f"未找到第{week_num}周计划")
        
        checkin = CheckIn(
            user_id=user_id,
            week_id=week.id,
            checkin_date=date_utils.format_date(datetime.now()),
            hours_spent=hours_spent,
            satisfaction=satisfaction,
            completed_tasks=json.dumps(completed_tasks or [], ensure_ascii=False),
            blockers=blockers,
            notes=notes
        )
        
        self.db.add(checkin)
        
        # 更新交付物完成状态
        if completed_tasks:
            for task_id in completed_tasks:
                deliverable = self.db.query(Deliverable).filter(
                    Deliverable.id == int(task_id)
                ).first()
                if deliverable and not deliverable.is_completed:
                    deliverable.is_completed = True
                    deliverable.completed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(checkin)
        
        return checkin
    
    def get_today_checkin(self, user_id: str) -> Optional[CheckIn]:
        """获取今日打卡"""
        today = date_utils.format_date(datetime.now())
        return self.db.query(CheckIn).filter(
            CheckIn.user_id == user_id,
            CheckIn.checkin_date == today
        ).first()
    
    def get_week_checkins(self, user_id: str, week_num: int) -> List[CheckIn]:
        """获取周的打卡记录"""
        week = self.db.query(WeeklyPlan).filter(WeeklyPlan.week_num == week_num).first()
        if not week:
            return []
        
        return self.db.query(CheckIn).filter(
            CheckIn.user_id == user_id,
            CheckIn.week_id == week.id
        ).order_by(CheckIn.created_at).all()
    
    def get_week_stats(self, user_id: str, week_num: int) -> Dict[str, Any]:
        """获取周打卡统计"""
        checkins = self.get_week_checkins(user_id, week_num)
        
        if not checkins:
            return {
                "checkin_days": 0,
                "total_hours": 0,
                "avg_satisfaction": 0,
                "target_hours": 28,
                "target_days": 7
            }
        
        total_hours = sum(c.hours_spent for c in checkins)
        avg_satisfaction = sum(c.satisfaction for c in checkins) / len(checkins)
        
        return {
            "checkin_days": len(checkins),
            "total_hours": round(total_hours, 1),
            "avg_satisfaction": round(avg_satisfaction, 1),
            "target_hours": 28,
            "target_days": 7
        }
    
    def get_overall_stats(self, user_id: str) -> Dict[str, Any]:
        """获取整体统计"""
        checkins = self.db.query(CheckIn).filter(CheckIn.user_id == user_id).all()
        
        if not checkins:
            return {
                "total_hours": 0,
                "total_days": 0,
                "total_weeks": 0,
                "avg_satisfaction": 0
            }
        
        total_hours = sum(c.hours_spent for c in checkins)
        unique_days = len(set(c.checkin_date for c in checkins))
        unique_weeks = len(set(c.week_id for c in checkins))
        avg_satisfaction = sum(c.satisfaction for c in checkins) / len(checkins)
        
        return {
            "total_hours": round(total_hours, 1),
            "total_days": unique_days,
            "total_weeks": unique_weeks,
            "avg_satisfaction": round(avg_satisfaction, 1)
        }
    
    def get_streak(self, user_id: str) -> int:
        """获取连续打卡天数"""
        checkins = self.db.query(CheckIn).filter(
            CheckIn.user_id == user_id
        ).order_by(CheckIn.checkin_date.desc()).all()
        
        if not checkins:
            return 0
        
        streak = 0
        today = datetime.now().date()
        expected_date = today
        
        for checkin in checkins:
            checkin_date = datetime.strptime(checkin.checkin_date, "%Y-%m-%d").date()
            
            # 检查是否是连续的
            if checkin_date == expected_date or (
                streak == 0 and (today - checkin_date).days <= 1
            ):
                streak += 1
                expected_date = checkin_date - timedelta(days=1)
            else:
                break
        
        return streak


from datetime import timedelta
