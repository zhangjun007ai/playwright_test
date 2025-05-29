#!/usr/bin/env python3
import requests
import json
import traceback

def debug_recording():
    """调试录制功能"""
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 开始调试录制功能...")
    
    # 1. 测试基本连接
    print("\n1. 测试基本连接...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return
    
    # 2. 测试开始录制
    print("\n2. 测试开始录制...")
    start_data = {
        "test_name": "调试测试",
        "description": "调试录制功能"
    }
    
    try:
        print(f"   发送数据: {json.dumps(start_data, ensure_ascii=False)}")
        response = requests.post(
            f"{base_url}/api/recording/start", 
            json=start_data,
            timeout=30  # 增加超时时间
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        print(f"   响应内容: {response.text}")
        
        if response.status_code != 200:
            print(f"   ❌ 请求失败")
            try:
                error_detail = response.json()
                print(f"   错误详情: {json.dumps(error_detail, ensure_ascii=False, indent=2)}")
            except:
                print(f"   原始响应: {response.text}")
        else:
            print(f"   ✅ 请求成功")
            
    except requests.exceptions.Timeout:
        print(f"   ❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ 连接错误")
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        print(f"   异常详情: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_recording() 