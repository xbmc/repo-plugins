import os
import sys
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from resources.lib import api


class APIITTests(unittest.TestCase):

    def test_get_topics(self):
        items = api.get_topics()
        self.assertTrue(len(items) > 10)  # currently 11

    def test_get_sub_topics(self):
        url = 'http://www.nytimes.com/video/landing/world/1194811622205/index.html'
        items = api.get_sub_topics(url)
        self.assertTrue(len(items) > 4)  # currently 5

        url = 'http://www.nytimes.com/video/landing/americas/1194811622209/index.html'
        items2 = api.get_sub_topics(url)
        # Ensure we don't re-parse sub topics when already on a sub topic page
        self.assertEqual(len(items2), 0)

    def test_get_videos(self):
        url = 'http://www.nytimes.com/video/landing/world/1194811622205/index.html'
        videos = api.get_videos(url)
        self.assertTrue(len(videos) > 99)
