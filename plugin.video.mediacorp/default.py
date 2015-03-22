# -*- coding: utf-8 -*-
# Mediacorp Broadcove


import urllib
import urllib2
import cookielib
import datetime
import time
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import cgi
import httplib, sys
from StringIO import StringIO
import cgi, gzip


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.mediacorp')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode('utf-8')
media         = xbmc.translatePath(os.path.join(home, 'resources', 'media'))
icon_next     = xbmc.translatePath(os.path.join(media, 'next.png'))
icon_channel5  = xbmc.translatePath(os.path.join(media, 'icon_channel5.png'))
icon_channel8  = xbmc.translatePath(os.path.join(media, 'icon_channel8.png'))
icon_channelu  = xbmc.translatePath(os.path.join(media, 'icon_channelu.png'))
icon_okto      = xbmc.translatePath(os.path.join(media, 'icon_okto.png'))
icon_suria     = xbmc.translatePath(os.path.join(media, 'icon_suria.png'))
icon_vasantham = xbmc.translatePath(os.path.join(media, 'icon_vasantham.png'))

icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


qp  = urllib.quote_plus
uqp = urllib.unquote_plus

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def cleanname(name):    
    return name.replace('&#39;',"'").replace('&amp;','&')


def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge

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
                 response = urllib2.urlopen(req)
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()

              except urllib2.URLError, e:
                 if alert:
                     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 10000) )
                 link1 = ""

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)



def getSources():
              dolist = [('channel5', 30002, icon_channel5),('channel8', 30003, icon_channel8),('channelu', 30004, icon_channelu), 
                        ('okto', 30007, icon_okto), ('suria', 30008, icon_suria), ('vasantham', 30009, icon_vasantham)]

              for url, gstr, img in dolist:
                  name = __language__(gstr)
                  liz  = xbmcgui.ListItem(name,'',img,img)
                  liz.setProperty( "Fanart_Image", addonfanart )
                  xbmcplugin.addDirectoryItem(int(sys.argv[1]), '%s?url=%s&name=%s&iconimage=%s&mode=%s' % (sys.argv[0],qp(url),qp(name), qp(img), 'GC'), liz, True)

def getChannel(url,iconimage,channame):
     iconimage = uqp(iconimage)
     channame  = uqp(channame)
     html  = getRequest('http://xin.msn.com/en-sg/video/catchup/', donotuseproxy=True)
     blob  = re.compile('class="section tabsection horizontal".+?data-section-id="%s"(.+?)</ul>' % (url)).search(html).group(1)
     blobs = re.compile('<li tabindex="0" data-tabid="(.+?)".+?>(.+?)</li>').findall(blob)
     ilist = []
     for curl, name in blobs:
         urx = '%s#%s' % (url, curl)
         name = cleanname(name).strip()
         plot = name
         u    = "%s?url=%s&name=%s&channame=%s&mode=%s" % (sys.argv[0], urx, qp(name), qp(channame), 'GS')
         liz=xbmcgui.ListItem(name, '','DefaultFolder.png', iconimage)
         liz.setProperty( "Fanart_Image", addonfanart )
         liz.setInfo( 'Video', { "Studio": channame, "Title": name, "Plot": plot })
         ilist.append((u, liz, True))
     xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getShows(url, channame):
 channame = uqp(channame)
 try:
  url, caturl = url.split('#')
  html = getRequest('http://xin.msn.com/en-sg/video/catchup/', donotuseproxy=True)
  blob  = re.compile('class="section tabsection horizontal".+?data-section-id="%s".+?<div data-tabkey="%s"(.+?)</ul>' % (url, caturl)).search(html).group(1)
  blobs = re.compile('<li.+?href="(.+?)".+?:&quot;(.+?)&quot.+?<h4>(.+?)</h4>.+?"duration">(.+?)<.+?</li>').findall(blob)

  ilist = []
  for url, img, name, dur in blobs:
     url  = 'http://xin.msn.com'+url
     dur  = dur.strip()
     name = cleanname(name).strip()
     plot = name
     img  = 'http:'+img.replace('&amp;','&')
     u    = "%s?url=%s&name=%s&mode=%s" % (sys.argv[0],qp(url), qp(name), 'GV')
     liz=xbmcgui.ListItem(name, '',img, img)
     liz.setProperty( "Fanart_Image", addonfanart )
     liz.setInfo( 'Video', { "Studio": channame, "Title": name, "Plot": plot })
     liz.setProperty('IsPlayable', 'true')
     ilist.append((u, liz, False))
  xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

 except:
     return


def getVideo(url):
  retry = 2
  dontuseproxy = True
  while (retry > 0):
    html = getRequest(url, donotuseproxy = dontuseproxy)
    html=html.replace('\r','').replace("&#39;","'").replace('&quot;','"')
    try:
       vidurl = re.compile('"formatCode":"103","url":"(.+?)"').search(html).group(1)
       retry = 0
    except:
       try:
          vidurl = re.compile('"formatCode":"101","url":"(.+?)"').search(html).group(1)
          retry = 0

       except:
          try:
            videoId = re.compile('"providerId":"(.+?)"').search(html).group(1)
            vidurl = getBrightCoveUrl(videoId)
            retry = 0

          except:
            retry -= 1
            if (retry != 0) and (addon.getSetting('us_proxy_enable') == 'true'):
               dontuseproxy = False
               continue
            else:
               dialog = xbmcgui.Dialog()
               dialog.ok(__language__(30000), '',__language__(30001))
               return

    vidurl = vidurl.encode(UTF8)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=vidurl))


def getBrightCoveUrl(video_content_id):
      html = getRequest('http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=1678873430001' % (video_content_id))
      html = html+'#'
      vids = re.compile('BANDWIDTH=([0-9]*).+?http(.+?)#').findall(html)
      b = 0
      furl = ''
      if (addon.getSetting('vid_res') == "1"):
        for bwidth, url in vids:
          if (int(bwidth) > b):
              b = int(bwidth)
              furl = url
      else: furl = vids[0][1]

      if (furl == ''): raise Exception('No Video')
      return 'http'+furl



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

mode = p('mode', None)

if mode==  None:  getSources()
elif mode=='GV':  getVideo(p('url'))
elif mode=='GS':  getShows(p('url'),p('channame'))
elif mode=='GC':  getChannel(p('url'),p('iconimage'),p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

