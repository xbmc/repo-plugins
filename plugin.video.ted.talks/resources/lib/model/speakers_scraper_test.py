import unittest
from speakers_scraper import Speakers
import test_util
import timeit

class TestSpeakersScraper(unittest.TestCase):

    def test_get_speaker_page_count(self):
        count = Speakers(test_util.get_HTML).get_speaker_page_count()
        self.assertLessEqual(64, count)

    def test_get_speakers_for_pages(self):
        speakers_generator = Speakers(test_util.get_HTML).get_speakers_for_pages([1, 2])
        self.assertTrue(timeit.itertools.islice(speakers_generator, 1).next() > 1)

        e_speakers = list(speakers_generator)

        self.assertTrue(len(e_speakers) > 0)
        self.assertEqual(60, len(e_speakers))  # 30 per page

        sample_speaker = [s for s in e_speakers if s[0] == 'Sandra Aamodt'][0]
        self.assertEqual('http://www.ted.com/speakers/sandra_aamodt', sample_speaker[1])
        self.assertEqual('https://pi.tedcdn.com/r/tedcdnpe-a.akamaihd.net/images/ted/4a37c5ed67bf4d4a1cf7aa643607626b44aee0cc_254x191.jpg?', sample_speaker[2])

    def test_get_speakers_performance(self):
        scraper = Speakers(test_util.CachedHTMLProvider().get_HTML)
        # Run once to cache.
        speakers = list(scraper.get_speakers_for_pages([3, 4]))
        print "%s speakers found" % (len(speakers) - 1)  # -1 because we yield #pages first

        def test():
            self.assertEqual(len(speakers), len(list(scraper.get_speakers_for_pages([3, 4]))))

        t = timeit.Timer(test)
        repeats = 2
        time = t.timeit(repeats) / repeats
        print "Getting speakers list took %s seconds per run" % (time)
        self.assertGreater(1, time)

    def test_get_talks_for_speaker(self):
        talks = list(Speakers(test_util.get_HTML).get_talks_for_speaker("http://www.ted.com/speakers/janine_benyus"))
        print "%s talks for speaker found" % (len(talks))
        self.assertLessEqual(0, len(talks))
        self.assertLessEqual(2, len(talks))  # 2 at time of writing

        talk = talks[0]
        self.assertEqual("Biomimicry's surprising lessons from nature's engineers", talk[0])
        self.assertEqual('http://www.ted.com/talks/janine_benyus_shares_nature_s_designs', talk[1])
        self.assertEqual('https://pi.tedcdn.com/r/pe.tedcdn.com/images/ted/12_240x180.jpg?cb=20160511&amp;quality=63&amp;u=&amp;w=512', talk[2])
