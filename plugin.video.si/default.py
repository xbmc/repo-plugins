# -*- coding: utf-8 -*-
# Sports Illustrated

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs
import cgi, gzip
from StringIO import StringIO

import json


USER_AGENT = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_2 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8H7 Safari/6533.18.5'
GENRE_SPORTS  = "Sports"
UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.si')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
fanart        = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

qp  = urllib.quote_plus
uqp = urllib.unquote_plus


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge


def getRequest(url):
              log("getRequest URL:"+str(url))
              headers = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8', 'Cookie':'hide_ce=true'} 
              req = urllib2.Request(url.encode(UTF8), None, headers)

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


def getSources():
              ilist=[]
              html = getRequest('http://www.si.com/videos?json=1')
              a = json.loads(html)
              x = json.dumps(a)
              x = x.replace('\\"','"')
              cats = re.compile('<div class="radio-group">.+?<a(.+?)/a>').findall(x)
              mode = 'GS'
              for cat in cats:
               (url,name) = re.compile('href="(.+?)".+?>(.+?)<').search(cat).groups(1)
               if '/videos/' in url:
                url = url.replace('/videos/','')
                if url == 'more-sports':
                   break
                else:
                   u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                   liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
                   liz.setInfo( 'Video', { "Title": name, "Plot": name })
                   liz.setProperty('fanart_image', fanart)
                   ilist.append((u, liz, True))

              name = __language__(30003)
              url  = 'swimdaily'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": name })
              liz.setProperty('fanart_image', fanart)
              ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getShow(pcode,catname):
              ilist=[]
              Category_url = "http://api.brightcove.com/services/library?callback=&command=search_videos&any=primarycategory%3A"+pcode+"&page_size=100&video_fields=id%2CshortDescription%2CcreationDate%2CthumbnailURL%2Clength%2Cname&custom_fields=primarycategory%2Csubcategory&sort_by=PUBLISH_DATE%3ADESC&get_item_count=true&token=HYk6klcc_dX8GkFqbW1C2tZHLqgLDxGWBMlica9EroqvNv-skogPlw..&format=json"
              pg = getRequest(Category_url)
              a = json.loads(pg)
              for item in a['items']:
                     url   = str(item['id'])
                     name  = item['name']
                     plot  = item['shortDescription']
                     pdate  = item['creationDate']
                     img = item['thumbnailURL']
                     ts = int(int(str(int(pdate)))/1000)
                     try:
                       plot  = datetime.datetime.fromtimestamp(ts).strftime('%a %b %d, %Y %H:%M')+'\n'+plot
                     except:
                       plot = ''
                     try:
                       img = img.replace('\\','')
                     except:
                       pass

                     mode = 'GV'
                     name = name.encode(UTF8)
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                     liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Studio":catname, "Plot": plot })
                     liz.setProperty('fanart_image', fanart)
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))

              if len(ilist) != 0:
                 xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

def getVideo(video_content_id):
            url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=myExperience&bgcolor=%23FFFFFF&playerID=2157889318001&playerKey=AQ~~,AAAB9mw57HE~,xU4DCdZtHhuasNZF5WPK5LWKKRK4p1HG&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+video_content_id+'&secureConnections=true&secureHTMLConnections=true'
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

            except:
                 pass

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
if mode==  None:  getSources()
elif mode=='GC':  getCats(p('url'))
elif mode=='GS':  getShow(p('url'),p('name'))
elif mode=='GV':  getVideo(p('url'))


xbmcplugin.endOfDirectory(int(sys.argv[1]))

sys.modules.clear()
