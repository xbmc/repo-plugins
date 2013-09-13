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

USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

addon         = xbmcaddon.Addon('plugin.video.rt')
__addonname__ = addon.getAddonInfo('name')
home          = addon.getAddonInfo('path').decode('utf-8')
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
fanart        = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))




def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


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







def getSources():

              log("RT -- RT Live main page")
              req = urllib2.Request("http://www.rt.com/shows")
              req.add_header('User-Agent', USER_AGENT)
              try:
                 response = urllib2.urlopen(req)
                 link1=response.read()
                 response.close()
              except:
                 link1 = ""

              addLink("rtmp://rt.fms-04.visionip.tv/live/rt-global-live-HD","Live",icon,fanart,"Live HD Stream","News","",False)
              link=str(link1).replace('\n','')     
              match=re.compile('<ul class="nav-extra">(.+?)</ul>').findall(str(link))
              for catblock in match:
                match=re.compile('<li><a href="(.+?)">(.+?)</a></li>').findall(str(catblock))
                for caturl, cattext in match:
                 try:
                      addDir(cattext.encode('utf-8', 'ignore'),caturl.encode('utf-8'),18,icon,fanart,cattext,"News","",False)
                 except:
                    log("RT -- Problem adding directory")



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


xbmcplugin.setContent(int(sys.argv[1]), 'movies')
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_GENRE)
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



log("RT -- Mode: "+str(mode))
if not url is None:
    print "RT -- URL: "+str(url.encode('utf-8'))
log("RT -- Name: "+str(name))

if mode==None:
    log("RT -- getSources")
    getSources()

elif mode==12:
    log("RT -- setResolvedUrl")
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

elif mode==13:
    log("RT -- play_playlist")
    play_playlist(name, playlist)



elif mode==18:
              log("RT -- Processing RT sub category item")
              url = "http://rt.com"+url
              req = urllib2.Request(url.encode('utf-8'))
              log("RT -- req === "+str(req))
              req.add_header('User-Agent', USER_AGENT)
              try:
                 response = urllib2.urlopen(req)
                 link1=response.read()
                 response.close()
              except:
                 link1 = ""
              link=str(link1).replace('\n','')

              match = re.compile('<dt class="(.+?)"(.+?)</dl>').findall(str(link))
              for classtype, classdata in match:
                 if "programm" in classtype:
                    match = re.compile('<a href="(.+?)".+?class="header">(.+?)<.+?<img src="(.+?)".+?<dd>(.+?)<span class="time">(.+?)<').findall(str(classdata))
                    for pgurl,cattitle,imgurl,catdesc, cattime in match:
                     caturl = "plugin://plugin.video.rt/?url=http://rt.com"+pgurl+"&mode=19"
                     caticon = "http://rt.com"+imgurl
                     try:
                        addLink(caturl.encode('utf-8'),str(cattitle),caticon,fanart,cattime+"\n"+catdesc,"News","")
                     except:
                        log("RT -- Problem adding directory")
                 else:
                    match = re.compile('<a href="(.+?)".+?<img src="(.+?)".+class="header">(.+?)</a>.+?<p>(.+?)</p.+?class="time">(.+?)<').findall(str(classdata))
                    for pgurl,imgurl, cattitle,catdesc, cattime in match:
                     caturl = "plugin://plugin.video.rt/?url=http://rt.com"+pgurl+"&name="+str(cattitle)+"&mode=19"
                     caticon = "http://rt.com"+imgurl
                     try:
                        addLink(caturl.encode('utf-8'),str(cattitle),caticon,fanart,cattime+"\n"+catdesc,"News","")
                     except:
                        log("RT -- Problem adding directory")

 
elif mode==19:
              log("RT -- Processing RT play category item")
              req = urllib2.Request(url.encode('utf-8'))
              log("RT -- req === "+str(req))
              req.add_header('User-Agent', USER_AGENT)
              try:
                 response = urllib2.urlopen(req)
                 link1=response.read()
                 response.close()
              except:
                 link1 = ""
              link=str(link1).replace('\n','')

              match = re.compile('<span class="time">(.+?)<.+?<div class="video_block".+?"thumbnailUrl" content="(.+?)".+?"contentURL" content="(.+?)".+?<p>(.+?)</p>').findall(str(link))
              if not match:
                 dialog = xbmcgui.Dialog()
                 dialog.ok("Russia Today News", '', 'No Playable Video Found')
              else:
               for viddate,icon,vidurl,viddesc in match:
                if "comhttp:" in vidurl:
                  vidurl = vidurl.replace("http://rt.com","")
                item = xbmcgui.ListItem(path=vidurl.encode('utf-8'), iconImage="DefaultVideo.png", thumbnailImage=icon)
                item.setInfo( type="Video", infoLabels={ "Title": name, "Plot": viddate+"\n"+viddesc } )
                item.setProperty("IsPlayable","true")
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
              

xbmcplugin.endOfDirectory(int(sys.argv[1]))