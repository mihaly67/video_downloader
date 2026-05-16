import flet as ft
import asyncio
from typing import Dict, Any


class VideoDownloaderApp:
    def __init__(self, page: ft.Page, queue_manager):
        self.page = page
        self.queue_manager = queue_manager

        self.page.title = "Jules Video Downloader"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        self.page.window_width = 800
        self.page.window_height = 600

        # UI elemek inicializálása
        self.url_input = ft.TextField(
            label="Videó vagy m3u8 URL beillesztése",
            expand=True,
            border_color=ft.Colors.BLUE_400,
        )
        self.download_btn = ft.ElevatedButton(
            "Letöltés hozzáadása",
            icon=ft.Icons.DOWNLOAD,
            on_click=self.on_download_clicked,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )

        # Extension figyelmezteto sav
        self.extension_status = ft.Text(
            "Chrome Kiegészítő (Jules Sniffer) integráció aktív: várjuk az URL-eket a böngészőből...",
            color=ft.Colors.GREEN_400,
            italic=True,
        )

        self.downloads_list = ft.ListView(expand=True, spacing=10, auto_scroll=True)

        # Itt tároljuk a sorokat az aktuális fájlnevek alapján
        self.progress_rows = {}

        self.setup_ui()

    def setup_ui(self):
        # Fejléc
        header = ft.Row(
            [
                ft.Icon(ft.Icons.VIDEO_LIBRARY, size=40, color=ft.Colors.BLUE_400),
                ft.Text("Jules Downloader", size=30, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Bemeneti sor
        input_row = ft.Row([self.url_input, self.download_btn])

        self.page.add(
            header,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            input_row,
            self.extension_status,
            ft.Divider(height=20, color=ft.Colors.GREY_800),
            ft.Text("Letöltések:", size=20, weight=ft.FontWeight.BOLD),
            self.downloads_list,
        )

    async def on_download_clicked(self, e):
        url = self.url_input.value.strip()
        if not url:
            return

        self.url_input.value = ""
        self.page.update()

        # A valós letöltést a Queue Manager végzi a háttérben
        await self.queue_manager.add_task(url)

    def handle_progress(self, event: Dict[str, Any]):
        """
        Ezt a metódust hívja meg a Queue Manager a fő Event Loop-on (UI thread) belül.
        """
        filename = event.get("filename")
        if not filename:
            return

        status = event.get("status")

        # Ha a fájl még nincs a listában, adjuk hozzá
        if filename not in self.progress_rows:
            pb = ft.ProgressBar(value=0.0, expand=True, color=ft.Colors.BLUE_400)
            status_text = ft.Text(
                "Indítás...", width=150, text_align=ft.TextAlign.RIGHT
            )

            row = ft.Row(
                [
                    ft.Text(filename[-50:], expand=True, tooltip=filename),
                    pb,
                    status_text,
                ]
            )
            self.progress_rows[filename] = {
                "row": row,
                "pb": pb,
                "status_text": status_text,
            }
            self.downloads_list.controls.append(row)
            self.page.update()

        # UI elemek frissítése
        ui_elements = self.progress_rows[filename]

        if status == "downloading":
            percent = event.get("percent", 0.0)
            speed = event.get("speed", 0) or 0
            speed_mb = speed / (1024 * 1024)

            ui_elements["pb"].value = percent / 100.0
            ui_elements["status_text"].value = f"{percent:.1f}% ({speed_mb:.1f} MB/s)"
            ui_elements["status_text"].color = ft.Colors.WHITE

        elif status == "finished":
            ui_elements["pb"].value = 1.0
            ui_elements["pb"].color = ft.Colors.GREEN_400
            ui_elements["status_text"].value = "Befejezve!"
            ui_elements["status_text"].color = ft.Colors.GREEN_400

        elif status == "error":
            error_msg = event.get("error", "Ismeretlen hiba")
            ui_elements["pb"].color = ft.Colors.RED_400
            ui_elements["status_text"].value = "Hiba!"
            ui_elements["status_text"].color = ft.Colors.RED_400
            ui_elements["row"].controls[0].tooltip = error_msg

        self.page.update()
