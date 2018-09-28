# -*- coding: utf-8 -*-
# Smithsonian Channel Kodi Video Addon
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
qp = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8 = 'utf-8'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      self.defaultVidStream['width'] = 1920
      self.defaultVidStream['height'] = 1080
      html = self.getRequest('https://www.smithsonianchannel.com/full-episodes')
      html = re.compile('<ul id="full(.+?)</ul>', re.DOTALL).search(html).group(1)
      a = re.compile('data-premium=".+?href="(.+?)".+?srcset="(.+?)".+?series-name">(.+?)<.+?show-name">(.+?)<.+?"timecode">(.+?)<.+?</li>',re.DOTALL).findall(html)
      for (url, thumb, tvshow, title, dur) in a:
          if not thumb.startswith('http:'):
              thumb = 'http:'+thumb
          infoList = {}
          length = 0
          dur = dur.replace('|','').split(':')
          for d in dur:
              length = length*60 + int(d.strip())
          fanart = thumb
          infoList['Duration'] = length
          infoList['TVShowTitle'] = h.unescape(tvshow)
          infoList['Title'] = h.unescape(title)
          infoList['Genre'] = 'Documentary'
          infoList['mediatype'] = 'episode'
          name = infoList['Title']
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonVideo(self,url):
      html = self.getRequest('https://www.smithsonianchannel.com%s' % uqp(url))
      vidID = re.compile('data-bcid="(.+?)"', re.DOTALL).search(html).groups()
      url = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=1466806621001' % (vidID)
      master = self.getRequest(url)
      urls = re.compile('http\:(.+?)\n', re.DOTALL).findall(master)
      url = 'http:'+urls[-1]
      liz = xbmcgui.ListItem(path = url)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

