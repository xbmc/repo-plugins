#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Home Shopping Network.
#
# Home Shopping Network is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Home Shopping Network is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Home Shopping Network.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.hsn'
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
BASE_URL      = 'http://www.hsn.com'
LIVE_URL      = '%s/watch/live'%BASE_URL
PAST_URL      = BASE_URL + '/watch/past-shows?showDate=%s'
YOUTUBE_URL   = 'plugin://plugin.video.youtube/play/?video_id=%s'
MAIN_MENU     = [('HSN1' , '1' , 1),
                 ('HSN2' , '2' , 1)]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
                 
socket.setdefaulttimeout(TIMEOUT)
class HSN(object):
    def __init__(self):
        log('__init__')
        self.cache   = SimpleCache()
           
           
    def openURL(self, url):
        log('openURL, url = ' + str(url))
        try:
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                request = urllib2.Request(url)
                response = urllib2.urlopen(request, timeout = TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(days=1))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
         
    def buildHSN(self, name, url):
        guide  = []
        isLive = False
        now    = datetime.datetime.now()
        soup   = BeautifulSoup(self.openURL(LIVE_URL), "html.parser")
        soup   = soup('div' , {'class': 'live-container'})[0]
        if int(url) is 1:
            gurl    = BASE_URL + soup.find_all('a')[0].attrs['href']
            liveurl = soup('div' , {'class': 'watch-nav-container'})[0].attrs['data-wap-hsn-live-video-normal-url']
            content = BeautifulSoup(self.openURL(gurl), "html.parser")
            guide   = content('div' , {'class': 'grid-content'})[0]('a', {'class': 'watch-now'})
        else:
            gurl    = BASE_URL + soup.find_all('a')[0].attrs['href']+'?network=4'
            liveurl  = soup('div' , {'class': 'watch-nav-container'})[0].attrs['data-wap-hsn2-live-video-normal-url']
            content = BeautifulSoup(self.openURL(gurl), "html.parser")
            guide   = content('div' , {'class': 'grid-content'})[0]('button', {'class': 'show-details'})
            
        for idx, item in enumerate(guide):
            try: isLive = content('div' , {'class': 'grid-content'})[0]('span', {'class': 'live-now'})[idx].get_text() == 'Watch Live'
            except: isLive = False
            try:
                vidurl = YOUTUBE_URL%(item.attrs['data-video-id'])
                date   = item.attrs['data-show-date']
                title  = item.attrs['data-show-name']
                if isLive: 
                    label  = '[B]Live[/B] - %s'%title
                    vidurl = liveurl
                else: label = '[B]Pre-Recorded: [/B]%s - %s'%(date, title)
            except:
                vidurl = liveurl
                date  = item.attrs['data-startdate']
                title = item.get_text()
                if isLive: label  = '[B]Live[/B] - %s'%title
                else: label = '%s - %s'%(date, title)
            CONTENT_TYPE  = 'episodes'
            aired = (datetime.datetime.strptime(date, '%m/%d/%Y %I:%M:%S %p'))
            date  = aired.strftime('%I:%M:%S %p')
            infoLabels   = {"mediatype":"episode","label":label ,"title":label,"plot":title,"aired":aired.strftime('%Y-%m-%d')}
            infoArt      = {"thumb":ICON,"poster":ICON,"fanart":FANART,"icon":ICON,"logo":ICON}
            self.addLink(label, vidurl, 9, infoLabels, infoArt, len(guide))
         
        
    def buildMenu(self, items):
        for item in items: self.addDir(*item)
        self.addYoutube("Browse Youtube" , 'plugin://plugin.video.youtube/user/HSN/')
         
                   
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        liz  = xbmcgui.ListItem(name, path=url)
        if url.startswith('rtmp'):
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

if mode==None:  HSN().buildMenu(MAIN_MENU)
elif mode == 1: HSN().buildHSN(name, url)
elif mode == 9: HSN().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)