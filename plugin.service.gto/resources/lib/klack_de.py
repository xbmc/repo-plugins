#!/usr/bin/python

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

        self.enabled = True
        self.baseurl = 'http://www.klack.de'
        self.rssurl = 'http://www.klack.de/xml/tippsRSS.xml'
        self.friendlyname = 'klack.de TV Highlights'
        self.shortname = 'klack.de'
        self.icon = 'klack.png'
        self.selector = '<item>'
        self.detailselector = '<span>Heute</span>'
        self.err404 = 'klackde_dummy.jpg'

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
            self.channel = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(': ')[0]
            self.thumb = re.compile('<img align="left" src="(.+?)"', re.DOTALL).findall(content)[0].replace('150x100.jpg', '500x333.jpg')
            self.thumb = self.checkResource(self.thumb, self.err404)
            self.detailURL = re.compile('<guid isPermaLink="true">(.+?)</guid>', re.DOTALL).findall(content)[0]
            self.title = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(': ')[1]
        except IndexError:
            pass

        try:
            self.extrainfos = re.compile('<description>(.+?)</description>', re.DOTALL).findall(content)[0].split('</a>')[1][:-3]
        except IndexError:
            pass

        try:
            self.date = re.compile('<dc:date>(.+?)</dc:date>', re.DOTALL).findall(content)[0].split('T')[0]
            self.date = '%s.%s.%s' % (self.date[8:2], self.date[5:2], self.date[0:4])
            self.starttime = re.compile('<dc:date>(.+?)</dc:date>', re.DOTALL).findall(content)[0].split('T')[1][0:5]
        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                # Broadcast Info (stop)
                try:
                    self.endtime = re.compile('<span style="color: #d10159!important">(.+?)</span>', re.DOTALL).findall(content)[0].split()[2]
                except IndexError:
                    pass

                # Genre
                self.genre = re.compile('<span>(.+?)</span>', re.DOTALL).findall(content)[3].strip()

                # Cast
                self.cast = ', '.join(re.compile('<td class="actor">(.+?)</td>', re.DOTALL).findall(content))

        except TypeError:
            pass

