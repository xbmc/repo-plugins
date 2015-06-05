# -*- coding: utf-8 -*-
# Kodi Mediacorp (toggle.sg) Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()

UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.mediacorp')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

qp  = urllib.quote_plus
uqp = urllib.unquote_plus

home         = addon.getAddonInfo('path').decode(UTF8)
icon         = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart  = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))
nextIcon     = xbmc.translatePath(os.path.join(home, 'resources','media','next.png'))
pageSize     = int(addon.getSetting('page_size'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


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
                 page = response.read()
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    page = zlib.decompress(page, zlib.MAX_WBITS + 16)

              except urllib2.URLError, e:
                 if alert:
                     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 10000) )
                 page = ""
              return(page)


def getSources():
              xbmcplugin.setContent(int(sys.argv[1]), 'files')
              ilist=[]
              html = getRequest('http://video.toggle.sg/en/tvshows/mediacorpcollection')
              cu   = re.compile('<h5 class="collapsible__title">.+?href="(.+?)">(.+?)<',re.DOTALL).findall(html)
              html = getRequest('http://video.toggle.sg/en/catchup-listing')
              cats = re.compile('<h5 class="collapsible__title">.+?href="(.+?)">(.+?)<',re.DOTALL).findall(html)
              cats.extend(cu)
              for url, name in cats:
                  name = name.strip()
                  plot = name
                  mode = 'GS'
                  u = '%s?url=%s&name=%s&mode=%s&start=10' % (sys.argv[0],qp(url), qp(name), mode)
                  liz=xbmcgui.ListItem(name, '',icon, None)
                  liz.setProperty('fanart_image', addonfanart)
                  ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
              if addon.getSetting('enable_views') == 'true':
                 xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
              xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getShows(cat_url, startOff):
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
              startOff = int(startOff)
              ilist=[] 
              cat_url = uqp(cat_url)  
              html = getRequest(cat_url)
              blob = re.compile('bandData =(.+?)toggle.functions',re.DOTALL).search(html).group(1)
              blob = blob.replace('JSON.stringify({})',"''")
              blob = blob.strip()
              blob = blob.replace('}',',').replace('{','')
              kpairs = re.compile('(.+?)\:(.+?),').findall(blob)
              u = ''
              for kkey,kval in kpairs:
                 kkey=kkey.strip()
                 kval=kval.strip()
                 u = u+'&%s=%s' % (kkey,kval.replace('"','').replace("'",''))
                 u = re.sub(r'pageSize=[0-9]*', 'pageSize=100', u)
              url = 'http://video.toggle.sg/en/blueprint/servlet/toggle/bandlist?%s' % u
              html = getRequest(url)
              cats = re.compile('<div class="tg-teaser-item".+?href="(.+?)".+?src="(.+?)".+?<h6 class.+?href=.+?">(.+?)<.+?</div',re.DOTALL).findall(html)
              end = (startOff+pageSize)
              if end > len(cats): end = len(cats)
              for url, thumb, name in cats[startOff:end]:
                 if not (thumb.startswith('http')): thumb = 'http://video.toggle.sg'+thumb
                 if ('/movies/' in url) or ('/extras' in cat_url): mode = 'GV'
                 else: mode = 'GE'
                 name = name.strip()
                 plot = name
                 u = '%s?url=%s&mode=%s&start=0' % (sys.argv[0],qp(url), mode)
                 liz=xbmcgui.ListItem(name, '',None, thumb)
#                 liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                 liz.setProperty('fanart_image', thumb)
                 if ('/movies' in url) or ('/extras' in cat_url):
                    liz.setProperty('IsPlayable', 'true')
                    ilist.append((u, liz, False))
                 else:
                    ilist.append((u, liz, True))
              if end != len(cats):
                 liz=xbmcgui.ListItem(__language__(30012), '',nextIcon, None)
                 u = '%s?url=%s&mode=GS&start=%s' % (sys.argv[0],qp(cat_url), str(startOff+pageSize))
                 ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
              if addon.getSetting('enable_views') == 'true':
                 xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('shows_view'))
              xbmcplugin.endOfDirectory(int(sys.argv[1]))
   

