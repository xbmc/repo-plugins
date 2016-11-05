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
      url     = b['content'][0]['url'].replace('manifest=f4m','manifest=m3u')
      name    = h.unescape(b['title'])
      thumb   = b.get('defaultThumbnailUrl')
      fanart  = self.addonFanart
      infoList = {}
      infoList['Duration'] = int(b['content'][0]['duration'])
      infoList['Title'] = name
      infoList['Studio'] = b.get('pl1$network')
      infoList['Date']   = datetime.datetime.fromtimestamp(b['pubDate']/1000).strftime('%Y-%m-%d')
      infoList['Aired']  = infoList['Date']
      infoList['Year']   = int(infoList['Date'].split('-',1)[0])
      mpaa = re.compile('ratings="(.+?)"',re.DOTALL).search(html)
      if mpaa is not None: infoList['MPAA'] = mpaa.group(1).split(':',1)[1]
      episode = b.get('pl1$episode')
      if episode is not None: infoList['Episode'] = int(episode)
      season = b.get('pl1$season')
      if season is not None: infoList['Season']  = int(season)
      else: infoList['Season']  = 1
      infoList['Plot']        = h.unescape(b["description"])
      infoList['TVShowTitle'] = b['pl1$show']
      infoList['mediatype'] = 'episode'
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    return(ilist)



  def getAddonVideo(self,url):
     html = self.getRequest(url) #needs proxy
     url = re.compile('video src="(.+?)"', re.DOTALL).search(html).group(1)
     suburl = re.compile('textstream src="(.+?)"', re.DOTALL).search(html)
     html = self.getRequest(url) #needs proxy
     url = re.compile('http(.+?)\n', re.DOTALL).search(html).group(0).strip()
     liz = xbmcgui.ListItem(path = url)
     if suburl is not None: 
        suburl=suburl.group(1).replace('.ttml','.vtt')
        liz.setSubtitles([suburl])
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

