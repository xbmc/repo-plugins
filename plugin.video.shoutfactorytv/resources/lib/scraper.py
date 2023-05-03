# -*- coding: utf-8 -*-
# Shout Factory TV Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import os
import xbmc
import xbmcplugin
import xbmcgui
import html
import sys
import requests

UNESCAPE = html.unescape


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      ilist = self.addMenuItem(self.addon.getLocalizedString(30004),'GC', ilist, '/film', self.addonIcon, self.addonFanart, {} , isFolder=True)
      ilist = self.addMenuItem(self.addon.getLocalizedString(30005),'GC', ilist, '/tv', self.addonIcon, self.addonFanart, {} , isFolder=True)
      return(ilist)

  def getAddonCats(self,url,ilist):
      html = requests.get(''.join(['https://www.shoutfactorytv.com',url]), headers=self.defaultHeaders).text
      html = re.compile('<div class="dropdown">.+?a href="'+url+'"(.+?)<li><a', re.DOTALL).search(html).group(1)
      cats = re.compile('<a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
      if url =='/film':
          mode = 'GM'
      else:
          mode = 'GS'
      for url, name in cats:
          ilist = self.addMenuItem(name, mode, ilist, url, self.addonIcon, self.addonFanart, {} , isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      html = requests.get(''.join(['https://www.shoutfactorytv.com',url]), headers=self.defaultHeaders).text
      html = re.compile('<div class="tabs-area(.+?)<div class="container add">', re.DOTALL).search(html).group(1)
      epis = re.compile('<a href="(.+?)".+?alt="(.+?)".+?src="(.+?)".+?Season:(.+?)\n.+?Episode:(.+?)\n.+?</li',re.DOTALL).findall(html)
      for url, name, thumb, season, episode in epis:
              url = url.rsplit('/',1)[1]
              infoList = {}
              name = UNESCAPE(name)
              fanart = thumb 
              infoList['Title'] = name
              infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
              infoList['Plot'] = name
              season = season.strip(' ,')
              if season.isdigit():
                  infoList['Season'] = int(season)
              episode = episode.strip()
              if episode.isdigit():
                  infoList['Episode'] = int(episode)
              infoList['mediatype'] = 'episode'
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonMovies(self,url,ilist):
      html = requests.get(''.join(['https://www.shoutfactorytv.com',url]), headers=self.defaultHeaders).text
      movies=re.compile('<div class="img-holder">.+?href="(.+?)".+?alt="(.+?)".+?src="(.+?)"',re.DOTALL).findall(html)
      movies = sorted(movies, key=lambda x: x[1])
      for url, name, thumb in movies:
              url = url.rsplit('/',1)[1]
              fanart = ''.join(['https://image.zype.com/53c0457a69702d4d66040000/',url,'/custom_thumbnail/1080.jpg'])
              infoList = {} 
              name = UNESCAPE(name).replace('?','') 
              infoList['Title'] = name
              infoList['Plot'] = name
              infoList['mediatype'] = 'movie'
              contextMenu = [(self.addon.getLocalizedString(30002),''.join(['RunPlugin(',sys.argv[0],'?mode=AM&url=',url,')']))]
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
      return(ilist)

  def getAddonShows(self,url,ilist):
      html = requests.get(''.join(['https://www.shoutfactorytv.com',url]), headers=self.defaultHeaders).text
      shows=re.compile('<div class="img-holder">.+?href="(.+?)".+?alt="(.+?)".+?src="(.+?)"',re.DOTALL).findall(html)
      shows = sorted(shows, key=lambda x: x[1])
      for url, name, thumb in shows:
              infoList = {}
              fanart = thumb
              name = UNESCAPE(name)
              infoList['Title'] = name
              infoList['TVShowTitle'] = name
              infoList['Plot'] = name
              infoList['mediatype'] = 'tvshow'
              contextMenu = [(self.addon.getLocalizedString(30002),''.join(['RunPlugin(',sys.argv[0],'?mode=AS&url=',url,')']))]
              ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList , isFolder=True, cm=contextMenu)
      return(ilist)



  def getAddonVideo(self,url):
      if not url.startswith('http'):
          url = ''.join(['https://player.zype.com/manifest/',url,'.m3u8?api_key=3PASB80DgKOdJoEdFmyaWw'])
      liz = xbmcgui.ListItem(path = url, offscreen=True)
      liz.setProperty('inputstream','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
