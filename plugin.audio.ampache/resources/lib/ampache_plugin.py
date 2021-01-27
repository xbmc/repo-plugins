from future import standard_library
from future.utils import PY2
standard_library.install_aliases()
from builtins import str
from builtins import range
import xbmc,xbmcaddon,xbmcplugin,xbmcgui
import urllib.request,urllib.parse,urllib.error
import sys, os
import math,random
import xml.etree.ElementTree as ET
import threading

#main plugin
from resources.lib import ampache_connect
from resources.lib import servers_manager
from resources.lib import gui
from resources.lib import utils as ut
from resources.lib import art

# Shared resources

#addon name : plugin.audio.ampache
#do not use xbmcaddon.Addon() to avoid crashes when kore app is used ( it is
#possible to start a song without initialising the plugin
ampache = xbmcaddon.Addon("plugin.audio.ampache")

#ampache_addon_path =  ampache.getAddonInfo('path')
#ampache_dir = xbmc.translatePath( ampache_addon_path )
#if PY2:
#    ampache_dir = ampache_dir.decode('utf-8')
#BASE_RESOURCE_PATH = os.path.join( ampache_dir, 'resources' )
#mediaDir = os.path.join( BASE_RESOURCE_PATH , 'media' )
#imagepath = os.path.join( mediaDir ,'images')

def searchGui():
    dialog = xbmcgui.Dialog()
    ret = dialog.contextmenu([ut.tString(30106),ut.tString(30107),ut.tString(30108),\
                              ut.tString(30109),ut.tString(30110),ut.tString(30111)])
    endDir = False
    if ret == 0:
        endDir = do_search("artists")
    elif ret == 1:
        endDir = do_search("albums")
    elif ret == 2:
        endDir = do_search("songs")
    elif ret == 3:
        endDir = do_search("playlists")
    elif ret == 4:
        endDir = do_search("songs","search_songs")
    elif ret == 5:
        ret2 = dialog.contextmenu([ut.tString(30112),ut.tString(30113),ut.tString(30114)])
        if ret2 == 0:
            endDir = do_search("tags","tag_artists")
        elif ret2 == 1:
            endDir = do_search("tags","tag_albums")
        elif ret2 == 2:
            endDir = do_search("tags","tag_songs")

    return endDir

#return album and artist name, only album could be confusing
def get_album_artist_name(node):
    disknumber = str(node.findtext("disk"))
    if PY2:
        fullname = str(node.findtext("name"))
        fullname += u" - "
        fullname += str(node.findtext("artist"))
    else:
        #no encode utf-8 in python3, not necessary
        fullname = node.findtext("name")
        fullname += " - "
        fullname += node.findtext("artist")
    #disknumber = "None" when disk number is not sent
    if disknumber!="None" and disknumber != "1" and disknumber !="0":
        if PY2:
            fullname = fullname + u" - [ " + ut.tString(30195) + u" " +\
               disknumber + u" ]"
        else:
            fullname = fullname + " - [ " + ut.tString(30195) + " " + disknumber + " ]"
    return fullname

def getRating(rating):
    if rating:
        #converts from five stats ampache rating to ten stars kodi rating
        rating = int(float(rating)*2)
    else:
        #zero equals no rating
        rating = 0
    return rating

def get_infolabels(object_type , node):
    infoLabels = None
    rating = getRating(node.findtext("rating"))
    if object_type == 'albums':
        infoLabels = {
            'Title' : str(node.findtext("name")) ,
            'Album' : str(node.findtext("name")) ,
            'Artist' : str(node.findtext("artist")),
            'DiscNumber' : str(node.findtext("disk")),
            'Year' : node.findtext("year") ,
            'UserRating' : rating,
            'Mediatype' : 'album'
        }
 
    elif object_type == 'artists':
        infoLabels = {
            'Title' : str(node.findtext("name")) ,
            'Artist' : str(node.findtext("name")),
            'Mediatype' : 'artist'
        }

    elif object_type == 'songs':
        infoLabels = {
            'Title' : str(node.findtext("title")) ,
            'Artist' : str(node.findtext("artist")),
            'Album' :  str(node.findtext("album")),
            'Size' : node.findtext("size") ,
            'Duration' : node.findtext("time"),
            'Year' : node.findtext("year") ,
            'TrackNumber' : node.findtext("track"),
            'UserRating' : rating,
            'Mediatype' : 'song'
        }

    return infoLabels

