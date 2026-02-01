"""
飞书长连接 WebSocket 客户端
使用 WebSocket 连接接收事件，无需公网地址和 HTTPS
"""
import json
import asyncio
import websockets
from typing import Callable, Optional
from datetime import datetime, timedelta
import threading
import time

from config.settings import settings
from lark_oapi import Client
from lark_oapi.api.application.v1 import 


class FeishuWebSocketClient:
    """飞书长连接客户端"""
    
    # 飞书 WebSocket 网关地址
    WS_GATEWAY_URL = "wss://ws-bootcamp.faisafe.com/gateway"
    
    def __init__(self, message_handler: Callable, card_handler: Callable = None):
        self.app_id = settings.feishu_app_id
        self.app_secret = settings.feishu_app_secret
        self.message_handler = message_handler
        self.card_handler = card_handler
        
        self.ws = None
        self.connected = False
        self.reconnect_interval = 5  # 重连间隔（秒）
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self._stop_event = threading.Event()
        self._heartbeat_task = None
        self._receive_task = None
        
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        try:
            # 使用飞书SDK获取tenant_access_token
            from lark_oapi.api.auth.v3 import InternalTenantTokenRequest
            
            client = Client.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .build()
            
            request = InternalTenantTokenRequest.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .build()
            
            response = client.auth.v3.tenant_access_token.internal(request)
            
            if response.success():
                return response.data.tenant_access_token
            else:
                print(f"获取token失败: {response.msg}")
                return None
        except Exception as e:
            print(f"获取token异常: {e}")
            return None
    
    async def _connect(self):
        """建立WebSocket连接"""
        token = self._get_access_token()
        if not token:
            print("无法获取访问令牌，连接失败")
            return False
        
        # 构建连接URL
        ws_url = f"{self.WS_GATEWAY_URL}?token={token}"
        
        try:
            print(f"[{datetime.now()}] 正在连接飞书WebSocket网关...")
            self.ws = await websockets.connect(
                ws_url,
                ping_interval=None,  # 我们自己处理心跳
                close_timeout=10
            )
            
            # 发送连接请求
            connect_msg = {
                "message_type": "connect",
                "token": token,
                "app_id": self.app_id
            }
            await self.ws.send(json.dumps(connect_msg))
            
            # 等待连接确认
            response = await asyncio.wait_for(self.ws.recv(), timeout=10)
            data = json.loads(response)
            
            if data.get("code") == 0:
                print(f"[{datetime.now()}] ✅ WebSocket连接成功！")
                self.connected = True
                return True
            else:
                print(f"连接被拒绝: {data.get('message')}")
                return False
                
        except asyncio.TimeoutError:
            print("连接超时")
            return False
        except Exception as e:
            print(f"连接异常: {e}")
            return False
    
    async def _heartbeat(self):
        """心跳保活"""
        while self.connected and not self._stop_event.is_set():
            try:
                if self.ws:
                    heartbeat_msg = {
                        "message_type": "heartbeat",
                        "timestamp": int(time.time())
                    }
                    await self.ws.send(json.dumps(heartbeat_msg))
                    await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                print(f"心跳发送失败: {e}")
                break
    
    async def _receive_messages(self):
        """接收消息循环"""
        while self.connected and not self._stop_event.is_set():
            try:
                if self.ws:
                    message = await self.ws.recv()
                    data = json.loads(message)
                    
                    # 处理消息
                    await self._handle_message(data)
                    
            except websockets.exceptions.ConnectionClosed:
                print("连接已关闭")
                self.connected = False
                break
            except Exception as e:
                print(f"接收消息异常: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, data: dict):
        """处理接收到的消息"""
        msg_type = data.get("message_type")
        
        if msg_type == "heartbeat":
            # 心跳响应，忽略
            pass
            
        elif msg_type == "event":
            # 业务事件
            event_data = data.get("event", {})
            event_type = event_data.get("type")
            
            print(f"收到事件: {event_type}")
            
            # 调用消息处理器
            if self.message_handler:
                try:
                    await self.message_handler(event_data)
                except Exception as e:
                    print(f"消息处理异常: {e}")
            
        elif msg_type == "card_action":
            # 卡片回调
            if self.card_handler:
                try:
                    await self.card_handler(data.get("action", {}))
                except Exception as e:
                    print(f"卡片处理异常: {e}")
        
        else:
            print(f"未知消息类型: {msg_type}, data: {data}")
    
    async def run(self):
        """运行长连接客户端"""
        while not self._stop_event.is_set():
            try:
                # 连接
                if await self._connect():
                    # 启动心跳
                    self._heartbeat_task = asyncio.create_task(self._heartbeat())
                    # 接收消息
                    self._receive_task = asyncio.create_task(self._receive_messages())
                    
                    # 等待任务完成（连接断开）
                    await asyncio.gather(
                        self._heartbeat_task,
                        self._receive_task,
                        return_exceptions=True
                    )
                
            except Exception as e:
                print(f"运行异常: {e}")
            
            finally:
                self.connected = False
                if self.ws:
                    try:
                        await self.ws.close()
                    except:
                        pass
                    self.ws = None
            
            # 重连
            if not self._stop_event.is_set():
                print(f"[{datetime.now()}] {self.reconnect_interval}秒后重连...")
                await asyncio.sleep(self.reconnect_interval)
    
    def start(self):
        """启动客户端（非阻塞）"""
        def run_async():
            asyncio.run(self.run())
        
        self._thread = threading.Thread(target=run_async, daemon=True)
        self._thread.start()
        print("✅ WebSocket客户端已启动（后台线程）")
    
    def stop(self):
        """停止客户端"""
        print("正在停止WebSocket客户端...")
        self._stop_event.set()
        self.connected = False
        
        if self.ws:
            try:
                asyncio.run(self.ws.close())
            except:
                pass
        
        if self._thread:
            self._thread.join(timeout=5)
        
        print("✅ WebSocket客户端已停止")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected


# 另一种实现：使用飞书官方推荐的长连接方式
class FeishuLongPollingClient:
    """
    飞书长轮询客户端
    通过持续请求 /event/subscribe 接口获取事件
    适用于无法使用WebSocket的场景
    """
    
    def __init__(self, message_handler: Callable):
        self.message_handler = message_handler
        self.client = Client.builder() \
            .app_id(settings.feishu_app_id) \
            .app_secret(settings.feishu_app_secret) \
            .build()
        self.running = False
        
    async def subscribe_events(self):
        """订阅事件"""
        while self.running:
            try:
                # 这里需要调用飞书的订阅接口
                # 实际实现需要使用飞书的Event订阅API
                await asyncio.sleep(30)  # 轮询间隔
                
            except Exception as e:
                print(f"订阅异常: {e}")
                await asyncio.sleep(5)
    
    def start(self):
        """启动"""
        self.running = True
        threading.Thread(target=lambda: asyncio.run(self.subscribe_events()), daemon=True).start()


# 简化的纯WebSocket实现（不依赖飞书SDK的WebSocket支持）
class SimpleWebSocketClient:
    """
    简化版WebSocket客户端
    直接连接飞书WebSocket网关
    """
    
    def __init__(self, on_message: Callable, on_connect: Callable = None, on_disconnect: Callable = None):
        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.ws = None
        self.running = False
        self.url = None
        
    async def connect_with_endpoint(self, endpoint_url: str):
        """
        使用飞书提供的WebSocket端点连接
        endpoint_url: 从飞书开放平台获取的WebSocket地址
        """
        self.url = endpoint_url
        self.running = True
        
        while self.running:
            try:
                print(f"正在连接: {endpoint_url}")
                async with websockets.connect(endpoint_url) as websocket:
                    self.ws = websocket
                    print("✅ WebSocket已连接")
                    
                    if self.on_connect:
                        await self.on_connect()
                    
                    # 接收消息
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            if self.on_message:
                                await self.on_message(data)
                        except json.JSONDecodeError:
                            print(f"收到非JSON消息: {message}")
                            
            except websockets.exceptions.ConnectionClosed:
                print("连接已断开")
            except Exception as e:
                print(f"连接异常: {e}")
            finally:
                self.ws = None
                if self.on_disconnect:
                    await self.on_disconnect()
            
            if self.running:
                print("5秒后重连...")
                await asyncio.sleep(5)
    
    async def send(self, data: dict):
        """发送消息"""
        if self.ws:
            await self.ws.send(json.dumps(data))
    
    async def close(self):
        """关闭连接"""
        self.running = False
        if self.ws:
            await self.ws.close()
