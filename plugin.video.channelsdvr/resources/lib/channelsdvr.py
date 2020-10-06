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
import os, sys, time, _strptime, datetime, re, traceback, json, inputstreamhelper, threading

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
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
M3UXMLTV      = REAL_SETTINGS.getSetting('Enable_M3UXMLTV') == 'true'
ENABLE_TS     = REAL_SETTINGS.getSetting('Enable_TS') == 'true'
ENABLE_CONFIG = REAL_SETTINGS.getSetting('Enable_Config') == 'true'
USER_PATH     = REAL_SETTINGS.getSetting('User_Folder') 

BASE_URL      = 'http://%s:%s'%(REAL_SETTINGS.getSetting('User_IP'),REAL_SETTINGS.getSetting('User_Port')) #todo dns discovery?
TS            = '?format=ts' if ENABLE_TS else ''
M3U_URL       = '%s/devices/ANY/channels.m3u%s'%(BASE_URL,TS)
GUIDE_URL     = '%s/devices/ANY/guide'%(BASE_URL)
UPNEXT_URL    = '%s/dvr/recordings/upnext'%(BASE_URL)
GROUPS_URL    = '%s/dvr/groups'%(BASE_URL)
SEARCH_URL    = '%s/dvr/guide/search/groups?q={query}'%(BASE_URL)
SUMMARY_URL   = '%s/dvr/recordings/summary'%(BASE_URL)
M3U_FILE      = os.path.join(USER_PATH,'channelsdvr.m3u')
XMLTV_FILE    = os.path.join(USER_PATH,'channelsdvr.xml')
MENU          = [(LANGUAGE(30002), '', 0),
                (LANGUAGE(30003), '', 1)]
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
    
    
class Service(object):
    def __init__(self, sysARG=sys.argv):
        self.running    = False
        self.myMonitor  = xbmc.Monitor()
        self.myChannels = Channels(sysARG)
        
        
    def run(self):
        while not self.myMonitor.abortRequested():
            if self.myMonitor.waitForAbort(2): break
            elif not M3UXMLTV or self.running: continue
            lastCheck = float(REAL_SETTINGS.getSetting('Last_Scan') or 0)
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
        if ENABLE_POOL: self.pool = ThreadPool(CORES)
        self.sysARG     = sysARG
        self.cache      = SimpleCache()
        self.xmltvList  = {'data'       : self.getData(),
                           'channels'   : [],
                           'programmes' : []}
        self.channels   = self.parseM3U(self.loadM3U())
        self.programmes = self.getGuidedata() 
        

    def saveURL(self, url, file=None, life=datetime.timedelta(minutes=1)):
        log('saveURL, url = %s, file = %s'%(url,file))
        try:
            cacheName = '%s.saveURL.%s'%(ADDON_ID,url)
            cacheResponse = self.cache.get(cacheName)
            if cacheResponse is None:
                response = urllib.request.urlopen(url).read()
                cacheResponse = response.decode("utf-8")
                self.cache.set(cacheName, cacheResponse, checksum=len(cacheResponse), expiration=life)
                if file is not None:
                    fle = xbmcvfs.File(file, 'w')
                    fle.write(cacheResponse)
                    fle.close()
            return cacheResponse
        except Exception as e: 
            log("saveURL, Failed! %s"%(e), xbmc.LOGERROR)
            notificationDialog(LANGUAGE(30001))
            return ''
        

    def loadM3U(self):
        m3uListTMP = self.saveURL(M3U_URL,M3U_FILE).split('\n')
        return ['%s\n%s'%(line,m3uListTMP[idx+1]) for idx, line in enumerate(m3uListTMP) if line.startswith('#EXTINF:')]


    def getGuidedata(self):
        return json.loads(self.saveURL(GUIDE_URL))


    def loadXMLTV(self):
        self.poolList(self.buildXMLTV, self.programmes)
        return self.saveXMLTV()
        
        
    def buildXMLTV(self, content):
        channel    = content['Channel']
        programmes = content['Airings']
        if channel['Hidden'] == True: return False
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
        citem    = ({'id'           : channel['Number'],
                     'display-name' : [(channel['Name'], LANG)],
                     'icon'         : [{'src':channel.get('Image',ICON)}]})
        log('addChannel = %s'%(citem))
        self.xmltvList['channels'].append(citem)
        return True


    def addProgram(self, program):
        # {
            # 'Source': 'tms',
            # 'Channel': '6070',
            # 'OriginalDate': '2016-04-11',
            # 'Time': 1601568000,
            # 'Duration': 3600,
            # 'Title': 'Wicked Tuna',
            # 'EpisodeTitle': 'Doubling Down',
            # 'Summary': 'Two captains make the long trip to Georges Bank after a huge haul offshore.',
            # 'Image': 'https://tmsimg.fancybits.co/assets/p9072643_b_h6_be.jpg',
            # 'Categories': ['Episode', 'Series'],
            # 'Genres': ['Reality', 'Outdoors', 'Adventure', 'Fishing'],
            # 'Tags': ['CC', 'HD 1080i', 'HDTV'],
            # 'SeriesID': '9072643',
            # 'ProgramID': 'EP015291270089',
            # 'TeamIDs': None,
            # 'SeasonNumber': 5,
            # 'EpisodeNumber': 10,
            # 'Directors': None,
            # 'Cast': ['T.J. Ott', 'Paul Hebert', 'Bill Monte'],
            # 'Raw': {
                # 'startTime': '2020-10-01T16:00Z',
                # 'endTime': '2020-10-01T17:00Z',
                # 'duration': 60,
                # 'channels': ['6070'],
                # 'stationId': '49438',
                # 'qualifiers': ['CC', 'HD 1080i', 'HDTV'],
                # 'ratings': [{
                    # 'body': 'USA Parental Rating',
                    # 'code': 'TV14'
                # }],
                # 'program': {
                    # 'tmsId': 'EP015291270089',
                    # 'rootId': '12694133',
                    # 'seriesId': '9072643',
                    # 'entityType': 'Episode',
                    # 'subType': 'Series',
                    # 'title': 'Wicked Tuna',
                    # 'titleLang': 'en',
                    # 'episodeTitle': 'Doubling Down',
                    # 'episodeNum': 10,
                    # 'seasonNum': 5,
                    # 'releaseYear': 2016,
                    # 'releaseDate': '2016-04-11',
                    # 'origAirDate': '2016-04-11',
                    # 'descriptionLang': 'en',
                    # 'shortDescription': 'Two captains make the long trip to Georges Bank after a huge haul offshore.',
                    # 'longDescription': 'After successful and massive haul offshore on Georges Bank, the captains of FV-Tuna.com and Hot Tuna decide to make the trip again.',
                    # 'topCast': ['T.J. Ott', 'Paul Hebert', 'Bill Monte'],
                    # 'genres': ['Reality', 'Outdoors', 'Adventure', 'Fishing'],
                    # 'preferredImage': {
                        # 'uri': 'https://tmsimg.fancybits.co/assets/p9072643_b_h6_be.jpg',
                        # 'height': '540',
                        # 'width': '720',
                        # 'primary': 'true',
                        # 'category': 'Banner-L1',
                        # 'text': 'yes',
                        # 'tier': 'Series'
                    # },
                    # 'sportsId': '110'
                # }
            # }
        # }, 
        pitem      = {'channel'     : program['Channel'],
                      # 'credits'     : {'director': [program.get('Directors',[])], 'cast': [program.get('Cast',[])]},
                      'category'    : [(genre,LANG) for genre in program.get('Categories',['Undefined'])],
                      'title'       : [(program['Title'], LANG)],
                      'desc'        : [((program['Summary'] or xbmc.getLocalizedString(161)), LANG)],
                      'stop'        : (strpTime(program['Raw']['endTime']).strftime(xmltv.date_format)),
                      'start'       : (strpTime(program['Raw']['startTime']).strftime(xmltv.date_format)),
                      'icon'        : [{'src': program.get('Image',FANART)}]}
                      
        if program.get('EpisodeTitle',''):
            pitem['sub-title'] = [(program['EpisodeTitle'], LANG)]
            
        if program.get('OriginalDate',''):
            pitem['date'] = (strpTime(program['OriginalDate'], '%Y-%m-%d')).strftime('%Y%m%d')

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
         ##### TODO #####
           # 'country'     : [('USA', LANG)],#todo
           # 'language': (u'English', u''),
           #  'length': {'units': u'minutes', 'length': '22'},
           # 'orig-language': (u'English', u''),
           # 'premiere': (u'Not really. Just testing', u'en'),
           # 'previously-shown': {'channel': u'C12whdh.zap2it.com', 'start': u'19950921103000 ADT'},
           # 'audio'       : {'stereo': u'stereo'},#todo                 
           # 'subtitles'   : [{'type': u'teletext', 'language': (u'English', u'')}],#todo
           # 'url'         : [(u'http://www.nbc.com/')],#todo
           # 'review'      : [{'type': 'url', 'value': 'http://some.review/'}],
           # 'video'       : {'colour': True, 'aspect': u'4:3', 'present': True, 'quality': 'standard'}},#todo
            
        log('addProgram = %s'%(pitem))
        self.xmltvList['programmes'].append(pitem)
        return True
        
        
    def parseM3U(self, lines):
        log('parseM3U')
        items = []
        for line in lines:
            if line.startswith('#EXTINF:'):
                groups = re.compile('tvg-chno=\"(.*?)\" tvg-logo=\"(.*?)\" tvg-name=\"(.*?)\" group-title=\"(.*?)\",(.*)\\n(.*)', re.IGNORECASE).search(line)
                items.append({'number':groups.group(1),'logo':groups.group(2),'name':groups.group(3),'groups':groups.group(4),'title':groups.group(5),'url':groups.group(6)})
        return sorted(items, key=lambda k: k['number'])
        
        
    def playVideo(self, name, url):
        log('playVideo, url = %s'%url)
        if url is None: 
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
            if args is not None: 
                results = self.pool.map(method, zip(items,repeat(args)))
            elif items: 
                results = self.pool.map(method, items)#, chunksize=chunk)
            self.pool.close()   
            self.pool.join()
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
        
        
    def buildLive(self):
        log('buildLive')
        self.poolList(self.buildPlayItem, self.programmes, 'live')
        
        
    def buildPlayItem(self, data):
        content, opt = data
        liveMatch  = False
        channel    = content['Channel']
        programmes = content['Airings']
        if channel['Hidden'] == True: return
        now = (datetime.datetime.fromtimestamp(float(getLocalTime())))
        for program in programmes:
            url   = ''
            stop  = (strpTime(program['Raw']['endTime']))
            start = (strpTime(program['Raw']['startTime']))
            label = program.get('Title','')
            url   = program.get('Path','')
            if opt == 'live': 
                label = '%s| %s'%(channel['Number'],channel['Name'])
            elif opt == 'lineup':
                label = '%s - %s'%(start.strftime('%I:%M %p').lstrip('0'),program.get('Title',''))
            if opt in ['live','lineup'] and now >= start and now < stop:
                url = self.getLiveURL(channel['Number'], self.channels)
                if opt == 'live': liveMatch = True
                if program.get('Title',''):
                    if opt == 'live':
                        label = '%s| %s: [B]%s[/B]'%(channel['Number'],channel['Name'],program['Title'])
                    elif opt == 'lineup':
                        label = '%s - [B]%s[/B]'%(start.strftime('%I:%M %p').lstrip('0'),program.get('Title',''))
            
            icon  = channel.get('Image',ICON)
            thumb = program.get('Image',icon)
            info  = {'label':label,'title':label,'duration':program.get('Duration',0),'genre':program.get('Genres',[]),'plot':program.get('Summary',xbmc.getLocalizedString(161)),'aired':program.get('OriginalDate','')}
            art   = {'icon':icon, 'thumb':thumb}
            self.addLink(channel['Name'], url, '9', liz=self.buildItemListItem(label, url, info, art))
            if opt == 'live' and liveMatch: break
            
            
    def buildRecordingItem(self, item):
        item['Airings']  = [item['Airing'].copy()]
        item['Channel'] = {'Hidden':False,'Number':0,'Name':'','Image':''}
        self.buildPlayItem((item,'recordings'))
        
   
        
    # {
	# 'ID': '28904',
	# 'JobID': '1599865190-ch6070',
	# 'RuleID': '',
	# 'GroupID': '248379',
	# 'Path': 'TV\\Inside 9-11 War on America\\Inside 9-11 War on America 2005-08-21 2020-09-11-1859.mpg',
	# 'Checksum': '',
	# 'CreatedAt': 1599865190,
	# 'Watched': False,
	# 'Deleted': False,
	# 'PlaybackTime': 0,
	# 'Duration': 7234.961933,
	# 'Commercials': [839.79, 989.84, 1413.81, 1659.18, 2137.23, 2352.71, 2686.46, 2907.73, 3437.7200000000003, 3707.59, 4401.52, 4635.47, 5091.42, 5331.6, 5810.4400000000005, 6020.59, 6351.610000000001, 6591.22],
	# 'Delayed': False,
	# 'Corrupted': False,
	# 'Cancelled': False,
	# 'Completed': True,
	# 'Processed': True,
	# 'Favorited': False,
	# 'Locked': False,
	# 'Airing': {
		# 'Source': 'tms',
		# 'Channel': '6070',
		# 'OriginalDate': '2005-08-21',
		# 'Time': 1599865200,
		# 'Duration': 7200,
		# 'Title': 'Inside 9/11: War on America',
		# 'Summary': 'Investigation of the events leading up to the terrorist attacks of Sept. 11, 2001.',
		# 'Image': 'https://tmsimg.fancybits.co/assets/p248379_b_h6_ak.jpg',
		# 'Categories': ['Show', 'Special'],
		# 'Genres': ['Documentary', 'Special'],
		# 'Tags': ['CC', 'HD 1080i', 'HDTV'],
		# 'SeriesID': '248379',
		# 'ProgramID': 'SH007602260000-1599865200',
		# 'TeamIDs': None,
		# 'SeasonNumber': 0,
		# 'EpisodeNumber': 0,
		# 'Directors': None,
		# 'Cast': None,
		# 'Raw': {
			# 'startTime': '2020-09-11T23:00Z',
			# 'endTime': '2020-09-12T01:00Z',
			# 'duration': 120,
			# 'channels': ['6070'],
			# 'stationId': '49438',
			# 'qualifiers': ['CC', 'HD 1080i', 'HDTV'],
			# 'ratings': [{
				# 'body': 'USA Parental Rating',
				# 'code': 'TVPG'
			# }],
			# 'program': {
				# 'tmsId': 'SH007602260000',
				# 'rootId': '248379',
				# 'seriesId': '248379',
				# 'entityType': 'Show',
				# 'subType': 'Special',
				# 'title': 'Inside 9/11: War on America',
				# 'titleLang': 'en',
				# 'releaseYear': 2005,
				# 'releaseDate': '2005-08-21',
				# 'origAirDate': '2005-08-21',
				# 'descriptionLang': 'en',
				# 'shortDescription': 'Investigation of the events leading up to the terrorist attacks of Sept. 11, 2001.',
				# 'longDescription': 'Investigation of the events leading up to the terrorist attacks of Sept. 11, 2001.',
				# 'topCast': None,
				# 'genres': ['Documentary', 'Special'],
				# 'preferredImage': {
					# 'uri': 'https://tmsimg.fancybits.co/assets/p248379_b_h6_ak.jpg',
					# 'height': '540',
					# 'width': '720',
					# 'primary': 'true',
					# 'category': 'Banner-L2',
					# 'text': 'yes',
					# 'tier': ''
				# }
			# }
		# }
	# },
	# 'ChannelNumber': '6070',
	# 'DeviceID': 'TVE-Spectrum',
	# 'PlayedAt': 0,
	# 'UpdatedAt': 1599879912739,
	# 'DeletedAt': 0,
	# 'FavoritedAt': 0,
	# 'DeletedReason': '',
	# 'DeleteNow': False,
	# 'HighestPTS': 651147881,
	# 'SignalStats': None,
	# 'CommercialsAligned': True,
	# 'CommercialsEdited': False,
	# 'CommercialsVerified': False,
	# 'CommercialDetectSource': 'local',
	# 'CloudComskip': {
		# 'Successful': False
	# },
	# 'ImportPath': '',
	# 'ImportQuery': '',
	# 'ImportGroup': '',
	# 'ImportedAt': 0,
	# 'DeleteScheduledFor': 259200000
# }
    
            
    def buildRecordings(self):
        self.poolList(self.buildRecordingItem, json.loads(self.saveURL(UPNEXT_URL)))
            
        
    def search(self, term=None):
        #todo match id with programmes
        if term is None: term = getKeyboard(header=LANGUAGE(30014))
        if term:
            log('search, term = %s'%(term))
            query = json.loads(self.saveURL(SEARCH_URL.format(query=term)))


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
        try:
            self.loadM3U()
            self.loadXMLTV()
            self.chkSettings()
            return True
        except:
            return False
        
        
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
        elif mode == 1:  self.buildLineup(url)
        elif mode == 2:  self.buildRecordings()
        elif mode == 8:  self.search(name)
        elif mode == 9:  self.playVideo(name, url)
        
        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=DISC_CACHE)