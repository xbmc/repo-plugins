#   Copyright (C) 2020 Lunatixz
#
#
# This file is part of PlutoTV.
#
# PlutoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PlutoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PlutoTV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, _strptime, datetime, re, traceback, uuid
import json, collections, inputstreamhelper, requests

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
ADDON_ID      = 'plugin.video.plutotv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString
MONITOR       = xbmc.Monitor()

## GLOBALS ##
LOGO          = os.path.join('special://home/addons/%s/'%(ADDON_ID),'resources','images','logo.png')
LANG          = 'en' #todo
TIMEOUT       = 30
CONTENT_TYPE  = 'episodes'
DISC_CACHE    = False
DTFORMAT      = '%Y%m%d%H%M%S'
PVR_CLIENT    = 'pvr.iptvsimple'
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
M3UXMLTV      = REAL_SETTINGS.getSetting('Enable_M3UXMLTV') == 'true'
ENABLE_CONFIG = REAL_SETTINGS.getSetting('Enable_Config') == 'true'
USER_PATH     = REAL_SETTINGS.getSetting('User_Folder') 
M3U_FILE      = os.path.join(USER_PATH,'plutotv.m3u')
XMLTV_FILE    = os.path.join(USER_PATH,'plutotv.xml')
GUIDE_URL     = 'https://service-channels.clusters.pluto.tv/v1/guide?start=%s&stop=%s&%s'
BASE_API      = 'https://api.pluto.tv'
BASE_LINEUP   = BASE_API + '/v2/channels.json?%s'
BASE_GUIDE    = BASE_API + '/v2/channels?start=%s&stop=%s&%s'
LOGIN_URL     = BASE_API + '/v1/auth/local?deviceType=web&%s'
BASE_CLIPS    = BASE_API + '/v2/episodes/%s/clips.json'
BASE_VOD      = BASE_API + '/v3/vod/categories?includeItems=true&deviceType=web&%s'
SEASON_VOD    = BASE_API + '/v3/vod/series/%s/seasons?includeItems=true&deviceType=web&%s'
PLUTO_MENU    = [(LANGUAGE(30011), '', 0),
                 (LANGUAGE(30018), '', 1),
                 (LANGUAGE(30017), '', 2),
                 (LANGUAGE(30012), '', 3)]
                
xmltv.locale      = 'UTF-8'
xmltv.date_format = DTFORMAT

def getPTVL():
    return xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'

def setUUID():
    if REAL_SETTINGS.getSetting("sid1_hex") and REAL_SETTINGS.getSetting("deviceId1_hex"): return
    REAL_SETTINGS.setSetting("sid1_hex",str(uuid.uuid1().hex))
    REAL_SETTINGS.setSetting("deviceId1_hex",str(uuid.uuid4().hex))

def getUUID():
    return REAL_SETTINGS.getSetting("sid1_hex"), REAL_SETTINGS.getSetting("deviceId1_hex")

def notificationDialog(message, header=ADDON_NAME, show=True, sound=False, time=1000, icon=ICON):
    try:    xbmcgui.Dialog().notification(header, message, icon, time, sound=False)
    except: xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))
   
def strpTime(datestring, format='%Y-%m-%dT%H:%M:%S.%fZ'):
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
     
def slugify(text):
    non_url_safe = [' ','"', '#', '$', '%', '&', '+',',', '/', ':', ';', '=', '?','@', '[', '\\', ']', '^', '`','{', '|', '}', '~', "'"]
    non_url_safe_regex = re.compile(r'[{}]'.format(''.join(re.escape(x) for x in non_url_safe)))
    text = non_url_safe_regex.sub('', text).strip()
    text = u'_'.join(re.split(r'\s+', text))
    return text
  
class Service(object):
    def __init__(self, sysARG=sys.argv):
        self.running   = False
        self.myMonitor = MONITOR
        self.myPlutoTV = PlutoTV(sysARG)
        
        
    def run(self):
        log('Service, run')
        while not self.myMonitor.abortRequested():
            if self.myMonitor.waitForAbort(2): break
            if not M3UXMLTV or self.running: continue
            lastCheck  = float(REAL_SETTINGS.getSetting('Last_Scan') or 0)
            conditions = [xbmcvfs.exists(M3U_FILE),xbmcvfs.exists(XMLTV_FILE)]
            if (time.time() > (lastCheck + 3600)) or (False in conditions):
                self.running = True
                if self.myPlutoTV.buildService():
                    REAL_SETTINGS.setSetting('Last_Scan',str(time.time()))
                    notificationDialog(LANGUAGE(30031))
                self.running = False
                

