#   Copyright (C) 2020 Lunatixz
#
#
# This file is part of Channels DVR.
#
# Channels DVR is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Channels DVR is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Channels DVR.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, _strptime, datetime, re, traceback, json, inputstreamhelper, threading, requests

from itertools     import repeat, cycle, chain, zip_longest
from resources.lib import xmltv
from simplecache   import SimpleCache, use_cache
from six.moves     import urllib
from kodi_six      import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode

try:
    from multiprocessing import cpu_count 
    from multiprocessing.pool import ThreadPool 
    ENABLE_POOL = True
    CORES = cpu_count()
except: ENABLE_POOL = False

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY3: 
    basestring = str
    unicode = str
  
# Plugin Info
ADDON_ID      = 'plugin.video.channelsdvr'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
LANG          = 'en' #todo
TIMEOUT       = 30
CONTENT_TYPE  = 'episodes'
DISC_CACHE    = False
DTFORMAT      = '%Y%m%d%H%M%S'
PVR_CLIENT    = 'pvr.iptvsimple'
DNS_CLIENT    = '_channels_app._tcp'
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
M3UXMLTV      = REAL_SETTINGS.getSetting('Enable_M3UXMLTV') == 'true'
ENABLE_TS     = REAL_SETTINGS.getSetting('Enable_TS') == 'true'
ENABLE_CONFIG = REAL_SETTINGS.getSetting('Enable_Config') == 'true'
BUILD_FAVS    = REAL_SETTINGS.getSetting('Build_Favorites') == 'true'
USER_PATH     = REAL_SETTINGS.getSetting('User_Folder') 

BASE_URL      = 'http://%s:%s'%(REAL_SETTINGS.getSetting('User_IP'),REAL_SETTINGS.getSetting('User_Port')) #todo dns discovery?
TS            = '?format=ts' if ENABLE_TS else ''
M3U_URL       = '%s/devices/ANY/channels.m3u%s'%(BASE_URL,TS)
GUIDE_URL     = '%s/devices/ANY/guide'%(BASE_URL)
UPNEXT_URL    = '%s/dvr/recordings/upnext'%(BASE_URL)
SEARCH_URL    = '%s/dvr/guide/search/groups?q={query}'%(BASE_URL)

SUMMARY_URL   = '%s/dvr/recordings/summary'%(BASE_URL)
GROUPS_URL    = '%s/dvr/groups'%(BASE_URL)
MOVIES_URL    = '%s/dvr/groups/movies/files'%(BASE_URL)
SOURCES_URL   = '%s/dvr/lineup'%(BASE_URL)
PROGRAMS_URL  = '%s/dvr/programs'%(BASE_URL)

M3U_TEMP      = os.path.join(SETTINGS_LOC,'channelsdvr.tmp')
M3U_FILE      = os.path.join(USER_PATH,'channelsdvr.m3u')
XMLTV_FILE    = os.path.join(USER_PATH,'channelsdvr.xml')
MENU          = [(LANGUAGE(30002), '', 0),
                 (LANGUAGE(30017), '', 1),
                 (LANGUAGE(30003), '', 2)]
                # (LANGUAGE(30015), '', 2)]
                #(LANGUAGE(30013), '', 8)]
                
xmltv.locale      = 'UTF-8'
xmltv.date_format = DTFORMAT

def getPTVL():
    return xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
    
def notificationDialog(message, header=ADDON_NAME, show=True, sound=False, time=1000, icon=ICON):
    try:    xbmcgui.Dialog().notification(header, message, icon, time, sound=False)
    except: xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))
   
def strpTime(datestring, format='%Y-%m-%dT%H:%MZ'):
    try: return datetime.datetime.strptime(datestring, format)
    except TypeError: return datetime.datetime.fromtimestamp(time.mktime(time.strptime(datestring, format)))

def timezone():
    if time.localtime(time.time()).tm_isdst and time.daylight: return time.altzone / -(60*60) * 100
    else: return time.timezone / -(60*60) * 100
    
