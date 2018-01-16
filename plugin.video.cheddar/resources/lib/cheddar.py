#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Cheddar
#
# Cheddar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cheddar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cheddar. If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, datetime, re, traceback
import urlparse, urllib, urllib2, socket
import xbmc, xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon

from YDStreamExtractor import getVideoInfo
from simplecache import SimpleCache, use_cache
from bs4 import BeautifulSoup

# Plugin Info
ADDON_ID      = 'plugin.video.cheddar'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT       = 30
BASEURL       = 'http://cheddar.com/'
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
QUALITY       = int(REAL_SETTINGS.getSetting('Quality'))
CONTENT_TYPE  = 'episodes'

Cheddar_MENU  = [("Latest" , 'collections/latest', 1),
                 ("Browse" , 'collections'       , 1)]
            
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
    
socket.setdefaulttimeout(TIMEOUT)
class Cheddar(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()
        
        
    def openURL(self, url):
        try:
            cacheResponce = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheResponce:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib2.urlopen(request, timeout=TIMEOUT)
                results = response.read()
                response.close()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, results, expiration=datetime.timedelta(hours=12))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except urllib2.URLError as e: log("openURL Failed! " + str(e), xbmc.LOGERROR)
        except socket.timeout as e: log("openURL Failed! " + str(e), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
        return ''
        
        
    def mainMenu(self):
        log('mainMenu')
        self.addLink('Live', '', 0)
        for item in Cheddar_MENU: self.addDir(*item)
        self.addYoutube("Browse Youtube" , 'plugin://plugin.video.youtube/channel/UC04KsGq3npibMCE9Td3mVDg/')
        
        
    def browseLive(self):
        log('browseLive')
        soup = BeautifulSoup(self.openURL(BASEURL), "html.parser")
        liveLink = soup('div', {'class': 'hero_video'})[0].find('source').get('src')
        self.playVideo('Live', liveLink)

        
    def browse(self, link):
        log('browse')
        soup = BeautifulSoup(self.openURL(BASEURL + link), "html.parser")
        latestLink = (soup('div', {'class': 'video_thumb'}))
        for item in latestLink:
            uriLink = item('a', {'class': 'cf'})[0]
            uri = BASEURL + uriLink['href']
            thumb = uriLink('div', {'class': 'vid_img'})[0].find_all('img')[0].get('src')
            airdate, title = uriLink.text.strip().replace('\r','').replace('\t','').split('\n')
            label = title.strip()
            plot  = '%s [CR]Aired: %s'%(label, airdate)
            try: airdate = datetime.datetime.strptime(airdate, "%B %d, %Y")
            except: airdate = datetime.datetime.now()
            airdate = airdate.strftime('%Y-%m-%d')
            infoList = {"mediatype":"episode","label":label,"title":label,"plot":plot,'genre':'News',"studio":"cheddar","aired":airdate}
            infoArt  = {"thumb":thumb,"poster":thumb,"fanart":FANART}
            self.addLink(label, uri, 9, infoList, infoArt)
                

    def playVideo(self, name, url):
        log('playVideo, name = ' + name)
        if name == 'Live': liz = xbmcgui.ListItem(name, path=url)
        else:
            info = getVideoInfo(url,QUALITY,True)
            if info is None: return
            info = info.streams()
            url  = info[0]['xbmc_url']
            liz  = xbmcgui.ListItem(name, path=url)
            if 'subtitles' in info[0]['ytdl_format']: liz.setSubtitles([x['url'] for x in info[0]['ytdl_format']['subtitles'].get('en','') if 'url' in x])   
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
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name} )
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

if mode==None:  Cheddar().mainMenu()
elif mode == 0: Cheddar().browseLive()
elif mode == 1: Cheddar().browse(url)
elif mode == 9: Cheddar().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)