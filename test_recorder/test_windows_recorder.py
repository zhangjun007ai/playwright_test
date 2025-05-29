#!/usr/bin/env python3
import requests
import json
import time
import websocket
import threading

def test_windows_recorder():
    """测试Windows录制器功能"""
    base_url = "http://127.0.0.1:8000"
    
    print("🎬 开始测试Windows录制器...")
    
    # WebSocket连接
    ws_messages = []
    ws_connected = False
    
    def on_ws_message(ws, message):
        try:
            data = json.loads(message)
            ws_messages.append(data)
            print(f"📡 WebSocket收到消息: {data.get('type', 'unknown')}")
            if data.get('type') == 'action_recorded':
                action = data.get('action', {})
                print(f"   操作类型: {action.get('action_type', 'unknown')}")
                print(f"   页面URL: {action.get('page_url', 'N/A')}")
        except Exception as e:
            print(f"   WebSocket消息解析失败: {e}")
    
    def on_ws_open(ws):
        nonlocal ws_connected
        ws_connected = True
        print("📡 WebSocket连接已建立")
        # 发送ping测试
        ws.send(json.dumps({"type": "ping"}))
    
    def on_ws_close(ws, close_status_code, close_msg):
        nonlocal ws_connected
        ws_connected = False
        print("📡 WebSocket连接已关闭")
    
    def on_ws_error(ws, error):
        print(f"📡 WebSocket错误: {error}")
    
    # 启动WebSocket连接
    print("\n1. 建立WebSocket连接...")
    ws = websocket.WebSocketApp(
        "ws://127.0.0.1:8000/ws",
        on_message=on_ws_message,
        on_open=on_ws_open,
        on_close=on_ws_close,
        on_error=on_ws_error
    )
    
    ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
    ws_thread.start()
    
    # 等待WebSocket连接
    time.sleep(3)
    if not ws_connected:
        print("   ❌ WebSocket连接失败，但继续测试...")
    else:
        print("   ✅ WebSocket连接成功")
    
    # 2. 检查初始状态
    print("\n2. 检查初始状态...")
    response = requests.get(f"{base_url}/api/status")
    status = response.json()
    print(f"   录制状态: {status['recording']}")
    print(f"   浏览器初始化: {status['browser_initialized']}")
    
    # 3. 开始录制
    print("\n3. 开始录制...")
    start_data = {
        "test_name": "Windows录制器测试",
        "description": "测试Windows录制器功能"
    }
    
    try:
        response = requests.post(f"{base_url}/api/recording/start", json=start_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 录制开始成功")
            print(f"   会话ID: {result['session_id']}")
            session_id = result['session_id']
        else:
            print(f"   ❌ 录制开始失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 录制开始异常: {e}")
        return False
    
    # 4. 等待浏览器启动
    print("\n4. 等待浏览器启动...")
    time.sleep(5)
    
    # 5. 检查录制状态
    print("\n5. 检查录制状态...")
    response = requests.get(f"{base_url}/api/status")
    status = response.json()
    print(f"   录制状态: {status['recording']}")
    print(f"   当前操作数: {status['action_count']}")
    
    # 6. 等待用户操作
    print("\n6. 等待用户操作...")
    print("   请在弹出的Playwright Inspector中进行一些操作：")
    print("   - 在地址栏输入网址（如 https://www.baidu.com）")
    print("   - 点击页面上的元素")
    print("   - 输入文本")
    print("   - 按回车键继续测试...")
    input()
    
    # 7. 检查WebSocket消息
    print("\n7. 检查WebSocket消息...")
    print(f"   收到的WebSocket消息数: {len(ws_messages)}")
    for i, msg in enumerate(ws_messages[-5:]):  # 显示最近5条消息
        print(f"   消息{i+1}: {msg.get('type', 'unknown')}")
    
    # 8. 检查操作记录
    print("\n8. 检查操作记录...")
    response = requests.get(f"{base_url}/api/status")
    status = response.json()
    print(f"   当前操作数: {status['action_count']}")
    
    # 9. 停止录制
    print("\n9. 停止录制...")
    try:
        response = requests.post(f"{base_url}/api/recording/stop")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 录制停止成功")
            print(f"   总操作数: {len(result['session']['actions'])}")
            
            # 显示录制的操作
            if result['session']['actions']:
                print("\n   录制的操作:")
                for i, action in enumerate(result['session']['actions'][:5]):
                    print(f"   {i+1}. {action['action_type']} - {action.get('page_url', 'N/A')}")
                if len(result['session']['actions']) > 5:
                    print(f"   ... 还有 {len(result['session']['actions']) - 5} 个操作")
            else:
                print("   ⚠️ 没有录制到任何操作")
                
        else:
            print(f"   ❌ 录制停止失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 录制停止异常: {e}")
        return False
    
    # 10. 验证浏览器是否关闭
    print("\n10. 验证浏览器是否关闭...")
    time.sleep(3)
    print("   请检查Playwright Inspector是否已关闭")
    print("   如果还在运行，说明浏览器进程关闭有问题")
    
    # 关闭WebSocket
    ws.close()
    
    print("\n🎉 Windows录制器测试完成！")
    return True

if __name__ == "__main__":
    test_windows_recorder() 