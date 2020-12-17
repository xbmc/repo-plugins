#   Copyright (C) 2019 Lunatixz
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
import os, sys, time, datetime, traceback, feedparser, random
import socket, json, collections, gzip
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

from io            import BytesIO
from simplecache   import SimpleCache, use_cache
from six.moves     import urllib
from kodi_six      import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode

# Plugin Info
ADDON_ID      = 'plugin.video.newson'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString
NEWSART       = os.path.join(ADDON_PATH,'resources','images','newscast.jpg')
CLIPART       = os.path.join(ADDON_PATH,'resources','images','videoclips.jpg')

## GLOBALS ##
TIMEOUT       = 15
CONTENT_TYPE  = 'episodes'
APIKEY        = REAL_SETTINGS.getSetting('MAPQUEST_API')
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
BASE_API      = 'http://watchnewson.com/api/linear/channels'
LOGO_URL      = 'https://dummyimage.com/512x512/035e8b/FFFFFF.png&text=%s'
FAN_URL       = 'https://dummyimage.com/1280x720/035e8b/FFFFFF.png&text=%s'
MAP_URL       = 'https://www.mapquestapi.com/staticmap/v5/map?key=%s&center=%s&size=@2x'

MENU          = [(LANGUAGE(30002), '0', 0, False, {"thumb":NEWSART,"poster":NEWSART,"fanart":FANART,"icon":ICON,"logo":ICON}),
                 (LANGUAGE(30003), '2', 2, False, {"thumb":CLIPART,"poster":CLIPART,"fanart":FANART,"icon":ICON,"logo":ICON})]
           
def log(msg, level=xbmc.LOGDEBUG):
    try: msg = str(msg)
    except: pass
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
       
