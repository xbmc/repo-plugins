# -*- coding: utf-8 -*-
# KodiAddon Sundance TV
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

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
     infoList = []
     addonLanguage  = self.addon.getLocalizedString
     html = self.getRequest('http://www.sundance.tv/watch-now/')
     a = re.compile(' <div class="show-title tablet-only">(.+?)<.+?src="(.+?)".+?class="episode" href="(.+?)"',re.DOTALL).findall(html)
     a.extend([(addonLanguage(30030),self.addonIcon,'http://www.sundance.tv/watch-now/movies/')])
     for name,thumb,url in a:
        name = h.unescape(name.decode(UTF8))
        ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
        self.defaultVidStream['width']  = 960
        self.defaultVidStream['height'] = 540

        url = uqp(url)
        hurl = 'http://www.sundance.tv/watch-now/'
        if '/movies/' in url : 
             seriesName = 'movie'
             hurl = hurl+'movies'
        else:    seriesName = url.replace('/watch-now/','',1).split('/',1)[0]
        target = '<a class="episode" href="/watch-now/%s/(.+?)"' % seriesName
        html  = self.getRequest(hurl)
        a  = re.compile(target, re.DOTALL).findall(html)
        url = a[0]
        if not '/movies' in hurl: html = self.getRequest('http://www.sundance.tv/watch-now/%s/%s' % (seriesName, url))
        for url in a:
              if '/movies' in hurl: html = self.getRequest('http://www.sundance.tv/watch-now/%s/%s' % ('movie', url))
              vid = url.split('/',1)[0]
              target = '<div id="video-%s-hover"(.+?)</a' % vid
              try: 
                  blob = re.compile(target, re.DOTALL).search(html).group(1)
                  name = re.compile('"video-title">(.+?)<', re.DOTALL).search(blob).group(1)
              except:
                 try:
                  target = '<div id="video-%s".+?video-title">(.+?)<' % vid
                  name = re.compile(target, re.DOTALL).search(html).group(1)
                 except: continue
              target = '<div id="video-%s" class="video".+?src="(.+?)"' % vid
              try:     thumb = re.compile(target, re.DOTALL).search(html).group(1)
              except:  thumb = self.addonIcon
              if not thumb.startswith('http'): thumb = self.addonIcon
              infoList={}
              infoList['Title'] = name
              if not '/movies' in hurl:
                 try: infoList['TVShowTitle'] = re.compile('<h2>(.+?)<', re.DOTALL).search(blob).group(1)
                 except: pass
                 try: infoList['Season'] = int(re.compile('"episode-info">.+?Season (.+?)\|', re.DOTALL).search(blob).group(1))
                 except: pass
                 try: infoList['Episode'] = int(re.compile('"episode-info">.+?Episode (.+?)\|', re.DOTALL).search(blob).group(1))
                 except: pass
                 try:
                   aired = re.compile('"episode-info">.+?Aired on (.+?)<', re.DOTALL).search(blob).group(1)
                   aired = aired.split('/')
                   aired = '%s-%s-%s' % (aired[2].strip(),aired[0], aired[1])
                   infoList['Aired'] = aired
                 except: pass
              try: infoList['Plot'] = re.compile('class="video-description">(.+?)<', re.DOTALL).search(blob).group(1)
              except: 
                  try: infoList['Plot'] = re.compile('<h4 class="video-title">.+?<p>(.+?)<', re.DOTALL).search(html).group(1)
                  except: pass
              url = vid
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)
        return(ilist)


  def getAddonVideo(self,url):
     vid = uqp(url)
     url = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=3605490453001' % (vid)
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))
