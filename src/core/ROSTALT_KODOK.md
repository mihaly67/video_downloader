# 🔬 ROSTÁLT (KIVÁLOGATOTT) KÓDOK A CORE-HOZ (Transzplantációs Bázis)

Ezek a fájlok képezik az alapot a `downloader.py` és a `queue_manager/` megírásához, miután a RAG-ból kiszűrtük a több ezer irreleváns fájlt.

## 📄 Fájl: `flet-main/sdk/python/examples/community/mind_queue/main.py`
- **Repó:** `flet-main`
- **Fontos Importok:**
  - `import asyncio`
  - `import flet as ft`
- **Globális Függvény:** `load_data()`
- **Globális Függvény:** `save_data(data)`
- **Globális Függvény:** `main(page: ft.Page)`
- **Globális Függvény:** `handle_keyboard_event(e: ft.KeyboardEvent)`
- **Globális Függvény:** `confirm_delete_system(system_name: str)`
- **Globális Függvény:** `do_delete(ev)`
- **Globális Függvény:** `do_cancel(ev)`
- **Globális Függvény:** `close_current_dialog()`
- **Globális Függvény:** `open_dialog(dialog: ft.AlertDialog)`
- **Globális Függvény:** `clone_system(system_name: str)`
- **Globális Függvény:** `delete_system(system_name: str)`
- **Globális Függvény:** `show_dashboard(e=None)`
- **Globális Függvény:** `open_system(system_name: str)`
- **Globális Függvény:** `open_system_actions(system_name: str)`
- **Globális Függvény:** `do_open(e)`
- **Globális Függvény:** `open_add_system_dialog(e)`
- **Globális Függvény:** `on_add(ev)`
- **Globális Függvény:** `show_system(system_name: str)`
- **Globális Függvény:** `edit_system_name()`
- **Globális Függvény:** `on_save(ev)`
- **Globális Függvény:** `clone_task(header: str, index: int)`
- **Globális Függvény:** `toggle_task(header: str, index: int, value: bool)`
- **Globális Függvény:** `delete_task(header: str, index: int)`
- **Globális Függvény:** `edit_task(header: str, index: int)`
- **Globális Függvény:** `on_save(ev)`
- **Globális Függvény:** `move_task(header: str, index: int, direction: int)`
- **Globális Függvény:** `open_task_actions(header: str, index: int)`
- **Globális Függvény:** `do_clone(ev)`
- **Globális Függvény:** `do_move_up(ev)`
- **Globális Függvény:** `do_move_down(ev)`
- **Globális Függvény:** `do_edit(ev)`
- **Globális Függvény:** `do_delete(ev)`
- **Globális Függvény:** `do_cancel(ev)`
- **Globális Függvény:** `add_task(header: str)`
- **Globális Függvény:** `on_add(ev)`
- **Globális Függvény:** `delete_header(header: str)`
- **Globális Függvény:** `edit_header(header: str)`
- **Globális Függvény:** `on_save(ev)`
- **Globális Függvény:** `add_header()`
- **Globális Függvény:** `on_add(ev)`
- **Globális Függvény:** `confirm_delete_header(header_name: str)`
- **Globális Függvény:** `do_delete(ev)`
- **Globális Függvény:** `do_cancel(ev)`
- **Globális Függvény:** `confirm_delete_system()`
- **Globális Függvény:** `do_delete(ev)`
- **Globális Függvény:** `do_cancel(ev)`

---

## 📄 Fájl: `flet-main/sdk/python/examples/cookbook/cpu_bound_queue.py`
- **Repó:** `flet-main`
- **Fontos Importok:**
  - `import asyncio`
  - `import flet as ft`
- **Osztály:** `CpuProgressApp`
  - Metódus: `__init__(self, page: ft.Page)`

---

## 📄 Fájl: `yt-dlp-master/test/test_downloader_http.py`
- **Repó:** `yt-dlp-master`
- **Fontos Importok:**
  - `from yt_dlp import YoutubeDL`
  - `from yt_dlp.downloader.http import HttpFD`
  - `from yt_dlp.utils._utils import _YDLLogger as FakeLogger`
- **Osztály:** `HTTPTestRequestHandler`
- **Osztály:** `TestHttpFD`
  - Metódus: `download(self, params, ep)`

---

## 📄 Fájl: `yt-dlp-master/yt_dlp/downloader/http.py`
- **Repó:** `yt-dlp-master`
- **Osztály:** `HttpFD`
- **Osztály:** `DownloadContext`
- **Osztály:** `SucceedDownload`
- **Osztály:** `RetryDownload`
  - Metódus: `__init__(self, source_error)`
- **Osztály:** `NextFragment`
  - Metódus: `download()`

---
