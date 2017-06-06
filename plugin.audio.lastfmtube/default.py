#   Copyright (C) 2016 Lunatixz
#
#
# This file is part of LastFM Tube.
#
# LastFM Tube is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LastFM Tube is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LastFM Tube.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding: utf-8 -*-
import os, sys, time, datetime, pylast, re
import urllib, socket, json, collections, random
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon

from simplecache import use_cache, SimpleCache

# Plugin Info
ADDON_ID      = 'plugin.audio.lastfmtube'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile').decode('utf-8')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')

## GLOBALS ##
TIMEOUT    = 15
USER1      = REAL_SETTINGS.getSetting('USER1')
PASS1      = REAL_SETTINGS.getSetting('PASS1')
USER2      = REAL_SETTINGS.getSetting('USER2').replace('Enter Username','')
PASS2      = REAL_SETTINGS.getSetting('PASS2').replace('Enter Password','')
MEDIA_LIMIT= [25,50,100,250][int(REAL_SETTINGS.getSetting('MEDIA_LIMIT'))]
RANDOM_PLAY= REAL_SETTINGS.getSetting('RANDOM_PLAY') == "true"
YTURL      = 'plugin://plugin.video.youtube/play/?video_id='
YSSEARCH   = 'plugin://plugin.video.youtube/kodion/search/query/?q=%s'
DEBUG      = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true' 
API_KEY    = REAL_SETTINGS.getSetting('LASTFM_APIKEY')
API_SECRET = REAL_SETTINGS.getSetting('LASTFM_APISECRET')

USERLST    = []
if len(USER1) > 0:
    USERLST.append((USER1, '', 0, USER1,pylast.md5(PASS1)))
if len(USER2) > 0:
    USERLST.append((USER2, '', 0, USER2,pylast.md5(PASS2)))
    
MENULST    = (('Top Tracks'     , '', 3),
              ('Loved Tracks'   , '', 4),
              ('Recently Played', '', 2))

def log(msg, level = xbmc.LOGDEBUG):
    if DEBUG == True:
        xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + stringify(msg), level)
     
def convertString(string):
    try:
        string = unicode(string, "ascii")
    except UnicodeError:
        string = unicode(string, "utf-8")
    else:
        string = stringify(string)
    return string
        
def uni(string, encoding='utf-8'):
    if isinstance(string, basestring):
        if not isinstance(string, unicode):
           string = unicode(string, encoding)
    return string

