# -*- coding: utf-8 -*-
# Wall Street Journal Live

import urllib, urllib2, cookielib, datetime, time, re, os
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs
import cgi, gzip
from StringIO import StringIO


USER_AGENT    = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
WSJ_URL       = "http://live.wsj.com"
WSJ_API_URL   = "/api-video/find_all_videos.asp?"
GENRE_NEWS      = "News"
MANIFEST      = '/manifest.f4m"'
VID_BASE      = "http://m.wsj.net"
UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.wsj')
__addonname__ = addon.getAddonInfo('name')
home          = addon.getAddonInfo('path').decode(UTF8)
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
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge

def getRequest(url):
              log("getRequest URL:"+str(url))
              headers = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8', 'Cookie':'hide_ce=true'} 
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


def getSources():

              match=re.compile('<li id="vcrTab_(.+?)".+?data-query="(.+?)".+?~(.+?)"').findall(getRequest(WSJ_URL))
              for category, caturl, cattext in match:
                 catdesc = cattext
                 caturl  = (WSJ_URL+WSJ_API_URL+caturl).encode(UTF8)
                 cattext = cattext.encode(UTF8, 'ignore')
                 try:
                    if (category == "startup") or (category == "markets"):
                      addDir(cattext,caturl,18,icon,fanart,catdesc,GENRE_NEWS,"",False)
                    else:
                      addDir(cattext,category.encode(UTF8),17,icon,fanart,catdesc,GENRE_NEWS,"",False)
 
                 except:
                    log("Problem adding directory")


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
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        dir_playable = False

        if mode != 12:
            u += "&name="+urllib.quote_plus(name)+"&fanart="+urllib.quote_plus(fanart)
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
            contextMenu_ = [('Play '+playlist_name+' PlayList','XBMC.RunPlugin(%s?mode=13&name=%s&playlist=%s)' %(sys.argv[0], urllib.quote_plus(playlist_name), urllib.quote_plus(str(playlist).replace(',','|'))))]
            liz.addContextMenuItems(contextMenu_)

        if autoplay == True:
            xbmc.PlayList(1).add(u, liz)
        else:    
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=dir_folder)
        return ok

def addLink(url,name,iconimage,fanart,description,genre,date,showcontext=True,playlist=None, autoplay=False):
        return addDir(name,url,12,iconimage,fanart,description,genre,date,showcontext,playlist,autoplay)


def strip_unicode(unistr):
    return(unistr.replace('\\u2018',"'").replace('\\u2019',"'").replace('\\u201C','"').replace('\\u201D','"').replace('\\u2013','-').replace('\\u2014','-').replace('\\u2005',' ').replace('\\u00E9','e'))


# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except:
    pass


url=name=iconimage=mode=playlist=fchan=fres=fhost=fname=fepg=None

_parse_argv()

auto_play = False


log("Mode: "+str(mode)+" Name: "+str(name))
if not url is None:
      log("URL: "+str(url.encode(UTF8)))

if mode==None:
    log("getSources")
    getSources()
    url = "topnews"
    if addon.getSetting('auto_play') == "true":
       auto_play = True
       xbmc.PlayList(1).clear()


if mode==12:
    log("setResolvedUrl")
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

if mode==13:
    log("play_playlist")
    play_playlist(name, playlist)

if (mode==17) or (auto_play == True):

              log("Processing category")

              if auto_play == True:
                subcatname = "News"
              else:
                subcatname = ".+?"
              match=re.compile('vcrDataPanel_'+str(url)+'(.+?)</ul>').findall(getRequest(WSJ_URL))
              for subcat in match:
                subcat = subcat.replace("&gt;",'>').replace("&lt;",'<')
                submatch = re.compile('<h5 id=".+?data-query="(.+?)".+?~('+subcatname+')"').findall(subcat)
                for caturl, cattext in submatch:
                 caturl = (WSJ_URL+WSJ_API_URL+caturl).encode(UTF8)
                 if auto_play != True:
                  try:
                    addDir(cattext,caturl,18,icon,fanart,cattext,GENRE_NEWS,"",False)
                  except:
                    log("problem adding Directory")
                 else:
                    url = caturl



if mode==18 or (auto_play == True):

              log("Processing subcategory")

              res_thumbs = ["_640x360.jpg","_512x288.jpg","_167x94.jpg"]
              res_videos = ["2564k.mp4","1864k.mp4","1264k.mp4","464k.mp4"]
              i = int(addon.getSetting('vid_res'))
              res_video = res_videos[i]
              i = int(addon.getSetting('thumb_res'))
              res_thumb = res_thumbs[i]

              link=getRequest(url).replace('\\/','/').replace('\\"',"'")
              match = re.compile('"name": "(.+?)","description": "(.+?)".+?"thumbnailURL": "(.+?)_167x94.jpg.+?"videoURL": "http://hdsvod-f.akamaihd.net/z(.+?),.+?CreationDate": "(.+?)"').findall(link)
              for cattitle, catdesc, caticon, caturl, catdate in match:
                if not MANIFEST in caturl:
                   caturl = VID_BASE+caturl+res_video
                else:
                   caturl = VID_BASE+caturl.replace(MANIFEST,"")
                caturl   =  caturl.encode(UTF8)
                caticon  += res_thumb
                catdesc  =  strip_unicode(catdesc)
                cattitle =  strip_unicode(cattitle)
                try:
                   addLink(caturl,cattitle,caticon,fanart,catdate+'\n'+catdesc,GENRE_NEWS,"",autoplay=auto_play)
                except:
                   log("Problem adding directory")

              if auto_play == True:
                   xbmc.executebuiltin('playlist.playoffset(video,0)')

xbmcplugin.endOfDirectory(int(sys.argv[1]))