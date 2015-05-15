__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.redbull_tv import Provider

import unittest


class TestProvider(unittest.TestCase):
    def test_on_root(self):
        provider = Provider()

        path = kodion.utils.create_path('/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_main(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/channels/main/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/channels/sports/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports_shows(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/channels/sports/shows/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports_all(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/channels/sports/')
        context = kodion.Context(path=path, params={'all': '1'})
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_shows_episodes(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/shows/AP-1H7T4RGM52111/episodes/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_live(self):
        provider = Provider()

        path = kodion.utils.create_path('/redbull/channels/live/')
        context = kodion.Context(path=path, params={'channel_id': 'live'})
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports_films(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/channels/sports/films/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports_videos(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/channels/sports/videos/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports_bike(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/channels/sports/bike/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_main_featured(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/channels/main/featured')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_main_featured_shows(self):
        provider = Provider()

        path = kodion.utils.create_path('redbull/channels/main/shows/featured')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_live_featured(self):
        provider = Provider()

        path = kodion.utils.create_path('/redbull/channels/live/featured')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_live_upcoming(self):
        provider = Provider()

        path = kodion.utils.create_path('/redbull/videos/event_streams')
        context = kodion.Context(path=path, params={'limit': '100',
                                                    'event_type': 'upcoming',
                                                    'next_page_allowed': '0'})
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_live_replay(self):
        provider = Provider()

        path = kodion.utils.create_path('/redbull/videos/event_streams')
        context = kodion.Context(path=path, params={'limit': '100',
                                                    'event_type': 'replay',
                                                    'next_page_allowed': '0'})
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_live_live(self):
        provider = Provider()

        path = kodion.utils.create_path('/redbull/channels/live/featured')
        context = kodion.Context(path=path, params={'limit': '100',
                                                    'event_type': 'replay',
                                                    'next_page_allowed': '0'})
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_search(self):
        provider = Provider()

        path = kodion.utils.create_path(kodion.constants.paths.SEARCH, 'query')
        context = kodion.Context(path=path, params={'q': 'race'})
        result = provider.navigate(context)
        items = result[0]
        pass

    pass