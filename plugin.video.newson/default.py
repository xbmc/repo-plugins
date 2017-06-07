#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of NewsOn.
#
# NewsOn is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NewsOn is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NewsOn.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback, feedparser
import urllib, urllib2, socket, json, collections
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon

from simplecache import SimpleCache
# Plugin Info
ADDON_ID      = 'plugin.video.newson'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
NEWSART       = os.path.join(ADDON_PATH,'resources','images','newscast.jpg')
CLIPART       = os.path.join(ADDON_PATH,'resources','images','videoclips.jpg')

## GLOBALS ##
TIMEOUT     = 15
DEBUG       = True#REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
BASE_URL    = 'http://watchnewson.com/'
BASE_API    = 'http://watchnewson.com/api/linear/channels'
USER_REGION = 'US'
MENU        = [("Newscasts"  , '0', 0, False, {"thumb":NEWSART,"poster":NEWSART,"fanart":FANART,"icon":ICON,"logo":ICON}),
               ("Video Clips", '2', 2, False, {"thumb":CLIPART,"poster":CLIPART,"fanart":FANART,"icon":ICON,"logo":ICON})]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == True:
        if level == xbmc.LOGERROR:
            msg += ' ,' + traceback.format_exc()
        xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + stringify(msg), level)
        
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

class NewsOn():
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()
        self.stateMenu = self.getStates()

        
    def openURL(self, url):
        try:
            cacheResponce = self.cache.get(ADDON_NAME + 'openURL, url = %s'%url)
            if not cacheResponce:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')
                page = urllib2.urlopen(request, timeout = 15)
                self.cache.set(ADDON_NAME + 'openURL, url = %s'%url, json.loads(page.read()), expiration=datetime.timedelta(hours=1))
            responce = self.cache.get(ADDON_NAME + 'openURL, url = %s'%url)
            if len(responce) > 0:
                return responce
        except urllib2.URLError, e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
        except socket.timeout, e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
        return {}

        
    def mainMenu(self):
        log('mainMenu')
        for item in MENU:
            self.addDir(*item)
        
                    
    def browseMenu(self, id=1):
        log('browseMenu, id = ' + str(id))
        self.stateMenu = [tuple(s.format(id) for s in tup) for tup in self.stateMenu]
        for item in self.stateMenu:
            self.addDir(*item)
            
            
    def getStates(self):
        log('getStates')
        state     = []
        stateLST  = []
        data = self.openURL(BASE_API)
        for channel in data:
            state.append(channel['config']['state'])
        states = collections.Counter(state)
        for key, value in sorted(states.iteritems()):
            stateLST.append(("%s"%(key), key , '{}'))
        del state[:]
        return stateLST
            
            
    def newsCasts(self, state):
        log('newsCasts, state = ' + state)
        urls = []
        data = self.openURL(BASE_API)
        for channel in data:
            if state in channel['config']['state']:
                chid   = channel['identifier']
                title  = channel['title']
                icon   = (channel['icon'] or ICON)
                for idx, stream in enumerate(channel['streams']):
                    #multiple urls, only and unique.
                    url = (stream['Url'].split('.m3u8?')[0])+'.m3u8'
                    offset = stream['OffsetFromNow']
                    delay  = url+'&delay=%d'
                    #todo do something with delay option?
                    if url not in urls:
                        urls.append(url)
                        chid = chid+'.%d'%idx if idx > 0 else chid
                        label      = "%s - %s" % (chid, title)
                        infoLabels ={"label":label ,"title":label}
                        infoArt    ={"thumb":icon,"poster":icon,"fanart":FANART,"icon":icon,"logo":icon} 
                        self.addLink(title, url, 9, infoLabels, infoArt)
        del urls[:]
        
        
    def videoclips(self, state):
        log('videoclips, state = ' + state)
        data = self.openURL(BASE_API)
        for channel in data:
            if state in channel['config']['state']:
                chid   = channel['identifier']
                title  = channel['title']
                icon   = (channel['icon'] or ICON)
                vidURL = channel['config']['localvodfeed']
                if vidURL:
                    label      = "%s - %s" % (chid, title)
                    infoLabels ={"label":label ,"title":label}
                    infoArt    ={"thumb":icon,"poster":icon,"fanart":FANART,"icon":ICON,"logo":ICON} 
                    self.addDir(label, vidURL, 4, infoLabels, infoArt)

                    
    def parseclips(self, url):
        log('parseclips, url = ' + url)
        #using xmltodict, feedparser too bulky for the job.
        feed = feedparser.parse(url)
        for item in feed['entries']:
            if item and 'summary_detail' in item:
                for vids in item['media_content']:
                    title = item['title']
                    url   = vids['url']
                    plot  = item['summary']
                    thumb = item['media_thumbnail'][0]['url']
                    infoLabels ={"label":title ,"title":title,"plot":plot}
                    infoArt    ={"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON} 
                    self.addLink(title, url, 9, infoLabels, infoArt)
                            
                    
                    
    def pagination(self, seq, rowlen):
        for start in xrange(0, len(seq), rowlen):
            yield seq[start:start+rowlen]

            
    def playVideo(self, name, url, list=None):
        log('playVideo')
        if not list:
            list = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list)

           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = stringify(name)
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
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = stringify(name)
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False:
            liz.setInfo(type="Video", infoLabels={"label":name,"title":name} )
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False:
            liz.setArt({'thumb':ICON,'fanart':FANART})
        else:
            liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
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
    mode=int(params["mode"])
except:
    mode=None
    
log("Mode: "+str(mode))
log("URL : "+str(url))
log("Name: "+str(name))

if mode==None:  NewsOn().mainMenu()
elif mode == 0: NewsOn().browseMenu(1)
elif mode == 1: NewsOn().newsCasts(url)
elif mode == 2: NewsOn().browseMenu(3)
elif mode == 3: NewsOn().videoclips(url)
elif mode == 4: NewsOn().parseclips(url)
elif mode == 9: NewsOn().playVideo(name, url)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)