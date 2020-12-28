from __future__ import absolute_import
import inspect
import os
import sys
import unittest
# Manipulate path first to add stubs
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib")

from resources.lib.api import svt

class TestSvtModule(unittest.TestCase):

  def assertHasContent(self, list):
    if list == None:
      self.fail("List is None")
      return False
    return True

  def assertHasContentStrict(self, list):
    if list == None:
      self.fail("List is None")
    if len(list) < 1:
      self.fail("List is empty")

  def test_get_alphas(self):
    alphas = svt.getAlphas()
    self.assertHasContentStrict(alphas)

  def test_get_video_json(self):
    json_obj = svt.getVideoJSON("ch-svt2")
    self.assertHasContent(json_obj)
  
  def test_get_svt_video_json(self):
    """
    This test is using an actual video ID.
    https://www.svtplay.se/video/22789702/babblarna/sov-gott-babblarna-sasong-5-avsnitt-9
    Might break in Match 4th 2021... 
    """
    svt_id = "ew17zDY"
    video_json = svt.getSvtVideoJson(svt_id)
    self.assertIsNotNone(video_json)
    self.assertTrue(video_json["videoReferences"])

  def test_episode_url_to_show_url(self):
    url = "/video/22132986/some-thing-here/abel-och-fant-sasong-2-kupa-pa-rymmen"
    actual = svt.episodeUrlToShowUrl(url)
    expected = "some-thing-here"
    self.assertEqual(actual, expected)

  def test_single_video_url_to_show_url(self):
    url = "/video/22132986/some-thing-here"
    actual = svt.episodeUrlToShowUrl(url)
    self.assertIsNone(actual)

if __name__ == "__main__":
  unittest.main()
