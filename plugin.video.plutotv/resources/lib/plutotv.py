#   Copyright (C) 2021 Lunatixz
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
import os, sys, time, _strptime, datetime, re, traceback, uuid, routing
import socket, json, inputstreamhelper, requests, collections

from six.moves     import urllib
from simplecache   import SimpleCache, use_cache
from itertools     import repeat, cycle, chain, zip_longest
from kodi_six      import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode
from favorites     import *

try:
    from multiprocessing import cpu_count 
    from multiprocessing.pool import ThreadPool 
    ENABLE_POOL = True
    CORES = cpu_count()
except: ENABLE_POOL = False

try:
  basestring #py2
except NameError: #py3
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
ROUTER        = routing.Plugin()

## GLOBALS ##
LOGO          = os.path.join('special://home/addons/%s/'%(ADDON_ID),'resources','images','logo.png')
DEBUG         = REAL_SETTINGS.getSettingBool('Enable_Debugging')
GUIDE_URL     = 'https://service-channels.clusters.pluto.tv/v1/guide?start=%s&stop=%s&%s'
BASE_API      = 'https://api.pluto.tv'
BASE_LINEUP   = BASE_API + '/v2/channels.json?%s'
BASE_GUIDE    = BASE_API + '/v2/channels?start=%s&stop=%s&%s'
LOGIN_URL     = BASE_API + '/v1/auth/local?deviceType=web&%s'
BASE_CLIPS    = BASE_API + '/v2/episodes/%s/clips.json'
BASE_VOD      = BASE_API + '/v3/vod/categories?includeItems=true&deviceType=web&%s'
SEASON_VOD    = BASE_API + '/v3/vod/series/%s/seasons?includeItems=true&deviceType=web&%s'

INPUTSTREAM       = 'inputstream.adaptive'
INPUTSTREAM_BETA  = 'inputstream.adaptive.testing'
CONTENT_TYPE      = 'episodes'
DISC_CACHE        = False
DTFORMAT          = '%Y-%m-%dT%H:%M:%S' #'YYYY-MM-DDTHH:MM:SS'
UTC_OFFSET        = datetime.datetime.utcnow() - datetime.datetime.now()

@ROUTER.route('/')
def buildMenu():
    PlutoTV().buildMenu()

@ROUTER.route('/live')
def getLive():
    PlutoTV().browseGuide(opt='live')
    
@ROUTER.route('/favorites')
def getLiveFavs():
    PlutoTV().browseGuide(opt='favorites')
       
@ROUTER.route('/lineup')
def getLineups():
    PlutoTV().browseGuide(opt='channels')
       
@ROUTER.route('/lineup/<chid>')
def getLineup(chid):
    PlutoTV().browseGuide(chid, opt='lineup')

@ROUTER.route('/categories')
def getCats():
    PlutoTV().browseCategories()
         
@ROUTER.route('/categories/<cat>')
def getCat(cat):
    PlutoTV().browseGuide(name=cat,opt='categories')
        
@ROUTER.route('/ondemand')
def getOD():
    PlutoTV().browseOndemand(opt='ondemand')
    
@ROUTER.route('/vod/<id>')
def getOndemand(id):
    PlutoTV().browseOndemand(id,opt='vod')

@ROUTER.route('/series/<season>/<sid>')
def getEpisodes(season,sid):
    PlutoTV().browseGuide(season, opt='episode', data=[PlutoTV().getVOD(sid)])
            
@ROUTER.route('/season/<sid>')
def getSeason(sid):
    PlutoTV().browseGuide(sid, opt='season', data=[PlutoTV().getVOD(sid)])
    
@ROUTER.route('/play/vod')#unknown bug causing this route to be called during /ondemand parse. todo find issue.
def dummy():
    pass

@ROUTER.route('/play/vod/<id>')
def playOD(id):
    PlutoTV().playVOD(id)
    
@ROUTER.route('/play/pvr/<id>')
def playChannel(id):
    PlutoTV().playLive(id,opt='pvr')

@ROUTER.route('/play/live/<id>')
def playChannel(id):
    PlutoTV().playLive(id,opt='live')

@ROUTER.route('/iptv/channels')
def iptv_channels():
    """Return JSON-STREAMS formatted data for all live channels"""
    from resources.lib.iptvmanager import IPTVManager
    port = int(ROUTER.args.get('port')[0])
    IPTVManager(port,PlutoTV()).send_channels()

