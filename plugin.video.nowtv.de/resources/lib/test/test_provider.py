import datetime

__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.nowtv import Provider
import unittest


class TestProvider(unittest.TestCase):
    def test_format(self):
        context = kodion.Context(path='/format/2/')
        provider = Provider()
        result = provider.navigate(context)
        list = result[0]
        pass

    def test_library(self):
        context = kodion.Context(path='/library/')
        provider = Provider()
        result = provider.navigate(context)
        kodion.utils.print_items(result[0])
        pass

    def test_root(self):
        context = kodion.Context(path='/')
        provider = Provider()
        result = provider.navigate(context)
        list = result[0]
        self.assertEquals(list[1].get_name(), 'RTL')
        self.assertEquals(list[2].get_name(), 'RTL II')
        self.assertEquals(list[3].get_name(), 'VOX')
        self.assertEquals(list[4].get_name(), 'N-TV')
        self.assertEquals(list[5].get_name(), 'RTL Nitro')
        self.assertEquals(list[6].get_name(), 'Super RTL')
        pass

    def test_rtl_formats(self):
        context = kodion.Context(path='/rtl/formats/')
        provider = Provider()
        result = provider.navigate(context)
        list = result[0]
        self.assertGreater(len(list), 0)
        pass

    def test_rtl_format_gzsz(self):
        context = kodion.Context(path='/rtl/format/1/', params={'seoUrl': 'gzsz'})
        provider = Provider()
        result = provider.navigate(context)
        list = result[0]
        self.assertGreater(len(list), 0)
        pass

    def test_rtl_format_alles_was_zaehlt(self):
        context = kodion.Context(path='/rtl/format/1/', params={'seoUrl': 'alles-was-zaehlt'})
        provider = Provider()
        result = provider.navigate(context)
        list = result[0]
        self.assertGreater(len(list), 0)
        pass

    def test_rtl_format_alles_was_zaehlt_per_year_and_month(self):
        now_date = datetime.datetime.now()
        year = now_date.year
        month = now_date.month

        start_date = '%d-01-01 00:00:00' % year
        end_date = now_date.strftime('%Y-%m-%d %H:%M:%S')

        context = kodion.Context(path='/rtl/format/1/year/%d/month/%d/' % (year, month),
                                 params={'start': start_date, 'end': end_date})
        provider = Provider()
        result = provider.navigate(context)
        list = result[0]
        self.assertGreater(len(list), 0)
        pass

    pass
