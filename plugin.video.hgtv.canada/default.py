# -*- coding: utf-8 -*-
# HGTV Canada Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.hgtv.canada')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 


def getRequest(url, headers = defaultHeaders):
   req = urllib2.Request(url.encode(UTF8), None, headers)
   try:
      response = urllib2.urlopen(req)
      page = response.read()
      if response.info().getheader('Content-Encoding') == 'gzip':
         log("Content Encoding == gzip")
         page = zlib.decompress(page, zlib.MAX_WBITS + 16)
   except:
      page = ""
   return(page)


def getShows():
   xbmcplugin.setContent(int(sys.argv[1]), 'files')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

   ilist=[]
   url = 'http://common.farm1.smdg.ca/Forms/PlatformVideoFeed?platformUrl=http%3A//feed.theplatform.com/f/dtjsEC/EAlt6FfQ_kCX/categories%3Fpretty%3Dtrue%26byHasReleases%3Dtrue%26range%3D1-1000%26byCustomValue%3D%7Bplayertag%7D%7Bz/HGTVNEWVC%20-%20New%20Video%20Center%7D%26sort%3DfullTitle&callback='
   html = getRequest(url)
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
       u = '%s?url=%s&mode=GC' % (sys.argv[0],url)
       liz=xbmcgui.ListItem(name, '',None, icon)
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getCats(geurl):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

   ilist=[]
   url = 'http://common.farm1.smdg.ca/Forms/PlatformVideoFeed?platformUrl=http%3A//feed.theplatform.com/f/dtjsEC/EAlt6FfQ_kCX/categories%3Fpretty%3Dtrue%26byHasReleases%3Dtrue%26range%3D1-1000%26byCustomValue%3D%7Bplayertag%7D%7Bz/HGTVNEWVC%20-%20New%20Video%20Center%7D%26sort%3DfullTitle&callback='
   html = getRequest(url)
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
          u = '%s?url=%s&mode=GE' % (sys.argv[0],url)
          liz=xbmcgui.ListItem(name, '',None, icon)
          liz.setProperty('fanart_image', addonfanart)
          ilist.append((u, liz, True))

   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getEpisodes(geurl):
  xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

  ilist=[]
  url = 'http://feed.theplatform.com/f/dtjsEC/EAlt6FfQ_kCX?count=true&byCategoryIDs=%s&startIndex=1&endIndex=100&sort=pubDate|desc&callback=' % geurl
  html  = getRequest(url)
  a = json.loads(html)['entries']
  if len(a) == 0:
   url = 'http://common.farm1.smdg.ca/Forms/PlatformVideoFeed?platformUrl=http%3A//feed.theplatform.com/f/dtjsEC/EAlt6FfQ_kCX/categories%3Fpretty%3Dtrue%26byHasReleases%3Dtrue%26range%3D1-1000%26byCustomValue%3D%7Bplayertag%7D%7Bz/HGTVNEWVC%20-%20New%20Video%20Center%7D%26sort%3DfullTitle&callback='
   html = getRequest(url)
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
          u = '%s?url=%s&mode=GE' % (sys.argv[0],url)
          liz=xbmcgui.ListItem(name, '',None, icon)
          liz.setProperty('fanart_image', addonfanart)
          ilist.append((u, liz, True))

  else:  
   for b in a:
      url     = 'http://hgtv-vh.akamaihd.net/i/,%s.mp4,.csmil/master.m3u8' % b['defaultThumbnailUrl'].rsplit('_',2)[0].split('http://media.hgtv.ca/videothumbnails/',1)[1]
      name    = h.unescape(b['title'])
      fanart  = b['defaultThumbnailUrl']
      thumb   = b['defaultThumbnailUrl']

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
      u = '%s?url=%s&mode=GV' % (sys.argv[0],qp(url))
      liz=xbmcgui.ListItem(name, '',icon, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width' : 640, 
                                   'height' : 360, 
                                   'aspect' : 1.78 })
      liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
      liz.addStreamInfo('subtitle', { 'language' : 'en'})
      liz.setProperty('fanart_image', addonfanart)
      liz.setProperty('IsPlayable', 'true')
      ilist.append((u, liz, False))
  xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
  if addon.getSetting('enable_views') == 'true':
    xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url):
   url = uqp(url)
   suburl = 'http://media.hgtv.ca/videothumbnails/%s.vtt' % url.split('/i/,',1)[1].split('.mp4',1)[0]
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))

   if (addon.getSetting('sub_enable') == "true") and (suburl != ''):
      profile = addon.getAddonInfo('profile').decode(UTF8)
      subfile = xbmc.translatePath(os.path.join(profile, 'Subtitles.srt'))
      prodir  = xbmc.translatePath(os.path.join(profile))
      if not os.path.isdir(prodir):
         os.makedirs(prodir)

      pg = getRequest(suburl)
      if pg != "":
        ofile = open(subfile, 'w+')
        ofile.write(pg)
        ofile.close()
        xbmc.sleep(2000)
        xbmc.Player().setSubtitles(subfile)


# MAIN EVENT PROCESSING STARTS HERE

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
      try:    parms[key] = urllib.unquote_plus(parms[key]).decode(UTF8)
      except: pass
except:
    parms = {}

p = parms.get

mode = p('mode',None)

if mode==  None:  getShows()
elif mode=='GC':  getCats(p('url'))
elif mode=='GE':  getEpisodes(p('url'))
elif mode=='GV':  getVideo(p('url'))
