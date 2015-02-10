# -*- coding: utf-8 -*-
# Wall Street Journal Live

import urllib, urllib2, cookielib, datetime, time, re, os
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs
import cgi, gzip
from StringIO import StringIO
import json


USER_AGENT    = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_2_1 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
GENRE_NEWS      = "News"
UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.wsj')
__addonname__ = addon.getAddonInfo('name')
home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
fanart        = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge

def getRequest(url, user_data=None, headers = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'}  ):
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


def getSources(fanART):
              blob  = re.compile('<nav class="top">(.+?)</nav').search(getRequest('http://wsj.com/video')).group(1)
              match = re.compile('href="(.+?)">(.+?)<').findall(blob)
              for caturl, category in match:
                if '/video' in caturl and (not ('/sponsored' in caturl)):
                    addDir(category,caturl,'GC',icon,fanart,"",GENRE_NEWS,"",False)

def getCats(url):
           if '/browse' in url:
             pg   = getRequest(url)
             blob = re.compile('<div class="select-holder">(.+?)</div>').search(pg).group(1)
             cats = re.compile('value="(.+?)">(.+?)</option>').findall(blob)
             for caturl, cattext in cats:
                 cattext = cattext.replace('&nbsp;','').replace('&amp;','&')
                 caturl  = 'http://www.wsj.com%s' % caturl
                 addDir(cattext,caturl,'GS',icon,fanart,"",GENRE_NEWS,"",False)
           elif ('/topics' in url):
             pg   = getRequest(url)
             topics = re.compile('data-ref="(.+?)".+?href="(.+?)"').findall(pg)
             for cattext, caturl in topics:
                 cattext = cattext.replace('&nbsp;','').replace('&amp;','&')
                 addDir(cattext,caturl,'GS',icon,fanart,"",GENRE_NEWS,"",False)
           elif ('/programs' in url):
             pg   = getRequest(url)
             topics = re.compile('span class="playbtn".+?href="(.+?)".+?title="(.+?)"').findall(pg)
             for caturl, cattext in topics:
                 cattext = cattext.replace('&nbsp;','').replace('&amp;','&').replace('&#39;',"'")
                 addDir(cattext,caturl,'GS',icon,fanart,"",GENRE_NEWS,"",False)


def getShow(url, name):
              url   = urllib.unquote_plus(url)
              pg    = getRequest(url)
              url   = re.compile('data-ref=.+?href="(.+?)"').search(pg).group(1)
              url   = url.replace('format=rss','format=json').replace('&amp;','&').replace(' ','%20').replace('&#39;','%27')
              url   = url+'&fields=name%2CvideoURL%2Ccolumn%2Cthumbnail1280x720URL%2Cthumbnail640x360URL%2ClinkURL%2CthumbnailURL%2CformattedCreationDate%2Cdescription&count=50'
              pg    = getRequest(url)
              a     = json.loads(pg)
              a = a['items']
              for item in a:
                 url = item['videoURL']
                 url = url.replace('\\','')
                 url = url.replace('http://hdsvod-f.akamaihd.net/z','http://wsjvod-i.akamaihd.net/i')
                 url = url.replace('manifest.f4m','master.m3u8')
                 addLink(url, item['name'] , item['thumbnailURL'],fanart, '%s\n%s' % (item['formattedCreationDate'],item['description']),item['column'],'')
                

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

mode = p('mode',None)
if mode==  None:  getSources(p('fanart'))
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=urllib.unquote_plus(p('url'))))
elif mode=='GC':  getCats(p('url'))
elif mode=='GS':  getShow(p('url'), p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))
