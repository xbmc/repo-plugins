# -*- coding: utf-8 -*-
# HGTV XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25
HGTVBASE = 'http://www.hgtv.com%s'
XMLBASE  = 'http://www.hgtv.com/hgtv/channel/xml/0,,%s,00.xml'

addon         = xbmcaddon.Addon('plugin.video.hgtv')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def cleanfilename(name):    
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in name if c in valid_chars)

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
              urlbase   = HGTVBASE % ('/hgtv-full-episodes/videos/index.html')
              pg = getRequest(urlbase)
              caturl = re.compile("SNI\.HGTV\.Player.+?,'(.+?)'").findall(pg)[0]
              catname = __language__(30000)
              caturl  = XMLBASE % (caturl)
              addDir(catname,caturl,'GC',icon,addonfanart,catname,GENRE_TV,'',False)
              cats = re.compile('<li class="switch.+?</em>(.+?)<.+?<a href="(.+?)".+?</li>').findall(pg)
              for catname, caturl in cats:
                  caturl = re.compile('_.+?_.+?_(.+?)-').findall(caturl)[0]
                  caturl = XMLBASE % (caturl)
                  catname = catname.strip()
                  addDir(catname,caturl,'GC',icon,addonfanart,catname,GENRE_TV,'',False)

def getCats(cat_url):
              pg = getRequest(cat_url)
              shows = re.compile('<video>.+?<clipName>.+?CDATA\[(.+?)\].+?<videoUrl>.+?CDATA\[(.+?)\].+?<thumbnailUrl>.+?CDATA\[(.+?)\].+?<abstract>.+?CDATA\[(.+?)\].+?</video>').findall(pg)
              for showname, showurl, showimg, showdesc in shows:
                 showurl = showurl.replace('http://wms.scrippsnetworks.com','').replace('.wmv','')
                 showurl = 'rtmp://flash.scrippsnetworks.com:1935/ondemand?ovpfv=1.1 swfUrl=http://common.scrippsnetworks.com/common/snap/snap-3.0.3.swf playpath=%s' % (showurl)
                 addLink(showurl.encode(UTF8),showname,showimg,addonfanart,showdesc,GENRE_TV,'')



def play_playlist(name, list):
        playlist = xbmc.PlayList(1)
        playlist.clear()
        item = 0
        for i in list:
            item += 1
            info = xbmcgui.ListItem('%s) %s' %(str(item),name))
            playlist.add(i, info)
        xbmc.executebuiltin('playlist.playoffset(video,0)')


def addDir(name,url,mode,iconimage,fanart,description,genre,date,showcontext=True,playlist=None,autoplay=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+mode
        dir_playable = False
        cm = []

        if mode != 'SR':
            u += "&name="+urllib.quote_plus(name)
            if (fanart is None) or fanart == '': fanart = addonfanart
            u += "&fanart="+urllib.quote_plus(fanart)
            dir_image = "DefaultFolder.png"
            dir_folder = True
        else:
            dir_image = "DefaultVideo.png"
            dir_folder = False
            dir_playable = True

        ok=True
        liz=xbmcgui.ListItem(name, iconImage=dir_image, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Year": date } )
        liz.setProperty( "Fanart_Image", fanart )

        if dir_playable == True:
         liz.setProperty('IsPlayable', 'true')
        if not playlist is None:
            playlist_name = name.split(') ')[1]
            cm.append(('Play '+playlist_name+' PlayList','XBMC.RunPlugin(%s?mode=PP&name=%s&playlist=%s)' %(sys.argv[0], playlist_name, urllib.quote_plus(str(playlist).replace(',','|')))))
        liz.addContextMenuItems(cm)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=dir_folder)

def addLink(url,name,iconimage,fanart,description,genre,date,showcontext=True,playlist=None, autoplay=False):
        return addDir(name,url,'SR',iconimage,fanart,description,genre,date,showcontext,playlist,autoplay)



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
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='PP':  play_playlist(p('name'), p('playlist'))
elif mode=='GC':  getCats(p('url'))
#elif mode=='GS':  getShow(p('url'), p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

