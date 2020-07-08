# -*- coding: utf-8 -*-
# Popcornflix Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import os
import xbmc
import xbmcplugin
import xbmcgui
import sys
import requests


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      ilist = self.addMenuItem(''.join(['[COLOR blue]',self.addon.getLocalizedString(30001),'[/COLOR]']),'GS', ilist, 'abc', self.addonIcon, self.addonFanart, {} , isFolder=True)
      a = requests.get('https://api.unreel.me/api/assets/5977ea0d32ef9f015341c987/discover?__site=popcornflix&__source=web&onlyEnabledChannels=true', headers=self.defaultHeaders).json()
      for b in a['channels']:
          name = b.get('name').title()
          infoList = {'Plot': name}
          ilist = self.addMenuItem(name, 'GM', ilist, ''.join([b.get('channelId'),'/0']), b.get('thumbnail'), self.addonFanart, infoList, isFolder=True)
      return(ilist)

  def getAddonShows(self,url,ilist):
      a = requests.get('https://api.unreel.me/v2/sites/popcornflix/channels/tv_shows_series/series?__site=popcornflix&__source=web&page=0&pageSize=80', headers=self.defaultHeaders).json()
      for b in a['videos']:
          url = b.get('uid')
          thumb = b.get('poster')
          fanart = thumb
          name = b['title']
          infoList = {'mediatype': 'tvshow',
                      'Title': name,
                      'Plot': b.get('description'),
                      'Genre': '',
                      'MPAA': ''.join(['Rated ',b.get('mpaa','Unrated')]),
                      'cast': []}
          [''.join([infoList['Genre'],genre,' ']) for genre in b.get('genres')]
          [infoList['cast'].append(cast) for cast in b.get('cast')]
          contextMenu = [(self.addon.getLocalizedString(30002),''.join(['RunPlugin(',sys.argv[0],'?mode=AS&url=',url,')']))]
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      a = requests.get(''.join(['https://api.unreel.me/v2/sites/popcornflix/series/',url,'/episodes?__site=popcornflix&__source=web']), headers=self.defaultHeaders).json()
      for c in a:
          if c is None:
              continue
          for b in c:
              if b is None:
                  continue
              infoList = {}
              url = b.get('uid')
              thumb = b['metadata']['thumbnails'].get('medium')
              fanart = b['metadata']['thumbnails'].get('maxres')
              if b.get('type') == 'episode':
                  name = b['title']
                  infoList = {'mediatype': 'episode',
                              'Title': name,
                              'Plot': b.get('description'),
                              'duration': b.get('duration',0),
                              'Season': b['series'].get('season'),
                              'Episode': b['series'].get('episode')}
                  ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonMovies(self,url,ilist):
      pgUrl = url
      a = requests.get(''.join(['https://api.unreel.me/v1/videos/channel/',url,'?__site=popcornflix&__source=web&max=20&videoSourceCombo=4']), headers=self.defaultHeaders).json()
      for b in a['videos']:
          url = b.get('uid')
          thumb = b['movieData'].get('poster')
          fanart = b['movieData'].get('background')
          if b.get('type') == 'movie':
              name = b['title']
              infoList = {'mediatype': 'movie',
                          'Title': name,
                          'Plot': b.get('description'),
                          'Genre': '',
                          'MPAA': ''.join(['Rated ',b['movieData'].get('mpaa','Unrated')]),
                          'duration': b['contentDetails'].get('duration',0),
                          'cast': []}
              [''.join([infoList['Genre'],genre,' ']) for genre in b['movieData'].get('genres')]
              [infoList['cast'].append(cast) for cast in b['movieData'].get('cast')]
              contextMenu = [(self.addon.getLocalizedString(30002),''.join(['RunPlugin(',sys.argv[0],'?mode=AM&url=',url,')']))]
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
          else:
              name = ''.join(['[COLOR blue]',name,'[/COLOR]'])
              infoList = {'mediatype':'tvshow',
                          'Title': name,
                          'TVShowTitle': name}
              ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList , isFolder=True)
      if a['hasMore'] == True:
          name = ''.join(['[COLOR red]',self.addon.getLocalizedString(30003),'[/COLOR]'])
          url = pgUrl.rsplit('/',1)
          url = ''.join([url[0],'/',str(int(url[1])+20)])
          ilist = self.addMenuItem(name,'GM', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return(ilist)


  def getAddonVideo(self,url):
      u = requests.get(''.join(['https://api.unreel.me/v2/sites/popcornflix/videos/',url,'/play-url?__site=popcornflix&__source=web&protocol=https'])).json()['url']
      liz = xbmcgui.ListItem(path = u)
      liz.setProperty('inputstream','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
