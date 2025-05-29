#!/usr/bin/env python3
import requests
import time

def test_api():
    """测试API是否正常运行"""
    try:
        print("测试API连接...")
        response = requests.get('http://127.0.0.1:8000/api/status', timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ API正常运行")
            return True
        else:
            print("❌ API响应异常")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保应用已启动")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_api() 