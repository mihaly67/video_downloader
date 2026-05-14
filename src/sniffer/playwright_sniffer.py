import asyncio
import json
import logging
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Request

logger = logging.getLogger(__name__)

try:
    from playwright_stealth import stealth
except ImportError:
    stealth = None
    logger.warning("playwright_stealth nem található. A lopakodó mód kikapcsolva.")


class VideoSniffer:
    """
    Playwright Stealth alapú hálózati forgalom elemző.
    Célja: m3u8 és mpd linkek kinyerése, valamint az azokat hitelesítő
    fejlécek (Cookie, User-Agent, Referer) rögzítése.
    """
    def __init__(self, output_file: str = "session_config.json"):
        self.output_file = output_file
        self.found_streams = []
        self.session_headers = {}

    async def _handle_request(self, request: Request):
        """
        Minden hálózati kérésnél megvizsgáljuk, hogy videó manifesztet (m3u8/mpd) kér-e.
        Ha igen, lementjük az URL-t és a hozzátartozó hitelesítő fejléceket.
        """
        url = request.url
        if ".m3u8" in url or ".mpd" in url:
            logger.info(f"Stream URL találat: {url}")
            self.found_streams.append(url)

            # Fejlécek kinyerése a kérésből
            headers = request.headers
            self.session_headers = {
                "User-Agent": headers.get("user-agent", ""),
                "Referer": headers.get("referer", ""),
                "Cookie": headers.get("cookie", "")
            }

    async def _inject_play_buttons(self, page: Page):
        """
        A beágyazott lejátszókat és lejátszás gombokat megpróbálja megnyomni.
        Sok esetben az iframe-eken belüli stream url nem töltődik be amíg
        rá nem kattintanak a videó indítására.
        """
        try:
            # 1. próbálkozás: ha van <video> elem, kattintson rá
            videos = await page.locator("video").all()
            for video in videos:
                await video.click(force=True)
                await asyncio.sleep(1)
        except Exception as e:
            logger.debug(f"Hiba a videó kattintásakor: {e}")

        try:
            # 2. próbálkozás: iframeken belüli lejátszás gombok
            for frame in page.frames:
                try:
                    play_buttons = await frame.locator("button, [class*='play'], [id*='play']").all()
                    for btn in play_buttons:
                        if await btn.is_visible():
                            await btn.click(force=True)
                            await asyncio.sleep(1)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Hiba az iframek kezelésekor: {e}")

    async def sniff(self, url: str, timeout: int = 15000) -> Optional[Dict[str, Any]]:
        """
        Megnyitja a megadott URL-t Headless Playwright segítségével,
        és figyel a hálózaton egy adott ideig.
        """
        logger.info(f"Sniffing indítása: {url}")
        self.found_streams = []
        self.session_headers = {}

        async with async_playwright() as p:
            # Megpróbáljuk elrejteni, hogy robotok vagyunk (Stealth) - DRM stabilizálás miatt Google Chrome-al
            chrome_path = "/usr/bin/google-chrome" if __import__("os").path.exists("/usr/bin/google-chrome") else None

            launch_args = {
                "headless": True,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-component-update",  # DRM (Widevine) stabilizálása miatt
                    "--no-sandbox"
                ]
            }
            if chrome_path:
                launch_args["executable_path"] = chrome_path
                logger.info(f"Hivatalos Google Chrome használata a DRM megkerüléséhez: {chrome_path}")

            browser = await p.chromium.launch(**launch_args)

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            if stealth is not None:
                try:
                    await stealth.stealth_async(page)
                except Exception as e:
                    logger.debug(f"Hiba a stealth injektálásakor: {e}")

            # Rácsatlakozunk a hálózati forgalomra (DRM és Streamek)
            page.on("request", self._handle_request)

            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout)

                # YouTube Cookie handling bypass
                if "youtube.com" in url or "youtu.be" in url:
                    logger.info("YouTube detektálva. Megpróbáljuk elfogadni a sütiket és letölteni a Netscape cookies formatumot yt-dlp-hez.")
                    try:
                        # Reject all vagy Accept all gomb keresése a consent oldalon
                        consent_btn = await page.query_selector("button[aria-label='Reject all']")
                        if consent_btn:
                            await consent_btn.click()
                        else:
                            consent_btn = await page.query_selector("button[aria-label='Accept all']")
                            if consent_btn:
                                await consent_btn.click()
                        await page.wait_for_timeout(3000)
                    except Exception as cookie_e:
                        logger.debug(f"Cookie gomb hiba: {cookie_e}")

                    # Youtube esetén a Playwright sniffer átadja a cookie-kat a 'cookies.txt'-be Netscape formátumban
                    cookies = await context.cookies()
                    cookie_str = ""
                    for c in cookies:
                        domain = c['domain']
                        include_subdomains = "TRUE" if domain.startswith('.') else "FALSE"
                        path = c['path']
                        secure = "TRUE" if c['secure'] else "FALSE"
                        expires = str(int(c.get('expires', 0)))
                        name = c['name']
                        value = c['value']
                        cookie_str += f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n"

                    # Szövegfájlba mentés a yt-dlp számára
                    with open("cookies.txt", "w") as f:
                        f.write("# Netscape HTTP Cookie File\n")
                        f.write(cookie_str)
                    logger.info("Netscape cookies.txt legenerálva a yt-dlp számára.")

                # Megpróbáljuk elindítani a videót ha nem indult el automatikusan
                await self._inject_play_buttons(page)
                # Várunk egy kicsit pluszban, hátha késleltetve töltődik be a videó
                await page.wait_for_timeout(5000)
            except Exception as e:
                logger.warning(f"Navigációs hiba vagy timeout (ez normális lehet videó oldalaknál): {e}")
            finally:
                await browser.close()

        result = {
            "streams": self.found_streams,
            "headers": self.session_headers
        }

        if self.found_streams or ("youtube.com" in url or "youtu.be" in url):
            # Eredmény mentése JSON-be (ez lesz a "Session Injector" forrása)
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4)

            logger.info(f"Sniffing befejezve. Eredmények mentve: {self.output_file}")
            return result
        else:
            logger.warning("Nem találtunk m3u8 vagy mpd streamet a hálózaton.")
            return None
