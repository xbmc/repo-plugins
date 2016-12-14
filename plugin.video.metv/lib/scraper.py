# -*- coding: utf-8 -*-
# KodiAddon (MeTV)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8 = 'utf-8'
METVBASE = 'http://metv.com%s'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
      pg = self.getRequest(METVBASE % '/videos/')
      shows = re.compile('<div class="content-grid-item video-grid-item.+?href="(.+?)".+?src="(.+?)".+?">(.+?)<.+?</div>',re.DOTALL).findall(pg)
      fanart = self.addonFanart
      for url, thumb, name in shows:
          pg = self.getRequest(METVBASE % url.rsplit('/',1)[0])
          plot = re.compile('<div class="show-synopsis has-airings">(.+?)</div',re.DOTALL).search(pg)
          if plot is None:
              plot = re.compile('<div class="show-synopsis">(.+?)</div',re.DOTALL).search(pg)
          if plot is not None:
              plot = plot.group(1).strip()
          else:
              plot = ''
          name = name.strip()
          infoList = {}
          infoList['TVShowTitle'] = name
          infoList['Title'] = name
          infoList['Plot'] = h.unescape(plot.decode(UTF8))
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
     self.defaultVidStream['width'] = 720
     self.defaultVidStream['height']= 480
     pg = self.getRequest(METVBASE % url)
     showName = re.compile('<div class="show-header".+?<h1>(.+?)</h1>',re.DOTALL).search(pg)
     if showName is not None:
         showName = showName.group(1)
     else:
         showName = ''
     fanart = re.compile('<img class="show-banner" src="(.+?)"',re.DOTALL).search(pg)
     if fanart is not None:
         fanart = fanart.group(1)
     else:
         fanart = self.addonFanart
     m = re.compile('<div id="main-content">(.+?)main-content ',re.DOTALL).search(pg)
     if m is None:
         m = re.compile('<div id="main-content">(.+?)<a href="/video/#">',re.DOTALL).search(pg)
     episodes = re.compile('<div class="category-list-item clearfix">.+?href="(.+?)".+?img src="(.+?)".+?href=.+?>(.+?)<.+?</div>(.+?)<div class="content-meta content-meta-tags">',re.DOTALL).findall(pg,m.start(1),m.end(1))
     for url, thumb, name, plot in episodes:
         plot = plot.replace('<p>','').replace('</p>','').strip()
         thumb = thumb.replace(' ','%20')
         infoList = {}
         infoList['TVShowTitle'] = showName
         infoList['Title'] = name
         infoList['Plot'] = h.unescape(plot)
         infoList['mediatype'] = 'episode'
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
     return(ilist)



  def getAddonVideo(self,url):
      pg = self.getRequest(METVBASE % uqp(url))
      url = re.compile('div class="hlsvideo-wrapper clearfix">.+?src="(.+?)"',re.DOTALL).search(pg).group(1)
      url = url.replace('captions-en.vtt','hls_index.m3u8',1)
      liz = xbmcgui.ListItem(path = url)
      subfile = url.replace('hls_index.m3u8','captions-en.vtt',1)
      liz.setSubtitles([subfile])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
