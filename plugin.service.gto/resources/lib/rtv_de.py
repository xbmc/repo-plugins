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

        self.enabled = False
        self.baseurl = 'http://www.rtv.de'
        self.rssurl = 'http://www.rtv.de/rss/filmtipps.xml'
        self.friendlyname = 'rtv Highlights'
        self.shortname = 'rtv'
        self.icon = 'rtv.png'
        self.selector = '<item><pubDate>'
        self.detailselector = '<div id="details">'
        self.err404 = 'broadcastDummy.jpg'

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
            self.channel = re.compile('<description>(.+?),', re.DOTALL).findall(content)[0]
            self.thumb = re.compile('<media:content url="(.+?)" type="image/jpeg"/>', re.DOTALL).findall(content)[0]
            self.thumb = self.checkResource(self.thumb, self.err404)
            self.detailURL = re.compile('<link>(.+?)</link>', re.DOTALL).findall(content)[0]
            self.title = ', '.join(re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' - ')[:-1])
        except IndexError:
            pass

        try:
            self.extrainfos = re.compile('<description>(.+?)</description>', re.DOTALL).findall(content)[0].split('&lt;br/&gt;&lt;br/&gt;')[1]
            self.genre = re.compile('Uhr&lt;br/&gt;(.+?),', re.DOTALL).findall(content)[0]
            self.cast = re.compile('<description>(.+?)</description>', re.DOTALL).findall(content)[0].split('&lt;br/&gt;&lt;br/&gt;')[2][5:]
        except IndexError:
            pass

        try:
            self.date = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(',')[-2].strip()
            self.starttime = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(',')[-1].strip().replace(' Uhr', '')
        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]


                # Thumbnail

                if not self.thumb:
                    try:
                        self.thumb = re.compile('style="background-image:(.+?);">', re.DOTALL).findall(content)[0].split("'")[1]
                    except IndexError:
                        try:
                            self.thumb = re.compile('<img class="kalooga_12730" src="(.+?)"', re.DOTALL).findall(content)[0]
                        except IndexError:
                            self.thumb = 'image://%s' % (self.err404)
                    self.thumb = self.checkResource(self.thumb, self.err404)

                # Broadcast Info (stop)
                try:
                    self.endtime = re.compile('<div class="time">(.+?)</div>', re.DOTALL).findall(content)[0].split()[2]
                except IndexError:
                    pass
                
                # Rating
                try:
                    self.rating = re.compile('<div class="rating editorialRating" onmouseout="Pit.StarRating.reset(this,(.+?))">', re.DOTALL).findall(content)[0].replace("'","")
                except IndexError:
                    pass
        except TypeError:
            pass

