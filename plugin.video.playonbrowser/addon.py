import sys
import urlparse
import urllib
import urllib2
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import string
import htmllib
import os
import platform
import random
import calendar
import re
import CommonFunctions
import xml.etree.ElementTree as ElementTree 
#from addon.common.net import Net
#from metahandler import metahandlers

try:
    import StorageServer
    Cache_Enabled = True
except Exception,e:
    import storageserverdummy as StorageServer
    Cache_Enabled = False

# 
#   Set-up global variables
addon = xbmcaddon.Addon()
addonId = 'plugin.video.playonbrowser'
addonVersion = '1.0.2'
addonId = addon.getAddonInfo('id')
mediaPath = xbmcaddon.Addon(addonId).getAddonInfo('path') + '/resources/media/' 
playonDataPath = '/data/data.xml'
displayCategories = {'MoviesAndTV': 3,
                        'News': 4,
                        'Sports': 8,
                        'Kids': 16,
                        'Music': 32,
                        'VideoSharing': 64,
                        'Comedy': 128,
                        'MyMedia': 256,
                        'Plugins': 512,
                        'Other': 1024,
                        'LiveTV': 2048}
displayTitles = {'MoviesAndTV': 'Movies And TV',
                    'News': 'News',
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
                    'Sports': '/images/categories/sports.png',
                    'Kids': '/images/categories/kids.png',
                    'Music': '/images/categories/music.png',
                    'VideoSharing': '/images/categories/videosharing.png',
                    'Comedy': '/images/categories/comedy.png',
                    'MyMedia': '/images/categories/mymedia.png',
                    'Plugins': '/images/categories/plugins.png',
                    'Other': '/images/categories/other.png',
                    'LiveTV': '/images/categories/livetv.png'}

#
#   Pull the arguments in. 
baseUrl = sys.argv[0]
addonHandle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

#
#   Pull the settings in. 
settings = xbmcaddon.Addon(id=addonId)
playonInternalUrl = settings.getSetting("playonserver").rstrip('/')
debug = settings.getSetting("debug")
cachePeriod = 1 #hours

#
#   Set-up some KODI defaults. 
xbmcplugin.setContent(addonHandle, 'movies')
common = CommonFunctions
common.plugin = addonId + '-' + addonVersion

#
#   Internal Functions 
#
def log_message(msg, information=False):
    """ Simple logging helper. """
    if (information or debug) and isinstance(msg, str):
        print addonId + "::" + addonVersion + ": " + msg
    elif (information or debug):
        print addonId + "::" + addonVersion + ":  ... \/ ..."
        print msg
        
def build_url(query):
    """ This will build and encode the URL for the addon. """
    log_message(query)
    return baseUrl + '?' + urllib.urlencode(query)

def build_playon_url(href = ""):
    """ This will generate the correct URL to access the XML pushed out by the machine running playon. """
    log_message('build_playon_url: '+ href)
    if not href:
        return playonInternalUrl + playonDataPath
    else:
        return playonInternalUrl + href

def build_playon_search_url(id, searchterm):
    """ Generates a search URL for the given ID. Will only work with some providers. """
    log_message('build_playon_search_url: '+ id + "::" + searchterm)
    #TODO: work out the full search term criteria.
    #TODO: Check international encoding.
    searchterm = urllib.quote_plus(searchterm)
    log_message('build_playon_search_url: '+ id + "::" + searchterm)
    return playonInternalUrl + playonDataPath + "?id=" + id + "&searchterm=dc:description%20contains%20" + searchterm

    
def get_xml(url):
    if Cache_Enabled == True:  
        commoncache = StorageServer.StorageServer("plugin.video.playonbrowser",cachePeriod)
        try:
            result = commoncache.cacheFunction(get_xml_request, url)
        except:
            result = get_xml_request(url)
            pass
    else:
        result = get_xml_request(url)
    if not result:
        result = False
    return result  
    
    
def get_xml_request(url):
    """ This will pull down the XML content and return a ElementTree. """
    try:
        log_message('get_xml: ' + url)
        usock = urllib2.urlopen(url)
        response = usock.read()
        usock.close()
        return ElementTree.fromstring(response)
    except: return False 

