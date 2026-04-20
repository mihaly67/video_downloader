import unittest
from unittest.mock import patch, MagicMock
import os
from src.core.downloader import VideoDownloader

class TestVideoDownloader(unittest.TestCase):

    def test_init(self):
        downloader = VideoDownloader()
        self.assertIsNone(downloader.ui_callback)
        self.assertEqual(downloader.ydl_opts['format'], 'bestvideo+bestaudio/best')

    def test_update_session_headers(self):
        downloader = VideoDownloader()
        headers = {'User-Agent': 'Test', 'Referer': 'http://test.com', 'Cookie': 'test_cookie'}
        downloader.update_session_headers(headers)
        self.assertEqual(downloader.ydl_opts['http_headers']['User-Agent'], 'Test')
        self.assertEqual(downloader.ydl_opts['http_headers']['Referer'], 'http://test.com')
        self.assertEqual(downloader.ydl_opts['http_headers']['Cookie'], 'test_cookie')

    def test_progress_hook(self):
        # Create a mock callback function
        mock_callback = MagicMock()

        # Instantiate VideoDownloader with the mock callback
        downloader = VideoDownloader(ui_callback=mock_callback)

        # Call _progress_hook with simulated data
        d = {'status': 'downloading', 'total_bytes': 100, 'downloaded_bytes': 50, 'speed': 10, 'eta': 5, 'filename': 'test.mp4'}
        downloader._progress_hook(d)

        # Verify that the callback was called with the expected event dictionary
        mock_callback.assert_called_once_with({
            'status': 'downloading',
            'percent': 50.0,
            'speed': 10,
            'eta': 5,
            'filename': 'test.mp4',
            'downloaded_bytes': 50,
            'total_bytes': 100
        })

    @patch('src.core.downloader.yt_dlp.YoutubeDL')
    def test_download_success(self, MockYoutubeDL):
        mock_ydl = MockYoutubeDL.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {'title': 'Test Video'}

        downloader = VideoDownloader()
        result = downloader.download('http://test.com/video.mp4')

        self.assertTrue(result)
        mock_ydl.extract_info.assert_called_once_with('http://test.com/video.mp4', download=True)

    @patch('src.core.downloader.yt_dlp.YoutubeDL')
    def test_download_failure(self, MockYoutubeDL):
        mock_ydl = MockYoutubeDL.return_value.__enter__.return_value
        mock_ydl.extract_info.side_effect = Exception("Test exception")

        mock_callback = MagicMock()
        downloader = VideoDownloader(ui_callback=mock_callback)
        result = downloader.download('http://test.com/video.mp4')

        self.assertFalse(result)
        mock_callback.assert_called_once_with({'status': 'error', 'error': 'Test exception'})

if __name__ == '__main__':
    unittest.main()
