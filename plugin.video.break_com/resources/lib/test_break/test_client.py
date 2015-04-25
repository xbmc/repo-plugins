from resources.lib.break_api import Client

__author__ = 'bromix'

import unittest


class TestClient(unittest.TestCase):
    def test_get_video_url(self):
        client = Client()
        url = client.get_video_urls(2848412)
        pass

    def test_search(self):
        client = Client()
        xml = client.search('superman')
        pass

    def test_get_video(self):
        client = Client()
        json_data = client.get_video(2608653)
        pass

    def test_get_feed(self):
        client = Client()
        json_data = client.get_feed(40)
        pass

    def test_get_home(self):
        client = Client()
        json_data = client.get_home()
        pass
    pass
