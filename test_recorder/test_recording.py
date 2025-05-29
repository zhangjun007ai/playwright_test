#!/usr/bin/env python3
import requests
import json
import time

def test_recording():
    """测试录制功能"""
    base_url = "http://127.0.0.1:8000"
    
    print("🎬 开始测试录制功能...")
    
    # 1. 检查初始状态
    print("\n1. 检查初始状态...")
    response = requests.get(f"{base_url}/api/status")
    status = response.json()
    print(f"   录制状态: {status['recording']}")
    print(f"   浏览器初始化: {status['browser_initialized']}")
    
    # 2. 开始录制
    print("\n2. 开始录制...")
    start_data = {
        "test_name": "自动化测试用例",
        "description": "测试增强录制器功能"
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
    
    # 3. 检查录制状态
    print("\n3. 检查录制状态...")
    time.sleep(2)  # 等待浏览器启动
    response = requests.get(f"{base_url}/api/status")
    status = response.json()
    print(f"   录制状态: {status['recording']}")
    print(f"   浏览器初始化: {status['browser_initialized']}")
    print(f"   当前操作数: {status['action_count']}")
    
    # 4. 导航到测试页面
    print("\n4. 导航到测试页面...")
    nav_data = {"url": "https://www.baidu.com"}
    try:
        response = requests.post(f"{base_url}/api/recording/navigate", json=nav_data)
        if response.status_code == 200:
            print(f"   ✅ 导航成功")
        else:
            print(f"   ❌ 导航失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 导航异常: {e}")
    
    # 5. 等待用户操作
    print("\n5. 等待用户操作...")
    print("   请在弹出的浏览器中进行一些操作（点击、输入等）")
    print("   按回车键继续...")
    input()
    
    # 6. 检查操作记录
    print("\n6. 检查操作记录...")
    response = requests.get(f"{base_url}/api/status")
    status = response.json()
    print(f"   当前操作数: {status['action_count']}")
    
    # 7. 停止录制
    print("\n7. 停止录制...")
    try:
        response = requests.post(f"{base_url}/api/recording/stop")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 录制停止成功")
            print(f"   总操作数: {len(result['session']['actions'])}")
            
            # 显示录制的操作
            if result['session']['actions']:
                print("\n   录制的操作:")
                for i, action in enumerate(result['session']['actions'][:5]):  # 只显示前5个
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
    
    print("\n🎉 录制功能测试完成！")
    return True

if __name__ == "__main__":
    test_recording() 