@ROUTER.route('/iptv/epg')
def iptv_epg():
    """Return JSON-EPG formatted data for all live channel EPG data"""
    from resources.lib.iptvmanager import IPTVManager
    port = int(ROUTER.args.get('port')[0])
    IPTVManager(port,PlutoTV()).send_epg()
     
def getInputStream():
    if xbmc.getCondVisibility('System.AddonIsEnabled(%s)'%(INPUTSTREAM_BETA)):
        return INPUTSTREAM_BETA
    else: return INPUTSTREAM

def setUUID():
    if REAL_SETTINGS.getSetting("sid1_hex") and REAL_SETTINGS.getSetting("deviceId1_hex"): return
    REAL_SETTINGS.setSetting("sid1_hex",str(uuid.uuid1().hex))
    REAL_SETTINGS.setSetting("deviceId1_hex",str(uuid.uuid4().hex))

def getUUID():
    return REAL_SETTINGS.getSetting("sid1_hex"), REAL_SETTINGS.getSetting("deviceId1_hex")

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

class PlutoTV(object):
    def __init__(self, sysARG=sys.argv):
        log('__init__, sysARG = %s'%(sysARG))
        setUUID()
        self.sysARG    = sysARG
        self.cache     = SimpleCache()

            
    def getURL(self, url, param={}, header={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0'}, life=datetime.timedelta(minutes=15)):
        log('getURL, url = %s, header = %s'%(url, header))
        cacheresponse = self.cache.get('%s.getURL, url = %s.%s.%s'%(ADDON_NAME,url,param,header))
        if not cacheresponse:
            try:
                req = requests.get(url, param, headers=header)
                cacheresponse = req.json()
                req.close()
            except Exception as e: 
                log("getURL, Failed! %s"%(e), xbmc.LOGERROR)
                notificationDialog(LANGUAGE(30001))
                return {}
            self.cache.set('%s.getURL, url = %s.%s.%s'%(ADDON_NAME,url,param,header), json.dumps(cacheresponse), expiration=life)
            return cacheresponse
        return json.loads(cacheresponse)

      
    def buildHeader(self):
        header_dict               = {}
        header_dict['Accept']     = 'application/json, text/javascript, */*; q=0.01'
        header_dict['Host']       = 'api.pluto.tv'
        header_dict['Connection'] = 'keep-alive'
        header_dict['Referer']    = 'http://pluto.tv/'
        header_dict['Origin']     = 'http://pluto.tv'
        header_dict['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0'
        return header_dict


    def buildMenu(self):
        log('buildMenu')
        PLUTO_MENU = [(LANGUAGE(30011),(getLive    ,)),
                      (LANGUAGE(30040),(getLiveFavs,)),
                      (LANGUAGE(30018),(getLineups ,)),
                      (LANGUAGE(30017),(getCats    ,)),
                      (LANGUAGE(30012),(getOD      ,))]
        for item in PLUTO_MENU: self.addDir(*item)

        
    def buildGuide(self, data):
        channel, opt, name = data
        log('buildGuide, opt=%s, name=%s'%(opt, name))
        urls      = []
        mtype     = 'video'
        chid      = channel.get('_id','')
        chname    = channel.get('name','')
        chnum     = channel.get('number','')
        chplot    = (channel.get('description','') or channel.get('summary',''))
        chgeo     = channel.get('visibility','everyone') != 'everyone'
        chcat     = (channel.get('category','')    or channel.get('genre',''))
        chfanart  = channel.get('featuredImage',{}).get('path',FANART)
        chthumb   = channel.get('thumbnail',{}).get('path',ICON)
        chlogo    = channel.get('logo',{}).get('path',LOGO) 
        if REAL_SETTINGS.getSettingBool('Use_Color_Logos'):
            chlogo = channel.get('colorLogoPNG',{}).get('path',chlogo)

        ondemand  = channel.get('onDemand','false') == 'true'
        featured  = channel.get('featured','false') == 'true'
        timelines = channel.get('timelines',[])
        
        favorite  = channel.get('favorite','false') == 'true'
        if favorite: addFavorite(chnum, silent=True)
        favorite  = isFavorite(chnum)
        
        if   opt == 'featured'       and not featured:   return None
        elif opt == 'favorites'      and not favorite:   return None
        elif opt == 'categories'     and chcat != name:  return None
        elif opt in ['lineup','vod'] and chid  != name:  return None
        
        if opt in ['live','favorites']: DISC_CACHE = False
        if opt in ['channels','categories','ondemand','season']:
            if opt == 'season':
                seasons   = (channel.get('seasons',{}))
                vodimages = channel.get('covers',[])
                try:    vodlogo   = [image.get('url',[]) for image in vodimages if image.get('aspectRatio','') == '1:1'][0]
                except: vodlogo   = ''
                try:    vodfanart = [image.get('url',[]) for image in vodimages if image.get('aspectRatio','') == '16:9'][0]
                except: vodfanart = ''
                
                for season in seasons:
                    vodlogo   = (vodlogo   or chlogo)
                    vodfanart = (vodfanart or FANART)
                    mtype = 'episode'
                    label = 'Season %s'%(season['number'])
                    infoLabels = {"favorite":favorite,"chnum":chnum,"chname":chname,"mediatype":mtype,"label":label,"title":label,"plot":chplot, "code":chid, "genre":[chcat]}
                    infoArt    = {"thumb":vodlogo,"poster":vodlogo,"fanart":vodfanart,"icon":vodlogo,"logo":vodlogo,"clearart":chthumb}                    
                    self.addDir(label, (getEpisodes, season['number'], chid), infoLabels, infoArt)
            else:
                if opt == 'ondemand':
                    label = chname
                else: 
                    label = '%s| %s'%(chnum,chname)
                infoLabels = {"favorite":favorite,"chnum":chnum,"chname":chname,"mediatype":mtype,"label":label,"title":label,"plot":chplot, "code":chid, "genre":[chcat]}
                infoArt    = {"thumb":chthumb,"poster":chthumb,"fanart":chfanart,"icon":chlogo,"logo":chlogo,"clearart":chthumb}
                if opt == 'ondemand': 
                    self.addDir(label, (getOndemand, chid), infoLabels, infoArt)
                else:
                    self.addDir(label, (getLineup, chid), infoLabels, infoArt)        
        else:
            urls = channel.get('stitched',{}).get('urls',[])
            if opt == 'episode':
                try:    
                    timelines = list(filter(lambda k:k.get('number') == int(name), channel.get('seasons',[])))[0].get('episodes',[])
                except: 
                    timelines = []
            elif not timelines:
                opt = 'ondemand'
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
                    start  = strpTime(item['start'],'%Y-%m-%dT%H:%M:%S.000Z') + datetime.timedelta(seconds=tz)
                    stop   = strpTime(item['stop'],'%Y-%m-%dT%H:%M:%S.000Z')  + datetime.timedelta(seconds=tz)
                except:
                    start  = totstart
                    stop   = start + datetime.timedelta(seconds=epdur)
                totstart   = stop                  
                type       = series.get('type','')
                tvtitle    = series.get('name',''                           or chname)
                title      = (item.get('title',''))
                tvplot     = (series.get('description','')                  or series.get('summary','')      or chplot)
                tvoutline  = (series.get('summary','')                      or series.get('description','')  or chplot)
                tvthumb    = (series.get('featuredImage',{}).get('path','') or chfanart)
                tvfanart   = (series.get('featuredImage',{}).get('path','') or chfanart)
                epid       = episode['_id']
                epnumber   = episode.get('number',0)
                epseason   = episode.get('season',0)
                epname     = (episode['name'])
                epplot     = (episode.get('description','') or tvplot or epname)
                epgenre    = (episode.get('genre','')       or chcat)
                eptag      = episode.get('subGenre','')
                epmpaa     = episode.get('rating','')
                epislive   = episode.get('liveBroadcast','false') == 'true'
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
                epposter   = (episode.get('poster',{}).get('path','')        or vodlogo   or vodposter or vodthumb  or tvthumb)
                epthumb    = (episode.get('thumbnail',{}).get('path','')     or vodlogo   or vodthumb  or vodposter or tvthumb)
                epfanart   = (episode.get('featuredImage',{}).get('path','') or vodfanart or tvfanart)
                
                if type == 'series':
                    mtype   = 'tvshows'
                    label   = tvtitle
                    tvtitle = tvtitle
                    epname  = ''
                    thumb   = tvthumb
                elif type in ['tv','episode']:
                    mtype  = 'episodes'
                    tvtitle = chname
                    epname  = epname
                    thumb  = epthumb
                    if epseason > 0 and epnumber > 0:
                        seaep  = '%sx%s'%(epseason, epnumber)
                        label  = '%s (%s) - %s'%(chname,seaep,epname)
                    else:
                        label  = '%s - %s'%(tvtitle,epname)
                else:
                    mtype   = 'files'
                    label   = chname
                    thumb   = chthumb
                    
                # if type in ['movie','film']:
                    # mtype  = 'movie'
                    # thumb  = epposter
                
                # elif type == 'series':
                    # mtype   = 'tvshow'
                    # tvtitle = chname
                        # else: label  = '%s - %s'%(tvtitle, label)
                    # elif type != 'series': label = '%s - %s'%(chname,epname)
                    # else: label = epname
                if type == 'music' or epgenre.lower() == 'music': 
                    mtype = 'musicvideo'

                if opt in ['live','favorites']:
                    if stop < now or start > now: continue
                    label = '%s| %s'%(chnum,chname)
                    if type in ['movie','film']:
                        mtype = 'movies'
                        thumb = epposter
                        label = '%s : [B]%s[/B]'%(label, title)
                    elif type in ['tv','series']:
                        mtype = 'episodes'
                        thumb = epposter
                        label = "%s : [B]%s - %s[/B]" % (label, tvtitle, epname)
                    elif len(epname) > 0: label = '%s: [B]%s - %s[/B]'%(label, title, epname)
                    epname = label
                    if type == 'music' or epgenre.lower() == 'music': mtype = 'musicvideo'

                elif opt == 'lineup':
                    if now > stop: continue
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
                if opt == 'ondemand' and type in ["series"]:
                    mtype = 'season'
                    infoLabels = {"mediatype":mtype,"label":label,"title":epname,"plot":epplot, "code":chid, "genre":[epgenre],"tvshowtitle":tvtitle}
                    infoArt    = {"thumb":thumb,"poster":epposter,"fanart":epfanart,"icon":chlogo,"logo":chlogo,"clearart":chthumb}
                    self.addDir(label, (getSeason,epid), infoLabels, infoArt)
                elif opt != 'guide':
                    infoLabels = {"favorite":favorite,"chnum":chnum,"chname":chname,"mediatype":mtype,"label":label,"title":epname,"plot":epplot, "code":epid, "genre":[epgenre], "duration":epdur,'season':epseason,'episode':epnumber,"tvshowtitle":tvtitle}
                    infoArt    = {"thumb":thumb,"poster":epposter,"fanart":epfanart,"icon":chlogo,"logo":chlogo,"clearart":chthumb}
                    if opt == 'play': 
                        if start <= now and stop > now: infoLabels['duration'] = ((stop) - now).seconds
                        self.addPlaylist(label, urls, infoLabels, infoArt)
                    elif opt in ['ondemand','vod','episode']:
                        self.addLink(label, (playOD,epid), infoLabels, infoArt)
                    else:
                        if urls == 'NEXT_SHOW': chid = urls
                        self.addLink(label, (playChannel,chid), infoLabels, infoArt)
            CONTENT_TYPE = '%ss'%mtype


    def browseGuide(self, name=None, opt=None, data=None):
        log('browseGuide, name=%s, opt=%s'%(name,opt))
        if data is None: data = self.getGuidedata()
        # if opt == 'categories': data = self.getGuidedata(full=True).get('categories',[])
        self.poolList(self.buildGuide, zip(data,repeat(opt),repeat(name)))
             

    def browseCategories(self):
        log('browseCategories')
        categoryMenu = list(self.getCategories())
        for item in categoryMenu:
            self.addDir(*item)
       
       
    def browseOndemand(self, id=None, opt='ondemand'):
        log('browseOndemand, opt = %s'%(opt))
        self.browseGuide(id, opt, data=self.getOndemand()['categories'])
        
       
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
        # categories = sorted(self.getGuidedata(full=True).get('categories',[]), key=lambda k: k['order'])
        # for category in categories: 
            # yield (category['name'], 'categories', 0, False, {'thumb':category.get('images',[{}])[0].get('url',ICON),'fanart':category.get('images',[{},{}])[1].get('url',FANART)})
        collect= []
        data = self.getChannels()
        for channel in data: collect.append(channel['category'])
        counter = collections.Counter(collect)
        categories = sorted(self.getGuidedata(full=True).get('categories',[]), key=lambda k: k['order'])
        for key, value in sorted(counter.items()): 
            category = {}
            for category in categories:
                if category['name'].lower() == key.lower(): break
            yield (key,(getCat,key), {}, {'thumb':category.get('images',[{}])[0].get('url',ICON),'fanart':category.get('images',[{},{}])[1].get('url',FANART)})
        
        
    @use_cache(7)
    def getCatbyID(self, id):
        categories = self.getGuidedata(full=True).get('categories',[])
        try: return list(filter(lambda k:k.get('id') == id, categories))[0].get('name','')
        except: return ''
        
            
    def getChans(self):
        log('getChannels')
        # https://github.com/add-ons/service.iptv.manager/wiki/JSON-STREAMS-format
        stations  = self.getGuidedata(full=True).get('channels',[])
        return list(self.poolList(self.buildStation, stations,'channel'))


    def getGuide(self):
        log('getGuide')
        # https://github.com/add-ons/service.iptv.manager/wiki/JSON-EPG-format
        stations  = self.getGuidedata(full=True).get('channels',[])
        return {k:v for x in self.poolList(self.buildStation, stations,'programmes') for k,v in x.items()}
        

    def buildStation(self, data):
        station, opt = data
        stnum    = station['number']
        stname   = station.get('name','')
        
        images   = station.get('images',[])
        if REAL_SETTINGS.getSettingBool('Use_Color_Logos'):
            try:   chlogo = list(filter(lambda k:k.get('type','') == 'colorLogoPNG', images))[0].get('url',LOGO)
            except:chlogo = LOGO
        else:
            try:   chlogo = list(filter(lambda k:k.get('type','') == 'logo', images))[0].get('url',LOGO)
            except:chlogo = LOGO
        try:   chfanart = list(filter(lambda k:k.get('type','') == 'logofeaturedImage', images))[0].get('url',FANART)
        except:chfanart = FANART
        category = self.getCatbyID(station.get('categoryID',''))
        if category == 'Pluto TV':
            chlogo   = LOGO
            chfanart = FANART
        favorite = isFavorite(stnum)
        channel  = {"name"  :stname,
                    "stream":"plugin://%s/play/pvr/%s"%(ADDON_ID,station.get('id','')), 
                    "id"    :"%s.%s@%s"%(stnum,slugify(stname),slugify(ADDON_NAME)), 
                    "logo"  :(chlogo or LOGO),
                    "preset":stnum,
                    "group" :[category,ADDON_NAME],
                    "radio" :False}
        if favorite: channel['group'].append(LANGUAGE(49012))
        channel['group'] = ';'.join(channel['group'])
        if REAL_SETTINGS.getSettingBool('Build_Favorites') and not favorite: return None
        elif opt == 'channel': return channel
        else:
            programmes = {channel['id']:[]}
            listings   = station.get('timelines',[])
            for listing in listings:
                episode = listing.get('episode',{})
                series  = episode.get('series',{})
                uri     = episode.get('_id','')
                try: starttime  = strpTime(listing['start'],'%Y-%m-%dT%H:%M:%S.%fZ')
                except: continue
                try:    aired = strpTime(episode['clip']['originalReleaseDate'])
                except: aired = starttime
                program = {"start"      :starttime.strftime(DTFORMAT),
                           "stop"       :(starttime + datetime.timedelta(seconds=(int(episode['duration']) // 1000))).strftime(DTFORMAT),
                           "title"      :listing.get('title',channel['name']),
                           "description":(episode.get('description','') or xbmc.getLocalizedString(161)),
                           "subtitle"   :episode.get('name',''),
                           "genre"      :episode.get('genres',""),
                           "image"      :(episode.get('poster','') or episode.get('thumbnail','') or episode.get('featuredImage',{})).get('path',chfanart),
                           "date"       :aired.strftime('%Y-%m-%d'),
                           "credits"    :"",
                           "stream"     :'plugin://%s/play/vod/%s'%(ADDON_ID,uri)}
                programmes[channel['id']].append(program)
            return programmes
                       
             
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


    def resolveURL(self, id, opt):
        log('resolveURL, id = %s, opt = %s'%(id,opt))  
        self.listitems = []
        self.playlist  = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        self.playlist.clear()
        channel = list(filter(lambda k:k.get('_id','') == id, self.getGuidedata()))[0]
        urls = channel.get('stitched',{}).get('urls',[])
        if isinstance(urls, list): urls = [url['url'] for url in urls if url['type'].lower() == 'hls'][0]
        liz = xbmcgui.ListItem(channel.get('name'),path=urls)
        liz.setProperty('IsPlayable','true')
        liz.setProperty('IsInternetStream','true')
        if opt != 'pvr':
            self.browseGuide(opt='play',data=[channel])
            [self.playlist.add(urls,lz,idx) for idx,lz in enumerate(self.listitems)]
            liz = self.listitems.pop(0)
            liz.setPath(path=urls)
        return liz
        

    def playVOD(self, id):
        log('playVOD, id = %s'%id)
        data = self.getClips(id)[0]
        if not data: return
        name  = data.get('name','')
        epdur = (data.get('duration',0) // 1000)
        url   = (data.get('url','') or data.get('sources',[])[0].get('file',''))
        liz   = xbmcgui.ListItem(name)
        liz.setPath(url)
        liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name,"duration":epdur})
        liz.setArt({'thumb':data.get('thumbnail',ICON),'fanart':data.get('thumbnail',FANART)})
        liz.setProperty("IsPlayable","true")
        if 'm3u8' in url.lower() and inputstreamhelper.Helper('hls').check_inputstream():
            inputstream = getInputStream()
            liz.setProperty('inputstream',inputstream)
            liz.setProperty('%s.manifest_type'%(inputstream),'hls')
            liz.setMimeType('application/vnd.apple.mpegurl')
        xbmcplugin.setResolvedUrl(ROUTER.handle, True, liz)
        
        
    def playLive(self, id, opt='live'):
        log('playLive, id = %s, opt = %s'%(id,opt))   
        if id == 'NEXT_SHOW': 
            found = False
            liz   = xbmcgui.ListItem()
            notificationDialog(LANGUAGE(30029), time=4000)
        else:
            found = True
            liz = self.resolveURL(id, opt)
            url = liz.getPath()
            if url.endswith('?deviceType='): url = url.replace('deviceType=','deviceType=&deviceMake=&deviceModel=&&deviceVersion=unknown&appVersion=unknown&deviceDNT=0&userId=&advertisingId=&app_name=&appName=&buildVersion=&appStoreUrl=&architecture=&includeExtendedEvents=false')#todo lazy fix replace
            if 'sid' not in url: url = url.replace('deviceModel=&','deviceModel=&' + LANGUAGE(30022)%(getUUID()))
            url = url.replace('deviceType=&','deviceType=web&').replace('deviceMake=&','deviceMake=Chrome&') .replace('deviceModel=&','deviceModel=Chrome&').replace('appName=&','appName=web&')#todo replace with regex!
            log('playVideo, url = %s'%url)
            liz.setPath(url)
            if 'm3u8' in liz.getPath().lower() and inputstreamhelper.Helper('hls').check_inputstream():
                inputstream = getInputStream()
                liz.setProperty('inputstream',inputstream)
                liz.setProperty('%s.manifest_type'%(inputstream),'hls')
                liz.setMimeType('application/vnd.apple.mpegurl')
        xbmcplugin.setResolvedUrl(ROUTER.handle, found, liz)

           
    def addPlaylist(self, name, path='', infoList={}, infoArt={}, infoVideo={}, infoAudio={}, infoType='video'):
        log('addPlaylist, name = %s'%name)
        liz = xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable','true')
        liz.setProperty('IsInternetStream','true')
        if infoList:  liz.setInfo(type=infoType, infoLabels=infoList)
        else:         liz.setInfo(type=infoType, infoLabels={"mediatype":infoType,"label":name,"title":name})
        if infoArt:   liz.setArt(infoArt)
        else:         liz.setArt({'thumb':ICON,'fanart':FANART})
        if infoVideo: liz.addStreamInfo('video', infoVideo)
        if infoAudio: liz.addStreamInfo('audio', infoAudio)
        self.listitems.append(liz)
        
    
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
        if infoList['favorite']:
            liz.addContextMenuItems([(LANGUAGE(49010), 'RunScript(special://home/addons/%s/favorites.py, %s)'%(ADDON_ID,urllib.parse.quote(json.dumps({"chnum":infoList.pop('chnum'),"chname":infoList.pop('chname'),"mode":"del"}))))])
        else:
            liz.addContextMenuItems([(LANGUAGE(49009), 'RunScript(special://home/addons/%s/favorites.py, %s)'%(ADDON_ID,urllib.parse.quote(json.dumps({"chnum":infoList.pop('chnum'),"chname":infoList.pop('chname'),"mode":"add"}))))])
        return liz
        
        
    def run(self): 
        ROUTER.run()
        xbmcplugin.setContent(ROUTER.handle     ,CONTENT_TYPE)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(ROUTER.handle ,cacheToDisc=DISC_CACHE)