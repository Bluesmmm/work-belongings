"""飞书自定义机器人 Webhook 客户端"""
import requests
import json
from typing import Dict, Any


class WebhookClient:
    """飞书自定义机器人客户端（单向消息推送）"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_text(self, content: str) -> bool:
        """发送文本消息"""
        data = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        return self._send(data)
    
    def send_card(self, card: Dict[str, Any]) -> bool:
        """发送卡片消息"""
        data = {
            "msg_type": "interactive",
            "card": card
        }
        return self._send(data)
    
    def send_markdown(self, content: str) -> bool:
        """发送 Markdown 消息"""
        data = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        return self._send(data)
    
    def _send(self, data: Dict[str, Any]) -> bool:
        """发送消息"""
        try:
            response = requests.post(
                self.webhook_url,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            result = response.json()
            
            # 检查返回码
            if result.get("code") == 0:
                print("✅ Webhook 消息发送成功")
                return True
            else:
                print(f"❌ Webhook 发送失败: {result}")
                return False
        except Exception as e:
            print(f"❌ Webhook 发送异常: {e}")
            return False


# 创建实例（使用你的 webhook）
webhook_client = WebhookClient(
    "https://open.feishu.cn/open-apis/bot/v2/hook/5b74afca-9700-4df6-9814-cd85cb4d3539"
)
