# -*- coding: utf-8 -*-
# WRAL Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import os
from datetime import datetime
import time
import xbmc
import xbmcplugin
import xbmcgui
import html.parser
import sys
import requests

UNESCAPE = html.parser.HTMLParser().unescape
WRALBASE = 'https://www.wral.com'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      ALS = self.addon.getLocalizedString
      shows = []
      infoList = {}
      fanart = self.addonFanart
      shows = [(''.join([WRALBASE,'/news/asset_gallery/13130437/?s=0']), ALS(30001)),
               (''.join([WRALBASE,'/news/video/1082826/']), ALS(30002)),
               (''.join([WRALBASE,'/wral-weathercenter-forecast/1076424/']), ALS(30003)),
               (''.join([WRALBASE,'/live_dualdoppler5000_radar/1068935/']), ALS(30004))]
      for url, name in shows:
          infoList = {'mediatype':'tvshow',
                      'Title': name,
                      'Plot': name,
                      'TVShowTitle': name}
          if 'Stream' in name:
              ilist = self.addMenuItem(name, 'GV', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=False)
          else:
              ilist = self.addMenuItem(name, 'GE', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      ALS = self.addon.getLocalizedString
      html = requests.get(url, headers=self.defaultHeaders).text
      nexturl = re.compile('page btn control next" href="(.+?)"', re.DOTALL).search(html)
      html = re.compile('<ul class="list-featured"(.+?)</ul>', re.DOTALL).search(html).group(1)
      a = re.compile('<a href="(.+?)".+?data-src="(.+?)".+?<strong>(.+?)<.+?<br />(.+?)</.+?"featured_meta">(.+?)<',re.DOTALL).findall(html)
      for url, thumb, name, plot, dtstr in a:
          url = ''.join([WRALBASE,url])
          fanart = thumb
          name = UNESCAPE(name)
          infoList = {'mediatype': 'episode',
                     'Title': name,
                     'plot': UNESCAPE(plot)}
          dtstr = dtstr.upper().replace('.','')
          z = dtstr.split(' ')
          if z[1][1] == ',':
              z[1] = ''.join(['0',z[1]])
          if z[3][1] == ':':
              z[3] = ''.join(['0',z[3]])
          dtstr = ' '.join(z[0:-1])
          aired = datetime(*(time.strptime(dtstr, "%B %d, %Y %I:%S %p")[0:6]))
          infoList['aired'] = aired.strftime("%Y-%m-%d")
          infoList['FirstAired'] = infoList['aired']
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      if nexturl is not None:
          url = nexturl.group(1)
          url = ''.join([WRALBASE,url])
          ilist = self.addMenuItem(''.join(['[COLOR blue]',ALS(30005),'[/COLOR]']),'GE', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return(ilist)


  def getAddonVideo(self,url):
      if not ('.m3u8' in url):
          html = requests.get(url, headers=self.defaultHeaders).text
          url = re.compile('mpegURL"."src"."(.+?)"', re.DOTALL).search(html).group(1)
          url = url.replace('\\','')
      liz = xbmcgui.ListItem(path = url)
      liz.setProperty('inputstream','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
