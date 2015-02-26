__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.rtlinteractive import Provider
import unittest


class TestProvider(unittest.TestCase):
    def test_top_10(self):
        context = kodion.Context(path='/top10/')
        provider = Provider()
        result = provider.navigate(context)
        list = result[0]
        pass

    def test_format(self):
        context = kodion.Context(path='/format/2/')
        provider = Provider()
        result = provider.navigate(context)
        list = result[0]
        pass

    def test_library(self):
        context = kodion.Context(path='/library/')
        provider = Provider()
        result = provider.navigate(context)
        kodion.utils.print_items(result[0])
        pass

    def test_root(self):
        context = kodion.Context(path='/')
        provider = Provider()
        result = provider.navigate(context)
        list = result[0]
        pass

    pass
