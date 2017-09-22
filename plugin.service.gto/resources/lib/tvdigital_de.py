#!/usr/bin/python

import re
import urllib2
import datetime
from dateutil import parser

RSS_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class Scraper():
    def __init__(self):

        # Properties

        self.enabled = True
        self.baseurl = 'https://www.tvdigital.de'
        self.rssurl = 'https://www.tvdigital.de/rss/tipp/spielfilm/'
        self.friendlyname = 'TV Digital Spielfilm Highlights'
        self.shortname = 'TV Digital'
        self.icon = 'tvd.png'
        self.selector = '<item>'
        self.detailselector = '<div id="main-content" class="clearfix">'
        self.err404 = 'tvd_dummy.jpg'

    def reset(self):

        # Items

        self.channel = ''
        self.title = ''
        self.thumb = False
        self.detailURL = ''
        self.startdate = ''
        self.enddate = ''
        self.runtime = '0'
        self.genre = ''
        self.plot = ''
        self.cast = ''
        self.rating = ''

    def checkResource(self, resource, fallback):
        if not resource: return fallback
        _req = urllib2.Request(resource)
        try:
            _res = urllib2.urlopen(_req, timeout=5)
        except urllib2.HTTPError as e:
            if e.code == '404': return fallback
        except urllib2.URLError as e:
            return fallback
        else:
            return resource
        return fallback

    def scrapeRSS(self, content):

        self.reset()

        try:
            self.channel = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' | ')[2]
            self.detailURL = self.baseurl + re.compile('<guid>(.+?)</guid>', re.DOTALL).findall(content)[0]
            self.title = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' | ')[0][:-3]
        except IndexError:
            pass

        try:
            _ts = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' | ')[1].split(' ', 1)[1]
            self.startdate = datetime.datetime.strftime(parser.parse(_ts), RSS_TIME_FORMAT)
        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                try:
                    self.plot = re.compile('<h2 class="title">Beschreibung</h2>(.+?)</div>', re.DOTALL).findall(content)[0]
                    self.plot = re.compile('<p>(.+?)</p>', re.DOTALL).findall(self.plot)[0]
                    self.genre = re.compile('<div class="genre">(.+?)</div>', re.DOTALL).findall(content)[0].split(' / ')[0]
                except IndexError:
                    pass

                # Cast
                try:
                    castlist = re.compile('<tbody>(.+?)</tbody>', re.DOTALL).findall(content)[0]
                    cast = re.compile('<span itemprop="name">(.+?)</span>', re.DOTALL).findall(castlist)
                    self.cast = ', '.join(cast)
                except IndexError:
                    pass

                # Thumbnail
                try:
                    self.thumb = re.compile('<img itemprop="image" src="(.+?)"', re.DOTALL).findall(content)[0]
                except IndexError:
                    self.thumb = 'image://%s' % (self.err404)

                self.thumb = self.checkResource(self.thumb, self.err404)


                # Broadcast Info (stop)

                _start = parser.parse(self.startdate)
                try:
                    _s = re.compile('<div class="broadcast-time">(.+?)</div>', re.DOTALL).findall(content)[0].split(' - ')[1]
                    _stop = _start.replace(hour=int(_s[0:2]), minute=int(_s[3:5]))
                except IndexError:
                    _stop = _start

                if _start > _stop: _stop += datetime.timedelta(days=1)
                self.enddate = datetime.datetime.strftime(_stop, RSS_TIME_FORMAT)
                self.runtime = str((_stop - _start).seconds / 60)

                # Rating
                try:
                    self.rating = re.compile('<span itemprop="ratingValue">(.+?)</span>', re.DOTALL).findall(content)[0]
                except IndexError:
                    pass
        except TypeError:
            pass

