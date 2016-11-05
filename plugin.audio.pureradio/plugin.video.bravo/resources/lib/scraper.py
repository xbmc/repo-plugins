# -*- coding: utf-8 -*-
# KodiAddon (Bravo TV)
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
BRAVOBASE = 'http://www.bravotv.com%s'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = self.getRequest(BRAVOBASE % '/full-episodes')
      cats = re.compile('<div class="views-row">.+?href="(.+?)".+?title="(.+?)".+?data-src="(.+?)".+?</article',re.DOTALL).findall(html)
      for (url, name, thumb) in cats:
          url = BRAVOBASE % (url)
          name = h.unescape(name.decode('utf-8')).strip()
          fanart = thumb
          infoList = {}
          infoList['TVShowTitle'] = name
          infoList['Title'] = name
          infoList['mediatype'] = 'tvshow'
          contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], url))]
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonEpisodes(self,url,ilist, getFileData = False):
      self.defaultVidStream['width'] = 1920
      self.defaultVidStream['height'] = 1080
      epiHTML = self.getRequest(url)
      (tvshow,  fanart) = re.compile('og:title" content="(.+?)".+?"og:image" content="(.+?)"',re.DOTALL).search(epiHTML).groups()
      epis = re.compile('class="watch__title.+?href="(.+?)".+?</ul>',re.DOTALL).findall(epiHTML)
      for url in epis:
          burl = BRAVOBASE % url
          html = self.getRequest(burl)
          purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html)
          if purl is not None:
              purl = purl.group(1)
          else:
              continue
          purl = 'http:'+purl+'&format=script'
          html = self.getRequest(purl)
          purl = re.compile('name="twitter:player" content="(.+?)"', re.DOTALL).search(html).group(1)
          purl = purl.split('?',1)[0]
          purl = purl.rsplit('/',1)[1]
          purl = 'http://link.theplatform.com/s/HNK2IC/media/%s?format=script' % purl
          url = purl.split('?',1)[0]
          html = self.getRequest(purl)
          a = json.loads(html)
          infoList = {}
          infoList['Date'] = datetime.datetime.fromtimestamp(a['pubDate']/1000).strftime('%Y-%m-%d')
          infoList['Aired'] = infoList['Date']
          infoList['MPAA'] = a['ratings'][0]['rating']
          infoList['Studio'] = a['provider']
          infoList['Genre'] = (a['nbcu$advertisingGenre']).replace('and','/')
          infoList['Episode'] = int(a.get('pl1$episodeNumber',-1))
          infoList['Season'] = int(a.get('pl1$seasonNumber',0))
          infoList['Year'] = int(infoList['Aired'].split('-',1)[0])
          infoList['Plot'] = h.unescape(a['description'])
          infoList['TVShowTitle'] = tvshow
          infoList['Title'] = a['title']
          name = a['title']
          thumb = a['defaultThumbnailUrl']
          name = name.encode(UTF8)
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
              xurl = '%s?mode=GV&url=%s' % (sys.argv[0], url)
              strmFile = xbmc.translatePath(os.path.join(movieDir, se+'.strm'))
              with open(strmFile, 'w') as outfile:
                  outfile.write(xurl)         
      json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
      jsonRespond = xbmc.executeJSONRPC(json_cmd)


  def getAddonVideo(self,url):
      gvu1 = 'https://tvebravo-vh.akamaihd.net/i/prod/video/%s_,40,25,18,12,7,4,2,00.mp4.csmil/master.m3u8?b=&__b__=1000&hdnea=st=%s~exp=%s'
      gvu2 = 'https://tvebravo-vh.akamaihd.net/i/prod/video/%s_,1696,1296,896,696,496,240,306,.mp4.csmil/master.m3u8?b=&__b__=1000&hdnea=st=%s~exp=%s'
      url = uqp(url)
      url = url+'?mbr=true&player=Bravo%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
      html = self.getRequest(url)
      a = json.loads(html)
      suburl = a["captions"][0]["src"]
      url = suburl.split('/caption/',1)[1]
      url = url.split('.',1)[0]
      td = (datetime.datetime.utcnow()- datetime.datetime(1970,1,1))
      unow = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
      u = gvu1 % (url, str(unow), str(unow+60))
      req = urllib2.Request(u.encode(UTF8), None, self.defaultHeaders)
      try:
          response = urllib2.urlopen(req, timeout=20) # check to see if video file exists
      except:
          u = gvu2 % (url, str(unow), str(unow+60))
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
