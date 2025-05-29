#!/usr/bin/env python3
"""
简单的Playwright测试脚本
用于验证Windows环境下的兼容性
"""

import asyncio
import platform
import sys
from pathlib import Path

# Windows环境下设置事件循环策略
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright

async def test_playwright():
    """测试Playwright基本功能"""
    print(f"操作系统: {platform.system()}")
    print(f"Python版本: {sys.version}")
    
    try:
        print("正在启动Playwright...")
        async with async_playwright() as p:
            print("Playwright启动成功")
            
            # 启动浏览器
            print("正在启动Chromium浏览器...")
            browser = await p.chromium.launch(
                headless=False,  # 显示浏览器窗口
                slow_mo=100
            )
            print("浏览器启动成功")
            
            # 创建页面
            print("正在创建页面...")
            page = await browser.new_page()
            print("页面创建成功")
            
            # 访问测试页面
            print("正在访问测试页面...")
            await page.goto("https://www.baidu.com")
            print("页面访问成功")
            
            # 获取页面标题
            title = await page.title()
            print(f"页面标题: {title}")
            
            # 等待几秒
            await asyncio.sleep(3)
            
            # 关闭浏览器
            await browser.close()
            print("浏览器关闭成功")
            
        print("✅ Playwright测试完成，一切正常！")
        return True
        
    except Exception as e:
        print(f"❌ Playwright测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_playwright())
    if result:
        print("\n🎉 您的环境支持Playwright录制功能！")
    else:
        print("\n⚠️ 需要进一步配置Playwright环境") 