#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of TuffTV.
#
# TuffTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TuffTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TuffTV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.tufftv'
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
LIVE_URL      = 'http://live.tufftv.com'
FEED_URL      = 'http://player.campfyre.tv/woo'
SCHD_URL      = 'http://www.tufftv.com/schedule'
SCHD_ZONES    = {'Eastern':'%s/eastern-schedule'%SCHD_URL,'Central':'%s/central-schedule'%SCHD_URL,'Mountain':'%s/mountain-schedule'%SCHD_URL,'Pacific':'%s/pacific-schedule'%SCHD_URL}
REGION        = REAL_SETTINGS.getSetting('Region')
REGION_URL    = SCHD_ZONES[REGION]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
                 
socket.setdefaulttimeout(TIMEOUT)
class TUFFTV(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()
           
           
    def openURL(self, url):
        log('openURL, url = ' + str(url))
        try:
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                request  = urllib2.Request(url)
                cacheresponse = urllib2.urlopen(request, timeout = TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, cacheresponse, expiration=datetime.timedelta(minutes=5))
            return cacheresponse
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''

         
    def buildMenu(self):
        self.addLink(LANGUAGE(30003)%self.buildGuide(live=True),'',0)
        self.addDir( LANGUAGE(30004)%REGION,'',1)
        self.addYoutube(LANGUAGE(30005), 'plugin://plugin.video.youtube/channel/UCXEIxLGYxu5pB61GHnaQ_hA/')
            
            
    def buildLive(self):
        log('buildLive')
        return 'http:'+re.findall('"file": "(.+?)"',self.openURL(FEED_URL),re.DOTALL)[0]
        
                
    def buildGuide(self, live=False):
        log('buildGuide, live = ' + str(live))
        idx   = 0
        AMPM  = 'AM'
        url   = self.buildLive()
        now   = datetime.datetime.now()
        tnow  = datetime.datetime.strptime((datetime.datetime.time(now)).strftime('%I:%M %p'), '%I:%M %p')
        dayofweek = {'Monday':1,'Tuesday':2,'Wednesday':3,'Thursday':4,'Friday':5,'Saturday':6,'Sunday':7}[now.strftime('%A')]
        soup  = BeautifulSoup(self.openURL(REGION_URL), "html.parser")
        items = soup('table' , {'class': 'schedule-table'})[0].find_all('tr')
        
        for item in items:
            item = item.find_all('td')
            try: 
                stime = int((item[0].get_text()).split(':')[0])
                if idx > 6 and stime == 12: AMPM = 'PM'
                starttime = '%s %s'%(item[0].get_text(),AMPM)
                title = item[dayofweek].get_text().replace('[block]2','').replace('[block]4','')
                if title == '[/block]': continue
                label = '%s %s'%(starttime,title)
                startDate  = (datetime.datetime.strptime(starttime, '%I:%M %p'))
                endDate1   = (startDate + datetime.timedelta(minutes=30))
                endDate2   = (startDate + datetime.timedelta(minutes=60))
                idx += 1
                if live and (tnow >= startDate and (tnow <= endDate1 or tnow <= endDate2)): return label
                elif live: continue
                airdate    = now.strftime('%Y-%m-%d')
                plot       = title
                infoLabels = {"mediatype":"episode","label":label,"title":label,"plot":plot,"aired":airdate,"studio":"Tuff.TV"}
                infoArt    = {"thumb":ICON,"poster":ICON,"fanart":FANART,"icon":ICON,"logo":ICON}
                self.addLink(label,url,9,infoLabels,infoArt)
            except: pass
        
                
    def playLive(self, name):
        log('playLive')
        self.playVideo(name, self.buildLive())        
        
        
    def playVideo(self, name, url):
        log('playVideo')
        liz = xbmcgui.ListItem(name, path=url)
        if 'm3u8' in url:
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

if mode==None:  TUFFTV().buildMenu()
elif mode == 0: TUFFTV().playLive(name)
elif mode == 1: TUFFTV().buildGuide()
elif mode == 2: TUFFTV().buildEpisodes(name, url)
elif mode == 9: TUFFTV().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)