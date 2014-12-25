from resources.lib import kodion
from resources.lib.break_api import Provider

__author__ = 'bromix'

import unittest


class TestProvider(unittest.TestCase):
    def test_feed(self):
        provider = Provider()

        context = kodion.Context(path='/show/2786742/')
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
