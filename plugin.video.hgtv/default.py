# -*- coding: utf-8 -*-
# HGTV Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.hgtv')
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
   url = 'http://www.hgtv.com/shows/full-episodes'
   html = getRequest(url)

   a  =[]
   try:
      name, vidcnt, img = re.compile('"video-player-embedded">.+?<h3>(.+?)</h3>.+?"total"\: (.+?),.+?"thumbnailUrl" \: "(.+?)"', re.DOTALL).search(html).groups()
      plot = ''
      a.append((icon, url, name, '%s Videos' % vidcnt))
   except: pass

   m = re.compile('<div class="video-player-embedded">(.+?)<section class="text-promo module">', re.DOTALL).search(html)
   b = re.compile('<li class="block">.+?src="(.+?)".+?href="(.+?)">(.+?)<.+?noWrap">(.+?)<.+?</li>', re.DOTALL).findall(html, m.start(1),m.end(1))
   a.extend(b)


   for img, url, name, vidcnt in a:
       name=name.strip()
       vidcnt = vidcnt.strip()
       infoList = {}
       try:    infoList['Episode'] = int(vidcnt.split(' ',1)[0])
       except: infoList['Episode'] = 0
       if infoList['Episode'] == 0: continue
       html = getRequest(url.rsplit('/',1)[0])
       try:    plot = re.compile('"og:description" content="(.+?)"',re.DOTALL).search(html).group(1)
       except: plot = name
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = 'HGTV'
       infoList['Genre']       = ''
       infoList['Plot'] = h.unescape(plot)
       mode = 'GE'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],url, qp(name), mode)
       liz=xbmcgui.ListItem(name, '',None, img)
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
   html  = getRequest(url)
   html    = re.compile("data\-video\-prop='(.+?)'></div>",re.DOTALL).search(html).group(1)
   a = json.loads(html)
   a = a['channels'][0]['videos']
   mode = 'GV'
   for b in a:
      url     = b['releaseUrl']
      name    = h.unescape(b['title'])
      fanart  = 'http://www.hgtv.com%s' % b['thumbnailUrl']
      thumb   = 'http://www.hgtv.com%s' % b['thumbnailUrl']

      infoList = {}
      infoList['Duration']    = b['length']
      infoList['Title']       = name
      infoList['Studio']      = b['publisherId']
      html = getRequest(url)
      months = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
      try:
         dstr = (re.compile('"premierDate" value="(.+?)"',re.DOTALL).search(html).group(1)).split(' ')
         dt   = '%s-%s-%s' % (dstr[5],months[dstr[1]],dstr[2])
         infoList['Date']        = dt
         infoList['Aired']       = infoList['Date']
      except: pass
      try:    infoList['MPAA'] = re.compile('ratings="(.+?)"',re.DOTALL).search(html).group(1).split(':',1)[1]
      except: infoList['MPAA'] = None
      try:    infoList['Episode'] = int(re.compile('"episodeNumber" value=".(.+?)H"',re.DOTALL).search(html).group(1).replace('Z',''), 16)
      except: infoList['Episode'] = None
      try:    infoList['Season']  = int(re.compile('"episodeNumber" value="(.+?)H"',re.DOTALL).search(html).group(1).replace('Z',''),16)/256
      except: infoList['Season']  = 1
      infoList['Plot']        = h.unescape(b["description"])
      infoList['TVShowTitle'] = showName
      u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
      liz=xbmcgui.ListItem(name, '',icon, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width' : 1280, 
                                   'height' : 720, 
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
   html   = getRequest(uqp(url))
   try:    
           subs = re.compile('<textstream src="(.+?)"',re.DOTALL).findall(html)
           suburl =''
           for st in subs:
             if '.srt' in st:
                suburl = st
                break
   except: pass
   try:
     url   = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
     if int(addon.getSetting('vid_res')) == 0: url = url.replace('_6.','_3.')
   except:
     url, msg   = re.compile('<ref src="(.+?)".+?abstract="(.+?)"',re.DOTALL).search(html).groups()
     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, msg , 5000) )
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))

   if (addon.getSetting('sub_enable') == "true") and (suburl != ''):
      profile = addon.getAddonInfo('profile').decode(UTF8)
      subfile = xbmc.translatePath(os.path.join(profile, 'DIYSubtitles.srt'))
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
