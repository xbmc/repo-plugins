#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of SpikeTV.
#
# SpikeTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SpikeTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SpikeTV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, time, datetime, re, traceback
import urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from youtube_dl import YoutubeDL
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.spiketv'
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
BASE_URL      = 'http://www.spike.com'
IGNORE_LIST   = ['ent_m100', 'ent_m069', 'ent_m150', 'ent_m151', 'ent_m112', 'ent_m116']
MAIN_MENU     = [("Latest Episodes", BASE_URL + '/full-episodes', 1),
                 ("Browse Shows"   , BASE_URL + '/shows'        , 1)]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    param=[]
    if len(sys.argv[2])>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'): params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2: param[splitparams[0]]=splitparams[1]
    return param
                 
socket.setdefaulttimeout(TIMEOUT)
class SpikeTV(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()
        self.ydl   = YoutubeDL()
           
           
    def openURL(self, url):
        log('openURL, url = ' + str(url))
        try:
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                request = urllib2.Request(url)
                response = urllib2.urlopen(request, timeout = TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(hours=1))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
         
    def buildMenu(self, items):
        for item in items: self.addDir(*item)
        self.addYoutube("Browse Youtube" , 'plugin://plugin.video.youtube/user/SpikeTV/')
            
            
    def browse(self, name, url):
        log('browse, ' + name)
        response = self.openURL(url)
        if len(response) == 0: return
        try: items = json.loads(re.search('var triforceManifestURL = "(.+?)";',response).group(1))
        except: items = json.loads(re.search('var triforceManifestFeed = (.+?);',response).group(1))
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
            ent_code = ent_code.split('_spike')[0]
            if ent_code not in IGNORE_LIST: continue
            jsonResponse = json.loads(self.openURL(result))
            if ent_code == 'ent_m151':
                try: title = jsonResponse['result']['data']['headerText'].title()
                except: continue
                infoLabels = {"mediatype":"tvshows","label":title ,"title":title,"TVShowTitle":title}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
                if name != 'Latest Episodes': self.addDir(title,result,2,infoLabels,infoArt)
                for item in jsonResponse['result']['data']['shows']:
                    title      = item['title']
                    infoLabels = {"mediatype":"tvshows","label":title ,"title":title,"TVShowTitle":title}
                    infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
                    if name == 'Latest Episodes' and title == 'all shows': return self.browseVideos(title, item['url'])
                    elif name == 'Latest Episodes': continue
                    self.addDir(title,item['url'],2,infoLabels,infoArt)
            elif ent_code == 'ent_m112':
                try: title = jsonResponse['result']['promo']['headline'].title()
                except: continue
                if title == 'Full Episodes': return self.browseVideos(title, result)
                elif name != 'Full Episodes': continue
                infoLabels = {"mediatype":"tvshows","label":title ,"title":title,"TVShowTitle":title}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
                self.addDir(title,result,2,infoLabels,infoArt)
            else:
                if ent_code == 'ent_m116':
                    type = 'filters'
                    try: title = jsonResponse['result']['promo']['headline'].title()
                    except: continue
                else:
                    type = 'items'
                    try: title = jsonResponse['result']['data']['headerText'].title()
                    except:
                        try: title = jsonResponse['result']['data']['header']['title'].title()
                        except: continue
                myURL      = json.dumps({"url":result,"type":type})
                if title == 'Full Episodes': return self.browseShows(title, myURL)
                elif name != 'Full Episodes' and name != 'Browse Shows': continue
                infoLabels = {"mediatype":"tvshows","label":title ,"title":title,"TVShowTitle":title}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
                if name == 'Browse Shows' and title == 'All Shows': return self.browseShows(title, myURL)
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
        self.ydl.add_default_info_extractors()
        with self.ydl:
            result = self.ydl.extract_info(url, download=False)
            url = result['entries'][0]['manifest_url']
            liz = xbmcgui.ListItem(name, path=url)
            if 'subtitles' in result['entries'][0]: liz.setSubtitles([x['url'] for x in result['entries'][0]['subtitles'].get('en','') if 'url' in x])
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

if mode==None:  SpikeTV().buildMenu(MAIN_MENU)
elif mode == 1: SpikeTV().browse(name, url)
elif mode == 2: SpikeTV().browseVideos(name, url)
elif mode == 3: SpikeTV().browseShows(name, url)
elif mode == 9: SpikeTV().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)