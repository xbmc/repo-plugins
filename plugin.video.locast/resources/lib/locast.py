#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Locast.
#
# Locast is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Locast is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Locast.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback, calendar, collections
import urlparse, urllib, urllib2, socket, json, net
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

from simplecache import SimpleCache, use_cache

try:
    from multiprocessing import cpu_count 
    from multiprocessing.pool import ThreadPool 
    ENABLE_POOL = True
except: ENABLE_POOL = False

# Plugin Info
ADDON_ID      = 'plugin.video.locast'
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
CONTENT_TYPE  = 'episodes'
USER_EMAIL    = REAL_SETTINGS.getSetting('User_Email')
PASSWORD      = REAL_SETTINGS.getSetting('User_Password')
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
TOKEN         = REAL_SETTINGS.getSetting('User_Token')
COOKIE_JAR    = xbmc.translatePath(os.path.join(SETTINGS_LOC, "cookiejar.lwp"))
GEO_URL       = 'http://ip-api.com/json'
BASE_URL      = 'https://www.locast.org'
BASE_API      = BASE_URL + '/wp/wp-admin/admin-ajax.php'

MAIN_MENU     = [(LANGUAGE(30003), '' , 3),
                 (LANGUAGE(30004), '' , 4),
                 (LANGUAGE(30005), '' , 20)]
             
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def uni(string1, encoding = 'utf-8'):
    if isinstance(string1, basestring):
        if not isinstance(string1, unicode): string1 = unicode(string1, encoding)
        elif isinstance(string1, unicode): string1 = string1.encode('ascii', 'replace')
    return string1  
    
def inputDialog(heading=ADDON_NAME, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    retval = xbmcgui.Dialog().input(heading, default, key, opt, close)
    if len(retval) > 0: return retval    
    
def okDialog(str1, str2='', str3='', header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2, str3)

def okDisable(string1):
    if yesnoDialog(string1, no=LANGUAGE(30009), yes=LANGUAGE(30015)): 
        results = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method":"Addons.SetAddonEnabled", "params":{"addonid":"%s","enabled":false}, "id": 1}'%ADDON_ID)
        if results and "OK" in results: notificationDialog(LANGUAGE(30016))
    else: sys.exit()
        
def yesnoDialog(str1, str2='', str3='', header=ADDON_NAME, yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesno(header, str1, str2, str3, no, yes, autoclose)
    
def notificationDialog(message, header=ADDON_NAME, sound=False, time=1000, icon=ICON):
    try: xbmcgui.Dialog().notification(header, message, icon, time, sound)
    except: xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))
     
