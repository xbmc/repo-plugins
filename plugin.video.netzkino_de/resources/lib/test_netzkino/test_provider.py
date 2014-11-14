from resources.lib.netzkino import Provider

__author__ = 'bromix'

import unittest


class TestProvider(unittest.TestCase):
    def setUp(self):
        pass

    def test_category(self):
        provider = Provider()
        result = provider.navigate('/category/5/')

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
        result = provider.navigate('/')

        items = result[0]
        self.assertGreater(len(items), 1)
        for item in items:
            print item
            pass

        options = result[1]
        self.assertEqual(False, options[provider.RESULT_CACHE_TO_DISC])
        pass

    pass
