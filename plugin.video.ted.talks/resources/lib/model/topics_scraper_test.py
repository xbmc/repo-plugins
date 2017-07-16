import timeit
import unittest

from test_util import skip_ted_rate_limited, CachedHTMLProvider
from topics_scraper import Topics


class TestTopicsScraper(unittest.TestCase):

    def setUp(self):
        self.sut = Topics(CachedHTMLProvider().get_HTML, None)

    def test_get_topics(self):
        e_topics = list(self.sut.get_topics())
        self.assertTrue(len(e_topics) > 0)
        sample_topic = [t for t in e_topics if t[0] == 'Activism'][0]
        self.assertEqual('activism', sample_topic[1])

    @skip_ted_rate_limited
    def test_get_topics_performance(self):
        # Run once to cache.
        topics = list(self.sut.get_topics())
        print "%s topics found" % (len(topics))

        def test():
            self.assertEqual(len(topics), len(list(self.sut.get_topics())))

        t = timeit.Timer(test)
        repeats = 2
        time = t.timeit(repeats) / repeats
        print "Getting topics list took %s seconds per run" % (time)
        self.assertGreater(1, time)

    def test_get_talks(self):
        '''
        Ideally a topic over 2 pages. More means that rate limiting is more likely to occur, less and we aren't testing the loop.
        '''
        e_talks = list(self.sut.get_talks('astronomy'))
        self.assertLess(0, len(e_talks))
        self.assertLessEqual(47, len(e_talks))
        sample_talk = [t for t in e_talks if t[0] == 'How radio telescopes show us unseen galaxies'][0]
        self.assertEqual('http://www.ted.com/talks/natasha_hurley_walker_how_radio_telescopes_show_us_unseen_galaxies', sample_talk[1])
        self.assertEqual('https://pi.tedcdn.com/r/pe.tedcdn.com/images/ted/4d92d229412791ad69ddb89fc52aea0079aed8d6_2880x1620.jpg?quality=89&amp;w=320', sample_talk[2])
        self.assertEqual('Natasha Hurley-Walker', sample_talk[3])

    @skip_ted_rate_limited
    def test_get_talks_performance(self):
        # Run once to cache.
        talks = list(self.sut.get_talks('activism'))
        print "%s talks for topic found" % (len(talks))

        def test():
            self.assertEqual(len(talks), len(list(self.sut.get_talks('activism'))))

        t = timeit.Timer(test)
        repeats = 2
        time = t.timeit(repeats) / repeats
        print "Getting talks for topic took %s seconds per run" % (time)
        self.assertGreater(1, time)
