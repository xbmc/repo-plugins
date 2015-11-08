# -*- coding: utf-8 -*-
# WNBC Programs Kodi Addon

import sys,httplib
import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.wnbc')
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
       response = urllib2.urlopen(req, timeout=30)
       page = response.read()
       if response.info().getheader('Content-Encoding') == 'gzip':
           log("Content Encoding == gzip")
           page = zlib.decompress(page, zlib.MAX_WBITS + 16)

    except urllib2.URLError, e:
       if alert:
           xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 5000) )
       page = ""
    return(page)


def getSources():
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
        ilist=[]
        meta ={}
        if addon.getSetting('init_meta') != 'true':
          try:
            with open(metafile) as infile:
                meta = json.load(infile)
          except: pass
        showDialog = len(meta)
        html = getRequest('http://www.nbc.com/ajax/dropdowns-global/America-New_York', donotuseproxy=True)
        a    = json.loads(html)['menu_html']
        a = re.compile('title">Current Episodes</div>(.+?)<div class="more-link">',re.DOTALL).search(a).group(1)
        b    = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(a)
        if showDialog == 0 : 
           pDialog = xbmcgui.DialogProgress()
           pDialog.create('NBC', 'Initializing ...')
           numShows = len(b)
           i = 1
        for url, name in b:
              try:
                  (name, plot,img) = meta[url]
              except:
                   html = getRequest(('http://www.nbc.com%s' % url.replace('/video','',1)), donotuseproxy=True)
                   try:
                       name, plot, img = re.compile('"og:title" content="(.+?)".+?"og:description" content="(.+?)".+?"og:image" content="(.+?)"',re.DOTALL).search(html).groups()
                   except:
                       try:
                          plot, name, img = re.compile('"description" content="(.+?)".+?"og:title" content="(.+?)".+?"og:image" content="(.+?)"',re.DOTALL).search(html).groups()
                       except:
                          name, plot,img = re.compile('"og:title" content="(.+?)".+?="description" content="(.+?)".+?"og:image" content="(.+?)"',re.DOTALL).search(html).groups()
                   meta[url] = (name, plot, img)
              lmode = 'GC'
              name = h.unescape(name)
              u = '%s?url=%s&mode=%s' % (sys.argv[0],url, lmode)
              liz=xbmcgui.ListItem(name, '',None, img)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              ilist.append((u, liz, True))
              if showDialog == 0 : 
                 pDialog.update(int((100*i)/numShows))
                 i = i+1
        if showDialog == 0 : pDialog.close()
        with open(metafile, 'w') as outfile:
            json.dump(meta, outfile)
        outfile.close
        addon.setSetting(id='init_meta', value='false')
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('shows_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))



def getCats(gcurl):
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
        ilist=[]
        html = getRequest(('http://www.nbc.com%s' % gcurl), donotuseproxy=True)
        if 'the-tonight-show' in gcurl:
             html = getRequest('http://www.nbc.com/the-tonight-show/episodes', donotuseproxy=True)
             urls = re.compile('class="icon-full-episode".+?href="(.+?)".+?</div', re.DOTALL).findall(html)
             for url in urls:
                     pg = getRequest(('http://www.nbc.com%s' % url), donotuseproxy=True)
                     try:    dataid = re.compile('data-video-id="(.+?)"',re.DOTALL).search(pg).group(1)
                     except: continue
                     img    = re.compile('<img class="visuallyHidden" src="(.+?)"',re.DOTALL).search(pg).group(1)
                     name   = h.unescape(re.compile('itemprop="title">(.+?)<',re.DOTALL).search(pg).group(1))
                     plot   = h.unescape(re.compile('itemprop="description"><p>(.+?)<',re.DOTALL).search(pg).group(1))
                     url    = re.compile('<iframe id="player" class="player" src="(.+?)"', re.DOTALL).search(pg).group(1)
                     url    = url.replace('amp;','')
                     lmode = 'GV'
                     u = '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), lmode)
                     liz=xbmcgui.ListItem(name, '',None, img)
                     liz.setInfo( 'Video', { "Title": name, "Plot": plot})
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))

        else:

              blob = re.compile('\(Drupal.settings,(.+?)\);',re.DOTALL).search(html).group(1)
              a  = json.loads(blob)
              cars = re.compile('<div class="nbc_mpx_carousel.+?id="(.+?)".+?"pane-title">(.+?)<.+?>(.+?)<',re.DOTALL).findall(html)
              for carid, name1, name2 in cars:

                     url = a['video_carousel'][carid]['feedUrl']
                     img = a['video_carousel'][carid]['defaultImages']['big']
                     name = h.unescape((name1+name2).replace('<span class="strong">','').replace('</h2>','')).strip()
                     lmode = 'GS'
                     u = '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), lmode)
                     liz=xbmcgui.ListItem(name, '',img, None)
                     ilist.append((u, liz, True))

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('category_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
                
              

def getShow(gsurl):
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
    ilist=[]
    pg = getRequest(('http://www.nbc.com%s?range=1-29' % uqp(gsurl)), donotuseproxy=True)
    a  =  json.loads(pg)['entries']
    for e in a:
           infoList = {}
           name = h.unescape(e['title'])
           infoList['Title'] = name
           infoList['Plot']  = h.unescape(e['description'])
           infoList['TVShowTitle'] = e['showShortName']
           try:    infoList['Season'] = int(e['season'])
           except: infoList['Season'] = 0
           try:    infoList['Episode'] = int(e['episode'])
           except: infoList['Episode'] = 0
           infoList['duration'] = int(e['duration'].split(' ',1)[0])*60
           infoList['Studio'] = 'NBC'
           ad = e['airdate'].split('/')
           if int(ad[2]) > 30 : ad = '19%s-%s-%s' % (ad[2], ad[0], ad[1])
           else: ad = '20%s-%s-%s' % (ad[2], ad[0], ad[1])
           infoList['date'] = ad
           infoList['Aired'] = infoList['date']
           infoList['Year']  = int(infoList['date'].split('-',1)[0])
           url  = e['playerUrl']
           img  = e['images']['medium']
           lmode = 'GV'
           u = '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), lmode)
           liz=xbmcgui.ListItem(name, '',None, img)
           liz.setInfo( 'Video', infoList)
           liz.addStreamInfo('video', { 'codec': 'avc1', 
                                   'width' : 1280, 
                                   'height' : 720, 
                                   'aspect' : 1.78 })
           liz.addStreamInfo('audio', { 'codec': 'aac', 'language' : 'en', 'channels': 2})
           liz.addStreamInfo('subtitle', { 'language' : 'en'})
           liz.setProperty('IsPlayable', 'true')
           ilist.append((u, liz, False))

    xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
    if addon.getSetting('enable_views') == 'true':
        xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getVideo(surl):
            surl = uqp(surl)
            if surl.startswith('//') : surl = 'http:'+surl
            if not ('http://link.theplatform.com' in surl):
                html = getRequest(surl)
                surl = re.compile('<meta name="twitter:player" content="(.+?)"',re.DOTALL).search(html).group(1)
                if not ('onsite_no_endcard' in surl): surl = surl.split('?',1)[0].rsplit('/',1)[1]

            try:
             print "surl = "+str(surl)
             if not ('onsite_no_endcard' in surl): 
                surl = 'http://link.theplatform.com/s/NnzsPC/media/'+surl+'?mbr=true&player=Onsite%20Player&policy=43674&manifest=m3u&format=SMIL&Tracking=true&Embedded=true&formats=MPEG4,FLV,MP3'
             else:
                vid = surl.split('?',1)[0].rsplit('/',1)[1]
                surl = 'https://link.theplatform.com/s/NnzsPC/media/'+vid+'?mbr=true&player=Onsite%20Player%20--%20No%20End%20Card&policy=43674&format=SMIL&manifest=m3u&Tracking=true&Embedded=true&formats=MPEG4,FLV,MP3'
             print "final surl = "+str(surl)
             html = getRequest(surl, alert=False)
             if html == "":
                 surl = 'http://link.theplatform.com/s/NnzsPC/'+vid+'?mbr=true&player=Onsite%20Player%20--%20No%20End%20Card&policy=43674&format=SMIL&manifest=m3u&Tracking=true&Embedded=true&formats=MPEG4,FLV,MP3'
                 html = getRequest(surl, alert=False)

             finalurl  = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
             if 'nbcvodenc-i.akamaihd.net' in finalurl:
               html1 = getRequest(finalurl, donotuseproxy=True)
               html1 = html1.replace('\n','')
               html1 += '#'
               choices = re.compile('BANDWIDTH=([0-9]*).+?http(.+?)#').findall(html1)
               bw = 0
               for bwidth, link in choices:
                  if int(bwidth) > bw:
                     bw = int(bwidth)
                     finalurl = 'http'+link

             xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))

             try:
               suburl    = re.compile('<textstream src="(.+?)"',re.DOTALL).search(html).group(1)

               if (suburl != "") and ('.tt' in suburl) and (addon.getSetting('sub_enable') == "true"):
                 profile = addon.getAddonInfo('profile').decode(UTF8)
                 subfile = xbmc.translatePath(os.path.join(profile, 'NBCSubtitles.srt'))
                 prodir  = xbmc.translatePath(os.path.join(profile))
                 if not os.path.isdir(prodir):
                    os.makedirs(prodir)

                 pg = getRequest(suburl, donotuseproxy=True)
                 if pg != "":
                   ofile = open(subfile, 'w+')
                   captions = re.compile('<p begin="(.+?)" end="(.+?)">(.+?)</p>',re.DOTALL).findall(pg)
                   idx = 1
                   for cstart, cend, caption in captions:
                     cstart = cstart.replace('.',',')
                     cend   = cend.replace('.',',').split('"',1)[0]
                     caption = caption.replace('<br/>','\n')
                     try:
                       caption = h.unescape(caption)
                     except: pass
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
elif mode=='GS':  getShow(p('url'))
elif mode=='GC':  getCats(p('url'))
elif mode=='GV':  getVideo(p('url'))
