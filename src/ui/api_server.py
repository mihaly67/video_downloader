from aiohttp import web
import json
import logging

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
            manifest_type = data.get('manifestType')
            cookies_str = data.get('cookies_str')

            logger.info(f"Új stream érkezett az Extensionből: {url} (Típus: {manifest_type})")

            # Netscape cookies.txt generálása a yt-dlp-nek, ha kaptunk
            if cookies_str:
                self._save_netscape_cookies(cookies_str)

            # Bepusholjuk a queue-ba
            if url:
                await self.queue_manager.add_task(url)
                return web.json_response({'status': 'success', 'message': 'Hozzáadva a letöltési sorhoz.'})
            else:
                return web.json_response({'status': 'error', 'message': 'Nincs URL.'}, status=400)
        except Exception as e:
            logger.error(f"Hiba az API szerverben: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    def _save_netscape_cookies(self, raw_cookie_str):
        # Egyszerű HTTP cookie string (név=érték; név=érték) konvertálása és mentése
        # Bár a yt-dlp a Netscape formátumot szereti, gyakran egy egyszerű --cookies fájlt is elfogad ha jól formázott.
        # Itt egy dummy Netscape formátumot generálunk a lehallgatott kulcs-értékekből a YouTube miatt.
        try:
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
                        # Dummy YouTube entry
                        f.write(f".youtube.com\\tTRUE\\t/\\tTRUE\\t2000000000\\t{name}\\t{val}\n")
            logger.info("Cookies.txt frissítve az Extension alapján.")
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
