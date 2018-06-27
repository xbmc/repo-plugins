#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Wired.
#
# Wired is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Wired is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Wired.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.wired'
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
mType         = int(REAL_SETTINGS.getSetting('Type'))
BASE_URL      = 'https://video.wired.com'
MAIN_MENU     = {(LANGUAGE(30003),BASE_URL+'/new'    ,1),
                 (LANGUAGE(30004),BASE_URL+'/popular',1),
                 (LANGUAGE(30005),BASE_URL+'/series' ,2),
                 (LANGUAGE(30006),BASE_URL+'/genres' ,3)}
             
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
socket.setdefaulttimeout(TIMEOUT)  
class Wired(object):
    def __init__(self, sysARG):
        log('__init__')
        self.cache   = SimpleCache()
        self.sysARG  = sysARG
           
           
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
        self.addYoutube(LANGUAGE(30007), 'plugin://plugin.video.youtube/channel/UCftwRNsjfRo08xYE31tkiyw/')
        
        
    def buildSeries(self, url):
        log('buildSeries, url = ' + str(url))
        soup  = BeautifulSoup(self.openURL(url), "html.parser")
        shows = soup('div', {'class': 'cne-thumb cne-series'})
        for show in shows: 
            link  = BASE_URL+show('a', {'class': 'cne-thumbnail cne-series'})[0].attrs['href']
            label = show('p', {'class': 'cne-series-title'})[0].get_text().strip()
            plot  = show('span', {'class': 'cne-thumb-description'})[0].get_text().strip()
            thumb = show.find('img').attrs['src']
            infoLabels = {"mediatype":"video","label":label,"title":label,"plot":plot}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
            self.addDir(label, link, 1, infoLabels, infoArt)
            
            
    def buildGenres(self, url):
        log('buildGenres, url = ' + str(url))
        soup   = BeautifulSoup(self.openURL(url), "html.parser")
        cats = soup('li', {'class': 'cne-nav--drawer__item--categories'})
        for cat in cats: 
            link  = BASE_URL+cat('a', {'class': 'js-nav-drawer-menu-item'})[0].attrs['href']
            label = cat('a', {'class': 'js-nav-drawer-menu-item'})[0].attrs['aria-label'].strip()
            thumb = 'http:%s'%cat.find('img').attrs['src']
            infoLabels = {"mediatype":"video","label":label,"title":label}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
            self.addDir(label, link, 1, infoLabels, infoArt)
   
        
    def browse(self, url):
        log('browse, url = ' + str(url))
        soup   = BeautifulSoup(self.openURL(url), "html.parser")
        videos = soup('div', {'class': 'cne-thumb'})
        for video in videos:
            link  = BASE_URL+video('a', {'class': 'js-ajax-video-load'})[0].attrs['href']
            thumb = video('a', {'class': 'cne-thumbnail js-ajax-video-load'})[0].find('img').attrs['src']
            genre = video('p', {'class': 'cne-rollover-category'})[0].get_text().strip()
            label = video('a', {'class': 'cne-thumbnail js-ajax-video-load'})[0].find('img').attrs['alt'].strip()
            plot  = ((str(video('div', {'class': 'cne-rollover-description'})[0]).split('</p>\n')[1] or label).strip()).split('</div>')[0]
            infoLabels = {"mediatype":"video","label":label,"title":label,"plot":plot,"genre":genre}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
            self.addLink(label, link, 9, infoLabels, infoArt, len(videos))
        next = soup('a', {'class': 'js-cne-ajax cne-more-button cne-more-videos cne-light-button'})
        if len(next) == 0: return
        next_url   = '%s?%s'%(url.split('?')[0],next[0].attrs['data-ajaxurl'].split('?')[1])
        next_label = LANGUAGE(30008)%(next_url.split('=')[1])
        self.addDir(next_label, next_url, 1)  
        
        
    def resolveURL(self, url):
        soup  = BeautifulSoup(self.openURL(url), "html.parser")
        items = soup('div', {'class': 'cne-video'})[0].find_all('meta')
        for item in items:
            url = item.attrs['content']
            if url.endswith(('mp4','m3u8')): break
        if mType == 1: url = url.replace('low.mp4','manifest-ios.m3u8')
        return url
        
            
    def playVideo(self, name, url):
        log('playVideo')
        liz  = xbmcgui.ListItem(name, path=self.resolveURL(url))
        if 'm3u8' in url.lower():
            liz.setProperty('inputstreamaddon','inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type','hls')
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
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
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
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)
     
              
    def getParams(self):
        return dict(urlparse.parse_qsl(self.sysARG[2][1:]))

            
    def run(self):  
        params=self.getParams()
        try: url=urllib.unquote_plus(params["url"])
        except: url=None
        try: name=urllib.unquote_plus(params["name"])
        except: name=None
        try: mode=int(params["mode"])
        except: mode=None
        log("Mode: "+str(mode))
        log("URL : "+str(url))
        log("Name: "+str(name))

        if mode==None:  self.buildMenu()
        elif mode == 1: self.browse(url)
        elif mode == 2: self.buildSeries(url)
        elif mode == 3: self.buildGenres(url)
        elif mode == 9: self.playVideo(name, url)

        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=True)