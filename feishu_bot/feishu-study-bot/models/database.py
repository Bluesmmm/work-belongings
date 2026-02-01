"""数据库模型"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config.settings import settings

Base = declarative_base()


class WeeklyPlan(Base):
    """周计划表"""
    __tablename__ = "weekly_plans"
    
    id = Column(Integer, primary_key=True)
    week_num = Column(Integer, nullable=False, index=True)  # 周次 1-22
    start_date = Column(String(20), nullable=False)  # 开始日期
    end_date = Column(String(20), nullable=False)  # 结束日期
    stage = Column(String(50), nullable=False)  # 阶段名称
    theme = Column(String(200), nullable=False)  # 本周主题
    focus = Column(Text, nullable=False)  # 本周重点
    main_goal = Column(Text, nullable=False)  # 主目标 (vLLM固定)
    deep_dive = Column(Text, nullable=False)  # 深挖主题
    trl_task = Column(Text)  # TRL学习任务
    slime_task = Column(Text)  # slime学习任务
    openrlhf_task = Column(Text)  # OpenRLHF学习任务
    risks = Column(Text)  # 风险备注
    created_at = Column(DateTime, default=datetime.now)
    
    deliverables = relationship("Deliverable", back_populates="week")
    checkins = relationship("CheckIn", back_populates="week")


class Deliverable(Base):
    """交付物表"""
    __tablename__ = "deliverables"
    
    id = Column(Integer, primary_key=True)
    week_id = Column(Integer, ForeignKey("weekly_plans.id"), nullable=False)
    name = Column(String(200), nullable=False)  # 交付物名称
    description = Column(Text)  # 描述
    acceptance_criteria = Column(Text)  # 验收标准
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    evidence_url = Column(String(500))  # 成果链接/截图
    
    week = relationship("WeeklyPlan", back_populates="deliverables")


class CheckIn(Base):
    """打卡记录表"""
    __tablename__ = "checkins"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)
    week_id = Column(Integer, ForeignKey("weekly_plans.id"), nullable=False)
    checkin_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    hours_spent = Column(Float, default=0)  # 投入时长
    satisfaction = Column(Integer, default=3)  # 1-5 满意度
    completed_tasks = Column(Text)  # 完成的任务（JSON列表）
    blockers = Column(Text)  # 遇到的卡点
    notes = Column(Text)  # 备注
    created_at = Column(DateTime, default=datetime.now)
    
    week = relationship("WeeklyPlan", back_populates="checkins")


class Milestone(Base):
    """里程碑表"""
    __tablename__ = "milestones"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    target_week = Column(Integer, nullable=False)  # 目标周次
    description = Column(Text)
    completion_criteria = Column(Text)  # 完成定义
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    notes = Column(Text)


class WeeklyReport(Base):
    """周报记录表"""
    __tablename__ = "weekly_reports"
    
    id = Column(Integer, primary_key=True)
    week_id = Column(Integer, ForeignKey("weekly_plans.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.now)
    summary = Column(Text)  # 总结
    highlights = Column(Text)  # 亮点（JSON）
    risks = Column(Text)  # 风险（JSON）
    next_week_preview = Column(Text)  # 下周预览
    card_content = Column(Text)  # 卡片内容（JSON）
    sent_to_chat = Column(Boolean, default=False)


# 数据库引擎和会话
engine = create_engine(settings.database_url, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
