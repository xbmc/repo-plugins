# -*- coding: utf-8 -*-
# snagfilms XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25

addon         = xbmcaddon.Addon('plugin.video.snagfilms')
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

def getRequest(url, user_data=None, headers = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'}  ):


      retries = 0
      while retries < 2:
           try:
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

           except urllib2.HTTPError,e:
              if e.code == 500:
                     dialog = xbmcgui.Dialog()
                     ok = dialog.ok(__addonname__, __language__(31000))
                     break
              retries += 1
              xbmc.sleep(2)
              continue
           else:
              break



def getSources(fanart):
      addDir(__language__(30002), __language__(30002), 'GM', icon, addonfanart, __language__(30002), '', '')
      addDir(__language__(30003), __language__(30003), 'GS', icon, addonfanart, __language__(30003), '', '')
      addDir('[COLOR red]'+__language__(30015)+'[/COLOR]','ABC','GH', icon, addonfanart, '[COLOR red]'+__language__(30015)+'[/COLOR]','','') 


def getShows(fanart):
    html = getRequest('http://www.snagfilms.com/shows/')
    cats = re.compile('image:(.+?)}').findall(html)
    for blob in cats:
      c_vars = re.compile("'(.+?)'").findall(blob)
      img  = c_vars[0]
      name = urllib.unquote_plus(str(c_vars[2]).replace('\\x','%'))
      url  = c_vars[3]
      if url.startswith('/show'):
       addDir(name.encode(UTF8), url, 'GC', img.encode(UTF8), addonfanart, name.encode(UTF8), '', '')


def getMovies(fanart):
    html = getRequest('http://www.snagfilms.com/categories/')
    cats = re.compile('<a class="genre-item(.+?)</a>').findall(html)
    for blob in cats:
      url = re.compile('href="(.+?)"').findall(blob)[0]
      img = re.compile('url\((.+?)\)').findall(blob)[0]
      name = re.compile('genre-centered">(.+?)<').findall(blob)[0]
      url = url+'#'+img
      addDir(name, url, 'GT', img, addonfanart, name, '', '')

def getMovieType(url, name):
       (url,img) = url.split('#',1)
       addDir((name+' - '+(__language__(30016))).encode(UTF8), url, 'GC', img , addonfanart, (name+' - '+(__language__(30016))).encode(UTF8), '', '')
       addDir((name+' - '+(__language__(30017))).encode(UTF8), url, 'GR', img , addonfanart, (name+' - '+(__language__(30017))).encode(UTF8), '', '')

def getMovieRecent(url):
       getCats(url,sort_type='justadded')


def getSearch(sid):
    keyb = xbmc.Keyboard('', __language__(30000))
    keyb.doModal()
    if (keyb.isConfirmed()):
         search = urllib.quote_plus(keyb.getText())
         x_url = '/search/?q=%s' % (search)

         url2 = 'http://www.snagfilms.com/'
         user_data = urllib.urlencode({'url': x_url})
         headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0', 'Accept' : '*/*', 'Referer' : 'http://www.snagfilms.com%s' % (x_url),'X-Requested-With' : 'XMLHttpRequest', 'Origin': 'http://www.snagfilms.com'}

         cj = cookielib.CookieJar()
         opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
         urllib2.install_opener(opener)

         html = getRequest(url2, user_data, headers)

         url2 = 'http://www.snagfilms.com/apis/user/incrementPageView'
         user_data = urllib.urlencode({'url': x_url})
         headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0', 'Accept' : '*/*', 'Referer' : 'http://www.snagfilms.com%s' % (x_url),'X-Requested-With' : 'XMLHttpRequest', 'Origin': 'http://www.snagfilms.com'}
         html = getRequest(url2, user_data, headers)


         s_url = 'http://www.snagfilms.com/apis/search.json?searchTerm=%s&type=film&limit=50' % (search)
         html = getRequest(s_url, None, headers)
         shows = re.compile('{"id":"(.+?)".+?"title":"(.+?)".+?"imageUrl":"(.+?)"').findall(html)
         for sid, sname, simg in shows:
             surl = sys.argv[0]+"?url="+urllib.quote_plus(sid)+"&mode=GV"
             simg = urllib.unquote_plus(simg)
             simg = simg.split('url=',1)[1]
             addLink(surl.encode(UTF8),sname,simg,addonfanart,sname,'','',False)

         s_url = 'http://www.snagfilms.com/apis/search.json?searchTerm=%s&type=show&limit=50' % (search)
         html = getRequest(s_url, None, headers)
         shows = re.compile('{"id":"(.+?)".+?"title":"(.+?)".+?"permaLink":"(.+?)".+?"imageUrl":"(.+?)"').findall(html)
         for sid, sname, surl, simg in shows:
             simg = urllib.unquote_plus(simg)
             simg = simg.split('url=',1)[1]
             addDir(sname, surl.encode(UTF8), 'GC', simg, addonfanart, sname,'','')


def getCats(c_url, sort_type='popular'):
    cat_url = 'http://www.snagfilms.com%s' % (c_url)
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    html = getRequest(cat_url)
    x_url = re.compile('rel="canonical" href="(.+?)"').search(html).group(1)
    try:
#      showid = re.compile('data-show-id="(.+?)"').search(html).group(1)
      showid = re.compile('data-content-id="(.+?)"').search(html).group(1)

    except:
      showid = ''

    url2 = 'http://www.snagfilms.com/apis/user/incrementPageView'
    user_data = urllib.urlencode({'url': x_url})
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0', 'Accept' : '*/*', 'Referer' : 'http://www.snagfilms.com%s' % (c_url)
,'X-Requested-With' : 'XMLHttpRequest', 'Origin': 'http://www.snagfilms.com'}
    html = getRequest(url2, user_data, headers)

    if x_url.startswith('/movie') or x_url.startswith('/film'):
      types = c_url.split('/')
      file_type = types[1]
      if types[2] == 'sci_fi':
        category = 'sci-fi'
      else:
        category  = types[2].replace('_','%20')
      url3 = 'http://www.snagfilms.com/apis/movies?limit=200&offset=0&sort_type=%s&film_type=%s&category=%s' % (sort_type,file_type, category)
    else:
      url3 = 'http://www.snagfilms.com/apis/show/%s' % (showid)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0', 'Accept' : 'application/json, text/javascript, */*', 'Referer' : 'http://www.snagfilms.com%s' % (c_url)
,'X-Requested-With' : 'XMLHttpRequest', 'Origin': 'http://www.snagfilms.com'}

    html = getRequest(url3, None , headers)
    shows = re.compile('{"id":"(.+?)".+?"title":"(.+?)".+?"logline":"(.+?)".+?"primaryCategory".+?"title":"(.+?)".+?{"height".+?"src":"(.+?)"').findall(html)
    for sid, sname, sdesc, sgenre, simg in shows:
      if ('url=' in simg):
        simg = urllib.unquote_plus(simg)
        simg = simg.split('url=',1)[1]
      if not ('ytimg' in simg):
       surl = sys.argv[0]+"?url="+urllib.quote_plus(sid)+"&mode=GV"
       addLink(surl.encode(UTF8),sname,simg.encode(UTF8),addonfanart,sdesc,sgenre,'',False)
      else:
       ytid = simg.split('/')[4]
       surl = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (ytid)
       addLink(surl.encode(UTF8),sname,simg.encode(UTF8),addonfanart,sdesc,sgenre,'',False)



