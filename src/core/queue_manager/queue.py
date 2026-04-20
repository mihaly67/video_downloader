import asyncio
import logging
from typing import Dict, Any, Callable
from src.core.downloader import VideoDownloader

logger = logging.getLogger(__name__)

class DownloadQueueManager:
    """
    Kezeli a letöltési feladatokat (sorba állít, és a háttérben futtat),
    biztosítva az aszinkron kommunikációt a szinkron yt-dlp és a Flet Event Loop között.
    """
    def __init__(self, ui_callback: Callable[[Dict[str, Any]], None], max_concurrent: int = 2):
        """
        :param ui_callback: Ezt a callback-et hívja meg minden progress eseménynél (async módban fut a main thread-en).
        """
        self.ui_callback = ui_callback
        self.max_concurrent = max_concurrent
        self.queue: asyncio.Queue[dict] = asyncio.Queue()
        self.loop = asyncio.get_running_loop()

        # A háttér worker-ek listája
        self.workers = []
        for i in range(max_concurrent):
            task = asyncio.create_task(self._worker(i))
            self.workers.append(task)

    def enqueue_progress(self, event: Dict[str, Any]):
        """
        Ezt hívja meg a VideoDownloader szinkron callbackje (worker thread-ből).
        Biztonságosan betesszük a main loop-ba a UI callback futtatását.
        """
        # A Flet update()-et és a state módosításokat a main thread-en (loop-ban) kell végrehajtani
        self.loop.call_soon_threadsafe(self.ui_callback, event)

    async def _worker(self, worker_id: int):
        """
        A worker folyamatosan vár a queue-ból kapott URL-ekre és letölti őket to_thread() segítségével.
        """
        logger.info(f"[Worker {worker_id}] Elindult.")
        while True:
            task = await self.queue.get()
            url = task.get("url")
            headers = task.get("headers", {})

            logger.info(f"[Worker {worker_id}] Új feladat kapva: {url}")

            try:
                # Inicializáljuk a downloadert az aktuális callback-el
                downloader = VideoDownloader(ui_callback=self.enqueue_progress)

                # Ha vannak egyedi fejlécek, hozzáadjuk (Session Injection)
                if headers:
                    downloader.update_session_headers(headers)

                # Futtatjuk a blokkoló letöltést egy külön szálon (Thread pool)
                success = await asyncio.to_thread(downloader.download, url)

                if not success:
                    logger.error(f"[Worker {worker_id}] Letöltés sikertelen: {url}")
            except asyncio.CancelledError:
                logger.info(f"[Worker {worker_id}] Leállítva.")
                break
            except Exception as e:
                logger.error(f"[Worker {worker_id}] Kivétel a feladat közben: {e}")
            finally:
                self.queue.task_done()

    async def add_task(self, url: str, headers: Dict[str, str] = None):
        """
        Új letöltési feladat hozzáadása a sorhoz.
        """
        task = {"url": url, "headers": headers or {}}
        await self.queue.put(task)
        logger.info(f"Feladat hozzáadva a sorhoz: {url}")

    async def shutdown(self):
        """
        Worker-ek leállítása.
        """
        logger.info("Letöltési sor leállítása...")
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
