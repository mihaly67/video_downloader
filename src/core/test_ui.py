import flet as ft
import asyncio
from src.core.queue_manager.queue import DownloadQueueManager

def main(page: ft.Page):
    page.title = "Video Downloader Test UI"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    url_input = ft.TextField(label="YouTube/Videa URL", width=400)
    progress_bar = ft.ProgressBar(width=400, value=0)
    status_text = ft.Text("Állapot: Készen áll")

    # Inicializáljuk a Queue Managert a UI update callbackkel
    def ui_update_callback(event):
        status = event.get('status')
        if status == 'downloading':
            percent = event.get('percent', 0)
            progress_bar.value = percent / 100.0
            status_text.value = f"Letöltés... {percent:.2f}% | Sebesség: {event.get('speed', 0)} bytes/s"
        elif status == 'finished':
            progress_bar.value = 1.0
            status_text.value = f"Letöltés befejezve: {event.get('filename')}"
        elif status == 'error':
            status_text.value = f"Hiba: {event.get('error')}"
        page.update()

    # Vigyázat: A Queue manager asyncio loopot igényel, ezért futtatás előtt be kell tölteni a Flet Async módjában.
    queue_manager = None

    async def btn_click(e):
        nonlocal queue_manager
        if queue_manager is None:
            queue_manager = DownloadQueueManager(ui_callback=ui_update_callback)

        if url_input.value:
            status_text.value = "Hozzáadva a sorhoz..."
            progress_bar.value = None # Indeterminate
            page.update()
            await queue_manager.add_task(url_input.value)

    start_btn = ft.ElevatedButton("Letöltés indítása", on_click=btn_click)

    page.add(url_input, start_btn, progress_bar, status_text)

if __name__ == "__main__":
    import threading
    ft.run(target=main)
