# -*- coding: utf-8 -*-
# KodiAddon (Adultswim)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin
import xbmcgui
import calendar
import datetime
import sys
import xbmc

UTF8 = 'utf-8'
ASBASE = 'http://www.adultswim.com'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = self.getRequest(ASBASE+'/videos')
      html = re.compile('type="application/json">(.+?)</script>', re.DOTALL).search(html).group(1)
      a = json.loads(html)
      for b in a['props']['pageProps']['shows']:
         name = b['title']
         url = b['url']
         thumb = b['poster']
         fanart = thumb
         infoList = {}
         infoList['TVShowTitle'] = name
         infoList['Title'] = name
         infoList['Plot'] = name
         infoList['mediatype'] = 'tvshow'
         ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      html = self.getRequest(ASBASE+url)
      html = re.compile('"application/json">(.+?)</script>', re.DOTALL).search(html).group(1)
      a = json.loads(html)
      x = a["props"]["pageProps"]["__APOLLO_STATE__"].keys()
      for b in x:
          if b.startswith("Video:"):
            b = a["props"]["pageProps"]["__APOLLO_STATE__"][b]
            if b.get('auth',True) == False:
              infoList = {}
              name = b['title']
              thumb = b.get('poster')
              fanart = thumb
              url = b['id']
              infoList = {}
              infoList['title'] = name
              infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
              infoList['mediatype'] = 'episode'
              infoList['Plot'] = b.get('description')
              infoList['Duration'] = b.get('duration')
              infoList['MPAA'] = b.get('tvRating')
              infoList['Episode'] = b.get('episodeNumber')
              infoList['Premiered'] = b.get('launchDate').split('T',1)[0]
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonVideo(self,url):
      html = self.getRequest('http://www.adultswim.com/api/shows/v1/videos/'+url+'?fields=title%2Ctype%2Cduration%2Ccollection_title%2Cposter%2Cstream%2Csegments%2Ctitle_id')
      a = json.loads(html)
      for b in a['data']['video']['stream']['assets']:
          if (b.get('mime_type') == 'application/x-mpegURL') and (b.get('url').endswith('stream_full.m3u8') or b.get('url').endswith('/stream.m3u8') ):
              url = b.get('url')
              liz = xbmcgui.ListItem(path = url)
              infoList = {}
              liz.setInfo('video', infoList)
              liz.setProperty('inputstreamaddon','inputstream.adaptive')
              liz.setProperty('inputstream.adaptive.manifest_type','hls')
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
