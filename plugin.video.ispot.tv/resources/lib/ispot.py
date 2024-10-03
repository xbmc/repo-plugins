#   Copyright (C) 2024 Lunatixz
#
#
# This file is part of iSpot.tv.
#
# iSpot.tv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iSpot.tv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iSpot.tv.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

import os, re, sys, routing, traceback, datetime
import json, requests, base64, time

from six.moves           import urllib
from youtube_dl          import YoutubeDL
from bs4                 import BeautifulSoup
from simplecache         import SimpleCache, use_cache
from kodi_six            import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode
from infotagger.listitem import ListItemInfoTag

try:
    from multiprocessing.pool import ThreadPool
    SUPPORTS_POOL = True
except Exception:
    SUPPORTS_POOL = False
    
# Plugin Info
ADDON_ID         = 'plugin.video.ispot.tv'
REAL_SETTINGS    = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME       = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC     = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH       = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION    = REAL_SETTINGS.getAddonInfo('version')
ICON             = REAL_SETTINGS.getAddonInfo('icon')
LOGO             = os.path.join('special://home/addons/%s/'%(ADDON_ID),'resources','images','logo.png')
FANART           = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE         = REAL_SETTINGS.getLocalizedString
ROUTER           = routing.Plugin()
CONTENT_TYPE     = 'episodes'
DISC_CACHE       = False
DEBUG_ENABLED    = REAL_SETTINGS.getSetting('Enable_Debugging').lower() == 'true'
ENABLE_DOWNLOAD  = REAL_SETTINGS.getSetting('Enable_Download').lower() == 'true'
ENABLE_SAP       = REAL_SETTINGS.getSetting('Enable_SAP').lower() == 'true'
DOWNLOAD_PATH    = os.path.join(REAL_SETTINGS.getSetting('Download_Folder'),'resources','').replace('/resources/resources','/resources').replace('\\','/')
DEFAULT_ENCODING = "utf-8"
HEADER           = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
BASE_URL         = 'https://www.ispot.tv'

MENU = {LANGUAGE(30015) : "/browse/k/apparel-footwear-and-accessories",
        LANGUAGE(30016) : "/browse/Y/business-and-legal",
        LANGUAGE(30017) : "/browse/7/education",
        LANGUAGE(30018) : "/browse/A/electronics-and-communication",
        LANGUAGE(30019) : "/browse/d/food-and-beverage",
        LANGUAGE(30020) : "/browse/I/health-and-beauty",
        LANGUAGE(30021) : "/browse/o/home-and-real-estate",
        LANGUAGE(30022) : "/browse/Z/insurance",
        LANGUAGE(30023) : "/browse/w/life-and-entertainment",
        LANGUAGE(30024) : "/browse/7k/pharmaceutical-and-medical",
        LANGUAGE(30025) : "/browse/q/politics-government-and-organizations",
        LANGUAGE(30026) : "/browse/b/restaurants",
        LANGUAGE(30027) : "/browse/2/retail-stores",
        LANGUAGE(30028) : "/browse/5/travel",
        LANGUAGE(30029) : "/browse/L/vehicles"}

#https://www.ispot.tv/events
def log(msg, level=xbmc.LOGDEBUG):
    if not DEBUG_ENABLED and level != xbmc.LOGERROR: return
    try:   xbmc.log('%s-%s-%s'%(ADDON_ID,ADDON_VERSION,msg),level)
    except Exception as e: 'log failed! %s'%(e)
    
