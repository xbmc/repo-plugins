# -*- coding: utf-8 -*-
# Bravo TV XBMC Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'
BRAVOBASE = 'http://www.bravotv.com%s'

addon         = xbmcaddon.Addon('plugin.video.bravo')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
#USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
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

def getShows():
   xbmcplugin.setContent(int(sys.argv[1]), 'files')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
   ilist=[]
   basehtml = getRequest('http://www.bravotv.com/full-episodes')
   cats = re.compile('<div class="views-row">.+?href="(.+?)".+?title="(.+?)".+?src="(.+?)".+?data-src="(.+?)".+?</article',re.DOTALL).findall(basehtml)
   for url, name,img, fanart in cats:
       name = name.strip()
       surl = BRAVOBASE % (url)
       img  = fanart
       epiHTML = getRequest(surl)
       epis = re.compile('<li class="watch__episode.+?href="(.+?)".+?</ul>',re.DOTALL).findall(epiHTML)
       vcnt = len(epis)
       if epis[len(epis)-1][0] != '/' : epis[len(epis)-1] = '/'+epis[len(epis)-1]
       url  = BRAVOBASE % epis[len(epis)-1]
       html = getRequest(url)
       try:
         purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html).group(1)
       except:
         continue
       purl = 'http://link.theplatform.com/s'+(purl.replace('/bravo_vod_p3/embed/select','').split('.com/p')[1]).split('?',1)[0]+'?mbr=true&player=Bravo%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
       html = getRequest(purl)
       a = json.loads(html)
       infoList = {}
       infoList['Date']        = datetime.datetime.fromtimestamp(a['pubDate']/1000).strftime('%Y-%m-%d')
       infoList['Aired']       = infoList['Date']
       infoList['MPAA']        = a['ratings'][0]['rating']
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = a['provider']
       infoList['Genre']       = (a['nbcu$advertisingGenre']).replace('and','/')
       infoList['Episode']     = vcnt
       infoList['Year']        = int(infoList['Aired'].split('-',1)[0])
       infoList['Plot'] = re.compile('"og:description" content="(.+?)"',re.DOTALL).search(epiHTML).group(1)
       infoList['Plot'] = h.unescape(infoList['Plot'].decode('utf-8'))
       url = surl
       mode = 'GE'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
       liz=xbmcgui.ListItem(name, '',None, img)
       liz.setInfo( 'Video', infoList)
       liz.setProperty('fanart_image', fanart)
       ilist.append((u, liz, True))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getEpisodes(eurl, showName):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
   ilist=[]        
   epiHTML = getRequest(eurl)
   (tvshow,  fanart) = re.compile('og:title" content="(.+?)".+?"og:image" content="(.+?)"',re.DOTALL).search(epiHTML).groups()
   epis = re.compile('<li class="watch__episode.+?href="(.+?)".+?</ul>',re.DOTALL).findall(epiHTML)
   for url in epis:
      url  = BRAVOBASE % url
      html = getRequest(url)
      purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html).group(1)
      purl = 'http://link.theplatform.com/s'+(purl.replace('/bravo_vod_p3/embed/select','').split('.com/p')[1]).split('?',1)[0]+'?mbr=true&player=Bravo%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
      html = getRequest(purl)
      a = json.loads(html)
      infoList = {}
      infoList['Date']        = datetime.datetime.fromtimestamp(a['pubDate']/1000).strftime('%Y-%m-%d')
      infoList['Aired']       = infoList['Date']
      infoList['MPAA']        = a['ratings'][0]['rating']
      infoList['Studio']      = a['provider']
      infoList['Genre']       = (a['nbcu$advertisingGenre']).replace('and','/')
      infoList['Episode']     = int(a['pl1$episodeNumber'])
      infoList['Season']      = int(a['pl1$seasonNumber'])
      infoList['Year']        = int(infoList['Aired'].split('-',1)[0])
      infoList['Plot'] = h.unescape(a['description'])
      infoList['TVShowTitle'] = tvshow
      infoList['Title']       = a['title']
      name = a['title']
      thumb = a['defaultThumbnailUrl']
      url = purl.split('?',1)[0]
      u = '%s?url=%s&name=%s&mode=GV' % (sys.argv[0],qp(url), qp(name))
      liz=xbmcgui.ListItem(name, '',None, thumb)
      liz.setInfo( 'Video', infoList)
      liz.addStreamInfo('video', { 'codec': 'h264', 
                                   'width' : 1920, 
                                   'height' : 1080, 
                                   'aspect' : 1.78 })
      liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en'})
      liz.addStreamInfo('subtitle', { 'language' : 'en'})
      liz.setProperty('fanart_image', fanart)
      liz.setProperty('IsPlayable', 'true')
      ilist.append((u, liz, False))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(url, show_name):
    gvu1 = 'https://tvebravo-vh.akamaihd.net/i/prod/video/%s_,40,25,18,12,7,4,2,00.mp4.csmil/master.m3u8?b=&__b__=1000&hdnea=st=%s~exp=%s'
    gvu2 = 'https://tvebravo-vh.akamaihd.net/i/prod/video/%s_,1696,1296,896,696,496,240,306,.mp4.csmil/master.m3u8?b=&__b__=1000&hdnea=st=%s~exp=%s'
    url = uqp(url)
    url = url+'?mbr=true&player=Bravo%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
    html = getRequest(url)
    a = json.loads(html)
    suburl = a["captions"][0]["src"]
    url = suburl.split('/caption/',1)[1]
    url = url.split('.',1)[0]
    td = (datetime.datetime.utcnow()- datetime.datetime(1970,1,1))
    unow = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
    u   =  gvu1 % (url, str(unow), str(unow+60))
    req = urllib2.Request(u.encode(UTF8), None, defaultHeaders)
    try:
       response = urllib2.urlopen(req, timeout=20) # check to see if video file exists
    except:
       u   =  gvu2 % (url, str(unow), str(unow+60))
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = u))

    if (addon.getSetting('sub_enable') == "true"):
      profile = addon.getAddonInfo('profile').decode(UTF8)
      subfile = xbmc.translatePath(os.path.join(profile, 'SyfySubtitles.srt'))
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
          caption = caption.replace('<br/>','\n').replace('&gt;','>')
          ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
          idx += 1
        ofile.close()
        xbmc.sleep(2000)
        xbmc.Player().setSubtitles(subfile)

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

if mode==  None:  getShows()
elif mode=='GE':  getEpisodes(p('url'), p('name'))
elif mode=='GV':  getVideo(p('url'), p('name'))
