#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of Haystack.TV.
#
# Haystack.TV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Haystack.TV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Haystack.TV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, datetime, re, traceback
import urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from simplecache import SimpleCache
from bs4 import BeautifulSoup
from YDStreamExtractor import getVideoInfo

# Plugin Info
ADDON_ID      = 'plugin.video.haystacktv'
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
BASEURL       = 'http://www.haystack.tv'
YTURL         = 'plugin://plugin.video.youtube/play/?video_id='
VMURL         = 'plugin://plugin.video.vimeo/play/?video_id='
IGNORE        = ', watch it on the web, Android, iPad and Chromecast.'
# MY HEADLINES,EDITOR'S PICKS,NEWS,SCITECH,ENTERTAINMENT,BUSINESS,U.S.POLITICS,SPORTS,GAMING,LATE NIGHT,MOVIES,POPULAR

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
class Haystack():
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()
        self.getCategories()

        
    def openURL(self, url):
        try:
            cacheResponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheResponse:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib2.urlopen(request, timeout=TIMEOUT)
                soup = BeautifulSoup(response.read(), "html.parser")
                data = (soup.find('script').text).rstrip()
                data = (data.split('window.__INITIAL_STATE__ = ')[1]).replace(';','')
                response.close()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, data, expiration=datetime.timedelta(hours=1))
            return json.loads(self.cache.get(ADDON_NAME + '.openURL, url = %s'%url))
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
            
        
    def mainMenu(self):
        log('mainMenu')
        for item in self.catMenu: self.addDir(*item)

        
    def resolveHAY(self, url, all=False):
        log('resolveHAY')
        responce = self.openURL(url)
        if responce and 'videos' in responce and 'videoList' in responce['videos']:
            for item in responce['videos']['videoList']:
                if item and 'mediaFiles' in item and 'adaptive' in item['mediaFiles'] and not all:
                    if item['mediaFiles']['adaptive']['type'] == 'm3u8': return item['mediaFiles']['adaptive']['url']
                    else:
                        info = self.getVideo(url)
                        if info is not None: return info[0]['xbmc_url']
        return None
        
        
    def resolveURL(self, provider, url):
        log('resolveURL, provider = ' + provider + ', url = ' + url)
        if provider.lower() == 'youtube':       
            if len(re.findall('http[s]?://www.youtube.com/watch', url)) > 0: return YTURL + url.split('/watch?v=')[1]
            elif len(re.findall('http[s]?://youtu.be/', url)) > 0: return YTURL + url.split('/youtu.be/')[1]
        elif provider.lower() == 'vimeo':
            if len(re.findall('http[s]?://vimeo.com/', url)) > 0: return VMURL + url.split('/vimeo.com/')[1]
        elif provider.lower() == 'haystack': return self.resolveHAY(url)
        return None

       
    def getVideo(self, url):
        cacheresponse = self.cache.get(ADDON_NAME + '.getVideo, url = %s'%url)
        if not cacheresponse:
            info = getVideoInfo(url,QUALITY,True)
            if info is not None: info = info.streams()
            self.cache.set(ADDON_NAME + '.getVideo, url = %s'%url, json.dumps(info), expiration=datetime.timedelta(days=14))
        return json.loads(self.cache.get(ADDON_NAME + '.getVideo, url = %s'%url))
        
                    
    def getVideos(self, cat, today=True):
        log('getVideos')
        responce = self.openURL(BASEURL)
        if today == False and responce and 'categories' in responce and 'categoryPlaylists' in responce['categories']:
            results = responce['categories']['categoryPlaylists']
            for items in results:
                if cat.lower() == items['sectionTitle'].lower(): self.getLinks(items['streams'])
        elif today == True and responce and 'videos' in responce and 'videoList' in responce['videos']: self.getLinks(responce['videos']['videoList'])
            
                 
    def getCategories(self):
        log('getCategories')
        responce = self.openURL(BASEURL)
        if responce and 'videos' in responce and 'playlistHeader' in responce['videos']:
            self.catMenu = [(responce['videos']['playlistHeader'],'',0)]
        if responce and 'categories' in responce and 'categoryPlaylists' in responce['categories']:
            for item in responce['categories']['categoryPlaylists']:
                infoLabel = {}
                title = responce['environment']['sitemap'][item['relativeUrl']]['sectionTitle']
                infoLabel['label'] = title
                infoLabel['title'] = title
                infoLabel['plot']  = responce['environment']['sitemap'][item['relativeUrl']]['description'].replace(IGNORE,'.')
                infoLabel['plotoutline'] = responce['environment']['sitemap'][item['relativeUrl']]['pageTitle'].replace(IGNORE,'.')
                infoLabel['genre'] = responce['environment']['sitemap'][item['relativeUrl']]['alias']
                self.catMenu.append((title,title,1,infoLabel))

   
    def getLinks(self, items):
        log('getLinks')
        for item in items:
            tagLST = []
            infoLabel = {}
            infoArt   = {}
            title = item['title']
            path  = self.resolveURL(item['site'],item['streamUrl'])
            if path is None: continue
            for tag in item['topics']:
                tagLST.append(tag['tag'])
            infoLabel['tag']      = tagLST
            infoLabel['mediatype']= 'video'
            infoLabel['duration'] = item['duration']
            infoLabel['label']    = item['title']
            infoLabel['title']    = title
            infoLabel['plot']     = title
            infoLabel['studio']   = item['author']
            infoLabel['genre']    = item['category'].title() 
            infoLabel['rating']   = item['popularityScore']
            infoLabel['aired']    = item['publishedDate'].split('T')[0]
            thumb   = (item.get('snapshotHighUrl','') or item.get('snapshotUrl','') or ICON)
            infoArt ={"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}    
            self.addLink(title, path, 9, infoLabel, infoArt)    
                        

    def playVideo(self, name, url, liz=None):
        log('playVideo')
        if liz is None: liz = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
           
           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':LOGO_URL%urllib.quote_plus(name),'fanart':FANART})
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
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART}) #LOGO_URL%urllib.quote_plus(name)
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

if mode==None:  Haystack().mainMenu()
elif mode == 0: Haystack().getVideos(name)
elif mode == 1: Haystack().getVideos(name, False)
elif mode == 9: Haystack().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)