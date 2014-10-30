from resources.lib.kodimon.abstract_settings import AbstractSettings
from resources.lib.kodimon import Plugin

__author__ = 'bromix'

from resources.lib.soundcloud.provider import Provider
import unittest


def print_items(items):
    for item in items:
        print item
        pass
    pass


class TestProvider(unittest.TestCase):
    TOKEN = u'1-21686-118589874-2e78a9be01d463'

    def setUp(self):
        # with login
        plugin = Plugin()
        settings = plugin.get_settings()
        settings.set_string(AbstractSettings.LOGIN_USERNAME, 'b194139@trbvm.com')
        settings.set_string(AbstractSettings.LOGIN_PASSWORD, '1234567890')
        settings.set_string(AbstractSettings.ACCESS_TOKEN, self.TOKEN)
        self._provider = Provider(plugin)
        pass

    def test_get_favorites(self):
        result = self._provider.navigate('/user/favorites/me/')
        items = result[0]
        print_items(items)
        pass

    def test_get_follower(self):
        result = self._provider.navigate('/user/follower/me/')
        items = result[0]
        print_items(items)
        pass

    def test_get_following(self):
        result = self._provider.navigate('/user/following/me/')
        items = result[0]
        print_items(items)
        pass

    def test_get_playlist(self):
        result = self._provider.navigate('/playlist/54934787/')
        items = result[0]
        print_items(items)
        pass

    def test_get_user_playlists(self):
        result = self._provider.navigate('/user/playlists/me/')
        items = result[0]
        print_items(items)
        pass

    def test_explore_trending(self):
        provider = Provider()
        provider.get_function_cache().disable()

        # music
        result = provider.navigate('/explore/trending/music/')
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)

        # audio
        result = provider.navigate('/explore/trending/audio/')
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)
        pass

    def test_search(self):
        provider = Provider()

        path = '/%s/query/' % provider.PATH_SEARCH
        result = provider.navigate(path, {'q': 'angerfist'})
        pass

    def test_explore_genres_drum_bass(self):
        provider = Provider()
        provider.get_function_cache().disable()

        # music
        result = provider.navigate('/explore/genre/music/Drum & Bass/')
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)
        pass

    def test_explore_genres(self):
        provider = Provider()
        provider.get_function_cache().disable()

        # music
        result = provider.navigate('/explore/genre/music/')
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)

        # audio
        result = provider.navigate('/explore/genre/audio/')
        items = result[0]
        self.assertGreater(len(items), 0)
        print_items(items)
        pass

    def test_explore(self):
        provider = Provider()

        result = provider.navigate('/explore/')
        items = result[0]

        self.assertEqual(4, len(items))
        print_items(items)
        pass

    def test_root(self):
        provider = Provider()
        plugin = provider.get_plugin()
        settings = plugin.get_settings()
        settings.set_string(AbstractSettings.LOGIN_USERNAME, '')

        # without login
        result = provider.navigate('/')
        items = result[0]
        self.assertEqual(2, len(items))
        print_items(items)

        # with login
        plugin = Plugin()
        settings = plugin.get_settings()
        settings.set_string(AbstractSettings.LOGIN_USERNAME, 'b194139@trbvm.com')
        settings.set_string(AbstractSettings.LOGIN_PASSWORD, '1234567890')
        provider = Provider(plugin)
        result = provider.navigate('/')
        items = result[0]
        self.assertEqual(4, len(items))

        print_items(items)
        pass

    def test_get_hires_images(self):
        provider = Provider()

        result = provider._get_hires_image(u'https://i1.sndcdn.com/avatars-000069503963-bk852l-large.jpg')
        self.assertEqual(u'https://i1.sndcdn.com/avatars-000069503963-bk852l-t500x500.jpg', result)

        result = provider._get_hires_image('https://i1.sndcdn.com/avatars-000069503963-bk852l-large.jpg?86347b7')
        self.assertEqual('https://i1.sndcdn.com/avatars-000069503963-bk852l-t500x500.jpg', result)

        result = provider._get_hires_image('https://i1.sndcdn.com/artworks-000044733261-1obt8a-large.jpg?86347b7')
        self.assertEqual('https://i1.sndcdn.com/artworks-000044733261-1obt8a-t500x500.jpg', result)
        pass

    pass
