import datetime

__author__ = 'bromix'

import unittest

from resources.lib import nightcrawler
from resources.lib.content.provider import Provider


class TestProvider(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # clear the cache
        # nightcrawler.Context().get_function_cache().clear()
        pass

    def test_on_root(self):
        context = nightcrawler.Context(path='/')
        result = Provider().navigate(context)
        self.assertGreaterEqual(len(result), 7)
        pass

    def test_on_browse_newest(self):
        context = nightcrawler.Context(path='/browse/newest/')
        result = Provider().navigate(context)
        self.assertEquals(len(result), 50)
        pass

    def test_on_week_in_review(self):
        # test years
        context = nightcrawler.Context(path='/browse/query/', params={'q': 'wochenrueckblick'})
        result = Provider().navigate(context)
        self.assertGreaterEqual(len(result), 1)

        # test month
        now = datetime.datetime.now()-datetime.timedelta(30)
        context = nightcrawler.Context(path='/browse/query/%d/' % now.year, params={'q': 'wochenrueckblick'})
        result = Provider().navigate(context)
        self.assertGreaterEqual(len(result), 1)

        # test end result
        context = nightcrawler.Context(path='/browse/query/%d/%d/' % (now.year, now.month),
                                       params={'q': 'wochenrueckblick'})
        result = Provider().navigate(context)
        self.assertGreaterEqual(len(result), 1)
        pass

    def test_on_manufacturer_videos(self):
        now = datetime.datetime.now()-datetime.timedelta(30)
        context = nightcrawler.Context(path='/browse/query/%d/%d/' % (now.year, now.month),
                                       params={'q': 'herstellervideo'})
        result = Provider().navigate(context)
        self.assertGreaterEqual(len(result), 1)
        pass

    def test_on_trailer(self):
        now = datetime.datetime.now()-datetime.timedelta(30)
        context = nightcrawler.Context(path='/browse/query/%d/%d/' % (now.year, now.month),
                                       params={'q': 'trailer'})
        result = Provider().navigate(context)
        self.assertGreaterEqual(len(result), 1)
        pass

    def test_on_year(self):
        now = datetime.datetime.now()
        context = nightcrawler.Context(path='/browse/date/%d/' % now.year)
        result = Provider().navigate(context)
        self.assertEquals(len(result), now.month)
        pass

    def test_on_year_and_month(self):
        now = datetime.datetime.now()
        context = nightcrawler.Context(path='/browse/date/%d/%d/' % (now.year, now.month))
        result = Provider().navigate(context)
        self.assertGreater(len(result), 0)
        pass

    def test_on_browse_all(self):
        context = nightcrawler.Context(path='/browse/all/')
        result = Provider().navigate(context)
        self.assertGreaterEqual(len(result), 100)
        pass

    def test_on_play(self):
        provider = Provider()

        context = nightcrawler.Context(path='/browse/newest/')
        result = provider.navigate(context)
        video = result[0]

        path, params = nightcrawler.utils.path.from_uri(video['uri'])
        context = nightcrawler.Context(path, params)
        settings = context.get_settings()
        settings.set_int(settings.VIDEO_QUALITY, 1)
        result = provider.navigate(context)
        self.assertEquals(result['type'], 'uri')
        self.assertIsNotNone(result.get('uri', None))
        pass

    def test_on_search_list(self):
        provider = Provider()

        context = nightcrawler.Context(provider.PATH_SEARCH)
        context.get_search_history().clear()
        result = provider.navigate(context)
        self.assertEquals(len(result), 1)
        pass

    def test_on_search_query(self):
        provider = Provider()

        context = nightcrawler.Context('/search/query/', {'q': 'trailer', 'limit': '10'})
        context.get_search_history().clear()
        result = provider.navigate(context)
        self.assertGreaterEqual(len(result), 1)

        context = nightcrawler.Context(provider.PATH_SEARCH)
        result = provider.navigate(context)
        self.assertEquals(len(result), 2)
        pass

    pass
