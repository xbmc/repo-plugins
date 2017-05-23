"""
Test Feed Parser
"""
import sys
import os
import unittest

# local imports
from feed_parser import FeedParser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

class TestFeedParser(unittest.TestCase):
    """
    Add feed parser test methods to this class
    """


    def setUp(self):
        pass

    def test_feed_burner_parsing_single_item(self):
        """
        Using a static feedburner xml feed
        verifies expected outcome of shows/pagnation
        """

        # load static feeds
        feeds = _feed_data()
        page = 0
        episodes_per_page = 25
        name = 'testFeed'

        feedParser = FeedParser(name, feeds['feed_burner_single_item']['url'], episodes_per_page, page )
        feedParser.parseXML()

        self.assertEquals(feeds['feed_burner_single_item']['episodes'], feedParser.getTotalItems())

        for item in feedParser.getItems():
            self.assertEquals(feeds['feed_burner_single_item']['title'],  feedParser.parseTitle(item))
            self.assertEquals(feeds['feed_burner_single_item']['size'],  feedParser.parseVideoSize(item))
            self.assertEquals(feeds['feed_burner_single_item']['video'],  feedParser.parseVideo(item))
            self.assertEquals(feeds['feed_burner_single_item']['pubDate'],  feedParser.parsePubDate(item))
            self.assertEquals(feeds['feed_burner_single_item']['summary'],  feedParser.parsePlotOutline(item))
            self.assertEquals(feeds['feed_burner_single_item']['description'],  feedParser.parsePlot(item))
            self.assertEquals(feeds['feed_burner_single_item']['director'],  feedParser.parseAuthor(item))
            self.assertEquals(feeds['feed_burner_single_item']['thumbnail'],  feedParser.parseThumbnail(item))

    def test_page_1_feed_burner_pagination_25_per_page(self):
        """
        Using a static feedburner xml verify
        pagination - page 1
        """
        feeds = _feed_data()
        page = 0
        episodes_per_page = 25
        name = 'testPagination25EpisodesPerPage'

        feedParser = FeedParser(name, feeds['feed_burner_pagination_25']['url'], episodes_per_page, page)
        feedParser.parseXML()

        countInfo = self._pagination_loop(feeds, feedParser)

        self.assertEquals(countInfo['beforePageCount'], 0)
        self.assertEquals(countInfo['itemCount'], episodes_per_page)
        self.assertEquals(countInfo['endOfPageCount'], 1)

    def test_page_2_feed_burner_pagination_13_per_page(self):
        """
        Using a static feedburner xml verify
        pagination - page 2
        """
        feeds = _feed_data()
        page = 1
        episodes_per_page = 13
        name = 'testPagination13EpisodesPerPage'

        feedParser = FeedParser(name, feeds['feed_burner_pagination_25']['url'], episodes_per_page, page)
        feedParser.parseXML()

        countInfo = self._pagination_loop(feeds, feedParser)

        self.assertEquals(countInfo['beforePageCount'], episodes_per_page)
        self.assertEquals(countInfo['itemCount'], episodes_per_page)
        self.assertEquals(countInfo['endOfPageCount'], 1)


    def _pagination_loop(self, feeds, feedParser):
        """
        This loop is designed to match the pagination loop
        in default.py as much as possible with exception
        to creating the show data and added separate variables
        to track expected items
        """

        countInfo = {
        'beforePageCount': 0,
        'itemCount': 0,
        'endOfPageCount': 0
        }

        # keep separate tracking of current item
        # to verify against feed parser
        expected_current_item = 0
        for item in feedParser.getItems():
            if feedParser.isItemBeforeCurrentPage():
                countInfo['beforePageCount'] += 1
                feedParser.nextItem()
                expected_current_item += 1
                # Skip this episode since it's before the page starts.
                continue
            if feedParser.isPageEnd():
                countInfo['endOfPageCount'] += 1
                break

            # assert correct order of shows,
            # + 1 to change to base 1 like parseTitle does
            if expected_current_item + 1 in (12, 25, 26, 49,100,135,174):
                    self.assertEquals(feedParser.parseTitle(item),
                     feeds['feed_burner_pagination_25'][expected_current_item + 1])

            expected_current_item +=1
            countInfo['itemCount'] += 1
            feedParser.nextItem()

        return countInfo


def _feed_data():
    """
    Add feed data here for validation
    """
    # current working dir
    cwd = os.getcwd()
    feeds = {}

    # Feeds
    feeds['feed_burner_pagination_25'] = {
        'url': 'file://' + cwd + '/tests/resources/feeds/feedburner.BsdNow.12.31.2016.xml',
        'episodes': 174,
        12: '12. Return of the Cantrill | BSD Now 163',
        25: '25. Sprinkle A Little BSD Into Your Life | BSD Now 150',
        26: '26. A Wild Dexter Appears! | BSD Now 149',
        49: '49. illuminating the future on PC-BSD | BSD Now 126',
        100: '100. From the Foundation (Part 1) | BSD Now 75',
        135: '135. AirPorts &amp; Packages | BSD Now 40',
        174: '174. BGP &amp; BSD | BSD Now 1'
    }

    feeds['feed_burner_single_item'] = {
        'url': 'file://' + cwd + '/tests/resources/feeds/feedburner.BsdNow.single.item.xml',
        'episodes': 1,
        'title' : '1. 2016 highlights | BSD Now 174',
        'size': 1186106641,
        'video': 'http://www.podtrac.com/pts/redirect.mp4/201406.jb-dl.cdn.scaleengine.net/bsdnow/2016/bsd-0174.mp4',
        'pubDate': 'Thu, 29 Dec 2016 10:30:24 -0800',
        'summary': 'Chris takes over and guest hosts the show to give the guys some time off.\n\nWe take a look back at 2016 in BSD, covering the announcement of TrueOS, OpenBSD and FreeBSD releases, a talk with Petra about NetBSD & much more!',
        'description': 'Chris takes over and guest hosts the show to give the guys some time off.\n\nWe take a look back at 2016 in BSD, covering the announcement of TrueOS, OpenBSD and FreeBSD releases, a talk with Petra about NetBSD & much more!',
        'director': 'Jupiter Broadcasting',
        'thumbnail': 'http://www.jupiterbroadcasting.com/wp-content/uploads/2016/12/bsd-0174v2-v.jpg'
    }

    return feeds
