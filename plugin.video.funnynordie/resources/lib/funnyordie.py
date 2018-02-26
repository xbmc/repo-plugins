#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Funny or Die.
#
# Funny or Die is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Funny or Die is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Funny or Die.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from bs4 import BeautifulSoup
from YDStreamExtractor import getVideoInfo
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.funnynordie'
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
BASE_URL      = 'http://www.funnyordie.com'
VID_URL       = BASE_URL + '/browse/videos/%s/%s'
CAT_URL       = '%s/browse/videos/all/originals/most_recent/all_time'%BASE_URL
  
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
                 
socket.setdefaulttimeout(TIMEOUT)
class FunnyOrDie(object):
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
         
         
    @use_cache(1)
    def getData(self):
        try:
            soup = BeautifulSoup(self.openURL(CAT_URL), "html.parser")
            return json.loads(re.compile("data-react-props='(.*?)'>", re.DOTALL ).findall(str(soup('div' , {'class': 'action-bar'})))[0])
        except Exception as e: 
            log("getData Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return None
         
         
    def getSorts(self):
        log('getSorts')
        getData = self.getData()
        if getData is None: return
        for sort in getData['sortOptions']: yield (sort['title'], '%s/%s'%(sort['key'], sort['date_filter']), 0)
        
        
    def getCategories(self, url):
        log('getCategories')
        getData = self.getData()
        if getData is None: return
        for cat in getData['categoryOptions']: yield (cat['title'], json.dumps({"url":'%s/%s/%s'%(cat['category'], cat['grade'], url), "page":1}), 1)

        
    def buildMenu(self, items, yt=False):
        for item in items: self.addDir(*item)
        if yt: self.addYoutube("Browse Youtube" , 'plugin://plugin.video.youtube/user/funnyordie/')
         
        
    def browseVideos(self, name, myurl):
        log('browse, ' + name)
        myurl = json.loads(myurl)
        url   = myurl['url']
        page  = myurl['page']
        soup  = BeautifulSoup(self.openURL(VID_URL%(url,page)), "html.parser")
        videos = soup('div' , {'class': 'media-preview-crop'})
        if len(videos) == 0: return
        for video in videos:
            vidurl= BASE_URL + video.find_all('a')[0].attrs['href']
            title = video.find_all('a')[0].attrs['title']
            thumb = (video.find_all('a')[0]('img' , {'class': 'media-preview-thumbnail'})[0].attrs['data-src'] or ICON)
            duration = video.find_all('a')[0]('span' , {'class': 'media-video-duration'})[0].get_text()
            try:
                runtime = duration.split(':')
                if len(runtime) == 3:
                    h, m, s = runtime
                    duration = int(h) * 3600 + int(m) * 60 + int(s)
                else:
                    m, s = runtime   
                    duration = int(m) * 60 + int(s)
            except: duration = duration
            infoLabels   = {"mediatype":"episode","label":title ,"title":title,"duration":duration,"plot":title}
            infoArt      = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
            CONTENT_TYPE = 'episodes'
            self.addLink(title, vidurl, 9, infoLabels, infoArt, len(videos))
        myurl = json.dumps({"url":url,"page":page + 1})
        self.addDir('>> Next', myurl, 1)

        
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

if mode==None:  FunnyOrDie().buildMenu(list(FunnyOrDie().getSorts()), True)
elif mode == 0: FunnyOrDie().buildMenu(list(FunnyOrDie().getCategories(url)))
elif mode == 1: FunnyOrDie().browseVideos(name, url)
elif mode == 9: FunnyOrDie().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)