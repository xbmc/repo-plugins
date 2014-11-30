import unittest


from resources.lib import kodion
from resources.lib.kodion.items import DirectoryItem
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

        path = '/%s/query/' % kodion.constants.paths.SEARCH
        context = kodion.Context(path=path, params={'q': 'halligalli'})
        result = provider.navigate(context)
        pass

    def test_latest_videos(self):
        provider = Provider()

        context = kodion.Context(path='/favs/latest/')
        format_item = DirectoryItem(u'Test',
                                    context.create_uri(['pro7', 'library', '277']))

        context.get_favorite_list().add(format_item)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_channel_highlights(self):
        provider = Provider()

        # test root of highlights
        context = kodion.Context(path='/pro7/highlights/')
        result = provider.navigate(context)
        items = result[0]

        self.assertEqual(3, len(items))
        print_items(items)

        # test 'Beliebte Sendungen' of highlights
        context = kodion.Context(path='/pro7/highlights/Beliebte Sendungen/')
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)

        # test 'Aktuelle ganze Folgen' of highlights
        context = kodion.Context(path='/pro7/highlights/Aktuelle ganze Folgen/')
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)

        # test 'Neueste Clips' of highlights
        context = kodion.Context(path='/pro7/highlights/Neueste Clips/')
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)
        pass

    def test_format_content(self):
        provider = Provider()

        # test full
        context = kodion.Context(path='/pro7/library/789/')
        context.get_function_cache()._clear()
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 2)

        options = result[1]
        self.assertTrue(not provider.RESULT_CACHE_TO_DISC in options)
        print_items(items)

        # test clips
        context = kodion.Context(path='/pro7/library/789/', params={'clip_type': 'short'})
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        options = result[1]
        self.assertTrue(not provider.RESULT_CACHE_TO_DISC in options)
        print_items(items)

        # test backstage
        context = kodion.Context(path='/pro7/library/789/', params={'clip_type': 'webexclusive'})
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        options = result[1]
        self.assertTrue(not provider.RESULT_CACHE_TO_DISC in options)
        print_items(items)
        pass

    def test_channel_formats(self):
        provider = Provider()

        context = kodion.Context(path='/pro7/library/')
        #context.get_function_cache().disable()
        result = provider.navigate(context)

        items = result[0]
        self.assertGreater(len(items), 0)

        options = result[1]
        self.assertTrue(not provider.RESULT_CACHE_TO_DISC in options)

        print_items(items)
        pass

    def test_channel_content(self):
        provider = Provider()

        context = kodion.Context(path='/pro7/')
        result = provider.navigate(context)
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
        context = kodion.Context('/')
        context.get_favorite_list().clear()
        context.get_watch_later_list().clear()

        # navigate to the root
        result = provider.navigate(context)
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

        context = kodion.Context(path='/pro7/library/505/')
        result = provider.navigate(context)

        items = result[0]
        item = items[len(items)-1]
        self.assertEqual('Next Page', item.get_name())
        pass

    pass