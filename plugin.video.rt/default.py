# -*- coding: utf-8 -*-
# Russia Today (RT) News

import urllib, urllib2, cookielib, datetime, time, re, os
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs
import cgi, gzip
from StringIO import StringIO


USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
GENRE_NEWS      = "News"
UTF8          = 'utf-8'
RTBASE_URL    = 'http://rt.com'
RTLIVE_BASE   = 'http://odna.octoshape.net/f3f5m2v4/cds/'

addon         = xbmcaddon.Addon('plugin.video.rt')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
fanart        = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


def _parse_argv():

        global url,name,iconimage, mode, playlist,fchan,fres,fhost,fname,fepg,fanArt

        params = {}
        try:
            params = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
        except:
            params = {}

        url =       demunge(params.get("url",None))
        name =      demunge(params.get("name",""))
        iconimage = demunge(params.get("iconimage",""))
        fanArt =    demunge(params.get("fanart",""))
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
              log("main page")
              link = getRequest(RTBASE_URL+"/shows/")
              addDir("RT Live","plugin://plugin.video.rt/",17,icon,fanart,"RT Live",GENRE_NEWS,"",False)

              match=re.compile('<p class="shows-gallery_bottom_link"><a href="(.+?)".+?<img src="(.+?)".+?class="shows-gallery_bottom_text_header">(.+?)</span>(.+?)</p>').findall(link)

              for caturl,caticon,cattitle,catdesc in match:
                 catdesc = catdesc.replace('<P>','').replace('<p>','').replace('</P>','')
                 caticon = caticon.replace('.a.','.gp.')
                 if "http:" not in caticon:
                    caticon = RTBASE_URL+caticon
                 try:
                      addDir(cattitle.encode(UTF8, 'ignore'),caturl.encode(UTF8),18,caticon,caticon,catdesc,GENRE_NEWS,"",False)
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


# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

url=name=iconimage=mode=playlist=fchan=fres=fhost=fname=fepg=None

_parse_argv()


log("Mode: "+str(mode))
if not url is None:
    try:
      log("URL: "+str(url.encode(UTF8)))
    except:
      pass

try:
 log("Name: "+str(name))
except:
 pass

auto_play = False

if mode==None:
    log("getSources")
    getSources()
    if addon.getSetting('auto_play') == "true":
      current_play=""
      try:
         current_play = xbmc.Player().getPlayingFile()
      except:
         auto_play = True
         xbmc.PlayList(1).clear()


elif mode==12:
    log("setResolvedUrl")
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

elif mode==13:
    log("play_playlist")
    play_playlist(name, playlist)

if (mode==17) or (auto_play == True):

              res_names = ["Auto","720p","480p","320p","240p"]
              i = int(addon.getSetting('rt_res'))
              res = res_names[i]
              if res == "Auto":
                res = "auto.smil"
              res_str = res_names[i]

              if (auto_play != True):
                addLink(RTLIVE_BASE+"ch1_"+str(res)+"/playlist.m3u8",'%s%s' %(__language__(30005),res_str),icon,fanart,'%s%s' %(__language__(30005),res_str),GENRE_NEWS,"",False)
                addLink(RTLIVE_BASE+"ch4_"+str(res)+"/playlist.m3u8",'%s%s' %(__language__(30006),res_str),icon,fanart,'%s%s' %(__language__(30006),res_str),GENRE_NEWS,"",False)
                addLink(RTLIVE_BASE+"ch5_"+str(res)+"/playlist.m3u8",'%s%s' %(__language__(30007),res_str),icon,fanart,'%s%s' %(__language__(30007),res_str),GENRE_NEWS,"",False)
                addLink(RTLIVE_BASE+"ch6_"+str(res)+"/playlist.m3u8",'%s%s' %(__language__(30008),res_str),icon,fanart,'%s%s' %(__language__(30008),res_str),GENRE_NEWS,"",False)
                addLink(RTLIVE_BASE+"ch2_"+str(res)+"/playlist.m3u8",'%s%s' %(__language__(30009),res_str),icon,fanart,'%s%s' %(__language__(30009),res_str),GENRE_NEWS,"",False)
                addLink(RTLIVE_BASE+"ch3_"+str(res)+"/playlist.m3u8",'%s%s' %(__language__(30010),res_str),icon,fanart,'%s%s' %(__language__(30010),res_str),GENRE_NEWS,"",False)

              else:
                if mode != 17:
                  addLink(RTLIVE_BASE+"ch1_"+str(res_str)+"/playlist.m3u8",'%s%s' %(__language__(30005),res_str),icon,fanart,'%s%s' %(__language__(30005),res_str),GENRE_NEWS,"",False, autoplay=True)
                  xbmc.executebuiltin('playlist.playoffset(video,0)')

