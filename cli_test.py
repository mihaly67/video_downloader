import asyncio
import logging
import sys
import os

# Hozzáadjuk a projekt gyökerét a path-hoz, hogy a src modulokat megtalálja
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.sniffer.playwright_sniffer import VideoSniffer
from src.core.queue_manager.queue import DownloadQueueManager

logging.basicConfig(level=logging.INFO)

def progress_callback(event):
    """
    Egyszerű konzolos callback a letöltési folyamat nyomon követésére.
    """
    status = event.get('status')
    if status == 'downloading':
        percent = event.get('percent', 0.0)
        speed = event.get('speed', 0)
        speed_mb = speed / (1024 * 1024) if speed else 0
        sys.stdout.write(f"\rLetöltés folyamatban: {percent:.2f}% | Sebesség: {speed_mb:.2f} MB/s")
        sys.stdout.flush()
    elif status == 'finished':
        print(f"\n✅ Letöltés befejezve: {event.get('filename')}")
    elif status == 'error':
        print(f"\n❌ Hiba történt: {event.get('error')}")


async def main():
    print("--------------------------------------------------")
    print("🚀 Video Downloader - CLI Teszt & Sniffer Demonstráció")
    print("--------------------------------------------------")

    url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/1080/Big_Buck_Bunny_1080_10s_1MB.mp4" # teszt videó
    print(f"\n1. LÉPÉS: Sniffer indítása a következő URL-en: {url}")
    print("Ez egy valós böngészőt nyit meg a háttérben (Stealth módban)...")

    sniffer = VideoSniffer()
    # Ezt most csak tesztként használjuk. Élesben a felhasználó weboldalát kapná, pl egy stream URL-t.
    # Itt most rögtön egy letölthető mp4-et adunk meg, de a Sniffer .m3u8-akat keres, így ezen nem fog találni semmit.
    # Ez a teszt bemutatja a folyamatot.

    result = await sniffer.sniff("https://demo.theoplayer.com/clear-key-drm-cenc-m3u8")

    headers = {}
    download_url = url

    if result and result.get('streams'):
        print(f"\n🎉 Talált streamek száma: {len(result['streams'])}")
        for i, stream in enumerate(result['streams']):
            print(f"  {i+1}. {stream[:80]}...")

        download_url = result['streams'][0]
        headers = result.get('headers', {})
        print(f"\n🔑 Kinyert fejlécek (Session Injection-höz):")
        print(f"User-Agent: {headers.get('User-Agent', '')[:50]}...")
        print(f"Referer: {headers.get('Referer', '')}")
    else:
        print("\n⚠️ Sniffer nem talált m3u8/mpd streamet ezen az oldalon (vagy időtúllépés történt).")
        print("A letöltést az alapértelmezett teszt videóval folytatjuk.")


    print(f"\n2. LÉPÉS: Letöltés indítása a Queue Manageren keresztül...")
    print(f"Letöltendő URL: {download_url}")

    # Queue elindítása (alapból 2 worker szál)
    queue_manager = DownloadQueueManager(ui_callback=progress_callback, max_concurrent=2)

    # Feladat bedobása a queue-ba a kinyert headerekkel (ha voltak)
    await queue_manager.add_task(download_url, headers=headers)

    # Várjuk meg, amíg a letöltés befejeződik
    await queue_manager.queue.join()
    print("\n✅ Minden feladat befejeződött.")

    # Zárjuk le a workereket
    await queue_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