def getVideo(sid):
    html = getRequest('http://www.snagfilms.com/api/assets.jsp?id=%s' % (sid))
    playlist = re.compile('"bitrate" : (.+?),.+?"streamName" : "(.+?)"').findall(html)
    try:
       bitrates = [500, 1500, 2500, 5000, 7000, 9500, 15000]
       try:
         urate    = bitrates[int(addon.getSetting('bitrate'))]
       except:
         urate = 500
       current  = 0
       for bitrate,pp in playlist:
        if (int(bitrate) < int(urate)) and (current < int(bitrate)):
          current = int(bitrate)
          playpath = pp
       if current == 0: (current, playpath) = playlist[0]
       surl = 'rtmp://stream.snagfilms.com/films playpath=%s swfUrl=http://www.snagfilms.com/assets/media-player/swf/MediaPlayer.swf pageUrl=http://www.snagfilms.com/' % (playpath)
       xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=surl))
    except:
       dialog = xbmcgui.Dialog()
       dialog.ok(__language__(30000), '',__language__(30001))
       




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

mode = p('mode', None)

if mode==  None:  getSources(p('fanart'))
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='PP':  play_playlist(p('name'), p('playlist'))
elif mode=='GV':  getVideo(p('url'))
elif mode=='GM':  getMovies(p('url'))
elif mode=='GS':  getShows(p('url'))
elif mode=='GC':  getCats(p('url'))
elif mode=='GH':  getSearch(p('url'))
elif mode=='GT':  getMovieType(p('url'),p('name'))
elif mode=='GR':  getMovieRecent(p('url'))


xbmcplugin.endOfDirectory(int(sys.argv[1]))




