import unittest
from search_scraper import Search
import test_util
import timeit
import math

class TestSearchScraper(unittest.TestCase):

    def test_get_talks_for_search_smoke(self):
        scraper = Search(test_util.get_HTML)
        talks_generator = scraper.get_talks_for_search('nuclear', 1)
        remaining_talks = timeit.itertools.islice(talks_generator, 1).next()

        self.assertLess(100, remaining_talks)  # 111 remaining at last check, just make sure we have a decent number remaining.

        talks = list(talks_generator)
        talks_per_page = 12.0
        self.assertEqual(talks_per_page, len(talks))
        # Actually no quarantee this talk is in top ten results. It is today.
        sample_talk = [s for s in talks if s[0] == 'Taylor Wilson: Yup, I built a nuclear fusion reactor'][0]
        self.assertEqual('http://www.ted.com/talks/taylor_wilson_yup_i_built_a_nuclear_fusion_reactor', sample_talk[1])
        self.assertEqual('https://pi.tedcdn.com/r/pe.tedcdn.com/images/ted/fa41dca52e81265b6e20f7ad9647711c1a58efb7_1600x1200.jpg?', sample_talk[2])

        last_page = 1 + int(math.ceil(remaining_talks / talks_per_page))
        talks_generator = scraper.get_talks_for_search('nuclear', last_page)
        remaining_talks = timeit.itertools.islice(talks_generator, 1).next()
        self.assertEqual(0, remaining_talks)
        self.assertLess(0, len(talks))

    def test_get_talks_for_search_decodes_entities(self):
        scraper = Search(test_util.get_HTML)
        talks_generator = scraper.get_talks_for_search('Onora', 1)
        timeit.itertools.islice(talks_generator, 1).next()
        self.assertTrue("Onora O'Neill: What we don't understand about trust" in [t[0] for t in list(talks_generator)])  # "'" is encoded so we need to decode it

    def test_search_for_speaker_name(self):
        scraper = Search(test_util.get_HTML)
        talks_generator = scraper.get_talks_for_search('Christopher Soghoian', 1)  # Random name I haven't heard of
        self.assertEqual(0, timeit.itertools.islice(talks_generator, 1).next())  # Should be uncommon enough to have all results
        list(talks_generator)  # We can generate a talk from each result - no contaminating "profile" results or similar
