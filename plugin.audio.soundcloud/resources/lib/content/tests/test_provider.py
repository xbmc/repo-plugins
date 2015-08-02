__author__ = 'bromix'

import unittest

from resources.lib import nightcrawler
from resources.lib.content import Provider


class TestProvider(unittest.TestCase):
    USERNAME = 'co4hu41hkqud5cm@my10minutemail.com'
    PASSWORD = '1234567890'

    def test_root(self):
        # without login
        context = nightcrawler.Context('/')
        result = Provider().navigate(context)
        self.assertEquals(len(result), 2)  # 50 + next page

        # with login
        context = nightcrawler.Context('/')
        settings = context.get_settings()
        settings.set_string(settings.LOGIN_USERNAME, self.USERNAME)
        settings.set_string(settings.LOGIN_PASSWORD, self.PASSWORD)
        result = Provider().navigate(context)
        self.assertEquals(len(result), 4)  # 50 + next page

        # with false login
        context = nightcrawler.Context('/')
        settings = context.get_settings()
        settings.set_string(settings.LOGIN_USERNAME, self.USERNAME)
        settings.set_string(settings.LOGIN_PASSWORD, 'fail')
        nightcrawler.run(Provider(), context)
        pass

    def test_on_explore(self):
        context = nightcrawler.Context('/explore/')
        result = Provider().navigate(context)
        self.assertEquals(len(result), 4)
        pass

    def test_explore_trending(self):
        provider = Provider()

        # music
        context = nightcrawler.Context('/explore/trending/music/')
        context.set_localization(provider.SOUNDCLOUD_LOCAL_GO_TO_USER, 'Go to %s')
        result = provider.navigate(context)
        self.assertEquals(len(result), 51)  # 50 + next page

        # audio
        context = nightcrawler.Context('/explore/trending/audio/')
        context.set_localization(provider.SOUNDCLOUD_LOCAL_GO_TO_USER, 'Go to %s')
        result = provider.navigate(context)
        self.assertEquals(len(result), 51)  # 50 + next page
        pass

    def test_explore_genres_drum_bass(self):
        provider = Provider()

        context = nightcrawler.Context('/explore/genre/music/Drum & Bass/')
        context.set_localization(provider.SOUNDCLOUD_LOCAL_GO_TO_USER, 'Go to %s')
        result = provider.navigate(context)
        self.assertEquals(len(result), 51)  # 50 + next page
        pass

    def test_get_user_playlists(self):
        provider = Provider()
        context = nightcrawler.Context('/user/playlists/2442230/')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    def test_get_user_tracks(self):
        provider = Provider()
        context = nightcrawler.Context('/user/tracks/2442230/')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    def test_get_following(self):
        provider = Provider()
        context = nightcrawler.Context('/user/following/2442230/')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    def test_get_follower(self):
        provider = Provider()

        context = nightcrawler.Context('/user/follower/2442230/')
        result = provider.navigate(context)
        self.assertEquals(len(result), 0)
        pass

    def test_get_favorites(self):
        provider = Provider()
        context = nightcrawler.Context('/user/favorites/2442230/')
        context.set_localization(provider.SOUNDCLOUD_LOCAL_GO_TO_USER, 'Go to %s')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    def test_play(self):
        provider = Provider()
        context = nightcrawler.Context('/play/', {'audio_id': 193347852})
        result = provider.navigate(context)
        pass

    def test_get_recommended_for_track(self):
        provider = Provider()

        context = nightcrawler.Context('/explore/recommended/tracks/193347852/')
        context.set_localization(provider.SOUNDCLOUD_LOCAL_GO_TO_USER, 'Go to %s')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    def test_search(self):
        provider = Provider()

        context = nightcrawler.Context(provider.PATH_SEARCH_QUERY, {'q': 'angerfist'})
        context.set_localization(provider.SOUNDCLOUD_LOCAL_GO_TO_USER, 'Go to %s')
        result = provider.navigate(context)
        self.assertGreaterEqual(len(result), 2)

        # playlist search
        path, params = nightcrawler.utils.path.from_uri(result[1]['uri'])
        context = nightcrawler.Context(provider.PATH_SEARCH_QUERY, params)
        context.set_localization(provider.SOUNDCLOUD_LOCAL_GO_TO_USER, 'Go to %s')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)

        # people search
        path, params = nightcrawler.utils.path.from_uri(result[0]['uri'])
        context = nightcrawler.Context(provider.PATH_SEARCH_QUERY, params)
        context.set_localization(provider.SOUNDCLOUD_LOCAL_GO_TO_USER, 'Go to %s')
        result = provider.navigate(context)
        self.assertGreater(len(result), 0)
        pass

    pass
