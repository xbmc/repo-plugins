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
        a = re.compile('<h3 class="featured-row-title.+?href="(.+?)">(.+?)<.+?src="(.+?)"',re.DOTALL).findall(html)
        a.extend([('http://www.sundance.tv/watch-now/movies/',__language__(30020),icon)])
        for url,name,img in a:
              mode = 'GC'
              name = h.unescape(name.decode(UTF8))
              plot = name
              if not url.startswith('http:'): url = 'http://www.sundance.tv%s' % url
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
          xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
   


def getCats(gsurl,catname):
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        html  = getRequest(uqp(gsurl))
        a=[]
        if '/movies/' in gsurl:
          try:
              img,url,name,plot = re.compile('<div class="video-player-holder clearfix">.+?src="(.+?)".+?<div id="video-(.+?)".+?"video-title">(.+?)<.+?<p>(.+?)<',re.DOTALL).search(html).groups()
              a =[(url,img,name,plot)]
          except:
              pass
            
        c     = re.compile('<a class="video-link related-triple".+?div id="video-(.+?)".+?src="(.+?)".+?"video-title">(.+?)<.+?"video-description">(.+?)<.+?</div',re.DOTALL).findall(html)
        a.extend(c)
        for url, img, name, plot in a:
              name = h.unescape(name.decode(UTF8))
              url = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=3605490453001' % (url)
              mode = 'GL'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": plot })
              liz.setProperty('fanart_image', img)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
        if len(ilist) != 0:
           xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getLink(url,vidname):
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
elif mode=='GL':  getLink(p('url'),p('name'))


