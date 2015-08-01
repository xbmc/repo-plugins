__author__ = 'bromix'

import unittest

from resources.lib.content.client import Client


class TestClient(unittest.TestCase):
    def test_get_root_data(self):
        json_data = Client().get_root_data()
        pass

    def test_get_categories(self):
        client = Client()
        categories = client.get_categories()
        pass

    def test_get_videos_by_category(self):
        client = Client()
        videos = client.get_videos_by_category(category='Panorama')
        pass

    def test_get_all_videos(self):
        client = Client()
        videos = client.get_all_videos()
        pass

    def test_get_related_videos(self):
        url = 'http://www.focus.de/sport/golf/golf-wissen-chippen-und-putten-reine-nervensache-vor-dem-einlochen-so-bleiben-sie-beim-kurzen-spiel-cool_id_4786330.html'
        client = Client()
        videos = client.get_related_videos(url)
        pass

    def test_get_video_streams(self):
        url = 'http://www.focus.de/sport/golf/golf-wissen-chippen-und-putten-reine-nervensache-vor-dem-einlochen-so-bleiben-sie-beim-kurzen-spiel-cool_id_4786330.html'
        streams = Client().get_video_streams(url)
        pass

    pass
