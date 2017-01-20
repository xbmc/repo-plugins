import unittest
from topics_scraper import Topics
import test_util
import timeit


class TestTopicsScraper(unittest.TestCase):

    def test_get_topics(self):
        e_topics = list(Topics(test_util.get_HTML, None).get_topics())
        self.assertTrue(len(e_topics) > 0)
        sample_topic = [t for t in e_topics if t[0] == 'Activism'][0]
        self.assertEqual('activism', sample_topic[1])

    def test_get_topics_performance(self):
        scraper = Topics(test_util.CachedHTMLProvider().get_HTML, None)
        # Run once to cache.
        topics = list(scraper.get_topics())
        print "%s topics found" % (len(topics))

        def test():
            self.assertEqual(len(topics), len(list(scraper.get_topics())))

        t = timeit.Timer(test)
        repeats = 2
        time = t.timeit(repeats) / repeats
        print "Getting topics list took %s seconds per run" % (time)
        self.assertGreater(1, time)

    def test_get_talks(self):
        e_talks = list(Topics(test_util.get_HTML, None).get_talks('activism'))
        self.assertLess(0, len(e_talks))
        self.assertLessEqual(68, len(e_talks))
        sample_talk = [t for t in e_talks if t[0] == 'Walk the earth ... my 17-year vow of silence'][0]
        self.assertEqual('http://www.ted.com/talks/john_francis_walks_the_earth', sample_talk[1])
        self.assertEqual('https://pi.tedcdn.com/r/pe.tedcdn.com/images/ted/58068_800x600.jpg?quality=89&amp;w=320', sample_talk[2])
        self.assertEqual('John Francis', sample_talk[3])

    def test_get_talks_performance(self):
        scraper = Topics(test_util.CachedHTMLProvider().get_HTML, None)
        # Run once to cache.
        talks = list(scraper.get_talks('activism'))
        print "%s talks for topic found" % (len(talks))

        def test():
            self.assertEqual(len(talks), len(list(scraper.get_talks('activism'))))

        t = timeit.Timer(test)
        repeats = 2
        time = t.timeit(repeats) / repeats
        print "Getting talks for topic took %s seconds per run" % (time)
        self.assertGreater(1, time)