#this function is used to speed up the loading of the images using differents
#theads, one for request
def precacheArt(elem,object_type):
    elem_type = ut.otype_to_type(object_type)
    if elem_type != "album" or elem_type != "song":
        return
    art_type = "album"
    for node in elem.iter(elem_type):
        if elem_type == "song":
            try:
                album_elem = node.find("album")
                object_id = int(album_elem.attrib["id"])
            except:
                object_id = None
        else:
            object_id = int(node.attrib["id"])
        image_url = check_get_art_url(node)
        x = threading.Thread(target=art.get_art,args=(object_id,art_type,image_url,))
        x.start()
    x.join()

def check_get_art_url(node):
    url = None
    if(int(ampache.getSetting("api-version"))) < 400001:
        url = node.findtext("art")
    return url

def getSuperId(node,elem_type):
    obj_elem = node.find(elem_type)
    obj_id = int(obj_elem.attrib["id"])
    return obj_id


#it handles albumArt and song info
def fillListItemWithSongInfo(liz,node):
    object_id = int(node.attrib["id"])
    image_url = check_get_art_url(node)
    try:
        album_id = getSuperId(node,"album")
        albumArt = art.get_art(album_id,"album",image_url)
    except:
        albumArt = art.get_art(None,"album",image_url)
    liz.setLabel(str(node.findtext("title")))
    liz.setArt( art.get_artLabels(albumArt) )
    #needed by play_track to play the song, added here to uniform api
    liz.setPath(node.findtext("url"))
    liz.setInfo( type="music", infoLabels=get_infolabels("songs", node) )
    liz.setMimeType(node.findtext("mime"))

def addLinks(elem,object_type,useCacheArt,mode):

    image = "DefaultFolder.png"
    elem_type = ut.otype_to_type(object_type)
    it=[]
    allid = set()

    for node in elem.iter(elem_type):
        cm = []
        object_id = int(node.attrib["id"])
        #xbmc.log("AmpachePlugin::addLinks: object_id  - " + str(object_id) , xbmc.LOGDEBUG )
        #xbmc.log("AmpachePlugin::addLinks: node " + ET.tostring(node) , xbmc.LOGDEBUG )

        name = str(node.findtext("name"))

        if elem_type == "album":
            try:
                #no unicode function, cause urllib quot_plus error ( bug )
                #album_id is ok also as string, cause it is needed to create
                #an url
                #remove duplicates in album names ( workaround for a problem in server comunication )
                if object_id not in allid:
                    allid.add(object_id)
                else:
                    continue
                try:
                    artist_id = getSuperId(node,"artist")
                    cm.append( ( ut.tString(30141), "Container.Update(%s?object_id=%s&mode=2)" % ( sys.argv[0],artist_id ) ) )
                except:
                    pass

                name = get_album_artist_name(node)
                if useCacheArt:
                    image_url = check_get_art_url(node)
                    image = art.get_art(object_id,elem_type,image_url)
            except:
                xbmc.log("AmpachePlugin::addLinks: album_id error", xbmc.LOGDEBUG)
        else:
            useCacheArt = False

        infoLabels=get_infolabels(object_type,node)

        if infoLabels == None:
            infoLabels={ "Title": name }

        liz=xbmcgui.ListItem(name)
        liz.setInfo( type="Music", infoLabels=infoLabels )

        if useCacheArt:
            #faster loading for libraries
            liz.setArt(  art.get_artLabels(image) )
        liz.setProperty('IsPlayable', 'false')

        if cm:
            liz.addContextMenuItems(cm)

        handle=int(sys.argv[1])

        u=sys.argv[0]+"?object_id="+str(object_id)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)
        #xbmc.log("AmpachePlugin::addLinks: u - " + u, xbmc.LOGDEBUG )
        isFolder=True
        tu= (u,liz,isFolder)
        it.append(tu)

    xbmcplugin.addDirectoryItems(handle=int(sys.argv[1]),items=it,totalItems=len(elem))

# Used to populate items for songs on XBMC. Calls plugin script with mode == 45 and object_id == (ampache song id)
# TODO: Merge with addLinks(). Same basic idea going on, this one adds links  all at once, as the other one
#       Also, some property things, some different context menu things.
def addSongLinks(elem):
   
    xbmcplugin.setContent(int(sys.argv[1]), "songs")
    ok=True
    it=[]
    for node in elem.iter("song"):
        liz=xbmcgui.ListItem()
        fillListItemWithSongInfo(liz,node)
        liz.setProperty("IsPlayable", "true")

        cm = []
        try:
            artist_id = getSuperId(node,"artist")
            cm.append( ( ut.tString(30138),
            "Container.Update(%s?object_id=%s&mode=15)" % (
                sys.argv[0],artist_id ) ) )
        except:
            pass
        
        try:
            album_id = getSuperId(node,"album")
            cm.append( ( ut.tString(30139),
            "Container.Update(%s?object_id=%s&mode=16)" % (
                sys.argv[0],album_id ) ) )
        except:
            pass
        
        song_title = str(node.findtext("title"))
        cm.append( ( ut.tString(30140),
        "Container.Update(%s?title=%s&mode=17)" % (
            sys.argv[0],song_title) ) )

        if cm != []:
            liz.addContextMenuItems(cm)

        song_url = node.findtext("url")
        song_id = int(node.attrib["id"])
        track_parameters = { "mode": 45, "song_url" : song_url, "object_id" : song_id}
        url = sys.argv[0] + '?' + urllib.parse.urlencode(track_parameters)
        tu= (url,liz)
        it.append(tu)
    
    xbmcplugin.addDirectoryItems(handle=int(sys.argv[1]),items=it,totalItems=len(elem))

