"""
Grab new talks from RSS feed. Yes we can just add an rss: source in XBMC,
but this allows us a little more power to tweak things how we want them,
so keep it for now.
"""

import urllib2
import time

from datetime import timedelta
try:
    from elementtree.ElementTree import fromstring
except ImportError:
    from xml.etree.ElementTree import fromstring

def get_document(url):
    """
    Return document at given URL.
    """
    usock = urllib2.urlopen(url)
    try:
        return usock.read()
    finally:
        usock.close()


class NewTalksRss:
    """
    Fetches new talks from RSS stream.
    """

    def __init__(self, logger):
        self.logger = logger

    def get_talk_details(self, item):
        """
        Return the details from an RSS <item> tag soup.
        """
        title = item.find('./{http://www.itunes.com/dtds/podcast-1.0.dtd}subtitle').text  # <title> tag has unecessary padding strings
        author = item.find('./{http://www.itunes.com/dtds/podcast-1.0.dtd}author').text
        pic = item.find('./{http://search.yahoo.com/mrss/}thumbnail').get('url')
        duration = item.find('./{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text
        duration = time.strptime(duration, '%H:%M:%S')
        duration_seconds = self.__total_seconds__(timedelta(hours=duration.tm_hour, minutes=duration.tm_min, seconds=duration.tm_sec))
        plot = item.find('./{http://www.itunes.com/dtds/podcast-1.0.dtd}summary').text
        link = item.find('./link').text

        # Get date as XBMC wants it
        pub_date = item.find('./pubDate').text[:-6]  # strptime can't handle timezone info.
        try:
            date = time.strptime(pub_date, "%a, %d %b %Y %H:%M:%S")
        except ValueError, e:
            self.logger("Could not parse date '%s': %s" % (pub_date, e))
            date = time.localtime()
        date = time.strftime("%d.%m.%Y", date)

        return {'title':title, 'author':author, 'thumb':pic, 'plot':plot, 'duration':duration_seconds, 'date':date, 'link':link}

    def __total_seconds__(self, delta):
        try:
            return delta.total_seconds()
        except AttributeError:
            # People still using Python <2.7 201303 :(
            return float((delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 10 ** 6)) / 10 ** 6

    def get_new_talks(self):
        """
        Returns talks as dicts {title:, author:, thumb:, date:, duration:, link:}.
        """
        talksByTitle = {}
        rss = get_document('http://feeds.feedburner.com/tedtalks_video')
        for item in fromstring(rss).findall('channel/item'):
            talk = self.get_talk_details(item)
            talksByTitle[talk['title']] = talk

        return talksByTitle.itervalues()

