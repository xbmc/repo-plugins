#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of ScreenRant.
#
# ScreenRant is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ScreenRant is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ScreenRant.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.screenrant'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT       = 15
CONTENT_TYPE  = 'episodes'
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
QUALITY       = int(REAL_SETTINGS.getSetting('Quality'))
BASE_URL      = 'https://www.screenrant.com'
VIDEO_URL     = 'https://secure.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=%s&secure=true'
MAIN_MENU     = [(LANGUAGE(30003),'/video', 1),
                 (LANGUAGE(30004),'/video', 1)]
             
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))

socket.setdefaulttimeout(TIMEOUT)  
class ScreenRant(object):
    def __init__(self):
        log('__init__')
        self.cache   = SimpleCache()

           
    def openURL(self, url):
        try:
            log('openURL, url = ' + str(url))
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                cacheresponse = urllib2.urlopen(request, timeout=TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, cacheresponse, expiration=datetime.timedelta(minutes=15))
            return cacheresponse
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         

    def buildMenu(self, items):
        for item in items: self.addDir(*item)
        self.addYoutube(LANGUAGE(30006), 'plugin://plugin.video.youtube/user/ScreenRant/')
        
        
    def browse(self, name, url):
        log('browse, name = ' + name)
        soup   = BeautifulSoup(self.openURL(BASE_URL+url), "html.parser")
        videos = soup('div', {'class': 'w-browse-clip'})
        if name == LANGUAGE(30004): idx = 1
        else: idx = 0
        videos = videos[idx]('article', {'class': 'browse-clip'})
        for video in videos:
            link  = BASE_URL+ video.find('a').attrs['href']
            thumb = video('div', {'class': 'responsive-img'})[0].find('source').attrs['srcset']
            try: label = video('h3', {'class': 'bc-title'})[0].find('a').attrs['title']
            except: label = (video('div', {'class': 'info-wrapper'})[0].find('a').get_text())
            try: airdate = datetime.datetime.strptime(video('div', {'class': 'bc-details'})[0].find('time').get_text(), '%b %d, %Y')
            except: airdate = datetime.datetime.now()
            airdate = airdate.strftime('%Y-%m-%d')
            plot    = '%s - %s'%(label,airdate)
            try: 
                dur = (video('a', {'class': 'bc-img-link'})[0].find('span').get_text()).split(':')
                if len(dur) == 3:
                    h, m, s = dur
                    duration  = int(h) * 3600 + int(m) * 60 + int(s)
                else:
                    m, s = dur   
                    duration  = int(m) * 60 + int(s)
            except: duration = '0'
            infoLabels = {"mediatype":"episode","label":label ,"title":label,"duration":duration,"plot":plot,"aired":airdate}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
            vidID      = thumb.split('/')[9].split('-')
            link       = VIDEO_URL%(vidID[5].split('_')[2],vidID[2])            
            self.addLink(label, link, 9, infoLabels, infoArt, len(videos))

        next = soup('div', {'class': 'wp-pagenavi'})
        if name == LANGUAGE(30004) or len(next) == 0: return
        current_pg = int(next[0]('span', {'class': 'current'})[0].get_text())
        next_url   = '/video/page/%s'%(str(current_pg+1))
        next_label = next[0]('span', {'class': 'pages'})[0].get_text()
        self.addDir(next_label, next_url, 1)
        
        
    def playVideo(self, name, url):
        log('playVideo')
        liz  = xbmcgui.ListItem(name, path=url)
        liz.setProperty('inputstreamaddon','inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.manifest_type','hls') 
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        
        
    def addYoutube(self, name, url):
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        liz.setInfo(type="Video", infoLabels={"label":name,"title":name} )
        liz.setArt({'thumb':ICON,'fanart':FANART})
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=True)
        
           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
     
params=getParams()
try: url=urllib.unquote_plus(params["url"])
except: url=None
try: name=urllib.unquote_plus(params["name"])
except: name=None
try: mode=int(params["mode"])
except: mode=None
log("Mode: "+str(mode))
log("URL : "+str(url))
log("Name: "+str(name))

if mode==None:  ScreenRant().buildMenu(MAIN_MENU)
elif mode == 1: ScreenRant().browse(name, url)
elif mode == 9: ScreenRant().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)