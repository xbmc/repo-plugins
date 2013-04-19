import unittest
import talk_scraper
import urllib2
import timeit


def get_HTML(url):
    return urllib2.urlopen(url).read()


class TestTalkScraper(unittest.TestCase):

    def test_get_ted_video(self):
        self.assert_talk_details("http://www.ted.com/talks/ariel_garten_know_thyself_with_a_brain_scanner.html", "http://download.ted.com/talks/ArielGarten_2011X.mp4?apikey=TEDDOWNLOAD", "Know thyself, with a brain scanner", "Ariel Garten")

        # No ':' in title. Can't determine speaker.
        self.assert_talk_details("http://www.ted.com/talks/tom_shannon_s_magnetic_sculpture.html", "http://download.ted.com/talks/TomShannon_2003.mp4?apikey=TEDDOWNLOAD", "Tom Shannon's anti-gravity sculpture", "");

    def test_get_youtube_video(self):
        self.assert_talk_details("http://www.ted.com/talks/bjarke_ingels_hedonistic_sustainability.html", "plugin://plugin.video.youtube/?action=play_video&videoid=ogXT_CI7KRU", "Hedonistic sustainability", "Bjarke Ingels")

    def test_get_vimeo_video(self):
        self.assert_talk_details("http://www.ted.com/talks/seth_godin_this_is_broken_1.html", "plugin://plugin.video.vimeo?action=play_video&videoid=4246943", "This is broken", "Seth Godin")

    def assert_talk_details(self, talk_url, expected_video_url, expected_title, expected_speaker):
        video_url, title, speaker, plot = talk_scraper.get(get_HTML(talk_url))
        self.assertEqual(expected_video_url, video_url)
        self.assertEqual(expected_title, title)
        self.assertEqual(expected_speaker, speaker)
        self.assertTrue(plot)  # Not null or empty.

    def test_get_custom_quality_video(self):
        html = get_HTML("http://www.ted.com/talks/edith_widder_how_we_found_the_giant_squid.html")
        # Note not customized. Should be a useful fallback if this code goes haywire.
        self.assert_custom_quality_url(html, "320kbps", "http://download.ted.com/talks/EdithWidder_2013.mp4?apikey=TEDDOWNLOAD")

        self.assert_custom_quality_url(html, "64kbps", "http://download.ted.com/talks/EdithWidder_2013-64k.mp4?apikey=TEDDOWNLOAD")
        self.assert_custom_quality_url(html, "180kbps", "http://download.ted.com/talks/EdithWidder_2013-180k.mp4?apikey=TEDDOWNLOAD")
        self.assert_custom_quality_url(html, "450kbps", "http://download.ted.com/talks/EdithWidder_2013-450k.mp4?apikey=TEDDOWNLOAD")
        self.assert_custom_quality_url(html, "600kbps", "http://download.ted.com/talks/EdithWidder_2013-600k.mp4?apikey=TEDDOWNLOAD")
        self.assert_custom_quality_url(html, "950kbps", "http://download.ted.com/talks/EdithWidder_2013-950k.mp4?apikey=TEDDOWNLOAD")
        self.assert_custom_quality_url(html, "1500kbps", "http://download.ted.com/talks/EdithWidder_2013-1500k.mp4?apikey=TEDDOWNLOAD")

        # Fall back to standard URL when custom URL 404s
        self.assert_custom_quality_url(html, "42kbps", "http://download.ted.com/talks/EdithWidder_2013.mp4?apikey=TEDDOWNLOAD")

    def assert_custom_quality_url(self, talk_html, video_quality, expected_video_url):
        video_url, title, speaker, plot = talk_scraper.get(talk_html, video_quality)
        self.assertEqual(expected_video_url, video_url)

    def test_performance(self):
        html = get_HTML("http://www.ted.com/talks/ariel_garten_know_thyself_with_a_brain_scanner.html")

        def test():
            talk_scraper.get(html);

        t = timeit.Timer(test)
        repeats = 10
        time = t.timeit(repeats)
        print "Extracting talk details took %s seconds per run" % (time / repeats)
        self.assertGreater(4, time)

