# -*- coding: utf-8 -*-
# Russia Today Kodi Video Addon
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
UTF8     = 'utf-8'
RTBASE_URL  = 'https://www.rt.com'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      ilist = self.addMenuItem('RT Live','GS', ilist, 'abc' , self.addonIcon, self.addonFanart, None, isFolder=True)
      page = self.getRequest(RTBASE_URL+"/shows/")
      match = re.compile('<li class="card-rows__item.+?src="(.+?)".+?href="(.+?)">(.+?)<.+?class="link link_disabled".+?>(.+?)</li',re.DOTALL).findall(page)
      for img,url,name,plot in match:
          thumb = img
          fanart = img
          infoList = {}
          name = name.strip()
          infoList['Title'] = name
          infoList['mediatype'] = 'tvshow'
          infoList['Plot']  = h.unescape(plot.strip().replace('<p>','').replace('</p>','').decode(UTF8))
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      page = self.getRequest(RTBASE_URL+url)
      match = re.compile('static-three_med-one">.+?src="(.+?)".+?class="link link_hover" href="(.+?)">(.+?)<.+?class="card__summary ">(.+?)</',re.DOTALL).findall(page)
      for img,url,name,plot in match:
          thumb = img
          fanart = img
          name = name.strip()
          infoList = {}
          infoList['Title'] = name
          infoList['mediatype'] = 'episode'
          infoList['Plot']  = h.unescape(plot.strip().replace('<p>','').replace('</p>','').decode(UTF8))
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonShows(self,url,ilist):
      rlist = [("https://www.rt.com/on-air/", 'Global'),
               ("https://www.rt.com/on-air/rt-america-air", 'US'),
               ("https://www.rt.com/on-air/rt-uk-air", 'UK'),
               ("https://rtd.rt.com/on-air/", 'Doc')]
      for url, name in rlist:
          name = name.strip()
          infoList = {}
          infoList['Title'] = name
          infoList['mediatype'] = 'episode'
          ilist = self.addMenuItem(name,'GV', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=False)
      return(ilist)



  def getAddonVideo(self,url):
      if not url.startswith('http'):
          url = RTBASE_URL + url
      html = self.getRequest(url)
      if 'rtd.rt.com' not in url:
          m = re.compile("file: '(.+?)'",re.DOTALL).search(html)
          if m != None:
              url = m.group(1)
          else:
               m = re.compile('file: "(.+?)"',re.DOTALL).search(html)
               if m != None:
                   url = m.group(1)
               else:
                   return
      else:
          m = re.compile('streams_hls.+?url: "(.+?)"',re.DOTALL).search(html)
          if m != None:
              url = m.group(1)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))
