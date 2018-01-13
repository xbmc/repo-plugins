#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of TV Land.
#
# TV Land is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TV Land is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TV Land.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from YDStreamExtractor import getVideoInfo
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.tvland'
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
BASE_URL      = 'http://www.tvland.com'
IGNORE_LIST   = ['ent_m100', 'ent_m150', 'ent_m151', 'ent_m112', 'ent_m116']
MAIN_MENU     = [("Latest Episodes", BASE_URL + '/full-episodes', 1),
                 ("Browse Shows"   , BASE_URL + '/shows'        , 1)]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
                 
socket.setdefaulttimeout(TIMEOUT)
class TVLand(object):
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
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
         
    def buildMenu(self, items):
        for item in items: self.addDir(*item)
        self.addYoutube("Browse Youtube" , 'plugin://plugin.video.youtube/user/tvland/')
            
            
    def browse(self, name, url):
        log('browse, ' + name)
        response = self.openURL(url)
        if len(response) == 0: return
        try: items = json.loads(re.search('var triforceManifestFeed = (.+?);\n',response).group(1))
        except: items = json.loads(re.search('var triforceManifestURL = "(.+?)";',response).group(1))  
        try: thumb = (response.split('//meta[@property="og:image"]/@content')[0].strip() or ICON)
        except: thumb = ICON
        thumb = (thumb or ICON)
        if not thumb.endswith(('.png','.jpg')): thumb = ICON
        if items and 'manifest' not in items: return
        for item in items['manifest']['zones']:
            if item in ('header', 'footer', 'ads-reporting', 'ENT_M171'): continue
            try: result = items['manifest']['zones'][item]['feed']
            except: result = None
            if result is None: continue
            try: ent_code = result.split('/feeds/')[1].split('/')[0]
            except: ent_code = ''
            ent_code = ent_code.split('_tvland')[0]
            if ent_code not in IGNORE_LIST: continue
            jsonResponse = json.loads(self.openURL(result))
            try: title = jsonResponse['result']['promo']['headline'].title()
            except: 
                try: title = jsonResponse['result']['data']['headerText'].title()
                except: title = feed_title
            infoLabels = {"mediatype":"tvshows","label":title ,"title":title,"TVShowTitle":title}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}    
            if ent_code == 'ent_m151': 
                if title == 'Latest Full Episodes': return self.browseVideos(title, result)
                self.addDir(title,result,2,infoLabels,infoArt)
                if name != 'Latest Episodes': self.addDir(title,result,2,infoLabels,infoArt)
                for item in jsonResponse['result']['data']['shows']:
                    title = item['title']
                    if name == 'Latest Episodes' and title == 'Latest Full Episodes': return self.browseVideos(title, item['url'])
                    elif name == 'Latest Episodes': continue
                    infoLabels = {"mediatype":"tvshows","label":title ,"title":title,"TVShowTitle":title}
                    infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}    
                    self.addDir(title,item['url'],2,infoLabels,infoArt)
            elif ent_code == 'ent_m112':
                if title in ['Latest Full Episodes','Full Episodes']: return self.browseVideos(title, result)
                self.addDir(title,result,2,infoLabels,infoArt) 
            else:
                if ent_code == 'ent_m116': type = 'filters'
                else: type = 'items'
                myURL = json.dumps({"url":result,"type":type})
                if title in ['Full Episodes','Featured Shows']: return self.browseShows(title, myURL)
                elif name == 'Browse Shows' and title == 'All Shows': return self.browseShows(title, myURL)
                self.addDir(title,myURL,3,infoLabels,infoArt)
      
      
    def browseVideos(self, name, url):
        log('browseVideos, ' + name)
        jsonResponse = json.loads(self.openURL(url))
        try: videos = jsonResponse['result']['items']
        except:
            try: videos = jsonResponse['result']['data']['items']
            except: return
        for video in videos:
            try: vid_url = video['canonicalURL']
            except:
                try: vid_url = video['itemURL']
                except: continue
            if not ('/video-clips/') in vid_url and not ('/video-playlists/') in vid_url and not ('/full-episodes/') in vid_url and not ('/episodes/') in vid_url: continue
            if 'bellator.spike.com' in vid_url: continue
            try: thumb = (video['images'][0]['url'] or ICON)
            except:
                try: thumb = (video['image'][0]['url'] or ICON)
                except: thumb = ICON
            thumb = (thumb or ICON)
            if thumb and thumb.startswith('//'): thumb = 'http:' + thumb 
            try: show = video['show']['title']
            except: show = video['showTitle']
            try: episodeNumber = int(video['season']['episodeNumber'])
            except: episodeNumber = 0
            try: seasonNumber = int(video['season']['seasonNumber'])
            except: seasonNumber = 0
            try: raw_date = video['airDate']
            except: raw_date = video['publishDate']
            try: aired = (datetime.datetime.strptime(raw_date, '%m/%d/%y'))
            except: aired = datetime.datetime.now()
            aired = aired.strftime('%Y-%m-%d')
            try:
                runtime = video['duration'].split(':')
                if len(runtime) == 3:
                    h, m, s = runtime
                    duration = int(h) * 3600 + int(m) * 60 + int(s)
                else:
                    m, s = runtime   
                    duration = int(m) * 60 + int(s)
            except: duration = video['duration']
            label  = video['title']
            seinfo = ('S' + ('0' if seasonNumber < 10 else '') + str(seasonNumber) + 'E' + ('0' if episodeNumber < 10 else '') + str(episodeNumber))
            label  = '%s'%(label) if seasonNumber + episodeNumber == 0 else '%s - %s'%(label, seinfo)
            label  = '%s - %s'%(show,label) if len(show) > 0 else label
            infoLabels   = {"mediatype":"episode","label":label ,"title":label,"TVShowTitle":show,"duration":duration,"plot":video['description'],"aired":aired}
            infoArt      = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
            CONTENT_TYPE = 'episodes'
            self.addLink(label, vid_url, 9, infoLabels, infoArt, len(videos))
        try: next_page = jsonResponse['result']['data']['nextPageURL']
        except: next_page = None
        if next_page:  self.addDir('>> Next',next_page, 2)


    def browseShows(self, name, myURL):
        log('browseShows, ' + name)
        myURL   = json.loads(myURL)
        url     = myURL['url']
        type    = myURL['type']
        feed    = url
        counter = 0
        jsonResponse = json.loads(self.openURL(url))
        try: shows = jsonResponse['result']['data'][type]
        except:
            try: shows = jsonResponse['result'][type]
            except: shows = []
        for item in shows:
            if '/ent_m150/' in feed or '/ent_m100/' in feed or '/ent_m069/' in feed:
                try: url = item['canonicalURL']
                except:
                    try: url = item['url']
                    except: continue
                if '/shows/' not in url: continue
                if item['title'] in IGNORE_LIST: continue
                try: thumb = (item['image']['url'] or ICON)
                except:
                    try: thumb = (item['image'][0]['url'] or ICON)
                    except: thumb = thumb
                thumb = (thumb or ICON)
                if thumb.startswith('//'): thumb = 'https:' + thumb
                title      = item['title']
                infoLabels = {"mediatype":"tvshows","label":title ,"title":title,"TVShowTitle":title}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
                self.addDir(title,url,1,infoLabels,infoArt)

                
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        if PTVL_RUNNING: return 
        info = getVideoInfo(url,QUALITY,True)
        if info is None: return
        info = info.streams()
        info = sorted(info, key=lambda x: x['idx'])
        plst = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        plst.clear()
        xbmc.sleep(200)
        idxLST = []
        for videos in info:
            vidIDX = videos['idx']
            url = videos['xbmc_url']
            liz = xbmcgui.ListItem(videos['title'], path=url)
            if 'subtitles' in videos['ytdl_format']: liz.setSubtitles([x['url'] for x in videos['ytdl_format']['subtitles'].get('en','') if 'url' in x])
            plst.add(url, liz, vidIDX)
            if vidIDX == 0: xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz) 
        plst.unshuffle()
        
        
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

if mode==None:  TVLand().buildMenu(MAIN_MENU)
elif mode == 1: TVLand().browse(name, url)
elif mode == 2: TVLand().browseVideos(name, url)
elif mode == 3: TVLand().browseShows(name, url)
elif mode == 9: TVLand().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)