import yt_dlp
import logging
from typing import Dict, Any, Callable, Optional
import os

logger = logging.getLogger(__name__)

class VideoDownloader:
    """
    Ez az osztály felelős a letöltés lebonyolításáért és az események (Progress hook)
    közvetítéséért a Queue Manager és a Flet UI felé.
    """
    def __init__(self, ui_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        :param ui_callback: Egy aszinkron vagy szinkron callback függvény, amely
                            a progress eventeket továbbítja a Flet felé.
        """
        self.ui_callback = ui_callback
        self.ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [self._progress_hook],
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
        }

    def update_session_headers(self, headers: Dict[str, str], cookies: Dict[str, str] = None) -> None:
        """
        Session injector: a Sniffer által generált fejlécek beállítása.
        """
        http_headers = {}
        if headers.get('User-Agent'):
            http_headers['User-Agent'] = headers.get('User-Agent')
        if headers.get('Referer'):
            http_headers['Referer'] = headers.get('Referer')
        if headers.get('Cookie'):
            http_headers['Cookie'] = headers.get('Cookie')

        if http_headers:
            self.ydl_opts['http_headers'] = http_headers
            logger.info("Session headers frissítve a yt-dlp számára.")

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """
        Ezt hívja meg a yt-dlp a letöltés közben. Itt generáljuk az egyedi Event-et.
        """
        status = d.get('status')
        event = {'status': status}

        if status == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            percent = (downloaded / total_bytes) * 100 if total_bytes else 0

            event.update({
                'percent': percent,
                'speed': speed,
                'eta': eta,
                'filename': d.get('filename'),
                'downloaded_bytes': downloaded,
                'total_bytes': total_bytes
            })
        elif status == 'finished':
            event.update({
                'filename': d.get('filename'),
                'percent': 100,
                'total_bytes': d.get('total_bytes', 0)
            })
        elif status == 'error':
            event.update({
                'error': d.get('error')
            })

        if self.ui_callback:
            # Csak átdobjuk a dict-et, a queue/UI majd eldönti, hogy aszinkron módon hogy futtatja.
            self.ui_callback(event)

    def download(self, url: str) -> bool:
        """
        A letöltés indítása. Vigyázat, ez blokkoló hívás!
        Ezt az asyncio loopból kell egy to_thread-el hívni.
        """
        logger.info(f"Letöltés indítása: {url}")
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                try:
                    res = ydl.extract_info(url, download=True)
                    return True
                except Exception as inner_e:
                    logger.error(f"Hiba a letöltés során: {inner_e}")
                    if self.ui_callback:
                        self.ui_callback({'status': 'error', 'error': str(inner_e)})
                    return False
        except Exception as e:
            logger.error(f"Hiba az ydl inicializálásakor: {e}")
            if self.ui_callback:
                self.ui_callback({'status': 'error', 'error': str(e)})
            return False
