# -*- coding: utf-8 -*-
# NPR Music Kodi Video Addon

import sys, httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8          = 'utf-8'
NPRBASE = 'http://www.npr.org%s'

addon         = xbmcaddon.Addon('plugin.video.npr')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
iconNext      = xbmc.translatePath(os.path.join(home, 'next.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
#USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, user_data=None, headers = defaultHeaders , alert=True):

    opener = urllib2.build_opener()
    urllib2.install_opener(opener)

    log("getRequest URL:"+str(url))
    req = urllib2.Request(url.encode(UTF8), user_data, headers)

    try:
       response = urllib2.urlopen(req, timeout=30)
       page = response.read()
       if response.info().getheader('Content-Encoding') == 'gzip':
           log("Content Encoding == gzip")
           page = zlib.decompress(page, zlib.MAX_WBITS + 16)

    except urllib2.URLError, e:
       if alert:
           xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 5000) )
       page = ""

    return(page)


def getSources():
              ilist = []
              urlbase   = NPRBASE % ('/sections/music-videos/')
              html = getRequest(urlbase)
              name = __language__(30000)
              urlbase = NPRBASE % ('/series/15667984/favorite-sessions')
              u = '%s?url=%s&mode=GC' % (sys.argv[0],urlbase.encode(UTF8))
              liz=xbmcgui.ListItem(name, '',icon, None)
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))

              m = re.compile('<div class="subtopics">(.+?)</ul>',re.DOTALL).search(html)
              cats = re.compile('<a href="(.+?)">(.+?)<',re.DOTALL).findall(html,m.start(1),m.end(1))
              for url, name in cats:
                  url = NPRBASE % (url)
                  u = '%s?url=%s&mode=GC' % (sys.argv[0],url)
                  liz=xbmcgui.ListItem(name, '',icon, None)
                  liz.setProperty('fanart_image', addonfanart)
                  ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
              if addon.getSetting('enable_views') == 'true':
                 xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
              xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getCats(url):
             xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
             xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
             xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
             xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
             xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

             ilist =[]
             html = getRequest(url)
             nexturl = url
             blobs = re.compile('<article class(.+?)</article>',re.DOTALL).findall(html)
             curlink  = 0
             nextlink = 1
             for blob in blobs:
               nextlink = nextlink+1
               if ('article-video' in blob) or ('type-video' in blob):
                 try:
                    (url, thumb, name, dt, plot) = re.compile('<a href="(.+?)".+?src="(.+?)".+?title="(.+?)".+?<time datetime="(.+?)".+?</time>(.+?)</p',re.DOTALL).search(blob).groups()
                 except:
                    (url, thumb, name) = re.compile('<a href="(.+?)".+?src="(.+?)".+?title="(.+?)"',re.DOTALL).search(blob).groups()
                    plot = name
                    dt   = ''
                 name = h.unescape(name)
                 plot = h.unescape(plot.strip().decode('utf-8'))
                 infoList ={}
                 infoList['Title'] = name
                 infoList['date']  = dt
                 infoList['Plot']  = plot
                 try: infoList['Year'] = int(dt.split('-',1)[0])
                 except: pass
                 u = "%s?url=%s&mode=GV" %(sys.argv[0], qp(url))
                 liz=xbmcgui.ListItem(name, '',None, thumb)
                 liz.setInfo( 'Video', infoList)
                 liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width' : 1280, 
                                   'height' : 720, 
                                   'aspect' : 1.78 })
                 liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
                 liz.addStreamInfo('subtitle', { 'language' : 'en'})
                 liz.setProperty('fanart_image', addonfanart)
                 liz.setProperty('IsPlayable', 'true')
                 ilist.append((u, liz, False))

             curlink=0
             nextstr = '/archive?start='
             if (nextstr in nexturl):
                (nexturl,curlink) = nexturl.split(nextstr,1)
                curlink = int(curlink)
             nextlink = str(nextlink+curlink+1)
             url = nexturl+nextstr+nextlink
             name = '[COLOR red]%s[/COLOR]' % (__language__(30001))
             u = '%s?url=%s&mode=GC' % (sys.argv[0],url)
             liz=xbmcgui.ListItem(name, '',iconNext, None)
             liz.setProperty('fanart_image', addonfanart)
             ilist.append((u, liz, True))
             xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
             if addon.getSetting('enable_views') == 'true':
                xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
             xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url):
            html = getRequest(uqp(url))
            try:
                finalurl = re.compile("'SD'.+?file:'(.+?)'",re.DOTALL).search(html).group(1)
            except:
                try:
                    videoid = re.compile('<div class="video-wrap">.+?src="http://www\.youtube\.com/embed/(.+?)\?',re.DOTALL).search(html).group(1)
                    finalurl = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (videoid)
                except:
                    dialog = xbmcgui.Dialog()
                    dialog.ok(__language__(30002), '',__language__(30003)) #tell them no video found
                    return
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))


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

if mode==  None:  getSources()
elif mode=='GC':  getCats(p('url'))
elif mode=='GV':  getVideo(p('url'))