def getLocalTime():
    offset = (datetime.datetime.utcnow() - datetime.datetime.now())
    return time.time() + offset.total_seconds()
        
def log(msg, level=xbmc.LOGDEBUG):
    try:   msg = str(msg)
    except Exception as e: 'log str failed! %s'%(str(e))
    if not DEBUG and level != xbmc.LOGERROR: return
    try:   xbmc.log('%s-%s-%s'%(ADDON_ID,ADDON_VERSION,msg),level)
    except Exception as e: 'log failed! %s'%(e)

def getKeyboard(default='',header=ADDON_NAME):
    kb = xbmc.Keyboard(default,header)
    xbmc.sleep(1000)
    kb.doModal()
    if kb.isConfirmed(): return kb.getText()
    return False

def slugify(text):
    non_url_safe = [' ','"', '#', '$', '%', '&', '+',',', '/', ':', ';', '=', '?','@', '[', '\\', ']', '^', '`','{', '|', '}', '~', "'"]
    non_url_safe_regex = re.compile(r'[{}]'.format(''.join(re.escape(x) for x in non_url_safe)))
    text = non_url_safe_regex.sub('', text).strip()
    text = u'_'.join(re.split(r'\s+', text))
    return text
     
class Service(object):
    def __init__(self, sysARG=sys.argv):
        self.running    = False
        self.myMonitor  = xbmc.Monitor()
        self.myChannels = Channels(sysARG)


    def run(self):
        while not self.myMonitor.abortRequested():
            if self.myMonitor.waitForAbort(2): break
            elif not M3UXMLTV or self.running: continue
            lastCheck  = float(REAL_SETTINGS.getSetting('Last_Scan') or 0)
            conditions = [xbmcvfs.exists(M3U_FILE),xbmcvfs.exists(XMLTV_FILE)]
            if (time.time() > (lastCheck + 3600)) or False in conditions:
                self.running = True
                if self.myChannels.buildService(): 
                    REAL_SETTINGS.setSetting('Last_Scan',str(time.time()))
                    notificationDialog(LANGUAGE(30007))
                self.running = False


