__author__ = 'bromix'

from resources.lib.clipfish.client import Client

import unittest


class TestClient(unittest.TestCase):
    def test_get_categories(self):
        client = Client()
        json_data = client.get_categories()
        pass

    def test_get_video_url(self):
        client = Client()
        json_data = client.get_video_url(4197270)
        pass
    pass

