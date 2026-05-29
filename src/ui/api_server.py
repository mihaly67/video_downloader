from aiohttp import web
import json
import logging
from urllib.parse import urlparse
import os

logger = logging.getLogger(__name__)

class LocalExtensionServer:
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.app = web.Application(middlewares=[self.cors_middleware])
        self.app.router.add_post('/api/add_stream', self.handle_add_stream)
        self.runner = None
        self.site = None

    @web.middleware
    async def cors_middleware(self, request, handler):
        # Enable CORS for the Chrome Extension
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    async def handle_add_stream(self, request):
        if request.method == 'OPTIONS':
            return web.Response(status=200)

        try:
            data = await request.json()
            url = data.get('url')
            manifest_type = data.get('manifestType', 'Link')
            cookies_str = data.get('cookies_str')
            page_url = data.get('pageUrl', '')
            user_agent = data.get('userAgent', '')

            logger.info(f"Új stream/link érkezett az Extensionből: {url} (Típus: {manifest_type})")

            # Netscape cookies.txt generálása a yt-dlp-nek
            if cookies_str and page_url:
                self._save_netscape_cookies(cookies_str, page_url)

            headers = {}
            if user_agent:
                headers['User-Agent'] = user_agent
            if page_url:
                headers['Referer'] = page_url

            # Bepusholjuk a queue-ba
            if url:
                await self.queue_manager.add_task(url, headers=headers)
                return web.json_response({'status': 'success', 'message': 'Hozzáadva a letöltési sorhoz.'})
            else:
                return web.json_response({'status': 'error', 'message': 'Nincs URL.'}, status=400)
        except Exception as e:
            logger.error(f"Hiba az API szerverben: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    def _save_netscape_cookies(self, raw_cookie_str, page_url):
        domain = ""
        try:
            if page_url:
                parsed_domain = urlparse(page_url).netloc
                if parsed_domain:
                    # Strip www. and prepend dot for broader matching
                    domain = "." + parsed_domain.replace("www.", "")
        except Exception:
            pass

        if not domain:
            logger.warning("Nem sikerült kinyerni a domaint, a sütik nem kerülnek mentésre.")
            return

        try:
            # Csak akkor írjuk felül, ha van érvényes domainünk
            with open("cookies.txt", "w") as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
                f.write("# This is a generated file! Do not edit.\n\n")

                pairs = raw_cookie_str.split(';')
                for p in pairs:
                    if '=' in p:
                        name, val = p.split('=', 1)
                        name = name.strip()
                        val = val.strip()
                        if name and val:
                            f.write(f"{domain}\tTRUE\t/\tTRUE\t2000000000\t{name}\t{val}\n")
            logger.info(f"Cookies.txt frissítve az Extension alapján (Domain: {domain}).")
        except Exception as e:
            logger.error(f"Sütik mentése sikertelen: {e}")

    async def start(self, host='127.0.0.1', port=8000):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, host, port)
        await self.site.start()
        logger.info(f"Lokális Extension API Szerver fut: http://{host}:{port}/")

    async def stop(self):
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
