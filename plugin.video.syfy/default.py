# -*- coding: utf-8 -*-
# Kodi Addon for Syfy 
import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus

UTF8     = 'utf-8'
SYFYBASE = 'http://www.syfy.com%s'

addon         = xbmcaddon.Addon('plugin.video.syfy')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
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

def getShows():
   xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

   ilist=[]
   epiHTML = getRequest('http://www.syfy.com/episodes')
   posterHTML = getRequest('http://www.syfy.com/shows')
   posters = re.compile('<div class="grid-image-above">.+?<img  srcset="(.+?)".+?class="title">(.+?)<',re.DOTALL).findall(posterHTML)
   shows = re.compile('<div class="show id.+?<h3>(.+?)<.+?</div',re.DOTALL).findall(epiHTML)
   for name in shows:
       poster = None
       for pimg, pname in posters:
          if pname == name:
            poster = pimg
            break

       m  = re.compile('<div class="show id.+?<h3>'+name+'</h3>(.+?)</a></div>  </div>  </div>\n    </div>',re.DOTALL).search(epiHTML)
       epis = re.compile('href="(.+?)"',re.DOTALL).findall(epiHTML,m.start(1),m.end(1))
       vcnt = len(epis)
       url  = SYFYBASE % epis[len(epis)-1]
       html = getRequest(url)
       purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html).group(1)
       purl = 'http:'+purl.replace('&amp;','&')
       html = getRequest(purl)
       purl = re.compile('<link rel="alternate" href=".+?<link rel="alternate" href="(.+?)"',re.DOTALL).search(html).group(1)
       purl += '&format=Script&height=576&width=1024'

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
       url = '%s/cast' % url.split('/video',1)[0]
       html = getRequest(url)
       try:    infoList['Plot'] = re.compile('<div class="field field-name-body.+?<p>(.+?)</p',re.DOTALL).search(html).group(1)
       except: 
          try:    infoList['Plot'] = re.compile('<meta name="description" content="(.+?)"',re.DOTALL).search(html).group(1)
          except: infoList['Plot'] = '%s Episodes' % str(vcnt)
       infoList['cast'] = re.compile('<article class="tile.+?tile-marqee">(.+?)<.+?</article',re.DOTALL).findall(html)
       if len(infoList['cast']) == 0: 
          infoList['cast'] = re.compile('<article class="tile.+?tile-title">(.+?)<.+?</article',re.DOTALL).findall(html)
       infoList['Plot'] = h.unescape(infoList['Plot'])
       url = name
       mode = 'GE'
       u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
       liz=xbmcgui.ListItem(name, '',poster, None)
       liz.setInfo( 'Video', infoList)
       liz.setProperty('fanart_image', addonfanart)
       ilist.append((u, liz, True))
   xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
   if addon.getSetting('enable_views') == 'true':
      xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
   xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getEpisodes(sname, showName):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
   xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

   sname = uqp(sname)
   ilist=[]
   html = getRequest('http://www.syfy.com/episodes')
   m  = re.compile('<div class="show id.+?<h3>'+sname+'</h3>(.+?)<div class="view-footer">',re.DOTALL).search(html)
   fd = re.compile('href="(.+?)/videos').search(html,m.start(1),m.end(1)).group(1)
   epis = re.compile('href="'+fd+'(.+?)"',re.DOTALL).findall(html,m.start(1),m.end(1))
   for url in epis:
      mode = 'GV'
      url = SYFYBASE % fd+url
      html = getRequest(url)
      purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html).group(1)
      purl = 'http:'+purl.replace('&amp;','&')
      html = getRequest(purl)
      purl = re.compile('<link rel="alternate" href=".+?<link rel="alternate" href="(.+?)"',re.DOTALL).search(html).group(1)
      purl += '&format=Script&height=576&width=1024'
      html = getRequest(purl)
      a = json.loads(html)
      name    = a['title']
      fanart  = a['defaultThumbnailUrl']
      thumb   = a['defaultThumbnailUrl']

      infoList = {}
      infoList['Date']        = datetime.datetime.fromtimestamp(a['pubDate']/1000).strftime('%Y-%m-%d')
      infoList['Aired']       = infoList['Date']
      infoList['Duration']    = str(int(a['duration']/1000))
      infoList['MPAA']        = a['ratings'][0]['rating']
      infoList['Title']       = a['title']
      infoList['Studio']      = a['provider']
      infoList['Genre']       = (a['nbcu$advertisingGenre']).replace('and','/')
      infoList['Episode']     = a['pl1$episodeNumber']
      infoList['Season']      = a['pl1$seasonNumber']
      try:
         infoList['Plot']     = h.unescape(a["description"])
      except:
         infoList['Plot']     = h.unescape(a["abstract"])
      infoList['Title']       = a['title']
      infoList['TVShowTitle'] = showName
      infoList['Studio']      = a['provider']

      url = purl
      u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
      liz=xbmcgui.ListItem(name, '',icon, thumb)
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
    gvu1 = 'https://tvesyfy-vh.akamaihd.net/i/prod/video/%s_,25,40,18,12,7,4,2,00.mp4.csmil/master.m3u8?__b__=1000&hdnea=st=%s~exp=%s'
    gvu2 = 'https://tvesyfy-vh.akamaihd.net/i/prod/video/%s_,1696,1296,896,696,496,240,306,.mp4.csmil/master.m3u8?__b__=1000&hdnea=st=%s~exp=%s'
    pfu1 = 'http://link.theplatform.com/s/HNK2IC/media/'
    pfparms = '?player=Syfy.com%20Player&policy=2713542&manifest=m3u&formats=flv,m3u,mpeg4&format=SMIL&embedded=true&tracking=true'

    url = uqp(url)
    url = url.replace(' ','%20')
    html = getRequest(url)
    a = json.loads(html)
    try:
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
    except:
         url = a['mediaPid']
         url = pfu1+url+pfparms
         html = getRequest(url)
         u  = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)

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
