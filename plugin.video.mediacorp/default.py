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

addon         = xbmcaddon.Addon('plugin.video.mediacorp')
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

              log("Mediacorp -- Mediacorp main page")
              addDir("Channel 5","http://video.xin.msn.com/browse/tv/network?tag=channel+5&currentpage=",17,"http://img.video.msn.com/video/i/network/ensg_channel-5_nl.png",fanart,"Channel 5","TV",False)
              addDir("Channel 8","http://video.xin.msn.com/browse/tv/network?tag=channel+8&currentpage=",17,"http://img.video.msn.com/video/i/network/ensg_channel-8_nl.png",fanart,"Channel 8","TV",False)
              addDir("Channel U","http://video.xin.msn.com/browse/tv/network?tag=channel+u&currentpage=",17,"http://img.video.msn.com/video/i/network/ensg_channel-u_nl.png",fanart,"Channel U","TV",False)
              addDir("Channel News Asia","http://video.xin.msn.com/browse/news/channel-newsasia?currentpage=",18,"http://img.video.msn.com/video/i/src/ensgcna~ensgcna_ppl.png",fanart,"Channel News Asia","TV",False)



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
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&fanart="+urllib.quote_plus(fanart)+"&iconimage="+urllib.quote_plus(iconimage)
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



log("Mediacorp -- Mode: "+str(mode))
if not url is None:
    print "Mediacorp -- URL: "+str(url.encode('utf-8'))
#log("Mediacorp -- Name: "+str(name))

if mode==None:
    log("Mediacorp -- getSources")
    getSources()

elif mode==12:
    log("Mediacorp -- setResolvedUrl")
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

elif mode==13:
    log("Mediacorp -- play_playlist")
    play_playlist(name, playlist)

elif mode==17:
              req = urllib2.Request(url.encode('utf-8'))
              req.add_header('User-Agent', USER_AGENT)
              try:
                 response = urllib2.urlopen(req)
                 link1=response.read()
                 response.close()
              except:
                 link1 = ""

              link=str(link1).replace('\n','')     
              match=re.compile('<ul class="vxp_tagList_column"(.+?)</ul>').findall(str(link))
              for catblock in match:
                match=re.compile('href="(.+?)".+?title="(.+?)"').findall(str(catblock))
                for caturl, cattext in match:
                 cattext = cattext.strip()
                 cattext = cattext.replace('&quot;','"').replace("&#39;","'").replace("&amp;","&")
                 try:
                    addDir(cattext,caturl.encode('utf-8'),18,iconimage,fanart,cattext,"TV","",False)
                 except:
                    log("Mediacorp -- Problem adding directory")

              match = re.compile('class="vxp_currentPage">(.+?)<.+?vxp_totalPages">(.+?)<').findall(str(link))
              catdone=False
              for currentpage, totalpages in match:
                if (currentpage!=totalpages) and catdone==False:
                  catdone = True
                  currentpage = str(int(currentpage)+1)
                  cattitle = ">>> Next Page"
                  catdesc = cattitle
                  caturl = url+currentpage
                  try:
                     addDir(cattitle,caturl,17,iconimage,fanart,catdesc,"TV","",False)
                  except:
                     log("Mediacorp -- Problem adding directory")




elif mode==18:
              log("Mediacorp -- Processing Mediacorp sub category item")
              req = urllib2.Request(url.encode('utf-8'))
              log("Mediacorp -- req === "+str(req))
              req.add_header('User-Agent', USER_AGENT)
              try:
                 response = urllib2.urlopen(req)
                 link1=response.read()
                 response.close()
              except:
                 link1 = ""
              link=str(link1).replace('\n','').replace('\r','')

              match = re.compile('<div class="vxp_gallery_thumb">(.+?)class="vxp_rating">').findall(str(link))
              for classdata in match:
                    classdata=classdata.replace("&amp;","&").replace("&#39;","'").replace('&quot;','"')
                    match = re.compile('title="(.+?)".+?src="(.+?)".+?vxp_thumbClickTarget" href="(.+?)".+?class="vxp_gallery_date vxp_tb1">(.+?)<.+?vxp_videoType vxp_tb1">(.+?)<.+?data-title="(.+?)"').findall(str(classdata))
                    cattype=""
                    for catdesc,caticon, caturl, cattime, cattype, cattitle in match:
                     cattype = cattype.strip()
                     cattime = cattime.strip()
                     cattitle= cattitle.strip()
                     catdesc = catdesc.strip()
                     caturl = "plugin://plugin.video.mediacorp/?url="+urllib.quote_plus(caturl)+"&name="+urllib.quote_plus(cattitle)+"&iconimage="+urllib.quote_plus(caticon)+"&mode=19"
                     try:
                      addLink(caturl,cattitle,caticon,fanart,cattype+" "+cattime+"\n"+catdesc,"TV","")
                     except:
                        log("Mediacorp -- Problem adding directory")



 
elif mode==19:
              log("Mediacorp -- Processing Mediacorp play category item")
              req = urllib2.Request(url.encode('utf-8'))
              log("Mediacorp -- req === "+str(req))
              req.add_header('User-Agent', USER_AGENT)
              try:
                 response = urllib2.urlopen(req)
                 link1=response.read()
                 response.close()
              except:
                 link1 = ""
              link=str(link1).replace('\n','').replace('\r','').replace("&#39;","'")

              if "{formatCode: 103, url:" in link:
                 match = re.compile("{formatCode: 103, url:.+?'(.+?)'").findall(str(link))
              else:
                 match = re.compile("{formatCode: 101, url:.+?'(.+?)'").findall(str(link))
              if not match:
                 dialog = xbmcgui.Dialog()
                 dialog.ok("Mediacorp TV Singapore", '', 'No Playable Video Found')
              else:
               for vidurl in match:
                vidurl = vidurl.replace("\\x3a",":").replace("\\x2f","/")
                vidurl = vidurl.encode('utf-8')
                item = xbmcgui.ListItem(path=vidurl, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
                item.setInfo( type="Video", infoLabels={ "Title": name} )
                item.setProperty("IsPlayable","true")
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
              

xbmcplugin.endOfDirectory(int(sys.argv[1]))