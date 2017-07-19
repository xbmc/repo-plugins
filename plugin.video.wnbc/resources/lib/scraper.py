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
      html = self.getRequest('http://www.nbc.com/shows/all')
      html = re.compile('<script>PRELOAD=(.+?)</script>', re.DOTALL).search(html).group(1)
      a = json.loads(html)
      a = a['allShows']
      mode = 'GE'
      for b in a:
          name = b['title']
          infoList ={}
          infoList['mediatype'] = 'tvshow'
          infoList['TVShowTitle'] = name
          infoList['Title'] = name
          url = b['urlAlias']
          thumb = b['image']['path']
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
      html = self.getRequest('http://www.nbc.com/%s?nbc=1' % url)
      id = re.compile('"entities"\:\{"(.+?)"', re.DOTALL).search(html)
      if id is not None:
          id = id.group(1)
      else:
          return(ilist)
      html = self.getRequest('https://api.nbc.com/v3.13/videos?fields%5Bvideos%5D=airdate%2Cavailable%2Cdescription%2Centitlement%2Cexpiration%2Cgenre%2Cguid%2CinternalId%2Ckeywords%2Cpermalink%2CrunTime%2Ctitle%2Ctype%2CvChipRating%2CembedUrl%2CseasonNumber%2CepisodeNumber%2CdayPart%2Ccredits&fields%5Bshows%5D=category%2Ccolors%2Cdescription%2CinternalId%2Cname%2Cnavigation%2Creference%2CschemaType%2CshortDescription%2CshortTitle%2CurlAlias%2CshowTag%2Csocial%2CtuneIn%2Ctype&fields%5Bseasons%5D=seasonNumber%2CcontestantTitle&fields%5Bimages%5D=derivatives&include=image%2Cshow%2Cshow.season&derivatives=landscape.widescreen.size350.x1%2Clandscape.widescreen.size640.x1%2Clandscape.widescreen.size640.x2&filter%5Bshow%5D='+id+'&filter%5Bexpiration%5D%5Bvalue%5D=2017-07-07T23%3A00%3A00-04%3A00&filter%5Bexpiration%5D%5Boperator%5D=%3E%3D&filter%5Btype%5D%5Bvalue%5D=Full%20Episode&filter%5Btype%5D%5Boperator%5D=%3D&sort=-airdate')
      a = json.loads(html)
      for b in a['data']:
           infoList = {}
           url = b['attributes'].get('mediaUrl')
           if url == None:
               url = b['attributes'].get('embedUrl')
               url = url.split('guid/',1)[1]
               url = url.split('?',1)[0]
               url = 'http://link.theplatform.com/s/NnzsPC/media/guid/%s?format=preview' % url
           else:
               url += '&format=preview'
           html = self.getRequest(url)
           if html == '':
               continue
           c = json.loads(html)
           name = c['title']
           thumb = c.get('defaultThumbnailUrl')
           fanart = thumb
           url = 'http://link.theplatform.com/s/NnzsPC/media/'+c['mediaPid']+'?policy=43674&player=NBC.com%20Instance%20of%3A%20rational-player-production&formats=m3u,mpeg4&format=SMIL&embedded=true&tracking=true'
           infoList['Title'] = name
           season = c.get('nbcu$seasonNumber', False)
           if season:
               infoList['Season'] = int(season)
           episode = c.get('nbcu$airOrder', False)
           if episode:
               infoList['Episode'] = int(episode)
           duration = c.get('duration')
           if duration:
               infoList['Duration'] = int(duration/1000)
           airDate = c.get('nbcu$airDate')
           if airDate is not None:
               airDate = int(airDate/1000)
               infoList['date'] = datetime.datetime.fromtimestamp(airDate).strftime('%d.%m.%Y')
               airDate = datetime.datetime.fromtimestamp(airDate).strftime('%Y-%m-%d')
               infoList['aired'] = airDate
               infoList['premiered'] = airDate
               infoList['year'] = int(airDate.split('-',1)[0])
           rating = c.get('ratings')
           if (rating is not None) and (rating != []):
               infoList['MPAA'] = rating[0].get('rating')
           infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
           infoList['Plot'] = c.get('description')
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
          else:
              headers = self.defaultHeaders.copy()
              headers['User-Agent']= 'Mozilla/5.0 (Linux; U; en-US) AppleWebKit/528.5+ (KHTML, like Gecko, Safari/528.5+) Version/4.0 Kindle/3.0 (screen 600X800; rotate)'
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
