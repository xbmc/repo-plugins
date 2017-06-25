import requests
import talk_scraper
import test_util
import timeit
import unittest


class TestTalkScraper(unittest.TestCase):

    def test_get_ted_video(self):
        self.assert_talk_details("http://www.ted.com/talks/ariel_garten_know_thyself_with_a_brain_scanner.html", "https://download.ted.com/talks/ArielGarten_2011X-320k.mp4?dnt", "Know thyself, with a brain scanner", "Ariel Garten", True, True)
        self.assert_talk_details("http://www.ted.com/talks/tom_shannon_s_magnetic_sculpture.html", "https://download.ted.com/talks/TomShannon_2003-320k.mp4?dnt", "Anti-gravity sculpture", "Tom Shannon", True, True);

    def test_get_youtube_video(self):
        self.assert_talk_details("http://www.ted.com/talks/seth_godin_this_is_broken_1.html", "plugin://plugin.video.youtube/?action=play_video&videoid=aNDiHSHYI_c", "This is broken", "Seth Godin", False, True)

    def assert_talk_details(self, talk_url, expected_video_url, expected_title, expected_speaker, expect_plot, expect_json):
        video_url, title, speaker, plot, talk_json = talk_scraper.get(test_util.get_HTML(talk_url))
        self.assertEqual(expected_video_url, video_url)
        self.assertEqual(expected_title, title)
        self.assertEqual(expected_speaker, speaker)

        if (expect_plot):
            self.assertTrue(plot)  # Not None or empty
        else:
            self.assertIsNone(plot)

        if expect_json:
            self.assertTrue(talk_json)  # Not None or empty
        else:
            self.assertIsNone(talk_json)

    def test_get_custom_quality_video_pre_2017(self):
        html = test_util.get_HTML("http://www.ted.com/talks/edith_widder_how_we_found_the_giant_squid.html")
        # Note not customized. Should be a useful fallback if this code goes haywire.
        self.assert_custom_quality_url(html, "320kbps", "https://download.ted.com/talks/EdithWidder_2013-320k.mp4?dnt")

        self.assert_custom_quality_url(html, "64kbps", "https://download.ted.com/talks/EdithWidder_2013-64k.mp4?dnt")
        self.assert_custom_quality_url(html, "180kbps", "https://download.ted.com/talks/EdithWidder_2013-180k.mp4?dnt")
        self.assert_custom_quality_url(html, "450kbps", "https://download.ted.com/talks/EdithWidder_2013-450k.mp4?dnt")
        self.assert_custom_quality_url(html, "600kbps", "https://download.ted.com/talks/EdithWidder_2013-600k.mp4?dnt")
        self.assert_custom_quality_url(html, "950kbps", "https://download.ted.com/talks/EdithWidder_2013-950k.mp4?dnt")
        self.assert_custom_quality_url(html, "1500kbps", "https://download.ted.com/talks/EdithWidder_2013-1500k.mp4?dnt")

        # Fall back to standard URL when custom URL 404s
        self.assert_custom_quality_url(html, "42kbps", "https://download.ted.com/talks/EdithWidder_2013-320k.mp4?dnt")

    def test_get_custom_quality_video_2017(self):
        html = test_util.get_HTML("https://www.ted.com/talks/dan_bricklin_meet_the_inventor_of_the_electronic_spreadsheet")
        # Note not customized. Should be a useful fallback if this code goes haywire.
        self.assert_custom_quality_url(html, "320kbps", "https://download.ted.com/talks/DanBricklin_2016X-320k.mp4?dnt")

        self.assert_custom_quality_url(html, "64kbps", "https://download.ted.com/talks/DanBricklin_2016X-64k.mp4?dnt")
        self.assert_custom_quality_url(html, "180kbps", "https://download.ted.com/talks/DanBricklin_2016X-180k.mp4?dnt")
        self.assert_custom_quality_url(html, "450kbps", "https://download.ted.com/talks/DanBricklin_2016X-450k.mp4?dnt")
        self.assert_custom_quality_url(html, "600kbps", "https://download.ted.com/talks/DanBricklin_2016X-600k.mp4?dnt")
        self.assert_custom_quality_url(html, "950kbps", "https://download.ted.com/talks/DanBricklin_2016X-900k.mp4?dnt")
        self.assert_custom_quality_url(html, "1500kbps", "https://download.ted.com/talks/DanBricklin_2016X-1500k.mp4?dnt")

        # Fall back to standard URL when custom URL 404s
        self.assert_custom_quality_url(html, "42kbps", "https://download.ted.com/talks/DanBricklin_2016X-320k.mp4?dnt")

    def assert_custom_quality_url(self, talk_html, video_quality, expected_video_url):
        video_url, title, speaker, plot, talk_json = talk_scraper.get(talk_html, video_quality)
        self.assertEqual(200, requests.head(video_url, allow_redirects=True).status_code)
        self.assertEqual(expected_video_url, video_url)

    def test_performance(self):
        html = test_util.get_HTML("http://www.ted.com/talks/ariel_garten_know_thyself_with_a_brain_scanner.html")

        def test():
            talk_scraper.get(html);

        t = timeit.Timer(test)
        repeats = 10
        time = t.timeit(repeats)
        print "Extracting talk details took %s seconds per run" % (time / repeats)
        self.assertGreater(4, time)

