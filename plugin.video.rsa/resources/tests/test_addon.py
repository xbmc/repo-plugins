import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from resources.lib import rsa


class UnitTests(unittest.TestCase):
    def test_scrape_video_list_returns_correct_values(self):
        contents = """
            <div class="video-result">
                <img src="thumb_url">
                <h3>
                    <a href="video_url">Video Title</a></h3>
                    <p></p>
          </div>
        """
        results = rsa.scrape_video_list(contents)
        self.assertTrue(results[0]['title'] == 'Video Title')
        self.assertTrue(results[0]['thumbnail'] == 'thumb_url')

    def test_scrape_video_page_returns_youtube_id_if_available(self):
        contents = """
            <meta name="youtube_url" content="XBmJay_qdNc" />
        """
        youtube_id = rsa.scrape_video_page(contents)
        self.assertTrue(youtube_id == 'XBmJay_qdNc')

    def test_scrape_video_page_returns_youtube_id_when_url_in_meta_tag(self):
        contents = """
            <meta name="youtube_url" content="http://youtu.be/nh-hW0uG_zs" />
        """
        youtube_id = rsa.scrape_video_page(contents)
        self.assertTrue(youtube_id == 'nh-hW0uG_zs')

    def test_scrape_video_page_returns_youtube_id_when_not_in_meta_tag(self):
        contents = """
            <meta name="no_what_i_want" content="" />
            <iframe src="the_wrong_one"></iframe>
            <div id="new_div_1526142">
                <iframe width="560" height="315"
                        src="//www.youtube.com/embed/hIJnEppwN0M"
                        frameborder="0" allowfullscreen>
                </iframe>
            </div>

        """
        youtube_id = rsa.scrape_video_page(contents)
        self.assertTrue(youtube_id == 'hIJnEppwN0M')


if __name__ == '__main__':
    unittest.main()