elif mode==18:
              log("Processing subcategory item")

              link = getRequest("http://rt.com"+url)

              match = re.compile('<dt class="(.+?)"(.+?)</dl>').findall(link)
              for classtype, classdata in match:
                 if "programm" in classtype:
                    match_str = '<a href="(.+?)".+?class="header">(.+?)<.+?<img src="(.+?)".+?<dd>(.+?)<span class="time">(.+?)<'
                 else:
                    match_str = '<a href="(.+?)".+?<img src="(.+?)".+class="header">(.+?)</a>.+?<p>(.+?)</p.+?class="time">(.+?)<'
                 match = re.compile(match_str).findall(classdata)
                 for pgurl,imgurl,cattitle,catdesc, cattime in match:
                     if "programm" in classtype:
                       imgurl,cattitle = cattitle,imgurl   # swap them
                     caturl = "plugin://plugin.video.rt/?url="+RTBASE_URL+pgurl+"&name="+urllib.quote_plus(cattitle)+"&mode=19"
                     caticon = imgurl
                     if "http:" not in caticon:
                        caticon = RTBASE_URL+caticon
                     catdesc = catdesc.strip()
                     try:
                        addLink(caturl.encode(UTF8),cattitle,caticon,fanArt,cattime+"\n"+catdesc,GENRE_NEWS,"")
                     except:
                        log("Problem adding directory")

              match = re.compile('<a class="pagerLink" href="(.+?)"').findall(link)
              for page in match:
                  addDir("-> Next Page",page,18,fanArt,fanArt,"Next Page",GENRE_NEWS,"",False)
              addDir("<< Home Page","",None,fanArt,fanArt,"Home Page",GENRE_NEWS,"",False)


 
elif mode==19:
              log("Processing play category item")
              link=getRequest(url)
              bad_match = False

              if not ("cdnapi.kaltura.com" in link):
                match = re.compile('<span class="time">(.+?)<.+?<div class="video_block".+?"thumbnailUrl" content="(.+?)".+?"contentURL" content="(.+?)".+?<p>(.+?)</p>').findall(link)
                if not match:
                   bad_match = True
                   dialog = xbmcgui.Dialog()
                   dialog.ok(__language__(30000), '',__language__(30001))
                else:
                 for viddate,icon,vidurl,viddesc in match:
                  if "comhttp:" in vidurl:
                    vidurl = vidurl.replace(RTBASE_URL,"")
              else:
                 match = re.compile('<meta name="description" content="(.+?)".+?<link rel="image_src" href="(.+?)".+?<span class="time">(.+?)<.+?<script src="(.+?)embedIframeJs/.+?"entry_id": "(.+?)"').findall(link)
                 for viddesc,icon,viddate,vidurl,entry_id in match:
                  vidurl = vidurl+"playManifest/entryId/"+entry_id+"/flavorId/0_ib2gjoc9/format/url/protocol/http/a.mp4"

              if not bad_match:
                 item = xbmcgui.ListItem(path=vidurl.encode(UTF8), iconImage="DefaultVideo.png", thumbnailImage=icon)
                 item.setInfo( type="Video", infoLabels={ "Title": name, "Plot": viddate+"\n"+viddesc } )
                 item.setProperty("IsPlayable","true")
                 xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


xbmcplugin.endOfDirectory(int(sys.argv[1]))