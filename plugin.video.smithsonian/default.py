# -*- coding: utf-8 -*-
# Smithsonian Channel Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.smithsonian')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
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



def getMovies():
   ct = ("files", "movies","episodes")
   xbmcplugin.setContent(int(sys.argv[1]), ct[int(addon.getSetting('content_type'))])
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_DURATION)

   ilist=[]
   html = getRequest('http://www.smithsonianchannel.com/full-episodes')
   vids = re.compile('data-premium=".+?href="(.+?)".+?srcset="(.+?)".+?"timecode">(.+?)<.+?</li>',re.DOTALL).findall(html)
   mode = 'GV'
   for url, thumb, dur in vids:
      html = getRequest('http://www.smithsonianchannel.com%s' % url)
      m = re.compile('property="og:title" content="(.+?)"',re.DOTALL).search(html)
      title = m.group(1)
      m = re.compile('property="og:image" content="(.+?)"',re.DOTALL).search(html, m.end(1))
      iconimg = m.group(1)
      m = re.compile('"og:site_name" content="(.+?)"', re.DOTALL).search(html, m.end(1))
      studio = m.group(1)
      m = re.compile('"twitter:image" content="(.+?)"',re.DOTALL).search(html, m.end(1))
      fanart = m.group(1)
      plot = re.compile('<div class="accordion-content-mobile">.+?"description">(.+?)</p',re.DOTALL).search(html,m.end(1)).group(1)
      infoList = {}
      length = 0
      dur = dur.replace('|','').split(':')
      for d in dur: length = length*60 + int(d.strip())

      infoList['Duration']    = length

      infoList['MPAA']        = 'tv-pg'
      infoList['Title']       = h.unescape(title)
      infoList['Studio']      = studio
      infoList['Genre']       = 'Documentary'
      infoList['Plot']        = h.unescape(plot)
      name  = infoList['Title']
      u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
      liz=xbmcgui.ListItem(name, '',iconimg, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'h264', 
                                   'width' : 1920, 
                                   'height' : 1080, 
                                   'aspect' : 1.78 })
      liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
      liz.addStreamInfo('subtitle', { 'language' : 'en'})
      liz.setProperty('fanart_image', fanart)
      liz.setProperty('IsPlayable', 'true')
      ilist.append((u, liz, False))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url):
   html = getRequest('http://www.smithsonianchannel.com%s' % uqp(url))
   (suburl, vidID) = re.compile('data-vttfile="(.+?)".+?data-bcid="(.+?)"', re.DOTALL).search(html).groups()
   html = getRequest('http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=1466806621001' % (vidID))
   html = str(html)+'#'
   urls = re.compile('http(.+?)#',re.DOTALL).findall(html)
   i = int(addon.getSetting('vid_res'))
   try:
     url = 'http'+urls[i]
   except:
     url = 'http'+urls[len(urls)-1]
   url = url.strip()
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))

   if (suburl != "") and (addon.getSetting('sub_enable') == "true"):
      profile = addon.getAddonInfo('profile').decode(UTF8)
      subfile = xbmc.translatePath(os.path.join(profile, 'SCSubtitles.srt'))
      prodir  = xbmc.translatePath(os.path.join(profile))
      if not os.path.isdir(prodir):
         os.makedirs(prodir)

      cc = getRequest('http://www.smithsonianchannel.com%s'% suburl)
      if cc != "":
        ofile = open(subfile, 'w+')
        ofile.write(cc)
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

if mode==  None:  getMovies()
elif mode=='GV':  getVideo(p('url'))
