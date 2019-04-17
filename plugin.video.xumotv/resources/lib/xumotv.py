#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Xumo.TV.
#
# Xumo.TV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Xumo.TV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Xumo.TV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback, calendar
import urlparse, urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.xumotv'
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
PTVL_RUN      = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
BASE_URL      = 'http://www.xumo.tv'
BASE_API      = 'https://valencia-app-mds.xumo.com/v2/%s'
BASE_LOGO     = 'https://image.xumo.com/v1/channels/channel/%s/512x512.png?type=color_onBlack'
BASE_ICON     = 'https://image.xumo.com/v1/providers/provider/%s/512x512.png?type=smartCast_channelTile'
BASE_FANART   = 'https://image.xumo.com/v1/channels/channel/%s/248x140.png?type=channelTile'
BASE_THUMB    = 'https://image.xumo.com/v1/assets/asset/%s/600x340.jpg'

MAIN_MENU     = [(LANGUAGE(30003), '0', 1),
                 (LANGUAGE(30004), '' , 2),
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
    
socket.setdefaulttimeout(TIMEOUT)  
class XumoTV(object):
    def __init__(self, sysARG):
        log('__init__, sysARG = ' + str(sysARG))
        self.sysARG = sysARG
        self.cache  = SimpleCache()
        self.geoID, self.geoLST  = self.getID()
        
           
    def openURL(self, url):
        try:
            log('openURL, url = ' + str(url))
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                cacheresponse = urllib2.urlopen(request, timeout=TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, cacheresponse, expiration=datetime.timedelta(minutes=5))
            return cacheresponse
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
         
    def getID(self):
        log('getID')
        results = json.loads(re.findall('__JOBS_REHYDRATE_STATE__=(.+?);</script>',(self.openURL(BASE_URL)), flags=re.DOTALL)[0])
        return results["jobs"]["1"]["data"]["geoId"], results["jobs"]["1"]["data"]["channelListId"]
        
        
    def getChannels(self):
        log('getChannels')
        '''{u'description': u'Dedicated to providing the best in journalism under standards it pioneered at the dawn of radio and television and continue in the digital age.', u'title': u'CBS News', u'number': 125, u'callsign': u'XCBSNWS', u'genre': [{u'genreId': 13, u'value': u'News'}], u'guid': {u'isPermaLink': False, u'value': u'9999158'}, u'properties': {u'has_vod': u'false', u'hybrid_type': u'promoted', u'brand_color': u'rgba(48,129,180,1)', u'is_simulcast': u'true', u'is_live': u'true', u'has_discontinuity': u'true'}}'''
        return json.loads(self.openURL(BASE_API%'channels/list/%s.json?sort=hybrid&geoId=%s'%(self.geoLST, self.geoID)))['channel']['item']
       
             
    def getChannelsByGenre(self, genre):
        log('getChannelsByGenre')
        return json.loads(self.openURL(BASE_API%'channels/list/%s.json?q=genreid:%s'%(self.geoLST, genre)))['channel']['item']
            
            
    def getChannelCategories(self, channelID):
        log('getChannelCategories')
        return json.loads(self.openURL(BASE_API%'channels/channel/%s/categories.json'%(channelID)))['categories']
        

    def getCategories(self, CatID):
        log('getCategories')
        try: return json.loads(self.openURL(BASE_API%'categories/category/%s.json?f=asset.title&f=asset.episodeTitle&f=asset.providers&f=asset.runtime&f=asset.availableSince'%(CatID)))
        except: return {}
        
        
    def getGenres(self):
        log('getGenres')
        '''{u'genreId': 195, u'value': u'TV & Movies'}'''
        return json.loads(self.openURL(BASE_API%'channels/list/%s/genres.json'%(self.geoLST)))['genres']
        
        
    def getOnNEXT(self, limit='3'):
        log('getOnNEXT')
        '''{u'end': 1536689700000L, u'title': u'Highlights', u'channelId': 9999301, u'start': 1536688800000L, u'descriptions': {u'small': u"Watch the world's best golfers in action with Highlights from the latest on the PGA TOUR."}, u'contentType': u'COMPOSITE', u'type': u'Asset', u'id': u'XM0FQO65KVUAYO'}'''
        return json.loads(self.openURL(BASE_API%'channels/list/%s/onnowandnext.json?f=asset.title&f=asset.descriptions&limit=%s'%(self.geoLST,limit)))['results']

        
    def getOnNow(self, channelID):
        log('getOnNow')
        '''{u'timestamps': {u'start': 946684800, u'end': 2145916800}, u'live': True, u'type': u'Asset', u'id': u'XM0IFYLJ0RMD0X'}'''
        try: return json.loads(self.openURL(BASE_API%'channels/channel/%s/onnow.json?f=title&f=descriptions#descriptions'%(channelID)))
        except: return {}
        
       
    def getLineup(self, channelID, hour='22'):
        log('getLineup')
        '''{u'timestamps': {u'start': 946684800, u'end': 2145916800}, u'live': True, u'type': u'Asset', u'id': u'XM0IFYLJ0RMD0X'}'''
        return json.loads(self.openURL(BASE_API%'channels/channel/%s/broadcast.json?hour=%s'%(channelID,hour)))['assets']
        
        
    @use_cache(28)
    def getMeta(self, contentID):
        '''{u'contentType': u'SIMULCAST', u'providers': [{u'title': u'CBSN', u'color': u'rgba(48,129,180,1)', u'sources': [{u'lang': u'en', u'produces': u'application/x-mpegURL', u'uri': u'https://dai.google.com/linear/hls/event/Sid4xiTQTkCT1SLu6rjUSQ/master.m3u8?iu=/8264/vaw-can/ott/cbsnews_xumo', u'height': 720, u'width': 1280, u'bitrate': 3009}], u'sunset': u'Tue, 19 Jan 2038 03:14:07 +0000', u'id': 42, u'sunrise': u'Thu, 1 Jan 1970 00:00:01 +0000'}], u'title': u'CBS News', u'descriptions': {u'medium': u"CBSN offers original, up-to-the-minute coverage of national and global stories with dynamic on-demand video content, including video from CBS News' extensive archives."}, u'availableSince': u'Tue, 20 Dec 2016 23:25:37 +0000', u'type': u'Asset', u'id': u'XM0IFYLJ0RMD0X'}'''
        return json.loads(self.openURL(BASE_API%'assets/asset/%s.json?f=title&f=providers&f=descriptions&f=runtime&f=availableSince'%(contentID)))
        
        
    def getDuration(self, start, end):
        dt1 = datetime.datetime.utcfromtimestamp(float(start)/1000)
        dt2 = datetime.datetime.utcfromtimestamp(float(end)/1000)
        return int((dt2-dt1).total_seconds())
        
        
    def getDescription(self, description):
        if   'large'  in description: return description['large']
        elif 'medium' in description: return description['medium']
        elif 'small'  in description: return description['small']
        elif 'tiny'   in description: return description['tiny']
        else: return ''

        
    def pagination(self, seq, rowlen):
        for start in xrange(0, len(seq), rowlen): yield seq[start:start+rowlen]

        
    def buildChannels(self, start=None, opt=None, end=14):
        log('buildChannels, start = ' + str(start) + ', opt = ' + str(opt))
        items = sorted(list(self.getChannels()), key=lambda item: item['number'])
        if start is not None:
            items = list(self.pagination(items, end))
            start = 0 if start >= len(items) else start
            items = items[start]
        for item in items:
            chid   = item['guid']['value']
            chnum  = item['number']
            chnam  = item['title']
            chlog  = BASE_LOGO%(chid)
            fanart = BASE_FANART%(chid)
            try: genre = item['genre']['value']
            except: genre = ''
            if opt == 'now':
                label, url, liz = self.buildAsset(self.getOnNow(chid)['id'], chid, chnam, chnum)
                self.addLink(label, url, 9, liz)
            else: 
                label = '%s: %s'%(chnum,chnam)
                plot  = (item.get('descriptions','') or label)
                infoLabels = {"mediatype":"episode","label":label ,"title":label,"plot":plot,"genre":genre}
                infoArt = ({'thumb':chlog,'fanart':fanart,'clearlogo':chlog})
                self.addDir(label, chid, 2, infoLabels, infoArt)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        if start is not None and opt == 'now': 
            start += 1
            self.addDir('>> Next', '%s'%(start), 1)

                
    def buildOnDemand(self, name, channelId=None):
        log('buildOnDemand, channelId = ' + str(channelId))
        if channelId is None:
            return self.buildChannels()
        else:
            items = sorted(list(self.getLineup(channelId)), key=lambda item: item['timestamps']['start'], reverse=False)
            for item in items:
                label, url, liz = self.buildAsset(item['id'], channelId)
                self.addLink(label, url, 9, liz)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        
    
    def buildMenu(self, items):
        for item in items: self.addDir(*item)
        
  
    def buildAsset(self, chid, channelId, channelName=None, channelNumber=None):
        log('buildAsset, chID = ' + chid)
        meta  = self.getMeta(chid)
        mType = ''
        url   = channelId
        label = meta['title']
        thumb = BASE_THUMB%(chid)
        if channelName is not None: 
            thumb = BASE_LOGO%(channelId)
            label = '%s - %s'%(channelName,label)
        if channelNumber is not None: 
            label = '%s: %s'%(channelNumber,label)
        try: 
            # if channelName is None: label = '%s - %s'%(meta['providers'][0]['title'],label)
            url   = meta['providers'][0]['sources'][0]['uri']
            mType = (meta.get('produces','') or meta['providers'][0]['sources'][0]['produces'])
        except: pass
        plot  = (self.getDescription(meta.get('descriptions',{})) or label)
        try: aired = datetime.datetime.strptime(meta['availableSince'],'%a, %d %b %Y %H:%M:%S %z')
        except: aired = datetime.datetime.now()
        duration = 0
        if channelName is None: duration = meta.get('runtime',0)
        liz  = xbmcgui.ListItem(label, path=url)
        liz.setProperty("IsPlayable","true")
        liz.setProperty("IsInternetStream","true")
        liz.setProperty('inputstreamaddon','inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.manifest_type','hls')
        liz.setMimeType(mType)
        liz.setSubtitles( [sub['url'] for sub in meta.get('captions',[]) if sub['type'] == 'text/srt'])
        liz.setInfo(type="Video", infoLabels={"mediatype":"episode","label":label ,"title":label,"plot":plot,"duration":duration,"aired":aired.strftime('%Y-%m-%d')})
        liz.setArt({'thumb':thumb,'fanart':BASE_FANART%(channelId),'clearlogo':BASE_LOGO%(channelId)})
        return label, url, liz
  
  
    def playVideo(self, name, url):
        if 'm3u8' not in url.lower(): return self.playAsset(name, url)
        log('playVideo, url = ' + url)
        liz  = xbmcgui.ListItem(name, path=url)
        liz.setProperty("IsPlayable","true")
        liz.setProperty("IsInternetStream","true")
        liz.setProperty('inputstreamaddon','inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.manifest_type','hls')
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)
        
        
    def playAsset(self, name, url):
        log('playAsset, url = ' + url)
        if url[0].isdigit(): return self.playChannel(name, url)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        xbmc.sleep(100)
        items = self.getChannelCategories(url)
        for idx, item in enumerate(items):
            label, url, liz = self.buildAsset(item['id'], url)
            playlist.add(url, liz, idx)
            if idx == 0: xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        
        
    def playChannel(self, name, channelId):
        log('playChannel, channelId = ' + channelId)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        xbmc.sleep(100)
        items = self.getCategories(self.getOnNow(channelId)['categoryId'])['results']
        for idx, item in enumerate(items):
            label, url, liz = self.buildAsset(item['id'], channelId)
            playlist.add(url, liz, idx)
            if idx == 0: xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

            
    def uEPG(self):
        log('uEPG')
        #support for uEPG universal epg framework module. https://github.com/Lunatixz/KODI_Addons/tree/master/script.module.uepg
        stations = sorted(list(self.getChannels()), key=lambda item: item['number'])
        listings = sorted(self.getOnNEXT(), key=lambda item: item['start'], reverse=False)
        return [self.buildGuide((station, listings)) for station in stations]
        
        
    def buildGuide(self, item):
        log('buildGuide')
        station, listings = tuple(item)
        chname     = station['title']
        chnum      = station['number']
        chid       = station['guid']['value']
        genre      = station['genre'][0]['value']
        chlogo     = BASE_LOGO%(chid)
        newChannel = {}
        guidedata  = []
        newChannel['channelname']   = chname
        newChannel['channelnumber'] = chnum
        newChannel['channellogo']   = chlogo
        newChannel['isfavorite']    = False
        endTime    = datetime.datetime.now()
        for listing in listings:
            if listing['channelId'] != int(chid): continue
            cid         = listing['id']
            meta        = self.getMeta(cid)
            label       = meta['title']
            plot        = (self.getDescription(meta.get('descriptions',{})) or label)
            try: aired  = datetime.datetime.strptime(meta['availableSince'],'%a, %d %b %Y %H:%M:%S %z')
            except: aired = datetime.datetime.now()
            duration    = meta.get('runtime',5200)
            startTime   = endTime
            endTime     = startTime + datetime.timedelta(seconds=duration)
            try: url    = meta['providers'][0]['sources'][0]['uri']
            except: url = chid
            tmpdata = {"mediatype":"episode","label":label ,"title":label,"plot":plot,"duration":duration,"aired":aired.strftime('%Y-%m-%d'),'genre':genre}
            tmpdata['starttime'] = int(time.mktime((startTime).timetuple()))
            tmpdata['url'] = self.sysARG[0]+'?mode=9&name=%s&url=%s'%(urllib.quote_plus(uni(chname)),url)
            tmpdata['art'] = {'thumb':BASE_THUMB%(cid),'fanart':BASE_FANART%(chid),'clearlogo':BASE_LOGO%(chid)}
            guidedata.append(tmpdata)
        newChannel['guidedata'] = guidedata
        return newChannel

        
    def addLink(self, name, u, mode, liz, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
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

        if mode==None:  self.buildMenu(MAIN_MENU)
        elif mode == 1: self.buildChannels(int(url), opt='now')
        elif mode == 2: self.buildOnDemand(name, url)
        elif mode == 9: self.playVideo(name, url)
        elif mode == 20:xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%(urllib.quote(json.dumps(list(self.uEPG()))),urllib.quote(json.dumps(self.sysARG[0]+"?mode=20")),urllib.quote(json.dumps("3600")),urllib.quote(json.dumps("7"))))


        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=True)