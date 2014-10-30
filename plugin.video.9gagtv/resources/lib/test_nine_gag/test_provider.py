from resources.lib import kodimon
from resources.lib.nine_gag import Provider

__author__ = 'bromix'

import unittest


class TestProvider(unittest.TestCase):
    def setUp(self):
        pass

    def test_on_category(self):
        provider = Provider()

        result = provider.navigate('/category/LJEGX/')
        items = result[0]

        kodimon.print_items(items)
        pass

    def test_on_root(self):
        provider = Provider()

        result = provider.navigate('/')
        items = result[0]

        kodimon.print_items(items)
        pass
    pass