#The function that actually plays an Ampache URL by using setResolvedUrl
def play_track(object_id,song_url):
    if song_url == None or object_id == None:
        xbmc.log("AmpachePlugin::play_track object or song null", xbmc.LOGNOTICE )
        return

    old_object_id = None

    #it checks if we need the song infolabels ( object_id cached is different from
    #object_id of the song, for instance as kore app call the song
    try:
            plugin_url = xbmc.getInfoLabel('ListItem.FileNameAndPath')
            params=ut.get_params(plugin_url)
            old_object_id=int(params["object_id"])
            xbmc.log("AmpachePlugin::play_track old_object_id " + str(old_object_id), xbmc.LOGDEBUG)
    except:
            pass

    liz = xbmcgui.ListItem()
    try:
        if old_object_id == None or old_object_id != object_id:
            ampConn = ampache_connect.AmpacheConnect()
            xbmc.log("AmpachePlugin::play_track refresh infoLabels", xbmc.LOGDEBUG)
            ampConn.filter = object_id
            elem = ampConn.ampache_http_request("song")
            for thisnode in elem:
                node = thisnode
            fillListItemWithSongInfo(liz,node)
            liz.setProperty("IsPlayable", "true")
    except:
        pass

    liz.setPath(song_url)
    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True,listitem=liz)

#Main function to add xbmc plugin elements
def addDir(name,object_id,mode,offset=None):
    infoLabels={ "Title": name }
    
    liz=xbmcgui.ListItem(name)
    liz.setInfo( type="Music", infoLabels=infoLabels )
    liz.setProperty('IsPlayable', 'false')

    handle=int(sys.argv[1])

    u=sys.argv[0]+"?object_id="+str(object_id)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)
    #offset, in case of very long lists
    if offset:
        u = u + "&offset="+str(offset)
    xbmc.log("AmpachePlugin::addDir url " + u, xbmc.LOGDEBUG)
    ok=xbmcplugin.addDirectoryItem(handle=handle,url=u,listitem=liz,isFolder=True)
    #xbmc.log("AmpachePlugin::addDir ok " + str(ok), xbmc.LOGDEBUG)
    return ok

#this function add items to the directory using the low level addLinks of ddSongLinks functions
def addItem( object_type, mode , elem, useCacheArt=True):
    image = "DefaultFolder.png"
    xbmc.log("AmpachePlugin::addItem: object_type - " + str(object_type) , xbmc.LOGDEBUG )

    if useCacheArt:
        precacheArt(elem,object_type)

    if object_type == 'songs':
        addSongLinks(elem)
    else:
        addLinks(elem,object_type,useCacheArt,mode)
    return

def get_all(object_type,offset=None):
    if offset == None:
        offset=0
    try:
        limit = int(ampache.getSetting(object_type))
    except:
        return
    #to not overload servers
    step = 100
    newLimit = offset+step
    #load images in long list
    if (ut.strBool_to_bool(ampache.getSetting("images-long-list"))):
        get_items(object_type, limit=step, offset=offset)
    else:
        get_items(object_type, limit=step, offset=offset, useCacheArt=False)
    if newLimit < limit:
        return newLimit
    else:
        return None

