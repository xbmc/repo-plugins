__author__ = 'bromix'

import unittest

from resources.lib.redbull_tv.client import Client


class TestClient(unittest.TestCase):
    def test_get_channels(self):
        client = Client()
        data = client.get_channels()
        pass

    def test_get_video_streams(self):
        client = Client()

        # live (upcoming)
        streams = client.get_streams('event-stream-529')

        streams = client.get_streams('AP-1HCAY4RND2111')
        streams = client.get_streams('AP-1H6ZJT8EH1W11')

        # live (replay)
        streams = client.get_streams('event-stream-507')
        pass

    pass