class PlutoTV(object):
    def __init__(self, sysARG=sys.argv):
        log('__init__, sysARG = %s'%(sysARG))
        setUUID()
        self.myMonitor = MONITOR
        self.sysARG    = sysARG
        self.cache     = SimpleCache()
        self.m3uList   = []
        self.xmltvList = {'data'       : self.getData(),
                          'channels'   : [],
                          'programmes' : []}

            
    def getURL(self, url, param={}, header={}, life=datetime.timedelta(minutes=15)):
        log('getURL, url = %s, header = %s'%(url, header))
        cacheresponse = self.cache.get(ADDON_NAME + '.getURL, url = %s.%s.%s'%(url,param,header))
        if not cacheresponse:
            try:
                req = requests.get(url, param, headers=header)
                cacheresponse = req.json()
                req.close()
                self.cache.set(ADDON_NAME + '.getURL, url = %s.%s.%s'%(url,param,header), json.dumps(cacheresponse), expiration=life)
                return cacheresponse
            except Exception as e: 
                log("getURL, Failed! %s"%(e), xbmc.LOGERROR)
                notificationDialog(LANGUAGE(30001))
                return {}
        else: return json.loads(cacheresponse)

      
    def buildHeader(self):
        header_dict               = {}
        header_dict['Accept']     = 'application/json, text/javascript, */*; q=0.01'
        header_dict['Host']       = 'api.pluto.tv'
        header_dict['Connection'] = 'keep-alive'
        header_dict['Referer']    = 'http://pluto.tv/'
        header_dict['Origin']     = 'http://pluto.tv'
        header_dict['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0'
        return header_dict


    def mainMenu(self):
        log('mainMenu')
        for item in PLUTO_MENU: self.addDir(*item)
            
            
    def browseMenu(self):
        log('browseMenu')
        categoryMenu = self.getCategories()
        for item in categoryMenu: self.addDir(*item)


    def getOndemand(self):
        return self.getURL(BASE_VOD%(LANGUAGE(30022)%(getUUID())), header=self.buildHeader(), life=datetime.timedelta(hours=1))


    def getVOD(self, epid):
        return self.getURL(SEASON_VOD%(epid,LANGUAGE(30022)%(getUUID())), header=self.buildHeader(), life=datetime.timedelta(hours=1))
        
        
    def getClips(self, epid):
        return self.getURL(BASE_CLIPS%(epid), header=self.buildHeader(), life=datetime.timedelta(hours=1))
        
        
    def getChannels(self):
        return sorted(self.getURL(BASE_LINEUP%(LANGUAGE(30022)%(getUUID())), header=self.buildHeader(), life=datetime.timedelta(hours=1)), key=lambda i: i['number'])
        

    def getGuidedata(self, full=False):
        start = (datetime.datetime.fromtimestamp(getLocalTime()).strftime('%Y-%m-%dT%H:00:00Z'))
        stop  = (datetime.datetime.fromtimestamp(getLocalTime()) + datetime.timedelta(hours=4)).strftime('%Y-%m-%dT%H:00:00Z')
        if full: return self.getURL(GUIDE_URL %(start,stop,LANGUAGE(30022)%(getUUID())), life=datetime.timedelta(hours=1))
        else: return sorted((self.getURL(BASE_GUIDE %(start,stop,LANGUAGE(30022)%(getUUID())), life=datetime.timedelta(hours=1))), key=lambda i: i['number'])

        
    def getCategories(self):
        log('getCategories')
        collect= []
        data = self.getChannels()
        for channel in data: collect.append(channel['category'])
        counter = collections.Counter(collect)
        for key, value in sorted(counter.items()): yield (key,'categories', 0)
        

    def buildGuide(self, data):
        channel, name, opt = data
        log('buildGuide, name=%s,opt=%s'%(name, opt))
        urls      = []
        guidedata = []
        newChannel= {}
        mtype     = 'video'
        chid      = channel.get('_id','')
        chname    = channel.get('name','')
        chnum     = channel.get('number','')
        chplot    = (channel.get('description','') or channel.get('summary',''))
        chgeo     = channel.get('visibility','everyone') != 'everyone'
        chcat     = (channel.get('category','')    or channel.get('genre',''))
        chfanart  = channel.get('featuredImage',{}).get('path',FANART)
        chthumb   = channel.get('thumbnail',{}).get('path',ICON)
        chlogo    = channel.get('logo',{}).get('path',ICON)
        ondemand  = channel.get('onDemand','false') == 'true'
        featured  = channel.get('featured','false') == 'true'
        favorite  = channel.get('favorite','false') == 'true'
        timelines = channel.get('timelines',[])

        if   name == 'featured'   and not featured: return None
        elif name == 'favorite'   and not favorite: return None
        elif name == 'categories' and chcat != opt: return None
        elif name == 'lineup'     and chid  != opt: return None
        elif name == 'live': DISC_CACHE = False
            
        if name in ['channels','categories','ondemand','season']:
            if name == 'season':
                seasons    = (channel.get('seasons',{}))
                vodimages  = channel.get('covers',[])
                try: vodlogo      = [image.get('url',[]) for image in vodimages if image.get('aspectRatio','') == '1:1'][0]
                except: vodlogo   = ICON
                try:    vodfanart = [image.get('url',[]) for image in vodimages if image.get('aspectRatio','') == '16:9'][0]
                except: vodfanart = FANART
                for season in seasons:
                    mtype = 'episode'
                    label = 'Season %s'%(season['number'])
                    infoLabels = {"mediatype":mtype,"label":label,"label2":label,"title":chname,"plot":chplot, "code":chid, "genre":[chcat]}
                    infoArt    = {"thumb":vodlogo,"poster":vodlogo,"fanart":vodfanart,"icon":vodlogo,"logo":vodlogo,"clearart":chthumb}
                    self.addDir(label, chid, 5, infoLabels, infoArt)
            else:
                if name == 'ondemand': 
                    mode  = 3
                    label = chname
                else:  
                    mode  = 1
                    label = '%s| %s'%(chnum,chname)
                infoLabels = {"mediatype":mtype,"label":label,"label2":label,"title":label,"plot":chplot, "code":chid, "genre":[chcat]}
                infoArt    = {"thumb":chthumb,"poster":chthumb,"fanart":chfanart,"icon":chlogo,"logo":chlogo,"clearart":chthumb}
                self.addDir(label, chid, mode, infoLabels, infoArt)
        else:
            newChannel['channelname']   = chname
            newChannel['channelnumber'] = chnum
            newChannel['channellogo']   = chlogo
            newChannel['isfavorite']    = favorite
            urls = channel.get('stitched',{}).get('urls',[])
            if not timelines:
                name = 'ondemand'
                timelines = (channel.get('items',[]) or channel.get('episodes',[]))
                
            now = datetime.datetime.now()
            totstart = now
            tz = (timezone()//100)*60*60
            
            for item in timelines:
                episode    = (item.get('episode',{})   or item)
                series     = (episode.get('series',{}) or item)
                epdur      = int(episode.get('duration','0') or '0') // 1000
                
                urls       = (item.get('stitched',{}).get('urls',[]) or urls)
                if len(urls) == 0: continue
                if isinstance(urls, list): urls  = [url['url'] for url in urls if url['type'].lower() == 'hls'][0] # todo select quality
                
                try:
                    start  = strpTime(item['start'],'%Y-%m-%dT%H:%M:00.000Z') + datetime.timedelta(seconds=tz)
                    stop   = strpTime(item['stop'],'%Y-%m-%dT%H:%M:00.000Z')  + datetime.timedelta(seconds=tz)
                except:
                    start  = totstart
                    stop   = start + datetime.timedelta(seconds=epdur)
                totstart   = stop  
                
                type       = series.get('type','')
                tvtitle    = series.get('name',''                           or chname)
                title      = (item.get('title',''))
                tvplot     = (series.get('description','')                  or series.get('summary','')      or chplot)
                tvoutline  = (series.get('summary','')                      or series.get('description','')  or chplot)
                tvthumb    = (series.get('title',{}).get('path','')         or chthumb)
                tvfanart   = (series.get('featuredImage',{}).get('path','') or chfanart)
                epid       = episode['_id']
                epnumber   = episode.get('number',0)
                epseason   = episode.get('season',0)
                epname     = (episode['name'])
                epplot     = (episode.get('description','') or tvplot or epname)
                epgenre    = (episode.get('genre','')       or chcat)
                eptag      = episode.get('subGenre','')
                epmpaa     = episode.get('rating','')
                
                vodimages  = episode.get('covers',[])
                vodposter  = vodfanart = vodthumb = vodlogo = ''
                if vodimages:
                    try:    vodposter = [image.get('url',[]) for image in vodimages if image.get('aspectRatio','') == '347:500'][0]
                    except: pass
                    try:    vodfanart = [image.get('url',[]) for image in vodimages if image.get('aspectRatio','') == '16:9'][0]
                    except: pass
                    try:    vodthumb  = [image.get('url',[]) for image in vodimages if image.get('aspectRatio','') == '4:3'][0]
                    except: pass
                    try:    vodlogo   = [image.get('url',[]) for image in vodimages if image.get('aspectRatio','') == '1:1'][0]
                    except: pass

                chlogo     = (vodlogo or chlogo)
                epposter   = (episode.get('poster',{}).get('path','')        or vodlogo or vodposter or vodthumb  or tvthumb)
                epthumb    = (episode.get('thumbnail',{}).get('path','')     or vodlogo or vodthumb  or vodposter or tvthumb)
                epfanart   = (episode.get('featuredImage',{}).get('path','') or vodfanart or tvfanart)
                epislive   = episode.get('liveBroadcast','false') == 'true'
                
                label      = title
                thumb      = chthumb
                if type in ['movie','film']:
                    mtype  = 'movie'
                    thumb  = epposter
                elif type in ['tv','episode','series']:
                    mtype  = 'episode'
                    thumb  = epposter
                    if epseason > 0 and epnumber > 0:
                        label  = '%sx%s'%(epseason, epnumber)
                        label  = '%s - %s'%(label, epname)
                        # else: label  = '%s - %s'%(tvtitle, label)
                    else: label = epname
                    epname = label
                    if type == 'music' or epgenre.lower() == 'music': mtype = 'musicvideo'

                if name == 'live':
                    if stop < now or start > now: continue
                    # epdur = (now - start).seconds
                    label = '%s| %s'%(chnum,chname)
                    if type in ['movie','film']:
                        mtype = 'movie'
                        thumb = epposter
                        label = '%s : [B]%s[/B]'%(label, title)
                    elif type in ['tv','series']:
                        mtype = 'episode'
                        thumb = epposter
                        label = "%s : [B]%s - %s[/B]" % (label, tvtitle, epname)
                    elif len(epname) > 0: label = '%s: [B]%s - %s[/B]'%(label, title, epname)
                    epname = label
                    if type == 'music' or epgenre.lower() == 'music': mtype = 'musicvideo'

                elif name == 'lineup':
                    if now > stop: continue
                    # elif start >= now and stop < now: epdur = (now - start).seconds
                    if type in ['movie','film']:
                        mtype = 'movie'
                        thumb = epposter
                        label = '%s'%(title)
                    elif type in ['tv','series']:
                        mtype = 'episode'
                        thumb = epposter
                        label = "%s - %s" % (tvtitle, epname)
                    elif len(epname) > 0: label = '%s - %s'%(title, epname)
                    epname = label
                    if type == 'music' or epgenre.lower() == 'music': mtype = 'musicvideo'
                    if now >= start and now < stop: 
                        label = '%s - [B]%s[/B]'%(start.strftime('%I:%M %p').lstrip('0'),label)
                    else: 
                        label = '%s - %s'%(start.strftime('%I:%M %p').lstrip('0'),label)
                        urls  = 'NEXT_SHOW'
                    epname = label

                tmpdata = {"mediatype":mtype,"label":label,"title":label,'duration':epdur,'plot':epplot,'genre':[epgenre],'season':epseason,'episode':epnumber}
                tmpdata['starttime'] = time.mktime((start).timetuple())
                tmpdata['url'] = self.sysARG[0]+'?mode=9&name=%s&url=%s'%(title,urls)
                tmpdata['art'] = {"thumb":thumb,"poster":epposter,"fanart":epfanart,"icon":chlogo,"logo":chlogo,"clearart":chthumb}
                guidedata.append(tmpdata)
                
                if name == 'ondemand' and type == "series":
                    mtype = 'season'
                    infoLabels = {"mediatype":mtype,"label":label,"label2":label,"title":label,"plot":epplot, "code":chid, "genre":[epgenre]}
                    infoArt    = {"thumb":epthumb,"poster":epposter,"fanart":epfanart,"icon":chlogo,"logo":chlogo,"clearart":chthumb}
                    self.addDir(label, epid, 4, infoLabels, infoArt)
                elif name != 'guide':
                    infoLabels = {"mediatype":mtype,"label":label,"label2":label,"tvshowtitle":tvtitle,"title":epname,"plot":epplot, "code":epid, "genre":[epgenre], "duration":epdur,'season':epseason,'episode':epnumber}
                    infoArt    = {"thumb":thumb,"poster":epposter,"fanart":epfanart,"icon":chlogo,"logo":chlogo,"clearart":chthumb}
                    self.addLink(title, urls, 9, infoLabels, infoArt)
                    
            CONTENT_TYPE = '%ss'%mtype
            if len(guidedata) > 0:
                newChannel['guidedata'] = guidedata
                return newChannel
        

    def browseGuide(self, name, opt=None, data=None):
        log('browseGuide, name=%s, opt=%s'%(name,opt))
        self.chnums = []
        if data is None: data = self.getGuidedata()
        if opt == 'categories': 
            opt  = name
            name = 'categories'
        self.poolList(self.buildGuide, zip(data,repeat(name.lower()),repeat(opt)))
             
             
    def browseLineup(self, name, opt=None):
        log('browseLineup, opt=%s'%opt)
        if opt is None: name = 'channels'
        else: name = 'lineup'
        self.browseGuide(name, opt)
        
      
    def browseOndemand(self, opt=None):
        log('browseOndemand')
        data = self.getOndemand()['categories']
        if opt is None: name = 'ondemand'
        else: name = 'lineup'
        self.browseGuide(name, opt, data)
        
        
    def browseSeason(self, opt=None):
        log('browseSeason')
        data = [self.getVOD(opt)]
        self.browseGuide('season', opt, data)
        
        
    def browseEpisodes(self, name, opt=None):
        log('browseEpisodes')
        season = int(name.split('Season ')[1])
        data = [self.getVOD(opt).get('seasons',[])[season - 1]]
        self.browseGuide('episode', opt, data)
                
                
    def browseCategories(self):
        log('browseCategories')
        data = list(self.getCategories())
        for item in data: self.addDir(*item) 
       
        
    def playVideo(self, name, url, liz=None):
        if url.lower() == 'next_show': 
            found = False
            liz   = xbmcgui.ListItem(name)
            return notificationDialog(LANGUAGE(30029), time=4000)
        else:
            found = True
            if url.endswith('?deviceType='): url = url.replace('deviceType=','deviceType=&deviceMake=&deviceModel=&&deviceVersion=unknown&appVersion=unknown&deviceDNT=0&userId=&advertisingId=&app_name=&appName=&buildVersion=&appStoreUrl=&architecture=&includeExtendedEvents=false')#todo lazy fix replace
            if 'sid' not in url: url = url.replace('deviceModel=&','deviceModel=&' + LANGUAGE(30022)%(getUUID()))
            url = url.replace('deviceType=&','deviceType=web&').replace('deviceMake=&','deviceMake=Chrome&') .replace('deviceModel=&','deviceModel=Chrome&').replace('appName=&','appName=web&')#todo replace with regex!
            log('playVideo, url = %s'%url)
            if liz is None: liz = xbmcgui.ListItem(name, path=url)
            if 'm3u8' in url.lower() and inputstreamhelper.Helper('hls').check_inputstream() and not DEBUG:
                liz.setProperty('inputstreamaddon','inputstream.adaptive')
                liz.setProperty('inputstream.adaptive.manifest_type','hls')
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), found, liz)

           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        log('addLink, name = %s'%name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true') 
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.parse.quote(u)+"&mode="+str(mode)+"&name="+urllib.parse.quote(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        log('addDir, name = %s'%name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name} )
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.parse.quote(u)+"&mode="+str(mode)+"&name="+urllib.parse.quote(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)


    def getData(self):
        log('getData')
        return {'date'                : datetime.datetime.fromtimestamp(float(time.time())).strftime(xmltv.date_format),
                'generator-info-name' : '%s Guidedata'%(ADDON_NAME),
                'generator-info-url'  : ADDON_ID,
                'source-info-name'    : ADDON_NAME,
                'source-info-url'     : ADDON_ID}


    def save(self, reset=True):
        log('save')
        fle = xbmcvfs.File(M3U_FILE, 'w')
        log('save, saving m3u to %s'%(M3U_FILE))
        fle.write('\n'.join([item for item in self.m3uList]))
        fle.close()
        
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
        log('save, saving xmltv to %s'%(XMLTV_FILE))
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


    def buildService(self):
        log('buildService')
        channels = self.getChannels()
        [self.buildM3U(channel) for channel in channels]
        self.poolList(self.buildXMLTV, self.getGuidedata(full=True).get('channels',[]))
        self.save()
        self.chkSettings()
        return True
        
        
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
        
        
    def buildM3U(self, channel):
        litem = '#EXTINF:-1 tvg-chno="%s" tvg-id="%s" tvg-name="%s" tvg-logo="%s" group-title="%s" radio="%s",%s\n%s'
        logo  = (channel.get('logo',{}).get('path',LOGO) or LOGO)
        group = [channel.get('category','')]
        radio = False#True if "Music" in group else False
        urls  = channel.get('stitched',{}).get('urls',[])
        if len(urls) == 0: return False
        if isinstance(urls, list): urls = [url['url'] for url in urls if url['type'].lower() == 'hls'][0] # todo select quality
        urls = urls.split('?')[0]+LANGUAGE(30034)
        self.m3uList.append(litem%(channel['number'],'%s@%s'%(channel['number'],slugify(ADDON_NAME)),channel['name'],logo,';'.join(group),str(radio).lower(),channel['name'],urls))
        return True
        
        
    def buildXMLTV(self, channel):
        self.addChannel(channel)
        [self.addProgram(channel, program) for program in  channel.get('timelines',[])]
        return True
        
        
    def addChannel(self, channel):
        logo  = [logo.get('url',ICON) for logo in channel.get('images',[]) if logo.get('type','') == 'logo'][0]
        citem = ({'id'           : '%s@%s'%(channel['number'],slugify(ADDON_NAME)),
                  'display-name' : [(channel['name'], LANG)],
                  'icon'         : [{'src':logo}]})
        log('addChannel = %s'%(citem))
        self.xmltvList['channels'].append(citem)
        return True


    def addProgram(self, channel, program):
        episode = program.get('episode',{})
        series  = episode.get('series',{})
        pitem   = {'channel'     : '%s@%s'%(channel['number'],slugify(ADDON_NAME)),
                   'category'    : [(episode.get('genre','Undefined'),LANG)],
                   'title'       : [(program['title'], LANG)],
                   'desc'        : [((episode['description'] or xbmc.getLocalizedString(161)), LANG)],
                   'stop'        : (strpTime(program['stop'] ,'%Y-%m-%dT%H:%M:%S.%fZ')).strftime(xmltv.date_format),
                   'start'       : (strpTime(program['start'],'%Y-%m-%dT%H:%M:%S.%fZ')).strftime(xmltv.date_format),
                   'icon'        : [{'src': (episode.get('poster','') or episode.get('thumbnail','') or episode.get('featuredImage',{})).get('path',FANART)}]}
                      
        if episode.get('name',''):
            pitem['sub-title'] = [(episode['name'], LANG)]
            
        if episode.get('clip',{}).get('originalReleaseDate',''):
            try:
                pitem['date'] = (strpTime(episode['clip']['originalReleaseDate'])).strftime('%Y%m%d')
            except: pass

        if episode.get('rating',''):
            rating = program.get('rating','')
            if rating.startswith('TV'): 
                pitem['rating'] = [{'system': 'VCHIP', 'value': rating}]
            else:  
                pitem['rating'] = [{'system': 'MPAA', 'value': rating}]
      
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

        
    def getParams(self):
        return dict(urllib.parse.parse_qsl(self.sysARG[2][1:]))

            
    def run(self):    
        params=self.getParams()
        try: url=urllib.parse.unquote_plus(params["url"])
        except: url=None
        try: name=urllib.parse.unquote_plus(params["name"])
        except: name=None
        try: mode=int(params["mode"])
        except: mode=None
        log("Mode: "+str(mode))
        log("URL : "+str(url))
        log("Name: "+str(name))

        if   mode==None: self.mainMenu()
        elif mode == 0:  self.browseGuide(name, url)
        elif mode == 1:  self.browseLineup(name, url)
        elif mode == 2:  self.browseCategories()
        elif mode == 3:  self.browseOndemand(url)
        elif mode == 4:  self.browseSeason(url)
        elif mode == 5:  self.browseEpisodes(name, url)
        elif mode == 9:  self.playVideo(name, url)
        
        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=DISC_CACHE)