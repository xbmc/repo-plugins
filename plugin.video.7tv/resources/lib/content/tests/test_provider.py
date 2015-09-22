import unittest

from resources.lib import nightcrawler
from resources.lib.content import Provider, Client


class TestProvider(unittest.TestCase):
    def test_root(self):
        provider = Provider()

        # clear all
        context = nightcrawler.Context('/')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    def test_on_channel(self):
        provider = Provider()

        for channel_id in Client.CHANNEL_ID_LIST:
            context = nightcrawler.Context('/%s/' % channel_id)
            result = provider.navigate(context)
            self.assertGreater(len(result), 0)

            context = nightcrawler.Context('/%s/library/' % channel_id)
            result = provider.navigate(context)
            self.assertGreater(len(result), 0)

            context = nightcrawler.Context('/%s/Beliebte Sendungen/' % channel_id)
            result = provider.navigate(context)
            self.assertGreater(len(result), 0)

            context = nightcrawler.Context('/%s/Aktuelle ganze Folgen/' % channel_id)
            result = provider.navigate(context)
            self.assertGreater(len(result), 0)

            context = nightcrawler.Context('/%s/Neueste Clips/' % channel_id)
            result = provider.navigate(context)
            self.assertGreater(len(result), 0)
            pass
        pass

    def test_channel_formats(self):
        provider = Provider()

        context = nightcrawler.Context('/pro7/library/')
        result = provider.navigate(context)
        pass

    def test_format_content(self):
        provider = Provider()

        # test full
        context = nightcrawler.Context(path='/pro7/library/pro7:789/')
        result = provider.navigate(context)

        context = nightcrawler.Context(path='/pro7/library/pro7:789/Ganze Folgen/')
        result = provider.navigate(context)
        pass

    def test_search(self):
        provider = Provider()

        context = nightcrawler.Context(path=provider.PATH_SEARCH_QUERY, params={'q': 'halligalli'})
        result = provider.navigate(context)
        pass

    pass