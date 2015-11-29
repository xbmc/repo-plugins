# -*- coding: utf-8 -*-
# Canadian Broadcasting Company Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()


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

def getRequest(url, user_data=None, headers = defaultHeaders , alert=True, donotuseProxy=True):

    log("getRequest URL:"+str(url))
    if (donotuseProxy!=True) and (addon.getSetting('us_proxy_enable') == 'true'):
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

    try:
       response = urllib2.urlopen(req, timeout=120)
       page = response.read()
       if response.info().getheader('Content-Encoding') == 'gzip':
           log("Content Encoding == gzip")
           page = zlib.decompress(page, zlib.MAX_WBITS + 16)

    except urllib2.URLError, e:
       if alert:
           xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 5000) )
       page = ""
    return(page)


def getSources(fanart):
        xbmcplugin.setContent(int(sys.argv[1]), 'files')

        ilist = []
        html = getRequest('http://www.cbc.ca/player/tv')
        html = re.compile('<section class="section-cats full">(.+?)</section>', re.DOTALL).search(html).group(1)
        a = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(html)
#        b = re.compile('<div class="menugroup"><ul class.+?a href="(.+?)".+?>(.+?)<.+?</a>').findall(html)
#        a.extend(b)
        a.append(('http://www.cbc.ca/player/news',__language__(30019)))
        a.append(('http://www.cbc.ca/player/Sports',__language__(30020)))
#        a.append(('http://www.cbc.ca/player/Digital+Archives',__language__(30021)))

        for url,name in a:
              if name.startswith('</') : name = __language__(30015)
              name = cleanname(name)
              plot = name
              mode = 'GC'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
#              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getCats(gcurl, gcname):
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        ilist = []
#        url = taburl % (gcurl.replace(' ','+'))
        url = gcurl.replace(' ','%20')

        html = getRequest(url)
#        html = re.compile('<div id="catnav">.+?<ul>(.+?)</ul>', re.DOTALL).search(html).group(1)

        try:    
                html = re.compile('<section class="category-subs full">(.+?)</section', re.DOTALL).search(html).group(1)
                a = re.compile('a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
                mode = 'GT'
        except:
           try:
                html = re.compile('<section class="category-content full">(.+?)</section', re.DOTALL).search(html).group(1)
                getTabs(gcurl, gcname)
                return
#                a = re.compile('a href="(.+?)" .+?="(.+?)"', re.DOTALL).findall(html)
#                mode = 'GL'
           except:
                html = re.compile('<section class="section-cats full">(.+?)</section', re.DOTALL).search(html).group(1)
                a = re.compile('a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
                mode = 'GT'


        for url,name in a:
              name = cleanname(name)
              plot = name
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              if mode != 'GL': ilist.append((u, liz, True))
              else:
                 liz.setProperty('IsPlayable', 'true')
                 ilist.append((u, liz, False))
                   
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getTabs(gturl, gtname):
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        url = gturl.replace(' ','%20')
        html = getRequest(url)
        html  = re.compile('<section class="category-content full">(.+?)</section', re.DOTALL).search(html).group(1)
        if '<li class="active">' in html:
           getShows(gturl, gtname)
           return

        cats  = re.compile('<a href="(.+?)" aria-label="(.+?)".+?src="(.+?)"(.+?)</a', re.DOTALL).findall(html)
        for url,name,img, md in cats:
           try:
              infoList={}
              name = cleanname(name)
              try:
                 html = getRequest(url, alert=False)
                 try:
                     plot = re.compile('<meta name="description" content="(.+?)"', re.DOTALL).search(html).group(1)
                 except:
                     plot = name
              except: plot=name
              mode = 'GL'
              catname = gtname
              if gtname != name:  catname = catname+' - '+name
              infoList['TVShowTitle'] = catname
              infoList['Title'] = name
              infoList['Plot'] = h.unescape(plot.decode('utf-8'))
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(catname), mode)
              liz=xbmcgui.ListItem(name, '',None, img)
              liz.setInfo( 'Video', infoList)
              liz.setProperty('fanart_image', img)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
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
        url = gsurl.replace(' ','%20')
        html = getRequest(url)
        try:
           html  = re.compile('<div class="clips">(.+?)<div class="spinner">', re.DOTALL).search(html).group(1)
        except:
           xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30011) , 5000) )
           return

        if 'class="desc">' in html:
          cats  = re.compile('><a href="(.+?)"><img src="(.+?)" alt="(.+?)".+?class="desc">(.+?)<', re.DOTALL).findall(html)
        else:
          cats  = re.compile('><a href="(.+?)"><img src="(.+?)" alt="(.+?)".+?class="title">(.+?)<', re.DOTALL).findall(html)

        for url,img,name,plot in cats:
           try:
              name = cleanname(name)
              plot = cleanname(plot)
              mode = 'GL'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { 'TVShowTitle': catname, "Title": name, "Studio":catname, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
           except:
              pass
        if len(ilist) != 0:
          try:
              url = re.compile('<span class="totalpages">.+?</span><a href="(.+?)"', re.DOTALL).search(html).group(1)
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
            vid = vid.rsplit('/',1)[1]
            html = getRequest('http://tpfeed.cbc.ca/f/ExhSPC/vms_5akSXx4Ng_Zn?q=*&byGuid=%s' % vid)
            a = json.loads(html)
            a = a['entries'][0]['content']
            u = ''
            vwid = 0
            for b in a:
               if b['width'] >= vwid:
                  u = b['url']
                  vwid = b['width']

            u = u.split('/meta.smil',1)[0]+'?mbr=true&manifest=m3u'
            html = getRequest(u, donotuseProxy=False)
            u = re.compile('<video src="(.+?)"', re.DOTALL).search(html).group(1)
            html = getRequest(u, donotuseProxy=False)
            try:
                urls = re.compile('BANDWIDTH=(.+?),.+?mp4a.40.2"(.+?)\n', re.DOTALL).findall(html)
                x = 0
                for (bw, v) in urls:
                   if int(bw)> x:
                     x = int(bw)
                     yy = v
       
                u = yy.strip()  
            except:
                u = re.compile('mp4a.40.2"(.+?)#', re.DOTALL).search(html).group(1)
            u = u.strip()
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=u))

#            if (addon.getSetting('sub_enable') == "false"):
#               xbmc.sleep(5000)
#               xbmc.Player().disableSubtitles()
#               xbmc.Player().showSubtitles(False)


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
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GS':  getShows(p('url'),p('name'))
elif mode=='GT':  getTabs(p('url'),p('name'))
elif mode=='GL':  getLink(p('url'),p('name'))

if mode!= 'GL': xbmcplugin.endOfDirectory(int(sys.argv[1]))

