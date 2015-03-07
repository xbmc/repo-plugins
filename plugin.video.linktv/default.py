# -*- coding: utf-8 -*-
# LinkTV Kodi Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.linktv')
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
    return name.replace('&apos;',"'").replace('&#8217;',"'").replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"')

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
                 response = urllib2.urlopen(req)
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()

              except urllib2.URLError, e:
                 if alert:
                     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 10000) )
                 link1 = ""

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
        ilist = []
        html  = getRequest('http://www.linktv.org')
        cats  = re.compile('<a href="#">(.+?)<').findall(html)
        for a in cats:
          if not a.startswith('<'):
              name = a
              plot = ''
              if name == 'Browse':
                 name = 'Documentaries'
                 url  = '/documentaries'
                 mode = 'GS'
              else:
                 url  = a
                 mode = 'GC'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
           


def getQuery(cat_url):
        keyb = xbmc.Keyboard('', __addonname__)
        keyb.doModal()
        if (keyb.isConfirmed()):
              qurl = qp('/search/?q=%s' % (keyb.getText()))
              getCats(qurl, '')



def getCats(gcurl, catname):
              ilist = []
              gcurl = uqp(gcurl)
              html = getRequest('http://www.linktv.org')
              blob = re.compile('<a href="#">'+gcurl+'.+?class="dropdown">(.+?)<li class="').search(html).group(1)
              cats = re.compile('<a href="(.+?)">(.+?)<').findall(blob)
              if len(cats) == 0:
                blob = re.compile('<a href="#">'+gcurl+'.+?class="dropdown">(.+?)<a href="#"').search(html).group(1)
                cats = re.compile('<a href="(.+?)">(.+?)<').findall(blob)
              for url,name in cats:
                     name = cleanname(name)
                     plot = ''

                     if '/videos/' in url:
                        mode = 'GL'
                        vid = re.compile('/videos/([0-9]*)').search(url).group(1)
                        u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],vid , qp(catname), mode)
                        liz = xbmcgui.ListItem(name, plot,'DefaultFolder.png', icon)
                        liz.setInfo( 'Video', { "Title": name, "Studio" : catname, "Plot": plot})
                        liz.setProperty('IsPlayable', 'true')
                        ilist.append((u, liz, False))
                     else:
                        mode = 'GS'
                        u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                        liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', icon)
                        liz.setInfo( 'Video', { "Title": name, "Studio" : catname, "Plot": plot})
                        ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

def getShows(gsurl,catname):
              ilist = []
              if not gsurl.startswith('http'):
                 gsurl = 'http://www.linktv.org%s' % (gsurl)
              gsurl   = uqp(gsurl)
              catname = uqp(catname)
              url     = gsurl
              html  = getRequest(gsurl)


              if '/take-action/' in gsurl:
                 shows = re.compile('<div class="col span_half">.+?href=".+?/video/([0-9]*).+?src="(.+?)".+?title="(.+?)"').findall(html)
                 for vid,img,name in shows:
                        mode = 'GL'
                        plot = ''
                        u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],vid , qp(catname), mode)
                        liz = xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                        liz.setInfo( 'Video', { "Title": name, "Studio" : catname, "Plot": plot})
                        liz.setProperty('IsPlayable', 'true')
                        ilist.append((u, liz, False))
                     
              else:
                 shows = re.compile('class="playlist-carousel">.+?<h2>(.+?)</h2>').findall(html)
                 try:
                      plot = re.compile('<div class="video-details-description".+?<p>(.+?)</p>').search(html).group(1)
                 except:
                      plot = ''
                 for name in shows:

                     dispname = cleanname(name)
                     try:
                       dispname = dispname.split('>',1)[1]
                       dispname = dispname.split('<',1)[0]
                     except:
                       pass    

                     mode = 'GV'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                     liz=xbmcgui.ListItem(dispname, plot,'DefaultFolder.png', icon)
                     liz.setInfo( 'Video', { "Title": dispname, "Studio" : catname, "Plot": plot})
                     ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getVids(gvurl,vidname):
              ilist=[]
              if not gvurl.startswith('http'):
                 gvurl = 'http://www.linktv.org%s' % (gvurl)

              gvurl   = uqp(gvurl)
              vidname = uqp(vidname)
              url     = gvurl
              html  = getRequest(gvurl)
              blob  = re.compile('class="playlist\-carousel">.+?<h2>%s</h2>(.+?)</ul>' % vidname).findall(html)
              shows = re.compile('<a href="/videos/(.+?)".+?src="(.+?)".+?<div class="(.+?)"(.+?)</a>').findall(str(blob))
              for (vid,img,ctype,stuff) in shows:
                 if ctype == 'vp-featured-caption':
                    name, plot = re.compile('<h2>(.+?)<.+?<p.+?>(.+?)</p>').search(stuff).groups(1)
                 else:
                    name = re.compile('<p.+?>(.+?)</p>').search(stuff).group(1)
                    plot = ''
                 name = cleanname(name.replace('\\t',''))
                 mode = 'GL'
                 u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],vid , qp(vidname), mode)
             
                 liz = xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                 liz.setInfo( 'Video', { "Title": name, "Studio" : vidname, "Plot": plot})
                 liz.setProperty('IsPlayable', 'true')
                 ilist.append((u, liz, False))

              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getLink(vid,vidname):
                 url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=myExperience'+vid+'&bgcolor=%23FFFFFF&playerID=2900605856001&playerKey=AQ~~%2CAAAAAAgg0EI~%2COBaMgax57U8d3-y-O4a_HqpOdJPQqbIp&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+vid+'&secureConnections=true&secureHTMLConnections=true'
                 html = getRequest(url)
                 a = re.compile('experienceJSON = (.+?)\};').search(html).group(1)
                 a = a+'}'
                 a = json.loads(a)
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
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='GQ':  getQuery(p('url'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GS':  getShows(p('url'),p('name'))
elif mode=='GV':  getVids(p('url'),p('name'))
elif mode=='GL':  getLink(p('url'),p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

