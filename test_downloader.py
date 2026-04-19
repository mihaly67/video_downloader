import asyncio
from src.core.queue_manager.queue import DownloadQueueManager
from src.core.downloader import VideoDownloader

def mock_callback(event):
    print(f"Event received: {event['status']}")
    if event['status'] == 'downloading':
        print(f"Progress: {event.get('percent', 0)}%")

async def main():
    print("Testing VideoDownloader...")
    downloader = VideoDownloader(ui_callback=mock_callback)

    print("\nTesting DownloadQueueManager...")
    queue_manager = DownloadQueueManager(ui_callback=mock_callback, max_concurrent=1)
    await queue_manager.add_task("https://www.w3schools.com/html/mov_bbb.mp4")

    # Wait a bit for the worker to start processing
    await asyncio.sleep(5)
    await queue_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
