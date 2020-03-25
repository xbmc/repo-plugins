# -*- coding: utf-8 -*-
# HGTV Kodi Video Addon
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
UTF8 = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      url = 'http://www.hgtv.com/shows/full-episodes'
      html = self.getRequest(url)
      a = re.compile('<div class="m-MediaBlock o-Capsule__m-MediaBlock m-MediaBlock--PLAYLIST">.+?href="(.+?)".+?data-src="(.+?)".+?HeadlineText.+?>(.+?)<.+?AssetInfo">(.+?)<', re.IGNORECASE | re.DOTALL).findall(html)
      for (url, thumb, name, vidcnt) in a:
          if not url.startswith('http'):
              url = 'http:'+url
          name=name.strip().replace('<i>','')
          name=h.unescape(name)
          vidcnt = vidcnt.strip()
          infoList = {}
          epinum = vidcnt.split(' ',1)[0]
          if epinum.isdigit():
              if int(epinum) == 0:
                  continue
              infoList['Episode'] = int(epinum)
          else: 
              continue
          html = self.getRequest(url.rsplit('/',1)[0])
          plot = re.compile('"og:description" content="(.+?)"',re.DOTALL).search(html)
          if plot is not None:
              plot = plot.group(1)
          else:
              plot = name
          infoList['Plot'] = h.unescape(plot)
          infoList['TVShowTitle'] = name
          infoList['Title'] = name
          infoList['Studio'] = 'HGTV'
          fanart = re.compile('property="og:image" content="(.+?)"',re.DOTALL).search(html)
          if fanart is not None:
              fanart = fanart.group(1).replace('616.347.jpeg','1280.720.jpeg',1)
          else:
              fanart = thumb
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      self.defaultVidStream['width'] = 1280
      self.defaultVidStream['height'] = 720
      url = uqp(url)
      if not url.startswith('http:'):
          url = 'http:' + url
      html = self.getRequest(url)
      html = re.compile('<div id="video-player".+?type="text/x-config">(.+?)</script>',re.DOTALL).search(html)
      if html is None:
          return(ilist)
      vids = json.loads(html.group(1))['channels'][0]['videos']
      for b in vids:
          url = b['releaseUrl']
          name = h.unescape(b['title'])
          fanart = 'http://www.hgtv.com%s' % b['thumbnailUrl']
          thumb = 'http://www.hgtv.com%s' % b['thumbnailUrl']
          infoList = {}
          infoList['Title'] = name
          infoList['Studio'] = b['publisherId']
          infoList['Duration'] = b['length']
          infoList['Plot'] = h.unescape(b["description"])
          infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.Title')
          html = self.getRequest(url)
          mpaa = re.compile('ratings="(.+?)"',re.DOTALL).search(html)
          if mpaa is not None: 
              infoList['MPAA'] = mpaa.group(1).split(':',1)[1]
          infoList['mediatype'] = 'episode'
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html = self.getRequest(uqp(url))
      suburl = None
      subs = re.compile('<textstream src="(.+?)"',re.DOTALL).findall(html)
      for st in subs:
          if '.srt' in st:
              suburl = st
              break

      url = re.compile('<video src="(.+?)"',re.DOTALL).search(html)
      if url is None:
          url, msg = re.compile('<ref src="(.+?)".+?abstract="(.+?)"',re.DOTALL).search(html).groups()
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, msg , 5000) )
          return
      liz = xbmcgui.ListItem(path = url.group(1))
      if suburl is not None: liz.setSubtitles([suburl])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
