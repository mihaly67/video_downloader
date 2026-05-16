import asyncio
import logging
import sys
import os
import flet as ft

# Hozzáadjuk a projekt gyökerét a path-hoz, hogy a src modulokat megtalálja
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.queue_manager.queue import DownloadQueueManager
from src.ui.flet_app import VideoDownloaderApp
from src.ui.api_server import LocalExtensionServer

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


async def flet_main(page: ft.Page):
    logger.info("Flet UI inicializálása...")

    # 1. Queue Manager létrehozása (Ez végzi a szálkezelést és letöltést)
    # Ahhoz, hogy a main threaden frissítsünk, a progress_callback-t később rendeljük hozzá,
    # de a Queue manager eleve async-safe módon (call_soon_threadsafe) hívja.

    app_state = {}

    def on_progress(event):
        if "app_instance" in app_state:
            app_state["app_instance"].handle_progress(event)

    queue_manager = DownloadQueueManager(ui_callback=on_progress, max_concurrent=3)

    # 2. Local API Szerver elindítása a Chrome Extension hívásokhoz
    api_server = LocalExtensionServer(queue_manager)
    await api_server.start(host="127.0.0.1", port=8000)

    # 3. Flet UI app összekötése
    app_instance = VideoDownloaderApp(page, queue_manager)
    app_state["app_instance"] = app_instance

    logger.info("Jules Video Downloader sikeresen elindult!")

    # Amikor az ablak bezárul
    def on_window_event(e):
        if e.data == "close":
            logger.info("Ablak bezárása, háttérfolyamatok leállítása...")
            page.window_prevent_close = False
            asyncio.create_task(api_server.stop())
            asyncio.create_task(queue_manager.shutdown())
            page.window_close()

    page.window_prevent_close = True
    page.on_window_event = on_window_event


def main():
    # A flet.run maga létrehoz egy asyncio event loopot, ezért a main logicot flet_main formában adjuk át
    ft.run(main=flet_main)


if __name__ == "__main__":
    main()
