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
import os, sys, datetime, re, traceback, HTMLParser, calendar
import urlparse, urllib, urllib2, socket, json, collections, random
import xbmc, xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon

from simplecache import SimpleCache, use_cache
from pyhdhr import PyHDHR

# Plugin Info
ADDON_ID      = 'plugin.video.hdhomerun.simple'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT      = 30
CONTENT_TYPE = 'episodes'
DEBUG        = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
PTVL_RUNNING = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
TRANSCODE    = REAL_SETTINGS.getSetting('Preferred_Transcoding').lower().replace('default','none')
MTYPES       = {'EP':'episode','SH':'episode','MV':'movie'}
HDHR_MENU    = [(LANGUAGE(30110), '{0}', 1),
                (LANGUAGE(30111), ''   , 2),
                (LANGUAGE(30112), '{0}', 4),
                (LANGUAGE(30113), '{0}', 11),
                (LANGUAGE(30114), '{0}', 20)]
                
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)

def collectData(mydict, key):
    items = []
    for item in mydict: items.append(item[key])
    counter = collections.Counter(items)
    return counter.most_common()
    
def getIndex(items, key, value):
    for item in items: 
        if item[key] == value: yield item

socket.setdefaulttimeout(TIMEOUT)
class HDHR(object):
    def __init__(self, sysARG):
        log('__init__, sysARG = ' + str(sysARG))
        self.cacheToDisc = True
        self.sysARG      = sysARG
        self.cache       = SimpleCache()
        self.pyHDHR      = PyHDHR.PyHDHR()
        self.tuners      = self.getTuners()
        self.hasDVR      = self.pyHDHR.hasSDDVR()
        
        
    def browseTuners(self):
        # if PTVL_RUNNING or len(self.tuners) == 1: self.browseTunerMenu('All')
        # else:
        for tunerkey in self.tuners: 
            if len(self.tuners) == 1: return self.browseTunerMenu(self.tuners[tunerkey].getLocalIP())
            self.addDir('%s - %s'%(self.tuners[tunerkey].FriendlyName,tunerkey), self.tuners[tunerkey].getLocalIP(), 0)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
                
            
    def browseTunerMenu(self, tunerkey):
        for idx, tup in enumerate(HDHR_MENU):
            if tup[0] == LANGUAGE(30111) and not self.hasDVR: continue
            self.addDir(tup[0], tup[1].format(tunerkey), tup[2])
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        
           
    def browseLive(self, tunerkey):
        self.setDevice(tunerkey)
        progs  = self.pyHDHR.getWhatsOn()
        self.cacheToDisc = False
        for channel in progs:
            try:
                label, liz = self.buildChannelListItem(channel, progs[channel])
                self.addLink(label, json.dumps({"tunerkey":tunerkey,"channel":channel}), 9, liz, len(progs))
            except: pass
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
            
            
    def browseGuide(self, mydata):
        try:
            mydata   = json.loads(mydata)
            chnum    = mydata['chnum']
            tunerkey = mydata['tunerkey']
        except:
            chnum    = None
            tunerkey = mydata
        self.setDevice(tunerkey)
        for channel in self.getChannelList():
            if chnum is not None and chnum != str(channel): continue
            chan        = self.getChannelInfo(channel)
            channelname = (chan.getAffiliate() or chan.getGuideName() or chan.getGuideNumber() or 'N/A')
            isFavorite  = chan.getFavorite() == 1
            isHD        = chan.getHD() == 1
            hasCC       = True
            chlogo      = (chan.getImageURL() or ICON)
            if chnum is None:
                try:
                    label, liz = self.buildChannelListItem(channel, None, '%s: %s'%(channel,channelname))
                    self.addDir(label,json.dumps({"tunerkey":tunerkey,"chnum":str(channel)}),4,liz)
                except: pass
            else:
                programs = chan.getProgramInfos()
                for program in programs:
                    if chnum != str(channel): continue
                    try:
                        label, liz = self.buildChannelListItem(chnum, program, opt='Lineup')
                        self.addLink(label, json.dumps({"tunerkey":tunerkey,"channel":chnum}), 9, liz, len(programs))
                    except: pass
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)

                    
    def browseRecordings(self):
        log('browseRecordings')
        progs = self.pyHDHR.getFilteredRecordedPrograms()
        if not progs: return
        collect = []
        for prog in progs:
            collect.append({'name':prog.getTitle(),'prog':prog})
        for show in collectData(collect, 'name'):
            prog       = list(getIndex(collect, 'name', show[0]))[0]['prog']
            title      = prog.getTitle()
            eptitle    = prog.getEpisodeTitle()
            starttime  = (datetime.datetime.fromtimestamp(float(prog.getStartTime())))
            if show[1] > 1:
                label = '%s (%d)'%(title, show[1])
                try:
                    label, liz = self.buildRecordListItem(prog, label, opt='show')
                    self.addDir(label, prog.getSeriesID(), 3, liz)
                except: pass
            else:
                if len(eptitle) > 0: label = '%s: %s - %s'%(starttime.strftime('%I:%M %p').lstrip('0'),title,eptitle)
                else: label = '%s: %s'%(starttime.strftime('%I:%M %p').lstrip('0'),title)
                try:
                    label, liz = self.buildRecordListItem(prog, label)
                    self.addLink(label, prog.getPlayURL(), 8, liz)
                except: pass
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_DATEADDED)

            
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
            self.addLink(label, prog.getPlayURL(), 8, liz)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
            
        
    def browseSearch(self):
        log('browseSearch')
        kb = xbmc.Keyboard('', LANGUAGE(30109)%ADDON_NAME)
        xbmc.sleep(1000)
        kb.doModal()
        if kb.isConfirmed():
            query = kb.getText()
            progs = (self.pyHDHR.searchWhatsOn(query))
            if progs is not None:
                for prog in progs:
                    try:
                        label, liz = self.buildChannelListItem(prog, progs[prog], opt='searchWhatsOn')
                        self.addLink(label, prog, 9, liz, len(progs))
                    except: pass

            progs = (self.pyHDHR.search(query))
            if progs is not None: 
                for prog in progs:
                    try:
                        label, liz = self.buildChannelListItem(prog, progs[prog], opt='search')
                        self.addLink(label, prog, 9, liz, len(progs))
                    except: pass
                    
            if not self.hasDVR: return
            progs = self.pyHDHR.searchRecorded(query)
            for prog in progs:
                if progs is not None: 
                    try:
                        label, liz = self.buildRecordListItem(progs[prog], opt='searchRecorded')
                        self.addLink(label, prog, 9, liz, len(progs))
                    except: pass
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        
            
    def buildRecordListItem(self, prog, label=None, opt='Live'):
        return self.buildChannelListItem(prog.getChannelNumber(), prog, label, opt)

        
    def buildChannelListItem(self, channel, item=None, label=None, opt='Live'):
        info   = self.getChannelInfo(channel)
        if info is None: return
        elif info.getDRM(): return
        chlogo = (info.getImageURL() or ICON)
        chname = (info.getAffiliate() or info.getGuideName() or info.getGuideNumber() or 'N/A')
        liz    = xbmcgui.ListItem(label)
        video  = {"codec":'mpeg2video',"width":480,"aspect":"1.33"}
        audio  = {"codec":'ac3',"bitrate":1500}
        if info is not None:
            tuner  = info.getTuner()
            if tuner.getModelNumber() == "HDTC-2US":
                if TRANSCODE == 'none': tranOPT = (tuner.getTranscodeOption() or 'none')
                else: tranOPT = TRANSCODE
                if tranOPT != "none": video = {'codec': 'h264'}
            else:
                if info.getVideoCodec() == "H264": video = {'codec':'h264'}
                if info.getAudioCodec() == "AAC":
                    if tuner.getModelNumber() == "HDHR4-2DT": audio = {'codec':'aac_latm'}
                    else: audio = {'codec': 'aac'}
                elif info.getAudioCodec() == "MPEG": audio = {'codec': 'mp2'}
            if info.getHD() == 1:
                video['width']  = 1080
                video['aspect'] = "1.78"
                if video['codec'] == 'mpeg2video' or video['codec'] == 'mpeg1video': audio['bitrate'] = 13000
                else: audio['bitrate'] = 4000
            else: 
                if video['codec'] == 'mpeg2video' or video['codec'] == 'mpeg1video': audio['bitrate'] = 4000
                else:audio['bitrate'] = 1500
        try:
            if item.getEpisodeTitle(): title = '%s - %s'%(item.getTitle(), item.getEpisodeTitle())
            else: title = (item.getTitle() or chname)
            if opt == 'searchRecorded': title = '%s (%s)'%(title,LANGUAGE(30116))
            elif opt == 'searchWhatsOn': title = '%s (%s)'%(title,LANGUAGE(30117))
            elif opt == 'search': title = '%s (%s)'%(title,LANGUAGE(30118))
            starttime  = float(item.getStartTime())
            endtime    = float(item.getEndTime())
            runtime    = int(endtime - starttime)
            airdate    = float(item.getOriginalAirdate() or starttime)
            starttime  = (datetime.datetime.fromtimestamp(starttime))
            endtime    = (datetime.datetime.fromtimestamp(endtime))
            date       = (starttime).strftime('%Y-%m-%d')
            airdate    = (datetime.datetime.fromtimestamp(airdate)).strftime('%Y-%m-%d')
            thumb      = (item.getImageURL() or chlogo)
            stime      = starttime.strftime('%I:%M %p').lstrip('0')
            if label is None: 
                if PTVL_RUNNING: label = chname 
                elif opt == 'Live': label = '%s: %s - %s'%(channel,chname,title)
                else: label = '%s: %s - %s'%(starttime.strftime('%I:%M %p').lstrip('0'),chname,title)
            label2     = '%s - %s'%(starttime.strftime('%I:%M %p').lstrip('0'),endtime.strftime('%I:%M %p').lstrip('0'))
            plot       = '' if opt == 'show' else (item.getSynopsis() or title)
            stime      = starttime.strftime('%I:%M %p').lstrip('0')
            try: mtype = MTYPES[item.getEpisodeNumber()[:2]]
            except: mtype = 'episode'
            liz.setArt({"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":chlogo,"logo":chlogo})
            liz.setInfo('video',{"mediatype":mtype,"label":label,"title":label,"label2":label2,"studio":chname,"aired":date,"plot": plot,"duration":runtime,"premiered":airdate})
        except:        
            if label is None: label = chname if PTVL_RUNNING else (label or '%s %s - %s'%(channel,chname,title))
            liz.setArt({"thumb":chlogo,"poster":chlogo,"fanart":FANART,"icon":chlogo,"logo":chlogo})
            liz.setInfo('video',{"mediatype":"episode","label":label,"title":label,"TVShowTitle":label})
        liz.addStreamInfo('video', video)
        liz.addStreamInfo('audio', audio)
        return label, liz

        
    def hasHDHR(self):
        return len((self.tuners)) > 0

        
    def setDevice(self, tunerkey):
        if tunerkey != 'All': self.pyHDHR.setManualTunerList(tunerkey)
        
    
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
        
        
    def playVideo(self, name, url):
        log('playVideo, name = ' + name + ', url = ' + url)
        liz = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)
        
        
    def playChannel(self, name, mydata):
        log('playChannel, name = ' + name + ', mydata = ' + mydata)
        mydata  = json.loads(mydata)
        channel = (mydata.get('channel','') or mydata.get('url',''))
        self.setDevice(mydata['tunerkey'])
        info = self.pyHDHR.getLiveTVChannelInfo(channel)
        url   = info.getURL()
        tuner = info.getTuner()
        if tuner.getModelNumber() == "HDTC-2US":
            if TRANSCODE == 'none': tranOPT = (tuner.getTranscodeOption() or 'none')
            else: tranOPT = TRANSCODE
            log("playChannel, Tuner transcode option: " + tranOPT)
            if tranOPT != "none": video = {'codec': 'h264'}
            url = url + "?transcode="+tranOPT
        liz = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)

        
    def addLink(self, name, u, mode, liz=None, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        if liz is None: 
            liz = xbmcgui.ListItem(name)
            liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
            liz.setArt({'thumb':ICON,'fanart':FANART})
        liz.setProperty('IsPlayable', 'true')
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, liz=None):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        if liz is None: 
            liz = xbmcgui.ListItem(name)
            liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
            liz.setArt({'thumb':ICON,'fanart':FANART})
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

        if mode==None:  self.browseTuners()
        elif mode == 0: self.browseTunerMenu(url)
        elif mode == 1: self.browseLive(url)
        elif mode == 2: self.browseRecordings()
        elif mode == 3: self.browseSeries(url)
        elif mode == 4: self.browseGuide(url)
        elif mode == 8: self.playVideo(name, url)
        elif mode == 9: self.playChannel(name, url)
        elif mode == 11: self.browseSearch()
        elif mode == 20:xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%("[]",urllib.quote(self.sysARG[0]+"?mode=20"),"7200","5"))

        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=self.cacheToDisc)