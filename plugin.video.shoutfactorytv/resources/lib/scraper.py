# -*- coding: utf-8 -*-
# Shout Factory TV Kodi Video Addon
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
      ilist = self.addMenuItem('Film','GC', ilist, '/film', self.addonIcon, self.addonFanart, {} , isFolder=True)
      ilist = self.addMenuItem('TV','GC', ilist, '/tv', self.addonIcon, self.addonFanart, {} , isFolder=True)
      return(ilist)

  def getAddonCats(self,url,ilist):
      html = self.getRequest('http://www.shoutfactorytv.com'+url)
      html = re.compile('<div class="dropdown">.+?a href="'+url+'"(.+?)</div', re.DOTALL).search(html).group(1)
      cats = re.compile('<a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
      if url =='/film':
          mode = 'GM'
      else:
          mode = 'GS'
      for url, name in cats:
          ilist = self.addMenuItem(name, mode, ilist, url, self.addonIcon, self.addonFanart, {} , isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist, getFileData = False):
      html = self.getRequest('http://www.shoutfactorytv.com%s' % (url))
      html = re.compile('<div class="tabs-area(.+?)<div class="container add">', re.DOTALL).search(html).group(1)
      epis=re.compile('<a href="(.+?)".+?alt="(.+?)".+?src="(.+?)".+?Season:(.+?)\n.+?Episode:(.+?)\n.+?</li',re.DOTALL).findall(html)
      for url, name, thumb, season, episode in epis:
              url = url.rsplit('/',1)[1]
              infoList = {}
              name = h.unescape(name) 
              infoList['Title'] = name
              infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
              season = season.strip(' ,')
              if season.isdigit():
                  infoList['Season'] = int(season)
              episode = episode.strip()
              if episode.isdigit():
                  infoList['Episode'] = int(episode)
              infoList['mediatype'] = 'episode'
              if not getFileData:
                  contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AM%s)' % (sys.argv[0], url))]
                  ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False, cm=contextMenu)
              else:
                  ilist.append((infoList.get('Season',''), infoList.get('Episode',''), url))
      return(ilist)

  def getAddonMovies(self,url,ilist):
      html  = self.getRequest('http://www.shoutfactorytv.com%s' % (url))
      movies=re.compile('<div class="img-holder">.+?href="(.+?)".+?alt="(.+?)".+?src="(.+?)"',re.DOTALL).findall(html)
      movies = sorted(movies, key=lambda x: x[1])
      for url, name, thumb in movies:
              url = url.rsplit('/',1)[1]
              infoList = {} 
              name = h.unescape(name).replace('?','') 
              infoList['Title'] = name
              infoList['mediatype'] = 'movie'
              contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AM%s)' % (sys.argv[0], url))]
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False, cm=contextMenu)
      return(ilist)

  def getAddonShows(self,url,ilist):
      html = self.getRequest('http://www.shoutfactorytv.com%s' % (url))
      shows=re.compile('<div class="img-holder">.+?href="(.+?)".+?alt="(.+?)".+?src="(.+?)"',re.DOTALL).findall(html)
      shows = sorted(shows, key=lambda x: x[1])
      for url, name, thumb in shows:
              infoList = {}
              name = h.unescape(name)
              infoList['Title'] = name
              infoList['TVShowTitle'] = name
              infoList['mediatype'] = 'tvshow'
              contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], url))]
              ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList , isFolder=True, cm=contextMenu)
      return(ilist)

  def doFunction(self, url):
      func = url[0:2]
      url  = url[2:]
      if func == 'AL':
          name = xbmc.getInfoLabel('ListItem.Title').replace('?','')
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          moviesDir = xbmc.translatePath(os.path.join(profile,'TV Shows'))
          movieDir = xbmc.translatePath(os.path.join(moviesDir, name))
          if not os.path.isdir(movieDir):
              os.makedirs(movieDir)
          ilist = []
          ilist = self.getAddonEpisodes(url, ilist, getFileData = True)
          for season, episode, url in ilist:
              se = 'S%sE%s' % (str(season), str(episode))
              xurl = '%s?mode=GV&url=%s' % (sys.argv[0], qp(url))
              strmFile = xbmc.translatePath(os.path.join(movieDir, se+'.strm'))
              with open(strmFile, 'w') as outfile:
                  outfile.write(xurl)         
      elif func == 'AM':
          name  = xbmc.getInfoLabel('ListItem.Title').replace('?','')
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


  def getAddonVideo(self,url):
      if not url.startswith('http'):
          url = 'https://player.zype.com/manifest/%s.m3u8?api_key=3PASB80DgKOdJoEdFmyaWw' % url
      liz = xbmcgui.ListItem(path = url)
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

