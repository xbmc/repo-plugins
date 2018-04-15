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
import os, sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

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
LIVE_URL      = BASE_URL + '/channels'
GUIDE_URL     = BASE_URL + '/tv-guide'
LOGO          = os.path.join(ADDON_PATH,'resources','images','%s.png')
MAIN_MENU     = [(LANGUAGE(30003), '' , 1),
                 (LANGUAGE(30004), '' , 2),
                 (LANGUAGE(30005), '' , 20)]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
                 
def cleanString(string1):
    return string1.strip(' \t\n\r')
              
def trimString(string1):
    return re.sub('[\s+]', '', string1.strip(' \t\n\r'))
              
socket.setdefaulttimeout(TIMEOUT)  
class TVCatchup(object):
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
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(minutes=5))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         

    def buildMenu(self, items):
        for item in items: self.addDir(*item)
        
        
    def buildLive(self):
        soup    = BeautifulSoup(self.openURL(LIVE_URL), "html.parser")
        results = soup('div' , {'class': 'channelsHolder'})
        for channel in results:
            chname = cleanString(channel.find_all('img')[1].attrs['alt']).replace('Watch ','')
            label = '%s - %s'%(chname,cleanString(channel.get_text()))
            link  = channel.find_all('a')[0].attrs['href']
            thumb = LOGO%chname
            infoLabels = {"mediatype":"episode","label":label ,"title":label}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
            self.addLink(label, link, 9, infoLabels, infoArt, len(results))
        

    def buildLineup(self, name=None):
        log('buildLineup, name = ' + str(name))
        soup    = BeautifulSoup(self.openURL(GUIDE_URL), "html.parser")
        results = soup('div' , {'class': 'row'})
        for channel in results:
            chname = cleanString(channel.find_all('img')[0].attrs['alt'])
            link   = cleanString(channel.find_all('a')[0].attrs['href'])
            thumb  = LOGO%chname
            if name is None:
                infoLabels = {"mediatype":"episode","label":chname ,"title":chname}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
                self.addDir(chname, link, 3, infoLabels, infoArt)
            elif name.lower() == chname.lower():
                try:
                    date = soup('a' , {'class': 'last'})[0].attrs['href']
                    aired = re.findall('/tv-guide/(.+?)/00',date, flags=re.DOTALL)[0]
                except: aired = datetime.datetime.now().strftime('%Y-%m-%d')
                items = channel('div' , {'class': 'hide'})
                for item in items:
                    try: 
                        time  = trimString(item.find_all('span')[0].get_text())
                        dur   = int((abs(eval(time.replace(':','.'))) * 60) * 60)
                    except: continue
                    label = '%s - %s'%(chname,cleanString(item.get_text()).split('\n')[0])
                    try: desc = trimString(item.find_all('br')[0].get_text())
                    except: desc = ''
                    infoLabels = {"mediatype":"episode","label":label ,"title":label,"plot":desc,"duration":dur,"aired":aired}
                    infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":thumb,"logo":thumb}
                    self.addLink(label, link, 9, infoLabels, infoArt, len(items))
                break
            
            
    def resolverURL(self, url):
        return re.compile('<source src="(.+?)" type="application/x-mpegURL">').findall(self.openURL(BASE_URL + url))[0]
            
            
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        liz  = xbmcgui.ListItem(name, path=self.resolverURL(url))
        liz.setMimeType('application/x-mpegURL')
        if url.endswith('m3u8'):
            liz.setProperty('inputstreamaddon','inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type','hls')
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


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

if mode==None:  TVCatchup().buildMenu(MAIN_MENU)
elif mode == 1: TVCatchup().buildLive()
elif mode == 2: TVCatchup().buildLineup()
elif mode == 3: TVCatchup().buildLineup(name)
elif mode == 20:xbmc.executebuiltin("RunScript(script.module.uepg,listitem=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%(urllib.quote(sys.argv[0]+"?mode=2"),urllib.quote(json.dumps(sys.argv[0]+"?mode=20")),urllib.quote(json.dumps("7200")),urllib.quote(json.dumps("7"))))
elif mode == 9: TVCatchup().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)