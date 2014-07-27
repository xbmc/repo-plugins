# -*- coding: utf-8 -*-
# Viewster XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
import json
from StringIO import StringIO


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25

addon         = xbmcaddon.Addon('plugin.video.viewster')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

#play = False

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

              link1 = str(link1).replace('\n','')
              return(link1)

def getSources(fanart):
    html = getRequest('http://api.live.viewster.com/api/v1/login', headers = {'Accept': '*/*', 'Origin': 'http://www.viewster.com', 
                      'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
                      'Referer' : 'http://www.viewster.com', 'Accept-Encoding': 'gzip,deflate,sdch', 
                      'Accept-Language' : 'en-US,en;q=0.8'})

    html = getRequest('http://api.live.viewster.com/api/v1/configuration/', headers = {'Accept': 'application/json, text/javascript, */*; q=0.01', 'Origin': 'http://www.viewster.com', 
                      'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
                      'Referer' : 'http://www.viewster.com', 'Accept-Encoding': 'gzip,deflate,sdch', 
                      'Accept-Language' : 'en-US,en;q=0.8'})

    cats = json.loads(html)
    x = cats['Genres']
    for list in x:
      sname = list['name']
      sid = list['id']
      img  =   'http://divaag.vo.llnwd.net/o42/http_rtmpe/shared/Viewster_Artwork/internal_artwork/g%s_1280x720.jpg' % sid
      sid = sid.encode(UTF8)+('#').encode(UTF8)+sname.encode(UTF8)
      addDir(sname, sid, 'GC', img, addonfanart, sname, '', '')      
    addDir("[COLOR red]%s[/COLOR]" % __language__(30001),"/search/Movies#%s" % __language__(30001),'DS','',fanart,__language__(30001),"","",False)
    addDir("[COLOR red]%s[/COLOR]" % __language__(30002),"/search/TvShow#%s" % __language__(30002),'DS','',fanart,__language__(30002),"","",False)

def doSearch(osid):
        keyb = xbmc.Keyboard('', 'Search')
        keyb.doModal()
        if (keyb.isConfirmed()):
            search = urllib.quote_plus(keyb.getText())
            getShow(osid, query=search)

def getCats(url):
    (url,xname) = url.split('#',1)
    img  =   'http://divaag.vo.llnwd.net/o42/http_rtmpe/shared/Viewster_Artwork/internal_artwork/g%s_1280x720.jpg' % url
    html = getRequest('http://api.live.viewster.com/api/v1/home/%s' % (url), headers = {'Accept': 'application/json, text/javascript, */*; q=0.01', 'Origin': 'http://www.viewster.com', 
                      'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
                      'Referer' : 'http://www.viewster.com', 'Accept-Encoding': 'gzip,deflate,sdch', 
                      'Accept-Language' : 'en-US,en;q=0.8'})
    a = json.loads(html)
    x = a['collections']
    for list in x:
      z = list['asset_list']
      for list1 in z:
        sid = list1['datasource']['path']  
        sname = list1['metadata']['display_text']  
        addDir(sname, '%s#%s' % (sid,sname), 'GS', img, addonfanart, xname, '', '')
       

def getShow(osid, start='0', end=str(MAX_PER_PAGE-1), order='1', lang='1', query='undefined'):
      (sid, sxname) = osid.split('#',1)
      if '#' in sxname:
          (sxname,start,end,order,lang,query) = sxname.split('#',5)
      qurl = 'http://api.live.viewster.com/api/v1%s?from=%s&to=%s&q=%s&order=%s&lang=%s' % (sid, start, end, query, order, lang)
      html = getRequest(qurl, headers = {'Accept': 'application/json, text/javascript, */*; q=0.01', 'Origin': 'http://www.viewster.com', 
                      'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
                      'Referer' : 'http://www.viewster.com', 'Accept-Encoding': 'gzip,deflate,sdch', 
                      'Accept-Language' : 'en-US,en;q=0.8'})

      a = json.loads(html)
      ptemplate = a['image_path_masks']['Poster']
      scnt = 0
      for show in a['data']:
        scnt = scnt + 1
        sname  = show['title'].encode(UTF8)
        sdate  = show['publish_date']
        shid   = show['id']
        xid    = shid.encode(UTF8)+('#').encode(UTF8)+sname
        sdesc  = show['synopsis'].encode(UTF8)
        sgenre = show['genre']
        ctitle = show['canonical_title']
        simg   = ptemplate.replace('[mid]',shid).replace('[size]','')
        if sxname != 'Tv-Series':
            surl = sys.argv[0]+"?url="+urllib.quote_plus(shid)+"&name="+urllib.quote_plus(ctitle)+"&mode=GV"
            addLink(surl.encode(UTF8),sname,simg.encode(UTF8),addonfanart,sdesc,sgenre,sdate,False)
        else:
            addDir(sname, xid , 'GE', simg.encode(UTF8), addonfanart, sdesc, sgenre, sdate)
      if scnt >= MAX_PER_PAGE-1:
           start = str(int(end)+1)
           end = str(int(end)+MAX_PER_PAGE)
           sname = '[COLOR blue] %s [/COLOR]' % __language__(30000)
           addDir(sname, '%s#%s#%s#%s#%s#%s#%s' % (sid,sxname,start,end,order,lang,query), 'GS', icon, addonfanart, sname, '', '')


