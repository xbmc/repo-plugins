# -*- coding: utf-8 -*-
# Food Network Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
import urllib2
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8  = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
     html = self.getRequest('http://www.foodnetwork.ca/shows/')
     html = re.compile('<section class="top-shows">(.+?)</ul>', re.DOTALL).search(html).group(1)
     a = re.compile('href="(.+?)".+?data-src="(.+?)".+?<h3>(.+?)<(.+?)</li>', re.DOTALL).findall(html)
     infoList = {}
     infoList['mediatype'] = 'tvshow'
     for url, thumb, name, extracrap in a:
        if 'Full Episodes' in extracrap:
           name = name.decode(UTF8)
           name = h.unescape(name)
           thumb = thumb.replace(' ','%20') #really? who the fuck puts spaces in urls?
           fanart = thumb
           ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
    self.defaultVidStream['width']  = 960
    self.defaultVidStream['height'] = 540
    if not url.endswith('/video/'):
        if url.endswith('/'):
           url += 'video/'
        else:
           url += '/video/'
    if not url.startswith('http:'):
        url = 'http://www.foodnetwork.ca'+url
    html = self.getRequest(url)
    endpoint, geurl = re.compile('endpoint: "(.+?)".+?categories: "(.+?)"', re.DOTALL).search(html).groups()
    url = 'http:%s?byCategories=%s&form=cjson&count=true&startIndex=1&endIndex=150&fields=id,content,defaultThumbnailUrl,title,description,:show,:season,:episode,pubdate,availableDate,:clipType,restrictionID,:allowHTML5&sort=pubDate|desc&callback=' % (endpoint, geurl)

    html = self.getRequest(url)
    a = json.loads(html)['entries']
    for b in a:
      url = b['content'][0]['url']
      url += '&manifest=m3u'
      name = h.unescape(b['title']).encode(UTF8)
      fanart = b['defaultThumbnailUrl']
      thumb = fanart
      infoList = {}
      infoList['Duration'] = int(b['content'][0]['duration'])
      infoList['Title'] = name
      infoList['Studio'] = b.get('pl1$network')
      infoList['Date'] = datetime.datetime.fromtimestamp(b['pubDate']/1000).strftime('%Y-%m-%d')
      infoList['Aired'] = infoList['Date']
      infoList['Year'] = int(infoList['Date'].split('-',1)[0])
      episode = b.get('pl1$episode')
      if episode is not None and episode.isdigit():
          infoList['Episode'] = int(episode)
      season = b.get('pl1$season')
      if season is not None and season.isdigit():
          infoList['Season']  = int(season)
      else:
          infoList['Season'] = 1
      infoList['Plot'] = h.unescape(b["description"])
      infoList['TVShowTitle'] = b['pl1$show']
      infoList['mediatype'] = 'episode'
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    return(ilist)


  def getAddonVideo(self,url):
     html = self.getRequest(url) #needs proxy
     url = re.compile('video src="(.+?)"', re.DOTALL).search(html).group(1)
     m3ranges = re.compile('_,(.+?),_', re.DOTALL).search(url)
     if m3ranges is not None:
         m3ranges = m3ranges.group(1)
         url = url.replace(m3ranges, 'highest,medium', 1)
     suburl = re.compile('textstream src="(.+?)"', re.DOTALL).search(html)
     html = self.getRequest(url) #needs proxy
     url = re.compile('http(.+?)\n', re.DOTALL).search(html).group(0).strip()
     liz = xbmcgui.ListItem(path = url)
     if suburl is not None: 
         suburl=suburl.group(1).replace('.ttml','.vtt')
         liz.setSubtitles([suburl])
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
