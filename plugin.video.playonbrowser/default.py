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

import sys, os, re, random, traceback
import urlparse, urllib, urllib2, socket
import xbmc, xbmcplugin, xbmcaddon, xbmcgui
import xml.etree.ElementTree as ElementTree 

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json
   
## GLOBALS ##

# Plugin Info
ADDON_ID = 'plugin.video.playonbrowser'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON = os.path.join(ADDON_PATH, 'icon.png')
FANART = os.path.join(ADDON_PATH, 'fanart.jpg')
LANGUAGE = REAL_SETTINGS.getLocalizedString

# Playon Info
PLAYON_DATA = '/data/data.xml'
BASE_URL = sys.argv[0]
BASE_HANDLE = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
TIMEOUT = 15
JSON_ART = ["thumb","poster","fanart","banner","landscape","clearart","clearlogo"]
ITEM_TYPES = ['genre','country','year','episode','season','sortepisode','sortseason','episodeguide','showlink','top250','setid','tracknumber','rating','userrating','watched','playcount','overlay','director','mpaa','plot','plotoutline','title','originaltitle','sorttitle','duration','studio','tagline','writer','tvshowtitle','premiered','status','set','setoverview','tag','imdbnumber','code','aired','credits','lastplayed','album','artist','votes','path','trailer','dateadded','mediatype','dbid']

socket.setdefaulttimeout(TIMEOUT)
    
# User Settings
DEBUG =  REAL_SETTINGS.getSetting("debug") == "true"
KODILIBRARY   = False #todo strm contextMenu
useUPNP = REAL_SETTINGS.getSetting("useUPNP") == "true"
cache = REAL_SETTINGS.getSetting('cache') == "true"
incMeta = REAL_SETTINGS.getSetting('meta') == "true"
playDirect = REAL_SETTINGS.getSetting("playDirect") == "true"
TMDB_API_KEY = REAL_SETTINGS.getSetting("TMDB_API_KEY")

if xbmcgui.Window(10000).getProperty('PseudoTVRunning') == "True":
    playDirect   = False
 
try:
    from metahandler import metahandlers
    metaget = metahandlers.MetaData(preparezip=False, tmdb_api_key=TMDB_API_KEY)              
except Exception,e:  
    incMeta = False
    xbmc.log("metahandler Import failed! " + str(e), xbmc.LOGERROR)    

# try:
    # from metadatautils import MetadataUtils
    # artutils = MetadataUtils()
# except Exception,e:  
    # incMeta = False
    # xbmc.log("artworkUtils Import failed! " + str(e), xbmc.LOGERROR)   
     
displayCategories = {'MoviesAndTV': 3,
                    'Comedy': 128,
                    'News': 4,
                    'Sports': 8,
                    'Kids': 16,
                    'Music': 32,
                    'VideoSharing': 64,
                    'LiveTV': 2048,
                    'MyMedia': 256,
                    'Plugins': 512,
                    'Other': 1024}
                        
displayTitles = {'MoviesAndTV': 'Movies And TV',
                'News': 'News',
                'Popular': 'Popular',
                'All': 'All',
                'Sports': 'Sports',
                'Kids': 'Kids',
                'Music': 'Music',
                'VideoSharing': 'Video Sharing',
                'Comedy': 'Comedy',
                'MyMedia': 'My Media',
                'Plugins': 'Plugins',
                'Other': 'Other',
                'LiveTV': 'Live TV'}
                    
displayImages = {'MoviesAndTV': '/images/categories/movies.png',
                'News': '/images/categories/news.png',
                'Popular': '/images/categories/popular.png',
                'All': '/images/categories/all.png',
                'Sports': '/images/categories/sports.png',
                'Kids': '/images/categories/kids.png',
                'Music': '/images/categories/music.png',
                'VideoSharing': '/images/categories/videosharing.png',
                'Comedy': '/images/categories/comedy.png',
                'MyMedia': '/images/categories/mymedia.png',
                'Plugins': '/images/categories/plugins.png',
                'Other': '/images/categories/other.png',
                'LiveTV': '/images/categories/livetv.png'}

def log(msg, level=xbmc.LOGDEBUG):
    msg = stringify(msg[:1000])
    if DEBUG == False and level == xbmc.LOGDEBUG:
        return
    if level == xbmc.LOGERROR:
        msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
       
