# -*- coding: utf-8 -*-
# WNBC Programs XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.wnbc')
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
    return name.replace('&apos;',"'").replace('&#8217;',"'").replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"').replace('&#039;',"'")

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

def getRequest(url, user_data=None, headers = defaultHeaders , alert=True, donotuseproxy=False):

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
        html = getRequest('http://www.nbc.com/ajax/dropdowns-global/America-New_York', donotuseproxy=True)
        a    = json.loads(html)['menu_html']
        a = a.encode('utf-8')
        a = re.compile('title">Current Episodes</div>(.+?)<div class="more-link">',re.DOTALL).search(a).group(1)
        b    = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(a)
        for url, name in b:
              name=cleanname(name)
              plot = ''
              lmode = 'GC'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],url, qp(name), lmode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              ilist.append((u, liz, True))

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))



def getCats(gcurl, catname):
        ilist=[]
        html = getRequest(('http://www.nbc.com%s' % gcurl), donotuseproxy=True)
        if 'the-tonight-show' in gcurl:
             startep = re.compile('<a href="/the-tonight-show/episodes/(.+?)"').search(html).group(1)
             for i in range(int(startep)-5,int(startep)):
                     url  = 'http://www.nbc.com/the-tonight-show/episodes/%s' % str(i)
                     pg = getRequest(url, donotuseproxy=True)
                     dataid = re.compile('data-video-id="(.+?)"').search(pg).group(1)
                     img    = re.compile('<img class="visuallyHidden" src="(.+?)"').search(pg).group(1)
                     name   = cleanname(re.compile('itemprop="title">(.+?)<').search(pg).group(1))
                     plot   = cleanname(re.compile('itemprop="description"><p>(.+?)<').search(pg).group(1))
                     url    = 'http://link.theplatform.com/s/NnzsPC/'+dataid+'?mbr=true&manifest=m3u&player=Onsite%20Player%20--%20No%20End%20Card&policy=43674'
                     lmode = 'GV'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(catname), lmode)
                     liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Studio": catname, "Plot": plot})
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))

        else:

              blob = re.compile('\(Drupal.settings,(.+?)\);').search(html).group(1)
              a  = json.loads(blob)
              cars = re.compile('<div class="nbc_mpx_carousel.+?id="(.+?)".+?"pane-title">(.+?)<.+?>(.+?)<').findall(html)
              for carid, name1, name2 in cars:

                     url = a['video_carousel'][carid]['feedUrl']
                     img = a['video_carousel'][carid]['defaultImages']['big']
                     name = cleanname((name1+name2).replace('<span class="strong">','').replace('</h2>',''))
                     plot = cleanname(catname)
                     lmode = 'GS'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(catname), lmode)
                     liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Studio": catname, "Plot": plot})
                     ilist.append((u, liz, True))

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

                 
              

def getShow(gsurl, catname):
              ilist=[]
              pg = getRequest(('http://www.nbc.com%s?range=1-29' % uqp(gsurl)), donotuseproxy=True)
              a  =  json.loads(pg)['entries']
              for e in a:

                     name = cleanname(e['title'].encode('utf-8'))
                     plot = cleanname(e['description'].encode('utf-8'))
                     url  = e['playerUrl']
                     img  = e['images']['medium']
                     lmode = 'GV'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), lmode)
                     liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Studio": catname, "Plot": plot})
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))

              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getVideo(surl):
            if surl.startswith('//') : surl = 'http:'+surl
            if not ('http://link.theplatform.com' in surl):
                html = getRequest(surl)
                surl = re.compile('<meta name="tp:EnableExternalController".+?href="(.+?)"').search(html).group(1)
                surl = surl.replace('&player=','&manifest=m3u&player=',1)

            try:
             html = getRequest(surl)
             finalurl  = re.compile('<video src="(.+?)"').search(html).group(1)
             if 'nbcvodenc-i.akamaihd.net' in finalurl:
               html = getRequest(finalurl, donotuseproxy=True)
               html += '#'
               choices = re.compile('BANDWIDTH=([0-9]*).+?http(.+?)#').findall(html)
               bw = 0
               for bwidth, link in choices:
                  if int(bwidth) > bw:
                     bw = int(bwidth)
                     finalurl = 'http'+link

             xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))

             try:
               suburl    = re.compile('<textstream src="(.+?)"').search(html).group(1)

               if (suburl != "") and ('.tt' in suburl) and (addon.getSetting('sub_enable') == "true"):
                 profile = addon.getAddonInfo('profile').decode(UTF8)
                 subfile = xbmc.translatePath(os.path.join(profile, 'NBCSubtitles.srt'))
                 prodir  = xbmc.translatePath(os.path.join(profile))
                 if not os.path.isdir(prodir):
                    os.makedirs(prodir)

                 pg = getRequest(suburl, donotuseproxy=True)
                 if pg != "":
                   ofile = open(subfile, 'w+')
                   captions = re.compile('<p begin="(.+?)" end="(.+?)">(.+?)</p>').findall(pg)
                   idx = 1
                   for cstart, cend, caption in captions:
                     cstart = cstart.replace('.',',')
                     cend   = cend.replace('.',',').split('"',1)[0]
                     caption = caption.replace('<br/>','\n').replace('&gt;','>').replace('&apos;',"'")
                     ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
                     idx += 1
                   ofile.close()
                   xbmc.sleep(5000)
                   if xbmc.Player().isPlaying():
                        xbmc.Player().setSubtitles(subfile)
             except:
                pass    

            except:
                xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__,__language__(30011), '10000') ) #added



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
elif mode=='GS':  getShow(p('url'),p('name'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GV':  getVideo(p('url'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