def get_argument_value(name):
    """ pulls a value out of the passed in arguments. """
    if args.get(name, None) is None:
        return None
    else:
        return args.get(name, None)[0]

def build_menu_for_mode_none():
    """
        This generates a static structure at the top of the menu tree. 
        It is the same as displayed by m.playon.tv when browsed to. 
    """
    log_message('build_menu_for_mode_none')
    
    for key, value in sorted(displayCategories.iteritems(), key=lambda (k,v): (v,k)):
        url = build_url({'mode': 'category', 'category':displayCategories[key]})
        image = playonInternalUrl + displayImages[key]
        li = xbmcgui.ListItem(displayTitles[key], iconImage=image, thumbnailImage=image)
        xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
    
    xbmcplugin.endOfDirectory(addonHandle)

def build_menu_for_mode_category(category):
    """
        This generates a menu for a selected category in the main menu. 
        It uses the category value to & agains the selected category to see if it
        should be shown. 
    """
    log_message('build_menu_for_mode_category:' + category)
    """ Pull back the whole catalog
        Sample XMl blob:
            <catalog apiVersion="1" playToAvailable="true" name="server" href="/data/data.xml?id=0" type="folder" art="/images/apple_touch_icon_precomposed.png" server="3.10.13.9930" product="PlayOn">
                <group name="PlayMark" href="/data/data.xml?id=playmark" type="folder" childs="0" category="256" art="/images/provider.png?id=playmark" />
                <group name="PlayLater Recordings" href="/data/data.xml?id=playlaterrecordings" type="folder" childs="0" category="256" art="/images/provider.png?id=playlaterrecordings" />
                <group name="Netflix" href="/data/data.xml?id=netflix" type="folder" childs="0" searchable="true" id="netflix" category="3" art="/images/provider.png?id=netflix" />
                <group name="Amazon Instant Video" href="/data/data.xml?id=amazon" type="folder" childs="0" searchable="true" id="amazon" category="3" art="/images/provider.png?id=amazon" />
                <group name="HBO GO" href="/data/data.xml?id=hbogo" type="folder" childs="0" searchable="true" id="hbogo" category="3" art="/images/provider.png?id=hbogo" />
                ...
    """

    playonUrl = build_playon_url()
    xml = get_xml(playonUrl)

    for group in xml.getiterator('group'):

        # Category number. 
        if group.attrib.get('category') == None:
            nodeCat = 1024
        else:
            nodeCat = group.attrib.get('category')

        # Art if there is any. 
        if group.attrib.get('art') == None:
            image = 'DefaultVideo.png'
        else:
            image = playonInternalUrl + group.attrib.get('art')

        # if we & them and it is not zero add it to this category. otherwise ignore as it is another category.                        
        if int(nodeCat) & int(category) != 0:
            name = group.attrib.get('name').encode('ascii', 'ignore') #TODO: Fix for international characters.
            url = build_url({'mode': group.attrib.get('type'), 
                             'foldername': name, 
                             'href': group.attrib.get('href'), 
                             'nametree': name})
            li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
                
    xbmcplugin.endOfDirectory(addonHandle)

def build_menu_for_search(xml):
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

    for group in xml.getiterator('group'):
        log_message(group.attrib.get('href'))
        # This is the top group node, just need to check if we can search. 
        if group.attrib.get('searchable') != None:
            # We can search at this group level. Add a list item for it. 
            name = "Search" #TODO: Localize
            url = build_url({'mode': 'search', 'id': group.attrib.get('id')})
            li = xbmcgui.ListItem(name)
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
        else:
        
            # Build up the name tree.
            name = group.attrib.get('name').encode('ascii', 'ignore')
            url = build_url({'mode': group.attrib.get('type'), 
                                'foldername': name, 
                                'href': group.attrib.get('href'), 
                                'parenthref': group.attrib.get('href')}) #,                                 'nametree': nametree + '/' + name

            if group.attrib.get('art') == None:
                image = 'DefaultVideo.png'
            else:
                image = playonInternalUrl + group.attrib.get('art')
            
            if group.attrib.get('type') == 'folder':
                li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
                xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
            
            elif group.attrib.get('type') == 'video':
                playonUrl = build_playon_url(group.attrib.get('href'))
                mediaXml = get_xml(playonUrl)
                mediaNode = mediaXml.find('media')
                li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
                li.setProperty('IsPlayable', 'true')
                li.setInfo('video', { 'plotoutline': group.attrib.get('description'), 'title': name})
                xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li)
            
    xbmcplugin.endOfDirectory(addonHandle)

