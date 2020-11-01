# -*- coding: utf-8 -*-
# KodiAddon Travel Channel
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

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://www.travelchannel.com/shows/video/full-episodes', headers=self.defaultHeaders).text
      a = re.compile('MediaBlock\-\-playlist.+?<a href="(.+?)".+?src="(.+?)".+?data-label>(.+?)<.+?HeadlineText.+?>(.+?)<', re.DOTALL).findall(html)
      for url,thumb,sname,name in a:
          name = UNESCAPE(''.join([name,' - ',sname]))
          plot = name
          thumb = ''.join(['https:',thumb])
          fanart = thumb
          infoList = {'mediatype': 'tvshow',
                      'TVShowTitle': name,
                      'Title' : name,
                      'Studio': 'Travel Channel',
                      'Plot': plot}
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      url = ''.join(['https:',url])
      html = requests.get(url, headers=self.defaultHeaders).text
      c = re.compile('class="m\-VideoPlayer__a\-Container".+?x\-config">(.+?)</script>', re.DOTALL).search(html).group(1)
      c = json.loads(c)
      c = c['channels'][0]['videos']
      for b in c:
         url = b.get('releaseUrl')
         name = b.get('title')
         thumb = ''.join(['https://www.travelchannel.com', b.get('thumbnailUrl')])
         fanart = thumb
         infoList = {'mediatype': 'episode',
                     'Title': name,
                     'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
                     'Studio': b.get('publisherId'),
                     'Duration': b.get('length'),
                     'Plot': UNESCAPE(b.get('description'))}
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html = requests.get(url, headers=self.defaultHeaders).text
      subs = re.compile('<textstream src="(.+?)"',re.DOTALL).findall(html)
      suburl = None
      for st in subs:
           if '.srt' in st:
               suburl = st
               break
      url = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
      liz = xbmcgui.ListItem(path=url)
      liz.setSubtitles([suburl])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
