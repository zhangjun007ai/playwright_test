#!/usr/bin/env python3
"""
测试Inspector录制器集成
验证Playwright Inspector录制器的所有功能
"""

import asyncio
import json
import sys
import time
import requests
import websocket
import threading
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")

class InspectorTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.ws = None
        self.messages = []
        self.connected = False
        
    def test_api_connection(self):
        """测试API连接"""
        try:
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                logger.info("✅ API连接正常")
                return True
            else:
                logger.error(f"❌ API连接失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ API连接异常: {e}")
            return False
    
    def test_websocket_connection(self):
        """测试WebSocket连接"""
        try:
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    self.messages.append(data)
                    logger.info(f"📨 收到WebSocket消息: {data.get('type', 'unknown')}")
                except Exception as e:
                    logger.error(f"❌ 解析WebSocket消息失败: {e}")
            
            def on_open(ws):
                self.connected = True
                logger.info("✅ WebSocket连接建立")
                
            def on_close(ws, close_status_code, close_msg):
                self.connected = False
                logger.info("🔌 WebSocket连接关闭")
                
            def on_error(ws, error):
                logger.error(f"❌ WebSocket错误: {error}")
            
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=on_message,
                on_open=on_open,
                on_close=on_close,
                on_error=on_error
            )
            
            # 在后台线程中运行WebSocket
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # 等待连接建立
            timeout = 5
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
            
            return self.connected
            
        except Exception as e:
            logger.error(f"❌ WebSocket连接异常: {e}")
            return False
    
    def test_recording_status(self):
        """测试录制状态API"""
        try:
            response = requests.get(f"{self.base_url}/api/recording/status")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 录制状态获取成功: {data.get('message', '未知状态')}")
                logger.info(f"   - 实时录制器: {'录制中' if data.get('realtime_recorder', {}).get('is_recording') else '空闲'}")
                logger.info(f"   - Inspector录制器: {'录制中' if data.get('inspector_recorder', {}).get('is_recording') else '空闲'}")
                return True
            else:
                logger.error(f"❌ 录制状态获取失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 录制状态获取异常: {e}")
            return False
    
    def test_inspector_recording_start(self):
        """测试启动Inspector录制"""
        try:
            payload = {
                "test_name": "test_inspector_recording",
                "description": "测试Inspector录制器功能",
                "recorder_type": "inspector"
            }
            
            response = requests.post(
                f"{self.base_url}/api/recording/start",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info(f"✅ Inspector录制启动成功: {data.get('message')}")
                    logger.info(f"   会话ID: {data.get('session_id')}")
                    logger.info(f"   录制器类型: {data.get('recorder_type')}")
                    if data.get('instructions'):
                        logger.info(f"   说明: {data.get('instructions')}")
                    return data.get('session_id')
                else:
                    logger.error(f"❌ Inspector录制启动失败: {data.get('error', '未知错误')}")
                    return None
            else:
                logger.error(f"❌ Inspector录制启动请求失败: {response.status_code}")
                logger.error(f"   响应内容: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Inspector录制启动异常: {e}")
            return None
    
    def test_inspector_recording_stop(self):
        """测试停止Inspector录制"""
        try:
            response = requests.post(f"{self.base_url}/api/recording/stop")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info(f"✅ 录制停止成功: {data.get('message')}")
                    session = data.get('session', {})
                    if session:
                        logger.info(f"   会话名称: {session.get('name')}")
                        logger.info(f"   操作数量: {session.get('action_count', 0)}")
                    return True
                else:
                    logger.error(f"❌ 录制停止失败: {data.get('error', '未知错误')}")
                    return False
            else:
                logger.error(f"❌ 录制停止请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 录制停止异常: {e}")
            return False
    
    def wait_for_messages(self, timeout=10):
        """等待WebSocket消息"""
        logger.info(f"⏳ 等待WebSocket消息 (最多{timeout}秒)...")
        start_time = time.time()
        initial_count = len(self.messages)
        
        while time.time() - start_time < timeout:
            if len(self.messages) > initial_count:
                logger.info(f"📨 收到 {len(self.messages) - initial_count} 条新消息")
                break
            time.sleep(0.1)
        
        # 显示消息详情
        for i, msg in enumerate(self.messages[initial_count:], 1):
            logger.info(f"   消息 {i}: {msg.get('type', 'unknown')} - {msg.get('message', str(msg)[:100])}...")
    
    def run_full_test(self):
        """运行完整测试流程"""
        logger.info("🚀 开始Inspector录制器集成测试")
        logger.info("=" * 50)
        
        # 1. 测试API连接
        logger.info("1️⃣ 测试API连接...")
        if not self.test_api_connection():
            logger.error("❌ API连接测试失败，终止测试")
            return False
        
        # 2. 测试WebSocket连接
        logger.info("\n2️⃣ 测试WebSocket连接...")
        if not self.test_websocket_connection():
            logger.error("❌ WebSocket连接测试失败，终止测试")
            return False
        
        # 3. 测试录制状态
        logger.info("\n3️⃣ 测试录制状态API...")
        self.test_recording_status()
        
        # 4. 测试Inspector录制启动
        logger.info("\n4️⃣ 测试Inspector录制启动...")
        session_id = self.test_inspector_recording_start()
        if not session_id:
            logger.error("❌ Inspector录制启动失败，跳过后续测试")
            return False
        
        # 5. 等待录制开始消息
        logger.info("\n5️⃣ 等待录制开始消息...")
        self.wait_for_messages(5)
        
        # 6. 给用户时间进行操作
        logger.info("\n6️⃣ 请在打开的Playwright Inspector窗口中进行一些操作...")
        logger.info("   👆 点击元素、输入文本、导航等操作")
        logger.info("   ⏰ 30秒后将自动停止录制，或按Ctrl+C提前停止")
        
        try:
            for i in range(30, 0, -1):
                print(f"\r   ⏳ 剩余时间: {i}秒", end="", flush=True)
                time.sleep(1)
                # 检查是否有新消息
                if len(self.messages) > 0:
                    break
        except KeyboardInterrupt:
            logger.info("\n   用户中断，开始停止录制...")
        
        print("\n")
        
        # 7. 测试录制停止
        logger.info("7️⃣ 测试录制停止...")
        if not self.test_inspector_recording_stop():
            logger.error("❌ 录制停止失败")
            return False
        
        # 8. 等待停止消息
        logger.info("\n8️⃣ 等待录制停止消息...")
        self.wait_for_messages(5)
        
        # 9. 最终状态检查
        logger.info("\n9️⃣ 最终状态检查...")
        self.test_recording_status()
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ Inspector录制器集成测试完成")
        logger.info(f"📊 总共收到 {len(self.messages)} 条WebSocket消息")
        
        return True

def main():
    """主函数"""
    tester = InspectorTester()
    
    try:
        success = tester.run_full_test()
        if success:
            logger.info("🎉 所有测试通过！")
            sys.exit(0)
        else:
            logger.error("💥 测试失败！")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 用户中断测试")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 测试异常: {e}")
        sys.exit(1)
    finally:
        if tester.ws:
            tester.ws.close()

if __name__ == "__main__":
    main() 