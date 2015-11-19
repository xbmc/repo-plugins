# -*- coding: utf-8 -*-
# Sundance TV Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.sundance')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


qp  = urllib.quote_plus
uqp = urllib.unquote_plus

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, headers = defaultHeaders):
   log("getRequest URL:"+str(url))
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


def getSources(fanart):
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        ilist = []
        html = getRequest('http://www.sundance.tv/watch-now/')
        a = re.compile(' <div class="show-title tablet-only">(.+?)<.+?href="(.+?)".+?src="(.+?)"',re.DOTALL).findall(html)
        a.extend([(__language__(30020),'http://www.sundance.tv/watch-now/movies/',icon)])
        for name,url,img in a:
              mode = 'GC'
              name = h.unescape(name.decode(UTF8))
#              plot = name
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '',None, img)
#              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
          xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
   


def getCats(url,catname):
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        url = uqp(url)
        hurl = 'http://www.sundance.tv/watch-now/'
        if '/movies/' in url : 
             seriesName = 'movie'
             hurl = hurl+'movies'
        else:    seriesName = url.replace('/series/','',1)
        target = '<a class="episode" href="/watch-now/%s/(.+?)"' % seriesName
        html  = getRequest(hurl)
        a  = re.compile(target, re.DOTALL).findall(html)
        url = a[0]
        html = getRequest('http://www.sundance.tv/watch-now/%s/%s' % (seriesName, url))
        for url in a:
              vid = url.split('/',1)[0]
              target = '<div id="video-%s-hover"(.+?)</a' % vid
              try: 
                  blob = re.compile(target, re.DOTALL).search(html).group(1)
                  name = re.compile('"video-title">(.+?)<', re.DOTALL).search(blob).group(1)
              except:
                  target = '<div id="video-%s".+?video-title">(.+?)<' % vid
                  name = re.compile(target, re.DOTALL).search(html).group(1)
              target = '<div id="video-%s" class="video".+?src="(.+?)"' % vid
              try:     img = re.compile(target, re.DOTALL).search(html).group(1)
              except:  img = icon
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
              u = '%s?url=%s&name=%s&mode=GL' % (sys.argv[0],qp(url), qp(name))
              liz=xbmcgui.ListItem(name, '', None, img)
              liz.setInfo( 'Video', infoList)
              liz.addStreamInfo('video', { 'codec': 'h264', 
                                   'width' : 960, 
                                   'height' : 540, 
                                   'aspect' : 1.78 })
              liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
              liz.setProperty('fanart_image', img )
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
        if len(ilist) != 0:
           xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))




def getLink(url,vidname):
              vid = uqp(url)
              url = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=3605490453001' % (vid)
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))


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

if mode==  None:  getSources(p('fanart'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GM':  getMovies(p('url'),p('name'))
elif mode=='GL':  getLink(p('url'),p('name'))