def build_menu_for_mode_folder(href, foldername, nametree):
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

    log_message("Entering build_menu_for_mode_folder")
    playonUrl = build_playon_url(href)
    xml = get_xml(playonUrl)

    for group in xml.getiterator('group'):
        log_message(group.attrib.get('href') + href)
        # This is the top group node, just need to check if we can search. 
        if group.attrib.get('href') == href:
            if group.attrib.get('searchable') != None:
                # We can search at this group level. Add a list item for it. 
                name = "Search" #TODO: Localize
                url = build_url({'mode': 'search', 'id': group.attrib.get('id')})
                li = xbmcgui.ListItem(name)
                xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
        else:
        
            # Build up the name tree.
            name = group.attrib.get('name').encode('ascii', 'ignore')
            if nametree == None:
                url = build_url({'mode': group.attrib.get('type'), 
                                'foldername': name, 
                                'href': group.attrib.get('href'), 
                                'parenthref': href})
            else:
                url = build_url({'mode': group.attrib.get('type'), 
                                'foldername': name, 
                                'href': group.attrib.get('href'), 
                                'parenthref': href, 
                                'nametree': nametree + '/' + name})
            
            log_message("url = " + url)

            if group.attrib.get('art') == None:
                image = 'DefaultVideo.png'
            else:
                image = playonInternalUrl + group.attrib.get('art')
            
            if group.attrib.get('type') == 'folder':
                """
                try:
                    
                    metaget = metahandlers.MetaData()
                    meta = metaget.get_meta('tvshow', name)
                
                    li = xbmcgui.ListItem(name, iconImage=meta['cover_url'], thumbnailImage=meta['cover_url'])
                    li.setInfo(type="Video", infoLabels=meta)
                    li.setProperty('fanart_image', meta['backdrop_url'])
                    xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
                except Exception,e:
                """
                #log_message(str(e))
                li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
                xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
            
            elif group.attrib.get('type') == 'video':
                playonUrl = build_playon_url(group.attrib.get('href'))
                mediaXml = get_xml(playonUrl)
                mediaNode = mediaXml.find('media')
                """
                try:
                    
                    metaget = metahandlers.MetaData()
                    meta = metaget.get_meta('movie', name)
                
                    li = xbmcgui.ListItem(name, iconImage=meta['cover_url'], thumbnailImage=meta['cover_url'])
                    li.setInfo(type="Video", infoLabels=meta)
                    li.setProperty('fanart_image', meta['backdrop_url'])
                    xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li)
                except Exception,e:
                    log_message(str(e))
                    """
                li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
                li.setInfo('video', { 'plotoutline': group.attrib.get('description'), 'title': name})
                li.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li)
     
            
    xbmcplugin.endOfDirectory(addonHandle)

def generate_list_items(xml, href, foldername, nametree):
    """ Will generate a list of directory items for the UI based on the xml values. """
    for group in xml.getiterator('group'):
        if group.attrib.get('href') == href:
            continue
        
        # Build up the name tree. 
        name = group.attrib.get('name').encode('ascii', 'ignore')
        url = build_url({'mode': group.attrib.get('type'), 
                            'foldername': name, 
                            'href': group.attrib.get('href'), 
                            'parenthref': href, 
                            'nametree': nametree + '/' + name})
        
        if group.attrib.get('art') == None:
            image = 'DefaultVideo.png'
        else:
            image = playonInternalUrl + group.attrib.get('art')
            
        if group.attrib.get('type') == 'folder':
            li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
        elif group.attrib.get('type') == 'video':
            playonUrl = build_playon_url(group.attrib.get('href'))
            mediaXml = get_xml(playonUrl)
            mediaNode = mediaXml.find('media')
            li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
            li.setProperty('IsPlayable', 'true')
            li.setInfo('video', { 'plotoutline': group.attrib.get('description'), 'title': name})
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li)
            
    xbmcplugin.endOfDirectory(addonHandle)


