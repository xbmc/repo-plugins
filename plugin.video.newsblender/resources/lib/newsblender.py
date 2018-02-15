#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of News Blender.
#
# News Blender is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# News Blender is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with News Blender.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback
import urllib, urllib2, socket, json, collections
import xbmc, xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon

from YDStreamExtractor import getVideoInfo
from simplecache import SimpleCache, use_cache

# Plugin Info
ADDON_ID      = 'plugin.video.newsblender'
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
CONTENT_TYPE  = 'files'
USER_REGION   = REAL_SETTINGS.getSetting("Select_Country")
PTVL_RUNNING  = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
ISO3166       = os.path.join(ADDON_PATH,'resources','iso3166-1.json')
ISO639        = os.path.join(ADDON_PATH,'resources','iso639-1.json')
COUNTRY_LIST  = sorted((json.load(xbmcvfs.File(ISO3166)))['3166-1'], key=lambda x: x['name'])
LANGUAGE_LIST = sorted((json.load(xbmcvfs.File(ISO639)))['639-1'], key=lambda x: x['name'])
API_KEY       = REAL_SETTINGS.getSetting('APIKEY')
BASE_URL      = 'http://newsapi.org/v2'
SOURCES_URL   = BASE_URL + '/sources?apiKey=%s'%API_KEY #?language=en&country=us
HEADLINE_URL  = BASE_URL + '/top-headlines?apiKey=%s'%API_KEY
EVRYTHING_URL = BASE_URL + '/everything?apiKey=%s'%API_KEY
'&sources=%s'
'&q=%s'
'&category=%s'
'&sortBy=%s' #popularity,top,latest
LOGO_URL      = 'http://icons.better-idea.org/icon?url=%s&size=70..120..200'
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
QUALITY       = int(REAL_SETTINGS.getSetting('Quality'))
MAIN_MENU     = ["Browse by Category","Browse by Source","Browse by Country","Browse by Language"]
ITEM_MENU     = ["All","Top","Latest","Popular","Search"]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    param=[]
    if len(sys.argv[2])>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'): params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2: param[splitparams[0]]=splitparams[1]
    return param
    
def getRegionName(region):
    for item in COUNTRY_LIST:
        if item['alpha_2'].lower() == region.lower(): return item['name']
    return region
        
def getLanguageName(language):
    for item in LANGUAGE_LIST:
        if item['code'].lower() == language.lower(): return item['name']
    return language
        
