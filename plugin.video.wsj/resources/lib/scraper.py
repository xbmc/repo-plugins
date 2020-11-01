# -*- coding: utf-8 -*-
# KodiAddon (The Wall Street Journal)
#
from t1mlib import t1mAddon
import json
import re
import urllib.parse
import xbmcplugin
import xbmcgui
import sys
import xbmc
import requests
import html.parser

UNESCAPE = html.parser.HTMLParser().unescape
QP = urllib.parse.urlencode


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://wsj.com/video', headers=self.defaultHeaders).text
      html = re.compile('<nav class="top">(.+?)</nav', re.DOTALL).search(html).group(1)
      cats = re.compile('href="(.+?)">(.+?)<', re.DOTALL).findall(html)
      for url, name in cats:
          if '/video' in url and (not ('/sponsored' in url)) and (not ('/series' in url)):
              infoList = {'mediatype':'tvshow',
                          'Title': name,
                          'TVShowTitle': name,
                          'Plot': name}
              ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)


  def getAddonShows(self,url,ilist):
      cats = []
      if '/browse' in url:
          html = requests.get(url, headers=self.defaultHeaders).text
          html = re.compile('<div class="select-holder">(.+?)</div>', re.DOTALL).search(html).group(1)
          cats = re.compile('value="(.+?)">(.+?)</option>', re.DOTALL).findall(html)
          cats = [(t[1], t[0]) for t in cats]
      elif ('/topics' in url) or ('/events' in url):
          html = requests.get(url, headers=self.defaultHeaders).text
          cats = re.compile('data-ref="(.+?)".+?href="(.+?)"', re.DOTALL).findall(html)
      for name, url in cats:
          if not url.startswith('http'):
              url = ''.join(['https://www.wsj.com',url])
          name = UNESCAPE(name)
          infoList = {'mediatype':'tvshow',
                      'Title': name,
                      'TVShowTitle': name,
                      'Plot': name}
          ilist = self.addMenuItem(name,'GE', ilist, url, self.addonFanart, self.addonFanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      start = re.compile('&startnumber=([0-9]+)').search(url)
      if start is None:
          start = 0
          html = requests.get(url, headers=self.defaultHeaders).text
          u = re.compile("data-apioptions='(.+?)'", re.DOTALL).search(html)
          if u is None:
              return(ilist)
          u = u.group(1)
          p = json.loads(u)
          p['fields'] = "guid,name,duration,thumbnail1280x720URL,thumbnail640x360URL,formattedCreationDate,column,description,hls"
          p['startnumber'] = str(start)
          p['count'] = "25"
          nexturl = ''.join(['https://video-api.wsj.com/api-video/find_all_videos.asp?',QP(p)])
      else:
          start = int(start.group(1))+25
          nexturl = re.sub('&startnumber=([0-9]+)','&startnumber='+str(start),url)
      a = requests.get(nexturl, headers=self.defaultHeaders).json()
      for item in a['items']:
          url = item['hls']
          name = item['name']
          thumb = item['thumbnail640x360URL']
          fanart = item['thumbnail1280x720URL']
          infoList = {'mediatype':'episode',
                      'Title': name,
                      'TVShowTitle': name,
                      'Plot': ''.join([item['formattedCreationDate'],'\n',item['description']])}
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      if len(ilist) >= 25-1:
          name = ''.join(['[COLOR blue]Next (',str(start+26),' to ',str(start+50),') [/COLOR]'])
          infoList = {'Plot': name, 'mediatype':'episode'}
          ilist = self.addMenuItem(name,'GE', ilist, nexturl, self.addonFanart, self.addonFanart, infoList, isFolder=True)
      return(ilist)


  def getAddonVideo(self,url):
      liz = xbmcgui.ListItem(path = url)
      liz.setProperty('inputstreamaddon','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
