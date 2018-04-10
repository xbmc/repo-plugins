#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Sky News.
#
# Sky News is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sky News is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sky News.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, re, sys, time, datetime, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from simplecache import SimpleCache
from bs4 import BeautifulSoup

# Plugin Info
ADDON_ID      = 'plugin.video.skynews'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT      = 15
CONTENT_TYPE = 'files'
DEBUG        = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
LIVEURL      = 'http://news.sky.com/watch-live'
YTURL        = 'plugin://plugin.video.youtube/play/?video_id='

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
                        
socket.setdefaulttimeout(TIMEOUT)
class Sky(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()

            
    def openURL(self, url):
        log('openURL, url = ' + str(url))
        try:
            cacheResponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheResponse:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib2.urlopen(request, timeout=TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(hours=6))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except Exception as e: log("openURL Failed! " + str(e), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
        return ''
         

    def buildMainMenu(self):
        self.addLink(LANGUAGE(30002),'',0)
        self.addYoutube(LANGUAGE(30003),'plugin://plugin.video.youtube/user/skynews/')
            
          
    def buildLiveLink(self):
        try:
            link = 'http:' + BeautifulSoup(self.openURL(LIVEURL), "html.parser")('div', {'class': 'video-embed'})[0].find('iframe').get('src')
            print self.resolveYoutube(link)
            self.playVideo(LANGUAGE(30004),self.resolveYoutube(link))
        except: self.playVideo(LANGUAGE(30004),YTURL + 'XOacA3RYrXk')
        
    def resolveYoutube(self, link):
        if len(re.findall('http[s]?://www.youtube.com/watch', link)) > 0: return YTURL + link.split('/watch?v=')[1]
        elif len(re.findall('http[s]?://www.youtube.com/embed', link)) > 0: return YTURL + link.split('/embed/')[1].split('?autoplay=1')[0]
        elif len(re.findall('http[s]?://youtu.be/', link)) > 0: return YTURL + link.split('/youtu.be/')[1] 

        
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        if not liz: liz = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


    def addYoutube(self, title, url):
        liz=xbmcgui.ListItem(title)
        liz.setProperty('IsPlayable', 'false')
        liz.setInfo(type="Video", infoLabels={"label":title,"title":title} )
        liz.setArt({'thumb':ICON,'fanart':FANART})
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=True)

        
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name,"genre":"News"})
        else: liz.setInfo(type="Video", infoLabels=infoList) 
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)

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

if mode==None:  Sky().buildMainMenu()
elif mode == 0: Sky().buildLiveLink()
elif mode == 9: Sky().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)