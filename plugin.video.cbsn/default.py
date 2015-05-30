# -*- coding: utf-8 -*-
# CBSN News Live Video Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.cbsn')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_2 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8H7 Safari/6533.18.5'
defaultHeaders = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, headers = defaultHeaders):
   log("getRequest URL:"+str(url))
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


def getEpisodes():
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   ilist=[]
   bselect = int(addon.getSetting('bselect'))
   bwidth = ['120','360','700','1200','1800','2200','4000']
   bw = 'index_%s' % (bwidth[bselect])
   c = [{'type':'dvr',
        'url' :'http://cbsnewshd-lh.akamaihd.net/i/CBSN_2@199302/%s_av-b.m3u8?sd=10&rebase=on' % bw,
        'startDate' : str(datetime.date.today()),
        'segmentDur'  : '59:59',
        'headline'  : 'LIVE',
        'headlineshort' : 'LIVE',
        'thumbnail_url_hd' : icon.replace('\\','/')}]

   html = getRequest('http://cbsn.cbsnews.com/rundown/?device=desktop')
   a = json.loads(html)
   a = a["navigation"]["data"]
   c.extend(a)
   mode = 'GV'
   for b in c:
    if b['type'] == 'dvr':
      url = b["url"].replace('index_700',bw)
      url = url.encode(UTF8)
      infoList = {}
      infoList['Date']        = b['startDate'].split(' ',1)[0]
      infoList['Aired']       = infoList['Date']
      dur = b['segmentDur'].split(':')
      infoList['Duration']    = str(int(dur[0])*60+int(dur[1]))
      infoList['MPAA']        = ''
      infoList['TVShowTitle'] = 'CBSN News Live'
      infoList['Title']       = b['headlineshort']
      infoList['Studio']      = 'CBSN'
      infoList['Genre']       = 'News'
      infoList['Season']      = None
      infoList['Episode']     = -1
      infoList['Year']        = int(infoList['Aired'].split('-',1)[0])
      infoList['Plot']        = '%s UTC\n%s' % (b['startDate'], b['headline'])
      thumb = b['thumbnail_url_hd'].replace('\\','')
      name  = b['headlineshort']
      u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
      liz=xbmcgui.ListItem(name, '',None, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'h264', 
                                   'width' : 1920, 
                                   'height' : 1080, 
                                   'aspect' : 1.78 })
      liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
      liz.addStreamInfo('subtitle', { 'language' : 'en'})
      liz.setProperty('fanart_image', addonfanart)
      liz.setProperty('IsPlayable', 'true')
      ilist.append((u, liz, False))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=False)


def getVideo(url, show_name):
    u = uqp(url)
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

if mode==  None:  getEpisodes()
elif mode=='GV':  getVideo(p('url'), p('name'))
