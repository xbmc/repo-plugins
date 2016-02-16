# -*- coding: utf-8 -*-
# Food Network Kodi Video Addon
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
     html = self.getRequest('http://www.foodnetwork.ca/video/')
     meta = self.getAddonMeta()
     try:    i = len(meta['shows'])
     except: meta['shows']={}
     a = re.compile('ShawVideoDrawer\(.+?drawerTitle: "(.+?)".+?categories: "(.+?)".+?\);',re.DOTALL).findall(html)
     pDialog = xbmcgui.DialogProgress()
     pDialog.create(self.addonName, addonLanguage(30101))
     pDialog.update(0)
     dirty = False
     numShows = len(a)
     fanart = self.addonFanart
     for i, (name, xurl) in list(enumerate(a[1:], start=1)):
      name = name.decode(UTF8)
      try:
        (name, url, thumb, fanart, infoList) = meta['shows'][xurl]
      except:
         url = xurl
         thumb  = self.addonIcon
         fanart = self.addonFanart
         infoList = {}
         dirty = True
         gsurl = 'http://feed.theplatform.com/f/dtjsEC/hoR6lzBdUZI9?byCategories=%s&form=cjson&count=true&startIndex=1&endIndex=2&fields=id,content,defaultThumbnailUrl,title,description,:show,:season,:episode,pubdate,availableDate,:clipType,restrictionID,:allowHTML5&sort=pubDate|desc&callback=' % xurl.replace(' ','%20')
         html  = self.getRequest(gsurl)
         a = json.loads(html)['totalResults']
         if a == 0: continue
         else: name = name+(' (%s)' % str(a))
         meta['shows'][xurl] = (name, url, thumb, fanart, infoList)
      ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      pDialog.update(int((100*i)/numShows))
     pDialog.close()
     if dirty == True: self.updateAddonMeta(meta)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
    self.defaultVidStream['width']  = 960
    self.defaultVidStream['height'] = 540
    geurl = uqp(url).replace(' ','%20')
    url = 'http://feed.theplatform.com/f/dtjsEC/hoR6lzBdUZI9?byCategories=%s&form=cjson&count=true&startIndex=1&endIndex=150&fields=id,content,defaultThumbnailUrl,title,description,:show,:season,:episode,pubdate,availableDate,:clipType,restrictionID,:allowHTML5&sort=pubDate|desc&callback=' % geurl
    html  = self.getRequest(url)
    a = json.loads(html)['entries']
    for b in a:
      url     = 'https://foodnetwork-vh.akamaihd.net/i/%s_,high,highest,medium,low,lowest,_16x9.mp4.csmil/master.m3u8' % b['defaultThumbnailUrl'].rsplit('_',2)[0].split('http://media.foodnetwork.ca/videothumbnails/',1)[1]
      name    = h.unescape(b['title']).encode(UTF8)
      fanart  = b['defaultThumbnailUrl'].rsplit('_',2)[0]+'.png'
      thumb   = fanart

      infoList = {}
      infoList['Duration']    = int(b['content'][0]['duration'])
      infoList['Title']       = name
      try: infoList['Studio']      = b['pl1$network']
      except: pass
      infoList['Date']        = datetime.datetime.fromtimestamp(b['pubDate']/1000).strftime('%Y-%m-%d')
      infoList['Aired']       = infoList['Date']
      infoList['Year']        = int(infoList['Date'].split('-',1)[0])
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
   xurl = url.split('/i/',1)[1].split('_,high',1)[0]
   suburl = 'http://media.foodnetwork.ca/videothumbnails/%s.vtt' % xurl

   req = urllib2.Request(url.encode(UTF8), None, self.defaultHeaders)
   try:
      response = urllib2.urlopen(req, timeout=20) # check to see if video file exists
   except:
      url = 'https://foodnetwork-vh.akamaihd.net/i/,%s.mp4,.csmil/master.m3u8' % xurl

   liz = xbmcgui.ListItem(path = url)
   if suburl != "" : liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

