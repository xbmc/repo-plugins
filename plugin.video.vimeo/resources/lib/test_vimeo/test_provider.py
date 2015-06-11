# -*- coding: utf-8 -*-

__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.vimeo import Provider

import unittest


class TestProvider(unittest.TestCase):
    def test_play(self):
        provider = Provider()

        path = kodion.utils.create_path('play')
        context = kodion.Context(path=path, params={'video_id': '127708722'})
        context.get_settings().set_int(kodion.constants.setting.VIDEO_QUALITY, 3)
        context.set_localization(30511, 'Go to %s')
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_playlists(self):
        provider = Provider()

        path = kodion.utils.create_path('channel', 'UCDbAn9LEzqONk__uXA6a9jQ', 'playlists')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel_playlist(self):
        provider = Provider()

        path = kodion.utils.create_path('channel', 'some_channel_id', 'playlist', 'UUDbAn9LEzqONk__uXA6a9jQ')
        context = kodion.Context(path=path)
        context.set_localization(30502, 'Go to %s')
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_channel(self):
        provider = Provider()

        path = kodion.utils.create_path('channel', 'UCDbAn9LEzqONk__uXA6a9jQ')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_search_video(self):
        provider = Provider()

        path = kodion.utils.create_path(kodion.constants.paths.SEARCH, 'query')
        context = kodion.Context(path=path, params={'q': u'Bäume'})
        context.set_localization(30511, 'Go to %s')
        result = provider.navigate(context)
        items = result[0]
        self.assertGreater(len(items), 0)
        kodion.utils.print_items(items)
        pass

    def test_on_root(self):
        provider = Provider()

        context = kodion.Context(path='/')
        settings = context.get_settings()
        settings.set_string(kodion.constants.setting.LOGIN_USERNAME, '')
        settings.set_string(kodion.constants.setting.LOGIN_PASSWORD, '')

        result = provider.navigate(context)

        items = result[0]
        self.assertGreater(len(items), 0)

        kodion.utils.print_items(items)
        pass

    pass
