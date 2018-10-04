#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of TVCatchup.
#
# TVCatchup is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TVCatchup is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TVCatchup.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, _strptime, datetime, re, traceback, pytz, calendar
import urlparse, urllib, urllib2, socket, json, threading, requests
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

from bs4 import BeautifulSoup
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.tvcatchups'
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
BASE_URL      = 'http://www.tvcatchup.com'
ICON_URL      = 'http://images-cache.tvcatchup.com/NEW/images/channels/hover/channel_%d.png'
LIVE_URL      = BASE_URL + '/channels'
GUIDE_URL     = BASE_URL + '/tv-guide'
LOGO          = os.path.join(SETTINGS_LOC,'%s.png')

MAIN_MENU     = [(LANGUAGE(30003), '' , 1),
                 (LANGUAGE(30004), '' , 2),
                 (LANGUAGE(30005), '' , 20)]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)

def cleanString(string1):
    return string1.strip(' \t\n\r')
              
def trimString(string1):
    return re.sub('[\s+]', '', string1.strip(' \t\n\r'))

def retrieveURL(url, dest):
    try: urllib.urlretrieve(url, dest)
    except Exception as e: log("retrieveURL, Failed! " + str(e), xbmc.LOGERROR)
    return True
    
socket.setdefaulttimeout(TIMEOUT)  
class TVCatchup(object):
    def __init__(self, sysARG):
        log('__init__')
        self.cache   = SimpleCache()
        self.sysARG  = sysARG
        self.downloadThread = threading.Timer(0.5, retrieveURL)
        
        
    def getDuration(self, timeString):
        starttime, endtime = timeString.split('-')
        try: endtime = datetime.datetime.strptime(endtime, '%H:%M') 
        except TypeError: endtime = datetime.datetime(*(time.strptime(endtime, '%H:%M')[0:6]))
        try: starttime = datetime.datetime.strptime(starttime, '%H:%M') 
        except TypeError: starttime = datetime.datetime(*(time.strptime(starttime, '%H:%M')[0:6]))
        durtime = (endtime - starttime)
        return durtime.seconds
        
        
    def getLocaltime(self, timeString, dst=False):
        ltz   = pytz.timezone('Europe/London')
        try: ltime = datetime.datetime.strptime(timeString, '%H:%M').time()
        except TypeError: ltime = datetime.datetime(*(time.strptime(timeString, '%H:%M')[0:6])).time()
        ldate = datetime.datetime.now(ltz).date()
        ltime = ltz.localize((datetime.datetime.combine(ldate, ltime)))
        ltime = ltime.astimezone(pytz.timezone('UTC')).replace(tzinfo=None)
        if dst: return ltime - ((datetime.datetime.utcnow() - datetime.datetime.now()) +  datetime.timedelta(hours=time.daylight))
        else: return ltime - (datetime.datetime.utcnow() - datetime.datetime.now())
        
        
    def openURL(self, url):
        try:
            url = requests.head(url, allow_redirects=True).url
            log('openURL, url = ' + str(url))
            if len(re.findall('http[s]?://transponder.tv', url)) > 0: 
                xbmcgui.Dialog().ok(ADDON_NAME, LANGUAGE(30007))
                xbmc.executebuiltin('XBMC.RunAddon(plugin.video.transpondertv)')
                return ''
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
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
        

    def downloadQueue(self, url, dest):
        if xbmcvfs.exists(LOGO%dest): return
        if self.downloadThread.isAlive(): self.downloadThread.join()
        self.downloadThread = threading.Timer(0.2, retrieveURL, [url, xbmc.translatePath(LOGO%dest)])
        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30006), ICON, 2)
        self.downloadThread.name = "downloadThread"
        self.downloadThread.start()
        
        
    def downloadLogos(self, items):
        log('downloadLogos')
        if xbmcvfs.exists(SETTINGS_LOC) == False: xbmcvfs.mkdirs(SETTINGS_LOC)
        for item in items: self.downloadQueue(*item)
        
        
    def buildLive(self):
        items   = []
        soup    = BeautifulSoup(self.openURL(LIVE_URL), "html.parser")
        results = soup('div' , {'class': 'channelsHolder'})
        for channel in results:
            chlogo = channel.find_all('img')[0].attrs['src']
            chname = cleanString(channel.find_all('img')[1].attrs['alt']).replace('Watch ','')
            items.append((chlogo,chname))
            label  = '%s - %s'%(chname,cleanString(channel.get_text()))
            link   = channel.find_all('a')[0].attrs['href']
            thumb  = LOGO%chname
            infoLabels = {"mediatype":"episode","label":label ,"title":label,"plot":label}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
            self.addLink(label, link, 9, infoLabels, infoArt, len(results))
        self.downloadLogos(items)
        
        
    def buildLineup(self, name=None):
        log('buildLineup, name = ' + str(name))
        soup    = BeautifulSoup(self.openURL(GUIDE_URL), "html.parser")
        results = soup('div' , {'class': 'row'})
        now = datetime.datetime.now()
        for channel in results:
            chname = cleanString(channel.find_all('img')[0].attrs['alt'])
            link   = cleanString(channel.find_all('a')[0].attrs['href'])
            thumb  = LOGO%chname
            if name is None:
                infoLabels = {"mediatype":"episode","label":chname ,"title":chname}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
                self.addDir(chname, chname, 2, infoLabels, infoArt)
            elif name.lower() == chname.lower().replace('+',' '):
                items = channel('div' , {'class': 'hide'})
                for item in items:
                    stime = item.find_all('span')
                    if not stime: continue
                    stime = trimString(stime[0].get_text())
                    dur   = self.getDuration(stime)
                    start = self.getLocaltime(stime.split('-')[0])
                    end   = start + datetime.timedelta(seconds=dur)
                    title = cleanString(item.get_text()).split('\n')[0]
                    if now > end: continue
                    if now >= start and now < end: title = '[B]%s[/B]'%title
                    aired = start.strftime('%Y-%m-%d')
                    start = start.strftime('%I:%M %p')
                    label = '%s: %s'%(start,title)
                    try: desc = trimString(item.find_all('br')[0].get_text())
                    except: desc = label
                    infoLabels = {"mediatype":"episode","label":label ,"title":label,"plot":desc,"duration":dur,"aired":aired}
                    infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
                    self.addLink(label, link, 9, infoLabels, infoArt, len(items))
                    # except Exception as e: log('buildLineup, failed! ' + str(e), xbmc.LOGERROR)
                break
            

    def uEPG(self):
        log('uEPG')
        #support for uEPG universal epg framework module available from the Kodi repository. https://github.com/Lunatixz/KODI_Addons/tree/master/script.module.uepg
        soup    = BeautifulSoup(self.openURL(GUIDE_URL), "html.parser")
        results = soup('div' , {'class': 'row'})
        return [self.buildGuide(idx, channel) for idx, channel in enumerate(results)]
        
        
    def buildGuide(self, idx, channel):
        log('buildGuide, idx = ' + str(idx))
        now        = datetime.datetime.now()
        chname     = cleanString(channel.find_all('img')[0].attrs['alt'])
        link       = cleanString(channel.find_all('a')[0].attrs['href'])
        chlogo     = LOGO%chname
        chnum      = idx + 1
        isFavorite = False 
        newChannel = {}
        guidedata  = []
        newChannel['channelname']   = chname
        newChannel['channelnumber'] = chnum
        newChannel['channellogo']   = chlogo
        newChannel['isfavorite']    = isFavorite
        items = channel('div' , {'class': 'hide'})
        for item in items:
            try:  
                stime = trimString(item.find_all('span')[0].get_text())
                dur   = self.getDuration(stime)
                title = cleanString(item.get_text()).split('\n')[0]
                label = '%s - %s'%(chname,title)
                start = self.getLocaltime(stime.split('-')[0], True)
                starttime = time.mktime(start.timetuple())
            except: continue
            try: desc = trimString(item.find_all('br')[0].get_text())
            except: desc = ''
            tmpdata = {"mediatype":"episode","label":title,"title":label,"originaltitle":label,"plot":desc,"duration":dur}
            tmpdata['starttime'] = starttime
            endtime = start + datetime.timedelta(seconds=dur)
            # if now > endtime: continue
            tmpdata['url'] = self.sysARG[0]+'?mode=9&name=%s&url=%s'%(label,link)
            tmpdata['art'] ={"thumb":chlogo,"clearart":chlogo,"fanart":FANART,"icon":chlogo,"clearlogo":chlogo}
            guidedata.append(tmpdata)
        newChannel['guidedata'] = guidedata
        return newChannel

            
    def resolverURL(self, url):
        return re.compile('<source src="(.+?)" type="application/x-mpegURL">').findall(self.openURL(BASE_URL + url))[0]
            
            
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        liz  = xbmcgui.ListItem(name, path=self.resolverURL(url))
        liz.setMimeType('application/x-mpegURL')
        liz.setProperty('inputstreamaddon','inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.manifest_type','hls')
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)


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

        if mode==None:  self.buildMenu(MAIN_MENU)
        elif mode == 1: self.buildLive()
        elif mode == 2: self.buildLineup(url)
        elif mode == 9: self.playVideo(name, url)
        elif mode == 20:xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%(urllib.quote(json.dumps(list(self.uEPG()))),urllib.quote(json.dumps(self.sysARG[0]+"?mode=20")),urllib.quote(json.dumps("7200")),urllib.quote(json.dumps("7"))))

        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=True)