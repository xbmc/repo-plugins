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
import cookielib

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
    ilist = self.addMenuItem('TV Shows', 'GS', ilist, 'http://www.snagfilms.com/shows/', self.addonIcon, self.addonFanart, {} , isFolder=True)
    html = self.getRequest('http://www.snagfilms.com/categories/')
    html = re.compile('Snag.page.data = (.+?);',re.DOTALL).search(html).group(1)
    a = json.loads(html)
    a = a[5]['data']['items']
    for item in a:
       url  = item['permalink']
       name = item['title']
       thumb  = item['image']
       ilist = self.addMenuItem(name, 'GM', ilist, url, thumb, self.addonFanart, {} , isFolder=True)
    return(ilist)

  def getAddonShows(self,url,ilist):
    html = self.getRequest(url)
    html = re.compile('Snag.page.data = (.+?)];',re.DOTALL).search(html).group(1)
    html += ']'
    a = json.loads(html)
    for b in a[4:]:
      try: c = b['data']['items']
      except: break
      for item in c:
       url  = item['permalink']
       name = item['title']
       thumb  = item['images']['poster']
       fanart = item['images']['landscape']
       infoList ={}
       infoList['TVShowTitle'] = name
       infoList['Title'] = name
       infoList['MPAA'] = item.get('rating',None)
       infoList['Plot'] = h.unescape(item['description'])
       infoList['Season'] = -1
       infoList['Episode'] = item['no_of_episodes']
       infoList['mediatype'] = 'tvshow'
       contextMenu = [(self.addon.getLocalizedString(30003),'XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], url))]
       ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, fanart, infoList , isFolder=True, cm=contextMenu)
    return(ilist)

  def getAddonEpisodes(self,url,ilist, getFileData = False):
      c_url = uqp(url)
      cat_url = c_url.split('#',1)[0]
      if not (cat_url.startswith('http')):
          cat_url = 'http://www.snagfilms.com%s' % cat_url
      cj = cookielib.CookieJar()
      opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
      urllib2.install_opener(opener)
      html = self.getRequest(cat_url)
      x_url = re.compile('rel="canonical" href="(.+?)"',re.DOTALL).search(html).group(1)
      showid = re.compile('data-content-id="(.+?)"',re.DOTALL).search(html)
      if showid is not None:
          showid = showid.group(1)
      else:
          showid = ''
      url3 = 'http://www.snagfilms.com/apis/show/%s' % (showid)
      url2 = 'http://www.snagfilms.com/apis/user/incrementPageView'
      user_data = urllib.urlencode({'url': x_url})
      headers = self.defaultHeaders
      headers['X-Requested-With'] = 'XMLHttpRequest'
      html = self.getRequest(url2, user_data, headers)
      html = self.getRequest(url3, None , headers)
      a = json.loads(html)
      for season in a['show']:
          seasonNumber = int(season.rsplit(' ',1)[1])
          for episodeNumber, show in enumerate(a['show'][season], start=1):
              url = show['id']
              name  = show['title']
              thumb = show['images']['image'][0]['src']
              if ('url=' in thumb):
                  thumb = urllib.unquote_plus(thumb)
                  thumb = thumb.split('url=',1)[1]
              if ('ytimg' in thumb):
                  ytid = thumb.split('/')[4]
                  url = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (ytid)
              infoList ={}
              infoList['Title'] = name
              infoList['Plot']  = h.unescape(show['description'])
              infoList['Genre'] = show['primaryCategory']['title']
              year = show.get('year','')
              if year != '':
                  infoList['Year']  = year
              infoList['MPAA']  = show.get('parentalRating', None)
              infoList['duration'] = int(show['durationMinutes']*60)
              infoList['tagline'] = show['logline']
              infoList['Season'] = seasonNumber
              infoList['Episode'] = episodeNumber
              infoList['mediatype'] = 'episode'
              if getFileData == False:
                  ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)
              else:
                  ilist.append((infoList.get('Season',''), infoList.get('Episode',''), url))
      return(ilist)



  def getAddonMovies(self,url,ilist):
      self.defaultVidStream['width']  = 1280
      self.defaultVidStream['height'] = 720
      url = uqp(url)
      if not url.startswith('http'):
          url = 'http://www.snagfilms.com%s' % url
      html = self.getRequest(url)
      html = re.compile('Snag.page.data = (.+?)];',re.DOTALL).search(html).group(1)
      html = html + ']'
      a = json.loads(html)
      for item in a[1]['data']['items']:
          infoList ={}
          name = h.unescape(item['title'])
          infoList['Title'] = name
          infoList['Plot'] = h.unescape(item['description'])
          infoList['Duration'] = int(item['durationMinutes']*60)
          infoList['MPAA'] = item.get('parentalRating', None)
          year = item.get('year','')
          if year != '':
              infoList['Year'] = int(year)
          url = item['id']
          thumb  = item['images']['poster']
          fanart = item['images']['landscape']
          infoList['mediatype'] = 'movie'
          contextMenu = [(self.addon.getLocalizedString(30003),'XBMC.RunPlugin(%s?mode=DF&url=AM%s)' % (sys.argv[0], url))]
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
      return(ilist)

  def doFunction(self, url):
      func = url[0:2]
      url  = url[2:]
      if func == 'AL':
          name = xbmc.getInfoLabel('ListItem.Title')
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


  def getAddonVideo(self,url):
      html = self.getRequest('http://www.snagfilms.com/embed/player?filmId=%s' % uqp(url))
      url = re.compile('file: "(.+?)"', re.DOTALL).findall(html)
      u = ''
      for x in url: 
          if '6912k' in x: u = x
      if u == '' :
          u = url[-1]
      bspeed = self.addon.getSetting('bitrate')
      if bspeed == '0':
          u = url[0]
      elif bspeed == '2':
          u = url[-1]
      liz = xbmcgui.ListItem(path=u)
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

