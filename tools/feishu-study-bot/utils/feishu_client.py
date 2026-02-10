"""飞书API客户端封装"""
import json
from typing import Optional, Dict, Any
from lark_oapi import Client
from lark_oapi.api.im.v1 import (
    CreateMessageRequest, CreateMessageRequestBody,
    ReplyMessageRequest, ReplyMessageRequestBody,
    UpdateMessageRequest, UpdateMessageRequestBody
)
from config.settings import settings


class FeishuClient:
    """飞书客户端"""
    
    def __init__(self):
        self.client = Client.builder() \
            .app_id(settings.feishu_app_id) \
            .app_secret(settings.feishu_app_secret) \
            .build()
    
    async def send_text(self, chat_id: str, text: str) -> Optional[str]:
        """发送文本消息"""
        try:
            content = json.dumps({"text": text})
            request = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .body(CreateMessageRequestBody.builder()
                      .receive_id(chat_id)
                      .msg_type("text")
                      .content(content)
                      .build()) \
                .build()
            
            response = self.client.im.v1.message.create(request)
            
            if response.success():
                return response.data.message_id
            else:
                print(f"发送消息失败: {response.msg}")
                return None
        except Exception as e:
            print(f"发送消息异常: {e}")
            return None
    
    async def send_card(self, chat_id: str, card: Dict[str, Any]) -> Optional[str]:
        """发送卡片消息"""
        try:
            content = json.dumps(card)
            request = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .body(CreateMessageRequestBody.builder()
                      .receive_id(chat_id)
                      .msg_type("interactive")
                      .content(content)
                      .build()) \
                .build()
            
            response = self.client.im.v1.message.create(request)
            
            if response.success():
                return response.data.message_id
            else:
                print(f"发送卡片失败: {response.msg}")
                return None
        except Exception as e:
            print(f"发送卡片异常: {e}")
            return None
    
    async def reply_text(self, message_id: str, text: str) -> bool:
        """回复文本消息"""
        try:
            content = json.dumps({"text": text})
            request = ReplyMessageRequest.builder() \
                .message_id(message_id) \
                .body(ReplyMessageRequestBody.builder()
                      .content(content)
                      .msg_type("text")
                      .build()) \
                .build()
            
            response = self.client.im.v1.message.reply(request)
            return response.success()
        except Exception as e:
            print(f"回复消息异常: {e}")
            return False
    
    async def reply_card(self, message_id: str, card: Dict[str, Any]) -> bool:
        """回复卡片消息"""
        try:
            content = json.dumps(card)
            request = ReplyMessageRequest.builder() \
                .message_id(message_id) \
                .body(ReplyMessageRequestBody.builder()
                      .content(content)
                      .msg_type("interactive")
                      .build()) \
                .build()
            
            response = self.client.im.v1.message.reply(request)
            return response.success()
        except Exception as e:
            print(f"回复卡片异常: {e}")
            return False
    
    async def update_card(self, message_id: str, card: Dict[str, Any]) -> bool:
        """更新卡片消息"""
        try:
            content = json.dumps(card)
            request = UpdateMessageRequest.builder() \
                .message_id(message_id) \
                .body(UpdateMessageRequestBody.builder()
                      .content(content)
                      .build()) \
                .build()
            
            response = self.client.im.v1.message.patch(request)
            return response.success()
        except Exception as e:
            print(f"更新卡片异常: {e}")
            return False


# 全局客户端实例
feishu_client = FeishuClient()
