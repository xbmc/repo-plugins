import unittest
import subtitles_scraper
import urllib
import tempfile
from BeautifulSoup import MinimalSoup


class TestSubtitlesScraper(unittest.TestCase):

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

    def test_real_talk(self):
        soup = MinimalSoup(urllib.urlopen('http://www.ted.com/talks/richard_wilkinson.html').read())
        flashvars = subtitles_scraper.get_flashvars(soup)

        self.assertTrue('15330', flashvars['introDuration']) # TED intro, need to offset subtitles with this
        self.assertEquals('1253', flashvars['ti']) # talk ID

        expected = set(['sq', 'ar', 'hy', 'bg', 'ca', 'zh-cn', 'zh-tw', 'hr', 'cs', 'da', 'nl', 'en', 'fr', 'ka', 'de', 'el', 'he', 'hu', 'id', 'it', 'ja', 'ko', 'fa', 'mk', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sr', 'sk', 'es', 'th', 'tr', 'uk', 'vi'])
        self.assertEquals(expected, set(subtitles_scraper.get_languages(soup)))

        subs = subtitles_scraper.get_subtitles_for_talk(soup, ['banana', 'fr', 'en'], None)
        self.assertTrue(subs.startswith('''1
00:00:15,330 --> 00:00:18,330
Vous savez tous que ce que je vais dire est vrai.

2'''))
