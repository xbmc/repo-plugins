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


def assertTalk(test_case, talk):
    """
    Assert the given talk has vaguely sane properties.
    """
    test_case.assertEqual(False, talk[0])
    test_case.assertEqual(4, len(talk[1]))
    test_case.assertEqual('playVideo', talk[1]['mode'])
    test_case.assertIsNotNone(talk[1]['Title'])
    test_case.assertIsNotNone(talk[1]['url'])
    test_case.assertIsNotNone(talk[1]['Thumb'])


class TestTedTalks(unittest.TestCase):
    
    def setUp(self):
        self.ted_talks = ted_talks_scraper.TedTalks(getHTML)

    def test_smoke(self):
        self.ted_talks.getVideoDetails("http://www.ted.com/talks/ariel_garten_know_thyself_with_a_brain_scanner.html")
        self.ted_talks.getVideoDetails("http://www.ted.com/talks/bjarke_ingels_hedonistic_sustainability.html")


class TestNewTalks(unittest.TestCase):

    def setUp(self):
        self.new_talks = ted_talks_scraper.NewTalks(getHTML, lambda code: "%s" % code)

    def test_smoke(self):
        new_talks_page_1 = list(self.new_talks.getNewTalks())
        self.assertEqual((True, {'Title':'30020', 'mode':'newTalks', 'url':u'http://www.ted.com/talks/list?page=2'}), new_talks_page_1[0])
        assertTalk(self, new_talks_page_1[1])
        
        new_talks_page_2 = list(self.new_talks.getNewTalks(new_talks_page_1[0][1]['url']))
        self.assertEqual((True, {'Title':'30020', 'mode':'newTalks', 'url':u'http://www.ted.com/talks/list?page=3'}), new_talks_page_2[0])
        self.assertEqual((True, {'Title':'30021', 'mode':'newTalks', 'url':u'http://www.ted.com/talks/list?page=1'}), new_talks_page_2[1])
        assertTalk(self, new_talks_page_2[2])
        
