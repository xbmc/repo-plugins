#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Looper.
#
# Looper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Looper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Looper.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.looper'
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
CONTENT_TYPE  = 'files'
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
BASE_URL      = 'http://www.looper.com/category/videos/?ajax=1&offset=%s'
YTURL         = 'plugin://plugin.video.youtube/play/?video_id=%s'
             
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))

socket.setdefaulttimeout(TIMEOUT)  
class Looper(object):
    def __init__(self):
        log('__init__')
        self.cache   = SimpleCache()

           
    def openURL(self, url):
        try:
            log('openURL, url = ' + str(url))
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                cacheresponse = urllib2.urlopen(urllib2.Request(url), timeout=TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, cacheresponse, expiration=datetime.timedelta(minutes=15))
            return cacheresponse
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         

    def buildMenu(self):
        self.addDir(LANGUAGE(30003), BASE_URL%'01', 1)
        self.addYoutube(LANGUAGE(30006), 'plugin://plugin.video.youtube/channel/UCP1iRaFlS5EYjJBryFV9JPw/')
        
        
    def browse(self, url):
        log('browse, url = ' + str(url))
        soup   = BeautifulSoup(self.openURL(url), "html.parser")
        videos = soup('article', {'class': 'article-block'})
        for video in videos:
            link  = video('div', {'class': 'image-holder'})[0].find('a').attrs['href']
            thumb = video('div', {'class': 'image-holder'})[0].find('img').attrs['src']
            label = plot = video('div', {'class': 'description'})[0].find('a').get_text()
            infoLabels = {"mediatype":"video","label":label ,"title":label,"plot":plot}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
            self.addLink(label, link, 9, infoLabels, infoArt, len(videos))
        next_offset = int(url[-2:]) + 13
        self.addDir(LANGUAGE(30004)%((next_offset//13) + 1), BASE_URL%(str(next_offset)), 1)
            

    def playVideo(self, name, url):
        log('playVideo')
        soup = BeautifulSoup(self.openURL(url), "html.parser")
        url  = soup('div', {'class': 'image-holder'})[0].find('iframe').attrs['src']
        if len(re.findall('http[s]?://www.youtube', url)) > 0: url = YTURL%(url.rsplit('/',1)[1]).split('?')[0]
        elif len(re.findall('http[s]?://youtu.be/', url)) > 0: url = YTURL%(url.split('/youtu.be/')[1]).split('?')[0]
        else: return
        liz  = xbmcgui.ListItem(name, path=url)
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

if mode==None:  Looper().buildMenu()
elif mode == 1: Looper().browse(url)
elif mode == 2: Looper().buildChannels()
elif mode == 9: Looper().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)