class Channels(object):
    def __init__(self, sysARG=sys.argv):
        log('__init__, sysARG = %s'%(sysARG))
        self.sysARG     = sysARG
        self.cache      = SimpleCache()
        self.m3uList    = []
        self.xmltvList  = {'data'       : self.getData(),
                           'channels'   : [],
                           'programmes' : []}
        self.channels   = self.getChannels(self.getM3U(),ADDON_VERSION)
        self.programmes = self.getGuidedata(ADDON_VERSION)
        
        
    def openURL(self, url, life=datetime.timedelta(minutes=5)):
        log('openURL, url = %s'%(url))
        try:
            cacheName = '%s.%s.openURL.%s'%(ADDON_ID,ADDON_VERSION,url)
            cacheResponse = self.cache.get(cacheName)
            if not cacheResponse:
                req = requests.get(url)
                cacheResponse = req.text
                req.close()
                self.cache.set(cacheName, cacheResponse, checksum=len(cacheResponse), expiration=life)
            return cacheResponse
        except Exception as e: 
            log("openURL, Failed! %s"%(e), xbmc.LOGERROR)
            notificationDialog(LANGUAGE(30001))
            return ''
        

    def saveURL(self, url, file):
        log('saveURL, url = %s, file = %s'%(url,file))
        try:
            #grab unadulterated m3u, option to preserve?
            response = self.openURL(url)
            fle = xbmcvfs.File(file, 'w')
            fle.write(response)
            fle.close()
            return response
        except Exception as e: 
            log("saveURL, Failed! %s"%(e), xbmc.LOGERROR)
            return ''
        

    def getM3U(self):
        log('getM3U')
        m3uListTMP = self.saveURL(M3U_URL,M3U_TEMP).split('\n')
        return ['%s\n%s'%(line,m3uListTMP[idx+1]) for idx, line in enumerate(m3uListTMP) if line.startswith('#EXTINF:')]


    # @use_cache(1)
    def getChannels(self, lines, version=ADDON_VERSION):
        log('getChannels')
        items = []
        for line in lines:
            if line.startswith('#EXTINF:'):
                groups = re.compile('tvg-chno=\"(.*?)\" tvg-logo=\"(.*?)\" tvg-name=\"(.*?)\" group-title=\"(.*?)\",(.*)\\n(.*)', re.IGNORECASE).search(line)
                items.append({'number':groups.group(1),'logo':groups.group(2),'name':groups.group(3),'groups':groups.group(4),'title':groups.group(5),'url':groups.group(6)})
        try: xbmcvfs.delete(M3U_TEMP)
        except: pass
        return sorted(items, key=lambda k: k['number'])
        

    def buildM3U(self, channel):
        litem = '#EXTINF:-1 tvg-chno="%s" tvg-id="%s" tvg-name="%s" tvg-logo="%s" group-title="%s" radio="%s",%s\n%s\n'
        logo  = (channel.get('logo','') or ICON)
        group = channel.get('groups','').split(';')
        if BUILD_FAVS and 'Favorites' not in group: return False
        group.append(ADDON_NAME)
        radio = False
        self.m3uList.append(litem%(channel['number'],'%s@%s'%(channel['number'],slugify(ADDON_NAME)),channel['name'],logo,';'.join(group),str(radio).lower(),channel['title'],channel['url']))
        return True
        
        
    def loadM3U(self):
        self.poolList(self.buildM3U, self.getChannels(self.getM3U()))
        return self.saveM3U(M3U_FILE)
        

    # @use_cache(1)
    def getGuidedata(self, version=ADDON_VERSION):
        log('getGuidedata')
        return json.loads(self.openURL(GUIDE_URL))


    def loadXMLTV(self):
        log('loadXMLTV')
        self.poolList(self.buildXMLTV, self.programmes)
        return self.saveXMLTV()
        
        
    def buildXMLTV(self, content):
        channel    = content['Channel']
        programmes = content['Airings']
        if channel.get('Hidden',False): return False
        elif BUILD_FAVS and not channel.get('Favorite',False): return False
        self.addChannel(channel)
        [self.addProgram(program) for program in  programmes]
        return True
        

    def getData(self):
        log('getData')
        return {'date'                : datetime.datetime.fromtimestamp(float(time.time())).strftime(xmltv.date_format),
                'generator-info-name' : '%s Guidedata'%(ADDON_NAME),
                'generator-info-url'  : ADDON_ID,
                'source-info-name'    : ADDON_NAME,
                'source-info-url'     : ADDON_ID}
                
    
    def saveM3U(self, file):
        fle = xbmcvfs.File(M3U_FILE, 'w')
        [fle.write(m3uList) for m3uList in self.m3uList]
        fle.close()
        return True
        

    def saveXMLTV(self, reset=True):
        log('saveXMLTV')
        data   = self.xmltvList['data']
        writer = xmltv.Writer(encoding=xmltv.locale, date=data['date'],
                              source_info_url     = data['source-info-url'], 
                              source_info_name    = data['source-info-name'],
                              generator_info_url  = data['generator-info-url'], 
                              generator_info_name = data['generator-info-name'])
               
        channels = self.sortChannels(self.xmltvList['channels'])
        for channel in channels: writer.addChannel(channel)
        programmes = self.sortProgrammes(self.xmltvList['programmes'])
        for program in programmes: writer.addProgramme(program)
        log('save, saving to %s'%(XMLTV_FILE))
        writer.write(XMLTV_FILE, pretty_print=True)
        return True
        
        
    def sortChannels(self, channels=None):
        channels.sort(key=lambda x:x['id'])
        log('sortChannels, channels = %s'%(len(channels)))
        return channels


    def sortProgrammes(self, programmes=None):
        programmes.sort(key=lambda x:x['channel'])
        programmes.sort(key=lambda x:x['start'])
        log('sortProgrammes, programmes = %s'%(len(programmes)))
        return programmes


    def addChannel(self, channel):
        citem    = ({'id'           : '%s@%s'%(channel['Number'],slugify(ADDON_NAME)),
                     'display-name' : [(channel['Name'], LANG)],
                     'icon'         : [{'src':channel.get('Image',ICON)}]})
        log('addChannel = %s'%(citem))
        self.xmltvList['channels'].append(citem)
        return True


    def addProgram(self, program):
        pitem = {'channel'     : '%s@%s'%(program['Channel'],slugify(ADDON_NAME)),
                # 'credits'     : {'director': [program.get('Directors',[])], 'cast': [program.get('Cast',[])]},
                 'category'    : [(genre,LANG) for genre in program.get('Categories',['Undefined'])],
                 'title'       : [(self.cleanString(program['Title']), LANG)],
                 'desc'        : [((self.cleanString(program.get('Summary','')) or xbmc.getLocalizedString(161)), LANG)],
                 'stop'        : (strpTime(program['Raw']['endTime']).strftime(xmltv.date_format)),
                 'start'       : (strpTime(program['Raw']['startTime']).strftime(xmltv.date_format)),
                 'icon'        : [{'src': program.get('Image',FANART)}]}
                      
        if program.get('EpisodeTitle',''):
            pitem['sub-title'] = [(self.cleanString(program['EpisodeTitle']), LANG)]
            
        if program.get('OriginalDate',''):
            try:
                pitem['date'] = (strpTime(program['OriginalDate'], '%Y-%m-%d')).strftime('%Y%m%d')
            except: pass
            
        if program.get('Tags',None):
            if 'New' in program.get('Tags',[]): pitem['new'] = '' #write blank tag, tag == True
        if program['Raw'].get('ratings',None):
            rating = program['Raw'].get('ratings',[{}])[0].get('code','')
            if rating.startswith('TV'): 
                pitem['rating'] = [{'system': 'VCHIP', 'value': rating}]
            else:  
                pitem['rating'] = [{'system': 'MPAA', 'value': rating}]
            
        if program.get('EpisodeNumber',''): 
            SElabel = 'S%sE%s'%(str(program.get("SeasonNumber",0)).zfill(2),str(program.get("EpisodeNumber",0)).zfill(2))
            pitem['episode-num'] = [(SElabel, 'onscreen')]

        log('addProgram = %s'%(pitem))
        self.xmltvList['programmes'].append(pitem)
        return True
        

    def cleanString(self, text):
        return text.encode("ascii", errors="replace").decode()

        
    def playVideo(self, name, url):
        log('playVideo, url = %s'%url)
        if url.lower() == 'next_show': 
            notificationDialog(LANGUAGE(30012), time=4000)
            found = False
            liz   = xbmcgui.ListItem(name)
        else:
            found = True
            liz   = xbmcgui.ListItem(name, path=url)
            liz.setProperty("IsPlayable","true")
            liz.setProperty("IsInternetStream","true")
            if 'm3u8' in url.lower() and inputstreamhelper.Helper('hls').check_inputstream():
                liz.setProperty('inputstreamaddon','inputstream.adaptive')
                liz.setProperty('inputstream.adaptive.manifest_type','hls')
            # elif 'mpg' in url.lower():
                # liz.setProperty('inputstreamaddon','inputstream.ffmpegdirect')
                # liz.setProperty('inputstream.ffmpegdirect.stream_mode','timeshift')
                # liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream','true')
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), found, liz)


    def addLink(self, name, path, mode='',icon=ICON, liz=None, total=0):
        if liz is None:
            liz=xbmcgui.ListItem(name)
            liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
            liz.setArt({'thumb':icon,'logo':icon,'icon':icon})
            liz.setProperty('IsPlayable', 'true')
        log('addLink, name = %s'%(name))
        u=self.sysARG[0]+"?url="+urllib.parse.quote(path)+"&name="+urllib.parse.quote(name)+"&mode="+str(mode)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, path, mode='',icon=ICON, liz=None):
        log('addDir, name = %s'%(name))
        if liz is None:
            liz=xbmcgui.ListItem(name)
            liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
            liz.setArt({'thumb':icon,'logo':icon,'icon':icon})
        liz.setProperty('IsPlayable', 'false')
        u=self.sysARG[0]+"?url="+urllib.parse.quote(path)+"&name="+urllib.parse.quote(name)+"&mode="+str(mode)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)
     
     
    def poolList(self, method, items=None, args=None, chunk=25):
        log("poolList")
        results = []
        if ENABLE_POOL:
            pool = ThreadPool(CORES)
            if args is not None: 
                results = pool.map(method, zip(items,repeat(args)))
            elif items: 
                results = pool.map(method, items)#, chunksize=chunk)
            pool.close()   
            pool.join()
        else:
            if args is not None: 
                results = [method((item, args)) for item in items]
            elif items: 
                results = [method(item) for item in items]
        return filter(None, results)


    def mainMenu(self):
        log('mainMenu')
        for item in MENU: self.addDir(*item)
        

    def buildItemListItem(self, label, path, info={}, art={}, mType='video', oscreen=True, playable=True):
        listitem = xbmcgui.ListItem(offscreen=oscreen)
        listitem.setLabel(label)
        listitem.setPath(path)
        listitem.setInfo(type=mType, infoLabels=info)
        listitem.setArt(art)
        if playable: listitem.setProperty("IsPlayable","true")
        return listitem
        
        
    def getLiveURL(self, chid, channels):
        log('getLiveURL, chid = %s'%(chid))
        for channel in channels:
            if channel['number'] == chid:
                return channel['url']
        return ''
        
        
    def buildLive(self, favorites=False):
        log('buildLive')
        self.poolList(self.buildPlayItem, self.programmes, ('live',favorites))
        
        
    def buildPlayItem(self, data):
        content, opt   = data
        opt, favorites = opt
        channel    = content['Channel']
        programmes = content['Airings']
        liveMatch  = False
        if channel['Hidden'] == True: return
        elif favorites and not channel.get('Favorite',False): return
        tz  = (timezone()//100)*60*60
        now = (datetime.datetime.fromtimestamp(float(getLocalTime()))) + datetime.timedelta(seconds=tz)
        url = self.getLiveURL(channel['Number'], self.channels)
        for program in programmes:
            label = program.get('Title','')
            path  = program.get('Path','')
            stop  = (strpTime(program['Raw']['endTime']))  + datetime.timedelta(seconds=tz)
            start = (strpTime(program['Raw']['startTime']))+ datetime.timedelta(seconds=tz)
            if now > stop: continue
            elif now >= start and now < stop:
                if opt == 'live':
                    if label:
                        label = '%s| %s: [B]%s[/B]'%(channel['Number'],channel['Name'],program.get('Title',''))
                    else: 
                        label = '%s| %s'%(channel['Number'],channel['Name'])
                    liveMatch = True
                elif opt == 'lineup':
                    label = '%s - [B]%s[/B]'%(start.strftime('%I:%M %p').lstrip('0'),program.get('Title',''))
            elif opt == 'live': continue
            elif opt == 'lineup':
                url   = 'next_show'
                label = '%s - %s'%(start.strftime('%I:%M %p').lstrip('0'),program.get('Title',''))
                   
            icon  = channel.get('Image',ICON)
            thumb = program.get('Image',icon)
            info  = {'label':label,'title':label,'duration':program.get('Duration',0),'genre':program.get('Genres',[]),'plot':program.get('Summary',xbmc.getLocalizedString(161)),'aired':program.get('OriginalDate','')}
            art   = {'icon':icon, 'thumb':thumb}
            self.addLink(channel['Name'], url, '9', liz=self.buildItemListItem(label, url, info, art))
            if liveMatch: break
            
            
    def buildRecordingItem(self, item):
        item['Airings']  = [item['Airing'].copy()]
        item['Channel'] = {'Hidden':False,'Number':0,'Name':'','Image':''}
        self.buildPlayItem((item,'recordings'))
        
            
    def buildRecordings(self):
        self.poolList(self.buildRecordingItem, json.loads(self.openURL(UPNEXT_URL)))
            
        
    def search(self, term=None):
        #todo match id with programmes
        if term is None: term = getKeyboard(header=LANGUAGE(30014))
        if term:
            log('search, term = %s'%(term))
            query = json.loads(self.openURL(SEARCH_URL.format(query=term)))


    def buildLineup(self, chid=None):
        log('buildLineup, chid = %s'%(chid))
        if chid is None:
            self.poolList(self.buildLineupItem, self.programmes)
        else:
            self.poolList(self.buildPlayItem, [program for program in self.programmes if program['Channel']['Number'] == chid], 'lineup')

  
    def buildLineupItem(self, content):
        channel = content['Channel']
        label = '%s| %s'%(channel['Number'],channel['Name'])
        self.addDir(label, channel['Number'], '1', channel.get('Image',ICON), liz=None)
        
        
    def buildService(self):
        log('buildService')
        if self.loadM3U() and self.loadXMLTV():
            self.chkSettings()
            return True
        
        
    def togglePVR(self, state='true'):
        return xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"%s","enabled":%s}, "id": 1}'%(PVR_CLIENT,state))

        
    def getPVR(self):
        try: return xbmcaddon.Addon(PVR_CLIENT)
        except: # backend disabled?
            self.togglePVR('true')
            xbmc.sleep(1000)
            return xbmcaddon.Addon(PVR_CLIENT)
            
            
    def chkSettings(self):
        if ENABLE_CONFIG:
            addon = self.getPVR()
            check = [addon.getSetting('m3uRefreshMode')         == '1',
                     addon.getSetting('m3uRefreshIntervalMins') == '5',
                     addon.getSetting('logoFromEpg')            == '1',
                     addon.getSetting('m3uPathType')            == '0',
                     addon.getSetting('m3uPath')                == M3U_FILE,
                     addon.getSetting('epgPathType')            == '0',
                     addon.getSetting('epgPath')                == XMLTV_FILE]
            if False in check: self.configurePVR()
        
        
    def configurePVR(self):
        addon = self.getPVR()
        addon.setSetting('m3uRefreshMode'        , '1')
        addon.setSetting('m3uRefreshIntervalMins', '5')
        addon.setSetting('logoFromEpg'           , '1')
        addon.setSetting('m3uPathType'           , '0')
        addon.setSetting('m3uPath'               , M3U_FILE)
        addon.setSetting('epgPathType'           , '0')
        addon.setSetting('epgPath'               , XMLTV_FILE)
        
        
    def getParams(self):
        return dict(urllib.parse.parse_qsl(self.sysARG[2][1:]))

            
    def run(self):    
        params=self.getParams()
        try:    url  = urllib.parse.unquote_plus(params["url"])
        except: url  = None
        try:    name = urllib.parse.unquote_plus(params["name"])
        except: name = None
        try:    mode = int(params["mode"])
        except: mode = None
        log("Mode: %s, Name: %s, URL : %s"%(mode,name,url))

        if   mode==None: self.mainMenu()
        elif mode == 0:  self.buildLive()
        elif mode == 1:  self.buildLive(favorites=True)
        elif mode == 2:  self.buildLineup(url)
        elif mode == 3:  self.buildRecordings()
        elif mode == 8:  self.search(name)
        elif mode == 9:  self.playVideo(name, url)
        
        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=DISC_CACHE)