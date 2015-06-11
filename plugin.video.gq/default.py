# -*- coding: utf-8 -*-
# GQ Magazine Video Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.gq')
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


def getShows():
   xbmcplugin.setContent(int(sys.argv[1]), 'files')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
   ilist=[]

   dolist = [('GE', 30081, icon, '/new.js?page=1'),('GE', 30082, icon, '/popular.js?page=1')]
   for mode, gstr, img, url in dolist:
       name = __language__(gstr)
       liz  = xbmcgui.ListItem(name,'',img,img)
       liz.setProperty('fanart_image', addonfanart)
       xbmcplugin.addDirectoryItem(int(sys.argv[1]), '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), mode), liz, True)

   html = getRequest('http://video.gq.com/categories')
   a    = re.compile('class="cne-nav--drawer__item--categories".+?="(.+?)".+?src="(.+?)".+?categories">(.+?)<' , re.DOTALL).findall(html)
   for url, img, name in a:
       name = h.unescape(name.decode(UTF8))
       url  = h.unescape(url)
       url += '.js?page=1'
       vidcnt = 1
       infoList = {}
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = __language__(30010)
       infoList['Genre']       = ''
       try:    infoList['Episode'] = int(vidcnt)
       except: infoList['Episode'] = 0
       infoList['Plot'] = name
       mode = 'GE'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],url, qp(name), mode)
       liz=xbmcgui.ListItem(name, '',None,img)
       liz.setInfo( 'Video', infoList)
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getEpisodes(url, showName):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

   ilist=[]
   url = 'http://video.gq.com%s' % uqp(url)
   azheaders = defaultHeaders
   azheaders['X-Requested-With'] = 'XMLHttpRequest'
   html = getRequest(url,None, azheaders).replace('\\n','').replace('\\','')
   shows = re.compile('<div class="cne-thumb cne-episode-block ".+?data-videoid=.+?href="(.+?)".+?<img.+?alt="(.+?)".+?src="(.+?)".+?"cne-rollover-description">(.+?)<',re.DOTALL).findall(html)
   mode = 'GV'
   for url,name,thumb,plot in shows:
      infoList = {}
      plot = plot.strip()
      infoList['Title']       = h.unescape(name.decode(UTF8))
      infoList['Studio']      = 'GQ'
      infoList['Plot']        = h.unescape(plot.decode(UTF8))
      infoList['TVShowTitle'] = showName
      u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
      liz=xbmcgui.ListItem(name, '',None, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width' : 1920, 
                                   'height' :1080, 
                                   'aspect' : 1.78 })
      liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
      liz.addStreamInfo('subtitle', { 'language' : 'en'})
      liz.setProperty('fanart_image', addonfanart)
      liz.setProperty('IsPlayable', 'true')
      ilist.append((u, liz, False))

   try:
       url = re.compile("'ajaxurl'.+?'(.+?)'",re.DOTALL).search(html).group(1)
       name ='[COLOR red]%s[/COLOR]' % (__language__(30084))
       mode = 'GE'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
       liz=xbmcgui.ListItem(name, '',icon,None)
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
   except:
      pass
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url, show_name):
   html = getRequest('http://video.gq.com/%s' % uqp(url)).replace('\\n','').replace('\\','')
   url  = re.compile('"contentURL" href="(.+?)"', re.DOTALL).search(html).group(1)
   if addon.getSetting('vid_res') == '1':
       url = url.replace('low.mp4','high.mp4')
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))


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
elif mode=='GE':  getEpisodes(p('url'), p('name'))
elif mode=='GV':  getVideo(p('url'), p('name'))
