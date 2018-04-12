#   Copyright (C) 2017 Lunatixz
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

import sys, os, re, random, traceback, json, xmltodict, collections
import urlparse, urllib, urllib2, socket, datetime
import xbmc, xbmcplugin, xbmcaddon, xbmcgui

from simplecache import SimpleCache

# Plugin Info
ADDON_ID      = 'plugin.video.playonbrowser'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

# Globals
TIMEOUT        = 30
CONTENT_TYPE   = 'files'
PLAYON_DATA    = '/data/data.xml'
SEARCH_URL     = "/data/data.xml?id=%s&searchterm="
BASE_VIDEO_URL = "%s/%s/main.m3u8"
AUTO_URL       = "http://m.playon.tv/q.php"
BASE_ID_URL    = "%s/data/data.xml?id=%s"
BASE_UPNP      = REAL_SETTINGS.getSetting("playonUPNPid").rstrip('/')
BASE_URL       = REAL_SETTINGS.getSetting("playonserver").rstrip('/')
DEBUG          =  REAL_SETTINGS.getSetting("debug") == "true"
KODILIBRARY    = False #todo strm contextMenu
URLTYPE        = {0:'m3u8',1:'upnp',2:'ext'}[int(REAL_SETTINGS.getSetting('playonmedia'))]
PTVL_RUNNING   = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == "True"

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + (msg.encode("utf-8")), level)
     
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
    
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

random.seed()
socket.setdefaulttimeout(TIMEOUT)
class PlayOn:
    def __init__(self):
        self.cache = SimpleCache()
        if URLTYPE == 'upnp': self.chkUPNP()
            
            
    def openURL(self, url):
        log('openURL, url = ' + str(url))
        try:
            cacheResponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheResponse:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib2.urlopen(request, timeout=TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(minutes=5))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except Exception as e: log("openURL Failed! " + str(e), xbmc.LOGERROR)
        if url == BASE_URL + PLAYON_DATA: self.getIP()
        
        
    def getIP(self):
        url   = self.openURL(AUTO_URL).replace('|','')
        match = re.findall(r'[0-9]+(?:\.[0-9]+){3}:[0-9]+', url)
        log('getIP, match = ' + str(match))
        if len(match) == 0:
            url = getKeyboard(LANGUAGE(30001),LANGUAGE(30002))
            if url == False: return
        if not url.startswith('http'): url = "http://%s"%url
        BASE_URL = url
        REAL_SETTINGS.setSetting("playonserver",url)
        self.chkIP(url)
        
        
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
            except Exception as e: log("chkIP Failed! " + str(e), xbmc.LOGERROR)
        else: xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30010), ICON, 5000)
    
    
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
        data = json.loads(xbmc.executeJSONRPC(json_query))
        try:
            if not data['result']['files'][0]['file'].endswith('/playonprovider/'): return None
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
            elif PTVL_RUNNING == False:
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
                results = response['group']['group']
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
        if query == False: 
            self.buildItemMenu(search=True)
            return
        else: query = 'dc:description%20contains%20' + urllib.quote(query)
        self.buildItemMenu(SEARCH_URL%(item['id']) + query)
        

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
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

            
    def buildListitem(self, uri, contextMenu=[]):
        result   = {}
        infoList = {}
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
            plot = (result.get('@description','') or dict(result.get('description','')).get('@name','') or '')
            thumb = BASE_URL + (result.get('@art','') or dict(result.get('media','')).get('@art','') or ICON).replace('&size=tiny','&size=large')
            try:
                aired = (dict(result.get('date','')).get('@name','') or datetime.datetime.now().strftime('%m/%d/%Y'))
                aired = (datetime.datetime.strptime(aired, '%m/%d/%Y')).strftime('%Y-%m-%d') 
            except: 
                aired = datetime.datetime.now().strftime('%Y-%m-%d')
            timeData  = (dict(result.get('time','')).get('@name','') or '')
            playLater = dict(result.get('media_playlater','')).get('@src','')
            contextMenu = contextMenu + [('Add to PlayLater','XBMC.RunPlugin(%s)'%(sys.argv[0]+"?url="+urllib.quote_plus(playLater)+"&mode="+str(8)+"&name="+urllib.quote_plus(label.encode("utf-8"))))]

            if len(timeData) > 0:
                timeList = timeData.split(':')
                hours = int(timeList[0])
                mins  = int(timeList[1])
                secs  = int(timeList[2])
                duration = ((hours * 60 * 60) + (mins * 60) + secs)
            else: duration = 0 
                
            if URLTYPE == 'm3u8' and 'playlaterrecordings' not in result['@href']: url = BASE_VIDEO_URL%(BASE_URL,result['@href'].split('?id=')[1])
            elif URLTYPE == 'ext' or 'playlaterrecordings' in result['@href']: url = BASE_URL + '/' + dict(result['media'])['@src']
            else: url = BASE_UPNP + '/' + dict(result['media'])['@src'].split('.')[0].split('/')[0] + '/'
                
            log('playVideo, url = ' + url)
            liz=xbmcgui.ListItem(name, path=url)
            liz.addContextMenuItems(contextMenu)
            CONTENT_TYPE = mType
            infoList = {"mediatype":mType,"label":label,"title":label,"tvshowtitle":tvshowtitle,"plot":plot,"duration":duration,"aired":aired}
            liz.setInfo(type="Video", infoLabels=infoList)
            liz.setArt({"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART})
            liz.setProperty("IsPlayable","true")
            liz.setProperty("IsInternetStream","true")
            return liz
            
            
    def addLink(self, name, u, mode, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        contextMenu = [('Add to Library','XBMC.RunPlugin(%s)'%(sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(7)+"&name="+urllib.quote_plus(name)))]
        liz = self.buildListitem(u) 
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, thumb=ICON, strm=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        # if strm:
            # contextMenu = [('Add to Library','XBMC.RunPlugin(%s)'%(sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(7)+"&name="+urllib.quote_plus(name)))]
            # liz.addContextMenuItems(contextMenu)
        liz.setProperty('IsPlayable', 'false')
        liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        liz.setArt({'thumb':thumb,'fanart':FANART})
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  
  
    def genSTRMS(self, name, uri):
        log('genSTRMS, name = ' + name)
        #todo
  
  
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

if mode==None:  PlayOn().buildItemMenu()
if mode==1:     PlayOn().buildItemMenu(url)
if mode==2:     PlayOn().buildItemMenu(search=True)
if mode==3:     PlayOn().searchItem(url)
if mode==7:     PlayOn().genSTRMS(name, url)
if mode==8:     PlayOn().playLater(name, url)
if mode==9:     PlayOn().playVideo(name, url)

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)