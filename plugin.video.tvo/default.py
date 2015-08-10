# -*- coding: utf-8 -*-
# TV Ontario Kodi Addon

import sys
import httplib, socket

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.tvo')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))
profile       = addon.getAddonInfo('profile').decode(UTF8)
pdir  = xbmc.translatePath(os.path.join(profile))
if not os.path.isdir(pdir):
   os.makedirs(pdir)

metafile      = xbmc.translatePath(os.path.join(profile, 'shows.json'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, userdata= None, headers = defaultHeaders):

#   log("getRequest URL:"+str(url))
   req = urllib2.Request(url.encode(UTF8), userdata, headers)
   try:
      response = urllib2.urlopen(req)
      page = response.read()
      if response.info().getheader('Content-Encoding') == 'gzip':
         log("Content Encoding == gzip")
         page = zlib.decompress(page, zlib.MAX_WBITS + 16)
   except:
      page = ""
   return(page)

def getHTTP(url):
 host = url.split('//',1)[1]
 host, url = host.split('/',1)
 url = '/'+url
 conn = httplib.HTTPConnection(host)
 conn.request("GET", url)
 r1 = conn.getresponse()
 if r1.status != 301: return r1.read()
 url = r1.getheader('Location')
 return getHTTP(url)



def getSources():
    ilist = []
    azurl = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1'

    for a in azurl:
        name = a
        plot = ''
        url  = a
        mode = 'GA'
        u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
        liz=xbmcgui.ListItem(name, '',icon, None)
        liz.setProperty( "Fanart_Image", addonfanart )
        ilist.append((u, liz, True))
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

           
def getAtoZ(gzurl):
    meta ={}
    dirty = False
    meta['shows']={}
    if addon.getSetting('init_meta') != 'true':
       try:
          with open(metafile) as infile:
              meta = json.load(infile)
       except: pass
    try:
       showDialog = len(meta['shows'][gzurl])
    except:
       meta['shows'][gzurl]={}
       showDialog = 0

    ilist = []
    azheaders = defaultHeaders
    azheaders['X-Requested-With'] = 'XMLHttpRequest'
    html = getRequest('http://tvo.org/programs/%s/filter-ajax' % gzurl,None, azheaders)
    a = re.compile('href="(.+?)">(.+?)<',re.DOTALL).findall(html)
    if showDialog == 0 : 
       pDialog = xbmcgui.DialogProgress()
       pDialog.create(__language__(30082), __language__(30083))
       numShows = len(a)
       i = 1

    for url, name in a:
      try:
         (vid, name, img, fanart, mode, infoList) = meta['shows'][gzurl][url]
      except:
        mode = 'GS'
        html = getHTTP('http://tvo.org%s' % url)
        try:
           vid = url
           img, plot = re.compile('field-featured-image.+?src="(.+?)".+?"field-item even">(.+?)<',re.DOTALL).search(html).groups()
           fanart = img
        except:
         try:
           mode = 'GV'
           vid = re.compile('data-video-id="(.+?)"',re.DOTALL).search(html).group(1)
           vurl = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=1280&height=720&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=756015080001&playerKey=AQ~~,AAAABDk7A3E~,xYAUE9lVY9-LlLNVmcdybcRZ8v_nIl00&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+vid+'&secureConnections=true&secureHTMLConnections=true'
           html = getRequest(vurl)
           m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
           a = json.loads(html[m.start(1):m.end(1)+1])
           a = a['data']['programmedContent']['videoPlayer']['mediaDTO']
           img = a['thumbnailURL']
           plot = a['longDescription']
           fanart = a['videoStillURL']
         except:
           mode = 'GS'
           img = icon
           plot = name
           fanart = addonfanart 
        infoList = {}
        name = h.unescape(name)
        infoList['Title'] = name
        try:    infoList['Plot']  = h.unescape(plot.decode(UTF8))
        except: infoList['Plot'] = plot
        infoList['TVShowTitle'] = name
        meta['shows'][gzurl][url] = (vid, name, img, fanart, mode, infoList)
        dirty = True
      u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(vid), qp(name), mode)
      liz=xbmcgui.ListItem(name, '', None, img)
      liz.setInfo( 'Video', infoList)
      liz.setProperty( "Fanart_Image", fanart )
      if mode == 'GV':
         liz.setProperty('IsPlayable', 'true')
         ilist.append((u, liz, False))
      else: 
         ilist.append((u, liz, True))
      if showDialog == 0 : 
          pDialog.update(int((100*i)/numShows))
          i = i+1
    if showDialog == 0 : pDialog.close()
    if dirty == True:
      with open(metafile, 'w') as outfile:
         json.dump(meta, outfile)
      outfile.close
    addon.setSetting(id='init_meta', value='false')
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getShows(gsurl,catname):
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        ilist = []
        meta ={}
        dirty = False
        meta[gsurl]={}
        if addon.getSetting('init_meta') != 'true':
           try:
              with open(metafile) as infile:
                  meta = json.load(infile)
           except: pass
        try: showDialog = len(meta[gsurl])
        except:
              meta[gsurl]={}
              showDialog = len(meta[gsurl])
      
        html = getRequest('http://tvo.org%s' % uqp(gsurl))
        cats = re.compile('<div class="content-list__first.+?href="(.+?)".+?src="(.+?)".+?title="(.+?)".+?field-summary">.+?>(.+?)<',re.DOTALL).findall(html)
        if len(cats) == 0:
              cats = re.compile('<li class="views-row.+?href="(.+?)".+?src="(.+?)".+?title="(.+?)".+?field-summary">.+?>(.+?)<.+?</li>',re.DOTALL).findall(html)

        if showDialog == 0 : 
            pDialog = xbmcgui.DialogProgress()
            pDialog.create(__language__(30082), __language__(30083))
            numShows = len(cats)
            i = 1

        for url,img,name,plot in cats:
          try:
              (name, img, vid, infoList) = meta[gsurl][url]
          except:
              infoList = {}
              html = getRequest('http://tvo.org%s' % url)
              try: vid = re.compile('data-video-id="(.+?)"',re.DOTALL).search(html).group(1)
              except: continue
              name = h.unescape(name)
              infoList['Title'] = name
              try:    infoList['Plot']  = h.unescape(plot.decode(UTF8))
              except:   infoList['Plot']  = plot
              infoList['TVShowTitle'] = catname
              meta[gsurl][url] = (name, img, vid, infoList)
              dirty = True
          u = '%s?url=%s&mode=GV' % (sys.argv[0],vid)
          liz=xbmcgui.ListItem(name, '',None, img)
          liz.setInfo( 'Video', infoList)
          liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width' : 480, 
                                   'height' : 360, 
                                   'aspect' : 1.78 })
          liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
          liz.addStreamInfo('subtitle', { 'language' : 'en'})
          liz.setProperty('fanart_image', img)
          liz.setProperty('IsPlayable', 'true')
          ilist.append((u, liz, False))
          if showDialog == 0 : 
             pDialog.update(int((100*i)/numShows))
             i = i+1
        if showDialog == 0 : pDialog.close()
        if dirty == True:
          with open(metafile, 'w') as outfile:
              json.dump(meta, outfile)
          outfile.close
        addon.setSetting(id='init_meta', value='false')

        if len(ilist) != 0:
          xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
          xbmcplugin.endOfDirectory(int(sys.argv[1]))
        else:
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, __language__(30011), 10000) )


def getVideo(vid):
            url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=1280&height=720&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=756015080001&playerKey=AQ~~,AAAABDk7A3E~,xYAUE9lVY9-LlLNVmcdybcRZ8v_nIl00&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+vid+'&secureConnections=true&secureHTMLConnections=true'
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
                    subfile = xbmc.translatePath(os.path.join(profile, 'TVOSubtitles.srt'))
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
elif mode=='GS':  getShows(p('url'),p('name'))
elif mode=='GV':  getVideo(p('url'))
elif mode=='GA':  getAtoZ(p('url'))
