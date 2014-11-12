from resources.lib.break_api import Client

__author__ = 'bromix'

import unittest


class TestClient(unittest.TestCase):
    def test_get_gallery(self):
        client = Client()
        json_data = client.get_gallery(2784037)
        pass

    def test_get_gallery_id(self):
        client = Client()
        gallery_id = client.get_gallery_id()
        pass

    def test_get_video_url(self):
        client = Client()
        url = client.get_video_url(2784704)
        pass

    def test_get_video(self):
        client = Client()
        json_data = client.get_video(2784704)
        pass

    def test_get_feed(self):
        client = Client()
        json_data = client.get_feed(43)
        pass

    def test_get_home(self):
        client = Client()
        json_data = client.get_home()
        pass
    pass
