# -*- coding: utf-8 -*-
# TVO Kids Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

import xml.etree.ElementTree as ET


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.tvokids')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

baseurl       = 'http://tvo.org/views/ajax?%s=%s&view_name=video_landing_page&view_display_id=%s&view_args=&view_path=node#2F120028'
taburl        = 'http://tvo.org/views/ajax?view_name=video_landing_page&view_display_id=%s&view_args='

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, headers = defaultHeaders):
#   log("getRequest URL:"+str(url))
   req = urllib2.Request(url.encode(UTF8), None, headers)
   try:
      response = urllib2.urlopen(req)
      page = response.read()
      if response.info().getheader('Content-Encoding') == 'gzip':
         log("Content Encoding == gzip")
         page = zlib.decompress(page, zlib.MAX_WBITS + 16)
   except:
      page = ""
   return(page)


def getSources():
        rlist = [('Ages 2 to 5','97'), ('Ages 11 and under','98')]
        ilist = []
        for name, url in rlist:
              u = '%s?url=%s&mode=GS' % (sys.argv[0],qp(url))
              liz=xbmcgui.ListItem(name, '',icon, None)
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))




def getShows(gsurl):
        ilist = []
        html = getRequest('http://www.tvokids.com/feeds/all/%s/shows' % uqp(gsurl))
        root = ET.fromstring(html)
        for b in root.findall('node'):
              url = b.find('node_id').text
              name = b.find('node_title').text
              plot = b.find('node_short_description').text.replace('<p>','').replace('</p>','')
              img  = b.find('node_thumbnail').text
              if img.endswith('.swf'): img = icon
              else:   img = 'http://www.tvokids.com/%s' % img
              u = '%s?url=%s&name=%s&mode=GE' % (sys.argv[0],qp(url), qp(name))
              liz=xbmcgui.ListItem(name, '',icon, img)
              liz.setInfo( 'Video', { "TVShowTitle": name, 'Title':name, "Plot": plot })
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))



           
def getEpis(geurl, showName):
        ilist = []
        showName = uqp(showName)
        html = getRequest('http://www.tvokids.com/feeds/%s/all/videos_list.xml?random=%s' % (geurl, str(int(time.time()))))
        root = ET.fromstring(html)
        for b in root.findall('node'):
              url = b.find('node_bc_id').text
              try:

                vurl = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=48543011001&playerKey=&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+url+'&secureConnections=true&secureHTMLConnections=true'
                html1 = getRequest(vurl)
                m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html1)
                a = json.loads(html1[m.start(1):m.end(1)+1])
                img    = a['data']['programmedContent']['videoPlayer']['mediaDTO']['videoStillURL']
                fanart = img
              except: continue
              name = b.find('node_title').text
              plot = b.find('node_short_description').text.replace('<p>','').replace('</p>','')
              infoList = {}
              infoList['Title'] = name
              infoList['TVShowTitle'] = showName
              infoList['Studio']      = 'TVO Kids'
              infoList['Episode'] = -1
              infoList['Season'] = 0
              infoList['Plot'] = plot
              u = '%s?url=%s&mode=GV' % (sys.argv[0],qp(url))
              liz=xbmcgui.ListItem(name, '',icon, img)
              liz.setInfo( 'Video', infoList)
              liz.addStreamInfo('video', { 'codec': 'h264', 
                                   'width' : 640, 
                                   'height' : 360, 
                                   'aspect' : 1.78 })
              liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
              liz.addStreamInfo('subtitle', { 'language' : 'en'})

              liz.setProperty('fanart_image', fanart)
              liz.setProperty('IsPlayable', 'true')
              ilist.append((u, liz, False))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

           

def getVideo(vid):
            url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=48543011001&playerKey=&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+vid+'&secureConnections=true&secureHTMLConnections=true'
            html = getRequest(url)
            m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
            a = json.loads(html[m.start(1):m.end(1)+1])
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
                    subfile = xbmc.translatePath(os.path.join(profile, 'Subtitles.srt'))
                    prodir  = xbmc.translatePath(os.path.join(profile))
                    if not os.path.isdir(prodir):
                       os.makedirs(prodir)

                    pg = getRequest(suburl)
                    if pg != "":
                      ofile = open(subfile, 'w+')
                      captions = re.compile('<p begin="(.+?)" end="(.+?)">(.+?)</p>',re.DOTALL).findall(pg)
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
elif mode=='GS':  getShows(p('url'))
elif mode=='GE':  getEpis(p('url'),p('name'))
elif mode=='GV':  getVideo(p('url'))


