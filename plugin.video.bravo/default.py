# -*- coding: utf-8 -*-
# Kodi Bravo Video Addon !!!!!!!!!!!!!!!!!! still need to add subtitles !!!!!

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25
BRAVOBASE = 'http://www.bravotv.com%s'

addon         = xbmcaddon.Addon('plugin.video.bravo')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

qp  = urllib.quote_plus
uqp = urllib.unquote_plus

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge

def deuni(a):
    a = a.replace('&amp;#039;',"'")
    a = a.replace('&amp','&')
    a = a.replace('&#039;',"'")
    return a

def getRequest(url):
              log("getRequest URL:"+str(url))
              headers = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'} 
              req = urllib2.Request(url.encode(UTF8), None, headers)

              try:
                 response = urllib2.urlopen(req)
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()
              except:
                 link1 = ""

              link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
              ilist=[]
              urlbase   = 'http://www.bravotv.com/now/'
              html = getRequest(urlbase)
              blob = re.compile('<div id="tve-widget-show-list"(.+?)<div class="ws">').search(html).group(1)
              cats = re.compile('<div.+?href="(.+?)".+?title="(.+?)".+?src="(.+?)".+?</div').findall(blob)
              for url, name, img in cats:
                  name = name.strip()
                  plot = name
                  url = BRAVOBASE % (url)
                  mode = 'GC'
                  u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                  liz=xbmcgui.ListItem(name, '',img, img)
                  liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                  liz.setProperty('fanart_image', addonfanart)
                  ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getCats(cat_url):
              ilist=[]        
              html = getRequest(cat_url)
              try:    fanart = re.compile('<img class="showBaner" src="(.+?)"').search(html).group(1)
              except: fanart = addonfanart
              html = re.compile("Drupal\.settings, (.+?)\);<").search(html).group(1)
              a = json.loads(html)
              a = a["tve_widgets"]["more_episodes"]["assets1"]
              for b in a:
                 name = b["episode_title"]
                 img  = b["episode_thumbnail"]["url"]
                 plot = b["synopsis"]
                 studio = b["show_title"]
                 url = b["link"]
                 mode = 'GS'
                 u = '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), mode)
                 liz=xbmcgui.ListItem(name, '',img, img)
                 liz.setInfo( 'Video', { "Studio": studio, "Title": name, "Plot": plot })
                 liz.setProperty('fanart_image', fanart)
                 liz.setProperty('IsPlayable', 'true')
                 ilist.append((u, liz, False))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
                 

def getShow(url):
            url = BRAVOBASE % uqp(url)
            html = getRequest(url)
            purl = re.compile('data-release-url="(.+?)"').search(html).group(1)
            purl = 'http:'+purl+'&player=Bravo%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
       
            html = getRequest(purl)
            a = json.loads(html)
            url = a["captions"][0]["src"]
            url = url.split('/caption/',1)[1]
            url = url.split('.',1)[0]

            td = (datetime.datetime.utcnow()- datetime.datetime(1970,1,1))
            unow = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)

            u   = 'https://tvebravo-vh.akamaihd.net/i/prod/video/%s_,40,25,18,12,7,4,2,00.mp4.csmil/master.m3u8?b=&__b__=1000&hdnea=st=%s~exp=%s' % (url, str(unow), str(unow+60))
            html = getRequest(u)
            if html == '':
               u   = 'https://tvebravo-vh.akamaihd.net/i/prod/video/%s_,1696,1296,896,696,496,240,306,.mp4.csmil/master.m3u8?b=&__b__=1000&hdnea=st=%s~exp=%s' % (url, str(unow), str(unow+60))

            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = u))


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
elif mode=='GC':  getCats(p('url'))
elif mode=='GS':  getShow(p('url'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

