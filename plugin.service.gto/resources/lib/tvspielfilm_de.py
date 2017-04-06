#!/usr/bin/python

import re
import urllib2


class Scraper():
    def __init__(self):

        # Items, do not change!

        self.channel = ''
        self.title = ''
        self.thumb = False
        self.detailURL = ''
        self.starttime = '00:00'
        self.endtime = '00:00'
        self.runtime = '0'
        self.genre = ''
        self.extrainfos = ''
        self.cast = ''
        self.rating = ''


        # Properties

        self.rssurl = 'http://www.tvspielfilm.de/tv-programm/rss/filme.xml'
        self.friendlyname = 'TV Spielfilm Highlights'
        self.shortname = 'TV Spielfilm'
        self.icon = 'tvspielfilm.png'
        self.selector = '<item>'
        self.detailselector = '<section id="content">'
        self.err404 = 'tvspielfilm_dummy.jpg'

    def checkResource(self, resource, fallback):
        if not resource or resource == '': return fallback
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

    # Feed Scraper

    def scrapeRSS(self, content):

        try:
            self.starttime = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' | ')[0]
            self.channel = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' | ')[1]
            self.title = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' | ')[2]
            self.detailURL = re.compile('<link>(.+?)</link>', re.DOTALL).findall(content)[0]

        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                try:
                    self.extrainfos = re.compile('<div class="description-text">(.+?)</p>', re.DOTALL).findall(content)[0].split('<p>')[1]
                    self.genre = re.compile('<span class="genre">(.+?)</span>', re.DOTALL).findall(content)[0].split(', ')[0]
                    endtime = re.compile('<span class="time">(.+?)</span>', re.DOTALL).findall(content)
                    self.endtime = endtime[2].split(' - ')[1]
                except IndexError:
                    pass

                # Cast
                try:
                    castlist = re.compile('<span class="name">(.+?)</span>', re.DOTALL).findall(content)
                    cast = []
                    for _cast in castlist: cast.append(re.sub('<[^>]*>', '', _cast))
                    self.cast = ', '.join(cast)
                except IndexError:
                    pass

                # Thumbnail
                try:
                    self.thumb = re.compile('<div class="gallery-box">(.+?)</div', re.DOTALL).findall(content)[0]
                    self.thumb = re.compile('href="(.+?)"', re.DOTALL).findall(self.thumb)[0]

                except IndexError:
                    self.thumb = 'image://%s' % (self.err404)

                self.thumb = self.checkResource(self.thumb, self.err404)

        except TypeError:
            pass

