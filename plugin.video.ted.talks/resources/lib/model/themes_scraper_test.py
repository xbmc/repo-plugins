import unittest
from themes_scraper import Themes
import test_util
import timeit


class TestThemesScraper(unittest.TestCase):

    def test_get_themes(self):
        e_themes = list(Themes(test_util.get_HTML).get_themes())
        self.assertTrue(len(e_themes) > 0)
        sample_theme = [t for t in e_themes if t[0] == 'A Greener Future?'][0]
        self.assertEqual('http://www.ted.com/themes/a_greener_future.html', sample_theme[1])
        self.assertEqual('http://images.ted.com/images/ted/1616_132x99.jpg', sample_theme[2])
        self.assertTrue(isinstance(sample_theme[3], int))

    def test_get_themes_performance(self):
        scraper = Themes(test_util.CachedHTMLProvider().get_HTML)
        # Run once to cache.
        themes = list(scraper.get_themes())
        print "%s themes found" % (len(themes))

        def test():
            self.assertEqual(len(themes), len(list(scraper.get_themes())))

        t = timeit.Timer(test)
        repeats = 2
        time = t.timeit(repeats) / repeats
        print "Getting themes list took %s seconds per run" % (time)
        self.assertGreater(1, time)

    def test_get_talks(self):
        e_talks = list(Themes(test_util.get_HTML).get_talks('http://www.ted.com/themes/a_greener_future.html'))
        self.assertLess(0, len(e_talks))
        self.assertLessEqual(120, len(e_talks))
        sample_talk = [t for t in e_talks if t[0] == "T. Boone Pickens: Let's transform energy -- with natural gas"][0]
        self.assertEqual('http://www.ted.com/talks/t_boone_pickens_let_s_transform_energy_with_natural_gas', sample_talk[1])
        self.assertEqual('http://images.ted.com/images/ted/94552e20361ccd9b4b707563d62b5fec0e3d9813_113x85.jpg', sample_talk[2])

    def test_get_talks_performance(self):
        scraper = Themes(test_util.CachedHTMLProvider().get_HTML)
        # Run once to cache.
        talks = list(scraper.get_talks('http://www.ted.com/themes/a_greener_future.html'))
        print "%s talks for theme found" % (len(talks))

        def test():
            self.assertEqual(len(talks), len(list(scraper.get_talks('http://www.ted.com/themes/a_greener_future.html'))))

        t = timeit.Timer(test)
        repeats = 2
        time = t.timeit(repeats) / repeats
        print "Getting talks for theme took %s seconds per run" % (time)
        self.assertGreater(1, time)
