#   Copyright (C) 2022 Lunatixz
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
import os, sys, time, datetime, traceback, random, routing
import socket, json, requests, collections, base64, gzip

from six.moves     import urllib
from itertools     import repeat, cycle, chain, zip_longest
from simplecache   import SimpleCache, use_cache
from kodi_six      import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode

try:
    from StringIO import StringIO ## for Python 2
except ImportError:
    from io import StringIO ## for Python 3
    
try:
    if (xbmc.getCondVisibility('System.Platform.Android') or xbmc.getCondVisibility('System.Platform.Windows')):
        from multiprocessing.dummy import Pool as ThreadPool
    else:
        from multiprocessing.pool  import ThreadPool
        
    from multiprocessing  import cpu_count
    from _multiprocessing import SemLock, sem_unlink #hack to raise two python issues. _multiprocessing import error, sem_unlink missing from native python (android).

    SUPPORTS_POOL = True
    CPU_COUNT     = cpu_count()
except Exception as e:
    CPU_COUNT     = 2
    SUPPORTS_POOL = False

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
ROUTER        = routing.Plugin()

## GLOBALS ##
DEFAULT_ENCODING = "utf-8"
CONTENT_TYPE     = 'episodes'
DISC_CACHE       = False
APIKEY           = REAL_SETTINGS.getSetting('MAPQUEST_API')
DEBUG            = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'

BASE_API      = 'https://newson.us/api'
OLD_API       = 'http://watchnewson.com/api/linear/channels'
LOGO_URL      = 'https://dummyimage.com/512x512/035e8b/FFFFFF.png&text=%s'
FAN_URL       = 'https://dummyimage.com/1280x720/035e8b/FFFFFF.png&text=%s'
MAP_URL       = 'https://www.mapquestapi.com/staticmap/v5/map?key=%s&center=%s&size=@2x'

@ROUTER.route('/')
def buildMenu():
    NewsOn().buildMenu()

@ROUTER.route('/live')
def buildLive(): pass
    # NewsOn().browse('now')
  
@ROUTER.route('/now')
def buildNow():
    NewsOn().browse('now')
  
@ROUTER.route('/new')
def buildBreaking():
    NewsOn().browse('new')
  
@ROUTER.route('/local')
def buildLocal():
    NewsOn().browse('local')
  
@ROUTER.route('/states')
def buildStates():
    NewsOn().browse('states')
  
@ROUTER.route('/stations/<state>')
def buildCities(state):
    NewsOn().browseCities(state)
    
@ROUTER.route('/stations/<state>/<city>')
def buildCity(state,city):
    NewsOn().browseChannels(state,city)
      
@ROUTER.route('/station/<chid>')
def buildStation(chid):
    NewsOn().browseStation(chid)
    
@ROUTER.route('/station/<chid>/<opt>')
def browseDetails(chid,opt):
    NewsOn().browseStation(chid,opt)
    
@ROUTER.route('/play/live')#unknown bug causing this route to be called during /ondemand parse. todo find issue.
def dummy():
    pass
    
@ROUTER.route('/play/live/<url>')
def playURL(url):
    NewsOn().playVideo(url,opt='live')
  
def log(msg, level=xbmc.LOGDEBUG):
    try: msg = str(msg)
    except: pass
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)

def encodeString(text):
    if not isinstance(text,str): text = str(text)
    return urllib.parse.quote_plus(text)

def decodeString(text):
    return urllib.parse.unquote_plus(text)

