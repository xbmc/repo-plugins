# -*- coding: utf-8 -*-
# Popcornflix Kodi Video Addon
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
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      ilist = self.addMenuItem('[COLOR blue]TV Shows[/COLOR]','GS', ilist, 'abc', self.addonIcon, self.addonFanart, {} , isFolder=True)
      html = self.getRequest('https://api.unreel.me/api/assets/5977ea0d32ef9f015341c987/discover?__site=popcornflix&__source=web&onlyEnabledChannels=true')
      a = json.loads(html)
      for b in a['channels']:
          ilist = self.addMenuItem(b.get('name'),'GM', ilist, b.get('channelId')+'/0', b.get('thumbnail'), self.addonFanart, {} , isFolder=True)
      return(ilist)

  def getAddonShows(self,url,ilist):
#      html = self.getRequest('https://api.unreel.me/v2/sites/popcornflix/channels/TV_SHOWS/series?__site=popcornflix&__source=web&index=0&max=30')
      html = self.getRequest('https://api.unreel.me/v2/sites/popcornflix/channels/tv_shows_series/series?__site=popcornflix&__source=web&page=0&pageSize=80')
      a = json.loads(html)
      for b in a['videos']:
          infoList = {}
          url = b.get('uid')
          thumb = b.get('poster')
          fanart = b.get('background')
          name = b['title']
          infoList['Plot'] = b.get('description')
          genres = b.get('genres')
          infoList['Genre'] = ''
          for genre in genres:
              infoList['Genre'] += genre+' '
          infoList['Title'] = name
          rating = b.get('mpaa')
          if rating in ['R','PG-13','PG','G']:
              rating = 'Rated '+rating
          infoList['MPAA']  = rating
          infoList['cast'] = []
          casts = b.get('cast')
          for cast in casts:
              infoList['cast'].append(cast)
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)



  def getAddonEpisodes(self,url,ilist):
      html = self.getRequest('https://api.unreel.me/v2/sites/popcornflix/series/%s/episodes?__site=popcornflix&__source=web' % (url))
      a = json.loads(html)
      for c in a:
        if c is None: continue
        for b in c:
          if b is None:
              continue
          infoList = {}
          url = b.get('uid')
          thumb = b['metadata'].get('thumbnails').get('default')
          if b.get('type') == 'episode': 
              name = b['title']
              infoList['Title'] = name
              infoList['Plot'] = b.get('description')
              if not (b.get('contentDetails') is None):
                  duration = b.get('contentDetails').get('duration')
                  if duration is not None:
                      infoList['duration'] = int(duration)
              infoList['Season'] = b['series'].get('season')
              infoList['Episode'] = b['series'].get('episode')
              infoList['mediatype'] = 'episode'
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)
      return(ilist)

  def doFunction(self, url):
      func = url[0:2]
      url  = url[2:]
      if func == 'AM':
          name  = xbmc.getInfoLabel('ListItem.Title')
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          moviesDir  = xbmc.translatePath(os.path.join(profile,'Movies'))
          movieDir  = xbmc.translatePath(os.path.join(moviesDir, name))
          if not os.path.isdir(movieDir):
              os.makedirs(movieDir)
          strmFile = xbmc.translatePath(os.path.join(movieDir, name+'.strm'))
          with open(strmFile, 'w') as outfile:
              outfile.write('%s?mode=GV&url=%s' %(sys.argv[0], url))
      json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
      jsonRespond = xbmc.executeJSONRPC(json_cmd)


  def getAddonMovies(self,url,ilist):
      pgUrl = url
      self.defaultVidStream['width']  = 960
      self.defaultVidStream['height'] = 540
      html = self.getRequest('https://api.unreel.me/v1/videos/channel/%s?__site=popcornflix&__source=web&max=20&videoSourceCombo=4' % url)
      a = json.loads(html)
      for b in a['videos']:
          infoList = {}
          url = b.get('uid')
          thumb = b['movieData'].get('poster')
          fanart = b['movieData'].get('background')
          if b.get('type') == 'movie': 
              name = b['title']
              infoList['Plot'] = b.get('description')
              genres = b['movieData'].get('genres')
              infoList['Genre'] = ''
              for genre in genres:
                  infoList['Genre'] += genre+' '
              infoList['Title'] = name
              rating = b['movieData'].get('mpaa')
              if rating in ['R','PG-13','PG','G']:
                  rating = 'Rated '+rating
              infoList['MPAA']  = rating
              duration = b.get('contentDetails').get('duration')
              if duration is not None:
                  infoList['duration'] = int(duration)
              infoList['cast'] = []
              casts = b['movieData'].get('cast')
              for cast in casts:
                  infoList['cast'].append(cast)
              infoList['mediatype'] = 'movie'
              contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AM%s)' % (sys.argv[0], url))]
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
          else:
              name = '[COLOR blue]'+name+'[/COLOR]'
              infoList['Title'] = name
              infoList['TVShowTitle'] = name
              infoList['mediatype'] = 'tvshow'
              ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList , isFolder=True)
      if a['hasMore'] == True:
          name = '[COLOR red]Next Page[/COLOR]'
          url = pgUrl.rsplit('/',1)
          url = url[0]+'/'+str(int(url[1])+20)
          ilist = self.addMenuItem(name,'GM', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return(ilist)


  def getAddonVideo(self,url):
      html = self.getRequest('https://api.unreel.me/v2/sites/popcornflix/videos/%s/play-url?__site=popcornflix&__source=web&protocol=https' % (url))
      a = json.loads(html)
      u = a['url']
      liz = xbmcgui.ListItem(path = u)
      infoList ={}
      infoList['mediatype'] = xbmc.getInfoLabel('ListItem.DBTYPE')
      infoList['Title'] = xbmc.getInfoLabel('ListItem.Title')
      infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
      infoList['Year'] = xbmc.getInfoLabel('ListItem.Year')
      infoList['Premiered'] = xbmc.getInfoLabel('Premiered')
      infoList['Plot'] = xbmc.getInfoLabel('ListItem.Plot')
      infoList['Studio'] = xbmc.getInfoLabel('ListItem.Studio')
      infoList['Genre'] = xbmc.getInfoLabel('ListItem.Genre')
      infoList['Duration'] = xbmc.getInfoLabel('ListItem.Duration')
      infoList['MPAA'] = xbmc.getInfoLabel('ListItem.Mpaa')
      infoList['Aired'] = xbmc.getInfoLabel('ListItem.Aired')
      infoList['Season'] = xbmc.getInfoLabel('ListItem.Season')
      infoList['Episode'] = xbmc.getInfoLabel('ListItem.Episode')
      liz.setInfo('video', infoList)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

