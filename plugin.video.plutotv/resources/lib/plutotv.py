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
import os, sys, time, _strptime, datetime, net, re, traceback, uuid
import socket, json, collections, inputstreamhelper
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon

from six.moves import urllib
from itertools import repeat
from simplecache import SimpleCache, use_cache

try:
    from multiprocessing import cpu_count 
    from multiprocessing.pool import ThreadPool 
    ENABLE_POOL = True
    CORES = cpu_count()
except: ENABLE_POOL = False
    
# Plugin Info
ADDON_ID      = 'plugin.video.plutotv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT      = 15
CONTENT_TYPE = 'files'
DISC_CACHE   = True
USER_EMAIL   = REAL_SETTINGS.getSetting('User_Email')
PASSWORD     = REAL_SETTINGS.getSetting('User_Password')
DEBUG        = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
COOKIE_JAR   = xbmc.translatePath(os.path.join(SETTINGS_LOC, "cookiejar.lwp"))
PTVL_RUN     = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
BASE_API     = 'https://api.pluto.tv'
BASE_LINEUP  = BASE_API + '/v2/channels.json'
BASE_GUIDE   = BASE_API + '/v2/channels?start=%s&stop=%s&%s'
LOGIN_URL    = BASE_API + '/v1/auth/local'
BASE_CLIPS   = BASE_API + '/v2/episodes/%s/clips.json'
BASE_VOD     = BASE_API + '/v3/vod/categories?includeItems=true&deviceType=web&%s'
SEASON_VOD   = BASE_API + '/v3/vod/series/%s/seasons?includeItems=true&deviceType=web&%s'
PLUTO_MENU   = [(LANGUAGE(30011), '', 0),
                (LANGUAGE(30018), '', 1),
                (LANGUAGE(30017), '', 2),
                (LANGUAGE(30012), '', 3),
                (LANGUAGE(30013), '', 20)]

def inputDialog(heading=ADDON_NAME, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    retval = xbmcgui.Dialog().input(heading, default, key, opt, close)
    if len(retval) > 0: return retval    
        
def notificationDialog(message, header=ADDON_NAME, show=True, sound=False, time=1000, icon=ICON):
    try: xbmcgui.Dialog().notification(header, message, icon, time, sound=False)
    except: xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))
     
