__author__ = 'bromix'

import unittest

from resources.lib.content import Client


class TestClient(unittest.TestCase):
    def test_get_home(self):
        client = Client()
        categories = client.get_home()
        self.assertGreaterEqual(len(categories), 0)
        pass

    def test_get_feed(self):
        client = Client()
        feed = client.get_feed(40)
        pass

    def test_get_video_streams(self):
        client = Client()
        videos = client.get_feed(40)
        video_id = videos[0]['id']
        json_data = client.get_video_streams(video_id)
        pass

    def test_search(self):
        client = Client()
        xml = client.search('superman')
        pass
    pass
