import asyncio
import logging
from src.sniffer.playwright_sniffer import VideoSniffer
from src.core.queue_manager.queue import DownloadQueueManager
from src.processor.media_merger import MediaMerger

logger = logging.getLogger(__name__)

class MainController:
    """
    Központi vezérlő osztály, amely összeköti a Sniffert, a Letöltőt és a Feldolgozót.
    """
    def __init__(self, ui_callback=None, max_concurrent_downloads=2):
        self.ui_callback = ui_callback
        self.sniffer = VideoSniffer()
        self.queue_manager = DownloadQueueManager(ui_callback=self._handle_download_event, max_concurrent=max_concurrent_downloads)
        self.media_merger = MediaMerger()

    def _handle_download_event(self, event):
        """
        A letöltő által küldött események (haladás, hiba, befejezés) feldolgozása.
        Ezeket továbbítja a UI-nak.
        """
        if self.ui_callback:
            self.ui_callback(event)

        if event.get('status') == 'finished':
             # Itt lehetne elindítani a post-processinget (pl. TS to MP4)
             # filename = event.get('filename')
             # if filename and filename.endswith('.ts'):
             #     self.media_merger.convert_ts_to_mp4(filename, filename.replace('.ts', '.mp4'))
             pass

    async def add_download_task(self, url: str):
        """
        Egy új letöltési feladat indítása.
        1. Sniffing a stream URL-ért és a headerekért.
        2. Hozzáadás a letöltési sorhoz.
        """
        logger.info(f"Új feladat hozzáadása: {url}")

        # 1. Lépés: Sniffing
        if self.ui_callback:
             self.ui_callback({'status': 'sniffing', 'url': url})

        sniff_result = await self.sniffer.sniff(url)

        if sniff_result and sniff_result.get('streams'):
            # 2. Lépés: A legelső talált stream hozzáadása a sorhoz
            stream_url = sniff_result['streams'][0]
            headers = sniff_result.get('headers', {})

            if self.ui_callback:
                 self.ui_callback({'status': 'added_to_queue', 'url': stream_url})

            await self.queue_manager.add_task(stream_url, headers)
        else:
            logger.error(f"Nem található stream a megadott URL-en: {url}")
            if self.ui_callback:
                 self.ui_callback({'status': 'error', 'error': 'Nem található stream a megadott URL-en.'})

    async def shutdown(self):
        """
        Leállítja a letöltési sort.
        """
        await self.queue_manager.shutdown()