def chunkLst(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
 
def slugify(s, lowercase=False):
  if lowercase: s = s.lower()
  s = s.strip()
  s = re.sub(r'[^\w\s-]', '', s)
  s = re.sub(r'[\s_-]+', '_', s)
  s = re.sub(r'^-+|-+$', '', s)
  return s
        
def unquoteString(text):
    return urllib.parse.unquote(text)
    
def quoteString(text):
    return urllib.parse.quote(text)

def encodeString(text):
    base64_bytes = base64.b64encode(text.encode(DEFAULT_ENCODING))
    return base64_bytes.decode(DEFAULT_ENCODING)

def decodeString(base64_bytes):
    try:
        message_bytes = base64.b64decode(base64_bytes.encode(DEFAULT_ENCODING))
        return message_bytes.decode(DEFAULT_ENCODING)
    except: pass

def poolit(func, items):
    results = []
    if SUPPORTS_POOL:
        pool = ThreadPool()
        try: results = pool.map(func, items)
        except Exception: pass
        pool.close()
        pool.join()
    else:
        results = [func(item) for item in items]
    results = filter(None, results)
    return results

@ROUTER.route('/')
def buildMenu():
    iSpotTV().buildMenu()

@ROUTER.route('/downloads')
def getDownloaded():
    iSpotTV().buildDownloaded()
    
@ROUTER.route('/browse/<url>')
def getCategory(url):
    iSpotTV().buildCategory(decodeString(url))
    
@ROUTER.route('/play/<meta>')
def playVideo(meta):
    iSpotTV().playVideo(meta.split('|')[0],decodeString(meta.split('|')[1]))
    
class iSpotTV(object):
    def __init__(self, sysARG=sys.argv):
        log('__init__, sysARG = %s'%(sysARG))
        self.sysARG    = sysARG
        self.cache     = SimpleCache()
        self.myMonitor = xbmc.Monitor()
        
        
    @use_cache(1)
    def getURL(self, url):
        log('getURL, url = %s'%(url))
        try:    return requests.get(url, headers=HEADER).content
        except Exception as e: log('getURL Failed! %s'%(e))
    
    
    def getSoup(self, url):
        log('getSoup, url = %s'%(url))
        return BeautifulSoup(self.getURL(url), 'html.parser')
        

    def buildMenu(self):
        log('buildMenu')
        if ENABLE_DOWNLOAD: self.addDir('- %s'%(LANGUAGE(30011)),uri=(getDownloaded,))
        for name, url in list(MENU.items()): self.addDir(name,uri=(getCategory,encodeString(url)))


    def buildDownloaded(self):
        def _buildFile(item):
            try: self.addLink(item.get('label'),(playVideo,'%s|%s'%(item.get('label'),encodeString(item.get('file')))),info={'label':item.get('label'),'label2':os.path.join(DOWNLOAD_PATH,item.get('label')),'title':item.get('title')},art={"thumb":ICON,"poster":ICON,"fanart":FANART,"icon":LOGO,"logo":LOGO})
            except: pass
        poolit(_buildFile,self.getDirectory(DOWNLOAD_PATH))


    def buildCategory(self, url):
        """ < div
        class ="mb-0" >
        < a adname = "FootJoy Pro/SLX TV Spot, 'Joy Ride' Featuring Max Homa, Danielle Kang, Song by 10cc - 16 airings" href = "/ad/6K6T/footjoy-pro-slx-joy-ride" >
        < img alt = "FootJoy Pro/SLX TV Spot, 'Joy Ride' Featuring Max Homa, Danielle Kang, Song by 10cc" class ="img-16x9" loading="lazy" src="https://images-cdn.ispot.tv/ad/6K6T/default-large.jpg" width="100%" / >< / a >
        < / div >"""
        def _buildDir(sub):
            try:
                if not sub.a['href'].startswith(('/brands/','/products/')):
                    self.addDir('- %s'%(sub.string),uri=(getCategory,encodeString(sub.a['href'])))
            except: pass
            
        def _buildFile(row):
            try:
                label, label2 = row.a['adname'].split(' - ')
                if label.lower().endswith('[spanish]') and not ENABLE_SAP: return
                uris.append(row.a['href'])
                self.addLink(label,(playVideo,'%s|%s'%(row.a['adname'],encodeString(row.a['href']))),info={'label':label,'label2':label2,'title':label},art={"thumb":row.img['src'],"poster":row.img['src'],"fanart":FANART,"icon":LOGO,"logo":LOGO})
            except: pass
        
        try:
            uris = []
            log('buildCategory, url = %s'%(url))
            soup = self.getSoup('%s%s'%(BASE_URL,url))
            poolit(_buildDir,soup.find_all('div', {'class': 'list-grid__item'}))
            poolit(_buildFile,soup.find_all('div', {'class': 'mb-0'}))
            if ENABLE_DOWNLOAD: self.queDownload(uris)
        except Exception as e: log('buildCategory Failed! %s'%(e))


    def addLink(self, name, uri=(''), info={}, art={}, media='video', total=0):
        log('addLink, name = %s'%name)
        if not info: info = {"label":name,"label2":"","title":name}
        if not art:   art = {"thumb":ICON,"poster":ICON,"fanart":FANART,"icon":LOGO,"logo":LOGO}
        info["mediatype"] = media
        liz = self.getListItem(info.pop('label'), info.pop('label2'), ROUTER.url_for(*uri))
        liz.setArt(art)
        liz.setProperty('IsPlayable','true')
        infoTag = ListItemInfoTag(liz, media) 
        infoTag.set_info(info)
        xbmcplugin.addDirectoryItem(ROUTER.handle, ROUTER.url_for(*uri), liz, isFolder=False, totalItems=total)
        

    def addDir(self, name, uri=(''), info={}, art={}, media='video'):
        log('addDir, name = %s'%name)
        if not info: info = {"label":name,"label2":"","title":name}
        if not art:   art = {"thumb":ICON,"poster":ICON,"fanart":FANART,"icon":LOGO,"logo":LOGO}
        info["mediatype"] = media
        liz = self.getListItem(info.pop('label'), info.pop('label2'), ROUTER.url_for(*uri))
        liz.setArt(art)
        liz.setProperty('IsPlayable','false')
        infoTag = ListItemInfoTag(liz, media)
        infoTag.set_info(info)
        xbmcplugin.addDirectoryItem(ROUTER.handle, ROUTER.url_for(*uri), liz, isFolder=True)
        
        
    def getListItem(self, label='', label2='', path='', offscreen=False):
        return xbmcgui.ListItem(label,label2,path,offscreen)
        
        
    @use_cache(1)
    def getVideo(self, url):
          # {'id': '5Gwt-video-sm', 'title': '5Gwt-video-sm', 'timestamp': 1697567715.0, 'direct': True, 
          # 'formats': [{'format_id': 'mp4', 'url': 'https://videos-cdn.ispot.tv/ad/d0c1/5Gwt-video-sm.mp4',
          # 'vcodec': None, 'ext': 'mp4', 'format': 'mp4 - unknown', 'protocol': 'https', 
          # 'http_headers':{}}], 'extractor': 'generic', 'webpage_url': 'https://videos-cdn.ispot.tv/ad/d0c1/5Gwt-video-sm.mp4', 
          # 'webpage_url_basename': '5Gwt-video-sm.mp4', 'extractor_key': 'Generic', 'playlist': None, 'playlist_index': None, 
          # 'display_id': '5Gwt-video-sm', 'upload_date': '20231017', 'requested_subtitles': None, 'format_id': 'mp4', 
          # 'url': 'https://videos-cdn.ispot.tv/ad/d0c1/5Gwt-video-sm.mp4', 'vcodec': None, 'ext': 'mp4', 'format': 'mp4 - unknown', 
          # 'protocol': 'https', 'http_headers': {}}
        log('getVideo, url = %s'%url)
        ydl = YoutubeDL({'no_color': True, 'format': 'best', 'outtmpl': '%(id)s.%(ext)s', 'no-mtime': True, 'add-header': HEADER})
        with ydl:
            result = ydl.extract_info(url, download=False)
            if 'entries' in result: return result['entries'][0] #playlist
            else:                   return result

        
    def playVideo(self, name, uri):
        file   = uri
        exists = True
        found  = True
        if uri.startswith('/'):
            file, exists = self.getFile(uri,que=True)
            if not exists:
                video = self.getVideo('%s%s'%(BASE_URL,uri))
                if video: file = video['url'].replace('https://','http://')
                else: found = False
        log('playVideo, file = %s, found = %s'%(file,found))
        xbmcplugin.setResolvedUrl(ROUTER.handle, found, self.getListItem(name, path=file))
        
        
    def getFile(self, uri, que=False):
        file   = xbmcvfs.translatePath(os.path.join(DOWNLOAD_PATH,'%s.mp4'%(slugify(uri)))).replace('\\','/')
        exists = xbmcvfs.exists(file)
        if que and not exists and ENABLE_DOWNLOAD: self.queDownload([uri])
        log('getFile, uri = %s, file = %s'%(uri,file))
        return file, exists
    

    def getDirectory(self, path):
        items = list()
        chks  = list()
        dirs  = [path]
        for idx, dir in enumerate(dirs):
            if self.myMonitor.waitForAbort(0.001): break
            else:
                log('getDirectory, walking %s/%s directory'%(idx,len(dirs)))
                if len(dirs) > 0: dir = dirs.pop(dirs.index(dir))
                if dir in chks: continue
                else: chks.append(dir)
                for item in json.loads(xbmc.executeJSONRPC(json.dumps({"jsonrpc":"2.0","id":ADDON_ID,"method":"Files.GetDirectory","params":{"directory":dir,"media":"files"}}))).get('result', {}).get('files',[]):
                    if self.myMonitor.waitForAbort(0.001): break
                    if item.get('filetype') == 'directory': dirs.append(item.get('file'))
                    else: items.append(item)
        log('getDirectory, returning %s items'%(len(items)))
        return items
        
        
    def queDownload(self, uris):
        log('queDownload, uris = %s'%(len(uris)))
        queuePool = (self.cache.get('queuePool', json_data=True) or {})
        queuePool.setdefault('uri',[]).extend(uris)
        if len(queuePool['uri']) > 0: queuePool['uri'] = list(set(queuePool['uri']))
        self.cache.set('queuePool', queuePool, json_data=True, expiration=datetime.timedelta(days=28))
        

    def queDownloads(self):
        if ENABLE_DOWNLOAD: [self.addDir(name,uri=(getCategory,encodeString(url))) for name, url in list(MENU.items())]
    
    
    def getDownloads(self):
        if ENABLE_DOWNLOAD:
            if not xbmcvfs.exists(DOWNLOAD_PATH): xbmcvfs.mkdir(DOWNLOAD_PATH)
            queuePool = (self.cache.get('queuePool', json_data=True) or {})
            uris      = queuePool.get('uri',[])
            dia       = self.progressBGDialog(message=LANGUAGE(30014))
            dluris    = (list(chunkLst(uris,5)) or [[]])[0]
            
            for idx, uri in enumerate(dluris):
                video = None
                diact = int(idx*100//len(dluris))
                dia   = self.progressBGDialog(diact, dia, message=LANGUAGE(30013)%(diact))
                dest, exists = self.getFile(uri)
                if not exists:
                    try:
                        video = self.getVideo('%s%s'%(BASE_URL,uri))
                        if video:
                            log('getDownloads, url = %s, dest = %s'%(video['url'],dest))
                            req = urllib.request.Request(video['url'], headers=HEADER)
                            response = urllib.request.urlopen(req)
                            with xbmcvfs.File(dest,'wb') as fle:
                                fle.write(response.read())
                            if self.myMonitor.waitForAbort(5): break #avoid DDoS 
                        uris.pop(uris.index(uri))
                    except Exception as e: log('getDownloads Failed! %s\nurl = %s\nvideo = %s'%(e,'%s%s'%(BASE_URL,uri),video))
            self.progressBGDialog(100, dia, message=LANGUAGE(30012))
            queuePool['uri'] = uris
            log('getDownloads, remaining urls = %s'%(len(uris)))
            self.cache.set('queuePool', queuePool, json_data=True, expiration=datetime.timedelta(days=28))
        
        
    def progressBGDialog(self, percent=0, control=None, message='', header=ADDON_NAME, silent=None, wait=None):
        if control is None and int(percent) == 0:
            control = xbmcgui.DialogProgressBG()
            control.create(header, message)
        elif control:
            if int(percent) == 100 or control.isFinished(): 
                if hasattr(control, 'close'):
                    control.close()
                    return None
            elif hasattr(control, 'update'):  control.update(int(percent), header, message)
            if wait: self.myMonitor.waitForAbort(wait/1000)
        return control
        
        
    def run(self): 
        ROUTER.run()
        xbmcplugin.setContent(ROUTER.handle     ,CONTENT_TYPE)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(ROUTER.handle  ,xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(ROUTER.handle ,cacheToDisc=DISC_CACHE)