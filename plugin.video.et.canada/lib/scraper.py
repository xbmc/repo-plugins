# -*- coding: utf-8 -*-
# ET Canada Kodi Video Addon
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
   url = 'http://common.farm1.smdg.ca/Forms/PlatformVideoFeed?platformUrl=http%3A//feed.theplatform.com/f/dtjsEC/2dJJlS8TfWZc/categories%3Fpretty%3Dtrue%26byHasReleases%3Dtrue%26byCustomValue%3D%7Bplayertag%7D%7Bz/ETCanada%20Video%20Centre%7D%26sort%3DfullTitle&callback='
   html = self.getRequest(url)
   a = json.loads(html[1:len(html)-1])['items']
   wewait = True
   for b in a:
     if b['hasReleases'] == True:
       name = b['title']
       url  = b['id'].rsplit('/',1)[1]
       ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
   return(ilist)

  def getAddonCats(self,url,ilist):
   self.defaultVidStream['width']  = 640
   self.defaultVidStream['height'] = 360
   geurl = uqp(url)
   url = 'http://common.farm1.smdg.ca/Forms/PlatformVideoFeed?platformUrl=http%3A//feed.theplatform.com/f/dtjsEC/2dJJlS8TfWZc/categories%3Fpretty%3Dtrue%26byHasReleases%3Dtrue%26byCustomValue%3D%7Bplayertag%7D%7Bz/ETCanada%20Video%20Centre%7D%26sort%3DfullTitle&callback='
   html = self.getRequest(url)
   a = json.loads(html[1:len(html)-1])['items']
   pid = 'http://data.media.theplatform.com/media/data/Category/%s' % geurl
   wewait = True
   for b in a:
      if b['parentId'] == pid:
          name = b['title']
          url  = b['id'].rsplit('/',1)[1]
          ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
   return(ilist)


  def getAddonEpisodes(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    self.defaultVidStream['width']  = 640
    self.defaultVidStream['height'] = 360
    geurl = uqp(url)
    url = 'http://feed.theplatform.com/f/dtjsEC/2dJJlS8TfWZc?count=true&byCategoryIDs=%s&startIndex=1&endIndex=100&sort=pubDate|desc&callback=' % geurl
    html  = self.getRequest(url)
    a = json.loads(html)['entries']
    if len(a) == 0:
     url = 'http://common.farm1.smdg.ca/Forms/PlatformVideoFeed?platformUrl=http%3A//feed.theplatform.com/f/dtjsEC/2dJJlS8TfWZc/categories%3Fpretty%3Dtrue%26byHasReleases%3Dtrue%26byCustomValue%3D%7Bplayertag%7D%7Bz/ETCanada%20Video%20Centre%7D%26sort%3DfullTitle&callback='
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
      url = b['content'][0]['url']
      name    = h.unescape(b['title'])
      thumb   = b['thumbnails'][0]['url']
      fanart = thumb
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

  def getProxyRequest(self, url):
    USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
    headers = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 
    if (self.addon.getSetting('us_proxy_enable') == 'true'):
       us_proxy = 'http://%s:%s' % (self.addon.getSetting('us_proxy'), self.addon.getSetting('us_proxy_port'))
       proxy_handler = urllib2.ProxyHandler({'http':us_proxy})
       if self.addon.getSetting('us_proxy_pass') <> '' and self.addon.getSetting('us_proxy_user') <> '':
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, us_proxy, self.addon.getSetting('us_proxy_user'), self.addon.getSetting('us_proxy_pass'))
            proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
            opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
       else:
            opener = urllib2.build_opener(proxy_handler)
    else:
       opener = urllib2.build_opener()
    urllib2.install_opener(opener)
    req = urllib2.Request(url.encode(UTF8), None, headers)
    try:
       response = urllib2.urlopen(req, timeout=120)
       page = response.read()
       if response.info().getheader('Content-Encoding') == 'gzip':
           page = zlib.decompress(page, zlib.MAX_WBITS + 16)

    except urllib2.URLError, e:
       xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % (self.addonName, e , 5000) )
       page = ""
    return(page)



  def getAddonVideo(self,url):
   url = uqp(url)
   url = url.replace('f4m','m3u',1)
   html = self.getProxyRequest(url)
   url = re.compile('<video src="(.+?)"', re.DOTALL).search(html).group(1)
   suburls = re.compile('<textstream src="(.+?)"', re.DOTALL).findall(html)
   suburl =''
   for subu in suburls: 
      if '.vtt' in subu: 
         suburl = subu
         break
   liz = xbmcgui.ListItem(path = url)
   if suburl != "" : liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