def yesnoDialog(str1, str2='', str3='', header=ADDON_NAME, yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesno(header, str1, str2, str3, no, yes, autoclose)
    
def strpTime(datestring, format='%Y-%m-%d %H:%M:%S'):
    try: return datetime.datetime.strptime(datestring, format)
    except TypeError: return datetime.datetime.fromtimestamp(time.mktime(time.strptime(datestring, format)))

def timezone():
    if time.localtime(time.time()).tm_isdst and time.daylight: return time.altzone / -(60*60) * 100
    else: return time.timezone / -(60*60) * 100
    
def setUUID():
    if REAL_SETTINGS.getSetting("sid"): return
    log('setUUID, creating uuid')
    REAL_SETTINGS.setSetting("sid",uuid.uuid1().hex[:18])
    REAL_SETTINGS.setSetting("deviceId",uuid.uuid4().hex[:18])

def getUUID():
    return REAL_SETTINGS.setSetting("sid",uuid.uuid1().hex[:18]), REAL_SETTINGS.setSetting("deviceId",uuid.uuid4().hex[:18])
    
def cookieJar():
    if not xbmcvfs.exists(COOKIE_JAR):
        try:
            xbmcvfs.mkdirs(SETTINGS_LOC)
            f = xbmcvfs.File(COOKIE_JAR, 'w')
            f.close()
        except: log('login, Unable to create cookie folder', xbmc.LOGERROR)

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
   
socket.setdefaulttimeout(TIMEOUT)
class PlutoTV(object):
    def __init__(self, sysARG):
        log('__init__, sysARG = ' + str(sysARG))
        self.sysARG  = sysARG
        self.net     = net.Net()
        self.cache   = SimpleCache()
        

    def login(self):
        log('login')
        setUUID()
        cookieJar()
        if USER_EMAIL == LANGUAGE(30009): return #ignore, using guest login
        if len(USER_EMAIL) > 0:
            header_dict               = {}
            header_dict['Accept']     = 'application/json, text/javascript, */*; q=0.01'
            header_dict['Host']       = 'api.pluto.tv'
            header_dict['Connection'] = 'keep-alive'
            header_dict['Referer']    = 'http://pluto.tv/'
            header_dict['Origin']     = 'http://pluto.tv'
            header_dict['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0'
            form_data = ({'optIn': 'true', 'password': PASSWORD,'synced': 'false', 'userIdentity': USER_EMAIL})
            self.net.set_cookies(COOKIE_JAR)
            try:
                loginlink = json.loads(self.net.http_POST(LOGIN_URL, form_data=form_data, headers=header_dict).content.encode("utf-8").rstrip())
                if loginlink and loginlink['email'].lower() == USER_EMAIL.lower():
                    notificationDialog(LANGUAGE(30006)%(loginlink['displayName']), time=4000)
                    self.net.save_cookies(COOKIE_JAR)
                else: notificationDialog(LANGUAGE(30007), time=4000)
            except Exception as e: log('login, failed! ' + str(e), xbmc.LOGERROR)
        else:
            #firstrun wizard
            if yesnoDialog(LANGUAGE(30008),no=LANGUAGE(30009), yes=LANGUAGE(30010)):
                REAL_SETTINGS.setSetting('User_Email',inputDialog(LANGUAGE(30001)))
                REAL_SETTINGS.setSetting('User_Password',inputDialog(LANGUAGE(30002)))
            else: REAL_SETTINGS.setSetting('User_Email',LANGUAGE(30009))
            
            
    def openURL(self, url, life=datetime.timedelta(minutes=15)):
        log('openURL, url = ' + url)
        try:
            header_dict               = {}
            header_dict['Accept']     = 'application/json, text/javascript, */*; q=0.01'
            header_dict['Host']       = 'api.pluto.tv'
            header_dict['Connection'] = 'keep-alive'
            header_dict['Referer']    = 'http://pluto.tv/'
            header_dict['Origin']     = 'http://pluto.tv'
            header_dict['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0'
            self.net.set_cookies(COOKIE_JAR)
            trans_table   = ''.join( [chr(i) for i in range(128)] + [' '] * 128 )
            cacheResponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheResponse:
                try: cacheResponse = self.net.http_GET(url, headers=header_dict).content.encode("utf-8", 'ignore')
                except: cacheResponse = (self.net.http_GET(url, headers=header_dict).content.translate(trans_table)).encode("utf-8")
                self.net.save_cookies(COOKIE_JAR)
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, cacheResponse, expiration=life)
            if isinstance(cacheResponse, basestring): cacheResponse = json.loads(cacheResponse)
            return cacheResponse
        except Exception as e:
            log('openURL, Unable to open url ' + str(e), xbmc.LOGERROR)
            notificationDialog(LANGUAGE(30028), time=4000)
            return {}
            

    def mainMenu(self):
        log('mainMenu')
        self.login()
        for item in PLUTO_MENU: self.addDir(*item)
            
            
    def browseMenu(self):
        log('browseMenu')
        categoryMenu = self.getCategories()
        for item in categoryMenu: self.addDir(*item)


    def getOndemand(self):
        return self.openURL(BASE_VOD%(LANGUAGE(30022)%(getUUID())), life=datetime.timedelta(hours=1))


    def getVOD(self, epid):
        return self.openURL(SEASON_VOD%(epid,LANGUAGE(30022)%(getUUID())), life=datetime.timedelta(hours=1))
        
        
    def getClips(self, epid):
        return self.openURL(BASE_CLIPS%(epid), life=datetime.timedelta(hours=1))
        
        
    def getChannels(self):
        return sorted(self.openURL(BASE_LINEUP, life=datetime.timedelta(hours=1)), key=lambda i: i['number'])
        
        
    def getGuidedata(self):
        tz    = str(timezone())
        start = datetime.datetime.now().strftime('%Y-%m-%dT%H:00:00').replace('T','%20').replace(':00:00','%3A00%3A00.000'+tz)
        stop  = (datetime.datetime.now() + datetime.timedelta(hours=4)).strftime('%Y-%m-%dT%H:00:00').replace('T','%20').replace(':00:00','%3A00%3A00.000'+tz)
        return sorted((self.openURL(BASE_GUIDE %(start,stop,'sid=%s&deviceId=%s'%(getUUID())), life=datetime.timedelta(hours=1))), key=lambda i: i['number'])


    def getCategories(self):
        log('getCategories')
        collect= []
        data = self.getChannels()
        for channel in data: collect.append(channel['category'])
        counter = collections.Counter(collect)
        for key, value in sorted(counter.iteritems()): yield (key,'categories', 0)
        
        
    def getMediaTypes(self, genre):
        if   type == 'Movies': return 'movie'
        elif type == 'TV': return 'episode'
        elif type == 'Music + Radio': return 'musicvideo'
        else: return 'video'
            
            
    def pagination(self, seq, rowlen):
        for start in xrange(0, len(seq), rowlen): yield seq[start:start+rowlen]

            
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
                        label = '%s :[B]%s[/B]'%(label, title)
                    elif type in ['tv','series']:
                        mtype = 'episode'
                        thumb = epposter
                        label = "%s :[B]%s - %s[/B]" % (label, tvtitle, epname)
                    elif len(epname) > 0: label = '%s :[B]%s - %s[/B]'%(label, title, epname)
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
        
        
    def uEPG(self):
        log('uEPG')
        data = self.getGuidedata()
        return urllib.parse.quote(json.dumps(list(self.poolList(self.buildGuide, zip(data,repeat('guide'),repeat(''))))))

            
    def browseGuide(self, name, opt=None, data=None):
        log('browseGuide, name=%s, opt=%s'%(name,opt))
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
        if url.lower() == 'next_show': return notificationDialog(LANGUAGE(30029), time=4000)
        elif LANGUAGE(30019) not in url: url = LANGUAGE(30021)%(url,LANGUAGE(30020)%(getUUID()))
        log('playVideo, url = %s'%url)
        if liz is None: liz = xbmcgui.ListItem(name, path=url)
        if 'm3u8' in url.lower() and inputstreamhelper.Helper('hls').check_inputstream() and not DEBUG:
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
        u=self.sysARG[0]+"?url="+urllib.parse.quote(u)+"&mode="+str(mode)+"&name="+urllib.parse.quote(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name} )
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.parse.quote(u)+"&mode="+str(mode)+"&name="+urllib.parse.quote(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)


    def poolList(self, method, items):
        results = []
        if ENABLE_POOL and not DEBUG:
            pool = ThreadPool(CORES)
            results = pool.imap_unordered(method, items, chunksize=25)
            pool.close()
            pool.join()
        else: results = [method(item) for item in items]
        results = filter(None, results)
        return results
        
        
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
        elif mode == 20: xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&skin_path=%s&refresh_path=%s&refresh_interval=%s&row_count=%s&include_hdhr=false)"%(self.uEPG(),urllib.parse.quote(ADDON_PATH),urllib.parse.quote(self.sysARG[0]+"?mode=20"),"7200","5"))

        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=DISC_CACHE)