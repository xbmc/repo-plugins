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
UTF8     = 'utf-8'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
     html = self.getRequest('http://www.foodnetwork.ca/video/')
     a = re.compile('ShawVideoDrawer\(.+?drawerTitle: "(.+?)".+?categories: "(.+?)".+?\);',re.DOTALL).findall(html)
     fanart = self.addonFanart
     for i, (name, xurl) in list(enumerate(a[1:], start=1)):
         name = name.decode(UTF8)
         url = xurl
         thumb  = self.addonIcon
         fanart = self.addonFanart
         infoList = {}
         ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
    self.defaultVidStream['width']  = 960
    self.defaultVidStream['height'] = 540
    geurl = uqp(url).replace(' ','%20')
    url = 'http://feed.theplatform.com/f/dtjsEC/hoR6lzBdUZI9?byCategories=%s&form=cjson&count=true&startIndex=1&endIndex=150&fields=id,content,defaultThumbnailUrl,title,description,:show,:season,:episode,pubdate,availableDate,:clipType,restrictionID,:allowHTML5&sort=pubDate|desc&callback=' % geurl
    html  = self.getRequest(url)
    a = json.loads(html)['entries']
    for b in a:
      url     = b['content'][0]['url']
      url    += '&manifest=m3u'
      name    = h.unescape(b['title']).encode(UTF8)
      fanart  = b['defaultThumbnailUrl'].rsplit('_',2)[0]+'.png'
      thumb   = fanart
      infoList = {}
      infoList['Duration']    = int(b['content'][0]['duration'])
      infoList['Title']       = name
      infoList['Studio']      = b.get('pl1$network')
      infoList['Date']        = datetime.datetime.fromtimestamp(b['pubDate']/1000).strftime('%Y-%m-%d')
      infoList['Aired']       = infoList['Date']
      infoList['Year']        = int(infoList['Date'].split('-',1)[0])
      episode = b.get('pl1$episode')
      if episode is not None: infoList['Episode'] = int(episode)
      season = b.get('pl1$season')
      if season is not None: infoList['Season']  = int(season)
      else: infoList['Season']  = 1
      infoList['Plot']        = h.unescape(b["description"])
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