#
#    Main Loop

log_message("Base URL:" + baseUrl, True)
log_message("Addon Handle:" + str(addonHandle), True)
log_message("Arguments", True)
log_message(args, True)

# Pull out the URL arguments for usage. 
mode = get_argument_value('mode')
foldername = get_argument_value('foldername')
nametree = get_argument_value('nametree')
href = get_argument_value('href')
searchable = get_argument_value('searchable')
category = get_argument_value('category')
id = get_argument_value('id')

if mode is None: #building the main menu... Replicate the XML structure. 
    build_menu_for_mode_none()

elif mode == 'search':
    searchvalue = xbmcgui.Dialog().input("What are you looking for?")
    log_message("Search Request:" +searchvalue)
    if (log_message != ""):
        searchurl = build_playon_search_url(id, searchvalue)
        xml = get_xml(searchurl)
        log_message(xml)
        build_menu_for_search(xml)

elif mode == 'category': # Category has been selected, build a list of items under that category. 
    build_menu_for_mode_category(category)

elif mode == 'folder': # General folder handling. 
    build_menu_for_mode_folder(href, foldername, nametree)

elif mode == 'video' : # Video link from Addon or STRM. Parse and play. 
    """ We are doing a manual play to handle the id change during playon restarts. """
    log_message("In a video:" + foldername + "::" + href )
    # Run though the name tree! No restart issues but slower.
    playonUrl = build_playon_url()
    xml = get_xml(playonUrl)

    if nametree == None:
        # Play the href directly. 
        playonUrl = build_playon_url(href)
        name = foldername.encode('ascii', 'ignore')
        mediaXml = get_xml(playonUrl)
        mediaNode = mediaXml.find('media')
        src = mediaNode.attrib.get('src')
        url =  playonInternalUrl + '/' + src
        vplaylist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
        vplaylist.clear()
        vplaylist.add(mediaPath + 'DummyEntry.mp4')
        vplaylist.add(url)
        listitem=xbmcgui.ListItem (name)
        xbmc.Player().stop()
        xbmc.sleep(50)
        xbmc.Player().play(vplaylist,listitem)
        xbmc.sleep(50)
        xbmc.executebuiltin("ActivateWindow('fullscreenvideo')")
    else:
        nametreelist = nametree.split('/')
        roothref = None
        for group in xml.getiterator('group'):
            if group.attrib.get('name') == nametreelist[0]:
                roothref = group.attrib.get('href')

        if roothref != None:
            for i, v in enumerate(nametreelist):
                log_message("Level:" + str(i) + " Value:" + v)
                if i != 0:
                    playonUrl = build_playon_url(roothref)
                    xml = get_xml(playonUrl)
                    for group in xml.getiterator('group'):
                        if group.attrib.get('name') == v:
                            roothref = group.attrib.get('href')
                            type = group.attrib.get('type')
                            if type == 'video':
                                # End of tree! I thinks. 
                                playonUrl = build_playon_url(group.attrib.get('href'))
                                name = group.attrib.get('name').encode('ascii', 'ignore')
                                mediaXml = get_xml(playonUrl)
                                mediaNode = mediaXml.find('media')
                                src = mediaNode.attrib.get('src')
                                url =  playonInternalUrl + '/' + src
                                vplaylist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
                                vplaylist.clear()
                                vplaylist.add(mediaPath + 'DummyEntry.mp4')
                                vplaylist.add(url)
                                listitem=xbmcgui.ListItem (name)
                                xbmc.Player().stop()
                                xbmc.sleep(50)
                                xbmc.Player().play(vplaylist,listitem)
                                xbmc.sleep(50)
                                xbmc.executebuiltin("ActivateWindow('fullscreenvideo')")
        

        

