#   Copyright (C) 2019 Lunatixz
#
#
# This file is part of HDHomerun Simple
#
# HDHomerun Simple is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HDHomerun Simple is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HDHomerun Simple. If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, _strptime, re, routing
import random, string, traceback, collections
import socket, json, inputstreamhelper, requests

from six.moves     import urllib
from simplecache   import SimpleCache, use_cache
from itertools     import repeat, cycle, chain, zip_longest
from kodi_six      import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode
from pyhdhr        import PyHDHR
    
try:
    if xbmc.getCondVisibility('System.Platform.Android'): raise Exception('Using Android threading')
    from multiprocessing.pool import ThreadPool
    SUPPORTS_POOL = True
except Exception:
    SUPPORTS_POOL = False

# Plugin Info
ADDON_ID      = 'plugin.video.hdhomerun.simple'
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
CONTENT_TYPE  = 'files'
DISC_CACHE    = False
DTFORMAT      = '%Y-%m-%dT%H:%M:%S' #'YYYY-MM-DDTHH:MM:SS'
UTC_OFFSET    = datetime.datetime.utcnow() - datetime.datetime.now()
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
MTYPES        = {'EP':'episode','SH':'episode','MV':'movie'}
TRANTYPES     = ['None','Heavy','Mobile','Internet540','Internet480','Internet360','Internet240']

@ROUTER.route('/')
def buildMenu():
    HDHR().browseTuners()

@ROUTER.route('/<tuner>')
def buildMenu(tuner):
    HDHR().browseTunerMenu(tuner)
   
@ROUTER.route('/live/<tuner>')
def getLive(tuner):
    HDHR().browseLive(tuner)
    
@ROUTER.route('/favorites/<tuner>')
def getLiveFavs(tuner):
    HDHR().browseLive(tuner,opt='favorites')

@ROUTER.route('/channels/<tuner>')
def getChans(tuner):
    HDHR().browseGuide(tuner)
            
@ROUTER.route('/lineup/<tuner>/<chid>')
def getLineup(tuner,chid):
    HDHR().browseGuide(tuner,chid)
       
@ROUTER.route('/recordings/<tuner>')
def getRec(tuner):
    HDHR().browseRecordings(tuner)
    
@ROUTER.route('/series/<tuner>/<sid>')
def getSeries(tuner,sid):
    HDHR().browseSeries(tunerkey,sid)
        
@ROUTER.route('/search/<tuner>')
def getSearch(tuner):
    HDHR().buildSearch(tuner)
    
@ROUTER.route('/search/<query>')
def getQuery(query):
    HDHR().browseSearch(query)
    
@ROUTER.route('/play/<tuner>/vod/<url>')
def playVOD(tuner,url):
    HDHR().playLive(tuner,url,opt='vod')

@ROUTER.route('/play/pvr/<id>')
def playChannel(id):
    HDHR().playLive('All',id,opt='pvr')

@ROUTER.route('/play/<tuner>/live/<id>')
def playChannel(tuner,id):
    HDHR().playLive(tuner,id,opt='live')

@ROUTER.route('/iptv/channels')
def iptv_channels():
    """Return JSON-STREAMS formatted data for all live channels"""
    from resources.lib.iptvmanager import IPTVManager
    port = int(ROUTER.args.get('port')[0])
    IPTVManager(port,HDHR()).send_channels()

@ROUTER.route('/iptv/epg')
def iptv_epg():
    """Return JSON-EPG formatted data for all live channel EPG data"""
    from resources.lib.iptvmanager import IPTVManager
    port = int(ROUTER.args.get('port')[0])
    IPTVManager(port,HDHR()).send_epg()
        
def slugify(text):
    non_url_safe = [' ','"', '#', '$', '%', '&', '+',',', '/', ':', ';', '=', '?','@', '[', '\\', ']', '^', '`','{', '|', '}', '~', "'"]
    non_url_safe_regex = re.compile(r'[{}]'.format(''.join(re.escape(x) for x in non_url_safe)))
    text = non_url_safe_regex.sub('', text).strip()
    text = u'_'.join(re.split(r'\s+', text))
    return text

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log('%s-%s-%s'%(ADDON_ID,ADDON_VERSION,msg), level)
      
def collectData(mydict, key):
    items = []
    for item in mydict: items.append(item[key])
    counter = collections.Counter(items)
    return counter.most_common()
    
