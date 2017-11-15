#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of CNN.
#
# CNN is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CNN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CNN.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback
import urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from YDStreamExtractor import getVideoInfo
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.cnn'
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
BASE_URL      = 'http://www.cnn.com'
SHORTS_URL    = 'http://www.cnn.com/specials/videos/digital-shorts'
JSON_URL      = 'http://www.cnn.com/video/data/3.0/video/%s/relateds.json'
MENU_ITEMS    = ['Business', 'Entertainment', 'Health', 'Justice', 'Living', 'CNNMoney', 'Politics', 'Style', 'Technology', 'Travel', 'TV', 'US', 'World', 'Weather']

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    param=[]
    if len(sys.argv[2])>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'): params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2: param[splitparams[0]]=splitparams[1]
    return param
                 
socket.setdefaulttimeout(TIMEOUT)
class CNN(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()
           
           
    def openURL(self, url):
        log('openURL, url = ' + str(url))
        try:
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                request = urllib2.Request(url)
                response = urllib2.urlopen(request, timeout = TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(hours=1))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
         
    def buildMenu(self):
        for item in MENU_ITEMS: self.addDir(item, JSON_URL%item.lower(), 1)
        self.addDir('Digital Shorts', SHORTS_URL, 2)
        self.addYoutube("Browse Youtube" , 'plugin://plugin.video.youtube/user/CNN/')
            
            
    def browse(self, name, url):
        log('browse, ' + name)
        response = json.loads(self.openURL(url))
        items = response['videos']
        for item in items:          
            try:
                runtime = item['duration'].split(':')
                if len(runtime) == 3:
                    h, m, s = runtime
                    duration = int(h) * 3600 + int(m) * 60 + int(s)
                else:
                    m, s = runtime   
                    duration = int(m) * 60 + int(s)
            except: duration = item['duration']
            label        = item['headline']
            thumb        = 'http:%s'%item['fullsize_url']
            infoLabels   = {"mediatype":"episode","label":label ,"title":label,"duration":duration,"plot":item['description'],"genre":"News"}
            infoArt      = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
            self.addLink(label, BASE_URL + item['clickback_url'], 9, infoLabels, infoArt, len(items))


    def browseShorts(self, name, url):
        log('browseShorts, ' + name)
        soup   = BeautifulSoup(self.openURL(url), "html.parser")
        videos = soup('article', {'class': 'cd'})
        for video in videos:
            vid_url = video('h3', {'class': 'cd__headline'})[0].find('a')['href']
            if not vid_url.startswith('http'): vid_url = BASE_URL + vid_url
            if vid_url.startswith('http://cnn.it'): continue
            if not '/video' in vid_url: continue
            thumb = (video('div', {'class': 'cd__wrapper'})[0])
            try: thumb = 'http:' + (json.loads((re.search('"large":(.*?)"},', str(thumb)).group(1) + '"}'))['uri'])
            except: thumb = ICON
            results = video('div', {'class': 'cd__content'})[0]
            try: title = results('div', {'class': 'cd__kicker'})[0].get_text()
            except: title = None
            subtitle = results('span', {'class': 'cd__headline-text'})[0].get_text()
            label = '%s - %s'%(title, subtitle) if title is not None else subtitle
            try: plot = results('div', {'class': 'cd__description'})[0].get_text()
            except: plot = subtitle
            duration   = 0
            infoLabels = {"mediatype":"episode","label":label ,"title":label,"duration":duration,"plot":plot}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
            self.addLink(label, vid_url, 9, infoLabels, infoArt, len(videos))

                
    def playVideo(self, name, url, liz=None):
        log('playVideo')
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

if mode==None:  CNN().buildMenu()
elif mode == 1: CNN().browse(name, url)
elif mode == 2: CNN().browseShorts(name, url)
elif mode == 9: CNN().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)