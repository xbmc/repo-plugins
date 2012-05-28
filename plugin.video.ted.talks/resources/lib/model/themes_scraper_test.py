import unittest
from themes_scraper import Themes
import urllib2

def get_HTML(url):
    return urllib2.urlopen(url).read()

class TestThemesScraper(unittest.TestCase):

    def test_get_themes(self):
        e_themes = list(Themes(get_HTML).get_themes())
        self.assertTrue(len(e_themes) > 0)
        sample_theme = [t for t in e_themes if t[0] == 'A Greener Future?'][0]
        self.assertEqual('http://www.ted.com/themes/a_greener_future.html', sample_theme[1])
        self.assertEqual('http://images.ted.com/images/ted/1616_132x99.jpg', sample_theme[2])

    def test_get_talks(self):
        e_talks = list(Themes(get_HTML).get_talks('http://www.ted.com/themes/a_greener_future.html'))
        self.assertTrue(len(e_talks) > 0)
        sample_talk = [t for t in e_talks if t[0] == "T. Boone Pickens: Let's transform energy -- with natural gas"][0]
        self.assertEqual('http://www.ted.com/talks/t_boone_pickens_let_s_transform_energy_with_natural_gas.html', sample_talk[1])
        self.assertEqual('http://images.ted.com/images/ted/94552e20361ccd9b4b707563d62b5fec0e3d9813_389x292.jpg', sample_talk[2])
