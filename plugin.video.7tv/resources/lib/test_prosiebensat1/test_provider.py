import unittest

from resources.lib import kodimon
from resources.lib import prosiebensat1


class TestProvider(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

        self._provider = prosiebensat1.Provider()
        self._plugin = self._provider.get_plugin()
        pass

    def test_format_next_page(self):
        self._plugin.set_path('/pro7/library/505/')
        kodimon.run(self._provider)
        pass
    
    def test_root(self):
        result = self._provider.navigate('/')
        items = result[0]
        self.assertEqual(len(items), 7)

        options = result[1]
        self.assertEqual(False, options[self._provider.RESULT_CACHE_TO_DISC])
        pass
    
    def test_channel_content(self):
        channel_items = self._provider.navigate('/pro7/')[0]
        self.assertEqual(len(channel_items), 3)
        pass

    def test_channel_content_by_category(self):
        self._plugin.set_path('/pro7/library/')
        kodimon.run(self._provider)
        pass
    
    def test_format_content(self):
        self._plugin.set_path('/pro7/library/277/')
        kodimon.run(self._provider)
        pass
    
    def test_publishing_date(self):
        aired = prosiebensat1.convert_to_aired('2014-09-02T14:45:00+02:00')
        self.assertEqual(aired, '2014-09-02')
        pass

if __name__ == "__main__":
    unittest.main()
    pass