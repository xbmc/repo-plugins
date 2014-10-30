import unittest
from resources.lib.kodimon import DirectoryItem

from resources.lib.prosiebensat1 import Provider


def print_items(items):
    for item in items:
        print item
        pass
    pass


class TestProvider(unittest.TestCase):
    def setUp(self):
        pass

    def test_search(self):
        provider = Provider()

        path = '/%s/query/' % provider.PATH_SEARCH
        result = provider.navigate(path, {'q': 'halligalli'})
        pass

    def test_latest_videos(self):
        provider = Provider()
        format_item = DirectoryItem(u'Test',
                                    provider.create_uri(['pro7', 'library', '277']))
        provider.get_favorite_list().add(format_item)

        result = provider.navigate('/favs/latest/')
        items = result[0]
        pass

    def test_channel_highlights(self):
        provider = Provider()

        # test root of highlights
        result = provider.navigate('/pro7/highlights/')
        items = result[0]

        self.assertEqual(3, len(items))
        print_items(items)

        # test 'Beliebte Sendungen' of highlights
        result = provider.navigate('/pro7/highlights/Beliebte Sendungen/')
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)

        # test 'Aktuelle ganze Folgen' of highlights
        result = provider.navigate('/pro7/highlights/Aktuelle ganze Folgen/')
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)

        # test 'Neueste Clips' of highlights
        result = provider.navigate('/pro7/highlights/Neueste Clips/')
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)
        pass

    def test_format_content(self):
        provider = Provider()

        # test full
        result = provider.navigate('/pro7/library/789/')
        items = result[0]
        self.assertGreater(len(items), 2)

        options = result[1]
        self.assertTrue(not provider.RESULT_CACHE_TO_DISC in options)
        print_items(items)

        # test clips
        result = provider.navigate('/pro7/library/789/', {'clip_type': 'short'})
        items = result[0]
        self.assertGreater(len(items), 0)
        options = result[1]
        self.assertTrue(not provider.RESULT_CACHE_TO_DISC in options)
        print_items(items)

        # test backstage
        result = provider.navigate('/pro7/library/789/', {'clip_type': 'webexclusive'})
        items = result[0]
        self.assertGreater(len(items), 0)
        options = result[1]
        self.assertTrue(not provider.RESULT_CACHE_TO_DISC in options)
        print_items(items)
        pass

    def test_channel_formats(self):
        provider = Provider()
        #provider.get_function_cache().disable()
        result = provider.navigate('/pro7/library/')

        items = result[0]
        self.assertGreater(len(items), 0)

        options = result[1]
        self.assertTrue(not provider.RESULT_CACHE_TO_DISC in options)

        print_items(items)
        pass

    def test_channel_content(self):
        provider = Provider()

        result = provider.navigate('/pro7/')
        items = result[0]

        # 'Highlights' and 'Library'
        self.assertEqual(len(items), 2)

        options = result[1]
        self.assertTrue(not provider.RESULT_CACHE_TO_DISC in options)

        print_items(items)
        pass

    def test_root(self):
        provider = Provider()

        # clear all
        provider.get_favorite_list().clear()
        provider.get_watch_later_list().clear()

        # navigate to the root
        result = provider.navigate('/')
        items = result[0]
        self.assertEqual(len(items), 7)

        # caching should be false, so the additional directories 'Favorties' and 'Watch Later'
        # will show correctly.
        options = result[1]
        self.assertEqual(False, options[provider.RESULT_CACHE_TO_DISC])

        print_items(items)
        pass

    def test_format_next_page(self):
        provider = Provider()
        result = provider.navigate('/pro7/library/505/')

        items = result[0]
        item = items[len(items)-1]
        self.assertEqual('Next Page', item.get_name())
        pass

    pass