def getEpis(epurl, startOff):
            xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
            xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
            xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
            startOff = int(startOff)
            ilist=[] 
            epurl = uqp(epurl)
            html = getRequest(epurl)
            epis = re.compile('<li class="fixed-height__item.+?href="(.+?)".+?data-src="(.+?)".+?href=.+?">(.+?)<.+?</div',re.DOTALL).findall(html)
            end = (startOff+pageSize)
            if end > len(epis): end = len(epis)
            for url, img, name in epis[startOff:end]:
                 vid = url.rsplit('/',1)[1]
                 vurl = 'http://toggleplayer-1410100339.ap-southeast-1.elb.amazonaws.com/v0.30/mwEmbed/mwEmbedFrame.php?&wid=_27017&uiconf_id=8413350&entry_id='+vid+'&flashvars[ks]=0&flashvars[logo]=undefined&flashvars[toggle.sgPlus]=false&flashvars[vast]=%7B%22htmlCompanions%22%3A%22video-companion-ad-320-100-in-flash%3A320%3A100%22%7D&flashvars[multiDrm]=%7B%22plugin%22%3Atrue%2C%22isClear%22%3Atrue%7D&flashvars[localizationCode]=en&flashvars[autoPlay]=true&flashvars[proxyData]=%7B%22initObj%22%3A%7B%22Locale%22%3A%7B%22LocaleLanguage%22%3A%22%22%2C%22LocaleCountry%22%3A%22%22%2C%22LocaleDevice%22%3A%22%22%2C%22LocaleUserState%22%3A0%7D%2C%22Platform%22%3A0%2C%22SiteGuid%22%3A0%2C%22DomainID%22%3A%220%22%2C%22UDID%22%3A%22%22%2C%22ApiUser%22%3A%22tvpapi_147%22%2C%22ApiPass%22%3A%2211111%22%7D%2C%22MediaID%22%3A%22'+vid+'%22%2C%22iMediaID%22%3A%22'+vid+'%22%2C%22picSize%22%3A%22640X360%22%7D&playerId=SilverlightContainer&forceMobileHTML5=true&urid=2.29.1.10&callback='
                 html = getRequest(vurl)
                 html = re.compile('kalturaIframePackageData = (.+?)};',re.DOTALL).search(html).group(1)
                 html = html+'}'
                 html = html.replace('\\','')
                 a = json.loads(html)
                 a = a['entryResult']['meta']
                 tags = {}
                 for b in a['partnerData']['Tags'] : tags[b['Key']] = b['Value']
                 metas = {}
                 for b in a['partnerData']['Metas']: metas[b['Key']] = b['Value']

                 thumb = a['thumbnailUrl']
                 name  = a['name']
                 infoList = {}
                 infoList['Date']  = a['startDate'].split('T',1)[0]
                 infoList['Aired'] = infoList['Date']
                 try: infoList['duration']    = int(a['duration'])
                 except: pass
                 try: 
                     infoList['MPAA'] = tags['Rating']
                     if tags['Rating'] == 'PG' : infoList['MPAA'] = 'TV-PG'
                 except: pass
                 try:    infoList['TVShowTitle'] = tags['Series name']
                 except: pass
                 try: 
                     infoList['Title'] = metas['Episode name']
                     name = infoList['Title']
                 except: infoList['Title']= name
                 try: infoList['Year'] = int(infoList['Aired'].split('-',1)[0])
                 except: pass

                 try: infoList['Studio'] = tags['Provider']
                 except: pass
                 try: infoList['Genre'] = tags['Genre']
                 except: pass
                 try:  
                     infoList['Season'] = int(metas['Season number'])
                     if infoList['Season'] == 0: infoList['Season'] = infoList['Year']
                 except: pass
                 try: infoList['Episode']     = int(metas['Episode number'])
                 except: pass
                 infoList['Plot'] = a['description']
                 a = a['partnerData']['Files']
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

                 url = u
                 u = '%s?url=%s&mode=GV' % (sys.argv[0], qp(url))
                 liz=xbmcgui.ListItem(name, '',None, thumb)
                 liz.setInfo( 'Video', infoList)
                 if addon.getSetting('vid_res') == '1': streams = {'codec':'h264', 'width':1280, 'height':720, 'aspect':1.78}
                 else: streams = {'codec':'h264', 'width':640, 'height':480, 'aspect':1.78}
                 liz.addStreamInfo('video', streams )
                 liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
                 liz.addStreamInfo('subtitle', { 'language' : 'en'})
                 liz.setProperty('fanart_image', thumb)
                 liz.setProperty('IsPlayable', 'true')
                 ilist.append((u, liz, False))
            if end != len(epis):
                 liz=xbmcgui.ListItem(__language__(30012), '',nextIcon, None)
                 u = '%s?url=%s&mode=GE&start=%s' % (sys.argv[0],qp(epurl), str(startOff+pageSize))
                 ilist.append((u, liz, True))
            xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
            if addon.getSetting('enable_views') == 'true':
               xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
            xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVid(vurl):
            u = uqp(vurl)
            if ( u == '' or u.endswith('.wvm')):
                 u=''
                 xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30011) , 10000) )
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = u))


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

if mode==  None:  getSources()
elif mode=='GS':  getShows(p('url'), p('start'))
elif mode=='GE':  getEpis(p('url'), p('start'))
elif mode=='GV':  getVid(p('url'))
