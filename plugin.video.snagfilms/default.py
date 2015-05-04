# -*- coding: utf-8 -*-
# snagfilms XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25

addon         = xbmcaddon.Addon('plugin.video.snagfilms')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

qp  = urllib.quote_plus
uqp = urllib.unquote_plus

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def cleanname(name):    
    return name.replace('&apos;',"'").replace('&#8217;',"'").replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"').replace('&nbsp;',' ')

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
              dolist = [('http://www.snagfilms.com/categories/','GM', 30002, icon),('http://www.snagfilms.com/shows/','GM', 30003, icon),('ABC','GH', 30015, icon)]

              for url, mode, gstr, img in dolist:
                  name = __language__(gstr)
                  liz  = xbmcgui.ListItem(name,'',img,img)
                  liz.setProperty('fanart_image', addonfanart)
                  xbmcplugin.addDirectoryItem(int(sys.argv[1]), '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), mode), liz, True)

def getShows(fanart):
    ilist=[]
    html = getRequest('http://www.snagfilms.com/shows/')
    cats = re.compile('image:(.+?)}').findall(html)
    for blob in cats:
      c_vars = re.compile("'(.+?)'").findall(blob)
      img  = c_vars[0].encode(UTF8)
      name = urllib.unquote_plus(str(c_vars[2]).replace('\\x','%')).encode(UTF8)
      plot = name
      url  = c_vars[3]
      if url.startswith('/show'):
          mode = 'GC'
          u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
          liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
          liz.setInfo( 'Video', { "Title": name, "Plot": plot })
          liz.setProperty('fanart_image', addonfanart)
          ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))



def getMovies(murl):
    ilist=[]
    murl = uqp(murl)
    html = getRequest(murl)
    html = re.compile('Snag.page.data = (.+?)];').search(html).group(1)
    html = html + ']'
    a = json.loads(html)
    a = a[3]['data']['items']
    for item in a:
       url  = item['permalink']
       name = item['title']
       img  = item['image']
       try:    plot = item['description']
       except: plot =''
       gurl = url+'#'+img
       if 'shows' in murl: mode ='GC'
       else: mode = 'GT'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(gurl), qp(name), mode)
       liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
       liz.setInfo( 'Video', { "Title": name, "Plot": plot })
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getMovieType(url, name):
    ilist=[]
    url = uqp(url)
    (url, img) = url.split('#',1)
    html = getRequest('http://www.snagfilms.com%s' % url)
    html = re.compile('Snag.page.data = (.+?)];').search(html).group(1)
    html = html + ']'
    a = json.loads(html)
    mode = 'GG'
    for item in a[1:]:
      try:
       if item["rendererCode"] == "tray":
         name = item['title']
         plot = name
         gurl = url +'#'+item["id"]
         u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(gurl), qp(name), mode)
         liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
         liz.setInfo( 'Video', { "Title": name, "Plot": plot })
         liz.setProperty('fanart_image', addonfanart)
         ilist.append((u, liz, True))
      except: pass
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))



