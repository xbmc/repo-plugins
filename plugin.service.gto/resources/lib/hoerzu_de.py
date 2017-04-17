#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import urllib2


class Scraper():
    def __init__(self):

        # Items

        self.channel = ''
        self.title = ''
        self.thumb = False
        self.detailURL = ''
        self.starttime = '00:00'
        self.runtime = '0'
        self.genre = ''
        self.extrainfos = ''
        self.cast = ''
        self.rating = ''

        self.endtime = '00:00'

        # Properties

        self.enabled = False
        self.baseurl = 'https://www.hoerzu.de'
        self.rssurl = 'https://www.hoerzu.de/rss/tipp/spielfilm/'
        self.friendlyname = 'HÖRZU Spielfilm Highlights'
        self.shortname = 'HÖRZU'
        self.icon = 'hoerzu.png'
        self.selector = '<item>'
        self.detailselector = '<div id="main-content">'
        self.err404 = 'hoerzu_dummy.jpg'

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

        try:
            self.channel = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' - ')[0]
            self.genre = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' - ')[1]
            self.detailURL = re.compile('<link>(.+?)</link>', re.DOTALL).findall(content)[0]
            self.title = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(': ')[1]
        except IndexError:
            pass

        try:
            self.starttime = re.compile('<description>(.+?)</description>', re.DOTALL).findall(content)[0][9:14]
            print (self.starttime).encode('utf-8')
        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                try:
                    self.extrainfos = re.compile('<p itemprop="description">(.+?)</p>', re.DOTALL).findall(content)[0]
                except IndexError:
                    pass

                # Cast
                try:
                    castlist = re.compile('<h2>Stars</h2>(.+?)</ul>', re.DOTALL).findall(content)[0]
                    cast = re.compile('<span itemprop="name">(.+?)</span>', re.DOTALL).findall(castlist)
                    self.cast = ', '.join(cast)
                except IndexError:
                    pass

                # Thumbnail
                try:
                    self.thumb = re.compile('<img src="(.+?)" itemprop="image"', re.DOTALL).findall(content)[0]
                except IndexError:
                    self.thumb = 'image://%s' % (self.err404)

                self.thumb = self.checkResource(self.thumb, self.err404)

        except TypeError:
            pass

