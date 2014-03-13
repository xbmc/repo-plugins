import unittest
import settings

class TestSettings(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.enable_subtitles = settings.enable_subtitles
        self.xbmc_language = settings.xbmc_language
        self.subtitle_language = settings.subtitle_language

    def tearDown(self):
        # This is rubbish. Need to understand how to test Python better.
        settings.enable_subtitles = self.enable_subtitles
        settings.xbmc_language = self.xbmc_language
        settings.subtitle_language = self.subtitle_language
        unittest.TestCase.tearDown(self)

    def test_get_subtitle_languages_disabled(self):
        settings.enable_subtitles = 'false'
        self.assertIsNone(settings.get_subtitle_languages())

    def test_get_subtitle_languages_enabled_standard(self):
        settings.enable_subtitles = 'true'
        settings.xbmc_language = 'Portuguese'
        settings.subtitle_language = "" # Default is "en", if pref unset then XBMC will replace with "".
        self.assertEqual(['pt'], settings.get_subtitle_languages())
        
    def test_get_subtitle_languages_enabled_standard_nomatch(self):
        settings.enable_subtitles = 'true'
        settings.xbmc_language = 'Klingon'
        settings.subtitle_language = ''
        self.assertEqual(None, settings.get_subtitle_languages())
        
    def test_get_subtitle_languages_enabled_custom(self):
        settings.enable_subtitles = 'true'
        settings.subtitle_language = 'en,fr , de ,'
        self.assertEqual(['en', 'fr', 'de'], settings.get_subtitle_languages())
