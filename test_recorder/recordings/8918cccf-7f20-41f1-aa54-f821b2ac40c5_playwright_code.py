import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect


async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("http://192.168.1.128/login")
    await page.get_by_text("登录").click()
    await page.goto("http://192.168.1.128/index")
    await page.get_by_text("系统管理").click()
    await page.get_by_text("角色管理").click()
    await page.locator("unknown").click()
    await page.locator("#remark").click()
    await page.locator("#roleName").click()
    await page.locator("#roleSort").click()
    await page.locator("#roleKey").click()
    await page.get_by_text("关闭").click()
    await page.get_by_text("参数设置").click()
    await page.locator("[type="text"]").click()
    await page.locator("[type="text"]").click()
    await page.get_by_placeholder("开始时间").click()
    await page.locator("[type="text"]").click()
    await page.get_by_text("系统监控").click()
    await page.get_by_text("定时任务").click()
    await page.get_by_text("新增").click()
    await page.locator("#jobName").click()
    await page.locator("#invokeTarget").click()
    await page.locator("#cronExpression").click()
    await page.locator("#remark").click()
    await page.locator("#jobName").click()
    await page.locator("#invokeTarget").click()
    await page.get_by_text("关闭").click()
    await page.get_by_text("服务监控").click()
    await page.get_by_text("数据监控").click()
    await page.get_by_text("在线用户").click()
    await page.get_by_text("定时任务").click()
    await page.get_by_text("新增").click()
    await page.locator("#jobName").click()
    await page.locator("#jobName").fill("")
    await page.locator("#invokeTarget").click()
    await page.locator("unknown").click()
    await page.locator("unknown").click()
    await page.locator("unknown").click()
    await page.locator("unknown").click()
    await page.locator("unknown").click()
    await page.get_by_text("新增").click()
    await page.get_by_text("任务名称：").click()

    # ---------------------
    await context.close()
    await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())