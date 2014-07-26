# -*- coding: utf-8 -*-
# NPR Music XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
GENRE      = "Music Video"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25
NPRBASE = 'http://www.npr.org%s'

addon         = xbmcaddon.Addon('plugin.video.npr')
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

def deuni(a):
    a = a.replace('&amp;#039;',"'")
    a = a.replace('&amp','&')
    a = a.replace('&;','&')
    a = a.replace('&quot;',"'")
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
              urlbase   = NPRBASE % ('/sections/music-videos/')
              pg = getRequest(urlbase)
              catname = __language__(30000)
              urlbase = NPRBASE % ('/series/15667984/favorite-sessions')
              addDir(catname,urlbase.encode(UTF8),'GC',icon,addonfanart,catname,GENRE,'',False)
              blob = re.compile('<div class="subtopics">(.+?)</ul>').findall(pg)[0]
              cats = re.compile('<a href="(.+?)">(.+?)<').findall(blob)
              for caturl, catname in cats:
                  caturl = NPRBASE % (caturl)
                  addDir(catname,caturl.encode(UTF8),'GC',icon,addonfanart,catname,GENRE,'',False)

def getCats(cat_url):
             pg = getRequest(cat_url)
             blobs = re.compile('<article class(.+?)</article>').findall(pg)
             curlink  = 0
             nextlink = 1
             for blob in blobs:
               nextlink = nextlink+1
               if ('article-video' in blob) or ('type-video' in blob):
                 (showurl, showimg, showname) = re.compile('<a href="(.+?)".+?src="(.+?)".+?title="(.+?)"').findall(blob)[0]
                 showurl = "%s?url=%s&name=%s&mode=GS" %(sys.argv[0], urllib.quote_plus(showurl), urllib.quote_plus(showname))
                 addLink(showurl.encode(UTF8),deuni(showname),showimg,addonfanart,deuni(showname),GENRE,'')

             nextstr = '/archive?start='
             nexturl = cat_url
             if (nextstr in cat_url):
                (nexturl,curlink) = nexturl.split(nextstr,1)
                curlink = int(curlink)
             nextlink = str(nextlink+curlink+1)
             nexturl = nexturl+nextstr+nextlink
             catname = '[COLOR red]%s[/COLOR]' % (__language__(30001))
             addDir(catname,nexturl.encode(UTF8),'GC','',addonfanart,catname,GENRE,'',False)


def getShow(show_url, show_name):
            pg = getRequest(show_url)
            try:
                finalurl = re.compile("'SD'.+?file:'(.+?)'").findall(pg)[0]
            except:
                try:
                    videoid = re.compile('<div class="video-wrap">.+?src="http://www\.youtube\.com/embed/(.+?)\?').findall(pg)[0]
                    finalurl = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (videoid)
                except:
                    dialog = xbmcgui.Dialog()
                    dialog.ok(__language__(30002), '',__language__(30003)) #tell them no video found
                    return
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))


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

mode = p('mode',None)

if mode==  None:  getSources(p('fanart'))
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='PP':  play_playlist(p('name'), p('playlist'))
elif mode=='GC':  getCats(p('url'))
elif mode=='GS':  getShow(p('url'), p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

