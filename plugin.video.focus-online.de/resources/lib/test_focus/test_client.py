__author__ = 'bromix'

import unittest
from resources.lib.focus.client import Client


class TestClient(unittest.TestCase):
    def test_get_categories(self):
        client = Client()
        categories = client.get_categories()
        pass

    def test_get_all_videos(self):
        client = Client()
        json_data = client.get_root_data()
        vidoes = client.get_all_videos(json_data)
        pass

    def test_get_root_data(self):
        json_data = Client().get_root_data()
        pass

    def test_get_videos(self):
        client = Client()
        json_data = client.get_videos(category='Panorama')
        pass

    pass
