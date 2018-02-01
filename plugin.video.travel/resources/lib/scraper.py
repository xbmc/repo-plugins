# -*- coding: utf-8 -*-
# KodiAddon Travel Channel
#
from t1mlib import t1mAddon
import json
import re
import os
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8 = 'utf-8'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = self.getRequest('http://www.travelchannel.com/shows/video/full-episodes')
      a = re.compile('MediaBlock\-\-playlist.+?<a href="(.+?)".+?src="(.+?)".+?HeadlineText.+?>(.+?)<', re.DOTALL).findall(html)
      for url,thumb,name in a:
          plot = name
          if not thumb.startswith('http'):
              thumb = 'http:'+thumb
          fanart = thumb
          infoList = {}
          infoList['TVShowTitle'] = name
          infoList['Title'] = name
          infoList['Studio'] = 'Travel Channel'
          infoList['Plot'] = h.unescape(plot)
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      if not url.startswith('http:'):
          url = 'http:'+url
      html  = self.getRequest(url)
      c = re.compile('class="m\-VideoPlayer__a\-Container".+?x\-config">(.+?)</script>', re.DOTALL).search(html).group(1)
      c = json.loads(c)
      c = c['channels'][0]['videos']
      for b in c:
         url = b['releaseUrl']
         html = self.getRequest(url)
         name = h.unescape(b['title'])
         thumb = 'http://www.travelchannel.com%s' % b['thumbnailUrl']
         fanart = thumb
         infoList = {}
         infoList['Duration'] = b['length']
         infoList['Title'] = name
         infoList['Studio'] = b['publisherId']
         infoList['Plot'] = h.unescape(b["description"])
         infoList['mediatype'] = 'episode'
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html   = self.getRequest(url)
      subs = re.compile('<textstream src="(.+?)"',re.DOTALL).findall(html)
      suburl =''
      for st in subs:
           if '.srt' in st:
               suburl = st
               break
      url   = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
      liz = xbmcgui.ListItem(path=url)
      if suburl != "" :
          liz.setSubtitles([suburl])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
