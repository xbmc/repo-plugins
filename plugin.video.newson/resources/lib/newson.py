#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of NewsOn.
#
# NewsOn is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NewsOn is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NewsOn.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, traceback, feedparser, random
import urlparse, urllib, urllib2, socket, json, collections, gzip
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from StringIO import StringIO
from simplecache import SimpleCache
# Plugin Info
ADDON_ID      = 'plugin.video.newson'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString
NEWSART       = os.path.join(ADDON_PATH,'resources','images','newscast.jpg')
CLIPART       = os.path.join(ADDON_PATH,'resources','images','videoclips.jpg')

## GLOBALS ##
TIMEOUT       = 30
CONTENT_TYPE  = 'episodes'
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
BASE_API      = 'http://watchnewson.com/api/linear/channels'
MENU          = [(LANGUAGE(30002), '0', 0, False, {"thumb":NEWSART,"poster":NEWSART,"fanart":FANART,"icon":ICON,"logo":ICON}),
                 (LANGUAGE(30003), '2', 2, False, {"thumb":CLIPART,"poster":CLIPART,"fanart":FANART,"icon":ICON,"logo":ICON})]
           
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
           
socket.setdefaulttimeout(TIMEOUT)
class NewsOn(object):
    def __init__(self):
        log('__init__')
        self.cache     = SimpleCache()
        self.stateMenu = self.getStates()

        
    def openURL(self, url):
        try:
            cacheResponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheResponse:
                request = urllib2.Request(url)
                request.add_header('Accept-encoding', 'gzip')
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib2.urlopen(request, timeout = TIMEOUT)
                log(response.headers['content-type'])
                log(response.headers['content-encoding'])
                if response.info().get('content-encoding') == 'gzip':
                    buf = StringIO(response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    cacheResponse = f.read()
                else: cacheResponse = response
                response.close()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, cacheResponse, expiration=datetime.timedelta(hours=1))
            if isinstance(cacheResponse, basestring): cacheResponse = json.loads(cacheResponse)
            return cacheResponse
        except Exception as e: 
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
        
        
    def mainMenu(self):
        log('mainMenu')
        for item in MENU: self.addDir(*item)
        
                    
    def browseMenu(self, id=1):
        log('browseMenu, id = ' + str(id))
        self.stateMenu = [tuple(s.format(id) for s in tup) for tup in self.stateMenu]
        for item in self.stateMenu: self.addDir(*item)
            
            
    def getStates(self):
        log('getStates')
        state     = []
        stateLST  = []
        data = self.openURL(BASE_API)
        if len(data) == 0: return []
        for channel in data: 
            try: state.append(channel['config']['state'])
            except: pass
        states = collections.Counter(state)
        for key, value in sorted(states.iteritems()): stateLST.append(("%s"%(key), key , '{}'))
        return stateLST
            
            
    def newsCasts(self, state):
        log('newsCasts, state = ' + state)
        urls = []
        data = self.openURL(BASE_API)
        if len(data) == 0: return
        for channel in data:
            try: states = channel['config']['state']
            except: continue
            if state in states:
                chid   = channel['identifier']
                title  = channel['title']
                icon   = (channel['icon'] or ICON)
                for idx, stream in enumerate(channel['streams']):
                    streamType = stream['StreamType']
                    if streamType == 'website': continue#random.choice(['website','roku']): 
                    #multiple urls, only add unique.
                    url = stream['Url']
                    offset = stream['OffsetFromNow']
                    delay  = url+'&delay=%d'
                    #todo do something with delay option?
                    if url not in urls:
                        urls.append(url)
                        chid = chid+'.%d'%idx if idx > 0 else chid
                        label      = "%s - %s" % (chid, title)
                        infoLabels ={"mediatype":"episodes","label":label ,"title":label}
                        infoArt    ={"thumb":icon,"poster":icon,"fanart":FANART,"icon":icon,"logo":icon} 
                        self.addLink(title, url, 9, infoLabels, infoArt)
        
        
    def videoclips(self, state):
        log('videoclips, state = ' + state)
        data = self.openURL(BASE_API)
        if len(data) == 0: return
        for channel in data:
            try: states = channel['config']['state']
            except: continue
            if state in states:
                chid   = channel['identifier']
                title  = channel['title']
                icon   = (channel['icon'] or ICON)
                vidURL = channel['config']['localvodfeed']
                if vidURL:
                    label      = "%s - %s" % (chid, title)
                    infoLabels ={"mediatype":"video","label":label,"title":label}
                    infoArt    ={"thumb":icon,"poster":icon,"fanart":FANART,"icon":ICON,"logo":ICON} 
                    self.addDir(label, vidURL, 4, infoLabels, infoArt)


    def parseclips(self, url):
        log('parseclips, url = ' + url)
        feed = feedparser.parse(url)
        for item in feed['entries']:
            if item and 'summary_detail' in item:
                for vids in item['media_content']:
                    title = item['title']
                    url   = vids['url']
                    plot  = item['summary']
                    aired = item.get('published','').replace(' EST','').replace(' UTC','').replace(' GMT','')
                    try: aired = (datetime.datetime.strptime(aired, '%a, %d %b %Y %H:%M:%S'))
                    except: aired = datetime.datetime.now()
                    aired = aired.strftime("%Y-%m-%d")
                    thumb = item['media_thumbnail'][0]['url']
                    tagLST = []
                    if 'tags' in item:
                        for tag in item['tags']: tagLST.append(((tag['term']).split('/')[0]).title())
                    if len(tagLST) > 0: genre = (tagLST[0] or '')
                    infoLabels ={"mediatype":"episode","label":title,"title":title,"plot":plot,"aired":aired,'genre':genre,'tags':tagLST}
                    infoArt    ={"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON} 
                    self.addLink(title, url, 8, infoLabels, infoArt)

                    
    def playVideo(self, name, url, live=False):
        log('playVideo')
        liz = xbmcgui.ListItem(name, path=url)
        if live: 
            liz.setProperty('inputstreamaddon','inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type','hls') 
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False: liz.setInfo( type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
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
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
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

if mode==None:  NewsOn().mainMenu()
elif mode == 0: NewsOn().browseMenu(1)
elif mode == 1: NewsOn().newsCasts(url)
elif mode == 2: NewsOn().browseMenu(3)
elif mode == 3: NewsOn().videoclips(url)
elif mode == 4: NewsOn().parseclips(url)
elif mode == 8: NewsOn().playVideo(name, url)
elif mode == 9: NewsOn().playVideo(name, url, True)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)