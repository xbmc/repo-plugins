# -*- coding: utf-8 -*-
# WRAL News and Weather XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import zlib,json,HTMLParser
h = HTMLParser.HTMLParser()


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.wral')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))
cbsIcon       = xbmc.translatePath(os.path.join(home, 'cbs_icon.png'))


qp  = urllib.quote_plus
uqp = urllib.unquote_plus

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, user_data=None, headers = defaultHeaders , alert=True):

    if addon.getSetting('us_proxy_enable') == 'true':
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
       if e.code == 404:
          response = e
          page = response.read()
          if response.info().getheader('Content-Encoding') == 'gzip':
             log("Content Encoding == gzip")
             page = zlib.decompress(page, zlib.MAX_WBITS + 16)

       elif alert:
           xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 5000) )
           page =""
       else:    page = ""

    return(page)

def getSources():
        ilist=[]

        name = 'WRAL Local News and Weather'
        u = '%s?url=%s&mode=%s' % (sys.argv[0],'dummy','GO1')
        liz=xbmcgui.ListItem(name, '',icon, None)
        liz.setProperty('fanart_image', addonfanart)
        ilist.append((u, liz, True))


        name = 'Watch CBS Shows'
        u = '%s?url=%s&mode=%s' % (sys.argv[0],'dummy','GB')
        liz=xbmcgui.ListItem(name, '',cbsIcon, None)
        liz.setProperty('fanart_image', addonfanart)
        ilist.append((u, liz, True))

        name = 'CBS News Shows'
        u = '%s?url=%s&mode=%s' % (sys.argv[0],'news','GBA')
        liz=xbmcgui.ListItem(name, '', cbsIcon, None)
        liz.setProperty('fanart_image', addonfanart)
        ilist.append((u, liz, True))

        name = 'CBS Sports'
        u = '%s?url=%s&mode=%s' % (sys.argv[0],'sports','GBA')
        liz=xbmcgui.ListItem(name, '',cbsIcon, None)
        liz.setProperty('fanart_image', addonfanart)
        ilist.append((u, liz, True))


        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))



def getSources1():
        ilist=[]
        html = getRequest('http://www.wral.com/weather/video/1076424/')
        b    = re.compile('<button data-switch-btn=.+?>(.+?)<',re.DOTALL).findall(html)
        i = 0
        for a in b:
              i += 1
              url = str(i)
              name = a
              plot = ''
              lmode = 'GC'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), lmode)
              liz=xbmcgui.ListItem(name, '',icon, None)
              liz.setProperty('fanart_image', addonfanart)
              ilist.append((u, liz, True))

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
        if addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))



def getCats(gcurl, catname):
              xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
  
              ilist=[]
              html = getRequest('http://www.wral.com/weather/video/1076424/')
              blob = re.compile('define\(.+?return (.+?)\};',re.DOTALL).search(html).group(1)
              blob = blob+'}'
              a  = json.loads(blob)
              a = a['multimedia']['standalone']['shelf_assets']
              i = 0
              for b in a:
                 i += 1
                 if i == int(gcurl):
                   for hl in b:
                     name = h.unescape(hl['headline'])
                     plot = h.unescape(hl['abstract'])
                     url  = hl['configURL']
                     img  = hl['image_100x75'].replace('100x75','640x480')
                     lmode = 'GS'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), lmode)
                     liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "TVShowTitle": catname, "Plot": plot})
                     liz.setProperty('fanart_image', addonfanart)
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))

              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
              if addon.getSetting('enable_views') == 'true':
                 xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
              xbmcplugin.endOfDirectory(int(sys.argv[1]))

                 
              

def getShow(gsurl):
              pg = getRequest(uqp(gsurl))
              a  =  json.loads(pg)['playlist'][0]
              url = '%s playpath=%s swfUrl=http://wwwcache.wral.com/presentation/v3/scripts/vendor/flowplayer/flowplayer.commercial-3.2.18-wral.swf?v=20140210a swfvfy=1 pageurl=http://www.wral.com/weather/video/1076424/' % (a['netConnectionUrl'], a['url'].replace('mp4:',''))
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))
              xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getCBSShowsAff(url):
              ilist=[]
              html = getRequest('http://can.cbs.com/thunder/player/iframe/index.php')
              blob = re.compile('<div id="'+url+'"(.+?)</div',re.DOTALL).search(html).group(1)
              shows = re.compile('<a href="(.+?)".+?>(.+?)<',re.DOTALL).findall(blob)
              for url, name in shows:
                 u = '%s?url=%s&name=%s&mode=GLA' % (sys.argv[0],qp(url),qp(name))
                 liz=xbmcgui.ListItem(name, '',cbsIcon, None)
                 ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
              if addon.getSetting('enable_views') == 'true':
                 xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('default_view'))
              xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getCBSVideosAff(gsurl,showName):
              xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
              ilist=[]
              showName = uqp(showName)
              gsurl = uqp(gsurl).replace(' ','%20')
              pg = getRequest(gsurl)
              vids = re.compile('img src="(.+?)".+?pid=(.+?)&.+?title="(.+?)".+?</h4>.+?>(.+?)<',re.DOTALL).findall(pg)
              for img, url, name, desc in vids:
                     name = h.unescape(name)
                     plot = h.unescape(desc)
                     img = img.replace('200x150.jpg','640x480.jpg')
                     u = '%s?url=%s&mode=GV1' % (sys.argv[0],qp(url))
                     liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "TVShowTitle":showName, "Plot": plot})
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))

              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
              if addon.getSetting('enable_views') == 'true':
                  xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
              xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getCBSShows(gsurl):
         ilist=[]
         html = getRequest('http://www.cbs.com/carousels/showsByCategory/0/offset/0/limit/100/?nm')
         a = json.loads(html)
         a = a['result']['data']


         html = getRequest('http://www.cbs.com/carousels/showsByCategory/4/offset/0/limit/100/?nm')
         b = json.loads(html)
         b = b['result']['data']
         a.extend(b)

         html = getRequest('http://www.cbs.com/carousels/showsByCategory/6/offset/0/limit/100/?nm')
         b = json.loads(html)
         b = b['result']['data']
         a.extend(b)

         for b in a:
              thumb = b['filepath_nav_medium_photo']
              name  = b['title'].encode('utf-8')
              url = ''
              navitem = {}
              try:
                   for c in b['navigationItemLink']:
                      navitem[c['title']] = c['link']
                   url = navitem['Watch']
              except: continue

              u = '%s?url=%s&mode=GL' % (sys.argv[0],qp(url))
              liz=xbmcgui.ListItem(name, '',None, thumb)
              liz.setProperty('fanart_image', thumb)
              ilist.append((u, liz, True))
         xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
         if addon.getSetting('enable_views') == 'true':
            xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('shows_view'))
         xbmcplugin.endOfDirectory(int(sys.argv[1]))




