#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of EarthCam.
#
# EarthCam is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EarthCam is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EarthCam.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.earthcam'
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
BASE_URL      = 'http://www.earthcam.com'
NET_URL       = '%s/network/'%BASE_URL
LOGO_URL      = 'http://icons.better-idea.org/icon?url=%s&size=70..120..200'
MAIN_MENU     = [(LANGUAGE(30003), NET_URL, 2),
				 (LANGUAGE(30004), NET_URL, 1)]
                 

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
                 
socket.setdefaulttimeout(TIMEOUT)
class EarthCam(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()
           
           
    def openURL(self, url, force=False):
        log('openURL, url = ' + str(url))
        try:
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse or force:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib2.urlopen(request, timeout = TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(days=1))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
         
    def buildMenu(self, items):
        for item in items: self.addDir(*item)
        self.addYoutube(LANGUAGE(30005), 'plugin://plugin.video.youtube/user/earthcam/')
            
            
    def browse(self, name, url):
        log('browse, ' + name)
        soup = BeautifulSoup(self.openURL(url), "html.parser")
        if len(soup) == 0: return
        networks = soup('a', {'class': 'locationLink'})
        for region in networks:
            title = region.get_text()
            url   = NET_URL + region.attrs['href']
            thumb = LOGO_URL%title
            infoLabels = {"mediatype":"files","label":title ,"title":title}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}  
            self.addDir(title,url,2,infoLabels,infoArt)

            
    def browseVideos(self, name, url):
        log('browseVideos, ' + name)
        soup = BeautifulSoup(self.openURL(url), "html.parser")
        if len(soup) == 0: return
        featured = soup('div', {'class': 'col-lg-3 col-md-4 col-sm-5 col-xs-12'})
        for cam in featured:
            feat  = cam('a', {'class': 'listImg'})
            url   = cam('a', {'class': 'featuredTitleLink'})[0].attrs['href']
            if url.endswith('php'): continue
            thumb = feat[0].find('img').attrs['src']
            title = feat[0].find('img').attrs['title']
            infoLabels = {"mediatype":"files","label":title ,"title":title}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}  
            self.addDir(title,url,8,infoLabels,infoArt) 

        
    def resolveURL(self, name, url):
        log('resolveURL, url = ' + str(url))
        try:
            response = self.openURL(url)
            results = json.loads(re.compile("var json_base					= (.*?);").findall(response)[0], strict=False)
            pageids  = (json.loads(re.compile("js_cam_list				= (.*?);").findall(response)[0], strict=False) or [url.split('?cam=')[1]])
        except: return
        
        for id in pageids:
            try: results = results["cam"][id]
            except: return
            
            # results["city"]
            # results["state"]
            # results["name"]
            # results["group"]
            # results["location"]
            # results["timezone_offset"]

            thumb   = results["thumbnail_512"]
            plot    = (results["description"] or results["title"])
            infoArt = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
            
            if  results["liveon"] == "true":
                label      = '%s,%s - Live (HLS)'%(results["long_title"],results["country"])
                infoLabels = {"mediatype":"episode","label":label ,"title":label,"plot":plot}
                liveurl = ('http:%s%s'%(results["html5_streamingdomain"],results["html5_streampath"]))
                self.addLink(label, liveurl, 9, infoLabels, infoArt, len(pageids))
                # label      = '%s,%s - Live (FLV)'%(results["long_title"],results["country"])
                # infoLabels = {"mediatype":"episode","label":label ,"title":label,"plot":plot}
                # liveurl = ('%s%s'%(results["streamingdomain"],results["livestreamingpath"]))
                # self.addLink(label, liveurl, 9, infoLabels, infoArt, len(pageids))
            elif  results["timelapseon"] == "true":
                label      = '%s,%s -TimeLapse'%(results["long_title"],results["country"])
                infoLabels = {"mediatype":"episode","label":label ,"title":label,"plot":plot}
                liveurl = ('http:%s%s'%(results["timelapsedomain"],results["timelapsepath"]))
                self.addLink(label, liveurl, 9, infoLabels, infoArt, len(pageids))
            elif  results["archiveon"] == "true":
                label      = '%s,%s - Archive'%(results["long_title"],results["country"])
                infoLabels = {"mediatype":"episode","label":label ,"title":label,"plot":plot}
                liveurl = ('http:%s%s'%(results["archivedomain"],results["archivepath"]))
                self.addLink(label, liveurl, 9, infoLabels, infoArt, len(pageids))
                

    def prepareLink(self, url):
        log('prepareLink, url = ' + str(url))
        if len(re.findall('http[s]?://www.youtube.com/watch', url)) > 0: return 'plugin://plugin.video.youtube/play/?video_id=%s'%(url.split('/watch?v=')[1])
        elif url.lower().endswith(".m3u8"): url = url.replace('playlist', re.search(r'^([^#].+)\.m3u8$', self.openURL(url, True), re.MULTILINE).group(1))
        return url

     
    def playVideo(self, name, url):
        log('playVideo')
        liz  = xbmcgui.ListItem(name, path=self.prepareLink(url))
        # if url.startswith('rtmp'):
            # liz.setProperty('inputstreamaddon','inputstream.adaptive')
            # liz.setProperty('inputstream.adaptive.manifest_type','hls')
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

if mode==None:  EarthCam().buildMenu(MAIN_MENU)
elif mode == 1: EarthCam().browse(name, url)
elif mode == 2: EarthCam().browseVideos(name, url)
elif mode == 8: EarthCam().resolveURL(name, url)
elif mode == 9: EarthCam().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)