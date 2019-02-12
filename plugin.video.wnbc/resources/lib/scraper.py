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
      html = self.getRequest('https://friendship.nbc.co/v2/graphql?extensions=%7B%22persistedQuery%22:%7B%22namedHash%22:%22page.v5%22%7D%7D&variables=%7B%22name%22:%22allShows%22,%22type%22:%22PAGE%22,%22userId%22:%22-6407222222222222222%22,%22platform%22:%22web%22,%22device%22:%22web%22,%22timeZone%22:%22America%2FNew_York%22%7D')
      a = json.loads(html)
      a = a["data"]["page"]["sections"][0]["data"]["items"][0]["data"]["items"]
      mode = 'GE'
      for b in a:
          b = b["data"]
          name = b['title']
          infoList ={}
          infoList['mediatype'] = 'tvshow'
          infoList['TVShowTitle'] = name
          infoList['Title'] = name
          url = b['urlAlias']
          thumb = b['image']
          fanart = thumb
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
      html = self.getRequest('https://friendship.nbc.co/v2/graphql?extensions=%7B%22persistedQuery%22:%7B%22namedHash%22:%22page.v4%22%7D%7D&variables=%7B%22name%22:%22'+url+'%22,%22type%22:%22SERIES%22,%22userId%22:%22-6407222222222222222%22,%22platform%22:%22web%22,%22device%22:%22web%22%7D')
      a = json.loads(html)
      for b in a['data']['page']['sections']:
       if b['component'] != 'LinksSelectableGroup':
           continue
       for c in b['data']['items']:
         if c['component'] != 'Shelf':
               continue
         for b in c['data']['items']:
           b = b['data']
           if b['programmingType'] != 'Full Episode':
               continue
           infoList = {}
           name = b['secondaryTitle']
           url = 'https://link.theplatform.com/s/NnzsPC/media/guid/2410887629/'+b['mpxGuid']+'?policy=43674&player=NBC.com%20Instance%20of%3A%20rational-player-production&formats=m3u,mpeg4&format=SMIL&embedded=true&tracking=true'
           thumb = b['image']
           fanart = thumb
           infoList['Title'] = name
           season = b.get('seasonNumber', False)
           if season:
               infoList['Season'] = int(season)
           episode = b.get('episodeNumber', False)
           if episode:
               infoList['Episode'] = int(episode)
           duration = b.get('duration', False)
           if duration:
               infoList['Duration'] = int(duration)
           infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
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
          name  = xbmc.getInfoLabel('ListItem.Title').replace(':','')
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
          if 'nbcvodenc' in url:
              html = self.getRequest(url)
              url = re.compile('http(.+?)\n', re.DOTALL).search(html).group(1)
              url = 'http'+url.strip()
          elif not (url.endswith(".mp4") or url.endswith(".flv")):
              headers = self.defaultHeaders.copy()
              headers['User-Agent']= 'Mozilla/5.0 (Linux; U; en-US) AppleWebKit/528.5+ (KHTML, like Gecko, Safari/528.5+) Version/4.0 Kindle/3.0 (screen 600X800; rotate)'
              html = self.getRequest(url, headers=headers)
              urls = re.compile('BANDWIDTH=(.+?),.+?\n(.+?)\n', re.DOTALL).findall(html)
              blast = 0
              for b,u in urls:
                  b = int(b)
                  if blast < b:
                      url = u
                      blast = b
              url += '|User-Agent='+urllib.quote(headers['User-Agent'])
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
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
