# -*- coding: utf-8 -*-
# HGTV XBMC Addon

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
HGTVBASE = 'http://www.hgtv.com%s'

addon         = xbmcaddon.Addon('plugin.video.hgtv')
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

def cleanname(name):    
    return name.replace('<p>','').replace('<strong>','').replace('&apos;',"'").replace('&#8217;',"'")

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge

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
              ilist = []
              urlbase   = HGTVBASE % ('/shows/full-episodes')
              pg = getRequest(urlbase)
              blob = re.compile('<div class="video-player-embedded">(.+?)<section class="text-promo module">').search(pg).group(1)
              cats = re.compile('<li class="block">.+?src="(.+?)".+?href="(.+?)">(.+?)<.+?</li>').findall(blob)
              for img, url, name in cats:
                  name = cleanname(name).strip()
                  plot = name
                  u = '%s?mode=GC&name=%s&url=%s' %(sys.argv[0], qp(name), qp(url))
                  liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
                  liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                  liz.setProperty('fanart_image', addonfanart)
                  ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

def getCats(caturl, catname):
              pg = getRequest(uqp(caturl))
              try:
                ilist = []
                shows = re.compile("data-video-prop='(.+?)'").search(pg).group(1)
                s = json.loads(shows)
                s = s["channels"][0]["videos"]
                for v in s:
                   name = cleanname(v["title"]).strip()
                   plot = cleanname(v["description"]).strip()
                   img  = HGTVBASE % (v["thumbnailUrl"])
                   u = '%s?mode=GS&url=%s' %(sys.argv[0], qp(v["releaseUrl"]))
                   liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
                   liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": plot })
                   liz.setProperty('fanart_image', addonfanart)
                   liz.setProperty('IsPlayable', 'true')
                   ilist.append((u, liz, False))
                xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

              except:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30010), '',__language__(30011))


def getShow(showurl):
            showurl = uqp(showurl)
            pg = getRequest(showurl)
            i = int(addon.getSetting('vid_res'))
            i = i+1
            try:
              url = re.compile('<video src="(.+?)_6.mp4"').search(pg).group(1)
              url = url+'_%s.mp4' % str(i)
            except:
              url = 'http://link.theplatform.com/s/errorFiles/Unavailable.mp4'
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))



# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'movies')

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
       parms[key] = demunge(parms[key])
except:
    parms = {}

p = parms.get

try:
    mode = p('mode')
except:
    mode = None

if mode==  None:  getSources(p('fanart'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GS':  getShow(p('url'))


xbmcplugin.endOfDirectory(int(sys.argv[1]))

