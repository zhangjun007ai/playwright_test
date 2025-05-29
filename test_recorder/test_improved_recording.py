#!/usr/bin/env python3
import requests
import json
import time
import websocket
import threading

def test_improved_recording():
    """测试改进后的录制功能"""
    base_url = "http://127.0.0.1:8000"
    
    print("🎬 测试改进后的录制功能...")
    
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
                print(f"   📝 操作类型: {action.get('action_type', 'unknown')}")
                print(f"   📄 标题: {action.get('title', 'N/A')}")
                print(f"   📋 描述: {action.get('description', 'N/A')}")
                print(f"   🌐 页面URL: {action.get('page_url', 'N/A')}")
                if action.get('element_info'):
                    element = action['element_info']
                    print(f"   🎯 元素: {element.get('description', element.get('selector', 'N/A'))}")
        except Exception as e:
            print(f"   WebSocket消息解析失败: {e}")
    
    def on_ws_open(ws):
        nonlocal ws_connected
        ws_connected = True
        print("📡 WebSocket连接已建立")
        ws.send(json.dumps({"type": "ping"}))
    
    def on_ws_close(ws, close_status_code, close_msg):
        nonlocal ws_connected
        ws_connected = False
        print("📡 WebSocket连接已关闭")
    
    def on_ws_error(ws, error):
        print(f"📡 WebSocket错误: {error}")
    
    # 等待应用启动
    print("\n1. 等待应用启动...")
    time.sleep(5)
    
    # 启动WebSocket连接
    print("\n2. 建立WebSocket连接...")
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
    
    # 3. 开始录制
    print("\n3. 开始录制...")
    start_data = {
        "test_name": "改进功能测试",
        "description": "测试改进后的操作记录显示功能"
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
    
    # 5. 用户操作指导
    print("\n5. 用户操作指导...")
    print("   🎯 请在Playwright Inspector中进行以下操作来测试改进后的功能：")
    print("   1. 在地址栏输入网址（如 https://www.baidu.com）并按回车")
    print("   2. 点击页面上的搜索框")
    print("   3. 输入一些文本（如 'playwright测试'）")
    print("   4. 点击搜索按钮或按回车")
    print("   5. 点击搜索结果中的链接")
    print("   ")
    print("   💡 每个操作都会在实时录制界面显示详细信息！")
    print("   按回车键继续监控...")
    input()
    
    # 6. 监控操作记录
    print("\n6. 监控操作记录...")
    print("   实时显示WebSocket接收到的操作信息...")
    print("   按Ctrl+C停止监控")
    
    try:
        last_count = 0
        while True:
            response = requests.get(f"{base_url}/api/status")
            status = response.json()
            current_count = status['action_count']
            
            if current_count != last_count:
                print(f"   📊 操作数更新: {last_count} -> {current_count}")
                last_count = current_count
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n   停止监控")
    
    # 7. 停止录制
    print("\n7. 停止录制...")
    try:
        response = requests.post(f"{base_url}/api/recording/stop")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 录制停止成功")
            print(f"   总操作数: {len(result['session']['actions'])}")
            
            # 显示所有操作的详细信息
            if result['session']['actions']:
                print("\n   📋 录制的所有操作详情:")
                for i, action in enumerate(result['session']['actions']):
                    print(f"   {i+1}. 类型: {action['action_type']}")
                    if 'title' in action:
                        print(f"      标题: {action['title']}")
                    if 'description' in action:
                        print(f"      描述: {action['description']}")
                    if action.get('page_url'):
                        print(f"      页面: {action['page_url']}")
                    if action.get('additional_data'):
                        try:
                            data = json.loads(action['additional_data'])
                            if data:
                                print(f"      数据: {data}")
                        except:
                            print(f"      数据: {action['additional_data']}")
                    print()
            else:
                print("   ⚠️ 没有录制到任何操作")
        else:
            print(f"   ❌ 录制停止失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 录制停止异常: {e}")
        return False
    
    # 8. 检查WebSocket消息
    print("\n8. WebSocket消息统计...")
    print(f"   总共收到 {len(ws_messages)} 条WebSocket消息")
    action_messages = [msg for msg in ws_messages if msg.get('type') == 'action_recorded']
    print(f"   其中 {len(action_messages)} 条是操作记录消息")
    
    if action_messages:
        print("\n   📝 操作记录消息示例:")
        for i, msg in enumerate(action_messages[:3]):  # 显示前3条
            action = msg.get('action', {})
            print(f"   消息{i+1}: {action.get('action_type', 'unknown')} - {action.get('title', 'N/A')}")
    
    # 关闭WebSocket
    ws.close()
    
    print("\n🎉 改进功能测试完成！")
    print("\n💡 现在您可以在Web界面 http://127.0.0.1:8000 查看：")
    print("   - 实时录制界面应该显示详细的操作信息")
    print("   - 每个操作都有图标、标题、描述和页面URL")
    print("   - 操作类型标签和时间戳")
    
    return True

if __name__ == "__main__":
    test_improved_recording() 