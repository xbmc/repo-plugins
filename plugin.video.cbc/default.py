# -*- coding: utf-8 -*-
# Canadian Broadcasting Company Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.cbc')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

baseurl       = 'http://www.cbc.ca'
taburl        = 'http://www.cbc.ca%s'

qp  = urllib.quote_plus
uqp = urllib.unquote_plus

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


USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
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
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()

              except urllib2.URLError, e:
                 if alert:
                     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 10000) )
                 link1 = ""

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
        ilist = []
        html = getRequest('http://www.cbc.ca/player/')
        html = re.compile('<div id="catnav">(.+?)<div id="cliplist">').search(html).group(1)
        a = re.compile('<div class="menugroup"><ul><li .+?a href="(.+?)".+?>(.+?)<.+?</div').findall(html)
        b = re.compile('<div class="menugroup"><ul class.+?a href="(.+?)".+?>(.+?)<.+?</div').findall(html)
        a.extend(b)
        a.append(('/player/News/',__language__(30019)))
        a.append(('/player/Sports/',__language__(30020)))
        a.append(('/player/Digital+Archives/',__language__(30021)))

        for url,name in a:
              if name.startswith('</') : name = __language__(30015)
              name = cleanname(name)
              plot = name
              mode = 'GC'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getCats(gcurl):
        ilist = []
        url = taburl % (gcurl.replace(' ','+'))
        html = getRequest(url)
#        html = re.compile('<div id="catnav">.+?<ul>(.+?)</ul>').search(html).group(1)

        html = re.compile('<div id="catnav">(.+?)<div id=').search(html).group(1)
        a = re.compile('a href="(.+?)">(.+?)<').findall(html)
        for url,name in a:
              name = cleanname(name)
              plot = name
              mode = 'GT'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getTabs(gturl, gtname):
        ilist = []
        url = taburl % (gturl.replace(' ','+'))
        html = getRequest(url)
        html  = re.compile('<div id="catnav">(.+?)<div id=').search(html).group(1)
        if '<li class="active">' in html:
           getShows(gturl, gtname)
           return

        cats  = re.compile('<a href="(.+?)">(.+?)<').findall(html)
        for url,name in cats:
           try:
              name = cleanname(name)
              plot = name
              mode = 'GS'
              catname = gtname
              if gtname != name:  catname = catname+' - '+name
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(catname), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
           except:
              pass
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
           


def getQuery(cat_url):
        keyb = xbmc.Keyboard('', __addonname__)
        keyb.doModal()
        if (keyb.isConfirmed()):
              qurl = qp('/search/?q=%s' % (keyb.getText()))
              getCats(qurl, '')


def getShows(gsurl,catname):
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        url = taburl % (gsurl.replace(' ','+'))
        html = getRequest(url)
        try:
           html  = re.compile('<div class="clips">(.+?)<div class="spinner">').search(html).group(1)
        except:
           xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30011) , 5000) )
           return

        if 'class="desc">' in html:
          cats  = re.compile('><a href="(.+?)"><img src="(.+?)" alt="(.+?)".+?class="desc">(.+?)<').findall(html)
        else:
          cats  = re.compile('><a href="(.+?)"><img src="(.+?)" alt="(.+?)".+?class="title">(.+?)<').findall(html)

        for url,img,name,plot in cats:
           try:
              name = cleanname(name)
              plot = cleanname(plot)
              mode = 'GL'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
           except:
              pass
        if len(ilist) != 0:
          try:
              url = re.compile('<span class="totalpages">.+?</span><a href="(.+?)"').search(html).group(1)
              name = '%s%s%s' % ('[COLOR blue]', __language__(30018), '[/COLOR]')
              plot = __language__(30018)
              mode = 'GS'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
          except:
              pass
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        else:
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30011), 10000) )


def getLink(vid,vidname):
            vid = uqp(vid)
            vid = re.compile('/ID/([0-9]*)/').search(vid).group(1)
            url = 'http://feed.theplatform.com/f/h9dtGB/r3VD0FujBumK?form=json&fields=id%2Ctitle%2Cdescription%2CpubDate%2CdefaultThumbnailUrl%2Ckeywords%2Capproved%2C%3AadSite%2C%3AbackgroundImage%2C%3Ashow%2C%3ArelatedURL1%2C%3ArelatedURL2%2C%3ArelatedURL3%2C%3Asport%2C%3AseasonNumber%2C%3Atype%2C%3Asegment%2C%3Aevent%2C%3AadCategory%2C%3AliveOnDemand%2C%3AaudioVideo%2C%3AepisodeNumber%2C%3ArelatedClips%2C%3Agenre%2C%3AcommentsEnabled%2C%3AmetaDataURL%2C%3AisPLS%2C%3AradioLargeImage%2C%3AcontentArea%2C%3AsubEvent%2C%3AfeatureImage%2Cmedia%3Acontent%2Cmedia%3Akeywords&byContent=byReleases%3DbyId%253D'+vid+'&byApproved=true'
            html = getRequest(url)
            a = json.loads(html)
            u = a["entries"][0]["media$content"][0]["plfile$downloadUrl"]
            if u=='':
              u = a["entries"][0]["media$content"][0]["plfile$releases"][0]["plrelease$url"]
              u += '?mbr=true&manifest=m3u'
              html = getRequest(u)
              u = re.compile('<video src="(.+?)"').search(html).group(1)

            if u.endswith('.mp4'): 
               if '640x360_900kbps' in u:    u=u.replace('640x360_900kbps','960x540_2500kbps')
               elif '640x360_1200kbps' in u: u=u.replace('640x360_1200kbps','960x540_2500kbps')
               elif '852x480_1800kbps' in u: u=u.replace('852x480_1800kbps','960x540_2500kbps')
               else:
                  if u.endswith('kbps.mp4'): 
                    cbr = re.compile('_([0-9]*)kbps\.mp4').search(u).group(1)
                    u = u.replace('_%skbps' % cbr, '_2500kbps')
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=u))

            if (addon.getSetting('sub_enable') == "false"):
               xbmc.sleep(5000)
#               xbmc.Player().disableSubtitles()
               xbmc.Player().showSubtitles(False)


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
elif mode=='GQ':  getQuery(p('url'))
elif mode=='GC':  getCats(p('url'))
elif mode=='GS':  getShows(p('url'),p('name'))
elif mode=='GT':  getTabs(p('url'),p('name'))
elif mode=='GL':  getLink(p('url'),p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

