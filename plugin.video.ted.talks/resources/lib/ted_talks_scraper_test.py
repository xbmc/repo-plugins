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


class TestSpeakers(unittest.TestCase):
    
    def setUp(self):
        self.speakers = ted_talks_scraper.Speakers(getHTML, None)
    
    def test_smoke(self):
        speakers = list(self.speakers.getAllSpeakers())
        # 1027 at time of writing, feel free to update
        self.assertTrue(len(speakers) >= 1027)
        # See https://github.com/moreginger/xbmc-plugin.video.ted.talks/issues/14 for the chosen speaker :)
        self.assertTrue('Clifford Stoll' in [s['Title'] for s in speakers])

