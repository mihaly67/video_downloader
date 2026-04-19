import unittest
import asyncio
from src.sniffer.playwright_sniffer import VideoSniffer

class TestPlaywrightSniffer(unittest.IsolatedAsyncioTestCase):
    async def test_sniffer_initialization(self):
        sniffer = VideoSniffer()
        self.assertEqual(sniffer.output_file, "session_config.json")
        self.assertEqual(sniffer.found_streams, [])
        self.assertEqual(sniffer.session_headers, {})

if __name__ == '__main__':
    unittest.main()
