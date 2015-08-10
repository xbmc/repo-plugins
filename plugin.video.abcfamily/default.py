# -*- coding: utf-8 -*-
# ABC Family Programs Kodi Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.abcfamily')
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


qp  = urllib.quote_plus
uqp = urllib.unquote_plus

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 'Accept':"text/html,*/*", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'} 

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
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

        ilist=[]
        html = getRequest('http://abcfamily.go.com/shows')
        a = re.compile('<article class="item fepAvailable">.+?href="(.+?)".+?title="(.+?)".+?"src":"(.+?)".+?"description hidden">(.+?)<.+?</article',re.DOTALL).findall(html)
        for url, name, img1, plot in a:
              name = name.replace('<strong>','').replace('</strong>','')
              name=h.unescape(name.decode(UTF8))
              fanart = 'http://static.east.abc.go.com/service/image/index/id/%s/dim/640x360.png' % img1
              thumb = fanart
              u = '%s?url=%s&mode=GS' % (sys.argv[0],qp(url))
              liz=xbmcgui.ListItem(name, '',None, thumb)
              infoList ={}
              infoList['Title'] = name
              infoList['TVShowTitle'] = name
              infoList['Plot'] = h.unescape(plot.decode(UTF8))
              liz.setInfo( 'Video', infoList)
              liz.setProperty('fanart_image', fanart)
              ilist.append((u, liz, True))

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
          xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getShows(gcurl):
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

        gcurl = uqp(gcurl)
        ilist=[]
        meta ={}
        sname = gcurl
        meta[sname]={}
        if addon.getSetting('init_meta') != 'true':
           try:
              with open(metafile) as infile:
                  meta = json.load(infile)
           except: pass
        try: showDialog = len(meta[sname])
        except:
              meta[sname]={}
              showDialog = len(meta[sname])
      

        html = getRequest(gcurl)
        vids = re.compile('<article class="item fep available">.+?href="(.+?)".+?</article>', re.DOTALL).findall(html)
        if showDialog == 0 : 
            pDialog = xbmcgui.DialogProgress()
            pDialog.create(__language__(30082), __language__(30083))
            pDialog.update(0)
            numShows = len(vids)
            i = 1
        dirty = False
        for xurl in vids:
           try:
               (name, vd, url, thumb, fanart, infoList) = meta[sname][xurl]
           except:
               dirty = True
               html = getRequest(xurl)
               try:    vd = re.compile('vp:video="VDKA(.+?)"',re.DOTALL).search(html).group(1)
               except: 
                 try: 
                     vd = re.compile('data-video-id="VDKA(.+?)"',re.DOTALL).search(html).group(1)
                 except: continue

               url = 'http://cdnapi.kaltura.com//api_v3/index.php?service=multirequest&action=null&ignoreNull=1&2%3Aaction=getContextData&3%3Aaction=list&2%3AcontextDataParams%3AflavorTags=uplynk&2%3AentryId='+vd+'&apiVersion=3%2E1%2E5&1%3Aversion=-1&2%3AcontextDataParams%3AstreamerType=http&3%3Afilter%3AentryIdEqual='+vd+'&clientTag=kdp%3Av3%2E9%2E2&1%3AentryId='+vd+'&2%3AcontextDataParams%3AobjectType=KalturaEntryContextDataParams&3%3Afilter%3AobjectType=KalturaCuePointFilter&2%3Aservice=baseentry&1%3Aservice=baseentry&1%3Aaction=get'
               html = getRequest(url)
               url,duration,name, description, catname,thumb,sdate = re.compile('<dataUrl>(.+?)</dataUrl>.+?<duration>(.+?)</duration>.+?<name>(.+?)</name><description>(.+?)</description>.+?<categories>(.+?)</categories>.+?<thumbnailUrl>(.+?)</thumbnailUrl>.+?<startDate>(.+?)</startDate>',re.DOTALL).search(html).groups()
               name = h.unescape(name.decode(UTF8))
               plot = h.unescape(description.decode(UTF8))
               url = url.strip()
               try: url = 'http://cdnapi.kaltura.com/p/585231/sp/58523100/playManifest/entryId/%s/flavorId/%s/format/http/protocol/http/cdnHost/cdnbakmi.kaltura.com/storageId/1571/uiConfId/8628162/tags/uplynk/a/a.f4m' % (vd , re.compile('<entryId>(.+?)<',re.DOTALL).search(html).group(1))
               except: pass
               thumb = thumb.strip()
               fanart = thumb
               infoList = {}
               try:
                 x = name.split(' ',3)
                 if x[1].startswith('Ep'):
                   infoList['Season'] = int(x[0].replace('S',''))
                   infoList['Episode'] = int(x[2])
                   name = x[3]
                 else: raise ValueError('Non fatal error')
               except:
                   infoList['Season'] = 0
                   infoList['Episode'] = 0
               infoList['Title'] = name
               infoList['Plot']  = plot
               infoList['TVShowTitle'] = h.unescape(catname)
               infoList['Duration'] = int(duration)
               infoList['Date']     = datetime.datetime.fromtimestamp(int(sdate)).strftime('%Y-%m-%d')
               infoList['Aired']    = infoList['Date']
               infoList['Year']     = int(infoList['Aired'].split('-',1)[0])
               infoList['Studio']   = 'ABC'
               meta[sname][xurl] = (name, vd, url, thumb, fanart, infoList)

           u = '%s?url=%s&name=%s&mode=GV' % (sys.argv[0],qp(url), vd)
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
        if addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
             

def getVideo(surl, vid):
    finalurl = uqp(surl)
    if finalurl.endswith('.f4m'):
       html = getRequest(finalurl)
       finalurl = re.compile('<media url="(.+?)"',re.DOTALL).search(html).group(1).replace('&amp;','&')
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))
    suburl = 'http://api.contents.watchabc.go.com/vp2/ws/s/contents/2020/videos/002/001/-1/-1/-1/VDKA%s/-1/-1?v=08.00' % vid
    if (suburl != "") and (addon.getSetting('sub_enable') == "true"):
       profile = addon.getAddonInfo('profile').decode(UTF8)
       subfile = xbmc.translatePath(os.path.join(profile, 'Subtitles.srt'))
       prodir  = xbmc.translatePath(os.path.join(profile))
       if not os.path.isdir(prodir):
          os.makedirs(prodir)

       pg = getRequest(suburl)
       suburl = re.compile('<closedcaption enabled="true">.+?http:(.+?)<',re.DOTALL).search(pg).group(1)
       suburl = 'http:'+suburl.strip()
       pg = getRequest(suburl)

       if pg != "":
          ofile = open(subfile, 'w+')
          captions = re.compile('<p begin="(.+?)" end="(.+?)".+?/>(.+?)</p>',re.DOTALL).findall(pg)
          idx = 1
          for cstart, cend, caption in captions:
              if cstart.startswith('01'): cstart = cstart.replace('01','00',1)
              if cend.startswith('01'): cend = cend.replace('01','00',1)
              cstart = cstart.replace('.',',')
              cend   = cend.replace('.',',').split('"',1)[0]
              caption = caption.replace('<br/>','\n').replace('&quot;',"'")
              try:  caption = h.unescape(caption.encode(UTF8))
              except: pass
              ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
              idx += 1
          ofile.close()
          xbmc.sleep(3000)
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

if mode==  None:  getSources()
elif mode=='GS':  getShows(p('url'))
elif mode=='GV':  getVideo(p('url'),p('name'))