def getIndex(items, key, value):
    return (filter(lambda k:k[key] == value, items))
    
def notificationDialog(message, header=ADDON_NAME, sound=False, time=1000, icon=ICON):
    try:    return xbmcgui.Dialog().notification(header, message, icon, time, sound)
    except: return xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))

class HDHR(object):
    def __init__(self, sysARG=sys.argv):
        log('__init__, sysARG = %s'%(sysARG))
        self.sysARG    = sysARG
        self.cache     = SimpleCache()
        self.pyHDHR    = PyHDHR.PyHDHR()
        self.tuners    = self.getTuners()
        self.hasDVR    = self.pyHDHR.hasSDDVR()
        self.transcode = TRANTYPES[int(REAL_SETTINGS.getSetting('Preferred_Transcoding'))].lower()
        self.fillDeviceInfo()
        
        
    def fillDeviceInfo(self):
        REAL_SETTINGS.setSetting('HDHR.TotalDevices',str(len(self.tuners)))
        for idx, tunerkey in enumerate(self.tuners):
            idx+=1
            REAL_SETTINGS.setSetting('HDHR.FriendlyName.%d'    %idx,'%s - %s'%(self.tuners[tunerkey].FriendlyName,tunerkey))
            REAL_SETTINGS.setSetting('HDHR.FirmwareName.%d'    %idx,'%s - %s'%(self.tuners[tunerkey].FirmwareName.upper(),self.tuners[tunerkey].FirmwareVersion))
            REAL_SETTINGS.setSetting('HDHR.TunerCount.%d'      %idx,str(self.tuners[tunerkey].TunerCount))
            REAL_SETTINGS.setSetting('HDHR.LocalIP.%d'         %idx,str(self.tuners[tunerkey].getLocalIP()))
            REAL_SETTINGS.setSetting('HDHR.TranscodeOption.%d' %idx,str(self.tuners[tunerkey].TranscodeOption))  
        
             
    def browseTuners(self):
        log('browseTuners')
        for tunerkey in self.tuners: 
            if len(self.tuners) == 1: return self.browseTunerMenu(tunerkey)
            self.addDir('%s - %s'%(self.tuners[tunerkey].FriendlyName,tunerkey), (buildMenu, tunerkey))
        
            
    def browseTunerMenu(self, tunerkey='All'):
        log('browseTunerMenu, tunerkey = %s'%(tunerkey))
        self.setDevice(tunerkey)
        HDHR_MENU = [(LANGUAGE(30110),getLive),
                     (LANGUAGE(49011),getLiveFavs),
                     (LANGUAGE(30112),getChans),
                     (LANGUAGE(30111),getRec),
                     (LANGUAGE(30113),getSearch)]
        for idx, tup in enumerate(HDHR_MENU):
            if tup[0] == LANGUAGE(30111) and not self.hasDVR: continue
            self.addDir(tup[0],(tup[1],tunerkey))
        
           
    def browseLive(self, tunerkey='All', opt='live'):
        self.setDevice(tunerkey)
        progs = self.pyHDHR.getWhatsOn()
        channels = self.getChannelList()
        self.poolList(self.buildLive, channels,(tunerkey,progs,opt))
            
            
    def buildLive(self, data):
        channel, data   = data
        tunerkey,progs,opt = data
        self.buildChannelListItem(tunerkey, str(channel), progs.get(str(channel),None), opt)
        
            
    def browseGuide(self, tunerkey='All', chnum=None):
        self.setDevice(tunerkey)
        channels = self.getChannelList()
        self.poolList(self.buildGuide, channels,(tunerkey,chnum))
        
    
    def buildGuide(self, data):
        channel, data   = data
        tunerkey, chnum = data
        if chnum is not None and chnum != str(channel): return None
        chan        = self.getChannelInfo(channel)
        channelname = (chan.getAffiliate() or chan.getGuideName() or chan.getGuideNumber() or 'N/A')
        isFavorite  = chan.getFavorite() == 1
        isHD        = chan.getHD() == 1
        hasCC       = True
        chlogo      = (chan.getImageURL() or ICON)
        if chnum is None: self.buildChannelListItem(tunerkey, channel, None, opt='channels')
        else:
            programs = chan.getProgramInfos()
            for program in programs:
                if chnum != str(channel): return None
                self.buildChannelListItem(tunerkey, chnum, program, opt='lineup')

                    
    def browseRecordings(self, tunerkey='All'):
        log('browseRecordings')
        self.setDevice(tunerkey)
        progs = self.pyHDHR.getFilteredRecordedPrograms()

        if not progs: return
        
        collect = []
        for prog in progs: collect.append({'name':prog.getTitle(),'prog':prog})
        for show in collectData(collect, 'name'):
            prog      = list(getIndex(collect, 'name', show[0]))[0]['prog']
            title     = prog.getTitle()
            eptitle   = prog.getEpisodeTitle()
            starttime = (datetime.datetime.fromtimestamp(float(prog.getStartTime())))
            if show[1] > 1:
                self.buildChannelListItem(tunerkey, prog.getChannelNumber(), prog, opt='show')
            else:
                self.buildChannelListItem(tunerkey, prog.getChannelNumber(), prog, opt='rec')

            
    def browseSeries(self, seriesid):
        log('browseSeries')
        progs = self.pyHDHR.getFilteredRecordedPrograms(grouptype=1, groupby=seriesid)
        if not progs: return
        for prog in progs:
            title      = prog.getTitle()
            eptitle    = prog.getEpisodeTitle()
            starttime  = (datetime.datetime.fromtimestamp(float(prog.getStartTime())))
            stime      = starttime.strftime('%I:%M %p').lstrip('0')
            if len(eptitle) > 0: label = '%s: %s - %s'%(stime,title,eptitle)
            else: label = '%s: %s'%(stime,title)
            label, liz = self.buildRecordListItem(prog, label)
            self.addLink(label, (playVOD,tunerkey,prog.getPlayURL()), listitem=liz)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_DATEADDED)
            
        
    def buildSearch(self, tunerkey='All'):
        log('buildSearch')
        self.setDevice(tunerkey)
        kb = xbmc.Keyboard('', LANGUAGE(30109)%ADDON_NAME)
        xbmc.sleep(500)
        kb.doModal()
        if kb.isConfirmed():
            self.browseSearch(kb.getText(),tunerkey)
            
            
    def browseSearch(self, query, tunerkey='All'):
        progs = (self.pyHDHR.searchWhatsOn(query))
        if progs is not None:
            for channel in progs:
                self.buildChannelListItem(tunerkey, channel, progs[channel], opt='searchWhatsOn')

        progs = (self.pyHDHR.search(query))
        if progs is not None: 
            for channel in progs:
                self.buildChannelListItem(tunerkey, channel, progs[channel], opt='search')
                
        if not self.hasDVR: return
        progs = self.pyHDHR.searchRecorded(query)
        for channel in progs:
            if progs is not None:
                self.buildRecordListItem(tunerkey, progs[channel], opt='searchRecorded')
    
            
    def buildRecordListItem(self, prog, label=None, opt='live'):
        pass
        # if opt in ['show','rec']:
            # info     = item
            # chlogo   = (info.getChannelImageURL()  or ICON)
            # chname   = (info.getChannelAffiliate() or info.getChannelName() or info.getChannelNumber() or 'N/A')
            # favorite = True
            # video    = {}
            # audio    = {}
        # else:
        # return self.buildChannelListItem(prog.getChannelNumber(), prog, label, opt)
        
        
    def buildChannelListItem(self, tunerkey, channel, item=None, opt='live'):
        self.setDevice(tunerkey)
        info = self.getChannelInfo(channel)
        if   info is None:  return None
        elif info.getDRM(): return None
        elif info.getTuner().getDeviceID() != tunerkey: return None
        
        favorite = info.getFavorite() == 1
        chname   = (info.getAffiliate() or info.getGuideName() or info.getGuideNumber() or 'N/A')
        tuner    = info.getTuner()
        if opt == 'favorites' and not favorite: return None
        
        video = {'codec':''}
        audio = {'codec':''}
        if tuner.getModelNumber() == "HDTC-2US":
            if self.transcode == 'none': 
                  tranOPT = (tuner.getTranscodeOption() or 'none')
            else: tranOPT = self.transcode
            if tranOPT != "none": video['codec'] = 'h264'
        else:
            if info.getVideoCodec() == "H264": 
                video['codec'] = 'h264'
            if info.getAudioCodec() == "AAC":
                if tuner.getModelNumber() == "HDHR4-2DT": 
                    audio['codec'] = 'aac_latm'
                else: 
                    audio['codec'] = 'aac'
            elif info.getAudioCodec() == "MPEG": 
                audio['codec'] = 'mp2'

        if info.getHD() == 1:
            video['width']  = 1080
            video['aspect'] = "1.78"
            if video['codec'] == 'mpeg2video' or video['codec'] == 'mpeg1video': 
                audio['bitrate'] = 13000
            else: audio['bitrate'] = 4000
        else: 
            if video['codec'] == 'mpeg2video' or video['codec'] == 'mpeg1video': 
                audio['bitrate'] = 4000
            else:audio['bitrate'] = 1500
                
        chlogo   = (info.getImageURL() or ICON)
        chnum    = channel
        path     = chnum
        video    = {"codec":'mpeg2video',"width":480,"aspect":"1.33"}
        audio    = {"codec":'ac3',"bitrate":1500}
        label    = '%s| %s'%(chnum,chname)
        
        if item is not None:
            if item.getEpisodeTitle(): 
                title = '%s - %s'%(item.getTitle(), item.getEpisodeTitle())
            else: 
                title = (item.getTitle() or '')
                
            if item.getSynopsis(): 
                plot = (item.getSynopsis() or xbmc.getLocalizedString(161))
            else:
                plot = xbmc.getLocalizedString(161)
                
            if   opt == 'searchRecorded': title = '%s (%s)'%(title,LANGUAGE(30116))
            elif opt == 'searchWhatsOn':  title = '%s (%s)'%(title,LANGUAGE(30117))
            elif opt == 'search':         title = '%s (%s)'%(title,LANGUAGE(30118))
            
            thumb      = (item.getImageURL() or chlogo)
            now        = datetime.datetime.now()
            starttime  = datetime.datetime.fromtimestamp(float(item.getStartTime()))
            endtime    = datetime.datetime.fromtimestamp(float(item.getEndTime()))
            runtime    = (endtime - starttime).seconds
            try:    aired = datetime.datetime.fromtimestamp(float(item.getOriginalAirdate()))
            except: aired = starttime
            
            if opt in ['live','favorites']:
                chname   = '%s| %s'%(channel,chname)
                label    = '%s : [B] %s[/B]'%(chname, title)
            elif opt in ['lineup','vod']:
                if now >= starttime and now < endtime:
                    label = '%s - [B]%s[/B]'%(starttime.strftime('%I:%M %p').lstrip('0'),title)
                else: 
                    path  = 'NEXT_SHOW'
                    label = '%s - %s'%(starttime.strftime('%I:%M %p').lstrip('0'),title)
            elif opt == 'show':
                label = title
            else: 
                label = '%s: %s - [B]%s[/B]'%(starttime.strftime('%I:%M %p').lstrip('0'),chname,title)
                
            try:    mtype = MTYPES[item.getEpisodeNumber()[:2]]
            except: mtype = 'episode'
            infoLabels = {"favorite":favorite,"chnum":chnum,"chname":chname,"mediatype":mtype,"label":label,"title":label,'duration':runtime,'plot':plot,"aired":aired.strftime('%Y-%m-%d')}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":chlogo,"logo":chlogo}
        else:
            label      = '%s| %s'%(chnum,chname)
            infoLabels = {"mediatype":"episode" ,"label":label,"title":label}
            infoArt    = {"thumb":chlogo,"poster":chlogo,"fanart":FANART,"icon":chlogo,"logo":chlogo}
        if opt in ['live','favorites','lineup']:
            self.addLink(label, (playChannel,tunerkey,path), infoList=infoLabels, infoArt=infoArt, infoVideo=video, infoAudio=audio)
        elif opt == 'play': 
            if starttime <= now and endtime > now: infoLabels['duration'] = ((endtime) - now).seconds
            self.addPlaylist(label, path, infoLabels, infoArt, video, audio)
        elif opt in ['channels']:
            self.addDir(label,(getLineup,tunerkey,chnum), infoList=infoLabels, infoArt=infoArt, infoType='video')
        elif opt == 'show':
            self.addDir(label,(getSeries,tunerkey,item.getSeriesID()), infoList=infoLabels, infoArt=infoArt, infoVideo=video, infoAudio=audio)
        elif opt == 'vod':
            self.addLink(label,(playVOD,tunerkey,prog.getPlayURL()), infoList=infoLabels, infoArt=infoArt, infoVideo=video, infoAudio=audio)
        else:
            self.addLink(label,(playChannel,tunerkey,path), infoList=infoLabels, infoArt=infoArt, infoVideo=video, infoAudio=audio)
        
        
    def hasHDHR(self):
        return len((self.tuners)) > 0

        
    def setDevice(self, tunerkey='All'):
        log('setDevice, tunerkey = %s'%(tunerkey))
        if tunerkey != 'All': self.pyHDHR.setManualTunerList(tunerkey)
        return True
        
    
    def getTuners(self):
        return self.pyHDHR.getTuners()
        
        
    def getChannelName(self, channel):
        chan = self.getChannelInfo(str(channel))
        return (chan.getAffiliate() or chan.getGuideName() or chan.getGuideNumber() or 'N/A')
        
        
    def getChannelList(self):
        return self.pyHDHR.getChannelList()
        

    def getLiveURL(self, channel):
        return self.pyHDHR.getLiveTVURL(str(channel))

  
    def getChannelInfo(self, channel):
        return self.pyHDHR.getChannelInfo(str(channel))
        
        
    def getChannels(self):
        log('getChannels')
        # https://github.com/add-ons/service.iptv.manager/wiki/JSON-STREAMS-format
        stations = self.getChannelList()
        return list(self.poolList(self.buildStation, stations,'channel'))


    def getGuide(self):
        log('getGuide')
        # https://github.com/add-ons/service.iptv.manager/wiki/JSON-EPG-format
        stations = self.getChannelList()
        return {k:v for x in self.poolList(self.buildStation, stations,'programmes') for k,v in x.items()}
        
        
    def buildStation(self, data):
        station, opt = data
        chan = self.getChannelInfo(station)
        if   chan is None:  return None
        elif chan.getDRM(): return None
        
        stnum    = station
        stname   = (chan.getAffiliate() or chan.getGuideName() or chan.getGuideNumber() or str(stnum))
        if not stname: return None
        favorite = chan.getFavorite() == 1
        channel  = {"name"  :stname,
                    "stream":"plugin://%s/play/pvr/%s"%(ADDON_ID,stnum), 
                    "id"    :"%s.%s@%s"%(stnum,slugify(stname),slugify(ADDON_NAME)), 
                    "logo"  :(chan.getImageURL() or LOGO), 
                    "preset":str(stnum),
                    "group" :ADDON_NAME,
                    "radio" :False}
        if favorite: channel['group'] = ';'.join([LANGUAGE(49012),ADDON_NAME])
        if REAL_SETTINGS.getSettingBool('Build_Favorites') and not favorite: return None
        elif opt == 'channel': return channel
        else:
            programmes = {channel['id']:[]}
            listings   = chan.getProgramInfos()
            for item in listings:
                starttime  = datetime.datetime.fromtimestamp(float(item.getStartTime())) + UTC_OFFSET
                endtime    = datetime.datetime.fromtimestamp(float(item.getEndTime())) + UTC_OFFSET
                try:    aired = datetime.datetime.fromtimestamp(float(item.getOriginalAirdate()))
                except: aired = starttime
                program = {"start"      :starttime.strftime(DTFORMAT),
                           "stop"       :endtime.strftime(DTFORMAT),
                           "title"      :(item.getTitle() or channel['name']),
                           "description":(item.getSynopsis() or xbmc.getLocalizedString(161)),
                           "subtitle"   :(item.getEpisodeTitle() or ""),
                           "episode"    :"",
                           "genre"      :"",
                           "image"      :(item.getImageURL() or channel['logo']),
                           "date"       :aired.strftime('%Y-%m-%d'),
                           "credits"    :"",
                           "stream"     :""}
                programmes[channel['id']].append(program)
            return programmes
                       

    def playVideo(self, channel, url):
        log('playVideo, channel = %s, url = %s'%(channel,url))
        liz = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)
        

    def resolveURL(self, tunerkey, channel, opt='pvr'):
        log('resolveURL, channel = %s, opt = %s'%(channel,opt)) 
        self.listitems = []
        self.playlist  = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        self.playlist.clear()
        liz = xbmcgui.ListItem('')
        self.setDevice(tunerkey)
        info  = self.pyHDHR.getLiveTVChannelInfo(channel)
        if not info: return liz
            
        url   = info.getURL()
        tuner = info.getTuner()
        if tuner.getModelNumber() == "HDTC-2US":
            if self.transcode == 'none': tranOPT = (tuner.getTranscodeOption() or 'none')
            else: tranOPT = self.transcode
            log("resolveURL, Tuner transcode option: " + tranOPT)
            if tranOPT != "none": video = {'codec': 'h264'}
            url = "%s?transcode=%s"%(url,tranOPT)
        else: liz.setMimeType('video/mpeg')
        liz.setProperty('IsPlayable','true') 
        
        if opt != 'pvr':
            chan  = self.getChannelInfo(channel)
            progs = chan.getProgramInfos()
            for prog in progs: self.buildChannelListItem(tunerkey, channel, prog, 'play')
            [self.playlist.add(url,lz,idx) for idx,lz in enumerate(self.listitems)]
            liz = self.listitems.pop(0)
            liz.setPath(path=url)
        else: liz.setPath(url)
        return liz
        
        
    def playLive(self, tunerkey, channel, opt='live'):
        log('playLive, channel = %s, opt = %s'%(channel,opt))
        self.setDevice(tunerkey)
        if channel == 'NEXT_SHOW': 
            found = False
            liz   = xbmcgui.ListItem(LANGUAGE(30029))
            notificationDialog(LANGUAGE(30029), time=4000)
        else:            
            found = True
            liz   = self.resolveURL(tunerkey,channel,opt)
        xbmcplugin.setResolvedUrl(ROUTER.handle, found, liz)
    
    
    def addPlaylist(self, name, path='', infoList={}, infoArt={}, infoVideo={}, infoAudio={}, infoType='video', listitem=None):
        log('addPlaylist, name = %s'%name)
        if listitem is None: 
            liz = xbmcgui.ListItem(name)        
            if infoList:  liz.setInfo(type=infoType, infoLabels=infoList)
            else:         liz.setInfo(type=infoType, infoLabels={"mediatype":infoType,"label":name,"title":name})
            if infoArt:   liz.setArt(infoArt)
            else:         liz.setArt({'thumb':ICON,'fanart':FANART})
            if infoVideo: liz.addStreamInfo('video', infoVideo)
            if infoAudio: liz.addStreamInfo('audio', infoAudio)
        else: liz = listitem
        liz.setProperty('IsPlayable','true')
        self.listitems.append(liz)
    
    
    def addLink(self, name, uri=(''), infoList={}, infoArt={}, infoVideo={}, infoAudio={}, infoType='video', listitem=None, total=0):
        log('addLink, name = %s'%name)
        if listitem is None: 
            liz = xbmcgui.ListItem(name)
            if infoList:  liz.setInfo(type=infoType, infoLabels=infoList)
            else:         liz.setInfo(type=infoType, infoLabels={"mediatype":infoType,"label":name,"title":name})
            if infoArt:   liz.setArt(infoArt)
            else:         liz.setArt({'thumb':ICON,'fanart':FANART})
            if infoVideo: liz.addStreamInfo('video', infoVideo)
            if infoAudio: liz.addStreamInfo('audio', infoAudio)
            if infoList.get('favorite',None) is not None: liz = self.addContextMenu(liz, infoList)
        else: liz = listitem
        liz.setProperty('IsPlayable','true')
        xbmcplugin.addDirectoryItem(ROUTER.handle, ROUTER.url_for(*uri), liz, isFolder=False, totalItems=total)
                

    def addDir(self, name, uri=(''), infoList={}, infoArt={}, infoType='video', listitem=None):
        log('addDir, name = %s'%name)
        if listitem is None: 
            liz = xbmcgui.ListItem(name)
            if infoList: liz.setInfo(type=infoType, infoLabels=infoList)
            else:        liz.setInfo(type=infoType, infoLabels={"mediatype":infoType,"label":name,"title":name})
            if infoArt:  liz.setArt(infoArt)
            else:        liz.setArt({'thumb':ICON,'fanart':FANART})
            if infoList.get('favorite',None) is not None: liz = self.addContextMenu(liz, infoList)
        else: liz = listitem
        liz.setProperty('IsPlayable','false')
        xbmcplugin.addDirectoryItem(ROUTER.handle, ROUTER.url_for(*uri), liz, isFolder=True)
        
        
    def addContextMenu(self, liz, infoList={}):
        log('addContextMenu')
        return liz
         
         
    def poolList(self, method, items=None, args=None, chunk=25):
        log("poolList")
        results = []
        if SUPPORTS_POOL:
            pool = ThreadPool()
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


    def run(self):  
        ROUTER.run()
        xbmcplugin.setContent(ROUTER.handle     ,CONTENT_TYPE)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(ROUTER.handle ,cacheToDisc=DISC_CACHE)