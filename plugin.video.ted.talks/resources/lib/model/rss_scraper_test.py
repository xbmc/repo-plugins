import unittest
from rss_scraper import NewTalksRss
from datetime import datetime
import sys
try:
    from elementtree.ElementTree import fromstring
except ImportError:
    from xml.etree.ElementTree import fromstring

minimal_item = """
<item xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:media="http://search.yahoo.com/mrss/">
  <itunes:author>Dovahkiin</itunes:author>
  <itunes:subtitle>fus ro dah</itunes:subtitle>
  <itunes:summary>Unrelenting Force</itunes:summary>
  <itunes:duration>01:02:03</itunes:duration>
  <guid isPermaLink="false">eng.video.talk.ted.com:830</guid>
  <pubDate>Sat, 04 Feb 2012 08:14:00 +0000</pubDate>
  <media:thumbnail url="invalid://nowhere/nothing.jpg" width="42" height="42" />
  <link>invalid://nowhere/nothing.html</link>
</item>"""

class TestNewTalksRss(unittest.TestCase):

    def setUp(self):
        self.talks = NewTalksRss(lambda x: sys.stdout.write(x))

    def test_get_talk_details_minimal(self):
        details = self.talks.get_talk_details(fromstring(minimal_item))
        expected_details = {
            'author':'Dovahkiin',
            'date':'04.02.2012',
            'link':'invalid://nowhere/nothing.html',
            'thumb':'invalid://nowhere/nothing.jpg',
            'title':'fus ro dah',
            'plot':'Unrelenting Force',
            'duration':3723
        }
        self.assertEqual(expected_details, details)

    def test_get_talk_details_broken_date(self):
        """
        It just seems likely this will break sooner or later, check that we handle gracefully.
        """
        document = fromstring(minimal_item)
        document.find('./pubDate').text = "Sat, 04 02 2012 08:14:00"  # Same date, different formatting
        details = self.talks.get_talk_details(document)
        date_now = datetime.strftime(datetime.now(), "%d.%m.%Y")
        self.assertEqual(date_now, details['date'])

    def test_smoke(self):
        talks = list(self.talks.get_new_talks())
        self.assertTrue(len(talks) > 10)  # If there are less then this than worry?
        talk = talks[0]  # Sanity check on most recent talk
        self.assertEqual(7, len(talk))
        self.assertIsNotNone(talk['author'])
        self.assertIsNotNone(talk['date'])
        self.assertIsNotNone(talk['link'])
        self.assertIsNotNone(talk['thumb'])
        self.assertIsNotNone(talk['title'])
        self.assertIsNotNone(talk['plot'])
        self.assertIsNotNone(talk['duration'])
