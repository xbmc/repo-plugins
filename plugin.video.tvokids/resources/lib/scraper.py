# -*- coding: utf-8 -*-
# TVO Kids Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import xbmc
import xbmcplugin
import xbmcgui
import html.parser
import sys
import requests

UNESCAPE = html.parser.HTMLParser().unescape
TVOKBASE = 'https://tvokids.com'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
     ALS = self.addon.getLocalizedString
     slist = [(ALS(30001),'/preschool'),(ALS(30002),'/school-age')]
     for name, url in slist:
         infoList = {'Title': name,
                     'Plot': name}
         ilist = self.addMenuItem(name, 'GS', ilist, url, self.addonIcon, self.addonFanart, infoList , isFolder=True)
     return(ilist)


  def getAddonShows(self,url,ilist):
     html = requests.get(''.join([TVOKBASE,url,'/videos']), headers=self.defaultHeaders).text
     shows = re.compile('<div class="tvokids-tile.+?href="(.+?)".+?"tile-title">(.+?)<.+?data-lazyload="(.+?)".+?</div', re.DOTALL).findall(html)
     for (url, name, thumb) in shows:
         name = name.strip()
         name = UNESCAPE(name).replace('&#039;',"'")
         fanart = thumb
         infoList = {'mediatype':'tvshows',
                     'Title': name,
                     'TVShowTitle':name,
                     'Plot': name}
         ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
     html = requests.get(''.join([TVOKBASE,url]), headers=self.defaultHeaders).text
     a = re.compile('tvokids-tile tile-small.+?href="(.+?)".+?class="tile-title">(.+?)<.+?src="(.+?)".+?</div>', re.DOTALL).findall(html)
     for url, name, thumb in a:
         name = name.strip()
         name = UNESCAPE(name).replace('&#039;',"'")
         thumb = xbmc.getInfoLabel('ListItem.Thumb')
         fanart = thumb
         infoList = {'mediatype':'episode',
                     'Title': name,
                     'TVShowTitle':xbmc.getInfoLabel('ListItem.TVShowTitle'),
                     'Studio': 'TVO Kids',
                     'Plot': name}
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
     return(ilist)
         

  def getAddonVideo(self,url):
     html = requests.get(''.join([TVOKBASE,url]), headers=self.defaultHeaders).text
     vid = re.compile('data-video-id="(.+?)"', re.DOTALL).search(html).group(1)
     u = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=15364602001' % vid
     liz = xbmcgui.ListItem(path=u)
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

