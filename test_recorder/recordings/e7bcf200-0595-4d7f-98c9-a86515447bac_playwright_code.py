import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect


async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("http://192.168.1.128/login")
    await page.get_by_placeholder("用户名").fill()
    await page.get_by_placeholder("用户名").fill("")
    await page.get_by_placeholder("用户名").fill("admin")
    await page.get_by_role("button", name="登录").click()
    await page.goto("http://192.168.1.128/index")
    await page.get_by_role("link", name="系统监控").click()
    await page.get_by_role("link", name="在线用户").click()
    await page.locator("input[type="text"]").fill()
    await page.locator("input[type="text"]").fill("192.168.1.126")
    await page.locator("input[type="text"]").fill("192.168.1.126")
    await page.locator(".fa").fill()
    await page.get_by_role("link", name="2601f5aa-64ba-49ad-9...").click()
    await page.get_by_role("navigation", name="系统管理").click()
    await page.get_by_role("link", name="角色管理").click()
    await page.get_by_role("link", name="新增").click()
    await page.locator("#roleName").fill()
    await page.locator("#roleName").fill("我")
    await page.locator("#roleName").fill("我")
    await page.locator("#roleKey").fill()
    await page.locator("#roleKey").fill("1")
    await page.locator(".iCheck-helper").click()
    await page.locator(".iCheck-helper").click()
    await page.locator("#roleKey").fill("1")
    await page.locator("#menuTrees_1_check").click()
    await page.locator("#menuTrees_1_switch").click()
    await page.locator("#menuTrees_85_check").click()
    await page.locator("#menuTrees_89_switch").click()
    await page.get_by_text("测试 @qwd").click()
    await page.locator("#menuTrees_90_check").click()
    await page.locator(".iCheck-helper").click()
    await page.locator(".iCheck-helper").click()
    await page.get_by_text("全选/全不选").click()
    await page.get_by_text("全选/全不选").click()
    await page.locator("#menuTrees_13_check").click()
    await page.get_by_text("system:role:edit").click()
    await page.get_by_text("角色修改 system:role:edit").click()

    # ---------------------
    await context.close()
    await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())