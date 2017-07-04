# -*- coding: utf-8 -*-
# Food Networsk Kodi Video Addon
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
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = self.getRequest('http://www.foodnetwork.com/videos/players/food-network-full-episodes.vc.html')
      a = re.compile('<div class="m-MediaBlock o-Capsule__m-MediaBlock m-MediaBlock--playlist">.+?href="(.+?)".+?data-src="(.+?)".+?HeadlineText.+?>(.+?)<.+?AssetInfo">(.+?) .+?</div',re.DOTALL).findall(html)
      for (url, thumb, name, vidcnt) in a:
          name=name.strip()
          fanart  = thumb.split('.rend.',1)[0]
          infoList = {}
          infoList['TVShowTitle'] = name
          infoList['Title'] = name
          infoList['Studio'] = 'Food Network'
          infoList['Plot'] = h.unescape(name)
          infoList['MPAA'] = 'TV-PG'
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      self.defaultVidStream['width']  = 1280
      self.defaultVidStream['height'] = 720
      html = self.getRequest(url)
      vids  = re.compile('"videos"\: \[(.+?)\]',re.DOTALL).search(html).group(1)
      vids = '['+vids+']'
      vids = eval(vids)
      for c in vids:
          b = dict(c)
          url = b['releaseUrl']
          name = h.unescape(b['title'])
          thumb = b['thumbnailUrl']
          if not thumb.startswith('http'):
              thumb = 'http://www.foodnetwork.com'+thumb
          fanart = thumb
          infoList = {}
          infoList['Duration'] = b['length']
          infoList['Title'] = h.unescape(b['title'])
          infoList['Studio'] = b['publisherId']
          infoList['Plot'] = h.unescape(b["description"])
          infoList['TVShowTitle'] = b['showTitle']
          infoList['MPAA'] = 'TV-PG'
          infoList['mediatype'] = 'episode'
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
   html = self.getRequest(uqp(url))
   suburl = None
   subs = re.compile('<textstream src="(.+?)"',re.DOTALL).findall(html)
   for st in subs:
       if '.srt' in st:
           suburl = st
           break
   url = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
   if url is None:
       url, msg = re.compile('<ref src="(.+?)".+?abstract="(.+?)"',re.DOTALL).search(html).groups()
       xbmcgui.Dialog().notification(self.addonName, msg , self.addonIcon, 5000)
       return
   liz = xbmcgui.ListItem(path = url)
   if suburl is not None :
       liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

