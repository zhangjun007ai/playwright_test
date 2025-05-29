#!/usr/bin/env python3
import requests
import json
import time

def test_simple_recording():
    """简化的录制测试"""
    base_url = "http://127.0.0.1:8000"
    
    print("🎬 开始简化录制测试...")
    
    # 1. 开始录制
    print("\n1. 开始录制...")
    start_data = {
        "test_name": "简化测试",
        "description": "测试操作记录"
    }
    
    response = requests.post(f"{base_url}/api/recording/start", json=start_data)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 录制开始成功")
        print(f"   会话ID: {result['session_id']}")
        session_id = result['session_id']
    else:
        print(f"   ❌ 录制开始失败: {response.text}")
        return False
    
    # 2. 等待浏览器启动
    print("\n2. 等待浏览器启动...")
    time.sleep(3)
    
    # 3. 持续监控操作数
    print("\n3. 监控操作记录...")
    print("   请在Playwright Inspector中进行操作，我会实时显示操作数...")
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
    
    # 4. 停止录制
    print("\n4. 停止录制...")
    response = requests.post(f"{base_url}/api/recording/stop")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 录制停止成功")
        print(f"   总操作数: {len(result['session']['actions'])}")
        
        # 显示所有操作
        if result['session']['actions']:
            print("\n   录制的所有操作:")
            for i, action in enumerate(result['session']['actions']):
                print(f"   {i+1}. {action['action_type']} - {action.get('page_url', 'N/A')}")
                if action.get('additional_data'):
                    try:
                        data = json.loads(action['additional_data'])
                        if data:
                            print(f"      数据: {data}")
                    except:
                        print(f"      数据: {action['additional_data']}")
        else:
            print("   ⚠️ 没有录制到任何操作")
    else:
        print(f"   ❌ 录制停止失败: {response.text}")
        return False
    
    print("\n🎉 简化录制测试完成！")
    return True

if __name__ == "__main__":
    test_simple_recording() 