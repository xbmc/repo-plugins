# -*- coding: utf-8 -*-
# SONY LIV Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.sonyliv')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home         = addon.getAddonInfo('path').decode(UTF8)
icon         = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart  = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))
nextIcon     = xbmc.translatePath(os.path.join(home, 'resources','media','next.png'))
pageSize     = int(addon.getSetting('page_size'))


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
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        ilist = []
        url = 'http://www.sonyliv.com/show/allMovies?offset=0&max=%s' %  str(pageSize)
        name = 'Movies'
        u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), 'GM')
        liz=xbmcgui.ListItem(name, '',icon, None)
        liz.setProperty('fanart_image', addonfanart)
        ilist.append((u, liz, True))
        
        html = getRequest('http://www.sonyliv.com/show/list')
        a = re.compile('<div class="item genre.+?src=(.+?) .+?href="(.+?)">(.+?)<',re.DOTALL).findall(html)
        for iconImg,url,name in a:
              mode = 'GC'
              iconImg = iconImg.strip("'")
              name = h.unescape(name.decode(UTF8))
              plot = name
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '',iconImg, None)
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
              xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
           


def getCats(gsurl,catname):
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
        ilist = []
        url   = uqp(gsurl)
        url   = url.split('genre=')[1]
        url   = 'http://www.sonyliv.com/show/categoryShows?max=100&offset=0&genre=%s' % url
        html  = getRequest(url)            
        c     = re.compile('<li class=.+?id="show_(.+?)".+?title="(.+?)".+?src=(.+?) .+?</li',re.DOTALL).findall(html)
        for url, name, img in c:
              name = h.unescape(name.decode(UTF8))
              plot = catname
              img  = img.strip("'")
              mode = 'GE'
              url   = 'http://www.sonyliv.com/show/allEpisodeList?&showId=%s&offset=0&galleryId=&max=%s' % (url, str(pageSize))
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        if len(ilist) != 0:
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
          if addon.getSetting('enable_views') == 'true':
              xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('shows_view'))
          xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getEpis(geurl, catname):
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        geurl   = uqp(geurl)
        html  = getRequest(geurl)            
        c     = re.compile("<div title='(.+?)'.+?href='(.+?)'.+?src='(.+?)'.+?<span class=.+?>(.+?)<.+?</div",re.DOTALL).findall(html)
        for name, murl, img, dur in c:
              murl = 'http://www.sonyliv.com%s' % murl
              html = getRequest(murl)
              m =  re.compile('<div class="notification">.+?">(.+?)<',re.DOTALL).search(html)
              try:    aired   = m.group(1).strip()
              except: aired =''
              duration = 0
              try:
                   dur = dur.strip()
                   for d in dur.split(':'): duration = duration*60+int(d)
              except: pass
              title, plot,playerKey,url = re.compile('"og:title" content="(.+?)".+?"og:description" content="(.+?)".+?playerKey=(.+?)&amp;videoID=(.+?)&',re.DOTALL).search(html).groups()
              playerKey = playerKey.split(' ',1)[0]
              playerKey = playerKey.split('=',1)[0]
              infoList ={}
              infoList['Title'] = h.unescape(title)
              infoList['TVShowTitle'] = catname
              infoList['Plot']  = h.unescape(plot)
              infoList['duration'] = duration
              infoList['season'] = 0
              infoList['episode'] = 0
              months = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
              try:
                  dstr = (aired).split(' ')
                  dt   = '%s-%s-%s' % (dstr[2],months[dstr[1]],dstr[0])
                  infoList['Date']  = dt
                  infoList['Aired'] = infoList['Date']
                  infoList['Year']  = int(dstr[2])
              except: pass
              u = '%s?url=%s&playerkey=%s&mode=GV' % (sys.argv[0],qp(url), playerKey)
              liz=xbmcgui.ListItem(name, '',None, img)
              liz.setInfo( 'Video', infoList)
              liz.setProperty('fanart_image', addonfanart)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
        if len(ilist) == pageSize:
              x = re.compile('offset=([0-9]*)&').search(geurl).group(1)
              y = str(int(x)+pageSize)
              url = geurl.replace('offset='+x, 'offset='+y)
              mode = 'GE'
              name = '[COLOR blue]%s[/COLOR]' % __language__(30012)
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(catname), mode)
              liz=xbmcgui.ListItem(name, '',nextIcon, None)
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
              
        if len(ilist) != 0:
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
          if addon.getSetting('enable_views') == 'true':
             xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
          xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getMovies(gmurl):
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        catname = 'Movies'
        ilist = []
        geurl   = uqp(gmurl)
        html  = getRequest(gmurl)            
        c     = re.compile("<a title='(.+?)'.+?href="+'"(.+?)"'+".+?src='(.+?)'.+?<span class=.+?</small>(.+?)<.+?</div",re.DOTALL).findall(html)
        for name, murl, img, year in c:
              html = getRequest(murl)
              title, plot,playerKey,url = re.compile('"og:title" content="(.+?)".+?"og:description" content="(.+?)".+?playerKey=(.+?)&amp;videoID=(.+?)&',re.DOTALL).search(html).groups()
              playerKey = playerKey.split(' ',1)[0]
              playerKey = playerKey.split('=',1)[0]
              infoList ={}
              infoList['Title'] = h.unescape(title)
              infoList['Plot']  = h.unescape(plot)
              infoList['Year']  = int(year.strip())

              u = '%s?url=%s&playerkey=%s&mode=GV' % (sys.argv[0],qp(url), playerKey)
              liz=xbmcgui.ListItem(name, '',None, img)
              liz.setInfo( 'Video', infoList)
              liz.setProperty('fanart_image', addonfanart)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
        if len(ilist) == pageSize:
              x = re.compile('offset=([0-9]*)&').search(gmurl).group(1)
              y = str(int(x)+pageSize)
              url = geurl.replace('offset='+x, 'offset='+y)
              mode = 'GM'
              name = '[COLOR blue]%s[/COLOR]' % __language__(30012)
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(catname), mode)
              liz=xbmcgui.ListItem(name, '',nextIcon, None)
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
              
        if len(ilist) != 0:
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
          xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url, playerKey):
              bcid = uqp(url)
              if (playerKey != 'AQ~~,AAABzYvvPDk~,iCNMB0hmLnxGz0SO_CwEK3e8q1VJusdj') and (playerKey != 'AQ~~,AAAB051hNik~,6rCKhN0TFnnNKf3MD5ILa725PmUN9D_9') :
                 url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=3780015692001&playerKey=AQ~~,AAAApSSxphE~,wbrmvPDFim0fWkqLtb6niKsPCskpElR9&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+bcid+'&secureConnections=true&secureHTMLConnections=true'
              else:
                url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=3780015692001&playerKey='+playerKey+'&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+bcid+'&secureConnections=true&secureHTMLConnections=true'        
              html = getRequest(url)
              m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
              a = json.loads(html[m.start(1):m.end(1)+1])
              b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['IOSRenditions']
              u =''
              rate = 0
              for c in b:
                    if c['encodingRate'] > rate:
                       rate = c['encodingRate']
                       u = c['defaultURL']
              b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['renditions']
              for c in b:
                    if c['encodingRate'] > rate:
                       rate = c['encodingRate']
                       u = c['defaultURL']
              if rate == 0:
                     try:
                        u = a['data']['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']
                     except:
                        u = ''

              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=u))


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
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GE':  getEpis(p('url'),p('name'))
elif mode=='GM':  getMovies(p('url'))
elif mode=='GV':  getVideo(p('url'),p('playerkey'))
