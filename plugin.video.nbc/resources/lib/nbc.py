#   Copyright (C) 2019 Lunatixz
#
#
# This file is part of NBC.
#
# NBC is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NBC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NBC.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback, inputstreamhelper
import urllib, urllib2, socket, json, urlparse
import xbmc, xbmcaddon, xbmcplugin, xbmcgui

from YDStreamExtractor import getVideoInfo
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.nbc'
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
BASE_URL      = 'http://www.nbc.com'
SHOW_URL      = 'https://api.nbc.com/v3.14/aggregatesShowProperties/%s'
SHOWS_URL     = 'https://api.nbc.com/v3.14/shows?filter[active]=1&include=image&page[size]=30&sort=sortTitle'
VIDEO_URL     = 'https://api.nbc.com/v3.14/videos?filter[entitlement]=free&filter[published]=1&include=image&page[size]=30&sort=-airdate'
FILTER        = '&filter[%s]=%s'

MAIN_MENU = [(LANGUAGE(30002), "", 1),
             (LANGUAGE(30003), "", 2)]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
  
socket.setdefaulttimeout(TIMEOUT)
class NBC(object):
    def __init__(self, sysARG):
        log('__init__, sysARG = ' + str(sysARG))
        self.sysARG = sysARG
        if self.chkUWP(): return
        self.cache  = SimpleCache()
           
           
    def chkUWP(self):
        isUWP = (xbmc.getCondVisibility("system.platform.uwp") or sys.platform == "win10" or re.search(r"[/\\]WindowsApps[/\\]XBMCFoundation\.Kodi_", xbmc.translatePath("special://xbmc/")))
        if isUWP: return xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30006), ICON, 4000)
        return isUWP
        
        
    def openURL(self, url):
        try:
            log('openURL, url = ' + str(url))
            if DEBUG: cacheresponse = None
            else: cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                cacheresponse = urllib2.urlopen(urllib2.Request(url), timeout=TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, cacheresponse, expiration=datetime.timedelta(minutes=15))
            return cacheresponse
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
         
    def buildMenu(self, items):
        for item in items: self.addDir(*item)
        self.addYoutube(LANGUAGE(30004), 'plugin://plugin.video.youtube/user/NBC/')

            
    def browseEpisodes(self, url=None):
        log('browseEpisodes')
        if url is None: url = VIDEO_URL+FILTER%('type','Full%20Episode')
        items = json.loads(self.openURL(url))
        if items and 'data' in items:
            for item in items['data']:
                path      = item['attributes']['fullUrl']
                aired     = str(item['attributes']['airdate']).split('T')[0]
                duration  = int(item['attributes']['runTime'])
                plot      = item['attributes']['description']
                title     = item['attributes']['title']
                
                showTitle = '' 
                for show in item['attributes']['categories']: 
                    if show.startswith('Series'):
                        showTitle = show.split('Series/')[1]
                        break

                try: episodeNumber = int(item['attributes']['episodeNumber'])
                except: episodeNumber = 0
                try: seasonNumber = int(item['attributes']['seasonNumber'])
                except: seasonNumber  = 0
                
                try: 
                    thumb = ICON
                    for image in items['included']:
                        if image['id'] == item['relationships']['image']['data']['id']:
                            thumb = BASE_URL+image['attributes']['path']
                            break
                except: thumb = ICON
                
                seinfo = ('S' + ('0' if seasonNumber < 10 else '') + str(seasonNumber) + 'E' + ('0' if episodeNumber < 10 else '') + str(episodeNumber))
                label  = '%s - %s'%(showTitle, title) if seasonNumber + episodeNumber == 0 else '%s - %s - %s'%(showTitle, seinfo, title)
                infoLabels ={"mediatype":"episodes","label":label ,"title":label,"TVShowTitle":showTitle,"plot":plot,"aired":aired,"duration":duration,"season":seasonNumber,"episode":episodeNumber}
                infoArt    ={"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
                self.addLink(label, path, 9, infoLabels, infoArt, len(items['data']))
                
            try: next_page = items['links']['next']
            except: next_page = None
            if next_page:
                 self.addDir('>> Next',next_page, 1)

                 
    def browseShows(self, url=None):
        log('browseShows')
        if url is None: url = SHOWS_URL
        items = json.loads(self.openURL(url))
        if items and 'data' in items:
            for item in items['data']:
                showTitle = item['attributes']['shortTitle']
                plot      = (item['attributes']['shortDescription'] or showTitle).replace('<p>','').replace('</p>','')
                path      = VIDEO_URL+FILTER%('show',item['id'])
                vidID     = item['relationships']['aggregates']['data']['id']

                try: 
                    thumb = ICON
                    for image in items['included']:
                        if image['id'] == item['relationships']['image']['data']['id']:
                            thumb = BASE_URL + image['attributes']['path']
                            break
                except: thumb = ICON
                
                myURL      = json.dumps({"url":path,"vidID":vidID})
                infoLabels ={"mediatype":"tvshows","label":showTitle ,"title":showTitle,"TVShowTitle":showTitle,"plot":plot}
                infoArt    ={"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
                self.addDir(showTitle,myURL,0,infoLabels,infoArt)

            try: next_page = items['links']['next']
            except: next_page = None
            if next_page:
                 self.addDir('>> Next',next_page, 2)
 

    def buildShow(self, url):
        log('buildShow')
        myURL = json.loads(url)
        items = json.loads(self.openURL(SHOW_URL%myURL['vidID']))
        if items and 'data' in items:
            for item in items['data']['attributes']['videoTypes']:
                self.browseEpisodes(myURL['url']+FILTER%('type',urllib2.quote(item)))
                
                
    @use_cache(28)
    def resolveURL(self, url):
        log('resolveURL')
        return getVideoInfo(url,QUALITY,True).streams()
    
    
    def playVideo(self, name, url):
        log('playVideo')
        info = self.resolveURL(url)
        if info is None: return
        url = info[0]['xbmc_url']
        liz = xbmcgui.ListItem(name, path=url)
        if 'm3u8' in url.lower() and inputstreamhelper.Helper('hls').check_inputstream() and not DEBUG:
            liz.setProperty('inputstreamaddon','inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type','hls')
        if 'subtitles' in info[0]['ytdl_format']: liz.setSubtitles([x['url'] for x in info[0]['ytdl_format']['subtitles'].get('en','') if 'url' in x])
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)

            
    def addYoutube(self, name, url):
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        liz.setInfo(type="Video", infoLabels={"label":name,"title":name} )
        liz.setArt({'thumb':ICON,'fanart':FANART})
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=url,listitem=liz,isFolder=True)
        
           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name,"genre":"News"})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name,"genre":"News"})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)


    def getParams(self):
        return dict(urlparse.parse_qsl(self.sysARG[2][1:]))

            
    def run(self):  
        params=self.getParams()
        try:url=urllib.unquote_plus(params["url"])
        except: url=None
        try: name=urllib.unquote_plus(params["name"])
        except: name=None
        try: mode=int(params["mode"])
        except: mode=None
        log("Mode: "+str(mode))
        log("URL : "+str(url))
        log("Name: "+str(name))

        if mode==None:  self.buildMenu(MAIN_MENU)
        elif mode == 0: self.buildShow(url)
        elif mode == 1: self.browseEpisodes(url)
        elif mode == 2: self.browseShows(url)
        elif mode == 9: self.playVideo(name, url)
            
        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=True)