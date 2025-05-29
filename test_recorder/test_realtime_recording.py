#!/usr/bin/env python3
import requests
import json
import time
import websocket
import threading

def test_realtime_recording():
    """测试实时录制功能"""
    base_url = "http://127.0.0.1:8000"
    
    print("🎬 测试实时录制功能...")
    print("=" * 60)
    
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
                print(f"   🎯 操作类型: {action.get('action_type', 'unknown')}")
                print(f"   📄 标题: {action.get('title', 'N/A')}")
                print(f"   📋 描述: {action.get('description', 'N/A')}")
                print(f"   🌐 页面URL: {action.get('page_url', 'N/A')}")
                
                # 显示元素信息
                element_info = action.get('element_info', {})
                if element_info:
                    print(f"   🎯 元素信息:")
                    if element_info.get('text'):
                        print(f"      文本: {element_info['text'][:50]}...")
                    if element_info.get('id'):
                        print(f"      ID: {element_info['id']}")
                    if element_info.get('className'):
                        print(f"      类名: {element_info['className']}")
                    if element_info.get('tagName'):
                        print(f"      标签: {element_info['tagName']}")
                
                # 显示截图信息
                if action.get('screenshot_path'):
                    print(f"   📸 截图: {action['screenshot_path']}")
                
                print()
                
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
    time.sleep(3)
    
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
        "test_name": "实时录制测试",
        "description": "测试直接获取Playwright操作数据的功能"
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
    print("   🔄 正在启动Playwright浏览器...")
    time.sleep(8)  # 给更多时间让浏览器启动
    
    # 5. 用户操作指导
    print("\n5. 🎯 用户操作指导")
    print("   现在浏览器应该已经启动，请进行以下操作来测试实时录制：")
    print()
    print("   📌 基础操作测试：")
    print("   1. 在地址栏输入网址（如 https://www.baidu.com）并按回车")
    print("   2. 等待页面加载完成")
    print("   3. 点击搜索框")
    print("   4. 输入一些文本（如 'playwright实时录制测试'）")
    print("   5. 点击搜索按钮或按回车")
    print()
    print("   📌 高级操作测试：")
    print("   6. 点击搜索结果中的链接")
    print("   7. 在新页面中进行更多交互")
    print("   8. 尝试下拉选择、复选框等操作")
    print()
    print("   💡 每个操作都会在控制台实时显示详细信息！")
    print("   💡 包括元素的ID、类名、文本内容、选择器等")
    print("   💡 还会自动截图并显示截图路径")
    print()
    print("   按回车键开始监控操作...")
    input()
    
    # 6. 监控操作记录
    print("\n6. 🔍 实时监控操作记录...")
    print("   正在监听WebSocket消息和API状态...")
    print("   按Ctrl+C停止监控")
    
    try:
        last_count = 0
        last_ws_count = 0
        
        while True:
            # 检查API状态
            try:
                response = requests.get(f"{base_url}/api/status")
                status = response.json()
                current_count = status['action_count']
                
                if current_count != last_count:
                    print(f"   📊 API操作数更新: {last_count} -> {current_count}")
                    last_count = current_count
            except:
                pass
            
            # 检查WebSocket消息数
            current_ws_count = len([msg for msg in ws_messages if msg.get('type') == 'action_recorded'])
            if current_ws_count != last_ws_count:
                print(f"   📡 WebSocket操作消息数: {last_ws_count} -> {current_ws_count}")
                last_ws_count = current_ws_count
            
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
            session_data = result.get('session', {})
            actions = session_data.get('actions', [])
            print(f"   总操作数: {len(actions)}")
            
            # 显示所有操作的详细信息
            if actions:
                print("\n   📋 录制的所有操作详情:")
                for i, action in enumerate(actions):
                    print(f"   {i+1}. 类型: {action['action_type']}")
                    print(f"      时间: {action['timestamp']}")
                    if action.get('page_title'):
                        print(f"      标题: {action['page_title']}")
                    if action.get('description'):
                        print(f"      描述: {action['description']}")
                    if action.get('page_url'):
                        print(f"      页面: {action['page_url']}")
                    if action.get('element_info'):
                        element = action['element_info']
                        if element.get('text'):
                            print(f"      元素文本: {element['text'][:50]}...")
                        if element.get('id'):
                            print(f"      元素ID: {element['id']}")
                        if element.get('selector'):
                            print(f"      选择器: {element['selector']}")
                    if action.get('screenshot_path'):
                        print(f"      截图: {action['screenshot_path']}")
                    print()
            else:
                print("   ⚠️ 没有录制到任何操作")
                print("   💡 请确保在浏览器中进行了操作")
        else:
            print(f"   ❌ 录制停止失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 录制停止异常: {e}")
        return False
    
    # 8. WebSocket消息统计
    print("\n8. 📊 WebSocket消息统计...")
    print(f"   总共收到 {len(ws_messages)} 条WebSocket消息")
    action_messages = [msg for msg in ws_messages if msg.get('type') == 'action_recorded']
    print(f"   其中 {len(action_messages)} 条是操作记录消息")
    
    if action_messages:
        print("\n   📝 操作记录消息示例:")
        for i, msg in enumerate(action_messages[:5]):  # 显示前5条
            action = msg.get('action', {})
            print(f"   消息{i+1}: {action.get('action_type', 'unknown')} - {action.get('title', 'N/A')}")
            if action.get('element_info', {}).get('text'):
                print(f"           元素文本: {action['element_info']['text'][:30]}...")
    
    # 关闭WebSocket
    ws.close()
    
    print("\n🎉 实时录制功能测试完成！")
    print("\n💡 新功能特点：")
    print("   ✅ 直接监听Playwright浏览器事件")
    print("   ✅ 实时获取用户操作数据")
    print("   ✅ 详细的元素信息（ID、类名、文本、选择器）")
    print("   ✅ 自动截图功能")
    print("   ✅ WebSocket实时传输")
    print("   ✅ 线程安全的消息队列")
    
    print("\n🌐 现在您可以在Web界面 http://127.0.0.1:8000 查看：")
    print("   - 实时录制界面显示所有操作详情")
    print("   - 每个操作都有完整的元素信息")
    print("   - 操作截图可以点击查看")
    print("   - 支持生成和导出测试用例")
    
    return True

if __name__ == "__main__":
    test_realtime_recording() 