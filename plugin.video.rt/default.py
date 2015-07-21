# -*- coding: utf-8 -*-
# Kodi Addon for Russia Today
import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'
RTBASE_URL    = 'http://www.rt.com'

addon         = xbmcaddon.Addon('plugin.video.rt')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))
profile       = addon.getAddonInfo('profile').decode(UTF8)
pdir  = xbmc.translatePath(os.path.join(profile))
if not os.path.isdir(pdir):
   os.makedirs(pdir)

metafile      = xbmc.translatePath(os.path.join(profile, 'shows.json'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
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
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
  ilist = []
  page = getRequest(RTBASE_URL+"/shows/")
  liz = xbmcgui.ListItem('RT Live', '',icon, None)
  liveUrl = '%s?url=%s&mode=GL' % (sys.argv[0],qp('abc'))
  ilist.append((liveUrl, liz, True))
  match = re.compile('card-rows__content .+?src="(.+?)".+?class="link link_hover" href="(.+?)">(.+?)<.+?class="link link_disabled".+?>(.+?)</a',re.DOTALL).findall(page)
  for img,url,name,plot in match:
       infoList = {}
       infoList['Title'] = name
       infoList['Plot']  = plot.strip().replace('<p>','').replace('</p>','')
       u = '%s?url=%s&mode=GE' % (sys.argv[0],qp(url))
       liz=xbmcgui.ListItem(name, '',img, None)
       liz.setInfo( 'Video', infoList)
       liz.setProperty('fanart_image', img)
       ilist.append((u, liz, True))
  xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
  if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getLive():
    ilist=[]
    rlist = [("http://rt-a.akamaihd.net/ch_01@325605/%s.m3u8", __language__(30005)),
             ("http://rt-a.akamaihd.net/ch_04@325608/%s.m3u8", __language__(30006)),
             ("http://rt-a.akamaihd.net/ch_05@325609/%s.m3u8", __language__(30007)),
             ("http://rt-a.akamaihd.net/ch_06@325610/%s.m3u8", __language__(30008)),
             ("http://rt-a.akamaihd.net/ch_02@325606/%s.m3u8", __language__(30009)),
             ("http://rt-a.akamaihd.net/ch_03@325607/%s.m3u8", __language__(30010))]
    res_names = ["Auto","720p","480p","320p","240p"]
    i = int(addon.getSetting('rt_res'))
    res = res_names[i]
    if res == "Auto": res = "master"
    res_str = res_names[i]
    for url, name in rlist:
       url = url % res
       name = '%s%s' % (name, res_str)    
       liz=xbmcgui.ListItem(name, '',icon, None)
       liz.setProperty('fanart_image', addonfanart)
       liz.setProperty('IsPlayable', 'true')
       ilist.append((url, liz, False))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))




def getEpisodes(url):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

   page = getRequest(RTBASE_URL+url)
   match = re.compile('static-three_med-one">.+?src="(.+?)".+?class="link link_hover" href="(.+?)">(.+?)<.+?class="card__summary ">(.+?)</',re.DOTALL).findall(page)
   ilist = []
   for img,url,name,plot in match:
       infoList = {}
       infoList['Title'] = name
       infoList['Plot']  = plot.strip().replace('<p>','').replace('</p>','')
       u = '%s?url=%s&mode=GV' % (sys.argv[0],qp(url))
       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setInfo( 'Video', infoList)
       liz.addStreamInfo('video', { 'codec': 'h264', 
                                   'width' : 1280, 
                                   'height' : 720, 
                                   'aspect' : 1.78 })
       liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
       liz.addStreamInfo('subtitle', { 'language' : 'en'})
       liz.setProperty('fanart_image', img)
       liz.setProperty('IsPlayable', 'true')
       ilist.append((u, liz, False))

   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url):
    print "url = "+str(url)
    html=getRequest(RTBASE_URL+url)
    try:
        m = re.compile('file:.+?"(.+?)"',re.DOTALL).search(html)
        url = m.group(1)
    except:
        m = re.compile('<div class="rtcode">.+?src="(.+?)"',re.DOTALL).search(html)
        try:
           url = m.group(1)
        except:
           xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30001) , 5000) )
           return
        if not url.startswith('http'): url = 'http:'+url
        html = getRequest(url)
        m = re.compile('"hls_stream":"(.+?)"',re.DOTALL).search(html)
        url = m.group(1)
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

if mode==  None:  getShows()
elif mode=='GE':  getEpisodes(p('url'))
elif mode=='GV':  getVideo(p('url'))
elif mode=='GL':  getLive()
