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
addonName = addon.getAddonInfo('name')
addonLanguage  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (addonName, txt.encode('ascii', 'ignore'))
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
  ilist = []
  page = getRequest(RTBASE_URL+"/shows/")
  liz = xbmcgui.ListItem('RT Live', '',icon, None)
  liveUrl = '%s?url=%s&mode=GL' % (sys.argv[0],qp('abc'))
  ilist.append((liveUrl, liz, True))
  match = re.compile('<li class="card-rows__item.+?src="(.+?)".+?href="(.+?)">(.+?)<.+?class="link link_disabled".+?>(.+?)</li',re.DOTALL).findall(page)
  for img,url,name,plot in match:
       infoList = {}
       name = name.strip()
       infoList['Title'] = name
       infoList['Plot']  = h.unescape(plot.strip().replace('<p>','').replace('</p>','').decode(UTF8))
       u = '%s?url=%s&mode=GE' % (sys.argv[0],qp(url))
       liz=xbmcgui.ListItem(name)
       liz.setArt({'thumb' : img, 'fanart' : img})
       liz.setInfo( 'Video', infoList)
       ilist.append((u, liz, True))
  xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getLive():
    ilist=[]
    rlist = [("https://www.rt.com/static/libs/octoshape/js/streams/news.js", addonLanguage(30005)),
             ("https://www.rt.com/static/libs/octoshape/js/streams/usa.js", addonLanguage(30006)),
             ("https://www.rt.com/static/libs/octoshape/js/streams/uk.js", addonLanguage(30007)),
             ("https://rtd.rt.com/s/octoplayer/octoshape/js/streams.js?7", addonLanguage(30008)),
             ("https://arabic.rt.com/static/libs/octoshape/js/streams.js", addonLanguage(30010))]
    res_names  = ["Auto","HD","Hi","Medium","Low"]
    i = int(addon.getSetting('rt_res'))
    res = res_names[i]
    for url, name in rlist:
       url = url+'-'+res
       url = '%s?url=%s&mode=GV' % (sys.argv[0],qp(url))
       name = '%s (%s)' % (name, res)    
       liz=xbmcgui.ListItem(name)
       liz.setArt({'thumb' : icon, 'fanart' : addonfanart})
       liz.setProperty('IsPlayable', 'true')
       ilist.append((url, liz, False))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))




def getEpisodes(url):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   page = getRequest(RTBASE_URL+url)
   match = re.compile('static-three_med-one">.+?src="(.+?)".+?class="link link_hover" href="(.+?)">(.+?)<.+?class="card__summary ">(.+?)</',re.DOTALL).findall(page)
   ilist = []
   for img,url,name,plot in match:
       name = name.strip()
       infoList = {}
       infoList['Title'] = name
       infoList['Plot']  = h.unescape(plot.strip().replace('<p>','').replace('</p>','').decode(UTF8))
       u = '%s?url=%s&mode=GV' % (sys.argv[0],qp(url))
       liz=xbmcgui.ListItem(name)
       liz.setInfo( 'Video', infoList)
       liz.addStreamInfo('video', { 'codec': 'h264', 
                                   'width' : 1280, 
                                   'height' : 720, 
                                   'aspect' : 1.78 })
       liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
       liz.addStreamInfo('subtitle', { 'language' : 'en'})
       liz.setArt({'thumb' : img, 'fanart' : img})
       liz.setProperty('IsPlayable', 'true')
       ilist.append((u, liz, False))

   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url):
    if url.startswith('https:'):
        url = url.rsplit('-',1)
        restype = url[1]
        url = url[0]
        if 'arabic' in url:
            restype = 'Auto'
        html = getRequest(url)
        streams = re.compile("    \{caption\: '(.+?)'.+?\+ '(.+?)'", re.DOTALL).findall(html)
        if streams == []:
            streams = re.compile("\{caption\: '(.+?)'.+? \"(.+?)\"", re.DOTALL).findall(html)

        url = None
        for res, u in streams:
            if res.startswith(restype):
               url = u
               break
               
        if url is None:
            return
        if not url.startswith('http:'):
            url = 'http:'+url
    else:
        html=getRequest(RTBASE_URL+url)
        m = re.compile('file:.+?"(.+?)"',re.DOTALL).search(html)
        if m != None:
            url = m.group(1)
        else:
            m = re.compile('<div class="rtcode">.+?src="(.+?)"',re.DOTALL).search(html)
            if m != None:
               url = m.group(1)
            else:
               xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( addonName, addonLanguage(30001) , 5000) )
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
