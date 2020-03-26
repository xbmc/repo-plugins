# -*- coding: utf-8 -*-
# TV Ontario Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8  = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      azurl = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1'
      for a in azurl:
          name = a
          plot = ''
          url  = a
          infoList = {}
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)

  def getAddonShows(self,url,ilist):
      html = self.getRequest("https://www.tvo.org/documentaries/browse/filters/ajax/%s" % url)
      html = html[11:-12]
      a = json.loads(html)
      a = a["data"]
      a = re.compile('<div class="views\-row">.+?href="(.+?)".+?<div class="bc-thumb-(.+?)".+?src="(.+?)".+?results">(.+?)<.+?field\-\-item">(.+?)<',re.DOTALL).findall(a)
      for url,playable,thumb,name,plot in a:
          infoList = {}
          name = name.strip()
          name = h.unescape(name)
          plot = h.unescape(plot)
          url = 'https://tvo.org%s' % url
          infoList['Plot'] = plot
          infoList['mediatype'] = 'tvshow'
          if playable == 'wrapper':
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, thumb, infoList, isFolder=False)
          else:
              ilist = self.addMenuItem(name+' (Series)','GE', ilist, url, thumb, thumb, infoList, isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      self.defaultVidStream['width']  = 640
      self.defaultVidStream['height'] = 480
      html = self.getRequest(url)
      vids = re.compile('<div class="content-list__first.+?href="(.+?)".+?src="(.+?)".+?href=.+?>(.+?)<.+?field-summary"><div class="field-content">(.+?)<',re.DOTALL).findall(html)
      if vids == []:
          vids = re.compile('"og:url" content="(.+?)".+?content="(.+?)".+?content="(.+?)".+?".+?content="(.+?)"',re.DOTALL).search(html).groups()
          vids = [(vids[0],vids[2],vids[1],vids[3])]
      TVShowTitle = re.compile('property="og:title" content="(.+?)"', re.DOTALL).search(html).group(1)
      for (url, thumb, name, plot) in vids:
          if not url.startswith('http'):
              url = 'https://tvo.org' + url
          if not thumb.startswith('http'):
              thumb = 'https://tvo.org' + thumb[1:]
          fanart = thumb
          infoList = {}
          infoList['Title'] = h.unescape(name)
          infoList['Studio'] = 'TV Ontario'
          infoList['Plot'] = h.unescape(plot)
          infoList['TVShowTitle'] = TVShowTitle
          infoList['mediatype'] = 'episode'
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html = self.getRequest(url)
      vid = re.compile('data-video-id="(.+?)"',re.DOTALL).search(html).group(1)
      u = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=18140038001' % vid
      liz = xbmcgui.ListItem(path=u)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
