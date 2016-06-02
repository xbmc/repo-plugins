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
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
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
          purl = 'http://link.theplatform.com/s'+(purl.replace('/bravo_vod_p3/embed/select','').split('.com/p')[1]).split('?',1)[0]+'?mbr=true&player=Bravo%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
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
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


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
      subfile = self.procConvertSubtitles(suburl)
      if subfile != "" : liz.setSubtitles([subfile])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
