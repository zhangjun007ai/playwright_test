#!/usr/bin/env python3
"""
测试事件捕获功能
验证修复后的JavaScript事件监听器是否能正确工作
"""

import asyncio
import json
import time
import websockets
import requests
from datetime import datetime
from loguru import logger

# 配置日志
logger.add("test_event_capture.log", rotation="1 MB")

class EventCaptureTester:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.test_page_url = "http://localhost:8000/static/test_page.html"
        self.received_events = []
        self.session_id = None
        
    async def test_event_capture_workflow(self):
        """测试完整的事件捕获工作流程"""
        logger.info("开始测试事件捕获功能...")
        
        try:
            # 启动WebSocket监听
            websocket_task = asyncio.create_task(self.monitor_websocket_messages())
            
            # 等待WebSocket连接建立
            await asyncio.sleep(1)
            
            # 开始录制
            logger.info("开始录制...")
            start_response = requests.post(f"{self.api_base}/api/recording/start", 
                json={
                    "test_name": "事件捕获测试",
                    "description": "测试JavaScript事件监听器是否正常工作"
                })
            
            if start_response.status_code == 200:
                result = start_response.json()
                if result.get("success"):
                    self.session_id = result.get('session_id')
                    logger.success(f"录制开始成功，会话ID: {self.session_id}")
                else:
                    logger.error(f"录制开始失败: {result.get('error')}")
                    return False
            else:
                logger.error(f"API请求失败: {start_response.status_code}")
                return False
            
            # 等待录制开始消息
            await asyncio.sleep(2)
            
            # 指导用户进行测试
            logger.info("录制已开始，现在请进行以下测试：")
            logger.info(f"1. 在浏览器中访问测试页面: {self.test_page_url}")
            logger.info("2. 点击页面上的各种按钮和链接")
            logger.info("3. 在输入框中输入文本")
            logger.info("4. 选择下拉框中的选项")
            logger.info("5. 等待30秒进行测试...")
            
            # 监听30秒
            for i in range(30, 0, -1):
                print(f"\r剩余测试时间: {i} 秒，已捕获事件: {len([e for e in self.received_events if e['data'].get('type') == 'action_recorded'])}", end="", flush=True)
                await asyncio.sleep(1)
            
            print()  # 换行
            
            # 停止录制
            logger.info("停止录制...")
            stop_response = requests.post(f"{self.api_base}/api/recording/stop")
            
            if stop_response.status_code == 200:
                result = stop_response.json()
                if result.get("success"):
                    logger.success("录制停止成功")
                else:
                    logger.error(f"录制停止失败: {result.get('error')}")
            
            # 取消WebSocket监听任务
            websocket_task.cancel()
            
            # 分析接收到的事件
            return self.analyze_captured_events()
            
        except Exception as e:
            logger.error(f"事件捕获测试失败: {e}")
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
                        self.received_events.append({
                            'timestamp': datetime.now().isoformat(),
                            'data': data
                        })
                        
                        if data.get('type') == 'action_recorded':
                            action = data.get('action', {})
                            logger.info(f"捕获到事件: {action.get('action_type')} - {action.get('description', '')[:50]}...")
                        
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("WebSocket连接已关闭")
                        break
                    except asyncio.CancelledError:
                        logger.info("WebSocket监听任务已取消")
                        break
                        
        except Exception as e:
            logger.error(f"WebSocket监听失败: {e}")
    
    def analyze_captured_events(self):
        """分析捕获到的事件"""
        logger.info(f"分析捕获到的事件，总消息数: {len(self.received_events)}")
        
        # 统计消息类型
        message_types = {}
        action_events = []
        
        for event in self.received_events:
            msg_type = event['data'].get('type', 'unknown')
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            if msg_type == 'action_recorded':
                action_events.append(event)
        
        logger.info("消息类型统计:")
        for msg_type, count in message_types.items():
            logger.info(f"  {msg_type}: {count} 条")
        
        # 分析操作事件
        if action_events:
            logger.success(f"成功捕获 {len(action_events)} 个用户操作事件")
            
            # 统计操作类型
            action_types = {}
            for event in action_events:
                action = event['data'].get('action', {})
                action_type = action.get('action_type', 'unknown')
                action_types[action_type] = action_types.get(action_type, 0) + 1
            
            logger.info("操作类型统计:")
            for action_type, count in action_types.items():
                logger.info(f"  {action_type}: {count} 次")
            
            # 显示前5个事件的详细信息
            logger.info("前5个事件详细信息:")
            for i, event in enumerate(action_events[:5]):
                action = event['data'].get('action', {})
                logger.info(f"  {i+1}. {action.get('action_type')} - {action.get('description', '')}")
                if action.get('playwright_code'):
                    logger.info(f"     代码: {action['playwright_code']}")
            
            # 检查是否有用户交互事件（非导航事件）
            user_interactions = [e for e in action_events 
                               if e['data'].get('action', {}).get('action_type') not in ['goto', 'load']]
            
            if user_interactions:
                logger.success(f"✅ 成功捕获到 {len(user_interactions)} 个用户交互事件")
                logger.success("✅ JavaScript事件监听器工作正常")
                return True
            else:
                logger.warning("❌ 没有捕获到用户交互事件，只有页面导航事件")
                logger.warning("❌ 可能JavaScript事件监听器没有正常工作")
                return False
        else:
            logger.error("❌ 没有捕获到任何操作事件")
            logger.error("❌ JavaScript事件监听器可能完全无效")
            return False
    
    def show_instructions(self):
        """显示测试说明"""
        print("\n" + "="*60)
        print("🎭 Playwright 事件捕获功能测试")
        print("="*60)
        print(f"测试页面地址: {self.test_page_url}")
        print("\n测试步骤:")
        print("1. 确保系统已启动 (http://localhost:8000)")
        print("2. 运行本测试脚本")
        print("3. 在浏览器中打开测试页面")
        print("4. 执行各种操作（点击、输入、选择等）")
        print("5. 观察控制台输出，确认事件被捕获")
        print("\n预期结果:")
        print("- 每次点击、输入等操作都会被实时捕获")
        print("- 控制台会显示'捕获到事件'的日志")
        print("- 最终会显示统计信息和测试结果")
        print("="*60 + "\n")

async def main():
    """主函数"""
    tester = EventCaptureTester()
    
    # 显示测试说明
    tester.show_instructions()
    
    # 确认用户准备好开始测试
    input("按回车键开始测试...")
    
    # 运行测试
    success = await tester.test_event_capture_workflow()
    
    if success:
        logger.success("🎉 事件捕获功能测试通过！")
        print("\n✅ 测试结果: 成功")
        print("JavaScript事件监听器正常工作，可以捕获用户交互事件")
    else:
        logger.error("💥 事件捕获功能测试失败！")
        print("\n❌ 测试结果: 失败")
        print("需要进一步检查JavaScript事件监听器的实现")

if __name__ == "__main__":
    asyncio.run(main()) 