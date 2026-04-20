import asyncio
import json
import logging
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Request, Response, Route

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class VideoSniffer:
    """
    Playwright based network sniffer.
    Intercepts m3u8, mp4, ts streams and records authentication headers.
    """
    def __init__(self, output_file: str = "session_config.json"):
        self.output_file = output_file
        self.found_streams = []
        self.session_headers = {}

    async def _handle_route(self, route: Route):
        """
        Intercept requests. We can log the URL and abort large media downloads to prevent OOM,
        but we need to let m3u8 playlists through to parse them.
        """
        request = route.request
        url = request.url

        if ".m3u8" in url or ".mp4" in url or ".ts" in url:
            logger.info(f"Stream URL found (Request): {url}")
            if url not in self.found_streams:
                self.found_streams.append(url)

            # Extract headers
            headers = request.headers
            self.session_headers = {
                "User-Agent": headers.get("user-agent", ""),
                "Referer": headers.get("referer", ""),
                "Cookie": headers.get("cookie", "")
            }

            # To prevent downloading large media files and causing OOM,
            # we can abort .ts and .mp4 files after capturing their URL.
            # .m3u8 files are text and small, so we let them through.
            if ".ts" in url or ".mp4" in url:
                await route.abort()
                return

        await route.continue_()

    async def _inject_play_buttons(self, page: Page):
        """
        Attempt to click video elements or play buttons to trigger streams.
        """
        try:
            await page.evaluate("""() => {
                const videos = document.querySelectorAll('video');
                videos.forEach(v => {
                    try { v.play(); } catch(e) {}
                });
            }""")
        except Exception as e:
            logger.debug(f"Error injecting play buttons: {e}")

    async def sniff(self, url: str, timeout: int = 15000) -> Optional[Dict[str, Any]]:
        """
        Open the URL in Headless Playwright and sniff network for a specific duration.
        """
        logger.info(f"Starting sniffing on: {url}")
        self.found_streams = []
        self.session_headers = {}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            # intercept requests
            await page.route("**/*", self._handle_route)

            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout)
                await self._inject_play_buttons(page)
                # Wait a bit for streams to load
                await page.wait_for_timeout(5000)
            except Exception as e:
                logger.warning(f"Navigation/Timeout issue (often normal for video sites): {e}")
            finally:
                await browser.close()

        if self.found_streams:
            result = {
                "streams": self.found_streams,
                "headers": self.session_headers
            }

            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4)

            logger.info(f"Sniffing successful. Results saved to: {self.output_file}")
            return result
        else:
            logger.warning("No m3u8/mp4/ts streams found on the network.")
            return None

if __name__ == "__main__":
    async def test():
        sniffer = VideoSniffer()
        # Test with a lightweight page that embeds a video or similar
        # Using a dummy URL for now to show it runs safely
        result = await sniffer.sniff("https://test-videos.co.uk/")
        print(json.dumps(result, indent=2))
    asyncio.run(test())
