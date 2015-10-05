# -*- coding: utf-8 -*-
# TCM Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus


UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.tcm')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 'Accept':"text/html,*/*", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, udata=None, headers = defaultHeaders):
#   log("getRequest URL:"+str(url))
   req = urllib2.Request(url.encode(UTF8), udata, headers)
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
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

    pg = getRequest('http://api.tcm.com//tcmws/v1/vod/tablet/catalog/orderBy/title.jsonp')
    a = json.loads(pg)
    epis = a['tcm']['titles']
    ilist = []
    for b in epis:
       url   = b['vod']['contentId']
       name  = b['name']
       try: thumb = b['imageProfiles'][1]['url']
       except: thumb = b['vod']['associations']['franchises'][0]['imageProfiles'][0]['url']
       fanart = thumb
       infoList = {}
       infoList['Title'] = name
       
       try:    infoList['Plot'] = b['description']
       except: pass
       try:    infoList['Duration'] = str(int(b['runtimeMinutes'])*60)
       except: pass
       try:    infoList['Year'] = b['releaseYear']
       except: pass
       try:    infoList['director'] = b['tvDirectors'].strip('.')
       except: pass
       try:    infoList['cast'] = b['tvParticipants'].split(',')
       except: pass
       try:    infoList['genre'] = b['tvGenres']
       except: pass
       try:    infoList['mpaa'] = 'Rated: %s' % b['tvRating']
       except: pass

       u = "%s?url=%s&mode=GV" %(sys.argv[0], qp(url))
       liz=xbmcgui.ListItem(name, '',None, thumb)
       liz.setInfo( 'Video', infoList)
       liz.addStreamInfo('video', { 'codec': 'mp4', 
                                   'width' : 1280, 
                                   'height' : 720, 
                                   'aspect' : 1.78 })
       liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
       liz.addStreamInfo('subtitle', { 'language' : 'en'})
       liz.setProperty('fanart_image', fanart)
       liz.setProperty('IsPlayable', 'true')
       ilist.append((u, liz, False))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getVideo(vid):
   pg = getRequest('http://www.tcm.com/tveverywhere/services/videoXML.do?id=%s' % vid)
   url = re.compile('<file bitrate="2048".+?>(.+?)<',re.DOTALL).search(pg).group(1)
   filename = url[1:len(url)-4]

   a=re.compile('<akamai>(.+?)</akamai>', re.DOTALL).search(pg).group(1)
   rtmpServer = re.compile('<src>(.+?)</src>',re.DOTALL).search(a).group(1).split('://')[1]
   aifp = re.compile('<aifp>(.+?)</aifp>', re.DOTALL).search(a).group(1)
   window = re.compile('<window>(.+?)</window>', re.DOTALL).search(a).group(1)
   tokentype = re.compile('<authTokenType>(.+?)</authTokenType>', re.DOTALL).search(a).group(1)

   udata = urllib.urlencode({'aifp': aifp, 'window': window, 'authTokenType': tokentype, 'videoId' : vid, 'profile': 'tcm', 'path': filename.replace('mp4:','')})

   pg = getRequest('http://www.tbs.com/processors/cvp/token.jsp', udata)
   authtoken = re.compile('<token>(.+?)</').search(pg).group(1)

   swfURL = 'http://z.cdn.turner.com/xslo/cvp/plugins/akamai/streaming/osmf1.6/2.10/AkamaiAdvancedStreamingPlugin.swf'
   url = 'rtmpe://' + rtmpServer + '?' + authtoken + ' playpath=' + filename + ' swfurl=' + swfURL + ' swfvfy=true'
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
elif mode=='GV':  getVideo(p('url'))
