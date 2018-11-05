# -*- coding: utf-8 -*-
# KodiAddon (The Wall Street Journal)
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


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = self.getRequest('https://wsj.com/video')
      html = re.compile('<nav class="top">(.+?)</nav', re.DOTALL).search(html).group(1)
      cats = re.compile('href="(.+?)">(.+?)<', re.DOTALL).findall(html)
      for url, name in cats:
          if '/video' in url and (not ('/sponsored' in url)) and (not ('/series' in url)):
              infoList = {}
              infoList['TVShowTitle'] = name
              infoList['Title'] = name
              infoList['Plot'] = name
              infoList['mediatype'] = 'tvshow'
              ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)

  def getAddonShows(self,url,ilist):
      if '/browse' in url:
          html   = self.getRequest(url)
          html = re.compile('<div class="select-holder">(.+?)</div>', re.DOTALL).search(html).group(1)
          cats = re.compile('value="(.+?)">(.+?)</option>', re.DOTALL).findall(html)
          cats = [(t[1], t[0]) for t in cats]
      elif ('/topics' in url) or ('/events' in url):
          html = self.getRequest(url)
          cats = re.compile('data-ref="(.+?)".+?href="(.+?)"', re.DOTALL).findall(html)
      for name, url in cats:
          if not url.startswith('http'):
              url = 'https://www.wsj.com%s' % url
          name = name.replace('&nbsp;','').replace('&amp;','&')
          infoList = {}
          infoList['TVShowTitle'] = name
          infoList['Title'] = name
          infoList['Plot'] = name
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, self.addonFanart, self.addonFanart, infoList, isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      start = re.compile('&startnumber=([0-9]+)').search(url)
      if not (start is None):
          start = int(start.group(1))+25
          url = re.sub('&startnumber=([0-9]+)','&startnumber='+str(start),url)
      else:
          start = 0
          html = self.getRequest(url)
          u = re.compile("data-apioptions='(.+?)'", re.DOTALL).search(html)
          if u is None:
              return(ilist)
          u = u.group(1)
          p = json.loads(u)
          p['fields'] = "guid,name,duration,thumbnail1280x720URL,thumbnail640x360URL,formattedCreationDate,column,description,hls"
          p['startnumber'] = str(start)
          p['count'] = "25"
          url = 'https://video-api.wsj.com/api-video/find_all_videos.asp?'+urllib.urlencode(p)
      html = self.getRequest(url)
      nexturl = url
      a = json.loads(html)
      a = a['items']
      for item in a:
              url = item['hls']
              name = item['name']
              thumb = item['thumbnail640x360URL']
              fanart = item['thumbnail1280x720URL']
              infoList = {}
              infoList['TVShowTitle'] = name
              infoList['Title'] = name
              infoList['Plot'] = '%s\n%s' % (item['formattedCreationDate'],item['description'])
              infoList['mediatype'] = 'episode'
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      if len(ilist) >= 25-1:
          name = '[COLOR blue]Next (%s to %s) [/COLOR]' % (str(start+1), str(start+25))
          ilist = self.addMenuItem(name,'GE', ilist, nexturl, self.addonFanart, self.addonFanart, {'PLOT': name, 'mediatype':'episode'}, isFolder=True)
      return(ilist)

  def getAddonVideo(self,url):
      liz = xbmcgui.ListItem(path = url)
      infoList = {}
      liz.setInfo('video', infoList)
      liz.setProperty('inputstreamaddon','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