socket.setdefaulttimeout(TIMEOUT)
class NewsBlender(object):
    def __init__(self):
        self.cache   = SimpleCache()
        self.sources = self.openURL(SOURCES_URL).get('sources','')
        
        
    def openURL(self, url):
        log('openURL, url = ' + url)
        try:
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib2.urlopen(request, timeout = TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(hours=1))
            return json.loads(self.cache.get(ADDON_NAME + '.openURL, url = %s'%url))
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
         
        
    def buildMenu(self):
        for idx, item in enumerate(MAIN_MENU): self.addDir(item,'',idx)
            
            
    def buildCategory(self):
        category = collections.Counter([x['category'] for x in self.sources])
        for category, value in sorted(category.iteritems()): self.addDir(category.title(),category,4)

        
    def buildCountry(self):
        countries  = collections.Counter([x['country'] for x in self.sources])
        for country, value in sorted(countries.iteritems()): self.addDir(getRegionName(country),country,6)
        
        
    def buildLanguage(self):
        languages  = collections.Counter([x['language'] for x in self.sources])
        for language, value in sorted(languages.iteritems()): self.addDir(getLanguageName(language),language,7)

        
    def buildSource(self, items=None):
        if items is None: items = self.sources
        for source in items:
            label      = source['name']
            thumb      = (LOGO_URL%source['url'] or ICON)
            infoLabels = {"mediatype":"files","label":label,"title":label,"genre":source.get('category','news'),"plot":source.get('description','news')}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
            self.addDir(label, source['id'], 5, infoLabels, infoArt)
    
    
    def browseCategory(self, url):
        self.buildSource(self.openURL(SOURCES_URL + '&category=%s'%url).get('sources',''))
        

    def browseCountry(self, url):
        self.buildSource(self.openURL(SOURCES_URL + '&country=%s'%url).get('sources',''))

        
    def browseLanguage(self, url):
        self.buildSource(self.openURL(SOURCES_URL + '&language=%s'%url).get('sources',''))
            
            
    def browseTop(self, url):
        self.browse(self.newsArticles.get_by_top(url).get('sources',''))
        
        
    def browseLatest(self, url):
        self.browse(self.newsArticles.get_by_latest(url).get('sources',''))
        
        
    def browsePopular(self, url):
        self.browse(self.newsArticles.get_by_popular(url).get('sources',''))
        
        
    def search(self, name, url):
        kb = xbmc.Keyboard('', LANGUAGE(30005)%name)
        xbmc.sleep(1000)
        kb.doModal()
        if kb.isConfirmed():
            try: self.browseArticles(name, url, self.openURL(EVRYTHING_URL + '&sources=%s&q=%s'%(url,urllib.quote_plus(kb.getText()))).get('articles',''), False)
            except Exception as e:
                log('search, failed ' + str(e), xbmc.LOGERROR)

                
    def buildArticles(self, name, url):
        self.browseArticles(name, url, self.openURL(HEADLINE_URL + '&sources=%s'%url).get('articles',''))

        
    def browseArticles(self, name, url, items, search=True):
        tmpList = []
        dlg = None
        dlg = xbmcgui.DialogBusy()
        dlg.create()
        for idx, item in enumerate(items):
            if dlg is not None: dlg.update(idx * 100 // len(items))
            info = self.getVideo(item['url'])
            if info is None: continue
            tmpList.append(info)
        if dlg is not None: dlg.close()
        for item in tmpList:
            try:
                source = item['source']['name']
                label  = item['title']
                thumb  = item['urlToImage']
                try: aired = item['publishedAt'].split('T')[0]
                except: aired = (datetime.datetime.now()).strftime('%Y-%m-%d') 
                url    = info[0]['xbmc_url']
                # if 'subtitles' in info[0]['ytdl_format']: liz.setSubtitles([x['url'] for x in info[0]['ytdl_format']['subtitles'].get('en','') if 'url' in x])
                infoLabels = {"mediatype":"episode","label":label ,"title":label,"duration":info[0]['ytdl_format'].get('duration',0),"aired":aired,"plot":item['description'],"genre":"News"}
                infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
                self.addLink(label, url, 9, infoLabels, infoArt)
            except: pass
        if len(tmpList) == 0: self.addLink((LANGUAGE(30003)%name), "", "")
        elif search: self.addSearch(name, url)
       
    def getVideo(self, url):
        cacheresponse = self.cache.get(ADDON_NAME + '.getVideo, url = %s'%url)
        if not cacheresponse:
            info = getVideoInfo(url,QUALITY,True)
            if info is not None: info = info.streams()
            self.cache.set(ADDON_NAME + '.getVideo, url = %s'%url, json.dumps(info), expiration=datetime.timedelta(days=14))
        return json.loads(self.cache.get(ADDON_NAME + '.getVideo, url = %s'%url))
            
            
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        if liz is None: liz = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        
           
    def addSearch(self, name, url):
        self.addDir((LANGUAGE(30004)%name), url, 8)
           
           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':LOGO_URL%urllib.quote_plus(name),'fanart':FANART})
        else: liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART}) #LOGO_URL%urllib.quote_plus(name)
        else: liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

params=getParams()
try: url=urllib.unquote_plus(params["url"])
except: url=None
try: name=urllib.unquote_plus(params["name"])
except: name=None
try: mode=int(params["mode"])
except: mode=None
log("Mode: "+str(mode))
log("URL : "+str(url))
log("Name: "+str(name))

if mode==None:  NewsBlender().buildMenu()
elif mode == 0: NewsBlender().buildCategory()
elif mode == 1: NewsBlender().buildSource()
elif mode == 2: NewsBlender().buildCountry()
elif mode == 3: NewsBlender().buildLanguage()
elif mode == 4: NewsBlender().browseCategory(url)
elif mode == 5: NewsBlender().buildArticles(name, url)
elif mode == 6: NewsBlender().browseCountry(url)
elif mode == 7: NewsBlender().browseLanguage(url)
elif mode == 8: NewsBlender().search(name, url)
elif mode == 9: NewsBlender().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)