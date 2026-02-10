"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # 飞书配置
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_encrypt_key: Optional[str] = None
    feishu_verification_token: Optional[str] = None
    
    # 机器人配置
    bot_name: str = "学习助手"
    default_chat_id: Optional[str] = None
    
    # 提醒时间
    daily_reminder_hour: int = 9
    daily_reminder_minute: int = 0
    checkin_reminder_hour: int = 21
    checkin_reminder_minute: int = 0
    weekly_report_hour: int = 20
    weekly_report_minute: int = 0
    weekly_report_day: str = "sun"  # mon, tue, wed, thu, fri, sat, sun
    
    # 数据库
    database_url: str = "sqlite:///./study_bot.db"
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # 学习规划文件路径
    plan_file: str = "config/schemas/weekly_plan.json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
