import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect


async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://www.baidu.com/")
    await page.locator("#kw").click()
    await page.locator("#kw").fill("")
    await page.locator("#kw").fill("")
    await page.locator("#kw").fill("")
    await page.locator("#kw").fill("")
    await page.locator("#kw").fill("")
    await page.locator("#su").click()
    await page.goto("https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&tn=baidu&wd=zhang&fenlei=256&rsv_pq=0x875fdca20007a96e&rsv_t=80b2uFhEZBVtbel5lBk3X8liyTQQGi%2FlnHQD0hmPJd5g4SJX6U61pFHk7aRR&rqlang=en&rsv_enter=1&rsv_dl=tb&rsv_sug3=6&rsv_sug1=4&rsv_sug7=100&rsv_sug2=0&rsv_btype=i&prefixsug=zhang&rsp=5&inputT=996&rsv_sug4=2902")
    await page.goto("http://192.168.1.128/login")
    await page.get_by_text("登录").click()
    await page.goto("http://192.168.1.128/index")
    await page.get_by_text("系统管理").click()
    await page.locator("unknown").click()
    await page.get_by_text("角色管理").click()
    await page.locator("[type="text"]").click()
    await page.locator("[type="text"]").fill("")
    await page.get_by_text("角色名称：").click()
    await page.locator("#startTime").click()
    await page.get_by_text("29").click()
    await page.locator("#endTime").click()
    await page.get_by_text("30").click()

    # ---------------------
    await context.close()
    await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())