def getEpisodes(sid):
    (sid, sxname) = sid.split('#',1)
    html = getRequest('http://api.live.viewster.com/api/v1/movie/%s' % (sid), headers = {'Accept': 'application/json, text/javascript, */*; q=0.01', 'Origin': 'http://www.viewster.com', 
                      'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
                      'Referer' : 'http://www.viewster.com', 'Accept-Encoding': 'gzip,deflate,sdch', 
                      'Accept-Language' : 'en-US,en;q=0.8'})
    c = json.loads(html)
    if c['content_type'] == 'Series':
      for clip in c['play_list']:
        if clip['clip_type'] == 'Episode':
           sname  = '%s - %s' % (sxname,clip['title'].encode(UTF8))
           sdesc  = clip['title'].encode(UTF8)
           sid    = clip['id']
           ctitle = clip['canonical_title']
           simg = 'http://divaag.vo.llnwd.net/o42/http_rtmpe/shared/Viewster_Artwork/movie_artwork/%s_EN.jpg' % (sid)
           surl = sys.argv[0]+"?url="+urllib.quote_plus(sid)+"&name="+urllib.quote_plus(ctitle)+"&mode=GV"
           addLink(surl.encode(UTF8),sname,simg.encode(UTF8),addonfanart,sdesc,'','',False)


def getVideo(sid, name):

    sid = urllib.unquote_plus(sid)
    name = urllib.unquote_plus(name)
    html = getRequest('http://api.live.viewster.com/api/v1/movie/%s' % (sid), headers = {'Accept': 'application/json, text/javascript, */*; q=0.01', 'Origin': 'http://www.viewster.com', 
                      'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
                      'Referer' : 'http://www.viewster.com', 'Accept-Encoding': 'gzip,deflate,sdch', 
                      'Accept-Language' : 'en-US,en;q=0.8'})

    c = json.loads(html)
    if c['content_type'] == 'Trailer':
      for clip in c['play_list']:
        if clip['clip_type'] == 'Trailer':
           url = clip['clip_data']['url']
           xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url)) 

    elif c['content_type'] == 'Movie' or c['content_type'] == 'Series':
      if c['content_type'] == 'Movie':
        a =  c['play_list'][0]['languages'][0]
      else:
        for a in c['play_list']:
          if a['autoplay'] == True:
            break

      try:
        a =  a['link_request']
      except:
        return
      parms = urllib.urlencode(a)
      html = getRequest('http://api.live.viewster.com/api/v1/MovieLink?%s' % (parms), 
            headers = {'Accept': '*/*', 'Origin': 'http://www.viewster.com', 
                      'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) CriOS/34.0.1847.18 #Mobile/11B554a Safari/9537.53',
                      'Referer' : 'http://www.viewster.com/movie/%s/%s' % (sid, name), 'Accept-Encoding': 'gzip,deflate,sdch', 
                      'Accept-Language' : 'en-US,en;q=0.8'})

      a = json.loads(html)
      url = 'http://production-ps.lvp.llnw.net/r/PlaylistService/media/%s/getMobilePlaylistByMediaId?platform=MobileH264&' % (a['media_id'])
      html = getRequest('%s' % (url), 
            headers = {'Accept': '*/*', 'Origin': 'http://www.viewster.com', 
                      'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) CriOS/34.0.1847.18 #Mobile/11B554a Safari/9537.53',
                      'Referer' : 'http://www.viewster.com/movie/%s/%s' % (sid, name), 'Accept-Encoding': 'gzip,deflate,sdch', 
                      'Accept-Language' : 'en-US,en;q=0.8'})

      a = json.loads(html)
      url = a['mediaList'][0]['mobileUrls'][0]['mobileUrl']
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url)) 

           
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

if mode==  None:  getSources(p('fanart'))
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='PP':  play_playlist(p('name'), p('playlist'))
elif mode=='GC':  getCats(p('url'))
elif mode=='GS':  getShow(p('url'))
elif mode=='GE':  getEpisodes(p('url'))
elif mode=='GV':  getVideo(p('url'),p('name'))
elif mode=='DS':  doSearch(p('url'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))




