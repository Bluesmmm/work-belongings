"""飞书卡片模板库"""
from typing import List, Dict, Any, Optional
from datetime import datetime


class CardBuilder:
    """卡片构建器"""
    
    @staticmethod
    def daily_reminder(week_num: int, stage: str, theme: str, 
                       focus: str, deliverables: List[Dict],
                       tips: str = "") -> Dict[str, Any]:
        """每日学习提醒卡片"""
        
        # 构建交付物列表
        deliverable_text = "\n".join([
            f"{'✅' if d.get('done') else '⏳'} **{d['name']}**" 
            for d in deliverables[:5]  # 最多显示5个
        ])
        
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": f"📚 今日学习计划 (第{week_num}周)"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**🎯 本周阶段：** {stage}\n**📌 今日主题：** {theme}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📝 今日重点：**\n{focus}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📦 本周交付物：**\n{deliverable_text}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"💡 Tips: {tips}" if tips else "💡 坚持打卡，积跬步以至千里！"
                        }
                    ]
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📝 今日打卡"},
                            "type": "primary",
                            "value": {"action": "checkin", "week": week_num}
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📊 查看进度"},
                            "type": "default",
                            "value": {"action": "view_progress"}
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def checkin_form(week_num: int, deliverables: List[Dict]) -> Dict[str, Any]:
        """打卡表单卡片"""
        
        # 构建交付物选项
        options = []
        for d in deliverables:
            options.append({
                "text": {"tag": "plain_text", "content": d['name']},
                "value": str(d['id'])
            })
        
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "green",
                "title": {
                    "tag": "plain_text",
                    "content": f"📋 第{week_num}周进度打卡"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**今日完成项**（可多选）："
                    }
                },
                {
                    "tag": "checkbox",
                    "options": options[:6],  # 限制选项数量
                    "name": "completed_tasks"
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**今日投入时长**："
                    }
                },
                {
                    "tag": "select",
                    "placeholder": "选择时长",
                    "options": [
                        {"text": {"tag": "plain_text", "content": "⏰ 1-2 小时"}, "value": "1.5"},
                        {"text": {"tag": "plain_text", "content": "⏰ 2-3 小时"}, "value": "2.5"},
                        {"text": {"tag": "plain_text", "content": "⏰ 3-4 小时"}, "value": "3.5"},
                        {"text": {"tag": "plain_text", "content": "⏰ 4-5 小时"}, "value": "4.5"},
                        {"text": {"tag": "plain_text", "content": "⏰ 5+ 小时"}, "value": "5.5"},
                    ],
                    "name": "hours_spent"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**今日满意度**："
                    }
                },
                {
                    "tag": "select",
                    "placeholder": "选择满意度",
                    "options": [
                        {"text": {"tag": "plain_text", "content": "😊 很满意"}, "value": "5"},
                        {"text": {"tag": "plain_text", "content": "🙂 满意"}, "value": "4"},
                        {"text": {"tag": "plain_text", "content": "😐 一般"}, "value": "3"},
                        {"text": {"tag": "plain_text", "content": "🙁 不满意"}, "value": "2"},
                        {"text": {"tag": "plain_text", "content": "😔 很不满意"}, "value": "1"},
                    ],
                    "name": "satisfaction"
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**遇到卡点**（选填）："
                    }
                },
                {
                    "tag": "input",
                    "placeholder": "描述今天遇到的困难...",
                    "name": "blockers"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**备注**（选填）："
                    }
                },
                {
                    "tag": "input",
                    "placeholder": "其他想说的话...",
                    "name": "notes"
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "✅ 提交打卡"},
                            "type": "primary",
                            "value": {"action": "submit_checkin", "week": week_num}
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def weekly_report(week_num: int, stage: str, theme: str,
                      progress: int, stats: Dict[str, Any],
                      deliverables: List[Dict], highlights: List[str],
                      risks: List[Dict], next_week: Dict) -> Dict[str, Any]:
        """周报卡片"""
        
        # 进度条
        progress_bar = "🟩" * (progress // 10) + "⬜" * ((100 - progress) // 10)
        
        # 交付物状态
        deliv_text = "\n".join([
            f"{'✅' if d.get('done') else '⏳'} {d['name'][:25]}{'...' if len(d['name']) > 25 else ''}"
            for d in deliverables[:6]
        ])
        
        # 亮点
        highlight_text = "\n".join([f"• {h}" for h in highlights[:3]]) if highlights else "暂无记录"
        
        # 风险
        risk_text = "\n".join([f"⚠️ {r['desc'][:30]}" for r in risks[:2]]) if risks else "本周无明显风险"
        
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": f"📊 第{week_num}周学习周报"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**阶段：** {stage} | **主题：** {theme}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**整体完成度**\n{progress_bar} {progress}%"
                    }
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**⏱️ 投入时长**\n{stats.get('hours', 0)}h / 目标 {stats.get('target_hours', 28)}h"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**📝 打卡天数**\n{stats.get('checkin_days', 0)}/7 天"
                            }
                        }
                    ]
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📦 本周交付物：**\n{deliv_text}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**🏆 本周亮点：**\n{highlight_text}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**⚠️ 风险与调整：**\n{risk_text}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📅 下周计划 (第{week_num+1}周)：**\n**主题：** {next_week.get('theme', 'TBD')}"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📤 分享周报"},
                            "type": "primary",
                            "value": {"action": "share_report", "week": week_num}
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📈 查看详情"},
                            "type": "default",
                            "value": {"action": "view_detail", "week": week_num}
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def milestone_achieved(milestone: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
        """里程碑达成庆祝卡片"""
        
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "yellow",
                "title": {
                    "tag": "plain_text",
                    "content": "🎉 里程碑达成！"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**恭喜完成 {milestone['name']}！**\n\n{milestone.get('description', '')}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**✅ 完成标准验证：**\n" + milestone.get('completion_criteria', '')
                    }
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**📊 投入时长**\n{stats.get('total_hours', 0)}h"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**📝 打卡次数**\n{stats.get('total_checkins', 0)}次"
                            }
                        }
                    ]
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "🚀 下一里程碑"},
                            "type": "primary",
                            "value": {"action": "next_milestone"}
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def overall_progress(current_week: int, total_weeks: int = 22,
                         milestones: List[Dict] = None,
                         recent_stats: Dict = None) -> Dict[str, Any]:
        """整体进度卡片"""
        
        progress = int((current_week / total_weeks) * 100)
        progress_bar = "█" * (progress // 5) + "░" * ((100 - progress) // 5)
        
        # 里程碑状态
        milestone_text = ""
        if milestones:
            for m in milestones[:5]:
                icon = "✅" if m.get('done') else "⏳"
                milestone_text += f"{icon} **{m['name']}** (W{m['target_week']})\n"
        
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": "📈 学习总进度"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**当前进度：第 {current_week} 周 / 共 {total_weeks} 周**\n```{progress_bar} {progress}%```"
                    }
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**⏱️ 累计投入**\n{recent_stats.get('total_hours', 0)}h"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**📅 打卡天数**\n{recent_stats.get('total_days', 0)}天"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**🎯 里程碑**\n{sum(1 for m in milestones if m.get('done'))}/{len(milestones)}"
                            }
                        }
                    ]
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**里程碑进度：**\n{milestone_text}"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📊 详细统计"},
                            "type": "default",
                            "value": {"action": "detailed_stats"}
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def checkin_success(week_num: int, hours: float, satisfaction: int) -> Dict[str, Any]:
        """打卡成功反馈卡片"""
        
        satisfaction_emojis = {5: "😊", 4: "🙂", 3: "😐", 2: "🙁", 1: "😔"}
        emoji = satisfaction_emojis.get(satisfaction, "😐")
        
        encouragements = [
            "积跬步以至千里，继续保持！",
            "今天的努力是明天的实力！",
            "坚持就是胜利，你已经走得很远了！",
            "每一小时都在塑造更好的自己！"
        ]
        import random
        encouragement = random.choice(encouragements)
        
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "green",
                "title": {
                    "tag": "plain_text",
                    "content": "✅ 打卡成功！"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**第{week_num}周打卡已记录**\n\n⏱️ 今日投入：**{hours}** 小时\n😊 满意度：**{emoji}**"
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"💪 {encouragement}"
                        }
                    ]
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📝 继续打卡"},
                            "type": "default",
                            "value": {"action": "checkin", "week": week_num}
                        }
                    ]
                }
            ]
        }
