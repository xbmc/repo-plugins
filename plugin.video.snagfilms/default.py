# -*- coding: utf-8 -*-
# Snagfilms Kodi Video Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
UTF8          = 'utf-8'

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


defaultHeaders = {'User-Agent':USER_AGENT, 'Accept':"application/json, text/javascript, text/html,*/*", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'}

def getRequest(url, udata=None, headers = defaultHeaders):
   log("getRequest URL:"+str(url))
   req = urllib2.Request(url.encode(UTF8), udata, headers)
   try:
      response = urllib2.urlopen(req)
      page = response.read()
      if response.info().getheader('Content-Encoding') == 'gzip':
         log("Content Encoding == gzip")
         page = zlib.decompress(page, zlib.MAX_WBITS + 16)
   except:
      page = ""
   return(page)




def getSources(fanart):
              dolist = [('http://www.snagfilms.com/categories/','GM', 30002, icon),('http://www.snagfilms.com/shows/','GM', 30003, icon),('ABC','GH', 30015, icon)]

              for url, mode, gstr, img in dolist:
                  name = __language__(gstr)
                  liz  = xbmcgui.ListItem(name,'',img,img)
                  liz.setProperty('fanart_image', addonfanart)
                  xbmcplugin.addDirectoryItem(int(sys.argv[1]), '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), mode), liz, True)
              xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getShows(fanart):
    ilist=[]
    html = getRequest('http://www.snagfilms.com/shows/')
    cats = re.compile('image:(.+?)}',re.DOTALL).findall(html)
    for blob in cats:
      c_vars = re.compile("'(.+?)'",re.DOTALL).findall(blob)
      img  = c_vars[0].encode(UTF8)
      name = urllib.unquote_plus(str(c_vars[2]).replace('\\x','%')).encode(UTF8)
      plot = name
      url  = c_vars[3]
      if url.startswith('/show'):
          mode = 'GC'
          u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
          liz=xbmcgui.ListItem(name, '',None, img)
          liz.setInfo( 'Video', { "Title": name, "Plot": plot })
          liz.setProperty('fanart_image', addonfanart)
          ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))



def getMovies(murl):
    ilist=[]
    murl = uqp(murl)
    html = getRequest(murl)
    html = re.compile('Snag.page.data = (.+?)];',re.DOTALL).search(html).group(1)
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
       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setInfo( 'Video', { "Title": name, "Plot": plot })
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getMovieType(url, name):
    ilist=[]
    url = uqp(url)
    (url, img) = url.split('#',1)
    if not 'http://' in url: url = 'http://www.snagfilms.com%s' % url
    html = getRequest(url)
    html = re.compile('Snag.page.data = (.+?)];',re.DOTALL).search(html).group(1)
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
         liz=xbmcgui.ListItem(name, '',None, img)
         liz.setInfo( 'Video', { "Title": name, "Plot": plot })
         liz.setProperty('fanart_image', addonfanart)
         ilist.append((u, liz, True))
      except: pass
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))