def ascii(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('ascii', 'ignore')
    return string
    
def utf(string):
    if isinstance(string, basestring):
        if not isinstance(string, unicode):
           string = string.encode('utf-8', 'ignore')
    return string
      
def encodeString(string):
    return ''.join(i for i in string.encode('utf8') if ord(i)<128)    
    
def stringify(string):
    if isinstance(string, list):
        string = stringify(string[0])
    elif isinstance(string, (int, float, long, complex, bool)):
        string = str(string) 
    if isinstance(string, basestring):
        if not isinstance(string, unicode):
            string = unicode(string, 'utf-8')
        elif isinstance(string, unicode):
            string = string.encode('ascii', 'ignore')
        else:
            string = string.encode('utf-8', 'ignore')
    return string
    
def getParams():
    param=[]
    if len(sys.argv[2])>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param
    
socket.setdefaulttimeout(TIMEOUT)
class LastFMTube():
    def __init__(self):
        self.cache = SimpleCache()
        
        
    def mainMenu(self):
        for item in USERLST:
            self.addDir(*item)
            
            
    def browseMenu(self, user, pwd):
        for item in MENULST:
            print item
            self.addDir(*item,**{'user':user,'pwd':pwd})
            
            
    def sendJSON(self, command):
        data = ''
        try:
            data = xbmc.executeJSONRPC(uni(command))
        except UnicodeEncodeError:
            data = xbmc.executeJSONRPC(ascii(command))
        return data
            
    
    def loadJson(self, string):
        if len(string) == 0:
            return {}
        try:
            return json.loads(uni(string))
        except Exception,e:
            return {}
            
            
    def escapeDirJSON(self, dir_name):
        mydir = uni(dir_name)
        if (mydir.find(":")):
            mydir = mydir.replace("\\", "\\\\")
        return mydir
        
        
    @use_cache(31)
    def getDirectory(self, path, media='video', ignore='false', method='random', order='ascending', end=0, start=0, filter={}):
        json_query    = ('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","properties":["thumbnail","fanart","plot","duration","playcount"],"media":"%s","sort":{"ignorearticle":%s,"method":"%s","order":"%s"},"limits":{"end":%s,"start":%s}},"id":1}' % (self.escapeDirJSON(path), media, ignore, method, order, end, start))
        json_response = self.sendJSON(json_query)
        return self.loadJson(json_response)
        
        
    def buildMenu(self, url, auto=False):
        log('buildMenu, url = ' + url)
        json_response = self.getDirectory(url)
        if 'result' in json_response and(json_response['result'] != None) and 'files' in json_response['result']:
            response = json_response['result']['files']
            response = [response[random.randint(0,len(response)-1)]] if auto == True else response
            for item in response: 
                label = encodeString(item.get('label',''))

                if (item.get('filetype','') or '') == 'file':  
                    url = item.get('file','')
                    infoLabels ={"label":label ,"title":label  ,"plot":item.get('plot',''), "duration":(item.get('duration','') or 0), "playcount":(item.get('playcount','') or 0)}
                    infoArt    ={"thumb":(item.get('thumbnail','') or ICON),"poster":(item.get('thumbnail','') or ICON),"fanart":(item.get('fanart','') or FANART)}
                    self.addLink(label, url, 9, infoList=infoLabels, infoArt=infoArt)
                        
                
    def getRecentTracks(self, user, pwd, auto=False, rand=False, limit=250):
        """
        Get list of recently played tracks
        """
        playList = []
        playCount = 0
        log('getRecentTracks, user = ' + user)
        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET, username=user, password_hash=pwd)
        if auto == False:
            self.addDir('[B]Create Playlist (%d)[/B]'%MEDIA_LIMIT, '5', 5, user, pwd)
        user = network.get_user(network.username)
        for track in user.get_recent_tracks(limit=limit):
            artist = track.track.get_artist().name
            title  = track.track.get_title()
            artist = encodeString(artist)
            title  = encodeString(title)
            name   = ('{0!s} - {1!s}'.format(artist, title))
            url    = YSSEARCH%(name.replace(' ','%20'))
            if auto == True:
                if rand == True and random.choice([True,False]) == True:
                    continue
                self.buildMenu(url, True)
                playCount += 1
                if playCount >= MEDIA_LIMIT:
                    break
            else:
                self.addDir(name, url, 1)

            
    def getLovedTracks(self, user, pwd, auto=False, rand=False, limit=250):
        """Returns this user's loved track"""
        playList = []
        playCount= 0
        log('getPlaylists, user = ' + user)
        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET, username=user, password_hash=pwd) 
        if auto == False:
            self.addDir('[B]Create Playlist (%d)[/B]'%MEDIA_LIMIT, '7', 7, user, pwd)
        user = network.get_user(network.username)
        for loved in user.get_loved_tracks(limit=limit):
            artist = loved.track.get_artist().name
            title  = loved.track.get_title()
            artist = encodeString(artist)
            title  = encodeString(title)
            name   = ('{0!s} - {1!s}'.format(artist, title))
            url    = YSSEARCH%(name.replace(' ','%20'))
            if auto == True:
                #lazy method, won't result in MEDIA_LIMIT
                if rand == True and random.choice([True,False]) == True:
                    continue
                self.buildMenu(url, True)
                playCount += 1
                if playCount >= MEDIA_LIMIT:
                    break
            else:
                self.addDir(name, url, 1)

                
    def getTopTracks(self, user, pwd, auto=False, rand=False):
        """Returns the most played tracks as a sequence of TopItem objects."""
        playList = []
        playCount= 0
        log('getTopTracks, user = ' + user)
        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET, username=user, password_hash=pwd)
        if auto == False:
            self.addDir('[B]Create Playlist (%d)[/B]'%MEDIA_LIMIT, '6', 6, user, pwd)
        user = network.get_user(network.username) 
        for top in user.get_top_tracks() :
            name   = encodeString(str(top.item))
            url    = YSSEARCH%(name.replace(' ','%20'))
            if auto == True:   
                #lazy method, won't result in MEDIA_LIMIT
                if rand == True and random.choice([True,False]) == True:
                    continue
                self.buildMenu(url, True)
                playCount += 1
                if playCount >= MEDIA_LIMIT:
                    break
            else:
                self.addDir(name, url, 1)
            
            
    def resolveURL(self, url):
        log('resolveURL, url = ' + url)  
        if len(re.findall('http[s]?://www.youtube.com/watch', url)) > 0:
            return YTURL + url.split('/watch?v=')[1]
        elif len(re.findall('http[s]?://youtu.be/', url)) > 0:
            return YTURL + url.split('/youtu.be/')[1]
        return url
        
              
    def playVideo(self, name, url):
        log('playVideo')
        liz=xbmcgui.ListItem(name, path=url)
        liz.setProperty("IsPlayable","true")
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

           
    def addLink(self, name, u, mode, user='', pwd='', infoList=False, infoArt=False, total=0):
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False:
            liz.setInfo( type="Video", infoLabels={"label":name,"title":name} )
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
            
        if infoArt == False:
            liz.setArt({'thumb':ICON,'fanart':FANART})
        else:
            liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&user="+urllib.quote_plus(user)+"&pwd="+str(pwd)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, user='', pwd='', infoList=False, infoArt=False):
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False:
            liz.setInfo(type="Video", infoLabels={"label":name,"title":name})
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False:
            liz.setArt({'thumb':ICON,'fanart':FANART})
        else:
            liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&user="+urllib.quote_plus(user)+"&pwd="+str(pwd)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  
  
params=getParams()
try:
    url=urllib.unquote_plus(params["url"])
except:
    url=None
try:
    name=urllib.unquote_plus(params["name"])
except:
    name=None
try:
    user=urllib.unquote_plus(params["user"])
except:
    user=None
try:
    pwd=urllib.unquote_plus(params["pwd"])
except:
    pwd=None
try:
    mode=int(params["mode"])
except:
    mode=None
    
log("Mode: "+str(mode))
log("URL : "+str(url))
log("Name: "+str(name))
log("User: "+str(user))
log("PWD : "+str(pwd))

if mode==None:  LastFMTube().mainMenu()
elif mode == 0: LastFMTube().browseMenu(user, pwd)
elif mode == 1: LastFMTube().buildMenu(url)
elif mode == 2: LastFMTube().getRecentTracks(user, pwd)
elif mode == 3: LastFMTube().getTopTracks(user, pwd)
elif mode == 4: LastFMTube().getLovedTracks(user, pwd)
elif mode == 5: LastFMTube().getRecentTracks(user, pwd, True, RANDOM_PLAY)
elif mode == 6: LastFMTube().getTopTracks(user, pwd, True, RANDOM_PLAY)
elif mode == 7: LastFMTube().getLovedTracks(user, pwd, True, RANDOM_PLAY)
elif mode == 9: LastFMTube().playVideo(name, url)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)