import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        st = stealth.Stealth()
        await st.apply_stealth_async(page)

        await page.route("**/*", lambda route: route.continue_())

        m3u8_url = None
        def handle_response(response):
            nonlocal m3u8_url
            if ".m3u8" in response.url:
                print(f"Found m3u8: {response.url}")
                m3u8_url = response.url

        page.on("response", handle_response)

        try:
            await page.goto("https://uqload.to/embed-kiv51v2a00q6.html", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Error: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
