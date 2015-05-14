# -*- coding: utf-8 -*-
# Kodi Mediacorp (toggle.sg) Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.mediacorp')
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

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge

def deuni(a):
    a = a.replace('&amp;#039;',"'")
    a = a.replace('&amp','&')
    a = a.replace('&#039;',"'")
    return a



USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, user_data=None, headers = defaultHeaders , alert=True, donotuseproxy=True):

              log("getRequest URL:"+str(url))
              if (donotuseproxy==False) and (addon.getSetting('us_proxy_enable') == 'true'):
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
                 response = urllib2.urlopen(req)
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
              ilist=[]
              html = getRequest('http://video.toggle.sg/en/tvshows/mediacorpcollection')
              cu   = re.compile('<h5 class="collapsible__title">.+?href="(.+?)">(.+?)<').findall(html)
              html = getRequest('http://video.toggle.sg/en/catchup-listing')
              cats = re.compile('<h5 class="collapsible__title">.+?href="(.+?)">(.+?)<').findall(html)
              cats.extend(cu)
              for url, name in cats:
                  name = name.strip()
                  plot = name
                  mode = 'GS'
                  u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                  liz=xbmcgui.ListItem(name, '',icon, icon)
                  liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                  liz.setProperty('fanart_image', addonfanart)
                  ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getShows(cat_url):
              ilist=[] 
              cat_url = uqp(cat_url)       
              html = getRequest(cat_url)
              cats = re.compile('<div class="tg-teaser-item">.+?href="(.+?)".+?src="(.+?)".+?<h6 class.+?href=.+?">(.+?)<.+?</div').findall(html)
              for url, img, name in cats:
                 if '/movies/' in url: mode = 'GV'
                 else: mode = 'GE'
                 name = name.strip()
                 plot = name
                 u = '%s?url=%s&mode=%s&name=%s' % (sys.argv[0],qp(url), mode, qp(name))
                 liz=xbmcgui.ListItem(name, '',img, img)
                 liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                 liz.setProperty('fanart_image', addonfanart)
                 if '/movies' in url:
                    liz.setProperty('IsPlayable', 'true')
                    ilist.append((u, liz, False))
                 else:
                    ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
                 

def getEpis(epurl, showname):
            xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
            ilist=[] 
            epurl = uqp(epurl)
            html = getRequest(epurl)
            epis = re.compile('<li class="fixed-height__item.+?href="(.+?)".+?data-src="(.+?)".+?href=.+?">(.+?)<.+?</div').findall(html)
            for url, img, name in epis:
                 if not (img.startswith('http')): img = 'http://video.toggle.sg'+img
                 mode = 'GV'
                 name = name.strip()
                 plot = name
                 u = '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), mode)
                 liz=xbmcgui.ListItem(name, '',img, img)
                 liz.setInfo( 'Video', { "Title": name, "Studio":showname, "Plot": showname })
                 liz.setProperty('fanart_image', addonfanart)
                 liz.setProperty('IsPlayable', 'true')
                 ilist.append((u, liz, False))
            xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))



def getVid(vurl):
            vurl = uqp(vurl)
            vid = vurl.rsplit('/',1)[1]
            url = 'http://toggleplayer-1410100339.ap-southeast-1.elb.amazonaws.com/v0.30/mwEmbed/mwEmbedFrame.php?&wid=_27017&uiconf_id=8413350&entry_id='+vid+'&flashvars[ks]=0&flashvars[logo]=undefined&flashvars[toggle.sgPlus]=false&flashvars[vast]=%7B%22htmlCompanions%22%3A%22video-companion-ad-320-100-in-flash%3A320%3A100%22%7D&flashvars[multiDrm]=%7B%22plugin%22%3Atrue%2C%22isClear%22%3Atrue%7D&flashvars[localizationCode]=en&flashvars[autoPlay]=true&flashvars[proxyData]=%7B%22initObj%22%3A%7B%22Locale%22%3A%7B%22LocaleLanguage%22%3A%22%22%2C%22LocaleCountry%22%3A%22%22%2C%22LocaleDevice%22%3A%22%22%2C%22LocaleUserState%22%3A0%7D%2C%22Platform%22%3A0%2C%22SiteGuid%22%3A0%2C%22DomainID%22%3A%220%22%2C%22UDID%22%3A%22%22%2C%22ApiUser%22%3A%22tvpapi_147%22%2C%22ApiPass%22%3A%2211111%22%7D%2C%22MediaID%22%3A%22'+vid+'%22%2C%22iMediaID%22%3A%22'+vid+'%22%2C%22picSize%22%3A%22640X360%22%7D&playerId=SilverlightContainer&forceMobileHTML5=true&urid=2.29.1.10&callback='
            html = getRequest(url)
            html = re.compile('kalturaIframePackageData = (.+?)};').search(html).group(1)
            html = html+'}'
            html = html.replace('\\','')
            a = json.loads(html)
            a = a['entryResult']['meta']['partnerData']['Files']
            u =''
            if addon.getSetting('vid_res') == '1':
              for b in a:
                vtype = 'STB Main'
                if b['Format'] == vtype:
                  u = b['URL']
                  break
              req = urllib2.Request(u, None, defaultHeaders)
              try:
                response = urllib2.urlopen(req, timeout=40)
              except:
                u = ''
            if u == '':
                for b in a:
                  vtype = 'Android'
                  if b['Format'] == vtype:
                    u = b['URL']
                    break
            if ( u == '' or u.endswith('.wvm')):
                 u=''
                 xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30001) , 10000) )

            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = u))


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
elif mode=='GS':  getShows(p('url'))
elif mode=='GE':  getEpis(p('url'), p('name'))
elif mode=='GV':  getVid(p('url'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

