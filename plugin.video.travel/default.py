# -*- coding: utf-8 -*-
# Travel Channel Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.travel')
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

              retries = 2
              while ( retries > 0):
                try:
                   response = urllib2.urlopen(req, timeout=30)
                   retries = 0
                except urllib2.URLError, e:
                   retries -= 1
                except socket.timeout:
                   retries -= 1
           

              try:
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()

              except:
                 if alert:
                     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 5000) )
                 link1 = ""

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
        ilist = []
        html = getRequest('http://www.travelchannel.com/shows/whats-new-on-travel-channel/articles/full-episodes')
        blob = re.compile('<article(.+?)</article').search(html).group(1)
        a = re.compile('<section class="topn-wrapper">.+?<a href="(.+?)".+?blank">(.+?)<.+?src="(.+?)".+?<p>(.+?)<.+?</section>').findall(blob)
        a[(len(a)-1)] = ('/video/p/1?wcmmode=disabled',__language__(30021),icon,__language__(30021))
        for url,name,img,plot in a:
              mode = 'GS'
              name = cleanname(name.decode(UTF8))
              plot = cleanname(plot.decode(UTF8))
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
           

def getQuery(cat_url):
        keyb = xbmc.Keyboard('', __addonname__)
        keyb.doModal()
        if (keyb.isConfirmed()):
              qurl = qp('/search/?q=%s' % (keyb.getText()))
              getCats(qurl, '')


def getShows(gsurl,catname):
        ilist = []
        html  = getRequest('http://www.travelchannel.com%s' % gsurl)
        c     = re.compile("data\-videoplaylist\-data='(.+?)'>").findall(html)
        for a in c:
              b = json.loads(a)
              name = cleanname(b["title"].decode(UTF8))
              url  = b["releaseUrl"]
              plot = cleanname(b["description"].decode(UTF8))
              img  = 'http://www.travelchannel.com%s' % b["thumbnailUrl"]
              dur  = b["length"]
              mode = 'GL'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
        if len(ilist) != 0:
          if 'wcmmode=disabled' in gsurl:
              name = '[COLOR red]%s[/COLOR]' % __language__(30012)
              mode = 'GS'
              url = '/video/p/%s?wcmmode=disabled' % str(int(gsurl[9])+1)
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": name })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
                
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getLink(url,vidname):
            html = getRequest(url)
            u = re.compile('<video src="(.+?)"').search(html).group(1)
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
elif mode=='GQ':  getQuery(p('url'))
elif mode=='GS':  getShows(p('url'),p('name'))
elif mode=='GL':  getLink(p('url'),p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