socket.setdefaulttimeout(TIMEOUT)
class NewsOn(object):
    def __init__(self, sysARG):
        log('__init__, sysARG = %s'%(sysARG))
        self.sysARG    = sysARG
        self.cache     = SimpleCache()
        self.stateMenu = self.getStates()


    def getMAP(self, args):
        try:
            map = self.cache.get(ADDON_NAME + '.getMAPs, args = %s'%str(args))
            if not map:
                if len(args) == 2: map = MAP_URL%(APIKEY, '%s,%s'%(tuple(args)))
                else: map = MAP_URL%(APIKEY, urllib.parse.quote(args))
                self.cache.set(ADDON_NAME + '.getMAPs, args = %s'%str(args), map, expiration=datetime.timedelta(days=28))
            return map
        except: return FANART
            
        
    def openURL(self, url):
        try:
            log('openURL, url = %s'%(url))
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                request = urllib.request.Request(url)
                request.add_header('Accept-Encoding', 'gzip')
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib.request.urlopen(request, timeout = TIMEOUT)
                if response.info().get('Content-Encoding') == 'gzip': 
                    cacheresponse = gzip.GzipFile(fileobj=BytesIO(response.read())).read()
                else: 
                    cacheresponse = response
                response.close()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, cacheresponse, expiration=datetime.timedelta(minutes=5))
            return json.loads(cacheresponse)
        except Exception as e: 
            log("openURL Failed! %s"%(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
        
        
    def mainMenu(self):
        log('mainMenu')
        for item in MENU: self.addDir(*item)
        
                    
    def browseMenu(self, id=1):
        log('browseMenu, id = %s'%(id))
        self.stateMenu = [tuple(s.format(id) for s in tup) for tup in self.stateMenu]
        for item in self.stateMenu: 
            self.addDir(item[0], item[1], item[2], False, {"thumb":LOGO_URL%item[0],"poster":LOGO_URL%item[0],"fanart":self.getMAP((item[0])),"landscape":FAN_URL%(item[0]),"icon":ICON,"logo":ICON})


    def cleanState(self, state):
        return state.strip(',').strip()

          
    def getStates(self):
        log('getStates')
        state     = []
        stateLST  = []
        data = self.openURL(BASE_API)
        if len(data) == 0: return []
        for channel in data:
            try:    state.append(self.cleanState(channel['config']['state']))
            except: state.append(self.cleanState(channel['config']['locations'][0]['state']))
        states = collections.Counter(state)
        for key, value in sorted(states.items()): stateLST.append(("%s"%(key), key , '{}'))
        return stateLST
            
            
    def newsCasts(self, state):
        log('newsCasts, state = %s'%(state))
        urls = []
        data = self.openURL(BASE_API)
        if len(data) == 0: return
        for channel in data:
            try: states = self.cleanState(channel['config']['state'])
            except: states = self.cleanState(channel['config']['locations'][0]['state'])
            if state in states:
                chid   = str(channel['identifier'])
                title  = channel['title']
                lat    = channel['config']['latitude']
                lon    = channel['config']['longitude']
                icon   = (channel['icon'] or ICON)
                for idx, stream in enumerate(channel['streams']):
                    if stream['StreamType'] == 'website': continue
                    url = stream['Url']
                    offset = stream['OffsetFromNow']
                    delay  = url+'&delay=%d' # todo do something with delay option?
                    if url in urls: continue # filter duplicate feeds
                    if url not in urls: urls.append(url)
                    chid = chid+'.%d'%idx if idx > 0 else chid
                    label      = "%s - %s" % (chid, title)
                    infoLabels ={"mediatype":"episodes","label":label,"title":label,'plot':label}
                    infoArt    ={"thumb":icon,"poster":icon,"fanart":self.getMAP((lat, lon)),"landscape":FAN_URL%(channel['config']['locations'][0]["state"]),"icon":icon,"logo":icon} 
                    self.addLink(title, url, 9, infoLabels, infoArt)
        
        
    def videoclips(self, state):
        log('videoclips, state = %s'%(state))
        data = self.openURL(BASE_API)
        if len(data) == 0: return
        for channel in data:
            try: states = self.cleanState(channel['config']['state'])
            except: states = self.cleanState(channel['config']['locations'][0]['state'])
            if state in states:
                try: 
                    vidURL = channel['config']['localvodfeed']
                    chid   = str(channel['identifier'])
                    title  = channel['title']
                    lat    = channel['config']['latitude']
                    lon    = channel['config']['longitude']
                    icon   = (channel['icon'] or ICON)
                    label  = "%s - %s" % (chid, title)
                    infoLabels ={"mediatype":"video","label":label,"title":label}
                    infoArt    ={"thumb":icon,"poster":icon,"fanart":self.getMAP((lat, lon)),"landscape":FAN_URL%(channel['config']['locations'][0]["state"]),"icon":ICON,"logo":ICON} 
                    self.addDir(label, vidURL, 4, infoLabels, infoArt)
                except: continue


    def parseclips(self, url):
        if url is None: return
        log('parseclips, url = %s'%(url))
        feed = feedparser.parse(url)
        for item in feed['entries']:
            if item and 'summary_detail' in item:
                for vids in item['media_content']:
                    try:
                        title = item['title']
                        url   = vids['url']
                        plot  = item['summary']
                        aired = item.get('published','').replace(' EST','').replace(' UTC','').replace(' GMT','')
                        try: aired = (datetime.datetime.strptime(aired, '%a, %d %b %Y %H:%M:%S'))
                        except: aired = datetime.datetime.now()
                        aired = aired.strftime("%Y-%m-%d")
                        try: thumb = item['media_thumbnail'][0]['url']
                        except: thumb = FANART
                        tagLST = []
                        if 'tags' in item:
                            for tag in item['tags']: tagLST.append(((tag['term']).split('/')[0]).title())
                        if len(tagLST) > 0: genre = (tagLST[0] or '')
                        infoLabels ={"mediatype":"episode","label":title,"title":title,"plot":plot,"aired":aired,'genre':genre,'tags':tagLST}
                        infoArt    ={"thumb":thumb,"poster":thumb,"fanart":thumb,"icon":ICON,"logo":ICON} 
                        self.addLink(title, url, 8, infoLabels, infoArt)
                    except: continue
                    
                    
    def playVideo(self, name, url, live=False):
        log('playVideo')
        liz = xbmcgui.ListItem(name, path=url)
        liz.setProperty('IsPlayable','true')
        liz.setProperty('IsInternetStream','true')
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)

           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        log('addLink, name = %s'%(name))
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable','true')
        liz.setProperty('IsInternetStream','true')
        if infoList == False: liz.setInfo( type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.parse.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        log('addDir, name = %s'%(name))
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.parse.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)
        
        
    def getParams(self):
        return dict(urllib.parse.parse_qsl(self.sysARG[2][1:]))

            
    def run(self):  
        params=self.getParams()
        try:    url=urllib.parse.unquote_plus(params["url"])
        except: url=None
        try:    name=urllib.parse.unquote_plus(params["name"])
        except: name=None
        try:    mode=int(params["mode"])
        except: mode=None
        log("Mode: %s, URL : %s, Name: %s"%(mode,url,name))

        if mode==None:  self.mainMenu()
        elif mode == 0: self.browseMenu(1)
        elif mode == 1: self.newsCasts(url)
        elif mode == 2: self.browseMenu(3)
        elif mode == 3: self.videoclips(url)
        elif mode == 4: self.parseclips(url)
        elif mode == 8: self.playVideo(name, url)
        elif mode == 9: self.playVideo(name, url, True)

        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=True)