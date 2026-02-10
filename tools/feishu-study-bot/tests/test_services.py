"""服务测试"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, WeeklyPlan, Deliverable, CheckIn
from services.plan_service import PlanService
from services.checkin_service import CheckInService


# 使用内存数据库测试
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestPlanService:
    """计划服务测试"""
    
    def test_create_week(self, db):
        """测试创建周计划"""
        week = WeeklyPlan(
            week_num=1,
            start_date="2026-02-01",
            end_date="2026-02-07",
            stage="基础基座",
            theme="vLLM单机服务搭建",
            focus="搭建仓库",
            main_goal="vLLM 交付模板",
            deep_dive="TRL学习"
        )
        db.add(week)
        db.commit()
        
        assert week.id is not None
        assert week.week_num == 1
    
    def test_get_week_by_num(self, db):
        """测试按周次查询"""
        # 创建测试数据
        week = WeeklyPlan(
            week_num=1,
            start_date="2026-02-01",
            end_date="2026-02-07",
            stage="基础基座",
            theme="vLLM单机服务搭建",
            focus="搭建仓库",
            main_goal="vLLM 交付模板",
            deep_dive="TRL学习"
        )
        db.add(week)
        db.commit()
        
        # 测试查询
        service = PlanService(db)
        result = service.get_week_by_num(1)
        
        assert result is not None
        assert result.theme == "vLLM单机服务搭建"


class TestCheckInService:
    """打卡服务测试"""
    
    def test_create_checkin(self, db):
        """测试创建打卡"""
        # 先创建周计划
        week = WeeklyPlan(
            week_num=1,
            start_date="2026-02-01",
            end_date="2026-02-07",
            stage="基础基座",
            theme="vLLM单机服务搭建",
            focus="搭建仓库",
            main_goal="vLLM 交付模板",
            deep_dive="TRL学习"
        )
        db.add(week)
        db.commit()
        
        # 创建打卡
        service = CheckInService(db)
        checkin = service.create_checkin(
            user_id="test_user",
            week_num=1,
            hours_spent=4.5,
            satisfaction=5,
            completed_tasks=[],
            blockers="",
            notes="测试打卡"
        )
        
        assert checkin.id is not None
        assert checkin.hours_spent == 4.5
        assert checkin.satisfaction == 5
    
    def test_get_week_stats(self, db):
        """测试周统计"""
        # 创建测试数据
        week = WeeklyPlan(
            week_num=1,
            start_date="2026-02-01",
            end_date="2026-02-07",
            stage="基础基座",
            theme="vLLM单机服务搭建",
            focus="搭建仓库",
            main_goal="vLLM 交付模板",
            deep_dive="TRL学习"
        )
        db.add(week)
        db.commit()
        
        # 创建多个打卡
        service = CheckInService(db)
        for i in range(3):
            service.create_checkin(
                user_id="test_user",
                week_num=1,
                hours_spent=4.0,
                satisfaction=4,
                completed_tasks=[],
                blockers="",
                notes=""
            )
        
        # 测试统计
        stats = service.get_week_stats("test_user", 1)
        
        assert stats["checkin_days"] == 3
        assert stats["total_hours"] == 12.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
