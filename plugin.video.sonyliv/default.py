# -*- coding: utf-8 -*-
# SONY LIV Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.sonyliv')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


qp  = urllib.quote_plus
uqp = urllib.unquote_plus

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def cleanname(name):
    return name.replace('&apos;',"'").replace('&#8217;',"'").replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"').replace('&#039;',"'")

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge


USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, user_data=None, headers = defaultHeaders , alert=True):

              log("getRequest URL:"+str(url))
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

                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()

              except urllib2.URLError, e:
                 if alert:
                     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 5000) )
                 link1 = ""

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
        ilist = []
        html = getRequest('http://www.sonyliv.com/show/list')
        a = re.compile('<div class="item genre.+?src=(.+?) .+?href="(.+?)">(.+?)<').findall(html)
        for img,url,name in a:
              mode = 'GC'
              img = img.strip("'")
              name = cleanname(name.decode(UTF8))
              plot = name
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
           


def getCats(gsurl,catname):
        ilist = []
        
        url   = uqp(gsurl)
        url   = url.split('genre-')[1]
        url   = 'http://www.sonyliv.com/show/categoryShows?max=100&offset=0&genre=%s' % url
        html  = getRequest(url)            
        c     = re.compile('<li class=.+?id="show_(.+?)".+?title="(.+?)".+?src=(.+?) .+?</li').findall(html)
        for url, name, img in c:
              name = cleanname(name.decode(UTF8))
              plot = catname
              img  = img.strip("'")
              mode = 'GE'
              url   = 'http://www.sonyliv.com/show/allEpisodeList?&showId=%s&offset=0&galleryId=&max=16' % url
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        if len(ilist) != 0:
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))



def getEpis(geurl, catname):
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        geurl   = uqp(geurl)
        html  = getRequest(geurl)            
        c     = re.compile("<div title='(.+?)'.+?src='(.+?)'.+?</div").findall(html)
        for name, img in c:
              url = img.rsplit('-',1)[1]
              url = url.split('.',1)[0]
              mode = 'GL'
              plot = ''
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
        if len(ilist) == 16:
              x = re.compile('offset=([0-9]*)&').search(geurl).group(1)
              y = str(int(x)+16)
              url = geurl.replace('offset='+x, 'offset='+y)
              mode = 'GE'
              name = '[COLOR blue]%s[/COLOR]' % __language__(30012)
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
              
        if len(ilist) != 0:
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getLink(url,vidname):
              bcid = uqp(url)
              url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=3780015692001&playerKey=AQ~~,AAAApSSxphE~,wbrmvPDFim0fWkqLtb6niKsPCskpElR9&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+bcid+'&secureConnections=true&secureHTMLConnections=true'
              html = getRequest(url)
              html = re.compile('experienceJSON = (.+?)\};').search(html).group(1)
              html = html+'}'
              a = json.loads(html)
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

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
       parms[key] = demunge(parms[key])
except:
    parms = {}

p = parms.get

mode = p('mode',None)

if mode==  None:  getSources(p('fanart'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GE':  getEpis(p('url'),p('name'))
elif mode=='GL':  getLink(p('url'),p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

