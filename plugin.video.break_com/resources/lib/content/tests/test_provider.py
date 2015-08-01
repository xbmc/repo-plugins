__author__ = 'bromix'

import unittest

from resources.lib import nightcrawler
from resources.lib.content import Provider, Client


class TestProvider(unittest.TestCase):
    def test_on_root(self):
        provider = Provider()

        context = nightcrawler.Context(path='/')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    def test_feed(self):
        provider = Provider()

        context = nightcrawler.Context(path='/feed/40/')
        result = provider.navigate(context)
        pass

    def test_play(self):
        provider = Provider()

        client = Client()
        videos = client.get_feed(40)
        video_id = videos[1]['id']
        context = nightcrawler.Context(path='/play/', params={'video_id': video_id})
        settings = context.get_settings()
        settings.set_int(settings.VIDEO_QUALITY, 4)
        result = provider.navigate(context)
        pass

    def test_search(self):
        provider = Provider()

        context = nightcrawler.Context(path=provider.PATH_SEARCH_QUERY, params={'q': 'superman'})
        result = provider.navigate(context)
        pass
    pass
