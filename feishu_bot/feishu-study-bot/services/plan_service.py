"""学习计划服务"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import WeeklyPlan, Deliverable, Milestone, get_db
from utils.date_utils import date_utils


class PlanService:
    """计划服务"""
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def load_plan_from_json(self, filepath: str):
        """从JSON文件加载计划"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 加载周计划
        for week_data in data.get('weeks', []):
            week = WeeklyPlan(
                week_num=week_data['week_num'],
                start_date=week_data['start_date'],
                end_date=week_data['end_date'],
                stage=week_data['stage'],
                theme=week_data['theme'],
                focus=week_data['focus'],
                main_goal=week_data.get('main_goal', ''),
                deep_dive=week_data.get('deep_dive', ''),
                trl_task=week_data.get('trl_task', ''),
                slime_task=week_data.get('slime_task', ''),
                openrlhf_task=week_data.get('openrlhf_task', ''),
                risks=week_data.get('risks', '')
            )
            self.db.add(week)
            self.db.flush()  # 获取ID
            
            # 添加交付物
            for deliv_data in week_data.get('deliverables', []):
                deliverable = Deliverable(
                    week_id=week.id,
                    name=deliv_data['name'],
                    description=deliv_data.get('description', ''),
                    acceptance_criteria=deliv_data.get('acceptance_criteria', '')
                )
                self.db.add(deliverable)
        
        # 加载里程碑
        for ms_data in data.get('milestones', []):
            milestone = Milestone(
                name=ms_data['name'],
                target_week=ms_data['target_week'],
                description=ms_data.get('description', ''),
                completion_criteria=ms_data.get('completion_criteria', '')
            )
            self.db.add(milestone)
        
        self.db.commit()
        print(f"成功加载 {len(data.get('weeks', []))} 周计划和 {len(data.get('milestones', []))} 个里程碑")
    
    def get_current_week(self) -> Optional[WeeklyPlan]:
        """获取当前周计划"""
        week_num, _, _ = date_utils.get_current_week_info()
        return self.db.query(WeeklyPlan).filter(WeeklyPlan.week_num == week_num).first()
    
    def get_week_by_num(self, week_num: int) -> Optional[WeeklyPlan]:
        """根据周次获取计划"""
        return self.db.query(WeeklyPlan).filter(WeeklyPlan.week_num == week_num).first()
    
    def get_week_deliverables(self, week_id: int) -> List[Deliverable]:
        """获取周交付物列表"""
        return self.db.query(Deliverable).filter(Deliverable.week_id == week_id).all()
    
    def get_all_milestones(self) -> List[Milestone]:
        """获取所有里程碑"""
        return self.db.query(Milestone).order_by(Milestone.target_week).all()
    
    def get_upcoming_milestones(self, weeks_ahead: int = 2) -> List[Milestone]:
        """获取即将到来的里程碑"""
        current_week, _, _ = date_utils.get_current_week_info()
        target_week = current_week + weeks_ahead
        
        return self.db.query(Milestone).filter(
            Milestone.target_week <= target_week,
            Milestone.is_completed == False
        ).order_by(Milestone.target_week).all()
    
    def complete_deliverable(self, deliverable_id: int) -> bool:
        """标记交付物完成"""
        deliverable = self.db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
        if deliverable:
            deliverable.is_completed = True
            deliverable.completed_at = datetime.now()
            self.db.commit()
            return True
        return False
    
    def complete_milestone(self, milestone_id: int) -> bool:
        """标记里程碑完成"""
        milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if milestone:
            milestone.is_completed = True
            milestone.completed_at = datetime.now()
            self.db.commit()
            return True
        return False
    
    def get_week_progress(self, week_id: int) -> Dict[str, Any]:
        """获取周进度统计"""
        deliverables = self.get_week_deliverables(week_id)
        total = len(deliverables)
        completed = sum(1 for d in deliverables if d.is_completed)
        
        return {
            "total": total,
            "completed": completed,
            "progress": int((completed / total * 100)) if total > 0 else 0
        }
