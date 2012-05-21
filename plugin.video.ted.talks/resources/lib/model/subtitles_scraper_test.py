import unittest
import subtitles_scraper
import urllib
import tempfile
from BeautifulSoup import MinimalSoup


class TestSubtitlesScraper(unittest.TestCase):

    __sample_languages__ = '%5B%7B%22LanguageCode%22%3A%22sq%22%2C%22OldLanguageCode%22%3A%22alb%22%2C%22Name%22%3A%22Albanian%22%2C%22Description%22%3Anull%2C%22CommunityUrl%22%3Anull%2C%22TranslationCount%22%3A288%2C%22DotsubOnly%22%3Afalse%2C%22CreatedAt%22%3A%222009-05-12+22%3A17%3A26%22%2C%22UpdatedAt%22%3A%222012-03-26+18%3A27%3A09%22%7D%2C%7B%22LanguageCode%22%3A%22ar%22%2C%22OldLanguageCode%22%3A%22ara%22%2C%22Name%22%3A%22Arabic%22%2C%22Description%22%3Anull%2C%22CommunityUrl%22%3Anull%2C%22TranslationCount%22%3A1086%2C%22DotsubOnly%22%3Afalse%2C%22CreatedAt%22%3A%222009-05-12+22%3A17%3A26%22%2C%22UpdatedAt%22%3A%222012-03-26+18%3A26%3A46%22%7D%2C%2C%7B%22LanguageCode%22%3A%22pt-br%22%2C%22OldLanguageCode%22%3A%22por_br%22%2C%22Name%22%3A%22Portuguese%2C+Brazilian%22%2C%22Description%22%3Anull%2C%22CommunityUrl%22%3Anull%2C%22TranslationCount%22%3A1112%2C%22DotsubOnly%22%3Afalse%2C%22CreatedAt%22%3A%222009-05-12+22%3A17%3A27%22%2C%22UpdatedAt%22%3A%222012-05-16+17%3A00%3A07%22%7D%'

    def test_format_time(self):
        self.assertEqual('00:00:00,000', subtitles_scraper.format_time(0))
        self.assertEqual('03:25:45,678', subtitles_scraper.format_time(12345678))

    def test_format_subtitles(self):
        subtitles = [{'content': 'Hello', 'start': 500, 'duration': 2500}, {'content': 'World', 'start': 3000, 'duration': 2500}]
        formatted_subs = subtitles_scraper.format_subtitles(subtitles, 666)
        self.assertEquals('''1
00:00:01,166 --> 00:00:03,666
Hello

2
00:00:03,666 --> 00:00:06,166
World

''', formatted_subs)

    def test_get_languages(self):
        self.assertEquals(['sq', 'ar', 'pt-br'], subtitles_scraper.get_languages(self.__sample_languages__))

    def test_get_flashvars_not_there(self):
        soup = MinimalSoup('<html><head/><body><script>Not much here</script></body></html>')
        try:
            subtitles_scraper.get_flashvars(soup)
            self.fail()
        except Exception, e:
            self.assertEqual('Could not find flashVars', e.args[0])

    def test_get_subtitles(self):
        subs = subtitles_scraper.get_subtitles('1253', 'en')
        self.assertEqual(385, len(subs))

    def test_get_subtitles_bad_language(self):
        subs = subtitles_scraper.get_subtitles('1253', 'panda')
        # Yes, it returns the English subtitles - so we have to parse flashVars to know whether they exist for a particular language
        self.assertEqual('You all know the truth of what I\'m going to say.', subs[0]['content'])

    def test_get_subtitles_for_url(self):
        json_subs = '{"captions":[{"content":"What","startTime":0,"duration":3000,"startOfParagraph":false},{"content":"Began","startTime":3000,"duration":4000,"startOfParagraph":false}]}'
        subs_file = tempfile.NamedTemporaryFile()
        try:
            subs_file.write(json_subs)
            subs_file.flush()
            subs = subtitles_scraper.get_subtitles_for_url(subs_file.name)
        finally:
            subs_file.close()
        self.assertEqual([{'duration': 3000, 'start': 0, 'content': 'What'}, {'duration': 4000, 'start': 3000, 'content': 'Began'}], subs)

    def test_get_subtitles_for_talk_no_languages(self):
        def logger(gnarly, pretty):
            self.gnarly = gnarly
            self.pretty = pretty

        soup = MinimalSoup('<script>flashVars = { } </script>')
        self.assertIsNone(subtitles_scraper.get_subtitles_for_talk(soup, ['fr'], logger))
        self.assertEqual('No subtitles found', self.pretty)
        self.assertEqual('No languages in flashvars.', self.gnarly)

    def test_get_subtitles_for_talk_no_talk_id(self):
        def logger(gnarly, pretty):
            self.gnarly = gnarly
            self.pretty = pretty

        soup = MinimalSoup('<script>flashVars = { languages:"%s" } </script>' % (self.__sample_languages__))
        self.assertIsNone(subtitles_scraper.get_subtitles_for_talk(soup, ['sq'], logger))
        self.assertEqual('Error showing subtitles', self.pretty)
        self.assertEqual('Could not determine talk ID for subtitles.', self.gnarly)

    def test_get_subtitles_for_talk_no_intro_duration(self):
        def logger(gnarly, pretty):
            self.gnarly = gnarly
            self.pretty = pretty

        soup = MinimalSoup('<script>flashVars = { languages:"%s",\nti:1234 } </script>' % (self.__sample_languages__))
        self.assertIsNone(subtitles_scraper.get_subtitles_for_talk(soup, ['sq'], logger))
        self.assertEqual('Error showing subtitles', self.pretty)
        self.assertEqual('Could not determine intro duration for subtitles.', self.gnarly)

    def test_get_subtitles_for_talk_no_language_match(self):
        def logger(gnarly, pretty):
            self.pretty = pretty
            self.gnarly = gnarly

        soup = MinimalSoup('<script>flashVars = { languages:"%s",\nti:1234,\nintroDuration:5678 } </script>' % (self.__sample_languages__))
        self.assertIsNone(subtitles_scraper.get_subtitles_for_talk(soup, ['fr', 'de'], logger))
        self.assertEqual('No subtitles in: fr,de', self.pretty)
        self.assertEqual('No subtitles in: fr,de', self.gnarly)

    def test_real_talk(self):
        soup = MinimalSoup(urllib.urlopen('http://www.ted.com/talks/richard_wilkinson.html').read())
        flashvars = subtitles_scraper.get_flashvars(soup)
        self.assertTrue('languages' in flashvars) # subtitle languages 
        self.assertTrue('15330', flashvars['introDuration']) # TED intro, need to offset subtitles with this
        self.assertEquals('1253', flashvars['ti']) # talk ID

        expected = set(['sq', 'ar', 'hy', 'bg', 'ca', 'zh-cn', 'zh-tw', 'hr', 'cs', 'da', 'nl', 'en', 'fr', 'ka', 'de', 'el', 'he', 'hu', 'id', 'it', 'ja', 'ko', 'fa', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sr', 'sk', 'es', 'th', 'tr', 'uk', 'vi'])
        self.assertEquals(expected, set(subtitles_scraper.get_languages(flashvars['languages'])))

        subs = subtitles_scraper.get_subtitles_for_talk(soup, ['banana', 'fr'], None)
        self.assertTrue(subs.startswith('''1
00:00:15,330 --> 00:00:18,330
Vous savez tous que ce que je vais dire est vrai.

2'''))
