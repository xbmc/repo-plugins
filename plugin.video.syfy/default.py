# -*- coding: utf-8 -*-
# Kodi Addon for Syfy !!!!!!!!!!!!!!!!!! still need to add subtitles !!!!!

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25
SYFYBASE = 'http://www.syfy.com%s'

addon         = xbmcaddon.Addon('plugin.video.syfy')
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

def getRequest(url):
              log("getRequest URL:"+str(url))
              headers = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'} 
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


def getSources(fanart):
              ilist=[]
              html = getRequest('http://www.syfy.com/episodes')
              cats = re.compile('<div class="show id.+?<h3>(.+?)<.+?header">(.+?)<.+?</div').findall(html)
              for name, vcnt in cats:
                  url = name
                  plot = '%ss' % vcnt
                  mode = 'GC'
                  u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                  liz=xbmcgui.ListItem(name, '',icon, icon)
                  liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                  liz.setProperty('fanart_image', addonfanart)
                  ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getCats(sname, catname):
              sname = uqp(sname)
              ilist=[]
              html = getRequest('http://www.syfy.com/episodes')
              blob = re.compile('syfy_show_microsite_show_list_form" />(.+?)<div class="view-footer">').search(html).group(1)
              blob += '<div class="show id'
              blob = re.compile('<div class="show id.+?<h3>'+sname+'</h3>(.+?)<div class="show id').search(blob).group(1)
              cats = re.compile('episode-info">.+?<span>(.+?)<.+?href="(.+?)".+?src="(.+?)".+?</div').findall(blob)
              for name, url, img in cats:
                 mode = 'GS'
                 url = SYFYBASE % url
                 html = getRequest(url)
                 purl = re.compile('data-src="(.+?)"').search(html).group(1)
                 purl = 'http:'+purl.replace('&amp;','&')
                 html = getRequest(purl)
                 purl = re.compile('<link rel="alternate" href="(.+?)"').findall(html)
                 purl = purl[1]+'&format=Script&height=576&width=1024'
                 html = getRequest(purl)
                 a = json.loads(html)
                 try:    plot = a["description"]
                 except: plot = a["abstract"]
                 url = purl
                 u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                 liz=xbmcgui.ListItem(name, '',icon, icon)
                 liz.setInfo( 'Video', { "Studio" : catname, "Title": name, "Plot": plot })
                 liz.setProperty('fanart_image', img)
                 liz.setProperty('IsPlayable', 'true')
                 ilist.append((u, liz, False))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
               

def getShow(url, show_name):
                 url = uqp(url)
                 url = url.replace(' ','%20')
                 html = getRequest(url)
                 a = json.loads(html)
                 try:
                    url = a["captions"][0]["src"]
                    url = url.split('/caption/',1)[1]
                    url = url.split('.',1)[0]
                    td = (datetime.datetime.utcnow()- datetime.datetime(1970,1,1))
                    unow = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)

                    u   = 'https://tvesyfy-vh.akamaihd.net/i/prod/video/%s_,25,40,18,12,7,4,2,00.mp4.csmil/master.m3u8?__b__=1000&hdnea=st=%s~exp=%s' % (url, str(unow), str(unow+60))
                    html = getRequest(u)
                    if html == '':
                       u   = 'https://tvesyfy-vh.akamaihd.net/i/prod/video/%s_,1696,1296,896,696,496,240,306,.mp4.csmil/master.m3u8?__b__=1000&hdnea=st=%s~exp=%s' % (url, str(unow), str(unow+60))

                 except:
                    url = a['mediaPid']
                    url = 'http://link.theplatform.com/s/HNK2IC/media/'+url+'?player=Syfy.com%20Player&policy=2713542&manifest=m3u&formats=flv,m3u,mpeg4&format=SMIL&embedded=true&tracking=true'
                    html = getRequest(url)
                    u  = re.compile('<video src="(.+?)"').search(html).group(1)

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
elif mode=='GC':  getCats(p('url'), p('name'))
elif mode=='GS':  getShow(p('url'), p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

