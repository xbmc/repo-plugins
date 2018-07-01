#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Easy Engineering TV.
#
# Easy Engineering TV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Easy Engineering TV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Easy Engineering TV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from YDStreamExtractor import getVideoInfo
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.easyengineering'
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
QUALITY       = int(REAL_SETTINGS.getSetting('Quality'))
BASE_URL      = 'http://easyengineeringtv.com/%s'
MAIN_MENU     = [(LANGUAGE(30003), BASE_URL%'videos/'                     , 0),
                 (LANGUAGE(30005), BASE_URL%'category/news/'              , 1),
                 (LANGUAGE(30006), BASE_URL%'category/slider-videos/'     , 1),
                 (LANGUAGE(30007), BASE_URL%'category/industry/'          , 1),
                 (LANGUAGE(30008), BASE_URL%'category/documentary/'       , 1),
                 (LANGUAGE(30009), BASE_URL%'category/behind-the-machine/', 1),
                 (LANGUAGE(30010), BASE_URL%'category/events/'            , 1),
                 (LANGUAGE(30011), BASE_URL%'category/uncategorized/'     , 1),
                 (LANGUAGE(30012), BASE_URL%'category/tv-online/'         , 1)]
        
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))

socket.setdefaulttimeout(TIMEOUT)  
class EasyTV(object):
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
        for item in MAIN_MENU: self.addDir(*item)
        self.addYoutube(LANGUAGE(30013), 'plugin://plugin.video.youtube/channel/UCP2Q1YpGGz1nBQmXT6GvI2Q/')
        
        
    def browse(self, name, url):
        log('browse, url = ' + str(url))
        soup = BeautifulSoup(self.openURL(url), "html.parser")
        videos = soup('div', {'class': 'col-md-3'})
        for video in videos:
            try:
                link  = video('div', {'class': 'item-thumbnail'})[0].find('a').attrs['href']
                thumb = video('div', {'class': 'item-thumbnail'})[0].find('img').attrs['src']
                label = video('div', {'class': 'item-thumbnail'})[0].find('img').attrs['alt'].strip()
                aired = video('span', {'class': 'item-date'})[0].get_text().strip()
                plot  = '%s - %s'%(aired,label)
                try: airdate = datetime.datetime.strptime(aired, '%B %d, %Y')
                except: airdate = datetime.datetime.now()
                airdate = airdate.strftime('%Y-%m-%d')
                infoLabels = {"mediatype":"episode","label":label,"title":label,"plot":plot,"aired":airdate}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
                self.addLink(label, link, 9, infoLabels, infoArt, len(videos))
            except: pass
        next_offset = re.compile("(.*)/(.*?)/").match(url).groups()[1]
        if next_offset.isdigit(): next_offset = int(next_offset) + 1
        else: next_offset = 2
        self.addDir(LANGUAGE(30014)%str(next_offset), BASE_URL%'videos/page/%s/'%next_offset, 0)
            

    def browseCategories (self, genre, url):
        log('browseCategories, url = ' + str(url))
        soup   = BeautifulSoup(self.openURL(url), "html.parser")
        videos = soup('div', {'class': 'col-md-6'})
        for video in videos:
            try:
                link  = video('a', {'class': 'maincolor2hover'})[0].attrs['href']
                id    = re.compile("http://easyengineeringtv.com/(.*?)/(.*?)/(.*?)/(.*?)/").match(link).groups()
                thumb = 'http://easyengineeringtv.com/wp-content/uploads/%s/%s/%s-139x89.jpg'%(id[0],id[1],id[3])
                label = plot = video('a', {'class': 'maincolor2hover'})[0].get_text().strip()
                infoLabels = {"mediatype":"video","label":label,"title":label,"plot":plot,"genre":genre}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
                self.addLink(label, link, 9, infoLabels, infoArt, len(videos))
            except: pass
           
           
    def playVideo(self, name, url):
        log('playVideo')
        info = getVideoInfo(url,QUALITY,True)
        if info is None: return
        info = info.streams()
        url  = info[0]['xbmc_url']
        liz  = xbmcgui.ListItem(name, path=url)
        if 'm3u8' in url.lower():
            liz.setProperty('inputstreamaddon','inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type','hls')
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

if mode==None:  EasyTV().buildMenu()
elif mode == 0: EasyTV().browse(name, url)
elif mode == 1: EasyTV().browseCategories(name, url)
elif mode == 2: EasyTV().buildChannels()
elif mode == 9: EasyTV().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)