def getGenre(url):
    ilist=[]
    url = uqp(url)
    (url, id) = url.split('#',1)
    html = getRequest('http://www.snagfilms.com%s' % url)
    html = re.compile('Snag.page.data = (.+?)];').search(html).group(1)
    html = html + ']'
    a = json.loads(html)
    for b in a[1:]:
      try:
       if b["id"] == id:
         c = b['data']['items']
         for item in c:
            name = cleanname(item['title']).encode(UTF8)
            plot = cleanname(item['description']).encode(UTF8)
            u  = "%s?url=%s&mode=GV" % (sys.argv[0], qp(item['id']))
            img  = item['images']['poster']
            liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
            liz.setInfo( 'Video', { "Title": name, "Plot": plot })
            liz.setProperty('fanart_image', addonfanart)
            liz.setProperty('IsPlayable', 'true')
            liz.setProperty('mimetype', 'video/x-msvideo')
            ilist.append((u, liz, False))
      except: pass
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getSearch(sid):
    keyb = xbmc.Keyboard('', __language__(30000))
    keyb.doModal()
    if (keyb.isConfirmed()):
         search = urllib.quote_plus(keyb.getText())
         x_url = '/search/?q=%s' % (search)

         url2 = 'http://www.snagfilms.com/'
         user_data = urllib.urlencode({'url': x_url})
         headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0', 
                    'Accept' : '*/*',
                    'Referer' : 'http://www.snagfilms.com%s' % (x_url),
                    'X-Requested-With' : 'XMLHttpRequest',
                    'Origin': 'http://www.snagfilms.com'}

         cj = cookielib.CookieJar()
         opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
         urllib2.install_opener(opener)

         html = getRequest(url2, user_data, headers)

         url2 = 'http://www.snagfilms.com/apis/user/incrementPageView'
         user_data = urllib.urlencode({'url': x_url})
         headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Fi refox/11.0',
                    'Accept' : '*/*',
                    'Referer' : 'http://www.snagfilms.com%s' % (x_url),
                    'X-Requested-With' : 'XMLHttpRequest',
                    'Origin': 'http://www.snagfilms.com'}
         html = getRequest(url2, user_data, headers)

         s_url = 'http://www.snagfilms.com/apis/search.json?searchTerm=%s&type=film&limit=50' % (search)
         html = getRequest(s_url, None, headers)
         shows = re.compile('{"id":"(.+?)".+?"title":"(.+?)".+?"imageUrl":"(.+?)"').findall(html)
         ilist=[]
         for sid, name, simg in shows:
             u = "%s?url=%s&mode=GV" %(sys.argv[0], uqp(sid))
             img = uqp(simg)
             img = img.split('url=',1)[1]
             plot = name
             liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
             liz.setInfo( 'Video', { "Title": name, "Plot": plot })
             liz.setProperty('fanart_image', addonfanart)
             liz.setProperty('mimetype', 'video/x-msvideo')
             liz.setProperty('IsPlayable', 'true')
             ilist.append((u, liz, False))
         xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


         s_url = 'http://www.snagfilms.com/apis/search.json?searchTerm=%s&type=show&limit=50' % (search)
         html = getRequest(s_url, None, headers)
         shows = re.compile('{"id":"(.+?)".+?"title":"(.+?)".+?"permaLink":"(.+?)".+?"imageUrl":"(.+?)"').findall(html)
         ilist =[]
         for sid, name, surl, simg in shows:
             u = "%s?url=%s&mode=GC" %(sys.argv[0], uqp(surl))
             img = uqp(simg)
             img = img.split('url=',1)[1]
             plot = name
             liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
             liz.setInfo( 'Video', { "Title": name, "Plot": plot })
             liz.setProperty('fanart_image', addonfanart)
             ilist.append((u, liz, True))
         xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getCats(c_url, sort_type='popular'):
    c_url = uqp(c_url)
    cat_url = c_url.split('#',1)[0]
    if not (cat_url.startswith('http')): cat_url = 'http://www.snagfilms.com%s' % cat_url
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    html = getRequest(cat_url)
    x_url = re.compile('rel="canonical" href="(.+?)"').search(html).group(1)
    try:    showid = re.compile('data-content-id="(.+?)"').search(html).group(1)
    except: showid = ''

    url3 = 'http://www.snagfilms.com/apis/show/%s' % (showid)
    url2 = 'http://www.snagfilms.com/apis/user/incrementPageView'
    user_data = urllib.urlencode({'url': x_url})
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0', 
               'Accept' : '*/*',
               'Referer' : 'http://www.snagfilms.com%s' % (c_url),
               'X-Requested-With' : 'XMLHttpRequest', 
               'Origin': 'http://www.snagfilms.com'}
    html = getRequest(url2, user_data, headers)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0', 
               'Accept' : 'application/json, text/javascript, */*',
               'Referer' : 'http://www.snagfilms.com%s' % (c_url),
               'X-Requested-With' : 'XMLHttpRequest', 
               'Origin': 'http://www.snagfilms.com'}

    html = getRequest(url3, None , headers)
    shows = re.compile('{"id":"(.+?)".+?"title":"(.+?)".+?"logline":"(.+?)".+?"primaryCategory".+?"title":"(.+?)".+?{"height".+?"src":"(.+?)"').findall(html)
    ilist=[]
    for sid, name, sdesc, sgenre, simg in shows:
      if ('url=' in simg):
          simg = urllib.unquote_plus(simg)
          simg = simg.split('url=',1)[1]
      if not ('ytimg' in simg):
          u = "%s?url=%s&mode=GV" %(sys.argv[0], uqp(sid))
          img = simg
          plot = cleanname(sdesc)
          liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
          liz.setInfo( 'Video', { "Title": name, "Plot": plot })
          liz.setProperty('fanart_image', addonfanart)
          liz.setProperty('mimetype', 'video/x-msvideo')
          liz.setProperty('IsPlayable', 'true')
          ilist.append((u, liz, False))
      else:
          ytid = simg.split('/')[4]
          u = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (ytid)
          img = simg
          plot = cleanname(sdesc)
          liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
          liz.setInfo( 'Video', { "Title": name, "Plot": plot })
          liz.setProperty('fanart_image', addonfanart)
          liz.setProperty('IsPlayable', 'true')
          ilist.append((u, liz, False))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))



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
elif mode=='GV':  getVideo(p('url'))
elif mode=='GM':  getMovies(p('url'))
elif mode=='GS':  getShows(p('url'))
elif mode=='GC':  getCats(p('url'))
elif mode=='GH':  getSearch(p('url'))
elif mode=='GT':  getMovieType(p('url'),p('name'))
elif mode=='GG':  getGenre(p('url'))


xbmcplugin.endOfDirectory(int(sys.argv[1]))




