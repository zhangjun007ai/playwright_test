#!/usr/bin/env python3
"""
测试实时显示功能
验证WebSocket消息是否能正确传输到前端并实时显示
"""

import asyncio
import json
import time
import websockets
import requests
from datetime import datetime
from loguru import logger

# 配置日志
logger.add("test_realtime_display.log", rotation="1 MB")

class RealtimeDisplayTester:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.received_messages = []
        
    async def test_websocket_connection(self):
        """测试WebSocket连接"""
        logger.info("开始测试WebSocket连接...")
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                logger.info("WebSocket连接成功建立")
                
                # 发送心跳
                await websocket.send(json.dumps({"type": "ping"}))
                logger.info("已发送心跳消息")
                
                # 等待响应
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                logger.info(f"收到响应: {message}")
                
                if message.get("type") == "pong":
                    logger.success("心跳测试成功")
                    return True
                else:
                    logger.error(f"心跳响应错误: {message}")
                    return False
                    
        except Exception as e:
            logger.error(f"WebSocket连接测试失败: {e}")
            return False
    
    async def test_recording_workflow(self):
        """测试完整的录制工作流程"""
        logger.info("开始测试录制工作流程...")
        
        try:
            # 启动WebSocket监听
            websocket_task = asyncio.create_task(self.monitor_websocket_messages())
            
            # 等待一秒让WebSocket连接建立
            await asyncio.sleep(1)
            
            # 开始录制
            logger.info("发送开始录制请求...")
            start_response = requests.post(f"{self.api_base}/api/recording/start", 
                json={
                    "test_name": "实时显示测试",
                    "description": "测试WebSocket实时消息传输"
                })
            
            if start_response.status_code == 200:
                result = start_response.json()
                if result.get("success"):
                    logger.success(f"录制开始成功，会话ID: {result.get('session_id')}")
                    session_id = result.get('session_id')
                else:
                    logger.error(f"录制开始失败: {result.get('error')}")
                    return False
            else:
                logger.error(f"API请求失败: {start_response.status_code}")
                return False
            
            # 等待一段时间来接收消息
            logger.info("等待接收WebSocket消息...")
            await asyncio.sleep(3)
            
            # 停止录制
            logger.info("发送停止录制请求...")
            stop_response = requests.post(f"{self.api_base}/api/recording/stop")
            
            if stop_response.status_code == 200:
                result = stop_response.json()
                if result.get("success"):
                    logger.success("录制停止成功")
                else:
                    logger.error(f"录制停止失败: {result.get('error')}")
            
            # 取消WebSocket监听任务
            websocket_task.cancel()
            
            # 分析接收到的消息
            self.analyze_received_messages()
            
            return True
            
        except Exception as e:
            logger.error(f"录制工作流程测试失败: {e}")
            return False
    
    async def monitor_websocket_messages(self):
        """监听WebSocket消息"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                logger.info("WebSocket监听器已启动")
                
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        self.received_messages.append({
                            'timestamp': datetime.now().isoformat(),
                            'data': data
                        })
                        logger.info(f"收到WebSocket消息: {data.get('type', 'unknown')}")
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("WebSocket连接已关闭")
                        break
                    except asyncio.CancelledError:
                        logger.info("WebSocket监听任务已取消")
                        break
                        
        except Exception as e:
            logger.error(f"WebSocket监听失败: {e}")
    
    def analyze_received_messages(self):
        """分析接收到的消息"""
        logger.info(f"共接收到 {len(self.received_messages)} 条消息")
        
        message_types = {}
        for msg in self.received_messages:
            msg_type = msg['data'].get('type', 'unknown')
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        logger.info("消息类型统计:")
        for msg_type, count in message_types.items():
            logger.info(f"  {msg_type}: {count} 条")
        
        # 检查是否有action_recorded消息
        action_messages = [msg for msg in self.received_messages 
                          if msg['data'].get('type') == 'action_recorded']
        
        if action_messages:
            logger.success(f"检测到 {len(action_messages)} 条操作记录消息")
            for i, msg in enumerate(action_messages[:3]):  # 只显示前3条
                action = msg['data'].get('action', {})
                logger.info(f"  操作 {i+1}: {action.get('action_type')} - {action.get('description', '')}")
                if action.get('playwright_code'):
                    logger.info(f"    Playwright代码: {action['playwright_code'][:50]}...")
        else:
            logger.warning("未检测到操作记录消息")
        
        return len(action_messages) > 0
    
    def test_api_status(self):
        """测试API状态"""
        logger.info("测试API状态...")
        
        try:
            response = requests.get(f"{self.api_base}/api/status")
            if response.status_code == 200:
                status = response.json()
                logger.success(f"API状态正常: {status}")
                return True
            else:
                logger.error(f"API状态请求失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"API状态测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行实时显示功能测试...")
        
        results = {}
        
        # 测试API状态
        results['api_status'] = self.test_api_status()
        
        # 测试WebSocket连接
        results['websocket_connection'] = await self.test_websocket_connection()
        
        # 测试录制工作流程
        results['recording_workflow'] = await self.test_recording_workflow()
        
        # 输出测试结果
        logger.info("测试结果汇总:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {test_name}: {status}")
        
        all_passed = all(results.values())
        if all_passed:
            logger.success("所有测试通过！实时显示功能正常")
        else:
            logger.error("部分测试失败，需要进一步调试")
        
        return all_passed

async def main():
    """主函数"""
    tester = RealtimeDisplayTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 