def getGenre(url):
    ilist=[]
    url = uqp(url)
    (url, id) = url.split('#',1)
    if not 'http://' in url: url = 'http://www.snagfilms.com%s' % url
    html = getRequest(url)
    html = re.compile('Snag.page.data = (.+?)];',re.DOTALL).search(html).group(1)
    html = html + ']'
    a = json.loads(html)
    for b in a[1:]:
       try:    z = b["id"]
       except: continue
       if z == id:
         c = b['data']['items']
         for item in c:
            name = h.unescape(item['title'])
            plot = h.unescape(item['description'])
            u  = "%s?url=%s&mode=GV" % (sys.argv[0], qp(item['id']))
            img  = item['images']['poster']
            liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
            liz.setInfo( 'Video', { "Title": name, "Plot": plot })
            liz.setProperty('fanart_image', addonfanart)
            liz.setProperty('IsPlayable', 'true')
            liz.setProperty('mimetype', 'video/x-msvideo')
            ilist.append((u, liz, False))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getSearch(sid):
    keyb = xbmc.Keyboard('', __language__(30000))
    keyb.doModal()
    if (keyb.isConfirmed()):
         search = urllib.quote_plus(keyb.getText())
         x_url = '/search/?q=%s' % (search)

         url2 = 'http://www.snagfilms.com/'
         user_data = urllib.urlencode({'url': x_url})

         headers = defaultHeaders
         headers['X-Requested-With'] = 'XMLHttpRequest'
         cj = cookielib.CookieJar()
         opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
         urllib2.install_opener(opener)

         html = getRequest(url2, user_data, headers)

         url2 = 'http://www.snagfilms.com/apis/user/incrementPageView'
         user_data = urllib.urlencode({'url': x_url})
         html = getRequest(url2, user_data, headers)

         s_url = 'http://www.snagfilms.com/apis/search.json?searchTerm=%s&type=film&limit=50' % (search)
         html = getRequest(s_url, None, headers)
         shows = re.compile('{"id":"(.+?)".+?"title":"(.+?)".+?"imageUrl":"(.+?)"',re.DOTALL).findall(html)
         ilist=[]
         for sid, name, simg in shows:
             u = "%s?url=%s&mode=GV" %(sys.argv[0], uqp(sid))
             img = uqp(simg)
             plot = name
             liz=xbmcgui.ListItem(name, '',None, img)
             liz.setInfo( 'Video', { "Title": name, "Plot": plot })
             liz.setProperty('fanart_image', addonfanart)
             liz.setProperty('mimetype', 'video/x-msvideo')
             liz.setProperty('IsPlayable', 'true')
             ilist.append((u, liz, False))
         xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


         s_url = 'http://www.snagfilms.com/apis/search.json?searchTerm=%s&type=show&limit=50' % (search)
         html = getRequest(s_url, None, headers)
         shows = re.compile('{"id":"(.+?)".+?"title":"(.+?)".+?"permaLink":"(.+?)".+?"imageUrl":"(.+?)"',re.DOTALL).findall(html)
         ilist =[]
         for sid, name, surl, simg in shows:
             u = "%s?url=%s&mode=GC" %(sys.argv[0], uqp(surl))
             img = uqp(simg)
             plot = name
             liz=xbmcgui.ListItem(name, '',None, img)
             liz.setInfo( 'Video', { "Title": name, "Plot": plot })
             liz.setProperty('fanart_image', addonfanart)
             ilist.append((u, liz, True))
         xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
         xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getCats(c_url, sort_type='popular'):
    c_url = uqp(c_url)
    cat_url = c_url.split('#',1)[0]
    if not (cat_url.startswith('http')): cat_url = 'http://www.snagfilms.com%s' % cat_url
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    html = getRequest(cat_url)
    x_url = re.compile('rel="canonical" href="(.+?)"',re.DOTALL).search(html).group(1)
    try:    showid = re.compile('data-content-id="(.+?)"',re.DOTALL).search(html).group(1)
    except: showid = ''

    url3 = 'http://www.snagfilms.com/apis/show/%s' % (showid)
    url2 = 'http://www.snagfilms.com/apis/user/incrementPageView'
    user_data = urllib.urlencode({'url': x_url})

    headers = defaultHeaders
    headers['X-Requested-With'] = 'XMLHttpRequest'

    html = getRequest(url2, user_data, headers)

    html = getRequest(url3, None , headers)
    shows = re.compile('{"id":"(.+?)".+?"title":"(.+?)".+?"logline":"(.+?)".+?"primaryCategory".+?"title":"(.+?)".+?{"height".+?"src":"(.+?)"',re.DOTALL).findall(html)
    ilist=[]
    for sid, name, sdesc, sgenre, simg in shows:
      if ('url=' in simg):
          simg = urllib.unquote_plus(simg)
          simg = simg.split('url=',1)[1]
      if not ('ytimg' in simg):
          u = "%s?url=%s&mode=GV" %(sys.argv[0], uqp(sid))
          img = simg
          plot = h.unescape(sdesc)
          liz=xbmcgui.ListItem(name, '',None, img)
          liz.setInfo( 'Video', { "Title": name, "Plot": plot })
          liz.setProperty('fanart_image', addonfanart)
          liz.setProperty('mimetype', 'video/x-msvideo')
          liz.setProperty('IsPlayable', 'true')
          ilist.append((u, liz, False))
      else:
          ytid = simg.split('/')[4]
          u = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (ytid)
          img = simg
          plot = h.unescape(sdesc)
          liz=xbmcgui.ListItem(name, '',None, img)
          liz.setInfo( 'Video', { "Title": name, "Plot": plot })
          liz.setProperty('fanart_image', addonfanart)
          liz.setProperty('IsPlayable', 'true')
          ilist.append((u, liz, False))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))



def getVideo(sid):
    html = getRequest('http://www.snagfilms.com/embed/player?filmId=%s' % uqp(sid))
    surl = re.compile('file: "(.+?)"', re.DOTALL).search(html).group(1)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=surl))
       


# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
      try:    parms[key] = urllib.unquote_plus(parms[key]).decode(UTF8)
      except: pass
except:
    parms = {}

p = parms.get

mode = p('mode',None)

if mode==  None:  getSources(p('fanart'))
elif mode=='GV':  getVideo(p('url'))
elif mode=='GM':  getMovies(p('url'))
elif mode=='GS':  getShows(p('url'))
elif mode=='GC':  getCats(p('url'))
elif mode=='GH':  getSearch(p('url'))
elif mode=='GT':  getMovieType(p('url'),p('name'))
elif mode=='GG':  getGenre(p('url'))



