# -*- coding: utf-8 -*-
# TVO Kids Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
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
     ilist = self.addMenuItem('Ages 2 to 5', 'GS', ilist, 'preschool', self.addonIcon, self.addonFanart, {} , isFolder=True)
     ilist = self.addMenuItem('Ages 11 and under', 'GS', ilist, 'school-age', self.addonIcon, self.addonFanart, {} , isFolder=True)
     return(ilist)

  def getAddonShows(self,url,ilist):
     html = self.getRequest('https://tvokids.com/%s/videos' % url)
     shows = re.compile('<div class="tvokids-tile.+?href="(.+?)".+?"tile-title">(.+?)<.+?data-lazyload="(.+?)".+?</div', re.DOTALL).findall(html)
     for (url, name, thumb) in shows:
         name = name.strip()
         name = h.unescape(name).replace('&#039;',"'")
         fanart = thumb
         infoList = {}
         infoList['title'] = name
         infoList['TVShowTitle'] = name
         infoList['mediatype'] = 'tvshow'
         ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     return(ilist)

  def getAddonEpisodes(self,url,ilist):
     html = self.getRequest('https://tvokids.com%s' % url)
     a = re.compile('tvokids-tile tile-small.+?href="(.+?)".+?class="tile-title">(.+?)<.+?src="(.+?)".+?</div>', re.DOTALL).findall(html)
     for url, name, thumb in a:
         infoList = {}
         name = name.strip()
         name = h.unescape(name).replace('&#039;',"'")
         infoList['Title'] = name
         infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
         thumb = xbmc.getInfoLabel('ListItem.Thumb')
         fanart = thumb
         infoList['Studio'] = 'TVO Kids'
#         infoList['Plot'] = h.unescape(plot)
         infoList['mediatype'] = 'episode'
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
     return(ilist)
         

  def getAddonVideo(self,url):
     html = self.getRequest('https://tvokids.com%s' % (url))
     vid = re.compile('data-video-id="(.+?)"', re.DOTALL).search(html).group(1)
     u = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=15364602001' % vid
     liz = xbmcgui.ListItem(path=u)
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

