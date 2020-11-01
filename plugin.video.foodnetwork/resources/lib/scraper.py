# -*- coding: utf-8 -*-
# Food Network Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import xbmc
import xbmcplugin
import xbmcgui
import sys
import html.parser
import requests

UNESCAPE = html.parser.HTMLParser().unescape


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://www.foodnetwork.com/videos/full-episodes', headers=self.defaultHeaders).text
      a = re.compile('m-MediaBlock--playlist.+?href="(.+?)".+?data-src="(.+?)".+?HeadlineText">(.+?)<.+?</div',re.DOTALL).findall(html)
      for (url, thumb, name) in a:
          name=UNESCAPE(name.strip())
          thumb = ''.join(['https:',thumb])
          fanart  = thumb.split('.rend.',1)[0]
          infoList = {'mediatype':'tvshow',
                      'TVShowTitle': name,
                      'Title': name,
                      'Studio': 'Food Network',
                      'Plot': name}
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      url = ''.join(['https:',url])
      html = requests.get(url, headers=self.defaultHeaders).text
      vids  = re.compile('"videos"\: \[(.+?)\]',re.DOTALL).search(html).group(1)
      vids = ''.join(['[',vids,']'])
      vids = eval(vids)
      for c in vids:
          b = dict(c)
          url = b['releaseUrl']
          name = UNESCAPE(b['title'])
          thumb = b['thumbnailUrl']
          thumb = ''.join(['https://www.foodnetwork.com',thumb])
          fanart = thumb
          infoList = {'mediatype':'episode',
                      'Duration': b.get('length'),
                      'Title': UNESCAPE(b['title']),
                      'Studio': b.get('publisherId'),
                      'Plot': UNESCAPE(b.get("description")),
                      'TVShowTitle': b.get('showTitle')}
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html = requests.get(url, headers=self.defaultHeaders).text
      subs = re.compile('<textstream src="(.+?\.srt)"',re.DOTALL).search(html)
      if subs != None:
          subs = subs.group(1)
      url = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
      if url is None:
          url, msg = re.compile('<ref src="(.+?)".+?abstract="(.+?)"',re.DOTALL).search(html).groups()
          xbmcgui.Dialog().notification(self.addonName, msg)
          return
      liz = xbmcgui.ListItem(path = url, offscreen=True)
      liz.setSubtitles([subs])
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
