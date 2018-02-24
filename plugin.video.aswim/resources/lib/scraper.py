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
      html = re.compile('__AS_INITIAL_DATA__ = (.+?);\n', re.DOTALL).search(html).group(1)
      a = json.loads(html)
      for b in a['shows']:
         name = b['title']
         url = b['url']
         infoList = {}
         infoList['TVShowTitle'] = name
         infoList['Title'] = name
         infoList['Plot'] = name
         infoList['mediatype'] = 'tvshow'
         ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      html = self.getRequest(ASBASE+url)
      html = re.compile('__AS_INITIAL_DATA__ = (.+?);\n', re.DOTALL).search(html).group(1)
      a = json.loads(html)
      for b in a['show']['videos']:
          if b['auth'] == False:
              infoList = {}
              name = b['title']
              thumb = b.get('poster')
              fanart = thumb
              url = b['id']
              infoList = {}
              infoList['title'] = name
              infoList['TVShowTitle'] = b.get('collection_title')
              infoList['mediatype'] = 'episode'
              infoList['Plot'] = b.get('description')
              infoList['Duration'] = b.get('duration')
              infoList['MPAA'] = b.get('tv_rating')
              infoList['Season'] = b.get('season_number')
              infoList['Episode'] = b.get('episode_number')
              infoList['Date'] = b.get('launch_date')
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonVideo(self,url):
      html = self.getRequest('http://www.adultswim.com/videos/api/v3/videos/%s?fields=title,type,duration,collection_title,poster,stream,segments,title_id' % url)
      a = json.loads(html)
      for b in a['data']['stream']['assets']:
          if (b.get('mime_type') == 'application/x-mpegURL') and (b.get('url').endswith('stream_full.m3u8') or b.get('url').endswith('/stream.m3u8') ):
              url = b.get('url')
              liz = xbmcgui.ListItem(path = url)
              infoList = {}
              liz.setInfo('video', infoList)
              liz.setProperty('inputstreamaddon','inputstream.adaptive')
              liz.setProperty('inputstream.adaptive.manifest_type','hls')
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
