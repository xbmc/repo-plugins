import unittest
from speakers_scraper import Speakers
import urllib2
from timeit import itertools

def get_HTML(url):
    return urllib2.urlopen(url).read()

class TestSpeakersScraper(unittest.TestCase):

    def test_get_speakers(self):
        speakers_generator = Speakers(get_HTML).get_speakers_for_letter('E')
        # First value returned is number of speakers, for progress.
        self.assertTrue(itertools.islice(speakers_generator, 1).next() > 0)
        e_speakers = list(speakers_generator)
        self.assertTrue(len(e_speakers) > 0)
        sample_speaker = [s for s in e_speakers if s[0] == 'Kenichi Ebina'][0]
        self.assertEqual('http://www.ted.com/speakers/kenichi_ebina.html', sample_speaker[1])
        self.assertEqual('http://images.ted.com/images/ted/16732_132x99.jpg', sample_speaker[2])
