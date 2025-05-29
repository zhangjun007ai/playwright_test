import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect


async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://www.baidu.com/")
    await page.goto("https://baike.baidu.com/item/%E6%B1%9F%E8%8B%8F%E7%9C%81%E5%9F%8E%E5%B8%82%E8%B6%B3%E7%90%83%E8%81%94%E8%B5%9B/65674721?fr=api_baidu_opex_festival#")
    await page.goto("chrome-error://chromewebdata/")
    await page.goto("https://playwright.dev/")
    await page.goto("https://playwright.dev/docs/intro")

    # ---------------------
    await context.close()
    await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())