#this functions handles the majority of the requests to the server
#so, we have a lot of optional params
def get_items(object_type, object_id=None, add=None,\
        thisFilter=None,limit=5000,useCacheArt=True, object_subtype=None,\
        exact=None, offset=None ):
    
    if object_type:
        xbmc.log("AmpachePlugin::get_items: object_type " + object_type, xbmc.LOGDEBUG)
    else:
        #it should be not possible
        xbmc.log("AmpachePlugin::get_items: object_type set to None" , xbmc.LOGDEBUG)
        return

    if object_id == None and thisFilter==None:
        return

    if object_subtype:
        xbmc.log("AmpachePlugin::get_items: object_subtype " + object_subtype, xbmc.LOGDEBUG)
    if object_id:
        xbmc.log("AmpachePlugin::get_items: object_id " + str(object_id), xbmc.LOGDEBUG)

    if limit == None:
        limit = int(ampache.getSetting(object_type))
    mode = None

    xbmcplugin.setContent(int(sys.argv[1]), object_type)
    #default: object_type is the action,otherwise see the if list below
    action = object_type
    
    #do not use action = object_subtype cause in tags it is used only to
    #discriminate between subtypes
    if object_type == 'albums':
        if object_subtype == 'artist_albums':
            action = 'artist_albums'
            addDir("All Songs",object_id,12)
        elif object_subtype == 'tag_albums':
            action = 'tag_albums'
        elif object_subtype == 'album':
            action = 'album'
    elif object_type == 'artists':
        if object_subtype == 'tag_artists':
            action = 'tag_artists'
        if object_subtype == 'artist':
            action = 'artist'
    elif object_type == 'songs':
        if object_subtype == 'tag_songs':
            action = 'tag_songs'
        elif object_subtype == 'playlist_songs':
            action = 'playlist_songs'
        elif object_subtype == 'album_songs':
            action = 'album_songs'
        elif object_subtype == 'artist_songs':
            action = 'artist_songs'
        elif object_subtype == 'search_songs':
            action = 'search_songs'

    if object_id:
        thisFilter = object_id

  #set the mode 

    if object_type == 'artists':
        mode = 2
    elif object_type == 'albums':
        mode = 3
    elif object_type == 'playlists':
        mode = 14
    elif object_type == 'tags':
        if object_subtype == 'tag_artists':
            mode = 19
        elif object_subtype == 'tag_albums':
            mode = 20
        elif object_subtype == 'tag_songs':
            mode = 21

    #here the documentation for an ampache connection
    #first create the connection object
    #second choose the api function to call in action variable
    #third add params using public AmpacheConnect attributes
    #( i know, it is ugly, but python doesnt' support structs, so..., if
    #someone has a better idea, i'm open to change )
    #if the params are not set, they simply are not added to the url
    #forth call ampache_http_request if the server return an xml file
    #or ampache_binary_request if the server return a binary file (eg. an
    #image )
    #it could be very simply to add json api, but we have to rewrite all
    #function that rely on xml input, like additem
  
    try:
        ampConn = ampache_connect.AmpacheConnect()
        ampConn.add = add
        ampConn.filter = thisFilter
        ampConn.limit = limit
        ampConn.exact = exact
        ampConn.offset = offset

        elem = ampConn.ampache_http_request(action)
        addItem( object_type, mode , elem, useCacheArt)
    except:
        return


def setRating():
    try:
        file_url = xbmc.Player().getPlayingFile()
        xbmc.log("AmpachePlugin::setRating url " + file_url , xbmc.LOGDEBUG)
    except:
        xbmc.log("AmpachePlugin::no playing file " , xbmc.LOGDEBUG)
        return

    object_id = ut.get_objectId_from_fileURL( file_url )
    if object_id == None:
        pass
    rating = xbmc.getInfoLabel('MusicPlayer.UserRating')
    if rating == "":
        rating = "0"

    xbmc.log("AmpachePlugin::setRating, user Rating " + rating , xbmc.LOGDEBUG)
    #converts from five stats ampache rating to ten stars kodi rating
    amp_rating = math.ceil(int(rating)/2.0)

    ampConn = ampache_connect.AmpacheConnect()

    action = "rate"
    ampConn.id = str(object_id)
    ampConn.type = "song"
    ampConn.rating = str(amp_rating)

    elem = ampConn.ampache_http_request(action)

def do_search(object_type,object_subtype=None,thisFilter=None):
    """
    do_search(object_type,object_subtype=None,thisFilter=None) -> boolean
    requires:
    object_type : ( albums, songs... )
    object_subtype :  ( search song, tag artists )
    filter : the test to search
    return true or false, used to check if call endDirectoryItem or not
    """
    if not thisFilter:
        thisFilter = gui.getFilterFromUser()
    if thisFilter:
        get_items(object_type=object_type,thisFilter=thisFilter,object_subtype=object_subtype)
        return True
    return False

def get_stats(object_type, object_subtype=None, limit=5000 ):       
    
    ampConn = ampache_connect.AmpacheConnect()
    
    xbmc.log("AmpachePlugin::get_stats ",  xbmc.LOGDEBUG)
    mode = None
    if object_type == 'artists':
        mode = 2
    elif object_type == 'albums':
        mode = 3
   
    xbmcplugin.setContent(int(sys.argv[1]), object_type)

    action = 'stats'
    if(int(ampache.getSetting("api-version"))) < 400001:
        amtype = object_subtype
        thisFilter = None
    else:
        amtype = ut.otype_to_type(object_type)
        thisFilter = object_subtype
    
    try:
        ampConn.filter = thisFilter
        ampConn.limit = limit
        ampConn.type = amtype
                
        elem = ampConn.ampache_http_request(action)
        addItem( object_type, mode , elem)
    except:
        return

