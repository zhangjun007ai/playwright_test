import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect


async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("http://192.168.1.128/login")
    await page.get_by_role("button", name="登录").click()
    await page.goto("http://192.168.1.128/index")
    await page.get_by_role("link", name="系统监控").click()
    await page.get_by_role("link", name="在线用户").click()
    await page.get_by_role("link", name="定时任务").click()
    await page.locator(".fa").click()
    await page.get_by_role("link", name="关闭").click()
    await page.get_by_role("link", name="新增").click()
    await page.locator("#jobName").fill()
    await page.locator("#jobName").fill()
    await page.locator("#jobName").fill("条欧式")

    # ---------------------
    await context.close()
    await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())