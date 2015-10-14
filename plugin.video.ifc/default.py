# -*- coding: utf-8 -*-
# IFC Video Addon for Kodi

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.ifc')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
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

def getShows():
   xbmcplugin.setContent(int(sys.argv[1]), 'files')
   ilist=[]

   html = getRequest('http://www.ifc.com/watch-now/')
   c = re.compile('<div class="featured-row.+?href="(.+?)".+?src="(.+?)".+?alt="(.+?)".+?</div>',re.DOTALL).findall(html)
   c.append(('http://www.ifc.com/watch-now/movies','http://www.ifc.com/watch-now/img/ifc-logo.png','Movies'))
   for purl, thumb, name in c:
      purl = 'http://www.ifc.com%s' % purl
      infoList = {}
      fanart = thumb
      if name == 'Movies':
         mode = 'GM'
      else: mode = 'GE'
      u = '%s?url=%s&mode=%s' % (sys.argv[0],qp(purl), mode)
      liz=xbmcgui.ListItem(name, '',None, thumb)
      liz.setProperty('fanart_image', fanart)
      ilist.append((u, liz, True))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getEpisodes(eurl):
   xbmcplugin.setContent(int(sys.argv[1]), 'files')
   ilist=[]

   html = getRequest(uqp(eurl))
   c = re.compile('<a class="video-link span4".+?id="video-(.+?)".+?src="(.+?)".+?<p class="video-title">(.+?)<.+?class="video-description">(.+?)</p>',re.DOTALL).findall(html)
   for url, thumb, name, plot in c:
     if not plot.startswith('</p>'):
      infoList = {}
      infoList['Title']       = name
      infoList['Studio']      = 'IFC'
      infoList['Plot']        = plot
      fanart = thumb
      u = '%s?url=%s&mode=GV' % (sys.argv[0],qp(url))
      liz=xbmcgui.ListItem(name, '',None, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'h264', 
                                   'width' : 960, 
                                   'height' : 540, 
                                   'aspect' : 1.78 })
      liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
      liz.addStreamInfo('subtitle', { 'language' : 'en'})
      liz.setProperty('fanart_image', fanart)
      liz.setProperty('IsPlayable', 'true')
      ilist.append((u, liz, False))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getMovies():
   xbmcplugin.setContent(int(sys.argv[1]), 'files')
   ilist=[]

   html = getRequest('http://www.ifc.com/watch-now/movies')
   c = re.compile('<a class="video-link span4".+?id="video-(.+?)".+?src="(.+?)".+?<p class="video-title">(.+?)<.+?class="video-description">(.+?)<.+?class="video-meta">(.+?)/p>',re.DOTALL).findall(html)
   for url, thumb, name, plot, meta in c:
      infoList = {}
      infoList['Title']       = name
      infoList['Studio']      = 'IFC'
      actors, director, releaseYear = re.compile('(.+?)<br>(.+?)<br>(.+?)<',re.DOTALL).search(meta).groups()
      infoList['Year']        = int(releaseYear.replace(' Released ','',1).strip())
      infoList['director']    = director.replace(' Directed by ','',1).strip()
      infoList['cast']        = actors.replace(' and ',', ',1).strip().split(', ')

      infoList['Plot']        = plot
      fanart = thumb
      u = '%s?url=%s&mode=GV' % (sys.argv[0],qp(url))
      liz=xbmcgui.ListItem(name, '',None, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'h264', 
                                   'width' : 960, 
                                   'height' : 540, 
                                   'aspect' : 1.78 })
      liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
      liz.addStreamInfo('subtitle', { 'language' : 'en'})
      liz.setProperty('fanart_image', fanart)
      liz.setProperty('IsPlayable', 'true')
      ilist.append((u, liz, False))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url):
    u = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=2272822658001' % uqp(url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = u))


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
elif mode=='GM':  getMovies()
elif mode=='GE':  getEpisodes(p('url'))
elif mode=='GV':  getVideo(p('url'))

