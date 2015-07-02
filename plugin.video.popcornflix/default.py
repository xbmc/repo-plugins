# -*- coding: utf-8 -*-
# Popcornflix XBMC Addon

import sys
import httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.popcornflix')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
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

    if addon.getSetting('us_proxy_enable') == 'true':
        us_proxy = 'http://%s:%s' % (addon.getSetting('us_proxy'), addon.getSetting('us_proxy_port'))
        proxy_handler = urllib2.ProxyHandler({'http':us_proxy})
        if addon.getSetting('us_proxy_pass') <> '' and addon.getSetting('us_proxy_user') <> '':
            log('Using authenticated proxy: ' + us_proxy)
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, us_proxy, addon.getSetting('us_proxy_user'), addon.getSetting('us_proxy_pass'))
            proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
            opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
        else:
            log('Using proxy: ' + us_proxy)
            opener = urllib2.build_opener(proxy_handler)
    else:   
        opener = urllib2.build_opener()
    urllib2.install_opener(opener)

#    log("getRequest URL:"+str(url))
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
    html = getRequest('http://www.popcornflix.com')
    m  = re.compile('>Home<(.+?)</ul',re.DOTALL).search(html)
    cats = re.compile('<a href="(.+?)">(.+?)</a>',re.DOTALL).findall(html, m.start(1),m.end(1))
    cats = cats[0:2]
    m = re.compile('Genres(.+?)<div class=',re.DOTALL).search(html)
    c2 = re.compile('<a href="(.+?)">(.+?)</a>',re.DOTALL).findall(html, m.start(1),m.end(1))
    cats.extend(c2)
    for url,name in cats:
       name = '[COLOR blue]'+name+'[/COLOR]'
       mode = 'GM'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],url, qp(name), mode)
       liz=xbmcgui.ListItem(name, '',icon,None)
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

    

def getMovies(url):
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

    ilist =[]
    cat_url = 'http://www.popcornflix.com%s' % (url)
    html    = getRequest(cat_url)
    m = re.compile('<div class="b-videos panes floated">(.+?)</ul',re.DOTALL).search(html)
    if m != None:
       shows=re.compile('<figure>.+?href="(.+?)".+?src="(.+?)".+?title">(.+?)<(.+?)genre">(.+?)<.+?desc">(.+?)<.+?</li>',re.DOTALL).findall(html,m.start(1),m.end(1)) 
    else:
       shows=re.compile('<figure>.+?href="(.+?)".+?src="(.+?)".+?title">(.+?)<(.+?)genre">(.+?)<.+?desc">(.+?)<.+?</li>',re.DOTALL).findall(html)
    for sid,thumb,name,blob,genre,plot in shows:
      if (not sid.startswith('/series')) and (not sid.startswith('/tv-shows')):
         infoList = {} 
         actors, rating, duration = re.compile('actors">(.+?)<.+?rating">(.+?)<.+?duration">(.+?)<',re.DOTALL).search(blob).groups()
         plot = plot.strip()
         infoList['Plot']  = plot.strip()
         infoList['Genre'] = genre
         infoList['Title'] = name
         if   rating == 'R'  : rating = 'Rated R'
         elif rating == 'PG-13' : rating = 'Rated PG-13'
         elif rating == 'PG' : rating = 'Rated PG'
         elif rating == 'G'  : rating = 'Rated G'
         infoList['MPAA']  = rating
         infoList['duration'] = int(duration)*60
         infoList['cast'] = actors.split(',')
         sid = sid.rsplit('/',1)[1]
         u= "%s?url=%s&mode=GV" %(sys.argv[0], sid)
         liz=xbmcgui.ListItem(name, '',None, thumb)
         liz.setInfo( 'Video', infoList)
         liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width'  : 852, 
                                   'height' : 480, 
                                   'aspect' : 1.78 })
         liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
         liz.addStreamInfo('subtitle', { 'language' : 'en'})
         liz.setProperty('fanart_image', addonfanart)
         liz.setProperty('IsPlayable', 'true')
         ilist.append((u, liz, False))

      else:
         name = '[COLOR blue]'+name+'[/COLOR]'
         u = '%s?url=%s&mode=GM' % (sys.argv[0],sid)
         liz=xbmcgui.ListItem(name, '',None,thumb)
         liz.setProperty('fanart_image', addonfanart)
         ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
       xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('movie_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
       

def getVideo(sid):
      html = getRequest('http://popcornflixv2.device.screenmedia.net/api/videos/%s' % (sid))
      a = json.loads(html)
      try:
         url = a['movies'][0]['urls']['Web v2 Player']
         html = getRequest(url)

         html += '#'
         playlist = re.compile('BANDWIDTH=([0-9]*).+?tp:(.+?)#',re.DOTALL).findall(html)
         bitrates = [150000, 240000, 340000, 440000, 552000, 640000, 840000, 1240000, 2400000]
         try:
           urate    = bitrates[int(addon.getSetting('bitrate'))]
         except:
           urate = 150000
         current  = 0
         for bitrate,pp in playlist:
          if (int(bitrate) <= int(urate)) and (current < int(bitrate)):
            current = int(bitrate)
            playpath = pp
         if current == 0: (current, playpath) = playlist[0]
         url = 'http:'+playpath
         url  = url.strip()
         xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))
      except:
       dialog = xbmcgui.Dialog()
       dialog.ok(__language__(30000), '',__language__(30001))
 


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

mode = p('mode', None)

if mode==  None:  getSources()
elif mode=='GM':  getMovies(p('url'))
elif mode=='GV':  getVideo(p('url'))



