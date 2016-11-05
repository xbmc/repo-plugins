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
      html = self.getRequest('http://www.popcornflix.com')
      m  = re.compile('>Home<(.+?)</ul',re.DOTALL).search(html)
      cats = re.compile('<a href="(.+?)">(.+?)</a>',re.DOTALL).findall(html, m.start(1),m.end(1))
      cats = cats[0:2]
      m = re.compile('Genres(.+?)<div class=',re.DOTALL).search(html)
      c2 = re.compile('<a href="(.+?)">(.+?)</a>',re.DOTALL).findall(html, m.start(1),m.end(1))
      cats.extend(c2)
      slist = []
      for url,name in cats:
          if name == 'Espanol':
              break
          if url in slist:
              continue
          slist.append(url)
          name = '[COLOR blue]'+name+'[/COLOR]'
          ilist = self.addMenuItem(name,'GM', ilist, url, self.addonIcon, self.addonFanart, {} , isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      html  = self.getRequest('http://www.popcornflix.com%s' % (url))
      shows=re.compile('<figure>.+?href="(.+?)".+?src="(.+?)".+?title">(.+?)<(.+?)genre">(.+?)<.+?desc">(.+?)<.+?</li>',re.DOTALL).findall(html)
      for url,thumb,name,blob,genre,plot in shows:
          infoList = {} 
          actors, rating, duration = re.compile('actors">(.+?)<.+?rating">(.+?)<.+?duration">(.+?)<',re.DOTALL).search(blob).groups()
          plot = plot.strip()
          infoList['Plot']  = plot.strip()
          infoList['Genre'] = genre
          infoList['Title'] = name
          if rating in ['R','PG-13','PG','G']:
              rating = 'Rated '+rating
          if duration.isdigit():
              infoList['duration'] = int(duration)*60
          infoList['cast'] = actors.split(',')
          url = url.rsplit('/',1)[1]
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
      self.defaultVidStream['width']  = 960
      self.defaultVidStream['height'] = 540
      html  = self.getRequest('http://www.popcornflix.com%s' % (url))
      shows=re.compile('<figure>.+?href="(.+?)".+?src="(.+?)".+?title">(.+?)<(.+?)genre">(.+?)<.+?desc">(.+?)<.+?</li>',re.DOTALL).findall(html)
      slist = []
      shows = sorted(shows, key=lambda x: x[2])
      for url,thumb,name,blob,genre,plot in shows:
          if url in slist:
              continue
          slist.append(url)
          infoList = {} 
          tmp = url.replace('%2f','/')
          if (not tmp.startswith('/series')) and (not tmp.startswith('/tv-shows')):
              infoList = {} 
              actors, rating, duration = re.compile('actors">(.+?)<.+?rating">(.+?)<.+?duration">(.+?)<',re.DOTALL).search(blob).groups()
              plot = plot.strip()
              infoList['Plot'] = plot.strip()
              infoList['Genre'] = genre
              infoList['Title'] = name
              if rating in ['R','PG-13','PG','G']:
                  rating = 'Rated '+rating
              infoList['MPAA']  = rating
              if duration.isdigit():
                  infoList['duration'] = int(duration)*60
              infoList['cast'] = actors.split(',')
              url = url.rsplit('/',1)[1]
              infoList['mediatype'] = 'movie'
              contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AM%s)' % (sys.argv[0], url))]
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False, cm=contextMenu)
          else:
              name = '[COLOR blue]'+name+'[/COLOR]'
              infoList['Title'] = name
              infoList['TVShowTitle'] = name
              infoList['mediatype'] = 'tvshow'
              ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList , isFolder=True)
      return(ilist)


  def getAddonVideo(self,url):
      html = self.getRequest('http://popcornflixv2.device.screenmedia.net/api/videos/%s' % (url))
      a = json.loads(html)
      u = a['movies'][0]['urls']['Web v2 Player']
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

