# -*- coding: utf-8 -*-
# WRAL News and Weather XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.wral')
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

def cleanname(name):    
    return name.replace('&apos;',"'").replace('&#8217;',"'").replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"')

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge


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

              try:
                 response = urllib2.urlopen(req)
              except urllib2.HTTPError, e:
                 if e.code == 404:
                    response = e
                 else:
                    link1 = ""

              if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
              else:
                    link1=response.read()
             

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
        ilist=[]
        html = getRequest('http://www.wral.com/weather/video/1076424/')
        b    = re.compile('<button data-switch-btn=.+?>(.+?)<').findall(html)
        i = 0
        for a in b:
              i += 1
              url = str(i)
              name = a
              plot = ''
              lmode = 'GC'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), lmode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              ilist.append((u, liz, True))

        name = 'Watch CBS Shows'
        u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp('dummy'),
                                           qp(name), 'GB')
        liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', icon)
        ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))



def getCats(gcurl, catname):
              ilist=[]
              html = getRequest('http://www.wral.com/weather/video/1076424/')
              blob = re.compile('define\(.+?return (.+?)\};').search(html).group(1)
              blob = blob+'}'
              a  = json.loads(blob)
              a = a['multimedia']['standalone']['shelf_assets']
              i = 0
              for b in a:
                 i += 1
                 if i == int(gcurl):
                   for hl in b:
                     name = cleanname(hl['headline'])
                     plot = cleanname(hl['abstract'])
                     url  = hl['configURL']
                     img  = hl['image_100x75']
                     lmode = 'GS'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), lmode)
                     liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Studio": catname, "Plot": plot})
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))

              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

                 
              

def getShow(gsurl):
              pg = getRequest(uqp(gsurl))
              a  =  json.loads(pg)['playlist'][0]
              url = a['netConnectionUrl']+a['url'].replace('mp4:','/')
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))

def getCBSShows(gsurl):
              ilist=[]
              pg = getRequest('http://can.cbs.com/thunder/player/iframe/index.php')
              shows = re.compile('<a href="(.+?)".+?>(.+?)<').findall(pg)
              lmode = 'GL'
              for url, name in shows:
                 u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), lmode)
                 liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
                 liz.setInfo( 'Video', { "Title": name })
                 ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

def getCBSVideos(gsurl, catname):
              ilist=[]
              gsurl = uqp(gsurl).replace(' ','%20')
              pg = getRequest(gsurl)
              vids = re.compile('img src="(.+?)".+?pid=(.+?)&.+?title="(.+?)".+?</h4>.+?>(.+?)<').findall(pg)
              for img, url, name, desc in vids:
                     name = cleanname(name)
                     plot = cleanname(desc)
                     lmode = 'GV'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), lmode)
                     liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Studio": catname, "Plot": plot})
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))

              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

def getVideo(foundpid):
              pg = getRequest('http://link.theplatform.com/s/dJ5BDC/%s?format=SMIL&mbr=true' % foundpid)
              try:
                 suburl = re.compile('"ClosedCaptionURL" value="(.+?)"').search(pg).group(1)
              except:
                 suburl = ""

              frtmp,fplay = re.compile('<meta base="(.+?)".+?<video src="(.+?)"').search(pg).groups()
              swfurl='http://canstatic.cbs.com/chrome/canplayer.swf swfvfy=true'
              if '.mp4' in fplay:
                pphdr = 'mp4:'
                frtmp = frtmp.replace('&amp;','&')
                fplay = fplay.replace('&amp;','&')
              else:
                pphdr = ''
                xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__,__language__(30011) , '10000') ) #added
                frtmp = frtmp.replace('rtmp:','rtmpe:')
                frtmp = frtmp.replace('.net','.net:1935')
                frtmp = frtmp.replace('?auth=','?ovpfv=2.1.9-internal&?auth=')
                swfurl = 'http://vidtech.cbsinteractive.com/player/3_3_2/CBSI_PLAYER_HD.swf swfvfy=true pageUrl=http://www.cbs.com/shows'
              finalurl = '%s playpath=%s%s swfurl=%s timeout=20' % (frtmp, pphdr, fplay, swfurl)
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))

              if (suburl != "") and ('xml' in suburl) and (addon.getSetting('sub_enable') == "true"):
                 profile = addon.getAddonInfo('profile').decode(UTF8)
                 subfile = xbmc.translatePath(os.path.join(profile, 'CBSSubtitles.srt'))
                 prodir  = xbmc.translatePath(os.path.join(profile))
                 if not os.path.isdir(prodir):
                    os.makedirs(prodir)

                 pg = getRequest(suburl)
                 if pg != "":
                   ofile = open(subfile, 'w+')
                   captions = re.compile('<p begin="(.+?)" end="(.+?)">(.+?)</p>').findall(pg)
                   idx = 1
                   for cstart, cend, caption in captions:
                     cstart = cstart.replace('.',',')
                     cend   = cend.replace('.',',').split('"',1)[0]
                     caption = caption.replace('<br/>','\n').replace('&gt;','>').replace('&apos;',"'").replace('&quot;','"')
                     ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
                     idx += 1
                   ofile.close()
                   xbmc.sleep(2000)
                   xbmc.Player().setSubtitles(subfile)
                


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
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='GS':  getShow(p('url'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GB':  getCBSShows(p('url'))
elif mode=='GL':  getCBSVideos(p('url'),p('name'))
elif mode=='GV':  getVideo(p('url'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

