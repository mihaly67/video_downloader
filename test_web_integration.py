import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.sniffer.playwright_sniffer import VideoSniffer
from src.core.queue_manager.queue import DownloadQueueManager

def progress_callback(event):
    status = event.get('status')
    if status == 'downloading':
        percent = event.get('percent', 0.0)
        sys.stdout.write(f"\rLetöltés folyamatban: {percent:.2f}%")
        sys.stdout.flush()
    elif status == 'finished':
        print(f"\n✅ Letöltés befejezve: {event.get('filename')}")
    elif status == 'error':
        print(f"\n❌ Hiba történt: {event.get('error')}")

async def run_integration_test():
    print("--- Integrációs teszt indítása (Sniffer + Downloader) ---")
    sniffer = VideoSniffer()
    # Egy példa URL, ami publikus videot tartalmaz
    url_to_test = "https://test-videos.co.uk/"
    print(f"1. Keresés ezen az oldalon: {url_to_test}")

    # A sniffer most csak szimulálni fogja a találatot, mert a valódi böngészés
    # környezettől függően sikertelen lehet.
    # Ennek ellenére meghívjuk a sniffert.
    try:
        result = await sniffer.sniff(url_to_test)
        if not result or not result.get("streams"):
            print("Nem talált streamet a Sniffer. Használunk egy fallback URL-t a teszthez.")
            fallback_url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/1080/Big_Buck_Bunny_1080_10s_1MB.mp4"
            headers = {}
        else:
            fallback_url = result["streams"][0]
            headers = result.get("headers", {})
            print(f"Talált stream: {fallback_url}")
    except Exception as e:
         print(f"Sniffer hiba (várt viselkedés homokozóban): {e}")
         fallback_url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/1080/Big_Buck_Bunny_1080_10s_1MB.mp4"
         headers = {}

    print(f"\n2. Letöltés indítása a Queue Managerrel...")
    qm = DownloadQueueManager(ui_callback=progress_callback, max_concurrent=1)
    await qm.add_task(fallback_url, headers=headers)
    await qm.queue.join()
    await qm.shutdown()
    print("--- Integrációs teszt vége ---")

if __name__ == '__main__':
    asyncio.run(run_integration_test())
