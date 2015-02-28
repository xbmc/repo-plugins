__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.soundcloud.provider import Provider
import unittest


def print_items(items):
    for item in items:
        print item
        pass
    pass


class TestProvider(unittest.TestCase):
    TOKEN = u'1-21686-118589874-2e78a9be01d463'

    def _create_context(self, path):
        context = kodion.Context(path=path)
        settings = context.get_settings()
        settings.set_string(kodion.constants.setting.LOGIN_USERNAME, 'b194139@trbvm.com')
        settings.set_string(kodion.constants.setting.LOGIN_PASSWORD, '1234567890')
        settings.set_string(kodion.constants.setting.ACCESS_TOKEN, self.TOKEN)
        return context

    def test_get_favorites(self):
        provider = Provider()
        context = self._create_context('/user/favorites/me/')
        context.set_localization(30516, 'TEST %s')
        result = provider.navigate(context)
        items = result[0]
        print_items(items)
        pass

    def test_get_recommended_for_track(self):
        provider = Provider()
        context = self._create_context('/explore/recommended/tracks/193347852/')
        context.set_localization(30516, 'TEST %s')
        result = provider.navigate(context)
        items = result[0]
        print_items(items)
        pass

    def test_get_follower(self):
        provider = Provider()

        context = self._create_context('/user/follower/me/')
        result = provider.navigate(context)
        items = result[0]
        print_items(items)
        pass

    def test_get_following(self):
        provider = Provider()

        context = self._create_context('/user/following/me/')
        result = provider.navigate(context)
        items = result[0]
        print_items(items)
        pass

    def test_get_playlist(self):
        provider = Provider()

        context = self._create_context('/playlist/54934787/')
        context.set_localization(30516, 'TEST %s')
        result = provider.navigate(context)
        items = result[0]
        print_items(items)
        pass

    def test_get_user_playlists(self):
        provider = Provider()

        context = self._create_context('/user/playlists/me/')
        result = provider.navigate(context)
        items = result[0]
        print_items(items)
        pass

    def test_explore_trending(self):
        provider = Provider()

        # music
        context = self._create_context('/explore/trending/music/')
        context.set_localization(30516, 'TEST %s')
        context.get_function_cache().disable()
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)

        # audio
        context = self._create_context('/explore/trending/audio/')
        context.set_localization(30516, 'TEST %s')
        context.get_function_cache().disable()
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)
        pass

    def test_search(self):
        provider = Provider()

        path = '/%s/query/' % kodion.constants.paths.SEARCH
        context = kodion.Context(path=path, params={'q': 'angerfist'})
        context.set_localization(30516, 'TEST %s')
        result = provider.navigate(context)
        pass

    def test_explore_genres_drum_bass(self):
        provider = Provider()

        context = self._create_context('/explore/genre/music/Drum & Bass/')
        context.set_localization(30516, 'TEST %s')
        context.get_function_cache().disable()

        # music
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)
        pass

    def test_explore_genres(self):
        provider = Provider()

        # music
        context = self._create_context('/explore/genre/music/')
        context.get_function_cache().disable()
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)

        # audio
        context = self._create_context('/explore/genre/audio/')
        context.get_function_cache().disable()
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)
        pass

    def test_explore(self):
        provider = Provider()

        context = kodion.Context(path='/explore/')
        result = provider.navigate(context)
        items = result[0]

        self.assertEqual(4, len(items))
        print_items(items)
        pass

    def test_root(self):
        provider = Provider()
        context = kodion.Context('/')
        settings = context.get_settings()
        settings.set_string(kodion.constants.setting.LOGIN_USERNAME, '')

        # without login
        result = provider.navigate(context)
        items = result[0]
        self.assertEqual(2, len(items))
        print_items(items)

        # with login
        context = kodion.Context('/')
        settings = context.get_settings()
        settings.set_string(kodion.constants.setting.LOGIN_USERNAME, 'b194139@trbvm.com')
        settings.set_string(kodion.constants.setting.LOGIN_PASSWORD, '1234567890')

        result = provider.navigate(context)
        items = result[0]
        self.assertEqual(4, len(items))

        print_items(items)
        pass

    def test_get_hires_images(self):
        provider = Provider()

        result = provider._get_hires_image(u'https://i1.sndcdn.com/avatars-000069503963-bk852l-large.jpg')
        self.assertEqual(u'https://i1.sndcdn.com/avatars-000069503963-bk852l-t300x300.jpg', result)

        result = provider._get_hires_image('https://i1.sndcdn.com/avatars-000069503963-bk852l-large.jpg?86347b7')
        self.assertEqual('https://i1.sndcdn.com/avatars-000069503963-bk852l-t300x300.jpg', result)

        result = provider._get_hires_image('https://i1.sndcdn.com/artworks-000044733261-1obt8a-large.jpg?86347b7')
        self.assertEqual('https://i1.sndcdn.com/artworks-000044733261-1obt8a-t300x300.jpg', result)
        pass

    pass
