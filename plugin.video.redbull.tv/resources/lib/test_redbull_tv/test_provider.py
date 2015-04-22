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

    def test_on_channel_sports(self):
        provider = Provider()

        path = kodion.utils.create_path('/channels/sports/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports_shows(self):
        provider = Provider()

        path = kodion.utils.create_path('/channels/sports/shows/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports_films(self):
        provider = Provider()

        path = kodion.utils.create_path('/channels/sports/films/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports_videos(self):
        provider = Provider()

        path = kodion.utils.create_path('/channels/sports/videos/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_shows_episodes(self):
        provider = Provider()

        path = kodion.utils.create_path('/shows/AP-1H7T4RGM52111/episodes/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_sports_bike(self):
        provider = Provider()

        path = kodion.utils.create_path('/channels/sports/bike/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_main_featured(self):
        provider = Provider()

        path = kodion.utils.create_path('/channels/main/featured')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_main_featured_shows(self):
        provider = Provider()

        path = kodion.utils.create_path('/channels/main/shows/featured')
        context = kodion.Context(path=path)
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