socket.setdefaulttimeout(TIMEOUT) 
class Locast(object):
    def __init__(self, sysARG):
        log('__init__, sysARG = ' + str(sysARG))
        self.token  = (TOKEN or LANGUAGE(30017))
        self.sysARG = sysARG
        self.cache  = SimpleCache()
        self.net    = net.Net(cookie_file=COOKIE_JAR,http_debug=DEBUG)
        self.lat, self.lon = self.setRegion()
        if self.login(USER_EMAIL, PASSWORD) == False: xbmc.executebuiltin("Container.Refresh")

        
    def buildHeader(self):
        header_dict               = {}
        header_dict['Accept']     = 'application/json, application/x-www-form-urlencoded, text/javascript, */*; q=0.01'
        header_dict['Connection'] = 'keep-alive'
        header_dict['Origin']     = BASE_URL
        header_dict['Referer']    = BASE_URL
        header_dict['Cookie']     = LANGUAGE(30014)%('%f%s%f'%(self.lat,'%2C',self.lon), USER_EMAIL, self.token)
        header_dict['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'
        return header_dict
        
    
    def login(self, user, password):
        log('login')
        if len(user) > 0:
            try: xbmcvfs.rmdir(COOKIE_JAR)
            except: pass
            
            if xbmcvfs.exists(COOKIE_JAR) == False:
                try:
                    xbmcvfs.mkdirs(SETTINGS_LOC)
                    f = xbmcvfs.File(COOKIE_JAR, 'w')
                    f.close()
                except: log('login, Unable to create the storage directory', xbmc.LOGERROR)
                
            data = json.loads(self.net.http_POST(BASE_API, form_data={'action':'member_login','username':user,'password':password}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
            '''{u'token': u'', u'role': 1}'''
            if data and 'token' in data: 
                self.token = data['token']
                if TOKEN != self.token: 
                    REAL_SETTINGS.setSetting('User_Token',self.token)
                    xbmc.executebuiltin("Container.Refresh")
        else:
            #firstrun wizard
            if yesnoDialog(LANGUAGE(30008),no=LANGUAGE(30009), yes=LANGUAGE(30010)):
                user     = inputDialog(LANGUAGE(30006))
                password = inputDialog(LANGUAGE(30007),opt=xbmcgui.ALPHANUM_HIDE_INPUT)
                REAL_SETTINGS.setSetting('User_Email'   ,user)
                REAL_SETTINGS.setSetting('User_Password',password)
                return self.login(user, password)
            else: 
                okDialog(LANGUAGE(30012))
                sys.exit()

        
    def getEPG(self, city):
        log("getEPG, city = " + city)
        epg = self.cache.get(ADDON_NAME + '.getEPG.%s'%city)
        '''[{"id":104,"dma":501,"name":"WCBSDT (WCBS-DT)","callSign":"WCBS","logoUrl":"https://fans.tmsimg.com/h5/NowShowing/28711/s28711_h5_aa.png","active":true,"affiliate":"CBS","affiliateName":"CBS",
             "listings":[{"stationId":104,"startTime":1535410800000,"duration":1800,"isNew":true,"audioProperties":"CC, HD 1080i, HDTV, New, Stereo","videoProperties":"CC, HD 1080i, HDTV, New, Stereo","programId":"EP000191906491","title":"Inside Edition","description":"Primary stories and alternative news.","entityType":"Episode","airdate":1535328000000,"genres":"Newsmagazine","showType":"Series"}]}'''
        if not epg:
            now = ('{0:.23s}{1:s}'.format(datetime.datetime.now().strftime('%Y-%m-%dT00:00:00'),'-07:00'))
            epg = json.loads(self.net.http_POST(BASE_API, form_data={'action':'get_epgs','dma':city,'start_time':now}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
            self.cache.set(ADDON_NAME + '.getEPG.%s'%city, epg, expiration=datetime.timedelta(hours=3))
        return epg

        
    def getCity(self):
        log("getCity")
        '''{"DMA": "501", "large_url": "https://s3.us-east-2.amazonaws.com/static.locastnet.org/cities/new-york.jpg", "name": "New York"}'''
        try: 
            city = self.cache.get(ADDON_NAME + 'getCity')
            if not city:
                city = json.loads(self.net.http_POST(BASE_API, form_data={'action':'get_dma','lat':self.lat,'lon':self.lon}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
                self.cache.set(ADDON_NAME + 'getCity', city, expiration=datetime.timedelta(hours=1))
            if city and 'DMA' not in city: okDisable(city.get('message'))
            else: return city
        except: okDisable(LANGUAGE(30013))

        
    def setRegion(self):
        try: 
            geo_data = self.cache.get(ADDON_NAME + 'setRegion')
            if not geo_data:
                geo_data = json.load(urllib2.urlopen(GEO_URL))
                self.cache.set(ADDON_NAME + 'setRegion', geo_data, expiration=datetime.timedelta(hours=1))
        except: geo_data = {'lat':0.0,'lon':0.0}
        return float('{0:.7f}'.format(geo_data['lat'])), float('{0:.7f}'.format(geo_data['lon']))

        
    def getRegion(self):
        log("getRegion")
        try: return self.getCity()['DMA']
        except: return sys.exit()
        

    def getStations(self, name, city, opt=None):
        log("getStations, name = " + name + ", city = " + city + ", opt = " + str(opt))
        stations = self.getEPG(city)
        for station in stations:
            if station['active'] == False: continue
            path     = str(station['id'])
            thumb    = station['logoUrl']
            listings = station['listings']
            label    = (station.get('affiliateName','') or station.get('affiliate','') or station.get('callSign','') or station.get('name',''))
            if opt == 'Live': self.buildListings(listings, label, thumb, path, opt)
            elif opt == 'Lineup' and name.lower() == label.lower(): return self.buildListings(listings, label, thumb, path, opt)
            elif opt == 'Lineups': self.addDir(label, city, 5, infoArt={"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON})
            else: continue
        
        
    def buildMenu(self, city):
        for item in MAIN_MENU: self.addDir(item[0],city,item[2])
            

    def buildListings(self, listings, chname, chlogo, path, opt='uEPG'):
        log('buildListings, chname = ' + chname)
        now = datetime.datetime.now()
        #todo added more meta from listings, ie mpaa, isNew, video/audio codec
        for listing in listings:
            try: starttime  = datetime.datetime.fromtimestamp(int(str(listing['startTime'])[:-3]))
            except: continue
            duration   = listing['duration']
            endtime    = starttime + datetime.timedelta(seconds=duration)
            label      = listing['title']
            # if listing['isNew']: label = '*%s'%label
            try: aired = datetime.datetime.fromtimestamp(int(str(listing['airdate'])[:-3]))
            except: aired = starttime
            try: type  = {'Series':'episode'}[listing['showType']]
            except: type = 'video'
            plot = (listing.get('description','') or label)
            if opt == 'Live' and starttime <= now <= endtime: label = '%s - %s'%(chname, label)
            elif opt == 'Lineup': label = '%s: %s - %s'%(starttime.strftime('%I:%M %p').lstrip('0'),chname,label)
            infoLabels = {"mediatype":type,"label":label,"title":label,'duration':duration,'plot':plot,'genre':listing['genres'],"aired":aired.strftime('%Y-%m-%d')}
            infoArt    = {"thumb":chlogo,"poster":chlogo,"fanart":FANART,"icon":chlogo,"logo":chlogo}
            if opt == 'Live':
                if starttime <= now <= endtime: return self.addLink(label, path, 9, infoLabels, infoArt, total=len(listings))
                else: continue
            else:self.addLink(label, path, 9, infoLabels, infoArt, total=len(listings))
        
        
    def uEPG(self):
        log('uEPG')
        #support for upcoming uEPG universal epg framework module, module will be available from the Kodi repository.
        #https://github.com/Lunatixz/KODI_Addons/tree/master/script.module.uepg
        stations = self.getEPG(self.getRegion())
        # return [self.buildGuide(station) for station in stations]
        return self.poolList(self.buildGuide, stations)
        
        
    def buildGuide(self, station):
        log('buildGuide')
        now        = datetime.datetime.now()
        chname     = (station.get('affiliateName','') or station.get('affiliate','') or station.get('callSign','') or station.get('name',''))
        chnum      = station['id']
        link       = str(chnum)
        chlogo     = station['logoUrl']
        isFavorite = False 
        newChannel = {}
        guidedata  = []
        newChannel['channelname']   = chname
        newChannel['channelnumber'] = chnum
        newChannel['channellogo']   = chlogo
        newChannel['isfavorite']    = isFavorite
        listings = station['listings']
        #todo added more meta from listings, ie mpaa, isNew, video/audio codec
        for listing in listings:
            try: type  = {'Series':'episode'}[listing['showType']]
            except: type = 'video'
            label = listing['title']
            plot  = (listing.get('description','') or label)
            try: aired = datetime.datetime.fromtimestamp(int(str(listing['airdate'])[:-3]))
            except: aired = now
            duration  = listing['duration']
            tmpdata   = {"mediatype":type,"label":label,"title":label,'duration':duration,'plot':plot,'genre':listing.get('genres',[]),"aired":aired.strftime('%Y-%m-%d')}
            starttime = datetime.datetime.fromtimestamp(int(str(listing['startTime'])[:-3]))
            endtime   = starttime + datetime.timedelta(seconds=duration)
            tmpdata['starttime'] = time.mktime((starttime).timetuple())
            tmpdata['url'] = self.sysARG[0]+'?mode=9&name=%s&url=%s'%(chname,link)
            tmpdata['art'] = {"thumb":chlogo,"poster":chlogo,"fanart":FANART,"icon":chlogo,"logo":chlogo}
            guidedata.append(tmpdata)
        newChannel['guidedata'] = guidedata
        return newChannel
        
        
    def poolList(self, method, items):
        results = []
        if ENABLE_POOL:
            pool = ThreadPool(cpu_count())
            results = pool.imap_unordered(method, items)
            pool.close()
            pool.join()
        else: results = [method(item) for item in items]
        results = filter(None, results)
        return results
        
        
    def resolveURL(self, id):
        log("resolveURL, id = " + str(id))
        '''{"active": true, "affiliate": "CBS", "affiliateName": "CBS", "callSign": "WCBS", "dma": 501, "id": 104, "logoUrl": "https://fans.tmsimg.com/h5/NowShowing/28711/s28711_h5_aa.png", "name": "WCBSDT (WCBS-DT)", "streamUrl": "https://www.kaltura.com/p/230/playManifest/entryId/1_qpkcj/uiConfId/40302/format/applehttp/protocol/https"}''' 
        return json.loads(self.net.http_POST(BASE_API, form_data={'action':'get_station','station_id':str(id),'lat':self.lat,'lon':self.lon}, headers=self.buildHeader()).content.encode("utf-8").rstrip())

        
    def playLive(self, name, url):
        log('playLive')
        liz  = xbmcgui.ListItem(name, path=self.resolveURL(int(url))['streamUrl'])
        if url.endswith('m3u8'):
            liz.setProperty('inputstreamaddon','inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type','hls') 
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)
    
           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)
     

    def getParams(self):
        return dict(urlparse.parse_qsl(self.sysARG[2][1:]))

            
    def run(self):  
        params=self.getParams()
        try: url=urllib.unquote_plus(params["url"])
        except: url=None
        try: name=urllib.unquote_plus(params["name"])
        except: name=None
        try: mode=int(params["mode"])
        except: mode=None
        log("Mode: "+str(mode))
        log("URL : "+str(url))
        log("Name: "+str(name))

        if mode==None:  self.buildMenu(self.getRegion())
        elif mode == 1: self.getStations(name, url)
        elif mode == 3: self.getStations(name, url, 'Live')
        elif mode == 4: self.getStations(name, url, 'Lineups')
        elif mode == 5: self.getStations(name, url, 'Lineup')
        elif mode == 9: self.playLive(name, url)
        elif mode == 20:xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%(urllib.quote(json.dumps(list(self.uEPG()))),urllib.quote(json.dumps(self.sysARG[0]+"?mode=20")),urllib.quote(json.dumps("7200")),urllib.quote(json.dumps("7"))))

        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=True)