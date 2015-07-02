# -*- coding: utf-8 -*-
# MeTV Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus


UTF8     = 'utf-8'
METVBASE = 'http://metvnetwork.com%s'

addon         = xbmcaddon.Addon('plugin.video.metv')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
defaultHeaders = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'} 

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
   pg = getRequest(METVBASE % '/videos/')
   m = re.compile('<div class="video-library-list clearfix">(.+?)video-library-list -->',re.DOTALL).search(pg)
   shows = re.compile('href="(.+?)".+?src="(.+?)".+?<h2>(.+?)<',re.DOTALL).findall(pg,m.start(1),m.end(1))
   for url, img, name in shows:
       pg = getRequest(METVBASE % url)
       img = METVBASE % img
       try:
          (cathead,catsyn)=re.compile('<span class="new-episodes">(.+?)<.+?"video-landing-main-desc-wrap clearfix".+?-->(.+?)<',re.DOTALL).search(pg).groups()
          plot = '%s \n %s' % (cathead.strip(), catsyn.strip())
       except:
          plot = re.compile('"video-landing-main-desc-wrap clearfix".+?-->(.+?)<',re.DOTALL).search(pg).group(1).strip()
       name = name.strip()
       fanart = addonfanart
       infoList = {}
       infoList['MPAA']        = ''
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = 'MeTV'
       infoList['Genre']       = ''
       infoList['Plot'] = h.unescape(plot.decode(UTF8))
       mode = 'GE'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
       liz=xbmcgui.ListItem(name, '',icon, img)
       liz.setInfo( 'Video', infoList)
       liz.setProperty('fanart_image', fanart)
       ilist.append((u, liz, True))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getEpisodes(eurl, showName):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

   ilist=[] 
   pg = getRequest(METVBASE % eurl)
   try:
      showName = re.compile('class="new-episodes">.+?<h2>(.+?)</h2>',re.DOTALL).search(pg).group(1)
   except:
      showName = 'MeTV'
   m = re.compile('<img class="video-landing-billboard" src="(.+?)"',re.DOTALL).search(pg)
   fanart = METVBASE % m.group(1)
   m = re.compile('<div class="video-landing-episodes-wrap clearfix">(.+?)video-landing-episodes-wrap -->',re.DOTALL).search(pg, m.end(1))
   episodes = re.compile('episode-title"><a href="(.+?)">(.+?)<.+?thumb-img" src="(.+?)".+?episode-desc">(.+?)<',re.DOTALL).findall(pg,m.start(1),m.end(1))
   for showpage, name, thumb, plot in episodes:
      plot = plot.replace('</span>','')
      try:
         url = re.compile('/media/(.+?)/').search(thumb).group(1)
      except:
         url = 'BADASS'+showpage
      u = "%s?url=%s&name=%s&mode=GV" %(sys.argv[0], qp(url), qp(name))
      infoList = {}
      infoList['MPAA']        = ''
      infoList['TVShowTitle'] = showName
      infoList['Title']       = name
      infoList['Studio']      = 'MeTV'
      infoList['Genre']       = ''
      infoList['Season']      = 0
      infoList['Episode']     = -1
      infoList['Plot']        = h.unescape(plot)
      liz=xbmcgui.ListItem(name, '',None, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'mp4', 
                                   'width' : 720, 
                                   'height' : 480, 
                                   'aspect' : 1.37 })
      liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
      liz.addStreamInfo('subtitle', { 'language' : 'en'})
      liz.setProperty('fanart_image', fanart)
      liz.setProperty('IsPlayable', 'true')
      ilist.append((u, liz, False))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getUrl(mediaID):
     if mediaID.startswith('BADASS'):
        mediaID = METVBASE % mediaID.replace('BADASS','')
        pg = getRequest(mediaID)
        mediaID = re.compile('mediaId=(.+?)&',re.DOTALL).search(pg).group(1)

     a = json.loads(getRequest('http://production-ps.lvp.llnw.net/r/PlaylistService/media/%s/getPlaylistByMediaId' % mediaID))
     show_url=''
     highbitrate = float(0)
     for stream in a['playlistItems'][0]['streams']:
         bitrate = float(stream['videoBitRate'])
         if bitrate > highbitrate:
            show_url = stream['url']
            highbitrate = float(bitrate)
     show_url  = show_url.split('mp4:',1)[1]
     finalurl  = 'http://s2.cpl.delvenetworks.com/%s' % show_url
     return finalurl



def getVideo(url, show_name):
    url = uqp(url)
    if (addon.getSetting('sub_enable') == "true"):
       try:
           a = json.loads(getRequest('http://api.video.limelight.com/rest/organizations/abee2d5fad8944c790db6a0bfd3b9ebd/media/%s/properties.json' % url))
           xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = getUrl(url)))
           try: 
               subfile = a["captions"][0]["url"]
               xbmc.sleep(2000)
               xbmc.Player().setSubtitles(subfile)
           except:
               pass
       except:
           pass
    else:
       xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = getUrl(url)))

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
