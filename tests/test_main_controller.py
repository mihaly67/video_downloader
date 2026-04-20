import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from src.core.main_controller import MainController

class TestMainController(unittest.IsolatedAsyncioTestCase):

    @patch('src.core.main_controller.VideoSniffer')
    @patch('src.core.main_controller.DownloadQueueManager')
    async def test_add_download_task_success(self, MockQueueManager, MockSniffer):
        # Mock Sniffer
        mock_sniffer_instance = MockSniffer.return_value
        mock_sniffer_instance.sniff = AsyncMock(return_value={
            'streams': ['http://test.com/stream.m3u8'],
            'headers': {'User-Agent': 'TestAgent'}
        })

        # Mock Queue Manager
        mock_queue_manager_instance = MockQueueManager.return_value
        mock_queue_manager_instance.add_task = AsyncMock()

        # Mock Callback
        mock_callback = MagicMock()

        controller = MainController(ui_callback=mock_callback)
        # Inyect the mocks
        controller.sniffer = mock_sniffer_instance
        controller.queue_manager = mock_queue_manager_instance

        await controller.add_download_task('http://example.com/video')

        mock_sniffer_instance.sniff.assert_called_once_with('http://example.com/video')
        mock_queue_manager_instance.add_task.assert_called_once_with('http://test.com/stream.m3u8', {'User-Agent': 'TestAgent'})

        # Check if callbacks were called correctly
        self.assertEqual(mock_callback.call_count, 2)
        mock_callback.assert_any_call({'status': 'sniffing', 'url': 'http://example.com/video'})
        mock_callback.assert_any_call({'status': 'added_to_queue', 'url': 'http://test.com/stream.m3u8'})

    @patch('src.core.main_controller.VideoSniffer')
    @patch('src.core.main_controller.DownloadQueueManager')
    async def test_add_download_task_no_stream(self, MockQueueManager, MockSniffer):
        # Mock Sniffer to return None (no stream found)
        mock_sniffer_instance = MockSniffer.return_value
        mock_sniffer_instance.sniff = AsyncMock(return_value=None)

        # Mock Queue Manager
        mock_queue_manager_instance = MockQueueManager.return_value
        mock_queue_manager_instance.add_task = AsyncMock()

        # Mock Callback
        mock_callback = MagicMock()

        controller = MainController(ui_callback=mock_callback)
        controller.sniffer = mock_sniffer_instance
        controller.queue_manager = mock_queue_manager_instance

        await controller.add_download_task('http://example.com/video')

        mock_sniffer_instance.sniff.assert_called_once_with('http://example.com/video')
        mock_queue_manager_instance.add_task.assert_not_called()

        # Check if callbacks were called correctly
        self.assertEqual(mock_callback.call_count, 2)
        mock_callback.assert_any_call({'status': 'sniffing', 'url': 'http://example.com/video'})
        mock_callback.assert_any_call({'status': 'error', 'error': 'Nem található stream a megadott URL-en.'})

if __name__ == '__main__':
    unittest.main()
