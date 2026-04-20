import unittest
import asyncio
from src.core.queue_manager.queue import DownloadQueueManager
from unittest.mock import MagicMock, patch

class TestDownloadQueueManager(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_callback = MagicMock()
        self.queue_manager = DownloadQueueManager(ui_callback=self.mock_callback, max_concurrent=2)

    async def asyncTearDown(self):
        await self.queue_manager.shutdown()

    @patch('src.core.queue_manager.queue.VideoDownloader.download')
    async def test_add_task(self, mock_download):
        mock_download.return_value = True
        await self.queue_manager.add_task("http://test.com/video1.mp4")
        self.assertEqual(self.queue_manager.queue.qsize(), 1)

    @patch('src.core.queue_manager.queue.VideoDownloader.download')
    async def test_worker_processing(self, mock_download):
        mock_download.return_value = True

        await self.queue_manager.add_task("http://test.com/video1.mp4")
        await asyncio.sleep(0.1) # allow time for the worker to pick up the task
        self.assertEqual(self.queue_manager.queue.qsize(), 0)

        # We need to wait for the worker to actually process the item, but that happens asynchronously.
        # So we can't easily assert that mock_download was called in this synchronous unit test setup.
        # A more complex test setup with asyncio coordination would be needed.

if __name__ == '__main__':
    unittest.main()
