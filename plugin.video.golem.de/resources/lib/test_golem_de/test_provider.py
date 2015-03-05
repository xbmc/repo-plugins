__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.golem_de import Provider

import unittest


class TestProvider(unittest.TestCase):
    def test_on_root(self):
        provider = Provider()

        path = kodion.utils.create_path('/')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_year_month(self):
        provider = Provider()

        path = kodion.utils.create_path('browse', '2014', '3')
        context = kodion.Context(path=path)
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_play(self):
        provider = Provider()

        path = kodion.utils.create_path('play')
        context = kodion.Context(path=path, params={'url': 'http://video.golem.de/games/14874/ue4-techdemo-auf-der-geforce-gtx-titan-x.html'})
        result = provider.navigate(context)
        items = result[0]
        pass

    def test_on_search(self):
        provider = Provider()

        path = kodion.utils.create_path(kodion.constants.paths.SEARCH, 'query')
        context = kodion.Context(path=path, params={'q': 'Lenovo'})
        result = provider.navigate(context)
        items = result[0]
        pass

    pass
