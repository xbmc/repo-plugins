import unittest
import urllib2
import ted_talks_scraper


def getHTML(url):
    """
    Trivial method to fetch document from a URL.
    """
    usock = urllib2.urlopen(url)
    try:
        return usock.read()
    finally:
        usock.close()


class TestTedTalks(unittest.TestCase):

    def setUp(self):
        self.ted_talks = ted_talks_scraper.TedTalks(getHTML, None)

    def test_smoke(self):
        self.ted_talks.getVideoDetails("http://www.ted.com/talks/ariel_garten_know_thyself_with_a_brain_scanner.html", "320kbps")
        self.ted_talks.getVideoDetails("http://www.ted.com/talks/bjarke_ingels_hedonistic_sustainability.html", "320kbps")
