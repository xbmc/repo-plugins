__author__ = 'bromix'

import unittest
from resources.lib.netzkino import Client

class TestClient(unittest.TestCase):
    def setUp(self):
        pass

    def test_search(self):
        client = Client()
        json_data = client.search('Der Schlachter')

        # at least 1 ore more items
        self.assertGreater(len(json_data), 1)
        pass

    def test_get_video_url(self):
        client = Client()
        url = client.get_video_url('some_id')

        self.assertEqual(u'http://netzkino_and-vh.akamaihd.net/i/some_id.mp4/master.m3u8', url)
        pass

    def test_get_category_content(self):
        client = Client()

        json_data = client.get_category_content(5)
        # at least 1 ore more items
        self.assertGreater(len(json_data), 1)
        pass

    def test_get_categories(self):
        client = Client()
        json_data = client.get_categories()

        # at least 1 ore more items
        self.assertGreater(len(json_data), 1)
        pass

    def test_get_home(self):
        client = Client()
        json_data = client.get_home()

        # at least 1 ore more items
        self.assertGreater(len(json_data), 1)
        pass

    pass
