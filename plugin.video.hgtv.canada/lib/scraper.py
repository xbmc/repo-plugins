# -*- coding: utf-8 -*-
# HGTV Canada Kodi Video Addon
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
   addonLanguage  = self.addon.getLocalizedString
   url = 'http://common.farm1.smdg.ca/Forms/PlatformVideoFeed?platformUrl=http%3A//feed.theplatform.com/f/dtjsEC/EAlt6FfQ_kCX/categories%3Fpretty%3Dtrue%26byHasReleases%3Dtrue%26range%3D1-1000%26byCustomValue%3D%7Bplayertag%7D%7Bz/HGTVNEWVC%20-%20New%20Video%20Center%7D%26sort%3DfullTitle&callback='
   html = self.getRequest(url)
   a = json.loads(html[1:len(html)-1])['items']
   wewait = True
   for b in a:
    if b['title'] == 'Shows' and wewait == True:
        wewait = False
        continue
    if wewait == False:
      if b['depth'] == 2:
       name = b['title']
       url  = b['id'].rsplit('/',1)[1]
       ilist = self.addMenuItem(name,'GC', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
   return(ilist)

  def getAddonCats(self,url,ilist):
   self.defaultVidStream['width']  = 640
   self.defaultVidStream['height'] = 360
   geurl = uqp(url)
   url = 'http://common.farm1.smdg.ca/Forms/PlatformVideoFeed?platformUrl=http%3A//feed.theplatform.com/f/dtjsEC/EAlt6FfQ_kCX/categories%3Fpretty%3Dtrue%26byHasReleases%3Dtrue%26range%3D1-1000%26byCustomValue%3D%7Bplayertag%7D%7Bz/HGTVNEWVC%20-%20New%20Video%20Center%7D%26sort%3DfullTitle&callback='
   html = self.getRequest(url)
   a = json.loads(html[1:len(html)-1])['items']
   pid = 'http://data.media.theplatform.com/media/data/Category/%s' % geurl
   wewait = True
   for b in a:
      if b['parentId'] == pid:
        if wewait == True:
          if b['title'] == 'Full Episodes': 
             wewait = False
             pid = b['id']
          if b['hasReleases'] == False: continue
        if wewait == False and b['hasReleases'] == True:
          name = b['title']
          url  = b['id'].rsplit('/',1)[1]
          ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
   return(ilist)


  def getAddonEpisodes(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    self.defaultVidStream['width']  = 640
    self.defaultVidStream['height'] = 360
    geurl = uqp(url)
    url = 'http://feed.theplatform.com/f/dtjsEC/EAlt6FfQ_kCX?count=true&byCategoryIDs=%s&startIndex=1&endIndex=100&sort=pubDate|desc&callback=' % geurl
    html  = self.getRequest(url)
    a = json.loads(html)['entries']
    if len(a) == 0:
     url = 'http://common.farm1.smdg.ca/Forms/PlatformVideoFeed?platformUrl=http%3A//feed.theplatform.com/f/dtjsEC/EAlt6FfQ_kCX/categories%3Fpretty%3Dtrue%26byHasReleases%3Dtrue%26range%3D1-1000%26byCustomValue%3D%7Bplayertag%7D%7Bz/HGTVNEWVC%20-%20New%20Video%20Center%7D%26sort%3DfullTitle&callback='
     html = self.getRequest(url)
     a = json.loads(html[1:len(html)-1])['items']
     pid = 'http://data.media.theplatform.com/media/data/Category/%s' % geurl
     wewait = True
     for b in a:
      if b['parentId'] == pid:
        if wewait == True:
          if b['title'] == 'Full Episodes': 
             wewait = False
             pid = b['id']
          if b['hasReleases'] == False: continue
        if wewait == False and b['hasReleases'] == True:
          name = b['title']
          url  = b['id'].rsplit('/',1)[1]
          ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)

    else:  
     for b in a:
      url     = 'http://hgtv-vh.akamaihd.net/i/,%s.mp4,.csmil/master.m3u8' % b['defaultThumbnailUrl'].rsplit('_',2)[0].split('http://media.hgtv.ca/videothumbnails/',1)[1]
      name    = h.unescape(b['title'])
      thumb   = b['defaultThumbnailUrl']
      fanart  = self.addonFanart

      infoList = {}
      infoList['Duration']    = int(b['content'][0]['duration'])
      infoList['Title']       = name
      try: infoList['Studio']      = b['pl1$network']
      except: pass
      infoList['Date']        = datetime.datetime.fromtimestamp(b['pubDate']/1000).strftime('%Y-%m-%d')
      infoList['Aired']       = infoList['Date']
      infoList['Year']        = int(infoList['Date'].split('-',1)[0])
      try:    infoList['MPAA'] = re.compile('ratings="(.+?)"',re.DOTALL).search(html).group(1).split(':',1)[1]
      except: infoList['MPAA'] = None
      try:    infoList['Episode'] = int(b['pl1$episode'])
      except: infoList['Episode'] = None
      try:    infoList['Season']  = int(b['pl1$season'])
      except: infoList['Season']  = 1
      infoList['Plot']        = h.unescape(b["description"])
      infoList['TVShowTitle'] = b['pl1$show']
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    return(ilist)



  def getAddonVideo(self,url):
   url = uqp(url)
   suburl = 'http://media.hgtv.ca/videothumbnails/%s.vtt' % url.split('/i/,',1)[1].split('.mp4',1)[0]
   liz = xbmcgui.ListItem(path = url)
   if suburl != "" : liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

