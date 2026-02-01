"""日期工具类"""
from datetime import datetime, timedelta
from typing import Tuple, List
from dateutil import parser


class DateUtils:
    """日期工具"""
    
    @staticmethod
    def get_current_week_info(start_date_str: str = "2026-02-01") -> Tuple[int, datetime, datetime]:
        """
        获取当前周信息
        返回: (周次, 本周开始日期, 本周结束日期)
        """
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        today = datetime.now()
        
        # 计算从计划开始到现在经过的天数
        days_passed = (today - start_date).days
        
        # 计算周次（从1开始）
        week_num = max(1, (days_passed // 7) + 1)
        
        # 计算本周开始和结束
        days_since_week_start = days_passed % 7
        week_start = today - timedelta(days=days_since_week_start)
        week_end = week_start + timedelta(days=6)
        
        return week_num, week_start, week_end
    
    @staticmethod
    def get_date_range(week_num: int, start_date_str: str = "2026-02-01") -> Tuple[str, str]:
        """
        根据周次获取日期范围
        返回: (开始日期, 结束日期) 格式 YYYY-MM-DD
        """
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        week_start = start_date + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=6)
        
        return week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")
    
    @staticmethod
    def format_date(dt: datetime) -> str:
        """格式化日期"""
        return dt.strftime("%Y-%m-%d")
    
    @staticmethod
    def parse_date(date_str: str) -> datetime:
        """解析日期字符串"""
        return parser.parse(date_str)
    
    @staticmethod
    def get_weekday_name(dt: datetime) -> str:
        """获取星期名称"""
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[dt.weekday()]
    
    @staticmethod
    def days_between(date1: str, date2: str) -> int:
        """计算两个日期之间的天数"""
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        return abs((d2 - d1).days)
    
    @staticmethod
    def is_today(date_str: str) -> bool:
        """判断是否为今天"""
        today = datetime.now().strftime("%Y-%m-%d")
        return date_str == today


date_utils = DateUtils()