def ascii(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('ascii', 'ignore')
    return string
    
def uni(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('utf-8', 'ignore' )
        else:
           string = ascii(string)
    return string
     
def stringify(string):
    if isinstance(string, list):
        string = stringify(string[0])
    elif isinstance(string, (int, float, long, complex, bool)):
        string = str(string)
    elif isinstance(string, (str, unicode)):
        string = uni(string)
    elif not isinstance(string, (str, unicode)):
        string = ascii(string)
    if isinstance(string, basestring):
        return string
    return ''
        
def mergeItems(mydict1, mydict2):
    log("utils: mergeItems")
    mydict = {}
    for key, value in mydict1.iteritems():
        if value:
            mydict.update({key: value})
    for key, value in mydict2.iteritems():
        if value:
            mydict.update({key: value})
    return mydict
  
def normalizeJson(mydict):
    log("utils: normalizeJson")
    dump = dumpJson(mydict)
    #correct metahandler art keys
    dump = dump.replace('banner_url','banner').replace('backdrop_url','fanart').replace('cover_url','poster')
    return loadJson(dump)
    
def loadJson(string, encode='utf-8'):
    log("utils: loadJson")
    if len(string) == 0:
        return {}
    try:
        return json.loads(uni(string))
    except:
        return json.loads(ascii(string))
        
def dumpJson(mydict, sortkey=True):
    log("utils: dumpJson")
    return json.dumps(mydict, sort_keys=sortkey)
    
def folderIcon(val):
    log('folderIcon')
    return random.choice(['/images/folders/folder_%s_0.png' %val,'/images/folders/folder_%s_1.png' %val])
         
class Playon:
    def __init__(self):
        random.seed()

    
    def chkUPNP(self, url):
        """ Check if upnp id is valid. """
        json_query = ('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s"},"id":1}'%url)      
        data = json.loads(xbmc.executeJSONRPC(json_query))
        try:
            if not data['result']['files'][0]['file'].endswith('/playonprovider/'):
                url = ''
        except Exception,e:
            url = ''
            log('chkUPNP, Failed! ' + str(e))
        log('chkUPNP, url = ' + url)
        return url
            
            
    def getUPNP(self):
        """ Query json, locate 'playon server' path, else prompt. """
        log('getUPNP')
        upnpID = self.chkUPNP(REAL_SETTINGS.getSetting("playonUPNPid"))
        if len(upnpID) > 0:
            return upnpID
        else:
            json_query = ('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"upnp://"},"id":1}')      
            data = json.loads(xbmc.executeJSONRPC(json_query))
            if 'result' in data and len(data['result']['files']) != 0:
                for item in data['result']['files']:
                    if (item['label']).lower().startswith('playon'):
                        REAL_SETTINGS.setSetting("playonUPNPid",item['file'].rstrip('/'))
                        return item['file']
            upnpID = xbmcgui.Dialog().browse(0, LANGUAGE(42010), 'files', '', False, False, 'upnp://')
            if upnpID != -1:
                REAL_SETTINGS.setSetting("playonUPNPid",upnpID.rstrip('/'))
                return upnpID


    def get_xml(self, url):
        """ This will pull down the XML content and return a ElementTree. """
        log('get_xml: ' + url)
        try:
            usock = urllib2.urlopen(url)
            response = usock.read()
            usock.close()
            return ElementTree.fromstring(response)
        except: return False 

        
    def get_argument_value(self, name):
        """ pulls a value out of the passed in arguments. """
        log('get_argument_value: ' + name)
        if args.get(name, None) is None:
            return None
        else:
            return args.get(name, None)[0]

            
    def build_url(self, query):
        """ This will build and encode the URL for the addon. """
        log('build_url')
        return BASE_URL + '?' + urllib.urlencode(query)

        
    def build_playon_url(self, href = ""):
        """ This will generate the correct URL to access the XML pushed out by the machine running playon. """
        log('build_playon_url: '+ href)
        if not href:
            return playonInternalUrl + PLAYON_DATA
        else:
            return playonInternalUrl + href

            
    def build_playon_search_url(self, id, searchterm):
        """ Generates a search URL for the given ID. Will only work with some providers. """
        #TODO: work out the full search term criteria.
        #TODO: Check international encoding.
        searchterm = urllib.quote_plus(searchterm)
        log('build_playon_search_url: '+ id + "::" + searchterm)
        return playonInternalUrl + PLAYON_DATA + "?id=" + id + "&searchterm=dc:description%20contains%20" + searchterm
     
     
    def build_menu_for_mode_none(self):
        """
            This generates a static structure at the top of the menu tree. 
            It is the same as displayed by m.playon.tv when browsed to. 
        """
        log('build_menu_for_mode_none')
        for key, value in sorted(displayCategories.iteritems(), key=lambda (k,v): (v,k)):
            url = self.build_url({'mode': 'category', 'category':displayCategories[key]})
            image = playonInternalUrl + displayImages[key]
            self.addDir(displayTitles[key],url,image,image)   
        xbmcplugin.endOfDirectory(BASE_HANDLE, cacheToDisc=True)
 
        
    def build_menu_for_mode_category(self, category):
        """
            This generates a menu for a selected category in the main menu. 
            It uses the category value to & agains the selected category to see if it
            should be shown. 

            Pull back the whole catalog
            Sample XMl blob:
                <catalog apiVersion="1" playToAvailable="true" name="server" href="/data/data.xml?id=0" type="folder" art="/images/apple_touch_icon_precomposed.png" server="3.10.13.9930" product="PlayOn">
                    <group name="PlayMark" href="/data/data.xml?id=playmark" type="folder" childs="0" category="256" art="/images/provider.png?id=playmark" />
                    <group name="PlayLater Recordings" href="/data/data.xml?id=playlaterrecordings" type="folder" childs="0" category="256" art="/images/provider.png?id=playlaterrecordings" />
                    <group name="Netflix" href="/data/data.xml?id=netflix" type="folder" childs="0" searchable="true" id="netflix" category="3" art="/images/provider.png?id=netflix" />
                    <group name="Amazon Instant Video" href="/data/data.xml?id=amazon" type="folder" childs="0" searchable="true" id="amazon" category="3" art="/images/provider.png?id=amazon" />
                    <group name="HBO GO" href="/data/data.xml?id=hbogo" type="folder" childs="0" searchable="true" id="hbogo" category="3" art="/images/provider.png?id=hbogo" />
                    ...
        """
        try:
            log('build_menu_for_mode_category:' + category)
            ranNum = random.randrange(9)
            for group in self.get_xml(self.build_playon_url()).getiterator('group'):
                # Category number. 
                if group.attrib.get('category') == None:
                    nodeCat = 1024
                else:
                    nodeCat = group.attrib.get('category')

                # Art if there is any. 
                if group.attrib.get('art') == None:
                    image = playonInternalUrl + folderIcon(ranNum)
                else:
                    image = (playonInternalUrl + group.attrib.get('art')).replace('&size=tiny','&size=large')
                    
                # if we & them and it is not zero add it to this category. otherwise ignore as it is another category.                        
                if int(nodeCat) & int(category) != 0:
                    name = group.attrib.get('name').encode('ascii', 'ignore') #TODO: Fix for international characters.
                    url = self.build_url({'mode': group.attrib.get('type'), 
                                     'foldername': name, 
                                     'href': group.attrib.get('href'),
                                     'nametree': name})
                    self.addDir(name,url,image,image)
        except Exception,e:
            log('build_menu_for_mode_category failed! ' + str(e), xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(BASE_HANDLE, cacheToDisc=True)

            
    def build_menu_for_search(self, xml):
        """ 
            Will generate a list of directory items for the UI based on the xml values. 
            This breaks the normal name tree approach for the moment

            Results can have folders and videos. 
            
            Example XML Blob:
            http://192.168.0.140:54479/data/data.xml?id=netflix&searchterm=dc:description%20contains%20american+dad
            <group name="Netflix" href="/data/data.xml?id=netflix" type="folder" art="/images/provider.png?id=netflix" searchable="true" id="netflix" childs="0" category="3">
                <group name="American Dad!" href="/data/data.xml?id=netflix-..." type="folder" childs="0" art="/images/poster.jpg?id=netflix-...&amp;size=large" />
            </group>

            http://192.168.0.140:54479/data/data.xml?id=netflix&searchterm=dc:description%20contains%20dog

            <group name="Netflix" href="/data/data.xml?id=netflix" type="folder" art="/images/provider.png?id=netflix" searchable="true" id="netflix" childs="0" category="3">
                <group name="Clifford the Big Red Dog" href="/data/data.xml?id=netflix-..." type="folder" childs="0" art="/images/poster.jpg?id=netflix-...&amp;size=large" />
                <group name="Courage the Cowardly Dog" href="/data/data.xml?id=netflix-..." type="folder" childs="0" art="/images/poster.jpg?id=netflix-...&amp;size=large" />
                <group name="Dogs with Jobs" href="/data/data.xml?id=netflix-..." type="folder" childs="0" art="/images/poster.jpg?id=netflix-...&amp;size=large" />
                <group name="The 12 Dogs of Christmas" href="/data/data.xml?id=netflix-..." type="video" art="/images/poster.jpg?id=netflix-...&amp;size=large" />
                <group name="12 Dogs of Christmas: Great Puppy Rescue" href="/data/data.xml?id=netflix-..." type="video" art="/images/poster.jpg?id=netflix-...&amp;size=large" />
        """
        try:
            log('build_menu_for_search')
            ranNum = random.randrange(9)
            for group in xml.getiterator('group'):
                log(group.attrib.get('href'))
                # This is the top group node, just need to check if we can search. 
                if group.attrib.get('searchable') != None:
                    # We can search at this group level. Add a list item for it.
                    name  = "Search" #TODO: Localize
                    url   = self.build_url({'mode': 'search', 'id': group.attrib.get('id')})
                    image = playonInternalUrl + folderIcon(ranNum)
                    self.addDir(name,url,image,image)
                else:
                    # Build up the name tree.
                    name = group.attrib.get('name').encode('ascii', 'ignore')
                    desc = group.attrib.get('description')
                    
                    if group.attrib.get('type') == 'folder':
                        if group.attrib.get('art') == None:
                            image = playonInternalUrl + folderIcon(ranNum)
                        else:
                            image = (playonInternalUrl + group.attrib.get('art')).replace('&size=tiny','&size=large')
                            
                    elif group.attrib.get('type') == 'video':
                        if group.attrib.get('art') == None:
                            image = os.path.join(playonInternalUrl,'images','play_720.png')
                        else:
                            image = (playonInternalUrl + group.attrib.get('art')).replace('&size=tiny','&size=large')

                    url = self.build_url({'mode': group.attrib.get('type'), 
                                    'foldername': name, 
                                    'href': group.attrib.get('href'), 
                                    'image': image, 
                                    'desc': desc,
                                    'parenthref': group.attrib.get('href')}) #,'nametree': nametree + '/' + name
                    self.getMeta('null', name, desc, url, image, group.attrib.get('type'),cnt=len(xml.getiterator('group')))
        except Exception,e:
            log('build_menu_for_search failed! ' + str(e), xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(BASE_HANDLE, cacheToDisc=True)
                    
                    
    def build_menu_for_mode_folder(self, href, foldername, nametree):
        """ 
            Will generate a list of directory items for the UI based on the xml values. 

            The folder could be at any depth in the tree, if the category is searchable
            then we can render a search option. 
            
            Example XML Blob:
                <group name="Netflix" href="/data/data.xml?id=netflix" type="folder" art="/images/provider.png?id=netflix" searchable="true" id="netflix" childs="0" category="3">
                    <group name="My List" href="/data/data.xml?id=netflix-..." type="folder" childs="0" />
                    <group name="Browse Genres" href="/data/data.xml?id=netflix-..." type="folder" childs="0" />
                    <group name="Just for Kids" href="/data/data.xml?id=netflix-..." type="folder" childs="0" />
                    <group name="Top Picks for Jon" href="/data/data.xml?id=netflix-..." type="folder" childs="0" />
        """
        log("build_menu_for_mode_folder")
        ranNum = random.randrange(9)
        try:
            for group in self.get_xml(self.build_playon_url(href)).getiterator('group'):
                log(group.attrib.get('href') + href)
                # This is the top group node, just need to check if we can search. 
                if group.attrib.get('href') == href:
                    if group.attrib.get('searchable') != None:
                        # We can search at this group level. Add a list item for it. 
                        name = "Search" #TODO: Localize
                        url = self.build_url({'mode': 'search', 'id': group.attrib.get('id')})
                        self.addDir(name,url)
                else:
                    # Build up the name tree.
                    name = group.attrib.get('name').encode('ascii', 'ignore')
                    desc = group.attrib.get('description')
                    
                    if group.attrib.get('type') == 'folder':
                        if group.attrib.get('art') == None:
                            image = playonInternalUrl + folderIcon(ranNum)
                        else:
                            image = (playonInternalUrl + group.attrib.get('art')).replace('&size=tiny','&size=large')
                    elif group.attrib.get('type') == 'video':
                        if group.attrib.get('art') == None:
                            image = os.path.join(playonInternalUrl,'images','play_720.png')
                        else:
                            image = (playonInternalUrl + group.attrib.get('art')).replace('&size=tiny','&size=large') 

                    if nametree == None:
                        nametree = name
                        url = self.build_url({'mode': group.attrib.get('type'), 
                                        'foldername': name, 
                                        'href': group.attrib.get('href'), 
                                        'image': image, 
                                        'desc': desc, 
                                        'parenthref': href})
                    else:
                        url = self.build_url({'mode': group.attrib.get('type'), 
                                        'foldername': name, 
                                        'href': group.attrib.get('href'), 
                                        'image': image, 
                                        'desc': desc, 
                                        'parenthref': href, 
                                        'nametree': nametree + '/' + name})
                    self.getMeta(nametree, name, desc, url, image, group.attrib.get('type'),cnt=len(self.get_xml(self.build_playon_url(href)).getiterator('group')))
        except Exception,e:
            log('build_menu_for_mode_folder failed! ' + str(e), xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(BASE_HANDLE, cacheToDisc=True)
            
            
    def generate_list_items(self, xml, href, foldername, nametree):
        """ Will generate a list of directory items for the UI based on the xml values. """
        log("generate_list_items")
        ranNum = random.randrange(9)
        try:
            for group in xml.getiterator('group'):
                if group.attrib.get('href') == href:
                    continue
                
                # Build up the name tree.
                name = group.attrib.get('name').encode('ascii', 'ignore')
                desc = group.attrib.get('description')
                if group.attrib.get('type') == 'folder':
                    if group.attrib.get('art') == None:
                        image = playonInternalUrl + folderIcon(ranNum)
                    else:
                        image = (playonInternalUrl + group.attrib.get('art')).replace('&size=tiny','&size=large')
                        
                elif group.attrib.get('type') == 'video':
                    if group.attrib.get('art') == None:
                        image = os.path.join(playonInternalUrl,'images','play_720.png')
                    else:
                        image = ((playonInternalUrl + group.attrib.get('art')).replace('&size=tiny','&size=large')).replace('&size=tiny','&size=large')
                    
                    url  = self.build_url({'mode': group.attrib.get('type'), 
                                    'foldername': name, 
                                    'href': group.attrib.get('href'), 
                                    'parenthref': href, 
                                    'desc': desc, 
                                    'image': image, 
                                    'nametree': nametree + '/' + name})
                self.getMeta(nametree, name, desc, url, image, group.attrib.get('type'),cnt=len(xml.getiterator('group')))
        except Exception,e:
            log('generate_list_items failed! ' + str(e), xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(BASE_HANDLE, cacheToDisc=True)

        
    def parseURL(self, nametree):
        log("parseURL")
        """ 
            Run though the name tree! No restart issues but slower.
        """
        nametreelist = nametree.split('/')
        roothref = None
        for group in self.get_xml(self.build_playon_url()).getiterator('group'):
            if group.attrib.get('name') == nametreelist[0]:
                roothref = group.attrib.get('href')

        if roothref != None:
            for i, v in enumerate(nametreelist):
                log("Level:" + str(i) + " Value:" + v)
                if i != 0:
                    xml = self.get_xml(self.build_playon_url(roothref))
                    for group in xml.getiterator('group'):
                        if group.attrib.get('name') == v:
                            roothref = group.attrib.get('href')
                            type = group.attrib.get('type')
                            if type == 'video':
                                mediaNode = self.get_xml(self.build_playon_url(group.attrib.get('href'))).find('media')
                                return mediaNode.attrib.get('src'), group.attrib.get('name').encode('ascii', 'ignore'), mediaNode.attrib.get('art'), group.attrib.get('description')

                                
    def play(self, nametree, src, name, image, desc):
        log("play")
        if useUPNP == False:
            url = playonInternalUrl + '/' + src
        else:
            url = playonExternalUrl + '/' + src.split('.')[0].split('/')[0] + '/'
        self.getMeta(nametree, name, desc, url, image, 'player')


    def parseMissingMeta(self, items, type='episode'):
        log("parseMissingMeta, type = " + type)
        dur = 0
        meta = {}
        title = ((items.get('tvshowtitle','') or items.get('title','') or items.get('label','')))
        year = str(items.get('year',''))

        if type in ['episode','episodes','tvshow']:
            try:
                meta  = normalizeJson(metaget.get_meta('tvshow',  title, year=year))
                items = mergeItems(meta,items)
            except Exception,e:
                log('parseMissingMeta, get_meta(tvshow) failed! ' + str(e))
                meta  = {}
            # try:
                # meta  = artutils.get_extended_artwork(meta.get('imdb_id',''), '', type.replace('episode','episodes'))
                # items = mergeItems(meta,items)
            # except Exception,e:
                # log('parseMissingMeta, get_extended_artwork(tvshow) failed! ' + str(e))
                # meta  = {}
                
            if (int(items.get('season','0')) + int(items.get('season','0'))) > 0:
                try:
                    meta  = normalizeJson(metaget.get_episode_meta(title, '', season=items.get('season',''), episode=items.get('episode',''), episode_title=items.get('title','')))
                    items = mergeItems(meta,items)
                except Exception,e:
                    log('parseMissingMeta, get_episode_meta(tvshow) failed! ' + str(e))
                    meta  = {}
                    
        elif type == 'movie':
            try:
                meta  = normalizeJson(metaget.get_meta('movie', title, year=year))
                items = mergeItems(meta,items)
            except Exception,e:
                log('parseMissingMeta, get_meta(movie) failed! ' + str(e))
                meta  = {}
            # try:
                # meta  = artutils.get_extended_artwork(meta.get('imdb_id',''), '', type)
                # items = mergeItems(meta,items)
            # except Exception,e:
                # log('parseMissingMeta, get_extended_artwork(movie) failed! ' + str(e))
                # meta  = {}
  
        # elif type in ['songs','albums','artists','music']:
            # try:
                # meta  = artutils.get_music_artwork(artist='', album="", track="", disc="")
                # items = mergeItems(meta,items)
            # except Exception,e:
                # log('parseMissingMeta, get_music_artwork failed! ' + str(e))
                # meta  = {}
        if meta:
            items['art']['poster'] = meta.get('cover_url_url',items['art']['icon'])
            items['art']['fanart'] = meta.get('backdrop_url',items['art']['icon'])
            items['art']['banner'] = meta.get('banner_url',items['art']['icon'])
            dur = int(meta.get('duration','0') or '0')
            if len(str(dur)) <= 4:
                dur = dur * 60
            elif dur == 0 and ('Duration.Minutes' in meta or 'runtime' in meta):
                dur = int(meta.get('Duration.Minutes','') or meta.get('runtime','') or '0') * 60
        return dur, items, items['art']
           
           
    def parseSE(self, SEtitle):
        season = 0
        episode = 0
        titlepattern1 = ' '.join(SEtitle.split(' ')[1:])
        titlepattern2 = re.search('[0-9]+x[0-9]+ (.+)', SEtitle)
        titlepattern3 = re.search('s[0-9]+e[0-9]+ (.+)', SEtitle)
        titlepattern4 = SEtitle
        titlepattern = [titlepattern1,titlepattern2,titlepattern3,titlepattern4]
        
        for n in range(len(titlepattern)):
            if titlepattern[n]:
                try:
                    title = titlepattern[n].group()
                except:
                    title = titlepattern[n]
                break
        
        pattern1 = re.compile(r"""(?:s|season)(?:\s)(?P<s>\d+)(?:e|x|episode|\n)(?:\s)(?P<ep>\d+) # s 01e 02"""                 , re.VERBOSE)
        pattern2 = re.compile(r"""(?:s|season)(?P<s>\d+)(?:e|x|episode|\n)(?:\s)(?P<ep>\d+) # s01e 02"""                        , re.VERBOSE)
        pattern3 = re.compile(r"""(?:s|season)(?:\s)(?P<s>\d+)(?:e|x|episode|\n)(?P<ep>\d+) # s 01e02"""                        , re.VERBOSE)
        pattern4 = re.compile(r"""(?:s|season)(?P<s>\d+)(?:e|x|episode|\n)(?P<ep>\d+) # s01e02"""                               , re.VERBOSE)
        pattern5 = re.compile(r"""(?:s|season)(?P<s>\d+)(?:.*)(?:e|x|episode|\n)(?P<ep>\d+) # s01 random123 e02"""              , re.VERBOSE)
        pattern6 = re.compile(r"""(?:s|season)(?:\s)(?P<s>\d+)(?:.*)(?:e|x|episode|\n)(?:\s)(?P<ep>\d+) # s 01 random123 e 02""", re.VERBOSE)
        pattern7 = re.compile(r"""(?:s|season)(?:\s)(?P<s>\d+)(?:.*)(?:e|x|episode|\n)(?P<ep>\d+) # s 01 random123 e02"""       , re.VERBOSE)
        pattern8 = re.compile(r"""(?:s|season)(?P<s>\d+)(?:.*)(?:e|x|episode|\n)(?:\s)(?P<ep>\d+) # s01 random123 e 02"""       , re.VERBOSE)
        patterns = [pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7, pattern8 ]

        for idx, p in enumerate(patterns):
            m = re.search(p, SEtitle)
            if m:
                season = int( m.group('s'))
                episode = int( m.group('ep'))
        log("parseSE, return " + str(season) +', '+ str(episode)) 
        return season, episode
  
  
    def parseLabel(self, nametree, item):
        log('parseLabel, parseLabel = ' + nametree)
        title = ''
        seep = ''
        eptitle = ''
        season = 0
        episode = 0
        year = ''
        type = 'video'
        nametree = nametree.split('/')
        label = item.get('label','')
        
        # episode check 1
        try:
            title, seep, eptitle = re.compile("(.*?) - (.*?) - (.*)").match(label).groups()
            type = 'episode'
        except:
            pass
            
        # episode check 2
        try:
            season, episode, eptitle = re.compile("s(\d*)e(\d*) (.*)", re.IGNORECASE).match(label).groups()
            if eptitle.startswith('- '):
                eptitle = eptitle.replace('- ','')
            type = 'episode'
        except:
            pass
            
        if type == 'episode':
            if season == 0 and episode == 0 and len(seep) > 0:
                season, episode = self.parseSE(seep)
                
            if len(title) == 0 or 'season' in title.lower():
                if len(nametree) >= 2 and 'season' not in (nametree[len(nametree)-2]).lower():
                    title = (nametree[len(nametree)-2])
                elif 'season' not in (nametree[len(nametree)-1]) and ():
                    title = (nametree[len(nametree)-1])
                elif len(nametree) >= 3:
                    title = (nametree[len(nametree)-3])
                else:
                    title = label
                
            item['tvshowtitle'] = title
            item['title'] = eptitle
            item['season'] = season
            item['episode'] = episode  
            if season + episode > 0:
                item['label'] = (title + ' - ' + ('0' if season < 10 else '') + str(season) + 'x' + ('0' if episode < 10 else '') + str(episode) + ' - '+ (eptitle))
            else:
                item['label'] = title + ' - ' + eptitle if len(eptitle) > 0 else title
        else:
            #dirty but functional, ignore root, parse for type.
            for n in range(len(nametree)):
                if n > 0:
                    if 'movie' in nametree[n].lower() :
                        type = 'movie'
                    elif 'tv' in nametree[n].lower() :
                        type = 'episode'
                    elif 'series' in nametree[n].lower() :
                        type = 'episode'
                    elif 'shows' in nametree[n].lower() :
                        type = 'episode'
                    elif 'season' in nametree[n].lower() :
                        type = 'episode'
                    elif 'episode' in nametree[n].lower() :
                        type = 'episode'  
                        
            if type != 'video':
                try:
                    title, year = re.compile('(.+?) [(](\d{4})[)]$').findall(label)[0]
                except:
                    title = label
                item['title'] = title
                item['year'] = year
                
        item['type'] = type
        log('parseLabel, title = ' + title + ', type = ' + type)
        return item
           
            
    def getMeta(self, nametree, name, desc, url, image, mode=False, cnt=0):
        log('getMeta, mode = ' + mode)
        dur = 0
        art = {"thumb":image,"poster":image,"fanart":image,"icon":image}
        item = {"label":name,"title":name,"plot":(desc or name),"art":art}
        
        #handle regex parsing
        item = self.parseLabel(nametree,{"label":name,"title":name,"plot":(desc or name),"art":art})
        #handle metadata parsing
        dur, item, art = self.parseMissingMeta(item, item.get('type','episode'))

        #remove items not common to listitems
        item.pop('art',{})
        for key in item.keys():
            if key.lower() not in ITEM_TYPES:
                item.pop(key,{})
        for key in art.keys():
            if key.lower() not in JSON_ART:
                art.pop(key,{})
                
        if mode == 'video':
            self.addLink(name, url, image, image , item, art, cnt)
        elif mode == 'folder':
            self.addDir(name, url, image, image, item, art)
        elif mode == 'player':
            listitem = xbmcgui.ListItem(name, path=url)
            listitem.setInfo(type="video", infoLabels=item)
            listitem.setArt(art)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
        else:
            return
        
        
    def addLink(self, name, u, thumb=ICON, fanart=FANART, infoList=False, infoArt=False, total=0):
        log('addLink')
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
                
        # if kodiLibrary == True:
            # log('addLink: kodiLibrary = True')
            # contextMenu = []
            # contextMenu.append(('Create Strm','XBMC.RunPlugin(%s)'%(self.build_url({'mode': 'strmFile', 'url':u}))))
            # liz.addContextMenuItems(contextMenu)

        if infoList == False:
            liz.setInfo( type="Video", infoLabels={"label":name,"title":name} )
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
            
        if infoArt == False:
            liz.setArt({'thumb':thumb,'fanart':fanart})
        else:
            liz.setArt(infoArt)
        liz.addStreamInfo('video', {})
        xbmcplugin.addSortMethod(handle=BASE_HANDLE, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(handle=BASE_HANDLE, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addDirectoryItem(handle=BASE_HANDLE,url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, thumb=ICON, fanart=FANART, infoList=False, infoArt=False):
        log('addDir')
        
        # if kodiLibrary == True:
            # contextMenu = []
            # contextMenu.append(('Create Strms','XBMC.RunPlugin(%s)'%(self.build_url({'mode': 'strmDir', 'url':u}))))
            # liz.addContextMenuItems(contextMenu)
        
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False:
            liz.setInfo( type="Video", infoLabels={"label":name,"title":name} )
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False:
            liz.setArt({'thumb':thumb,'fanart':fanart})
        else:
            liz.setArt(infoArt)
        liz.addStreamInfo('video', {})
        xbmcplugin.addSortMethod(handle=BASE_HANDLE, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(handle=BASE_HANDLE, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addDirectoryItem(handle=BASE_HANDLE,url=u,listitem=liz,isFolder=True)

        
# Parameters    
log("Base URL:" + BASE_URL)
log("Addon Handle:" + str(BASE_HANDLE))

# Pull out the URL arguments for usage. 
mode       = Playon().get_argument_value('mode')
foldername = Playon().get_argument_value('foldername')
nametree   = Playon().get_argument_value('nametree')
href       = Playon().get_argument_value('href')
searchable = Playon().get_argument_value('searchable')
category   = Playon().get_argument_value('category')
art        = (Playon().get_argument_value('image') or ICON)
desc       = (Playon().get_argument_value('desc') or "N/A")
id         = Playon().get_argument_value('id')

playonInternalUrl = REAL_SETTINGS.getSetting("playonserver").rstrip('/')
playonExternalUrl = Playon().getUPNP().rstrip('/')
log('playonInternalUrl = ' + playonInternalUrl)
log('playonExternalUrl = ' + playonExternalUrl)

if mode is None: #building the main menu... Replicate the XML structure. 
    Playon().build_menu_for_mode_none()

elif mode == 'search':
    searchvalue = xbmcgui.Dialog().input("What are you looking for?")
    log("Search Request:" + searchvalue)
    searchurl = Playon().build_playon_search_url(id, searchvalue)
    xml = Playon().get_xml(searchurl)
    log(xml)
    Playon().build_menu_for_search(xml)

elif mode == 'category': # Category has been selected, build a list of items under that category. 
    Playon().build_menu_for_mode_category(category)

elif mode == 'folder': # General folder handling. 
    Playon().build_menu_for_mode_folder(href, foldername, nametree)

elif mode == 'video' : # Video link from Addon or STRM. Parse and play. 
    """ We are doing a manual play to handle the id change during playon restarts. """
    log("In a video:" + foldername + "::" + href +"::" + nametree)  
    if playDirect == True:
        src, name, art, desc = Playon().parseURL(nametree)  
    else:
        # Play the href directly. 
        playonUrl = Playon().build_playon_url(href)
        name = foldername.encode('ascii', 'ignore')
        mediaXml = Playon().get_xml(playonUrl)
        mediaNode = mediaXml.find('media')
        src = mediaNode.attrib.get('src')
        art = ICON
        desc = ''
    Playon().play(nametree, src, name, art, desc)  