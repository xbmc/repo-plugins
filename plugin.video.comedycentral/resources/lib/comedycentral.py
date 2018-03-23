#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Comedy Central.
#
# Comedy Central is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Comedy Central is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Comedy Central.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from YDStreamExtractor import getVideoInfo
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.comedycentral'
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
PTVL_RUNNING  = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
BASE_URL      = 'http://www.cc.com'
LOGO_URL      = 'https://dummyimage.com/512x512/035e8b/FFFFFF.png&text=%s'
MAIN_MENU     = [(LANGUAGE(30007), BASE_URL + '/full-episodes' , 1),
                 (LANGUAGE(30008), BASE_URL + '/shows'         , 1),
                 (LANGUAGE(30004), BASE_URL + '/shows'         , 1)]
                 
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
                 
socket.setdefaulttimeout(TIMEOUT)
class CC(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()
           
           
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
            if str(e).startswith('HTTP Error 500'): return ''
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
         
    def buildMenu(self, items):
        for item in items: self.addDir(*item)
        self.addYoutube(LANGUAGE(30006), 'plugin://plugin.video.youtube/user/comedycentral/')
            
            
    def browse(self, name, url):
        log('browse, ' + name)
        response = self.openURL(url)
        if len(response) == 0: return
        try: items = json.loads(re.search('var triforceManifestFeed = (.+?);\n',response).group(1))
        except: items = json.loads(re.search('var triforceManifestURL = "(.+?)";',response).group(1))  
        try: thumb = (response.split('//meta[@property="og:image"]/@content')[0].strip() or ICON)
        except: thumb = ICON
        if not thumb.endswith(('.png','.jpg')): thumb = ICON
        elif thumb.startswith('//'): thumb = 'http:%s'%thumb
        if items and 'manifest' not in items: return
        for item in items['manifest']['zones']:
            if item in ('header', 'footer', 'ads-reporting', 'ENT_M171'): continue
            try: result = items['manifest']['zones'][item]['feed']
            except: result = None
            if result is None: continue
            try: ent_code = result.split('/feeds/')[1].split('/')[0]
            except:
                try: ent_code = result.split('/modules/')[1].split('/')[0]
                except: ent_code = ''
            ent_code = ent_code.split('_cc')[0].split('_tosh')[0]
            try: jsonResponse = json.loads(self.openURL(result))['result']
            except: log('browse, jsonResponse failed! ' + str(jsonResponse))
            if ent_code == 'ent_m081': return self.buildEpisodes(name, url, jsonResponse, jsonResponse['episodes'])
            elif ent_code == 'ent_m013': return self.buildEpisodes(name, url, jsonResponse, jsonResponse['episodes'])
            elif ent_code in ['ent_m100','ent_m150']:
                for item in jsonResponse['data']['items']:
                    if ent_code == 'ent_m100' and name == LANGUAGE(30008): self.buildShow(item)
                    elif ent_code == 'ent_m150' and name == LANGUAGE(30004):
                        for show in item['sortedItems']: self.buildShow(show)


    def buildShow(self, show):
        vid_url = (show.get('canonicalURL','') or show.get('url',None))
        title = (show.get('title','')          or show.get('shortTitle',None))
        plot  = (show.get('description','')    or show.get('shortDescription','') or title)
        if vid_url is None or title is None or not vid_url.startswith(BASE_URL): return
        try: thumb = show['image']['url']
        except: thumb = LOGO_URL%(urllib.quote(title))
        infoLabels = {"mediatype":"tvshows","label":title ,"title":title,"TVShowTitle":title,"plot":plot}
        infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
        self.addDir(title,vid_url,1,infoLabels,infoArt)
                            
                            
    def buildEpisodes(self, name, url, jsonResponse=None, videos=[], jsonKey='episodes'):
        log('buildEpisodes, ' + name)
        if jsonResponse is None: 
            jsonResponse = json.loads(self.openURL(url))['result']
            videos = jsonResponse[jsonKey]
        for video in videos:
            vid_url = (video.get('canonicalURL','') or video.get('url',None))
            title   = (video.get('title','')          or video.get('shortTitle',None))
            plot    = (video.get('description','')    or video.get('shortDescription','') or title)
            if vid_url is None or title is None: continue
            elif not vid_url.startswith(BASE_URL): continue
            try: show = video['show'].get('title',None)
            except: show = name
            try: thumb = video['images'][0]['url']
            except: thumb = video['image'][0]['url']
            try: season = int(video['season']['seasonNumber'])
            except: season = 0
            try: episode = int(video['season']['episodeAiringOrder'])
            except: episode = 0
            label   = '%s - %s'%(show,title)
            seinfo  = ('S' + ('0' if season < 10 else '') + str(season) + 'E' + ('0' if episode < 10 else '') + str(episode))
            if season + episode > 0: label = '%s - %s - %s'%(show, seinfo, title)
            try: aired = datetime.datetime.fromtimestamp(float(video['airDate']))
            except: aired = datetime.datetime.now()
            try: duration = video['duration']
            except: duration = 0
            infoLabels = {"mediatype":"episode","label":label ,"title":label,"TVShowTitle":show,"plot":plot,"aired":aired.strftime('%Y-%m-%d'),"duration":duration,"season":season,"episode":episode}
            infoArt      = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
            CONTENT_TYPE = 'episodes'
            self.addLink(label, vid_url, 9, infoLabels, infoArt, len(videos))
        try: next_page = jsonResponse['nextPageURL']
        except: next_page = None
        if next_page:  self.addDir('>> Next',next_page, 2)
            
    
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        info = getVideoInfo(url,QUALITY,True)
        if info is None: return
        info = info.streams()
        if len(info) > 1:
            if PTVL_RUNNING: return xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30007), ICON, 4000)
            info = sorted(info, key=lambda x: x['idx'])
            plst = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            plst.clear()
            xbmc.sleep(200)
            for videos in info:
                vidIDX = videos['idx']
                url = videos['xbmc_url']
                liz = xbmcgui.ListItem(videos['title'], path=url)
                try: 
                    if 'subtitles' in videos['ytdl_format']: liz.setSubtitles([x['url'] for x in videos['ytdl_format']['subtitles'].get('en','') if 'url' in x])
                except: pass
                plst.add(url, liz, vidIDX)
                if vidIDX == 0: xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz) 
            plst.unshuffle()
        else:
            liz = xbmcgui.ListItem(info[0]['title'], path=info[0]['xbmc_url'])
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

if mode==None:  CC().buildMenu(MAIN_MENU)
elif mode == 1: CC().browse(name, url)
elif mode == 2: CC().buildEpisodes(name, url)
elif mode == 9: CC().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)