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
        self.baseurl = 'http://www.klack.de'
        self.rssurl = 'http://www.klack.de/xml/motorsportRSS.xml'
        self.friendlyname = 'klack.de - Motorsport'
        self.shortname = 'klack.de - Motorsport'
        self.icon = 'klack.png'
        self.selector = '<item>'
        self.detailselector = '<table id="content">'
        self.err404 = 'klackde_dummy.jpg'


    def reset(self):
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
            self.channel = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(': ')[0]
            self.detailURL = re.compile('<link>(.+?)</link>', re.DOTALL).findall(content)[0]
            self.title = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(': ')[1]
            self.thumb = re.compile('<img align="left" src="(.+?)"', re.DOTALL).findall(content)[0].replace('150x100.jpg', '500x333.jpg')
        except IndexError:
            pass

        self.thumb = self.checkResource(self.thumb, self.err404)
        try:
            self.plot = re.compile('<description>(.+?)</description>', re.DOTALL).findall(content)[0].split('</a>')[1][:-3]
        except IndexError:
            self.plot = re.compile('<description>(.+?)</description>', re.DOTALL).findall(content)[0].split('<br>')[1][:-3]

        try:
            self.startdate = (re.compile('<dc:date>(.+?)</dc:date>', re.DOTALL).findall(content)[0][0:19]).replace('T', ' ')
        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                # Broadcast Info (stop)

                _start = parser.parse(self.startdate)
                try:
                    _s = re.compile('<span style="color: #d10159!important">(.+?)</span>', re.DOTALL).findall(content)[0].split()[2]
                    _stop = _start.replace(hour=int(_s[0:2]), minute=int(_s[3:5]))
                except IndexError:
                    _stop = _start

                if _start > _stop: _stop += datetime.timedelta(days=1)
                self.enddate = datetime.datetime.strftime(_stop, RSS_TIME_FORMAT)
                self.runtime = str((_stop - _start).seconds / 60)

                # Genre
                try:
                    self.genre = re.compile('<span>(.+?)</span>', re.DOTALL).findall(content)[4].strip()

                    # Cast
                    self.cast = ', '.join(re.compile('<td class="actor">(.+?)</td>', re.DOTALL).findall(content))
                except IndexError:
                    pass

        except TypeError:
            pass

