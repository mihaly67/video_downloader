import unittest
import asyncio
from src.core.downloader import VideoDownloader
from src.core.queue_manager.queue import DownloadQueueManager

class TestCoreDownloader(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.events = []

    def mock_callback(self, event):
        self.events.append(event)

    def test_downloader_init(self):
        downloader = VideoDownloader(ui_callback=self.mock_callback)
        self.assertIsNotNone(downloader)
        self.assertEqual(downloader.ydl_opts['format'], 'bestvideo+bestaudio/best')

    def test_downloader_update_session_headers(self):
        downloader = VideoDownloader()
        headers = {'User-Agent': 'Test', 'Referer': 'http://test.com'}
        downloader.update_session_headers(headers)
        self.assertEqual(downloader.ydl_opts['http_headers'], headers)

    def test_progress_hook(self):
        downloader = VideoDownloader(ui_callback=self.mock_callback)
        downloader._progress_hook({'status': 'downloading', 'total_bytes': 100, 'downloaded_bytes': 50, 'speed': 10, 'eta': 5, 'filename': 'test.mp4'})
        self.assertEqual(len(self.events), 1)
        self.assertEqual(self.events[0]['status'], 'downloading')
        self.assertEqual(self.events[0]['percent'], 50.0)

    async def test_queue_manager(self):
        queue_manager = DownloadQueueManager(ui_callback=self.mock_callback, max_concurrent=1)
        await queue_manager.add_task("invalid_url")
        # Give worker a chance to process
        await asyncio.sleep(1)
        await queue_manager.shutdown()
        # Expect an error event due to invalid URL
        error_events = [e for e in self.events if e.get('status') == 'error']
        self.assertTrue(len(error_events) > 0)

if __name__ == '__main__':
    unittest.main()
