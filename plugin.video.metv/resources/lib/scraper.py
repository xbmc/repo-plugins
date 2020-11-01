# -*- coding: utf-8 -*-
# KodiAddon (MeTV)
#
from t1mlib import t1mAddon
import re
import xbmcplugin
import xbmcgui
import sys
import xbmc
import requests

METVBASE = 'https://metv.com'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      pg = requests.get(''.join([METVBASE,'/videos/']), headers=self.defaultHeaders).text
      shows = re.compile('class="section-title"><a href="(.+?)">(.+?)<.+?img src="(.+?)"',re.DOTALL).findall(pg)
      for url, name, thumb in shows:
          name = name.strip()
          fanart = thumb
          infoList = {'mediatype': 'tvshow',
                      'TVShowTitle': name,
                      'Title': name,
                      'Plot': name}
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      self.defaultVidStream['width'] = 720
      self.defaultVidStream['height']= 480
      pg = requests.get(''.join([METVBASE, url]), headers=self.defaultHeaders).text
      episodes = re.compile('class="content-grid-item content-grid-item-3".+?src="(.+?)".+?href="(.+?)">(.+?)<',re.DOTALL).findall(pg)
      for thumb, url, name in episodes:
          if '+ title +' in name:
               continue
          fanart = thumb
          infoList = {'mediatype': 'episode',
                      'TVShowTitle': xbmc.getInfoLabel('ListItem.Title'),
                      'Title': name,
                      'Plot': name}
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      pg = requests.get(''.join([METVBASE, url]), headers=self.defaultHeaders).text
      url = re.compile('class="media-container".+?source src="(.+?)"',re.DOTALL).search(pg).group(1)
      subfile = re.compile('class="media-container".+?kind="captions" src="(.+?)"',re.DOTALL).search(pg)
      liz = xbmcgui.ListItem(path = url, offscreen=True)
      if subfile != None:
          liz.setSubtitles([subfile.group(1)])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
