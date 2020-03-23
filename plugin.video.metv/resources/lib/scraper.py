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
import xbmc

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8 = 'utf-8'
METVBASE = 'https://metv.com%s'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      pg = self.getRequest(METVBASE % '/videos/')
      shows = re.compile('class="section-title"><a href="(.+?)">(.+?)<.+?img src="(.+?)"',re.DOTALL).findall(pg)
      for url, name, thumb in shows:
          name = name.strip()
          fanart = thumb
          infoList = {}
          infoList['TVShowTitle'] = name
          infoList['Title'] = name
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
     self.defaultVidStream['width'] = 720
     self.defaultVidStream['height']= 480
     pg = self.getRequest(METVBASE % url)
     episodes = re.compile('class="content-grid-item content-grid-item-3".+?src="(.+?)".+?href="(.+?)">(.+?)<',re.DOTALL).findall(pg)
     for thumb, url, name in episodes:
         if '+ title +' in name:
              continue
         fanart = thumb
         infoList = {}
         infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.Title')
         infoList['Title'] = name
         infoList['mediatype'] = 'episode'
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
     return(ilist)



  def getAddonVideo(self,url):
      pg = self.getRequest(METVBASE % uqp(url))
      url = re.compile('class="media-container".+?source src="(.+?)"',re.DOTALL).search(pg).group(1)
      subfile = re.compile('class="media-container".+?kind="captions" src="(.+?)"',re.DOTALL).search(pg)
      liz = xbmcgui.ListItem(path = url)
      if subfile != None:
          liz.setSubtitles([subfile.group(1)])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