def get_recent(object_type,object_id,object_subtype=None):   

    if object_id == 9999998:
        update = ampache.getSetting("add")
        xbmc.log(update[:10],xbmc.LOGNOTICE)
        get_items(object_type=object_type,add=update[:10],object_subtype=object_subtype)
    elif object_id == 9999997:
        get_items(object_type=object_type,add=ut.get_time(-7),object_subtype=object_subtype)
    elif object_id == 9999996:
        get_items(object_type=object_type,add=ut.get_time(-30),object_subtype=object_subtype)
    elif object_id == 9999995:
        get_items(object_type=object_type,add=ut.get_time(-90),object_subtype=object_subtype)

def get_random(object_type):
    xbmc.log("AmpachePlugin::get_random: object_type " + object_type, xbmc.LOGDEBUG)
    mode = None
    #object type can be : albums, artists, songs, playlists
    
    ampConn = ampache_connect.AmpacheConnect()
    
    amtype = ut.otype_to_type(object_type)
    if object_type == 'albums':
        mode = 3
    elif object_type == 'artists':
        mode = 2
    elif object_type == 'playlists':
        mode = 14
    #song is the same mode

    xbmcplugin.setContent(int(sys.argv[1]), object_type)

    try:
        random_items = (int(ampache.getSetting("random_items"))*3)+3
        xbmc.log("AmpachePlugin::get_random: random_items " + str(random_items), xbmc.LOGDEBUG )
        items = int(ampache.getSetting(object_type))
        xbmc.log("AmpachePlugin::get_random: total items in the catalog " + str(items), xbmc.LOGDEBUG )
    except:
        return
    if random_items > items:
        #if items are less than random_itmes, return all items
        get_items(object_type, limit=items)
        return
    #playlists are not in the new stats api, so, use the old mode
    if(int(ampache.getSetting("api-version"))) >= 400001 and object_type != 'playlists':
        action = 'stats'
        thisFilter = 'random'
        try:
            ampConn.filter = thisFilter
            ampConn.limit = random_items
            ampConn.type = amtype

            elem = ampConn.ampache_http_request(action)
            addItem( object_type, mode , elem)
        except:
            return
    
    else: 
        seq = random.sample(list(range(items)),random_items)
        xbmc.log("AmpachePlugin::get_random: seq " + str(seq), xbmc.LOGDEBUG )
        elements = []
        for item_id in seq:
            try:
                ampConn.offset = item_id
                ampConn.limit = 1
                elem = ampConn.ampache_http_request(object_type)
                addItem( object_type, mode , elem)
            except:
                pass

def checkCloseMusicPlaylist(addon_url, mode, object_id=None, title=None):
    """
    this function checks if musicplaylist window is active and switchs to the music window
    necessary when we have to display albums or songs
    """
    if xbmc.getCondVisibility("Window.IsActive(musicplaylist)"):
        #close busydialog to activate music window
        #remove the line below once the busydialog bug is correct
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        xbmc.executebuiltin("ActivateWindow(music)")
        if object_id:
            xbmc.executebuiltin("Container.Update(%s?object_id=%s&mode=%s)" %\
                    ( addon_url,object_id, mode ) )
        elif title:
            xbmc.executebuiltin("Container.Update(%s?title=%s&mode=%s)" %\
                    ( addon_url,title, mode ) )


def main_params(plugin_url):
    """
    main_params(plugin_url) -> associative array
    this function extracts the params from plugin url
    and put the in an associative array
    not all params are present in url so we need to handle it with exceptions
    """
    m_params={}
    m_params['mode'] = None
    m_params['object_id'] = None
    m_params['title'] = None
    #used only in play tracks
    m_params['song_url'] = None
    #used to managed very long lists
    m_params['offset'] = None

    params=ut.get_params(plugin_url)

    try:
            m_params['mode']=int(params["mode"])
            xbmc.log("AmpachePlugin::mode " + str(m_params['mode']), xbmc.LOGDEBUG)
    except:
            pass
    try:
            m_params['object_id']=int(params["object_id"])
            xbmc.log("AmpachePlugin::object_id " + str(m_params['object_id']), xbmc.LOGDEBUG)
    except:
            pass
    try:
            m_params['title']=urllib.parse.unquote_plus(params["title"])
            xbmc.log("AmpachePlugin::title " + m_params['title'], xbmc.LOGDEBUG)
    except:
            pass
    try:
            m_params['song_url']=urllib.parse.unquote_plus(params["song_url"])
            xbmc.log("AmpachePlugin::song_url " + m_params['song_url'], xbmc.LOGDEBUG)
    except:
            pass
    try:
            m_params['offset']=int(params["offset"])
            xbmc.log("AmpachePlugin::offset " + str(m_params['offset']), xbmc.LOGDEBUG)
    except:
            pass

    return m_params

