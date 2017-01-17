import unittest
import subtitles_scraper
import urllib
import tempfile
import talk_scraper
import time
import sys


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
        subs = subtitles_scraper.get_subtitles('1253', 'panda', None)
        # It returns the English subtitles :(
        self.assertEqual('You all know the truth of what I\'m going to say.', subs[0]['content'])

    def test_get_languages(self):
        talk_json = self.__get_talk_json__('http://www.ted.com/talks/richard_wilkinson.html')
        expected = set(['ar', 'bg', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'eu', 'fa', 'fr', 'gl', 'he', 'hr', 'hu', 'hy', 'id', 'it', 'ja', 'ka', 'ko', 'mk', 'nb', 'nl', 'pl', 'pt', 'pt-br', 'ro', 'ru', 'sk', 'sq', 'sr', 'sv', 'th', 'tr', 'uk', 'vi', 'zh-cn', 'zh-tw'])
        result = set(subtitles_scraper.__get_languages__(talk_json))
        self.assertEqual(expected, result, msg="New translations are likely to appear; please update the test if so :)\n%s" % (sorted(result)))

    def test_get_subtitles_for_talk(self):
        talk_json = self.__get_talk_json__('http://www.ted.com/talks/richard_wilkinson.html')

        subs = subtitles_scraper.get_subtitles_for_talk(talk_json, ['banana', 'fr', 'en'], None)
        self.assertTrue(subs.startswith('''1
00:00:11,820 --> 00:00:14,820
Vous savez tous que ce que je vais dire est vrai.

2'''))

    def test_get_subtitles_for_newest_talk(self):
        '''
        Newest talk often won't have subtitles when first made available.
        When this is the case we must return None and not throw.
        '''
        from rss_scraper import NewTalksRss
        newest_talk = sorted(NewTalksRss(None).get_new_talks(), key=lambda t: time.strptime(t['date'], "%d.%m.%Y"), reverse=True)[0]

        talk_json = self.__get_talk_json__(newest_talk['link'])
        subs = subtitles_scraper.get_subtitles_for_talk(talk_json, ['en'], lambda m1, m2: sys.stdout.write('%s\n%s' % (m1, m2)))
        if subs:
            print "Newest Talk (%s) has subtitles: test ineffective" % (newest_talk['title'])


    def __get_talk_json__(self, url):
        html = urllib.urlopen(url).read()
        foo, fi, fo, fum, talk_json = talk_scraper.get(html)
        return talk_json
