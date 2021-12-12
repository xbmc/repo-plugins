"""
Grab new talks from RSS feed. Yes we can just add an rss: source in XBMC,
but this allows us a little more power to tweak things how we want them,
so keep it for now.
"""

from datetime import timedelta
import time
import urllib.request, urllib.error, urllib.parse


try:
    from elementtree.ElementTree import fromstring
except ImportError:
    from xml.etree.ElementTree import fromstring

def get_document(url):
    """
    Return document at given URL.
    """
    usock = urllib.request.urlopen(url)
    try:
        return usock.read()
    finally:
        usock.close()


class NewTalksRss(object):
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

        self.logger('%s = %s' % ('pic', str(pic)), level='debug')

        duration = item.find('./{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text
        duration = time.strptime(duration, '%H:%M:%S')
        duration_seconds = self.__total_seconds__(timedelta(hours=duration.tm_hour, minutes=duration.tm_min, seconds=duration.tm_sec))
        plot = item.find('./{http://www.itunes.com/dtds/podcast-1.0.dtd}summary').text
        link = item.find('./link').text

        # TODO: Upgrade link to user's bitrate, looks like can synthesize URL of form https://download.ted.com/talks/{lastPathSegment.mp4}

        # Get date as XBMC wants it
        pub_date = item.find('./pubDate').text[:-6]  # strptime can't handle timezone info.
        try:
            date = time.strptime(pub_date, "%a, %d %b %Y %H:%M:%S")
        except ValueError as e:
            self.logger("Could not parse date '%s': %s" % (pub_date, e))
            date = time.localtime()
        date = time.strftime("%d.%m.%Y", date)

        return {'title':title, 'author':author, 'thumb':pic, 'plot':plot, 'duration':duration_seconds, 'date':date, 'link':link, 'mediatype': "video"}

    def __total_seconds__(self, delta):
        return delta.total_seconds()

    def get_new_talks(self):
        """
        Returns talks as dicts {title:, author:, thumb:, date:, duration:, link:}.
        """
        talks_by_title = {}
        rss = get_document('http://feeds.feedburner.com/tedtalks_video')
        for item in fromstring(rss).findall('channel/item'):
            talk = self.get_talk_details(item)
            talks_by_title[talk['title']] = talk

        return iter(talks_by_title.values())