class NewsOn(object):
    def __init__(self, sysARG=sys.argv):
        log('__init__, sysARG = %s'%(sysARG))
        self.sysARG    = sysARG
        self.cache     = SimpleCache()
        self.region    = self.getCoordinates()
        self.states    = collections.Counter()
        self.cities    = collections.Counter()
        

    def buildMenu(self):
        log('buildMenu')
        MENU = [(LANGUAGE(30004), (buildNow,)     ),
                (LANGUAGE(30005), (buildBreaking,)),
                (LANGUAGE(30006), (buildLocal,)   ),
                (LANGUAGE(30007), (buildStates,)  )]
        for item in MENU: self.addDir(*item)
        
    
    def browse(self, opt='now'):
        log('browse, opt = %s'%(opt))
        items = {'now'   :self.getLiveNow,
                 'new'   :self.getBreakingNews,
                 'local' :self.getLocalStations,
                 'states':self.getStates}[opt]()
        if opt in ['states','cities']: 
            if opt == 'states':
                if self.poolList(self.buildStates, items.get('states',[])):
                    for state in self.states.keys(): 
                        self.addDir(state,(buildCities,state),infoArt={"thumb":FAN_URL%(state),"poster":LOGO_URL%(state),"fanart":FANART,"icon":ICON,"logo":ICON})
        else: 
            if not (list(set(self.poolList(self.buildChannel, items, opt)))): 
                self.addDir(LANGUAGE(30008), (buildMenu,))
        
    def browseCities(self, state):
        log('browseCities, state = %s'%(state))
        if self.poolList(self.buildStates, self.getStates().get('states',[])):
            if self.poolList(self.buildCities, self.states):
                for city in self.cities.get(state,[]): 
                    self.addDir(city,(buildCity,state,encodeString(city)),infoArt={"thumb":FAN_URL%(city),"poster":LOGO_URL%(city),"fanart":self.getMAP(city),"icon":ICON,"logo":ICON})
        
        
    def browseChannels(self, state, city):
        city = decodeString(city)
        log('browseChannels, state = %s, city = %s'%(state,city))
        if self.poolList(self.buildStates, self.getStates().get('states',[])):
            if self.poolList(self.buildCities, self.states):
                self.poolList(self.buildChannel, self.cities.get(state,{}).get(city,[]), 'channels')
                
                
    def browseStation(self, chid, opt=None):
        log('browseStation, chid = %s'%(chid))
        data    = self.getStationDetails(chid)
        channel = data.get('channel',{})
        chname  = channel.get('name','')
        chlogo = (channel.get('icon','') or LOGO_URL%(chname))
        if opt is None:
            for key in data.keys(): self.addDir(key.title(),(browseDetails,chid,key),infoArt={"thumb":chlogo,"poster":chlogo,"fanart":FANART,"icon":ICON,"logo":ICON})
        else:
            items =  data.get(opt,[])
            if opt != 'programs': items = [items]
            self.poolList(self.buildChannel, items, opt)
        
        
    def buildStates(self, state):
        for city in state.get('cities',[]):
            for channel in city.get('channels',[]):
                locations = channel.get('configValue',{}).get('locations',[])
                if not locations: continue
                self.states[locations[0]['state']] = state.get('cities',[])
                

    def buildCities(self, state):
        self.cities[state] = {}
        cities = self.states[state]
        for city in cities:
            for channel in city.get('channels',[]):
                locations = channel.get('configValue',{}).get('locations',[])
                if not locations: continue
                self.cities[state][locations[0]['city']] = city.get('channels',[])
    
    
    def buildChannel(self, data):
        item, opt = data
        if not item.get('live',False) and opt in ['now']: return None
        chid        = item['id']
        chname      = item['name']
        chdesc      = (item.get('description','') or xbmc.getLocalizedString(161))
        chlogo      = (item.get('icon','') or ICON)
        configValue = item.get('configValue',{})        
        latest      = item.get('latest',{}  or item)
        name        = (latest.get('name','' or chname))
        if chname != name:
            label   = '%s: [B]%s[/B]'%(chname,name)
        else:
            label   = chname
        plot        = (latest.get('description','')  or chdesc)
        url         = (latest.get('streamUrl','')    or chid)
        thumb       = (latest.get('thumbnailUrl','') or chlogo)
        try:
            starttime   = datetime.datetime.fromtimestamp(float(latest['startTime']))
            endtime     = datetime.datetime.fromtimestamp(float(latest['endTime']))
            duration    = (endtime - starttime).seconds
        except: 
            duration = 0
        infoLabel   = {"mediatype":"video","label":label,"title":label,"plot":plot,"duration":duration,"genre":['News']}
        infoArt     = {"thumb":thumb,"poster":thumb,"fanart":self.getMAP((configValue.get('latitude','undefined'),configValue.get('longitude','undefined'))),"icon":chlogo,"logo":chlogo} 
        if opt == 'local':infoArt['fanart'] = thumb
        
        if opt == 'channels':
            self.addDir(chname,(buildStation,chid),infoArt={"thumb":chlogo,"poster":chlogo,"fanart":FANART,"icon":ICON,"logo":ICON})
            return True
        else:
            self.addLink(label, (playURL,encodeString(url)), infoList=infoLabel, infoArt=infoArt)
            return True
        
        
    @use_cache(1)
    def getCoordinates(self):
        log('getCoordinates')
        return (self.openURL(BASE_API + '/getCoordinates'))
        

    def getLiveNow(self):
        log('getLiveNow')
        return (self.openURL(BASE_API + '/liveNow/999/{lat}/{lon}'.format(lat=self.region.get('latitude','undefined'),lon=self.region.get('longitude','undefined'))))


    def getBreakingNews(self):
        log('getBreakingNews')
        return (self.openURL(BASE_API + '/breakingNews/{lat}/{lon}'.format(lat=self.region.get('latitude','undefined'),lon=self.region.get('longitude','undefined'))))[0]


    def getStates(self):
        log('getStates')
        return (self.openURL(BASE_API + '/getStates/{lat}/{lon}'.format(lat=self.region.get('latitude','undefined'),lon=self.region.get('longitude','undefined'))))

        
    def getLocalStations(self, page=25):
        log('getLocalStations')
        return (self.openURL(BASE_API + '/localStations/{page}/{lat}/{lon}'.format(page=page,lat=self.region.get('latitude','undefined'),lon=self.region.get('longitude','undefined'))))


    def getStationDetails(self, id):
        log('getStationDetails')
        return (self.openURL(BASE_API + '/stationDetails/{chid}/{lat}/{lon}'.format(chid=id,lat=self.region.get('latitude','undefined'),lon=self.region.get('longitude','undefined'))))


    def getMAP(self, args):
        try:
            map = self.cache.get(ADDON_NAME + '.getMAPs, args = %s'%str(args))
            if not map:
                if len(args) == 2: map = MAP_URL%(APIKEY, '%s,%s'%(tuple(args)))
                else: map = MAP_URL%(APIKEY, urllib.parse.quote(args))
                self.cache.set(ADDON_NAME + '.getMAPs, args = %s'%str(args), map, expiration=datetime.timedelta(days=28))
            return map
        except: return FANART
            
        
    def openURL(self, url, param={}, life=datetime.timedelta(minutes=15)):
        try:
            log('openURL, url = %s'%(url))
            cacheName = '%s.openURL, url = %s.%s'%(ADDON_NAME,url,json.dumps(param))
            cacheresponse = self.cache.get(cacheName)
            if not cacheresponse:
                req = requests.get(url, param, headers={'Accept-Encoding':'gzip','User-Agent':'Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)'})
                try:
                    cacheresponse = json.loads(gzip.GzipFile(fileobj=StringIO(req.content)))
                except:
                    cacheresponse = req.json()
                req.close()
                self.cache.set(cacheName, json.dumps(cacheresponse), checksum=len(json.dumps(cacheresponse)), expiration=life)
                return cacheresponse
            else: return json.loads(cacheresponse)
        except Exception as e: 
            log("openURL Failed! %s"%(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return {}
            
                    
    def playVideo(self, url, opt='live'):
        url = decodeString(url)
        log('playVideo, url = %s, opt = %s'%(url,opt))
        liz = xbmcgui.ListItem(path=url)
        liz.setProperty('IsPlayable','true')
        liz.setProperty('IsInternetStream','true')
        xbmcplugin.setResolvedUrl(ROUTER.handle, True, liz)

             
    def poolList(self, method, items=None, args=None, chunk=25):
        log("poolList")
        results = []
        if SUPPORTS_POOL:
            pool = ThreadPool()
            if args is not None: 
                results = pool.imap(method, zip(items,repeat(args)))
            elif items: 
                results = pool.imap(method, items)#, chunksize=chunk)
            pool.close()
            pool.join()
        else:
            if args is not None: 
                results = [method((item, args)) for item in items]
            elif items: 
                results = [method(item) for item in items]
        return filter(None, results)


    def addPlaylist(self, name, path='', infoList={}, infoArt={}, infoVideo={}, infoAudio={}, infoType='video'):
        log('addPlaylist, name = %s'%name)

    
    def addLink(self, name, uri=(''), infoList={}, infoArt={}, infoVideo={}, infoAudio={}, infoType='video', total=0):
        log('addLink, name = %s'%name)
        liz = xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable','true')
        liz.setProperty('IsInternetStream','true')
        if infoList:  liz.setInfo(type=infoType, infoLabels=infoList)
        else:         liz.setInfo(type=infoType, infoLabels={"mediatype":infoType,"label":name,"title":name})
        if infoArt:   liz.setArt(infoArt)
        else:         liz.setArt({'thumb':ICON,'fanart':FANART})
        if infoVideo: liz.addStreamInfo('video', infoVideo)
        if infoAudio: liz.addStreamInfo('audio', infoAudio)
        if infoList.get('favorite',None) is not None: liz = self.addContextMenu(liz, infoList)
        xbmcplugin.addDirectoryItem(ROUTER.handle, ROUTER.url_for(*uri), liz, isFolder=False, totalItems=total)
                

    def addDir(self, name, uri=(''), infoList={}, infoArt={}, infoType='video'):
        log('addDir, name = %s'%name)
        liz = xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable','false')
        if infoList: liz.setInfo(type=infoType, infoLabels=infoList)
        else:        liz.setInfo(type=infoType, infoLabels={"mediatype":infoType,"label":name,"title":name})
        if infoArt:  liz.setArt(infoArt)
        else:        liz.setArt({'thumb':ICON,'fanart':FANART})
        if infoList.get('favorite',None) is not None: liz = self.addContextMenu(liz, infoList)
        xbmcplugin.addDirectoryItem(ROUTER.handle, ROUTER.url_for(*uri), liz, isFolder=True)
        
        
    def addContextMenu(self, liz, infoList={}):
        log('addContextMenu')
        return liz
        
        
    def run(self): 
        ROUTER.run()
        xbmcplugin.setContent(ROUTER.handle     ,CONTENT_TYPE)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(ROUTER.handle ,cacheToDisc=DISC_CACHE)