#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of disclosetv.
#
# disclosetv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# disclosetv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with disclosetv.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.disclosetv'
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
BASE_URL      = 'http://www.disclose.tv/'
BASE_VID      = BASE_URL + 'videos'
YTURL        = 'plugin://plugin.video.youtube/play/?video_id='
VMURL        = 'plugin://plugin.video.vimeo/play/?video_id='

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)

def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
    
def isUWP():
    return len(fnmatch.filter(glob.glob(LANGUAGE(30011)),'*.*') + fnmatch.filter(glob.glob(LANGUAGE(30012)),'*.*')) > 0
     
socket.setdefaulttimeout(TIMEOUT)
class Disclose(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()
           
           
    def openURL(self, url):
        log('openURL, url = ' + str(url))
        try:
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib2.urlopen(request, timeout = TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(hours=1))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
         
    def buildMenu(self):
        self.addDir(LANGUAGE(30003), BASE_VID, 1)
        self.addYoutube(LANGUAGE(30004), 'plugin://plugin.video.youtube/channel/UCA-Ls4dkRBXHMjRjeTDTdjg/')
            
            
    def browse(self, url):
        log('browse')
        soup   = BeautifulSoup(self.openURL(url), "html.parser")
        videos = soup('div', {'class': 'teaser teaser--third'})
        for video in videos:
            try:
                try: thumb = 'http:%s'%(video('div', {'class': 'ratio-container ratio16_9'})[0].find('img').attrs['data-src'])
                except: thumb = FANART
                items   = video('div', {'class': 'teaser__caption'})
                vid_url = BASE_URL + (items[0]('a', {'class': 'article-link'})[0].attrs['href'])
                label   = items[0]('a', {'class': 'article-link'})[0].get_text()
                timeago = items[0]('span', {'class': 'meta-timeago'})[0].get_text()
                plot    = '%s - %s'%(timeago, label)
                try: genre = video('span', {'class': 'teaser-figure__cat'})[0].get_text()
                except: genre = 'Unknown'
                runtime = (video('span', {'class': 'teaser-figure__len'})[0].get_text()).split(':')
                if len(runtime) == 3:
                    h, m, s = runtime
                    duration  = int(h) * 3600 + int(m) * 60 + int(s)
                else:
                    m, s = runtime
                    duration  = (int(m) * 60) + int(s)
                infoLabels = {"mediatype":"episode","label":label ,"title":label,"duration":duration,"plot":plot}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
                self.addLink(label, vid_url, 9, infoLabels, infoArt, len(videos))
            except Exception as e: log("browse Failed! " + str(e), xbmc.LOGERROR)
        next = soup('li', {'class': 'more-container__button m-auto'})
        if len(next) == 0: return
        next_url   = BASE_URL + next[0].find('a').attrs['href']
        next_label = (next[0].find('a').attrs['title'] or next[0].get_text())
        self.addDir(next_label, next_url, 1)
            
            
    def resolveURL(self, name, url):
        try:
            data = json.loads(re.findall('"drupal-settings-json">(.+?)</script>',self.openURL(url), flags=re.DOTALL)[0])['dtv_video']
            provider = data['provider']
            log('resolveURL, provider = ' + provider)
            url = re.findall('src="(.+?)"',(data['player_code']), flags=re.DOTALL)[0].split('?')[0]
            if provider == 'youtube':
                if len(re.findall('http[s]?://www.youtube.com/embed', url)) > 0: url = YTURL + url.split('/embed/')[1]
                elif len(re.findall('http[s]?://www.youtube.com/watch', url)) > 0: url = YTURL + url.split('/watch?v=')[1]
                elif len(re.findall('http[s]?://youtu.be/', url)) > 0: url = YTURL + url.split('/youtu.be/')[1]
            elif provider == 'vimeo':
                if len(re.findall('http[s]?://vimeo.com/', url)) > 0: url = VMURL + url.split('/vimeo.com/')[1]
            else: raise Exception('resolveURL, unknown provider; data =' + json.dumps(data))
            log('resolveURL, url = ' + url)
            return xbmcgui.ListItem(name, path=url)
        except Exception as e: log("resolveURL Failed! " + str(e), xbmc.LOGERROR)
        if isUWP(): return ''
        from YDStreamExtractor import getVideoInfo
        info = getVideoInfo(url,QUALITY,True)
        if info is None: return
        info = info.streams()
        url  = info[0]['xbmc_url']
        liz  = xbmcgui.ListItem(name, path=url)
        try: 
            if 'subtitles' in info[0]['ytdl_format']: liz.setSubtitles([x['url'] for x in info[0]['ytdl_format']['subtitles'].get('en','') if 'url' in x])
        except: pass
        return liz
            
            
    def playVideo(self, name, url):
        log('playVideo')
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, self.resolveURL(name, url))
        
        
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

if mode==None:  Disclose().buildMenu()
elif mode == 1: Disclose().browse(url)
elif mode == 9: Disclose().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)