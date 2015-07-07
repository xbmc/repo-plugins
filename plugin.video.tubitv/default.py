# -*- coding: utf-8 -*-
# TUBI TV Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
import zlib,json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.tubitv')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


qp  = urllib.quote_plus
uqp = urllib.unquote_plus

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, user_data=None, headers = defaultHeaders , alert=True):

              log("getRequest URL:"+str(url))
              if addon.getSetting('us_proxy_enable') == 'true':
                  us_proxy = 'http://%s:%s' % (addon.getSetting('us_proxy'), addon.getSetting('us_proxy_port'))
                  proxy_handler = urllib2.ProxyHandler({'http':us_proxy})
                  if addon.getSetting('us_proxy_pass') <> '' and addon.getSetting('us_proxy_user') <> '':
                      log('Using authenticated proxy: ' + us_proxy)
                      password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
                      password_mgr.add_password(None, us_proxy, addon.getSetting('us_proxy_user'), addon.getSetting('us_proxy_pass'))
                      proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
                      opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
                  else:
                      log('Using proxy: ' + us_proxy)
                      opener = urllib2.build_opener(proxy_handler)
              else:   
                  opener = urllib2.build_opener()
              urllib2.install_opener(opener)

              log("getRequest URL:"+str(url))
              req = urllib2.Request(url.encode(UTF8), user_data, headers)

              retries = 2
              while ( retries > 0):
                try:
                   response = urllib2.urlopen(req, timeout=30)
                   retries = 0
                except urllib2.URLError, e:
                   retries -= 1
                except socket.timeout:
                   retries -= 1
           
              try:
                 page = response.read()
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    page = zlib.decompress(page, zlib.MAX_WBITS + 16)

              except:
                 if alert:
                     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 5000) )
                 page = ""

              return(page)


def getSources(fanart):
        ilist = []
        html  = getRequest('http://tubitv.com')
        c     = re.compile('<li.+?class=".+?href="(.+?)">(.+?)<',re.DOTALL).findall(html)
        for url, name in c:
              mode = 'GS'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
                
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
          xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getQuery(cat_url):
        keyb = xbmc.Keyboard('', __addonname__)
        keyb.doModal()
        if (keyb.isConfirmed()):
              qurl = qp('/search/?q=%s' % (keyb.getText()))
              getCats(qurl, '')


def getShows(gsurl,catname):
        ilist = []
        gsurl = uqp(gsurl)
        html  = getRequest('http://tubitv.com%s' % gsurl)
        c     = re.compile("<A class='img_box' href='(.+?)'.+?src='(.+?)'.+?title'>(.+?)<.+?description'>(.+?)<.+?</A",re.DOTALL).findall(html)
        for url,img,name,plot in c:
          try: 
              season, epi = re.compile('S([0-9]*)\:E([0-9]*)').search(url).groups()
              mode ='GE'
              name = name+__language__(30019)
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
              continue
          except:
              pass

          mode = 'GL'
          u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
          liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
          liz.setInfo( 'Video', { "Title": name, "Plot": plot })
          liz.setProperty('fanart_image', addonfanart)
          liz.setProperty('IsPlayable', 'true')
          ilist.append((u, liz, False))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('movie_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getEpis(gsurl,catname):
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        gsurl = uqp(gsurl)
        catname = uqp(catname)
        html  = getRequest('http://tubitv.com%s' % gsurl)
        c     = re.compile("<A class='img_box' href='(.+?)'.+?src='(.+?)'.+?Title'>(.+?)<.+?</A", re.DOTALL).findall(html)
        for url,img,name in c:
          mode = 'GL'
          u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
          liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
          liz.setInfo( 'Video', { "Title": name, "TVShowTitle":catname })
          liz.setProperty('fanart_image', addonfanart)
          liz.setProperty('IsPlayable', 'true')
          ilist.append((u, liz, False))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getLink(url,vidname):
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)

        aheaders = { "Origin": "http://tubitv.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "tubitv.com",
            "Accept-Language":"en-US,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Cache-Control": "max-age=0",
            "Referer": "http://tubitv.com/",
            "Connection": "keep-alive"}

        username = addon.getSetting('login_name')
        password = addon.getSetting('login_pass')
        url1  = ('http://tubitv.com/login') # the login is extremely sensitive to headers and position so using urrlib2 calls
        xheaders = aheaders
        xheaders.update({"Content-Type": "application/x-www-form-urlencoded"})
        udata = 'username=%s&password=%s' % (urllib.quote(username),urllib.quote(password))
        req = urllib2.Request(url1, udata, xheaders)
        response = urllib2.urlopen(req)

        req = urllib2.Request('http://tubitv.com')
        response = urllib2.urlopen(req)

        url = ('http://tubitv.com%s' % (uqp(url).replace('./','/')))
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)

        try:
           if response.info().getheader('Content-Encoding') == 'gzip': # in case of gzip'd contents
              log("Content Encoding == gzip")
              buf = StringIO( response.read())
              f = gzip.GzipFile(fileobj=buf)
              html = f.read()
           else:
              html=response.read()
        except:
           html =''

        try:
            a = re.compile("<script>apu='(.+?)'",re.DOTALL).search(html).group(1)
        except:
            xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30018) , 5000) )
            return

        a = list(a)
        for x in range(len(a)):
             if ord(a[x]) >= ord('n'):
                a[x] = chr(ord(a[x])-(ord('n'))+(ord('a')))
             elif ord(a[x])>=ord('a'): 
                a[x] = chr(ord(a[x]) - ord('a')+ord('n'))
             x += 1
        a = ''.join(a)
        u = a[::-1] # this reverses the string

        try:
          vres = int(addon.getSetting('vid_res'))
          data = getRequest(u)
          urls = re.compile('BANDWIDTH=[0-9]*(.+?)#', re.DOTALL).findall(data)
          if vres !=0: vres = len(urls)-1
          u = '%s/%s' % (u.rsplit('/',1)[0], urls[vres].strip())
        except: pass

        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=u))

        try:
           suburl = re.compile("sbt=(.+?);", re.DOTALL).search(html).group(1)
           if suburl != "undefined":
              suburl = json.loads(suburl)
              suburl = suburl[0]["subtitle"]["url"]
        except:
           return

        if (suburl != "undefined") and ('.srt' in suburl) and (addon.getSetting('sub_enable') == "true"):
                 profile = addon.getAddonInfo('profile').decode(UTF8)
                 subfile = xbmc.translatePath(os.path.join(profile, 'subtitles.srt'))
                 prodir  = xbmc.translatePath(os.path.join(profile))
                 if not os.path.isdir(prodir):
                    os.makedirs(prodir)

                 captions = getRequest(suburl)
                 if captions != "":
                   ofile = open(subfile, 'w+')
                   ofile.write(captions)
                   ofile.close()
                   xbmc.sleep(5000)
                   xbmc.Player().setSubtitles(subfile)


# MAIN EVENT PROCESSING STARTS HERE

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
elif mode=='GQ':  getQuery(p('url'))
elif mode=='GS':  getShows(p('url'),p('name'))
elif mode=='GE':  getEpis(p('url'),p('name'))
elif mode=='GL':  getLink(p('url'),p('name'))

