# -*- coding: utf-8 -*-

import urllib
import urllib2
import cookielib
import datetime
import time
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import cgi
from StringIO import StringIO
import gzip


USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

addon         = xbmcaddon.Addon('plugin.video.wsj')
__addonname__ = addon.getAddonInfo('name')
home          = addon.getAddonInfo('path').decode('utf-8')
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
fanart        = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))



def log(txt):
   try:
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)
   except:
    pass

def _parse_argv():

        global url,name,iconimage, mode, playlist,fchan,fres,fhost,fname,fepg

        params = {}
        try:
            params = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
        except:
            params = {}

        url =       demunge(params.get("url",None))
        name =      demunge(params.get("name",""))
        iconimage = demunge(params.get("iconimage",""))
#        fanart =    demunge(params.get("fanart",""))
        playlist =  demunge(params.get("playlist",""))
        fchan =     demunge(params.get("fchan",""))
        fres =      demunge(params.get("fres",""))
        fhost =     demunge(params.get("fhost",""))
        fname =     demunge(params.get("fname",""))
        fepg =      demunge(params.get("fepg",None))

        try:
            playlist=eval(playlist.replace('|',','))
        except:
            pass

        try:
            mode = int(params.get( "mode", None ))
        except:
            mode = None


def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode('utf-8')
        except:
            pass
        return munge

def getRequest(url):
              log("WSJ - getRequest URL: "+str(url))
              req = urllib2.Request(url.encode('utf-8'))
              req.add_header('User-Agent', USER_AGENT)
              req.add_header('Accept',"text/html")
              req.add_header('Accept-Encoding', None )
              req.add_header('Accept-Encoding', 'gzip,deflate,sdch')
              req.add_header('Accept-Language', 'en-US,en;q=0.8')
              req.add_header('Cookie','hide_ce=true')
              log("RT -- request headers = "+str(req.header_items()))
              try:
                 response = urllib2.urlopen(req)
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("WSj -- Content Encoding == 'gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()
                 response.close()
              except:
                 link1 = ""
              return(link1)


def getSources():

              log("WSJ -- WSJ Live main page")
              link1 = getRequest("http://live.wsj.com")
              link=str(link1).replace('\n','')     
              match=re.compile('<li id="vcrTab_(.+?)".+?data-query="(.+?)".+?~(.+?)"').findall(str(link))
              for category, caturl, cattext in match:
                 caturl = "http://live.wsj.com/api-video/find_all_videos.asp?"+caturl
                 try:
                    if (category == "startup") or (category == "markets"):
                      addDir(cattext.encode('utf-8', 'ignore'),caturl.encode('utf-8'),18,icon,fanart,cattext,"News","",False)
                    else:
                      addDir(cattext.encode('utf-8', 'ignore'),category.encode('utf-8'),17,icon,fanart,cattext,"News","",False)
 
                 except:
                    log("WSJ -- Problem adding directory")



def play_playlist(name, list):
        playlist = xbmc.PlayList(1)
        playlist.clear()
        item = 0
        for i in list:
            item += 1
            info = xbmcgui.ListItem('%s) %s' %(str(item),name))
            playlist.add(i, info)
        xbmc.executebuiltin('playlist.playoffset(video,0)')


def addDir(name,url,mode,iconimage,fanart,description,genre,date,showcontext=True):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&fanart="+urllib.quote_plus(fanart)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Year": date } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok



def addLink(url,name,iconimage,fanart,description,genre,date,showcontext=True,playlist=None):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=12"
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Year": date } )
        liz.setProperty( "Fanart_Image", fanart )
        liz.setProperty('IsPlayable', 'true')
        if not playlist is None:
            playlist_name = name.split(') ')[1]
            contextMenu_ = [('Play '+playlist_name+' PlayList','XBMC.RunPlugin(%s?mode=13&name=%s&playlist=%s)' %(sys.argv[0], urllib.quote_plus(playlist_name), urllib.quote_plus(str(playlist).replace(',','|'))))]
            liz.addContextMenuItems(contextMenu_)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def strip_unicode(unistr):
    return(unistr.replace('\\u2018',"'").replace('\\u2019',"'").replace('\\u201C','"').replace('\\u201D','"').replace('\\u2013','-').replace('\\u2014','-').replace('\\u2005',' ').replace('\\u00E9','e'))


xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except:
    pass


url=None
name=None
iconimage=None
mode=None
playlist=None
fchan=None
fres=None
fhost=None
fname=None
fepg=None

_parse_argv()



log("WSJ -- Mode: "+str(mode))

if not url is None:
      log("WSJ -- URL: "+str(url.encode('utf-8')))

log("WSJ -- Name: "+str(name))

if mode==None:
    log("WSJ -- getSources")
    getSources()

elif mode==12:
    log("WSJ -- setResolvedUrl")
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

elif mode==13:
    log("WSJ -- play_playlist")
    play_playlist(name, playlist)

elif mode==17:
              log("WSJ -- Processing WSJ category item")
              link1 = getRequest("http://live.wsj.com")
              link=str(link1).replace('\n','')
              log("WSJ -- url = "+str(url))
              match=re.compile('vcrDataPanel_'+str(url)+'(.+?)</ul>').findall(str(link))
              for subcat in match:
                subcat = str(subcat).replace("&gt;",'>').replace("&lt;",'<')
                submatch = re.compile('<h5 id=".+?data-query="(.+?)".+?~(.+?)"').findall(str(subcat))
                for caturl, cattext in submatch:
                 caturl = "http://live.wsj.com/api-video/find_all_videos.asp?"+caturl
                 try:
                   addDir(str(cattext),caturl.encode('utf-8'),18,icon,fanart,str(cattext),"News","",False)
                 except:
                   log("WSJ -- problem adding Directory")

elif mode==18:
              log("WSJ -- Processing WSJ sub category item")

              res_thumbs = ["_640x360.jpg","_512x288.jpg","_167x94.jpg"]
              res_videos = ["2564k.mp4","1864k.mp4","1264k.mp4","464k.mp4"]
              i = int(addon.getSetting('vid_res'))
              res_video = res_videos[i]
              i = int(addon.getSetting('thumb_res'))
              res_thumb = res_thumbs[i]

              link1 = getRequest(url)
              link=str(link1).replace('\n','').replace('\\/','/').replace('\\"',"'")
              match = re.compile('"name": "(.+?)","description": "(.+?)".+?"thumbnailURL": "(.+?)_167x94.jpg.+?"videoURL": "http://hdsvod-f.akamaihd.net/z(.+?),.+?CreationDate": "(.+?)"').findall(link)
              for cattitle, catdesc, caticon, caturl, catdate in match:
                caturl = "http://m.wsj.net"+caturl+res_video
                caticon += res_thumb
                catdesc = strip_unicode(catdesc)
                cattitle = strip_unicode(cattitle)
                try:
                   addLink(caturl.encode('utf-8'),cattitle,caticon,fanart,catdate+'\n'+catdesc,"News","")
                except:
                   log("WSJ -- Problem adding directory")


xbmcplugin.endOfDirectory(int(sys.argv[1]))