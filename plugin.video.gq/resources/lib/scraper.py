# -*- coding: utf-8 -*-
# GQ Magazine Kodi Video Addon
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
GQBASE = 'https://www.gq.com'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
     ALS = self.addon.getLocalizedString
     html = requests.get('https://www.gq.com/video/genres', headers=self.defaultHeaders).text
     a = [(ALS(30001),'/video/new', self.addonFanart),(ALS(30002),'/video/popular', self.addonFanart)]
     a.extend(re.compile('class="cne-nav--drawer__item--categories".+?label="(.+?)".+?href="(.+?)".+?src="(.+?)"' , re.DOTALL).findall(html))
     for name, url, fanart in a:
         name = UNESCAPE(name)
         url = ''.join([UNESCAPE(url),'.js?page=1'])
         infoList = {'mediatype':'tvshow',
                     'TVShowTitle':name,
                     'Title':name,
                     'Studio':'GQ',
                     'Plot':name}
         ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, fanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
     ALS = self.addon.getLocalizedString
     if not url.startswith('http'):
         url = ''.join([GQBASE,url])
     headers = self.defaultHeaders.copy()
     headers['X-Requested-With'] = 'XMLHttpRequest'
     html = requests.get(url,headers = headers).text
     html = html.replace('\\n','').replace('\\','')
     shows = re.compile('<div class="cne-thumb cne-episode-block ".+?src="(.+?)".+?href="(.+?)">(.+?)<.+?class="cne-rollover-description".+?p>(.+?)<',re.DOTALL).findall(html)
     for thumb,url,name,plot in shows:
         plot = plot.strip()
         name = name.strip()
         fanart = thumb
         infoList = {'mediatype': 'episode',
                     'Title': UNESCAPE(name),
                     'Studio': 'GQ',
                     'Plot':UNESCAPE(plot)}                      
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, None, infoList, isFolder=False)
     url = re.compile("'ajaxurl'.+?'(.+?)'",re.DOTALL).search(html)
     if url:
         url = url.group(1)
         name =''.join(['[COLOR blue]',ALS(30005),'[/COLOR]'])
         ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
     return(ilist)


  def getAddonVideo(self,url):
     if not url.startswith('http'):
         url = ''.join([GQBASE,url])
     html = requests.get(url,headers = self.defaultHeaders).text
     url = re.compile('"contentURL".+?="(.+?)"', re.DOTALL).search(html).group(1)
     url = url.replace('low.mp4','high.mp4')
     liz = xbmcgui.ListItem(path = url)
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
