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
import sys

qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'

STUDIO = 'Food Network'


class myAddon(t1mAddon):


  def getAddonMenu(self,url,ilist):
     html = self.getRequest('http://www.foodnetwork.com/videos/players/food-network-full-episodes.vc.html')
     m = re.compile('<section class="multichannel-component">(.+?)</section', re.DOTALL).search(html)
     a = re.compile('<a href="(.+?)".+?src="(.+?)".+?data-max="35">(.+?)<.+?</div', re.DOTALL).findall(html,m.start(1),m.end(1))
     for url,fanart,name in a:
       infoList={}
       name=name.strip().replace(' Full Episodes','')
       thumb  = self.addonIcon
       fanart = fanart.replace('231x130.jpg','480x360.jpg')
       infoList['Title'] = name
       infoList['Studio'] = STUDIO
       ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
        url = uqp(url)
        html  = self.getRequest('http://www.foodnetwork.com%s' % url)
        m  = re.compile('"channels".+?\[(.+?)\]\},', re.DOTALL).search(html)
        a = json.loads(m.group(1))
        for b in a['videos']:
           url     = b['releaseUrl'].split('?',1)[0]+'?MBR=true&format=SMIL&manifest=m3u'
           name    = b['title']
           thumb   = b['thumbnailUrl16x9'].replace('126x71.jpg','480x360.jpg')
           fanart  = thumb
           infoList = {}
           infoList['Duration']    = b['length']
           infoList['Title']       = b['title']
           infoList['Studio']      = STUDIO
           infoList['Plot']        = b["description"]
           infoList['TVShowTitle'] = b["showName"]
           infoList['MPAA']        = 'TV-PG'
           infoList['mediatype']   = 'episode'
           ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
        return(ilist)


  def getAddonVideo(self,url):
   html   = self.getRequest(uqp(url))
   m    = re.compile('<video src="(.+?)"',re.DOTALL).search(html)
   url = m.group(1)
   suburl = None
   subs   = re.compile('<textstream src="(.+?)"',re.DOTALL).findall(html[m.start(1):])
   for st in subs:
      if '.srt' in st:
         suburl = st
         break

   liz = xbmcgui.ListItem(path = url)
   if suburl: liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

