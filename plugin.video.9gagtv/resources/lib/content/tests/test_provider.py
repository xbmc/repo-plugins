__author__ = 'bromix'

import unittest

from resources.lib import nightcrawler
from resources.lib.content import Provider, Client


class TestProvider(unittest.TestCase):
    def setUp(self):
        pass

    def test_on_category(self):
        provider = Provider()

        context = nightcrawler.Context(path='/category/LJEGX/')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    def test_on_root(self):
        provider = Provider()

        context = nightcrawler.Context(path='/')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    pass
