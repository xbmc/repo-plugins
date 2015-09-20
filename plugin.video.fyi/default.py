# -*- coding: utf-8 -*-
# FYI TV Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.fyi')
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
   url = 'http://www.fyi.tv/videos'
   html = getRequest(url)
   a = re.compile('<li class="span4">.+?href="(.+?)".+?src="(.+?)".+?"title">(.+?)<.+?</li',re.DOTALL).findall(html)
   for url, img, name in a:
       html = getRequest('http://www.fyi.tv%s' % url)
       try:    url  = re.compile('>Full Episode</h3>.+?href="(.+?)"',re.DOTALL).search(html).group(1)
       except: continue
       try:    plot = re.compile('property="og:description" content="(.+?)"',re.DOTALL).search(html).group(1)
       except: plot =''
       infoList = {}
       name = h.unescape(name.decode(UTF8))
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = 'FYI'
       infoList['Genre']       = ''
       infoList['Episode'] = 0
       infoList['Plot'] = h.unescape(plot.decode(UTF8))
       u = '%s?url=%s&name=%s&mode=GE' % (sys.argv[0],qp(url), qp(name))
       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setInfo( 'Video', infoList)
       liz.setProperty('fanart_image', img)
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
   html  = getRequest(uqp(url))
   url  = re.compile('>Full Episode</h3>.+?href="(.+?)"',re.DOTALL).search(html).group(1)
   html = getRequest(url)
   a  = re.compile('<div data-id="(.+?)/h3>',re.DOTALL).findall(html)
   mode = 'GV'
   for b in a:
      if not b.endswith('>Full Episode<') : continue
      url,name,plot,img   = re.compile('data-target="(.+?)".+?data-title="(.+?)".+?data-description="(.+?)".+?src="(.+?)"',re.DOTALL).search(b).groups()
      html = getRequest(uqp(url))
      url, vstatus  = re.compile("_videoPlayer.play\('(.+?)', '(.+?)'", re.DOTALL).search(html).groups()
      if vstatus != 'video': continue
      name    = h.unescape(name)
      fanart  = img
      thumb   = img

      infoList = {}
#      infoList['Duration']    = b['length']
      infoList['Title']       = name
      infoList['Studio']      = 'FYI'
      html = getRequest(url)
      infoList['Plot']        = h.unescape(plot.decode(UTF8))
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
   if len(ilist) > 0:
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
      if addon.getSetting('enable_views') == 'true':
         xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
      xbmcplugin.endOfDirectory(int(sys.argv[1]))
   else:
      xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30011) , 5000) )
      


def getVideo(url, show_name):
   suburl =''
   url = uqp(url)
   url = url.split('?',1)[0]
   surl = 'http://www.history.com/components/get-signed-signature?url=xc6n8B/%s' % url.rsplit('/',1)[1]
   print "surl = "+str(surl)
   sig = getRequest(surl).strip()
   print "sig = "+str(sig)
   url = url+'?policy=27773&metafile=false&mbr=true&format=SMIL&Tracking=true&Embedded=true&sig=%s' % sig
   print "url = "+str(url)
   html = getRequest(url)
   print "html = "+str(html)
   url  = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
   url  = url.replace('&amp;','&')
   x = url.split('.mp4',1)[0].rsplit('_',1)[1]
   url = url.replace('_%s.mp4' % x, '_2500.mp4')

   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))

   try:    suburl = re.compile('<textstream src="(.+?)"',re.DOTALL).search(html).group(1)
   except: return

   if (suburl != "") and ('dfxp' in suburl) and (addon.getSetting('sub_enable') == "true"):
      profile = addon.getAddonInfo('profile').decode(UTF8)
      subfile = xbmc.translatePath(os.path.join(profile, 'Subtitles.srt'))
      prodir  = xbmc.translatePath(os.path.join(profile))
      if not os.path.isdir(prodir):
          os.makedirs(prodir)

      pg = getRequest(suburl)
      if pg != "":
          ofile = open(subfile, 'w+')
          captions = re.compile('<p begin="(.+?)" end="(.+?)">(.+?)</p>',re.DOTALL).findall(pg)
          idx = 1
          for cstart, cend, caption in captions:
              cstart = cstart.replace('.',',')
              cend   = cend.replace('.',',').split('"',1)[0]
              caption = caption.replace('<br/>','\n').replace('&gt;','>').replace('&apos;',"'").replace('&quot;','"')
              ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
              idx += 1
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
