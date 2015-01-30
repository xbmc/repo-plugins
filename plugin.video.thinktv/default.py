# -*- coding: utf-8 -*-
# ThinkTV PBS XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25

addon         = xbmcaddon.Addon('plugin.video.thinktv')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def cleanname(name):    
    return name.replace('&apos;',"'").replace('&#8217;',"'").replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"')

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge


def getRequest(url, user_data=None, headers = {'User-Agent':USER_AGENT, 
                                               'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                                               'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'}  ):
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

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
              pset = '0ABCDEFGHIJKLMNOPQRSTUVWXYZ'
              addDir(__language__(30012),pset,'GA',icon,addonfanart,__language__(30012),GENRE_TV,'')
              addDir(__language__(30013),pset,'GZ',icon,addonfanart,__language__(30013),GENRE_TV,'')
              addDir(__language__(30014),'dummy','GQ',icon,addonfanart,__language__(30014),GENRE_TV,'')

def getQuery(cat_url):
        keyb = xbmc.Keyboard('', __addonname__)
        keyb.doModal()
        if (keyb.isConfirmed()):
              qurl = urllib.quote_plus('/search/?q=%s' % (keyb.getText()))
              getCats(qurl)

def showAtoZ(azurl):
        for a in azurl:
              addDir(a,a,'GA',icon,addonfanart,a,GENRE_TV,'')
                
def getAtoZ(gzurl):
              pg = getRequest('http://video.pbs.org/programs/list',None, 
                    {'X-Requested-With': 'XMLHttpRequest', 
                     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                     'User-Agent': USER_AGENT,
                     'Accept-Encoding': 'gzip, deflate, sdch',
                     'Accept-Language': 'en-US,en;q=0.8'})
              log("GS pg="+str(pg))
              a = json.loads(pg)
              for y in gzurl:
                try:
                  b = a[y]
                  for x in b:
                     showname = cleanname('%s [%s]' %(x['title'], x['video_count']))
                     showurl = urllib.quote_plus('program/%s/episodes/' % x['slug'])
                     addDir(showname.encode(UTF8),showurl.encode(UTF8),'GC',icon,addonfanart,showname,GENRE_TV,'')
                except:
                  pass

def getCats(gcurl):
              gcurl = urllib.unquote_plus(gcurl)
              if 'search/?q=' in gcurl:
                chsplit = '&'
                gcurl = gcurl.replace(' ','+')
              else:
                chsplit = '?'
              log("final gcurl = "+str(gcurl))
              pg = getRequest('http://video.pbs.org/%s' % (gcurl))
              epis = re.compile('<li class="videoItem".+?data-videoid="(.+?)".+?data-title="(.+?)".+?src="(.+?)".+?class="description">(.+?)<.+?<p class="duration">(.+?)</p></li>').findall(pg)
              for url,name,img,desc,dur in epis:
                  surl = '%s?mode=GS&url=%s' %(sys.argv[0], urllib.quote_plus(url))
                  addLink(surl,cleanname(name),img,addonfanart,cleanname(desc),GENRE_TV,'')
              try:
                  nps = re.compile('visiblePage"><a href="(.+?)">(.+?)<').findall(pg)
                  (npurl, npname) = nps[len(nps)-1]
                  if npname == 'Next':
                     npurl = npurl.split(chsplit,1)[1]
                     npurl = urllib.quote_plus(gcurl.split(chsplit,1)[0]+chsplit+npurl)
                     npname = '[COLOR blue]%s[/COLOR]' % npname
                     addDir(npname,npurl,'GC',icon,addonfanart,npname,GENRE_TV,'')
              except:
                  pass

                 


def getShow(gsurl):
              pg = getRequest('http://video.pbs.org/videoInfo/%s/?format=json' % (urllib.unquote_plus(gsurl)))
              log("show page = "+str(pg))
              url = json.loads(pg)['recommended_encoding']['url']
              pg = getRequest('%s?format=json' % url)
              url = json.loads(pg)['url']
              if '.m3u8' in url:
                 try:
                   url = url.split('hls-64-800k',1)[0]
                   url += 'hls-2500k.m3u8'
                 except:
                   pass

              log("final url = "+str(url))
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))


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

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

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
elif mode=='GA':  getAtoZ(p('url'))
elif mode=='GQ':  getQuery(p('url'))
elif mode=='GZ':  showAtoZ(p('url'))
elif mode=='GS':  getShow(p('url'))
elif mode=='GC':  getCats(p('url'))


xbmcplugin.endOfDirectory(int(sys.argv[1]))

