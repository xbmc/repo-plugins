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
from operator import itemgetter


USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25

addon         = xbmcaddon.Addon('plugin.video.mediacorp')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode('utf-8')
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

def getRequest(url, user_data=None, headers = {'User-Agent':USER_AGENT}):
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
              except:
                 link1 = ""

              link1 = str(link1).replace('\n','')
              return(link1)


def getSources():

              addDir(__language__(30002),"http://video.xin.msn.com/browse/tv/network?tag=channel+5&currentpage=",'GC',"http://img.video.msn.com/video/i/network/ensg_channel-5_nl.png",addonfanart,__language__(30002),"TV",False)
              addDir(__language__(30003),"http://video.xin.msn.com/browse/tv/network?tag=channel+8&currentpage=",'GC',"http://img.video.msn.com/video/i/network/ensg_channel-8_nl.png",addonfanart,__language__(30003),"TV",False)
              addDir(__language__(30004),"http://video.xin.msn.com/browse/tv/network?tag=channel+u&currentpage=",'GC',"http://img.video.msn.com/video/i/network/ensg_channel-u_nl.png",addonfanart,__language__(30004),"TV",False)
              addDir(__language__(30005),"http://video.xin.msn.com/browse/news/channel-newsasia?currentpage=",'GS',"http://img.video.msn.com/video/i/src/ensgcna~ensgcna_ppl.png",addonfanart,__language__(30005),"TV",False)

def getnextPage(html, url, mode):
  try:
    (currentpage, totalpages) = re.compile('class="vxp_currentPage">(.+?)<.+?vxp_totalPages">(.+?)<').findall(html)[0]
    if (currentpage!=totalpages):
       currentpage = str(int(currentpage)+1)
       cattitle = "[COLOR blue]>>> %s[/COLOR]" % (__language__(30006))
       url = re.compile('(.+?)&currentpage=').findall(url)[0]
       caturl = url+'&currentpage=%s' % (currentpage)
       addDir(cattitle, caturl, mode, icon, addonfanart, "", "TV", "", False)
  except:
    return

def getChannel(url):
     html     = getRequest(url)
     blobs = re.compile('<ul class="vxp_tagList_column"(.+?)</ul>').findall(html)
     for catblock in blobs:
       match=re.compile('href="(.+?)".+?title="(.+?)"').findall(catblock)
       for caturl, cattext in match:
         caturl = caturl+'&currentpage='
         cattext = cattext.strip()
         cattext = cattext.replace('&quot;','"').replace("&#39;","'").replace("&amp;","&")
         addDir(cattext,caturl.encode('utf-8'),'GS',icon,addonfanart,cattext,"TV","",False)
     getnextPage(html,url, 'GC')


def getShows(url):
  html = getRequest(url)
  html = html.replace("&amp;","&").replace("&#39;","'").replace('&quot;','"')
  match = re.compile('vxp_gallery_thumb">.+?title="(.+?)".+?src="(.+?)".+?vxp_thumbClickTarget" href="(.+?)".+?vxp_gallery_date vxp_tb1">(.+?)<.+?vxp_videoType vxp_tb1">(.+?)<.+?data-title="(.+?)".+?vxp_rating">').findall(html)
  match = sorted(match, key=itemgetter(5))
  for catdesc, caticon, caturl, cattime, cattype, cattitle in match:
     cattype = cattype.strip()
     cattime = cattime.strip()
     cattitle= cattitle.strip()
     catdesc = catdesc.strip()
     caturl = "plugin://plugin.video.mediacorp/?url="+urllib.quote_plus(caturl)+"&name="+urllib.quote_plus(cattitle)+"&iconimage="+urllib.quote_plus(caticon)+"&mode=GV"
     addLink(caturl, cattitle, caticon, addonfanart, cattype+" "+cattime+"\n"+catdesc, "TV", "")

  getnextPage(html, url, 'GS')


def getVideo(url):
    html = getRequest(url)  
    html=html.replace('\r','').replace("&#39;","'")
    try:
        if "{formatCode: 103, url:" in html:
            vidurl = re.compile("{formatCode: 103, url:.+?'(.+?)'").findall(html)[0]
        else:
            vidurl = re.compile("{formatCode: 101, url:.+?'(.+?)'").findall(html)[0]
    except:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30000), '',__language__(30001))

    vidurl = vidurl.replace("\\x3a",":").replace("\\x2f","/")
    vidurl = vidurl.encode(UTF8)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=vidurl))


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

mode = p('mode', None)

if mode==  None:  getSources()
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='PP':  play_playlist(p('name'), p('playlist'))
elif mode=='GV':  getVideo(p('url'))
elif mode=='GS':  getShows(p('url'))
elif mode=='GC':  getChannel(p('url'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

