import os
import os.path
import sys
import unittest

# Manipulate path to include addon source and stubs
sys.path.append("../")
sys.path.append("./lib")

import resources.lib.helper as helper

DEBUG = True


JSON_GOOD = {
      "video": {
        "videoReferences": [
          {
            "url": "http://bar",
            "bitrate": "0",
            "playerType": "ios"
          }
        ],
        "subtitleReferences": [
          {
            "url": ""
          }
        ]
      }
}
JSON_BAD = {
      "video": {
        "videoReferences": [
          {
            "url": "http://foo",
            "bitrate": "0",
            "playerType": "flash"
          }
        ],
        "subtitleReferences": [
          {
            "url": ""
          }
        ]
      }
}

# Stubbing and patching
class MyFile(file):
  name = "NotSet"
  def __init__(self, name):
    self.name = name
  def close(self):
    pass
  def get_name(self):
    return self.name

def stub_urllib_urlopen(url):
  return MyFile(url)

def stub_json_load(file):
  if file.get_name() == "good":
    return JSON_GOOD
  else:
    return JSON_BAD

helper.urllib.urlopen = stub_urllib_urlopen
helper.json.load = stub_json_load

# The real testing begins
class TestHelperModule(unittest.TestCase):

  def test_getVideoUrl(self):
    # Testing a JSON object with an iOS stream
    result = None
    result = helper.getVideoURL(JSON_GOOD)
    self.assertIsNotNone(result)

    # Testing a JSON object without an iOS stream
    result = helper.getVideoURL(JSON_BAD)
    self.assertIsNone(result)



  def test_resolveShowURL(self):
    # Test with a good URL
    show_obj = helper.resolveShowURL("good")
    self.assertIsNotNone(show_obj["videoUrl"])

    show_obj = None

    # Test with a bad URL
    show_obj = helper.resolveShowURL("bad")
    self.assertIsNone(show_obj["videoUrl"])

  def test_prepareFanart(self):
    url = "http://apa/large/"
    expected = "http://apa/extralarge_imax/"
    result = helper.prepareFanart(url, "www.base.org")
    self.assertEqual(expected, result)

  def test_prepareThumb(self):
    url = "http://apa/medium/"
    expected = "http://apa/extralarge/"
    result = helper.prepareThumb(url, "www.base.org")
    self.assertEqual(expected, result)

  def test_prepareThumbLeadingSlashes(self):
    url = "//www.svt.se/apa/medium/"
    expected = "http://www.svt.se/apa/extralarge/"
    result = helper.prepareThumb(url, "www.base.org")
    self.assertEqual(expected, result)

  def test_prepareThumbMissingHttp(self):
    url = "/apa/medium/"
    expected = "http://svtplay.se/apa/extralarge/"
    result = helper.prepareThumb(url, "http://svtplay.se")
    self.assertEqual(expected, result)

  def test_cleanUrl(self):
    url1 = "apa.bepa?cc1=1232"
    url2 = "apa.bepa?alt=123&cc1=434"
    url3 = "apa.bepa"
    result1 = helper.cleanUrl(url1)
    self.assertEqual("apa.bepa?", result1)

    result2 = helper.cleanUrl(url2)
    self.assertEqual("apa.bepa?&alt=123", result2)

    result3 = helper.cleanUrl(url3)
    self.assertEqual("apa.bepa", result3)
