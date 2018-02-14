"""
Feed Parser Class
Handles parsing of XML feeds
"""

import requests
from BeautifulSoup import BeautifulStoneSoup

# local imports
import ml_stripper

class FeedParser(object):

    def __init__ (self, show_name, feed_url, episodes_per_page, current_page):
        self.show_name = show_name
        self.feed_url = feed_url
        self.episodes_per_page = episodes_per_page
        self.current_page = current_page
        self.start_feed_item = episodes_per_page * int(current_page)
        self.current_feed_item = 0
        self.total_feed_items = 0
        self.soup = None
        self.items = None

    def parseXML(self):
        """
        Loads feed url and parse
        """
        data = self._readUrl()
        self.soup = self._parseWithSoup(data)
        self.items = self.soup.findAll('item')
        self.total_feed_items = len(self.items)


    def _readUrl(self):
        """
        Loads the XML Feed
        """
        return requests.get(self.feed_url).text

    def _parseWithSoup(self, data):
        """
        Parse the data with BeautifulStoneSoup,
        noting any self-closing tags.
        """
        return BeautifulStoneSoup(
            data,
            convertEntities=BeautifulStoneSoup.XML_ENTITIES,
            selfClosingTags=['media:thumbnail', 'enclosure', 'media:content'])

    def parseTitle(self, item):
        title = str(self.current_feed_item + 1) + '. '
        found_title = item.find('title')
        if found_title:
            title += found_title.string

        return title

    def parseVideo(self, item):
        # Get the video enclosure.
        enclosure = item.find('enclosure')
        if enclosure != None:
            video = enclosure.get('href')
            if video == None:
                video = enclosure.get('url')
            if video == None:
                video = ''

        return video

    def parseVideoSize(self, item):
        enclosure = item.find('enclosure')
        size = enclosure.get('length')
        if size == None:
            size = 0
        return int(size)

    def parsePubDate(self, item):
        date = ''
        pubdate = item.find('pubdate')
        if pubdate != None:
            date = pubdate.string
            # @ToDo: add date parsing here
        return date

    def parsePlotOutline(self, item):
        plot_outline = ''
        summary = item.find('itunes:summary')
        if summary != None:
            plot_outline = ml_stripper.html_to_text(summary.string)
        return plot_outline

    def parsePlot(self, item):
        plot = ''
        description = item.find('description')
        if description != None:
            # strip html from string
            plot = ml_stripper.html_to_text(description.string)

        return plot

    def parseAuthor(self, item):
        author = ''
        parsed_author = item.find('itunes:author')
        if parsed_author != None:
            author = parsed_author.string

        return author

    def parseThumbnail(self, item):
        # Load the self-closing media:thumbnail data.
        thumbnail = None
        mediathumbnail = item.findAll('media:thumbnail')
        if mediathumbnail:
            thumbnail = mediathumbnail[0]['url']
        return thumbnail

    def isItemBeforeCurrentPage(self):
        return self.current_feed_item < self.start_feed_item

    def isPageEnd(self):
        return self.current_feed_item >= self.start_feed_item + self.episodes_per_page

    def nextItem(self):
        self.current_feed_item += 1

    """
    Getters/Setters
    """
    def getParsedXML(self):
        return self.soup

    def getTotalItems(self):
        return self.total_feed_items

    def getItems(self):
        return self.items

    def getPage(self):
        return self.pagination_index

    def getStartIndex(self):
        return self.start_feed_item

    def getCurrentFeedItem(self):
        return self.current_feed_item
