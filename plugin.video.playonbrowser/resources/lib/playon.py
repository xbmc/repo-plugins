#   Copyright (C) 2020 Lunatixz
#
#
# This file is part of Playon Browser
#
# Playon Browser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Playon Browser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Playon Browser.  If not, see <http://www.gnu.org/licenses/>.

import sys, os, re, random, traceback, json, xmltodict, collections, datetime

from simplecache import SimpleCache
from six.moves   import urllib
from kodi_six    import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode

# Plugin Info
ADDON_ID      = 'plugin.video.playonbrowser'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

# Globals
TIMEOUT        = 30
CONTENT_TYPE   = 'episodes'
PLAYON_DATA    = '/data/data.xml'
SEARCH_URL     = "/data/data.xml?id=%s&searchterm="
BASE_VIDEO_URL = "%s/%s/main.m3u8"
AUTO_URL       = "http://m.playon.tv/q.php"
BASE_ID_URL    = "%s/data/data.xml?id=%s"
BASE_UPNP      = REAL_SETTINGS.getSetting("playonUPNPid").rstrip('/')
BASE_URL       = REAL_SETTINGS.getSetting("playonserver").rstrip('/')
DEBUG          = REAL_SETTINGS.getSetting("debug") == "true"
KODILIBRARY    = False #todo strm contextMenuc

def getPTVL():
    return xbmcgui.Window(10000).getProperty('PseudoTVRunning') == "True"

def getURLTYPE():
    return {0:'m3u8',1:'upnp',2:'ext'}[int(REAL_SETTINGS.getSetting('playonmedia'))]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg = '%s, %s'%((msg),traceback.format_exc())
    xbmc.log('%s-%s-%s'%(ADDON_ID,ADDON_VERSION,msg), level)

def getKeyboard(default='',header=ADDON_NAME):
    kb = xbmc.Keyboard(default,header)
    xbmc.sleep(1000)
    kb.doModal()
    if kb.isConfirmed(): return kb.getText()
    return False
    
def folderIcon(val):
    log('folderIcon')
    return random.choice(['/images/folders/folder_%s_0.png' %val,'/images/folders/folder_%s_1.png' %val])
     
def parseSEinfo(label):
    season   = -1
    episode  = -1
    pattern1 = re.compile(r"""(?:s|season)(?:\s)(?P<s>\d+)(?:e|x|episode|\n)(?:\s)(?P<ep>\d+) # s 01e 02"""                 , re.VERBOSE)
    pattern2 = re.compile(r"""(?:s|season)(?P<s>\d+)(?:e|x|episode|\n)(?:\s)(?P<ep>\d+) # s01e 02"""                        , re.VERBOSE)
    pattern3 = re.compile(r"""(?:s|season)(?:\s)(?P<s>\d+)(?:e|x|episode|\n)(?P<ep>\d+) # s 01e02"""                        , re.VERBOSE)
    pattern4 = re.compile(r"""(?:s|season)(?P<s>\d+)(?:e|x|episode|\n)(?P<ep>\d+) # s01e02"""                               , re.VERBOSE)
    pattern5 = re.compile(r"""(?:s|season)(?P<s>\d+)(?:.*)(?:e|x|episode|\n)(?P<ep>\d+) # s01 random123 e02"""              , re.VERBOSE)
    pattern6 = re.compile(r"""(?:s|season)(?:\s)(?P<s>\d+)(?:.*)(?:e|x|episode|\n)(?:\s)(?P<ep>\d+) # s 01 random123 e 02""", re.VERBOSE)
    pattern7 = re.compile(r"""(?:s|season)(?:\s)(?P<s>\d+)(?:.*)(?:e|x|episode|\n)(?P<ep>\d+) # s 01 random123 e02"""       , re.VERBOSE)
    pattern8 = re.compile(r"""(?:s|season)(?P<s>\d+)(?:.*)(?:e|x|episode|\n)(?:\s)(?P<ep>\d+) # s01 random123 e 02"""       , re.VERBOSE)
    patterns = [pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7, pattern8 ]

    for pattern in patterns:
        match = re.search(pattern, label)
        if match:
            season  = int(match.group('s'))
            episode = int(match.group('ep'))
    log("parseSEinfo, return S:" + str(season) +',E:'+ str(episode)) 
    return season, episode

