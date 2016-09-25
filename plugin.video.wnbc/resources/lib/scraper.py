# -*- coding: utf-8 -*-
# WNBC Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import sys

qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8 = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = self.getRequest('http://tve-atcnbce.nbcuni.com/live/3/nbce/containers/iPad')
      a = json.loads(html)
      for b in a:
          infoList ={}
          url  = b['assetID']
          name = b['title']
          infoList['Title'] = name
          infoList['TVShowTitle'] = name
          infoList['Plot'] = b['description']
          if (b['seasons'] != []):
              infoList['Season'] = int(b['seasons'][0]['number'])
          fanart = b['images'][0]['images'].get('featured_large_3')
          thumb  = b['images'][0]['images'].get('show_tile')
          mode = 'GE'
          if (b['seasons'] != []):
              if (b['seasons'][0]['hasClips']):
                  mode = 'GC'
          infoList['mediatype'] = 'tvshow'
          contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], url))]
          ilist = self.addMenuItem(name, mode, ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)

  def getAddonCats(self,url,ilist):
      thumb  = xbmc.getInfoLabel('ListItem.Art(thumb)')
      fanart = xbmc.getInfoLabel('ListItem.Art(fanart)')
      ilist = self.addMenuItem('Episodes','GE', ilist, url, thumb, fanart, {}, isFolder=True)
      ilist = self.addMenuItem('Clips','GM', ilist, url, thumb, fanart, {}, isFolder=True)
      return(ilist)

  def getAddonMovies(self,url,ilist):
      xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
      self.getAddonEpisodes(url,ilist,dtype='clip')
      return(ilist)


  def getAddonEpisodes(self,url,ilist, dtype='episode', getFileData = False):
      url = uqp(url)
      html = self.getRequest('http://tve-atcnbce.nbcuni.com/live/3/nbce/containers/%s/iPad' % url)
      a = json.loads(html)
      for b in a['results']:
       if b['subtype'] == dtype:
           infoList = {}
           name = b['title']
           fanart = b['images'][0]['images'].get('featured_large_5')
           thumb  = b['images'][0]['images'].get('episode_tile')
           if not b['requiresAuth']:
               url = b['videoURL']
           else:
               url = b['videoURL'].split('?',1)[0]
               if url == '':
                   continue
               url += '?format=preview'
               html = self.getRequest(url)
               c = json.loads(html)
               catQuoted = urllib.quote(c['categories'][0]['name'])
               pubDateStr = str(c['pubDate'])
               url = 'http://feed.theplatform.com/f/NnzsPC/end_card?range=1-10&byCustomValue={fullEpisode}{true},{showInNavigation}{true}&byCategories='+catQuoted+'&form=json&sort=nbcu:seasonNumber,nbcu:airOrder,pubDate&byPubDate='+pubDateStr+'~'
               html = self.getRequest(url)
               c = json.loads(html)
               if c['entries'] == []:
                   continue
               for d in c['entries'][0]['media$content']:
                   if d['plfile$isDefault']:
                       url = d['plfile$url']+'&manifest=m3u'
                       break
           infoList['Title'] = name
           infoList['TVShowTitle'] = b.get('parentContainerTitle')
           season = b.get('seasonNumber', False)
           if season:
               infoList['Season'] = int(season)
           episode = b.get('episodeNumber', False)
           if episode:
               infoList['Episode'] = int(episode)
           duration = b.get('totalDuration')
           if duration:
               infoList['Duration'] = int(duration/1000)
           airDate = int(b['firstAiredDate'])
           infoList['date'] = datetime.datetime.fromtimestamp(airDate).strftime('%d.%m.%Y')
           airDate = datetime.datetime.fromtimestamp(airDate).strftime('%Y-%m-%d')
           infoList['aired'] = airDate
           infoList['premiered'] = airDate
           infoList['year'] = int(airDate.split('-',1)[0])
           infoList['MPAA'] = b.get('rating')
           infoList['Plot'] = b.get('description')
           infoList['Studio'] = 'NBC'
           infoList['mediatype'] = 'episode'
           if getFileData == False:
               ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
           else:
               ilist.append((infoList.get('Season',''), infoList.get('Episode',''), url))
      return(ilist)

  def doFunction(self, url):
      func = url[0:2]
      url  = url[2:]
      if func == 'AL':
          name  = xbmc.getInfoLabel('ListItem.Title')
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          moviesDir  = xbmc.translatePath(os.path.join(profile,'TV Shows'))
          movieDir  = xbmc.translatePath(os.path.join(moviesDir, name))
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
      json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
      jsonRespond = xbmc.executeJSONRPC(json_cmd)

  def getAddonVideo(self,url):
      if not '&format=redirect' in url:
          html = self.getRequest(url)
          if 'video src="' in html:
              url  = re.compile('video src="(.+?)"', re.DOTALL).search(html).group(1)
          else:
              url  = re.compile('ref src="(.+?)"', re.DOTALL).search(html).group(1)
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