def manage_get_all(object_type, mode ,offset):
    new_offset=get_all(object_type,offset)
    if new_offset:
        addDir(ut.tString(30194),None,mode,new_offset)

#add new line in case of new stat function implemented, checking the version
#in menus
def manage_stats_menu(object_id, object_type, num_items):
    if object_id == 9999993:
        get_stats(object_type=object_type,object_subtype="highest",limit=num_items)
    elif object_id == 9999992:
        get_stats(object_type=object_type,object_subtype="frequent",limit=num_items)
    elif object_id == 9999991:
        get_stats(object_type=object_type,object_subtype="flagged",limit=num_items)
    elif object_id == 9999990:
        get_stats(object_type=object_type,object_subtype="forgotten",limit=num_items)
    elif object_id == 9999989:
        get_stats(object_type=object_type,object_subtype="newest",limit=num_items)
    elif object_id == 9999988:
        get_stats(object_type=object_type,object_subtype="recent",limit=num_items)

def Main():

    mode=None
    object_id=None
    #sometimes we need to not endDirectory, but
    #we need to check if the connection is alive
    #until endDirectoryMode -> endDirectoy and checkConnection
    #from endDirectoryMode to endCheckConnection  -> no endDirectory but checkConnection
    #else no end and no check
    endDirectoryMode = 40
    endCheckConnection = 50
    modeMax = 100
    endDir = True

    addon_url = sys.argv[0]
    handle = int(sys.argv[1])
    plugin_url=sys.argv[2]

    xbmc.log("AmpachePlugin::init handle: " + str(handle) + " url: " + plugin_url, xbmc.LOGDEBUG)

    m_params=main_params(plugin_url)
    #faster to change variable
    mode = m_params['mode']
    object_id = m_params['object_id']

    servers_manager.initializeServer()
    
    ampacheConnect = ampache_connect.AmpacheConnect()

    #check if the connection is expired
    #connect to the server
    #do not connect on main screen and when we operate setting; 
    #do not block the main screen in case the connection to a server it is not available and we kwow it
    if mode!=None and mode < endCheckConnection:
        if ut.check_tokenexp():
            try:
                ampacheConnect.AMPACHECONNECT()
            except:
                pass

    #start menu
    if mode==None:
        #search
        addDir(ut.tString(30101),None,4)
        #quick access
        addDir(ut.tString(30102),None,25)
        #explore
        addDir(ut.tString(30103),None,23)
        #library
        addDir(ut.tString(30104),None,24)
        #switch server
        addDir(ut.tString(30023),None,54)
        #settings
        addDir(ut.tString(30105),None,50)
        
    #artist mode ( called from search screen ( mode 4 ), recent ( mode 5 )  )
    #and others
    elif mode==1:
        #artist, album, songs, playlist follow the same structure
        #search function
        num_items = (int(ampache.getSetting("random_items"))*3)+3
        #get all artists
        if object_id == None:
            manage_get_all("artists", mode ,m_params['offset'])
            #get_items("artists", limit=None, useCacheArt=False)
        elif object_id == 9999999:
            endDir = do_search("artists")
        #recent function
        elif object_id > 9999994 and object_id < 9999999:
            get_recent( "artists", object_id )
        elif object_id == 9999994:
            #removed cause nasty recursive call using some commands in web interface
            #addDir("Refresh..",9999994,2,os.path.join(imagepath,'refresh_icon.png'))
            #get random is separated from stats to mantain compatibility with
            #older ampache api
            get_random('artists')
        #object_id between 99..93 e 99..88 ( highest .. recent )
        elif object_id >= 9999988 and object_id <=9999993:
            manage_stats_menu(object_id, "artists", num_items)
    
    
    #albums mode ( called from search screen ( mode 4 ) , recent ( mode 5 )
    #and others
    elif mode==2:
        num_items = (int(ampache.getSetting("random_items"))*3)+3
        #get all albums
        if object_id == None:
            manage_get_all("albums", mode ,m_params['offset'])
            #get_items("albums", limit=None, useCacheArt=False)
        elif object_id == 9999999:
            endDir = do_search("albums")
        elif object_id > 9999994 and object_id < 9999999:
            get_recent( "albums", object_id )
        elif object_id == 9999994:
            #removed cause nasty recursive call using some commands in web interface
            #addDir("Refresh..",9999990,2,os.path.join(imagepath, 'refresh_icon.png'))
            get_random('albums')
        elif object_id >= 9999988 and object_id <=9999993:
            manage_stats_menu(object_id, "albums", num_items)
        elif object_id:
            get_items(object_type="albums",object_id=object_id,object_subtype="artist_albums")

    #song mode ( called from search screen ( mode 4 ) and recent ( mode 5 )  )
    #and others
    elif mode == 3:
        num_items = (int(ampache.getSetting("random_items"))*3)+3
        if object_id == None:
            #handle wrong object_id
            pass
        elif object_id > 9999994 and object_id < 9999999:
            get_recent( "songs", object_id )
        elif object_id == 9999999:
            endDir = do_search("songs")
        elif object_id == 9999994:
            #removed cause nasty recursive call using some commands in web interface
            #addDir("Refresh..",9999994,2,os.path.join(imagepath, 'refresh_icon.png'))
            get_random('songs')
        elif object_id >= 9999988 and object_id <=9999993:
            manage_stats_menu(object_id, "songs", num_items)
        else:
            get_items(object_type="songs",object_id=object_id,object_subtype="album_songs")

    #search mode
    elif mode==4:
        if not (ut.strBool_to_bool(ampache.getSetting("old-search-gui"))):
            endDir = searchGui()
        else:
            addDir(ut.tString(30120),9999999,1)
            addDir(ut.tString(30121),9999999,2)
            addDir(ut.tString(30122),9999999,3)
            addDir(ut.tString(30123),9999999,13)
            addDir(ut.tString(30124),9999999,11)
            addDir(ut.tString(30125),9999999,18)


    # recently added screen
    elif mode==5:
        addDir(ut.tString(30126),9999998,6)
        addDir(ut.tString(30127),9999997,6)
        addDir(ut.tString(30128),9999996,6)
        addDir(ut.tString(30129),9999995,6)

    #screen with recent time possibilities ( subscreen of recent artists,
    #recent albums, recent songs ) ( called from mode 5 )
    elif mode==6:
        #not clean, but i don't want to change too much the old code
        if object_id > 9999995:
            #object_id for playlists is 9999995 so 9999999-object_id is 4 that is search mode
            #i have to use another method, so i use the hardcoded mode number (13)
            mode_new = 9999999-object_id
        elif object_id == 9999995:
            mode_new = 13
        
        addDir(ut.tString(30130),9999998,mode_new)
        addDir(ut.tString(30131),9999997,mode_new)
        addDir(ut.tString(30132),9999996,mode_new)
        addDir(ut.tString(30133),9999995,mode_new)

    #general random mode screen
    elif mode==7:
        addDir(ut.tString(30134),9999994,1)
        addDir(ut.tString(30135),9999994,2)
        addDir(ut.tString(30136),9999994,3)
        addDir(ut.tString(30137),9999994,13)

    # mode 11 : search all
    elif mode==11:
        endDir = do_search("songs","search_songs")

    # mode 12 : artist_songs
    elif mode==12:
        get_items(object_type="songs",object_id=object_id,object_subtype="artist_songs" )

    #playlist full list
    elif mode==13:
        if object_id == None:
            manage_get_all("playlists", mode ,m_params['offset'])
            #get_items(object_type="playlists")
        elif object_id == 9999999:
            endDir = do_search("playlists")
        elif object_id > 9999994 and object_id < 9999999:
            get_recent( "playlists", object_id )
        elif object_id == 9999994:
            #removed cause nasty recursive call using some commands in web interface
            #addDir("Refresh..",9999994,2,os.path.join(imagepath, 'refresh_icon.png'))
            get_random('playlists')
        elif object_id:
            get_items(object_type="playlists",object_id=object_id)

    #playlist song mode
    elif mode==14:
        get_items(object_type="songs",object_id=object_id,object_subtype="playlist_songs")

    elif mode==15:
        checkCloseMusicPlaylist(addon_url, mode, object_id=object_id )
        get_items(object_type="artists",object_id=object_id,object_subtype="artist")

    elif mode==16:
        checkCloseMusicPlaylist(addon_url, mode, object_id=object_id )
        get_items(object_type="albums",object_id=object_id,object_subtype="album")

    elif mode==17:
        checkCloseMusicPlaylist(addon_url, mode, object_id=object_id )
        endDir = do_search("songs",thisFilter=m_params['title'])

    #tags
    elif mode==18:
        addDir(ut.tString(30142),object_id,19)
        addDir(ut.tString(30143),object_id,20)
        addDir(ut.tString(30144),object_id,21)

    elif mode==19:
        if object_id == 9999999:
            endDir = do_search("tags","tag_artists")
        elif object_id:
            get_items(object_type="artists", object_subtype="tag_artists",object_id=object_id)
        else:
            get_items(object_type = "tags", object_subtype="tag_artists")

    elif mode==20:
        if object_id == 9999999:
            endDir = do_search("tags","tag_albums")
        elif object_id:
            get_items(object_type="albums", object_subtype="tag_albums",object_id=object_id)
        else:
            get_items(object_type = "tags", object_subtype="tag_albums")

    elif mode==21:
        if object_id == 9999999:
            endDir = do_search("tags","tag_songs")
        elif object_id:
            get_items(object_type="songs", object_subtype="tag_songs",object_id=object_id)
        else:
            get_items(object_type = "tags", object_subtype="tag_songs")

    #explore
    elif mode==23:
        addDir(ut.tString(30145),None,5)
        addDir(ut.tString(30146),None,7)
        if(int(ampache.getSetting("api-version"))) >= 400001:
            addDir(ut.tString(30148),9999993,30)
            addDir(ut.tString(30164),9999992,31)
            addDir(ut.tString(30165),9999991,32)
            addDir(ut.tString(30166),9999990,33)
            addDir(ut.tString(30167),9999989,34)
            addDir(ut.tString(30193),9999988,35)

    #Library
    elif mode==24:
        addDir(ut.tString(30115) +" (" + ampache.getSetting("artists")+ ")",None,1)
        addDir(ut.tString(30116) + " (" + ampache.getSetting("albums") + ")",None,2)
        addDir(ut.tString(30118) + " (" + ampache.getSetting("playlists")+ ")",None,13)
        apiVersion = int(ampache.getSetting("api-version"))
        if apiVersion >= 380001:
            addDir(ut.tString(30119),None,18)

    #quick access
    elif mode==25:
        addDir(ut.tString(30135),9999994,2)
        if(int(ampache.getSetting("api-version"))) >= 400001:
            addDir(ut.tString(30162),9999989,2)
            addDir(ut.tString(30153),9999992,2)
            addDir(ut.tString(30191),9999988,2)
        else:
            #use recently added for old api versions
            addDir(ut.tString(30127),9999997,6)
        addDir(ut.tString(30147),9999994,3)

    #highest
    elif mode==30:
        addDir(ut.tString(30149),9999993,1)
        addDir(ut.tString(30150),9999993,2)
        addDir(ut.tString(30151),9999993,3)

    #frequent
    elif mode==31:
        addDir(ut.tString(30152),9999992,1)
        addDir(ut.tString(30153),9999992,2)
        addDir(ut.tString(30154),9999992,3)
    
    #flagged
    elif mode==32:
        addDir(ut.tString(30155),9999991,1)
        addDir(ut.tString(30156),9999991,2)
        addDir(ut.tString(30157),9999991,3)

    #forgotten
    elif mode==33:
        addDir(ut.tString(30158),9999990,1)
        addDir(ut.tString(30159),9999990,2)
        addDir(ut.tString(30160),9999990,3)
    
    #newest
    elif mode==34:
        addDir(ut.tString(30161),9999989,1)
        addDir(ut.tString(30162),9999989,2)
        addDir(ut.tString(30163),9999989,3)
    
    #recent
    elif mode==35:
        addDir(ut.tString(30190),9999988,1)
        addDir(ut.tString(30191),9999988,2)
        addDir(ut.tString(30192),9999988,3)

    #play track mode  ( mode set in add_links function )
    #mode 45 to avoid endDirectory
    elif mode==45:
        #workaround busydialog bug
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        play_track(object_id, m_params['song_url'])

    #change rating
    elif mode==47:
        setRating()

    #settings
    elif mode==50:
        ampache.openSettings()

    #the four modes below are used to manage servers
    elif mode==51:
        if servers_manager.addServer():
            servers_manager.switchServer()
    
    elif mode==52:
        if servers_manager.deleteServer():
            servers_manager.switchServer()
    
    elif mode==53:
        servers_manager.modifyServer()
    
    elif mode==54:
        servers_manager.switchServer()

    #no end directory item ( problem with failed searches )
    #endDir is the result of the search function
    if endDir == False:
        mode = modeMax

    if mode == None or mode < endDirectoryMode:
        xbmc.log("AmpachePlugin::endOfDirectory " + str(handle),  xbmc.LOGDEBUG)
        xbmcplugin.endOfDirectory(handle)