class PlayOn:
    def __init__(self, sysARG):
        log('__init__, sysARG = %s'%(sysARG))
        random.seed()
        self.sysARG  = sysARG
        self.cache   = SimpleCache()
        self.chkUPNP()
           
           
    def openURL(self, url):
        log('openURL, url = %s'%(url))
        try:
            cacheResponse = self.cache.get('%s.%s.openURL.url=%s'%(ADDON_ID,ADDON_VERSION,url))
            if DEBUG: cacheResponse = None
            if not cacheResponse:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                    cacheResponse = response.read()
                    if isinstance(cacheResponse, bytes): cacheResponse = cacheResponse.decode(errors='replace')
                    self.cache.set('%s.%s.openURL.url=%s'%(ADDON_ID,ADDON_VERSION,url), cacheResponse, expiration=datetime.timedelta(minutes=5))
            return cacheResponse
        except Exception as e: log("openURL Failed! " + str(e), xbmc.LOGERROR)
        if url == BASE_URL + PLAYON_DATA: self.getIP()
        
        
    def getIP(self):
        urls = self.openURL(AUTO_URL).split('|')
        for url in urls:
            match = re.findall(r'[0-9]+(?:\.[0-9]+){3}:[0-9]+', url)
            log('getIP, match = ' + str(match))
            if len(match) == 0:
                url = getKeyboard(LANGUAGE(30001),LANGUAGE(30002))
                if url == False: return
            if not url.startswith('http'): url = "http://%s"%url
            BASE_URL = url
            REAL_SETTINGS.setSetting("playonserver",url)
            if self.chkIP(url): return
        
        
    def chkIP(self, url=BASE_URL):
        log('chkIP, url = ' + str(url))
        results = xmltodict.parse(self.openURL(url + PLAYON_DATA))
        if results and 'catalog' in results:
            try:
                ServerName = results['catalog']['@name']
                ServerVer = 'PlayOn v.%s'%results['catalog']['@server']
                ServerMSG = "Connected to [B]%s %s[/B]"%(ServerName,ServerVer)
                log('chkIP, ServerName = ' + ServerName)
                log('chkIP, ServerVer = ' + ServerVer)
                REAL_SETTINGS.setSetting("playonServerid",ServerMSG)
                xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30011)%ServerName, ICON, 5000)
                xbmc.executebuiltin("Container.Refresh")
                return True
            except Exception as e: log("chkIP Failed! " + str(e), xbmc.LOGERROR)
        else: xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30010), ICON, 5000)
        return False
        
    
    def getUPNP(self):
        log('getUPNP')
        """ Check Kodi UPNP support. """
        json_query = ('{"jsonrpc":"2.0","method":"Settings.GetSettingValue","params":{"setting":"services.upnp"},"id":1}')
        data = json.loads(xbmc.executeJSONRPC(json_query))
        try:
            if 'result' in data and 'value' in data['result']: return data['result']['value']
        except Exception as e: log('getUPNP, Failed! ' + str(e))
        return False
        
    
    def setUPNP(self):
        log('setUPNP')
        """ Enable Kodi UPNP support. """
        json_query = ('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","params":{"setting":"services.upnp","value":true},"id":1}')
        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30015), ICON, 5000)
        return json.loads(xbmc.executeJSONRPC(json_query))

    
    def getUPNP_ID(self):
        log('getUPNP_ID')
        """ Check if upnp id is valid. """
        json_query = ('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s"},"id":1}'%BASE_UPNP)
        try:
            if not json.loads(xbmc.executeJSONRPC(json_query))['result']['files'][0]['file'].endswith('/playonprovider/'): return None
        except Exception as e: 
            log('getUPNP_ID, Failed! ' + str(e))
            return None
        return BASE_UPNP
            
            
    def chkUPNP(self):
        log('chkUPNP')
        """ Query json, locate 'playon server' path, else prompt. """
        if self.getUPNP_ID() is not None: return
        else:
            if not self.getUPNP(): self.setUPNP()
            json_query = ('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"upnp://"},"id":1}')
            data = json.loads(xbmc.executeJSONRPC(json_query))
            if data and 'result' in data and 'files' in data['result']:
                for item in data['result']['files']:
                    if (item['label']).lower().startswith('playon'):
                        REAL_SETTINGS.setSetting("playonUPNPid",item['file'].rstrip('/'))
                        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30013), ICON, 5000)
                        BASE_UPNP = item['file']
                        REAL_SETTINGS.setSetting("playonUPNPid",BASE_UPNP.rstrip('/'))
            elif getPTVL() == False:
                BASE_UPNP = xbmcgui.Dialog().browse(0, LANGUAGE(30014), 'files', '', False, False, 'upnp://')
                if BASE_UPNP != -1: REAL_SETTINGS.setSetting("playonUPNPid",BASE_UPNP.rstrip('/'))
            else: xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30010), ICON, 5000)
                

    def buildItemMenu(self, uri=PLAYON_DATA, search=False):
        log('buildItemMenu, uri = ' + uri)
        try:
            genSTRM  = False
            results  = []
            ranNum   = random.randrange(9)
            response = dict(xmltodict.parse(self.openURL(BASE_URL + uri)))
            if response and 'catalog' in response and 'group' in response['catalog']: results = response['catalog']['group']
            elif response and 'group' in response:# and response['group']['@href'] == uri:
                results = response['group'].get('group',{})
                genSTRM = True            
            if isinstance(results,collections.OrderedDict): results = [dict(results)]
            if not search and uri == PLAYON_DATA: self.addDir('[B][PlayOn][/B] Search','',2,ICON,genSTRM)
            for item in results:
                try:
                    if isinstance(item,collections.OrderedDict): item = dict(item)
                    if item['@type'] == 'folder':
                        name  = item['@name'].replace('PlayOn','[B][PlayOn][/B]').replace('PlayMark','[B][Playon][/B] PlayMark')
                        if search and name.startswith('[B][PlayOn][/B]'): continue
                        thumb = BASE_URL + ((item.get('@art','').replace('&size=tiny','&size=large')) or folderIcon(ranNum))
                        if search and item.get('@searchable','false') == 'true':
                            myURL = json.dumps({'id':item.get('@id',''),'uri':item['@href'],'searchable':item.get('@searchable','false')})
                            self.addDir('Search %s'%name,myURL,3,thumb)
                        elif not search: self.addDir(name,item['@href'],1,thumb, genSTRM)
                    elif item['@type'] == 'video': self.addLink(item['@name'],item['@href'],9,len(results))
                except Exception as e: log("buildItemMenu Failed! " + str(e), xbmc.LOGERROR)
        except Exception as e: log("buildItemMenu Failed! " + str(e), xbmc.LOGERROR)
           
                           
    def searchItem(self, uri):
        log('searchItem, uri = ' + uri)
        item  = json.loads(uri)
        query = getKeyboard(header=LANGUAGE(30016))
        if query == False: self.buildItemMenu(search=True)
        else: self.buildItemMenu(SEARCH_URL%(item['id']) + 'dc:description%20contains%20' + urllib.parse.quote(query))
        

    def playLater(self, name, uri):
        log('playLater, uri = ' + uri)
        response = dict(xmltodict.parse(self.openURL(BASE_URL + uri)))
        if response and 'result' in response:
            result = dict(response['result'])
            if result['status'] == "true":
                msg = result['msg'].replace('The media item',name)
                xbmcgui.Dialog().notification(ADDON_NAME, msg, ICON, 5000)
        
   
    def playVideo(self, name, uri):
        log('playVideo, uri = ' + uri)
        liz = self.buildListitem(uri)
        url = liz.getPath()
        log('playVideo, uri = %s, url = %s'%(uri,url))
        if url.startswith('upnp://'):
            xbmc.executebuiltin('PlayMedia(%s)'%url)
        else:
            if url.strip('/').endswith('.m3u8'):
                liz.setProperty('inputstreamaddon','inputstream.adaptive')
                liz.setProperty('inputstream.adaptive.manifest_type','hls')
            xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)

            
    def buildListitem(self, uri, contextMenu=[]):
        result   = {}
        infoList = {}
        URLTYPE  = getURLTYPE()
        response = dict(xmltodict.parse(self.openURL(BASE_URL + uri)))
        if response and 'group' in response and response['group']['@href'] == uri:
            result = dict(response['group'])
            tvshowtitle = (dict(result.get('series','')).get('@name','') or None)
            title = (result.get('@name','') or dict(result['media_title'])['@name'] or dict(result['media'])['@name'])
            label = title
            mType = 'movie'
            if tvshowtitle is not None:
                if tvshowtitle not in title: label = '%s - %s'%(tvshowtitle,title)
                season, episode = parseSEinfo(title)
                infoList['season']  = int(season)
                infoList['episode'] = int(episode)
                mType = 'episode'
            plot  = (result.get('@description','') or dict(result.get('description','')).get('@name','') or '')
            thumb = BASE_URL + (result.get('@art','') or dict(result.get('media','')).get('@art','') or ICON).replace('&size=tiny','&size=large')
            try:
                aired = (dict(result.get('date','')).get('@name','') or datetime.datetime.now().strftime('%m/%d/%Y'))
                aired = (datetime.datetime.strptime(aired, '%m/%d/%Y')).strftime('%Y-%m-%d') 
            except: aired = datetime.datetime.now().strftime('%Y-%m-%d')
            
            playLater = dict(result.get('media_playlater','')).get('@src','')
            if playLater:
                u=self.sysARG[0]+"?url="+urllib.parse.quote(playLater)+"&mode="+str(8)+"&name="+urllib.parse.quote(label)
                contextMenu = [(LANGUAGE(30017),'RunPlugin(%s)'%(u))]

            timeData  = (dict(result.get('time','')).get('@name','') or '')
            if len(timeData) > 0:
                timeList = timeData.split(':')
                hours = int(timeList[0])
                mins  = int(timeList[1])
                secs  = int(timeList[2])
                duration = ((hours * 60 * 60) + (mins * 60) + secs)
            else: duration = 0 

            if URLTYPE == 'm3u8' and 'playlaterrecordings' not in result['@href']: 
                url = BASE_VIDEO_URL%(BASE_URL,result['@href'].split('?id=')[1])
            elif URLTYPE == 'ext' or 'playlaterrecordings' in result['@href']: 
                url = BASE_URL + '/' + dict(result['media'])['@src']
            else: 
                url = BASE_UPNP + '/' + (result['@href'].split('?id=')[1]) + '/'
            log('buildListitem, url = ' + url)
            liz=xbmcgui.ListItem(label, path=url)
            liz.addContextMenuItems(contextMenu)
            CONTENT_TYPE = mType
            infoList = {"mediatype":mType,"label":label,"title":label,"tvshowtitle":tvshowtitle,"plot":plot,"duration":duration,"aired":aired}
            liz.setInfo(type="Video", infoLabels=infoList)
            liz.setArt({"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART})
            liz.setProperty("IsPlayable","true")
            liz.setProperty("IsInternetStream","true")
            return liz
            
            
    def addLink(self, name, u, mode, total=0):
        log('addLink, name = ' + name)
        # contextMenu = [('Add to Library','RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.parse.quote(u)+"&mode="+str(7)+"&name="+urllib.parse.quote(name)))]
        liz = self.buildListitem(u) 
        u=self.sysARG[0]+"?url="+urllib.parse.quote(u)+"&mode="+str(mode)+"&name="+urllib.parse.quote(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, thumb=ICON, strm=False):
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        # if strm:
            # contextMenu = [('Add to Library','RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.parse.quote(u)+"&mode="+str(7)+"&name="+urllib.parse.quote(name)))]
            # liz.addContextMenuItems(contextMenu)
        liz.setProperty('IsPlayable', 'false')
        liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        liz.setArt({'thumb':thumb,'icon':thumb,'fanart':FANART})
        u=self.sysARG[0]+"?url="+urllib.parse.quote(u)+"&mode="+str(mode)+"&name="+urllib.parse.quote(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)
  
  
    def genSTRMS(self, name, uri):
        log('genSTRMS, name = ' + name)
        #todo
       
              
    def getParams(self):
        return dict(urllib.parse.parse_qsl(self.sysARG[2][1:]))

            
    def run(self):  
        params=self.getParams()
        try: url=urllib.parse.unquote(params["url"])
        except: url=None
        try: name=urllib.parse.unquote(params["name"])
        except: name=None
        try: mode=int(params["mode"])
        except: mode=None
        log("Mode: "+str(mode))
        log("URL : "+str(url))
        log("Name: "+str(name))

        if mode==None:  self.buildItemMenu()
        if mode==1:     self.buildItemMenu(url)
        if mode==2:     self.buildItemMenu(search=True)
        if mode==3:     self.searchItem(url)
        if mode==7:     self.genSTRMS(name, url)
        if mode==8:     self.playLater(name, url)
        if mode==9:     self.playVideo(name, url)

        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=False)