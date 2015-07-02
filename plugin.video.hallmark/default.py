# -*- coding: utf-8 -*-
# Hallmark Channel Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()


UTF8          = 'utf-8'
HALLMARKBASE  = 'http://www.hallmarkchanneleverywhere.com%s'

addon         = xbmcaddon.Addon('plugin.video.hallmark')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home         = addon.getAddonInfo('path').decode(UTF8)
icon         = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart  = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


qp  = urllib.quote_plus
uqp = urllib.unquote_plus

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, user_data=None, headers = defaultHeaders , alert=True, donotuseproxy=True):

              log("getRequest URL:"+str(url))
              if (donotuseproxy==False) and (addon.getSetting('us_proxy_enable') == 'true'):
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
                 response = urllib2.urlopen(req)
                 page = response.read()
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    page = zlib.decompress(page, zlib.MAX_WBITS + 16)

              except urllib2.URLError, e:
                 if alert:
                     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 10000) )
                 page = ""
              return(page)


def getSources():
        ilist = []
        url = 'http://www.hallmarkchanneleverywhere.com/Movies?NodeID=28'
        name = 'Movies'
        u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), 'GM')
        liz=xbmcgui.ListItem(name, '',icon, None)
        liz.setProperty('fanart_image', addonfanart)
        ilist.append((u, liz, True))
        
        html = getRequest('http://www.hallmarkchanneleverywhere.com/Series?NodeID=29')
        c     = re.compile('<div class="imageviewitem">.+?src="(.+?)".+?class="commontitle" href="(.+?)">(.+?)<',re.DOTALL).findall(html)
        for  img, url, name in c:
              img = HALLMARKBASE % img
              name = h.unescape(name.decode(UTF8))
              url = HALLMARKBASE % url.replace('&amp;','&')
              html = getRequest(url)
              plot = re.compile('<div id="imageDetail">.+?</div>(.+?)<', re.DOTALL).search(html).group(1)
              plot  = h.unescape(plot.decode(UTF8)).strip()
              infoList ={}
              infoList['Title'] = name
              infoList['Plot']  = plot
              u = '%s?url=%s&name=%s&mode=GE' % (sys.argv[0], qp(url), qp(name))
              liz=xbmcgui.ListItem(name, '',None, img)
              liz.setInfo( 'Video', infoList)
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
              
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
              xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
           

def getEpis(geurl, showName):
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        html  = getRequest(uqp(geurl))
        c     = re.compile('<div class="commoneptitle".+?<span.+?">(.+?)<.+?"epsynopsis">(.+?)<.+?bc="(.+?)"',re.DOTALL).findall(html)
        for name, plot, vid in c:
              infoList ={}
              infoList['TVShowTitle'] = uqp(showName)
              infoList['Title'] = h.unescape(name.decode(UTF8))
              infoList['Plot']  = h.unescape(plot.decode(UTF8).strip())
              infoURL = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=3811967664001&playerKey=&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+vid+'&secureConnections=true&secureHTMLConnections=true'
              html = getRequest(infoURL)
              m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
              a = json.loads(html[m.start(1):m.end(1)+1])
              img = a['data']['programmedContent']['videoPlayer']['mediaDTO']['videoStillURL']

              u = '%s?url=%s&mode=GV' % (sys.argv[0], vid)
              liz=xbmcgui.ListItem(name, '',None, img)
              liz.setInfo( 'Video', infoList)
              liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width' : 1280, 
                                   'height' : 720, 
                                   'aspect' : 1.78 })
              liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
              liz.addStreamInfo('subtitle', { 'language' : 'en'})
              liz.setProperty('fanart_image', img)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
              
        if len(ilist) != 0:
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
          if addon.getSetting('enable_views') == 'true':
              xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
          xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getMovies(gmurl):
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        html  = getRequest(uqp(gmurl))
        c     = re.compile('<div class="imageviewitem">.+?src="(.+?)".+?class="commontitle" href="(.+?)">(.+?)<.+?fwmediaid = \'(.+?)\'.+?</script>',re.DOTALL).findall(html)
        for  img, murl, name, vid in c:
              html = getRequest(HALLMARKBASE % murl.replace('&amp;','&'))
              genre,mpaa,cast,plot=re.compile('<div class="moviesubtitle">(.+?)<.+?</span>(.+?)<.+?">(.+?)<.+?<div id="imageDetail">.+?</div>(.+?)<', re.DOTALL).search(html).groups()
              genre = genre.strip().replace(';',',')
              mpaa  = mpaa.strip()
              cast  = h.unescape(cast.decode(UTF8))
              cast  = cast.strip().split(';')
              plot  = h.unescape(plot.decode(UTF8)).strip()
              img = 'http://www.hallmarkchanneleverywhere.com%s' % img
              infoList ={}
              infoList['Title'] = h.unescape(name.decode(UTF8))
              infoList['Genre'] = genre
              infoList['Plot']  = plot
              infoList['MPAA']  = 'TV-'+mpaa
              infoList['Cast']  = cast
              infoList['Studio']  = 'Hallmark Channel'
              u = '%s?url=%s&mode=GV' % (sys.argv[0], vid)
              liz=xbmcgui.ListItem(name, '',None, img)
              liz.setInfo( 'Video', infoList)
              liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width' : 1280, 
                                   'height' : 720, 
                                   'aspect' : 1.78 })
              liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
              liz.addStreamInfo('subtitle', { 'language' : 'en'})
              liz.setProperty('fanart_image', img)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
              
        if len(ilist) != 0:
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
          if addon.getSetting('enable_views') == 'true':
              xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('movies_view'))
          xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(bcid):
    url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=3811967664001&playerKey=&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+bcid+'&secureConnections=true&secureHTMLConnections=true'

    html = getRequest(url)
    m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
    a = json.loads(html[m.start(1):m.end(1)+1])
    u =''
    rate = 0
    b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['renditions']
    for c in b:
           if c['encodingRate'] > rate:
              rate = c['encodingRate']
              u = c['defaultURL']
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=u))

    try:
        suburl = a['data']['programmedContent']['videoPlayer']['mediaDTO']['captions'][0]['URL']
    except:
        suburl = ''

    if (addon.getSetting('sub_enable') == "true") and (suburl != ''):
      profile = addon.getAddonInfo('profile').decode(UTF8)
      subfile = xbmc.translatePath(os.path.join(profile, 'HallmarkSubtitles.srt'))
      prodir  = xbmc.translatePath(os.path.join(profile))
      if not os.path.isdir(prodir):
         os.makedirs(prodir)

      pg = getRequest(suburl)
      if pg != "":
        ofile = open(subfile, 'w+')
        captions = re.compile('<p begin="(.+?)" end="(.+?)">(.+?)</p>',re.DOTALL).findall(pg)
        if len(captions) == 0: captions = re.compile("<p .+?begin='(.+?)'.+?end='(.+?)'.+?>(.+?)</p>",re.DOTALL).findall(pg)
        idx = 1
        for cstart, cend, caption in captions:
          cstart = cstart.replace('.',',')
          cend   = cend.replace('.',',').split('"',1)[0]
          try:
            if '<span' in caption: caption = re.compile('<span.+?>(.+?)</span').search(caption).group(1)
          except: pass
          caption = caption.replace('<br/>','\n').replace('&gt;','>').replace('&apos;',"'").replace('&quot;','"')
          ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
          idx += 1
        ofile.close()
        xbmc.sleep(3000)
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

if mode==  None:  getSources()
elif mode=='GE':  getEpis(p('url'),p('name'))
elif mode=='GM':  getMovies(p('url'))
elif mode=='GV':  getVideo(p('url'))