def getCBSVideos(gsurl):
              xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_VIDEO_YEAR)
              xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)
              ilist=[]
              gsurl = uqp(gsurl).replace(' ','%20')
              if not gsurl.startswith('http'): gsurl = 'http://www.cbs.com%s' % gsurl
              html = getRequest(gsurl)
              catid = re.compile('video.section_ids = \[(.+?)\]',re.DOTALL).search(html).group(1)
              catid = catid.split(',',1)[0]
              html = getRequest('http://www.cbs.com/carousels/videosBySection/%s/offset/0/limit/40/xs/0/' % catid)
              a = json.loads(html)
              a = a['result']['data']
              for b in a:
                     if b["is_paid_content"] == True: continue
                     infoList = {}
                     try:
                        infoList['Date']    = datetime.datetime.fromtimestamp(b['airdate_ts']/1000).strftime('%Y-%m-%d')
                        infoList['Aired']   = infoList['Date']
                        infoList['Year']    = int(infoList['Aired'].split('-',1)[0])
                     except: pass
                     infoList['Title']   = b['episode_title']
                     name                = infoList['Title']
                     url                 = b['url']
                     infoList['Plot']    = b['description']
                     img    = b['thumb']["640x480"]
                     infoList['TVShowTitle'] = b['series_title']
                     try:    infoList['Season']      = b['season_number']
                     except: infoList['Season'] = -1
                     try:    infoList['Episode']     = b['episode_number']
                     except: infoList['Episode'] = -1
                     infoList['Studio']      = 'CBS'
                     dur = b['duration']
                     duration = 0
                     try:
                        dur = dur.strip()
                        for d in dur.split(':'): duration = duration*60+int(d)
                     except: pass
                     infoList['duration'] = duration
                     u = '%s?url=%s&mode=GV' % (sys.argv[0],qp(url))
                     liz=xbmcgui.ListItem(name, '',img, None)
                     liz.setInfo( 'Video', infoList)
                     liz.setProperty('fanart_image', img)
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))

              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
              if addon.getSetting('enable_views') == 'true':
                  xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.getSetting('episode_view'))
              xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getVideo(url):
              html = getRequest('http://www.cbs.com%s' % uqp(url))
              foundpid = re.compile("cbsplayer.pid = '(.+?)'", re.DOTALL).search(html).group(1)
              getVideo1(foundpid)

def getVideo1(foundpid):
              pg = getRequest('http://link.theplatform.com/s/dJ5BDC/%s?format=SMIL&mbr=true' % foundpid)
              try:
                 suburl = re.compile('"ClosedCaptionURL" value="(.+?)"',re.DOTALL).search(pg).group(1)
              except:
                 suburl = ""

              frtmp,fplay = re.compile('<meta base="(.+?)".+?<video src="(.+?)"',re.DOTALL).search(pg).groups()
              swfurl='http://canstatic.cbs.com/chrome/canplayer.swf swfvfy=true'
              if '.mp4' in fplay:
                pphdr = 'mp4:'
                frtmp = frtmp.replace('&amp;','&')
                fplay = fplay.replace('&amp;','&')
              else:
                pphdr = ''
                xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__,__language__(30011) , '10000') ) #added
                frtmp = frtmp.replace('rtmp:','rtmpe:')
                frtmp = frtmp.replace('.net','.net:1935')
                frtmp = frtmp.replace('?auth=','?ovpfv=2.1.9-internal&?auth=')
                swfurl = 'http://vidtech.cbsinteractive.com/player/3_3_2/CBSI_PLAYER_HD.swf swfvfy=true pageUrl=http://www.cbs.com/shows'
              finalurl = '%s playpath=%s%s swfurl=%s timeout=20' % (frtmp, pphdr, fplay, swfurl)
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))

              if (suburl != "") and ('xml' in suburl) and (addon.getSetting('sub_enable') == "true"):
                 profile = addon.getAddonInfo('profile').decode(UTF8)
                 subfile = xbmc.translatePath(os.path.join(profile, 'CBSSubtitles.srt'))
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

if mode==  None:  getSources()
elif mode=='GO1': getSources1()
elif mode=='GS':  getShow(p('url'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GB':  getCBSShows(p('url'))
elif mode=='GBA':  getCBSShowsAff(p('url'))
elif mode=='GL':  getCBSVideos(p('url'))
elif mode=='GLA':  getCBSVideosAff(p('url'),p('name'))
elif mode=='GV':  getVideo(p('url'))
elif mode=='GV1':  getVideo1(p('url'))


