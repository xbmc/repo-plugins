# -*- coding: utf-8 -*-
# TV Ontario Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.tvo')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

baseurl       = 'http://tvo.org/views/ajax?%s=%s&view_name=video_landing_page&view_display_id=%s&view_args=&view_path=node#2F120028'
taburl        = 'http://tvo.org/views/ajax?view_name=video_landing_page&view_display_id=%s&view_args='

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
        html = getRequest('http://tvo.org/video')
        html = re.compile('Drupal.settings, (.+?)\);').search(html).group(1)
        a = json.loads(html)['quicktabs']['qt_3']['tabs']
        for b in a:
              url = b['display']
              name = b['title']
              plot = ''
              mode = 'GT'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
           



def getTabs(gturl):
        ilist = []
        vdi = gturl
        url = taburl % (gturl)
        html = getRequest(url)
        html = html.replace('\\"',"'").replace('\\x3c','<').replace('\\x3e','>').replace('\\n','').replace('\\x26','&').replace('\\r','').replace("\\'",'').replace(chr(9),'')
        html = json.loads(html)['display']
        cats  = re.compile("<div class='form-item'.+?name='(.+?)'.+?value='(.+?)'.+?<label.+?>(.+?)<").findall(html)
        for cat,url,name in cats[1:]:
           try:
              url = '%s|%s|%s' % (cat,url,vdi)
              plot = ''
              mode = 'GS'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
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
        ilist = []
        cat,id,vdi = gsurl.split('|')
        url = baseurl % (cat, id, vdi)
        url = url.replace('#','%')
        html  = getRequest(url)
        html = html.replace('\\"',"'").replace('\\x3c','<').replace('\\x3e','>').replace('\\n','').replace('\\x26','&').replace('\\r','').replace("\\'",'').replace(chr(9),'')
        html = json.loads(html)['display']
        cats  = re.compile("td class=.+?tvo.org/bcid/([0-9]*).+?src='(.+?)'.+?h5>(.+?)</h5.+?description-value.+?field-content'>(.+?)<.+?</td",re.DOTALL).findall(html)
        for url,img,name,plot in cats:
           try:
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
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        else:
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30011), 10000) )


def getLink(vid,vidname):
            url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=1280&height=720&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=756015080001&playerKey=AQ~~,AAAABDk7A3E~,xYAUE9lVY9-LlLNVmcdybcRZ8v_nIl00&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+vid+'&secureConnections=true&secureHTMLConnections=true'
            html = getRequest(url)
            a = re.compile('experienceJSON = (.+?)\};').search(html).group(1)
            a = a+'}'
            a = json.loads(a)
            try:
                 b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['IOSRenditions']
                 u =''
                 rate = 0
                 for c in b:
                    if c['encodingRate'] > rate:
                       rate = c['encodingRate']
                       u = c['defaultURL']
                 b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['renditions']
                 for c in b:
                    if c['encodingRate'] > rate:
                       rate = c['encodingRate']
                       u = c['defaultURL']
                 if rate == 0:
                     try:
                        u = a['data']['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']
                     except:
                        u = ''
                 xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=u))

                 try:
                     suburl = a['data']['programmedContent']['videoPlayer']['mediaDTO']['captions'][0]['URL']
                 except:
                     suburl = ''

                 if (suburl != "") and ('dfxp' in suburl) and (addon.getSetting('sub_enable') == "true"):
                    profile = addon.getAddonInfo('profile').decode(UTF8)
                    subfile = xbmc.translatePath(os.path.join(profile, 'TVOSubtitles.srt'))
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
                      xbmc.sleep(5000)
                      xbmc.Player().setSubtitles(subfile)

            except:
                 xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30011), 10000) )


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
elif mode=='GQ':  getQuery(p('url'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GS':  getShows(p('url'),p('name'))
elif mode=='GT':  getTabs(p('url'))
elif mode=='GL':  getLink(p('url'),p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

