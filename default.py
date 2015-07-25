# -*- coding: utf-8 -*-
# Food Network Canada Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.foodnetwork.canada')
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


def getRequest(url, headers = defaultHeaders):
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
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

   ilist=[]
   url = 'http://www.foodnetwork.ca/video/'
   html = getRequest(url)
   a = re.compile('ShawVideoDrawer\(.+?drawerTitle: "(.+?)".+?categories: "(.+?)".+?\);',re.DOTALL).findall(html)
   for name, url in a[3:]:
       mode = 'GE'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],url, qp(name), mode)
       liz=xbmcgui.ListItem(name, '',None, icon)
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getEpisodes(geurl, showName):
  geurl = urllib.quote(geurl)
  xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

  ilist=[]
  url = 'http://feed.theplatform.com/f/dtjsEC/hoR6lzBdUZI9?byCategories=%s&form=cjson&count=true&startIndex=1&endIndex=50&fields=id,content,defaultThumbnailUrl,title,description,:show,:season,:episode,pubdate,availableDate,:clipType,restrictionID,:allowHTML5&sort=pubDate|desc&callback=' % geurl
  html  = getRequest(url)
  a = json.loads(html)['entries']
  mode = 'GV'
  for b in a:
      url     = 'https://foodnetwork-vh.akamaihd.net/i/%s_,high,highest,medium,low,lowest,_16x9.mp4.csmil/master.m3u8' % b['defaultThumbnailUrl'].rsplit('_',2)[0].split('http://media.foodnetwork.ca/videothumbnails/',1)[1]
      name    = h.unescape(b['title']).encode(UTF8)
      fanart  = b['defaultThumbnailUrl'].rsplit('_',2)[0]+'.png'
      thumb   = fanart

      infoList = {}
      infoList['Duration']    = int(b['content'][0]['duration'])
      infoList['Title']       = name
      try: infoList['Studio']      = b['pl1$network']
      except: pass
      infoList['Date']        = datetime.datetime.fromtimestamp(b['pubDate']/1000).strftime('%Y-%m-%d')
      infoList['Aired']       = infoList['Date']
      infoList['Year']        = int(infoList['Date'].split('-',1)[0])
      try:    infoList['Episode'] = int(b['pl1$episode'])
      except: infoList['Episode'] = None
      try:    infoList['Season']  = int(b['pl1$season'])
      except: infoList['Season']  = 1
      infoList['Plot']        = h.unescape(b["description"])
      infoList['TVShowTitle'] = b['pl1$show']
      u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
      liz=xbmcgui.ListItem(name, '',icon, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width' : 960, 
                                   'height' : 540, 
                                   'aspect' : 1.78 })
      liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
      liz.addStreamInfo('subtitle', { 'language' : 'en'})
      liz.setProperty('fanart_image', fanart)
      liz.setProperty('IsPlayable', 'true')
      ilist.append((u, liz, False))
  xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
  if addon.getSetting('enable_views') == 'true':
    xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url, show_name):
   url = uqp(url)
   xurl = url.split('/i/',1)[1].split('_,high',1)[0]
   suburl = 'http://media.foodnetwork.ca/videothumbnails/%s.vtt' % xurl

   req = urllib2.Request(url.encode(UTF8), None, defaultHeaders)
   try:
      response = urllib2.urlopen(req, timeout=20) # check to see if video file exists
   except:
      url = 'https://foodnetwork-vh.akamaihd.net/i/,%s.mp4,.csmil/master.m3u8' % xurl

   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))

   if (addon.getSetting('sub_enable') == "true") and (suburl != ''):
      profile = addon.getAddonInfo('profile').decode(UTF8)
      subfile = xbmc.translatePath(os.path.join(profile, 'Subtitles.srt'))
      prodir  = xbmc.translatePath(os.path.join(profile))
      if not os.path.isdir(prodir):
         os.makedirs(prodir)

      pg = getRequest(suburl)
      if pg != "":
        ofile = open(subfile, 'w+')
        ofile.write(pg)
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

if mode==  None:  getShows()
elif mode=='GE':  getEpisodes(p('url'), p('name'))
elif mode=='GV':  getVideo(p('url'), p('name'))
