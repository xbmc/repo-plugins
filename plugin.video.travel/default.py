# -*- coding: utf-8 -*-
# Travel Channel Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.travel')
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
   html = getRequest('http://www.travelchannel.com/shows/whats-new-on-travel-channel/articles/full-episodes')
   m = re.compile('<article(.+?)</article',re.DOTALL).search(html)
   a = re.compile('<section class="topn-wrapper">.+?<a href="(.+?)".+?blank">(.+?)<.+?src="(.+?)".+?<p>(.+?)<.+?</section>', re.DOTALL).findall(html,m.start(1),m.end(1))
   a[(len(a)-1)] = ('/video/p/1?wcmmode=disabled',__language__(30021),icon,__language__(30021))
   for url,name,img,plot in a:
       html  = getRequest('http://www.travelchannel.com%s' % url, alert=False)
       c     = re.compile("data\-videoplaylist\-data='(.+?)'>", re.DOTALL).findall(html)
       if len(c) == 0: continue
       else: vidcnt = len(c)
       name=name.strip()
       fanart = img
       infoList = {}
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = __language__(30010)
       infoList['Genre']       = ''
       try:    infoList['Episode'] = int(vidcnt)
       except: infoList['Episode'] = 0
       infoList['Plot'] = h.unescape(plot)
       mode = 'GE'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setInfo( 'Video', infoList)
       liz.setProperty('fanart_image', fanart)
       ilist.append((u, liz, True))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getEpisodes(geurl, showName):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

   ilist=[]
   html  = getRequest('http://www.travelchannel.com%s' % uqp(geurl))
   c     = re.compile("data\-videoplaylist\-data='(.+?)'>", re.DOTALL).findall(html)
   mode = 'GV'
   for a in c:
      b = json.loads(a)
      url     = b['releaseUrl']
      html = getRequest(url)
      name    = h.unescape(b['title'])
      fanart  = 'http://www.travelchannel.com%s' % b['thumbnailUrl']
      thumb   = 'http://www.travelchannel.com%s' % b['thumbnailUrl']

      infoList = {}
      infoList['Duration']    = b['length']
      infoList['Title']       = name
      infoList['Studio']      = b['publisherId']
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

   if len(ilist) != 0:
      if 'wcmmode=disabled' in geurl:
        name = '[COLOR red]%s[/COLOR]' % __language__(30012)
        mode = 'GE'
        url = '/video/p/%s?wcmmode=disabled' % str(int(geurl[9])+1)
        u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
        liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
        liz.setInfo( 'Video', { "Title": name, "Studio":showName, "Plot": name })
        liz.setProperty('fanart_image', addonfanart)
        ilist.append((u, liz, True))

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
