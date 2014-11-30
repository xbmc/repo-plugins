from resources.lib import kodion
from resources.lib.nine_gag import Provider

__author__ = 'bromix'

import unittest


class TestProvider(unittest.TestCase):
    def setUp(self):
        pass

    def test_on_category(self):
        provider = Provider()
        context = kodion.Context(path='/category/LJEGX/')
        result = provider.navigate(context)
        items = result[0]

        kodion.utils.print_items(items)
        pass

    def test_on_root(self):
        provider = Provider()

        context = kodion.Context(path='/')
        result = provider.navigate(context)
        items = result[0]

        kodion.utils.print_items(items)
        pass
    pass
