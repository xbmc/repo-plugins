__author__ = 'bromix'

import unittest
from resources.lib.netzkino import Provider
from resources.lib import kodion

class TestProvider(unittest.TestCase):
    def setUp(self):
        pass

    def test_category(self):
        context = kodion.Context(path='/category/5/')
        provider = Provider()
        result = provider.navigate(context)

        items = result[0]
        self.assertGreater(len(items), 1)
        for item in items:
            print item
            pass

        options = result[1]
        self.assertEqual(0, len(options))
        pass

    def test_root(self):
        provider = Provider()
        context = kodion.Context(path='/')
        result = provider.navigate(context)

        items = result[0]
        self.assertGreater(len(items), 1)
        for item in items:
            print item
            pass

        options = result[1]
        self.assertEqual(False, options[provider.RESULT_CACHE_TO_DISC])
        pass

    pass
