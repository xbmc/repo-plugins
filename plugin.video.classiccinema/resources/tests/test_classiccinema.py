import os
import sys
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from resources.lib import api


class APIITTests(unittest.TestCase):

    def test_url(self):
        self.assertEqual(api._url('blah'), 'http://www.classiccinemaonline.com/blah')

    def test_get_categories(self):
        items = api.get_categories()
        self.assertEqual(items, [u'Movie Billboards', u'Serials', u'Silent Films'])

    def test_get_genres_flat(self):
        items = api.get_genres_flat('Movie Billboards')
        self.assertTrue(len(items) > 25)  # Currently 27

        items = api.get_genres_flat('Serials')
        self.assertTrue(len(items) > 32)  # Currently 34

        items = api.get_genres_flat('Silent Films')
        self.assertTrue(len(items) > 5)  # Currently 7

    def test_get_films(self):
        url = 'http://classiccinemaonline.com/movie-billboards/drama'
        items = api.get_films(url)

        self.assertTrue(len(items) > 10)  # currently 12

    def test_get_film(self):
        url = 'http://classiccinemaonline.com/movie-billboards/drama/240-crashing-through-danger-1938'
        item = api.get_film(url)

        film = {
            'url': 'plugin://plugin.video.youtube/?action=play_video&videoid=t0vlyASFz8I',
            'thumbnail': u'http://www.classiccinemaonline.com/images/posters/CrashingThroughDanger1938.jpg',
            'title': u'Crashing Through Danger (1938)'
        }
        self.assertEqual(item, film)
