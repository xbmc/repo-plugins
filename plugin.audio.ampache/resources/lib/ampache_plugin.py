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

class AmpMode:
    """Enumeration of all possible modes"""

    ARTISTS = 1
    ALBUMS = 2
    SONGS = 3
    PLAYLISTS = 4
    PODCASTS =5
    LIVE_STREAMS=6
    VIDEOS = 8
    TAG_ARTISTS = 19
    TAG_ALBUMS =20
    TAG_SONGS=21
    EXPLORE=50
    LIBRARY=51
    QUICK_ACCESS=52
    SEARCH_MODE=53
    SEARCH_TAGS=54
    RECENTLY_ADDED=55
    RANDOM=100
    HIGHEST=101
    FREQUENT=102
    FLAGGED=103
    FORGOTTEN=104
    NEWEST=105
    RECENTLY_LISTENED=106
    RECENTLY_ADDED_MENU=107
    END_DIRECTORY=200
    #server menu
    SET_RATINGS=205
    END_CHECK_CONNECTION = 299
    SETTINGS=300
    ADD_SERVER=301
    DELETE_SERVER=302
    MODIFY_SERVER=303
    SWITCH_SERVER=304
    CLEAN_CACHE_ART=400
    MAX=1000

class AmpSubmode:
    """Enumeration of all possible submodes"""
    ARTISTS = 1
    ALBUMS = 2
    SONGS = 3
    PLAYLISTS = 4
    GET_ALL=5
    GET_PARENT_ITEM=6
    DO_SEARCH=10
    DO_SEARCH_ALL=11
    DO_SEARCH_ITEM=12
    LAST_UPDATE = 31
    WEEK_UPDATE = 32
    MONTH_UPDATE = 33
    THREE_MONTH_UPDATE = 34
    RANDOM=40
    HIGHEST=41
    FREQUENT=42
    FLAGGED=43
    FORGOTTEN=44
    NEWEST=45
    RECENT=46
    GET_ALL_SUBITEMS=71
    GET_ALL_ARTISTS_SONGS=72

def searchGui():
    dialog = xbmcgui.Dialog()
    ret = dialog.contextmenu([ut.tString(30106),ut.tString(30107),ut.tString(30108),\
                              ut.tString(30109),ut.tString(30110),ut.tString(30220),ut.tString(30225),ut.tString(30228),ut.tString(30111)])
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
        endDir = do_search("videos")
    elif ret == 6:
        endDir = do_search("podcasts")
    elif ret == 7:
        endDir = do_search("songs","live_streams")
    elif ret == 8:
        ret2 = dialog.contextmenu([ut.tString(30112),ut.tString(30113),ut.tString(30114)])
        if(int(ampache.getSetting("api-version"))) < 500000:
            if ret2 == 0:
                endDir = do_search("tags","tag_artists")
            elif ret2 == 1:
                endDir = do_search("tags","tag_albums")
            elif ret2 == 2:
                endDir = do_search("tags","tag_songs")
        else:
            if ret2 == 0:
                endDir = do_search("genres","genre_artists")
            elif ret2 == 1:
                endDir = do_search("genres","genre_albums")
            elif ret2 == 2:
                endDir = do_search("genres","genre_songs")
    return endDir

#necessary due the api changes in 6.0
def get_name(node,amType):
    if(int(ampache.getSetting("api-version"))) < 600000:
        artist_name = str(node.findtext(amType))
    else:
        artist_name = str(getNestedTypeText(node, "name" ,amType))
    return artist_name

#return album and artist name, only album could be confusing
def get_album_artist_name(node):

    disknumber = str(node.findtext("disk"))
    album_name = str(node.findtext("name"))
    artist_name = get_name(node,"artist")
    fullname = album_name
    
    if PY2:
        fullname += u" - "
    else:
        #no encode utf-8 in python3, not necessary
        fullname += " - "
    fullname += artist_name
    #disknumber = "None" when disk number is not sent
    if disknumber!="None" and disknumber != "1" and disknumber !="0":
        if PY2:
            fullname = fullname + u" - [ " + ut.tString(30195) + u" " +\
               disknumber + u" ]"
        else:
            fullname = fullname + " - [ " + ut.tString(30195) + " " + disknumber + " ]"
    return fullname

def fill_tags(elem_type , node, info_tag):
    rating = ut.getRating(node.findtext("rating"))

    if elem_type == 'song':
        info_tag.setMediaType('song')
        info_tag.setTitle(str(node.findtext("title")))
        info_tag.setArtist(get_name(node,"artist"))
        info_tag.setAlbum(get_name(node,"album"))
        duration_str = node.findtext("time")
        info_tag.setDuration(int(duration_str) if duration_str else 0)
        year_str = node.findtext("year")
        info_tag.setYear(int(year_str) if year_str else None)
        track_num = node.findtext("track")
        info_tag.setTrack(int(track_num) if track_num else 0)
        info_tag.setUserRating(rating)

    elif elem_type == 'album':
        info_tag.setMediaType('album')
        info_tag.setAlbum(str(node.findtext("name")))
        info_tag.setArtist(get_name(node, "artist"))
        disc_num = node.findtext("disk")
        #xbmc.log("AmpachePlugin::disc_num " + str(disc_num),  xbmc.LOGDEBUG)
        info_tag.setDisc(int(disc_num) if disc_num else 0)
        year_str = node.findtext("year")
        info_tag.setYear(int(year_str) if year_str else None)
        info_tag.setUserRating(rating)

    elif elem_type == 'artist':
        info_tag.setMediaType('artist')
        info_tag.setArtist(str(node.findtext("name")))

    elif elem_type == 'podcast_episode':
        info_tag.setMediaType('song')
        info_tag.setTitle(str(node.findtext("title")))
        info_tag.setUserRating(rating)

    elif elem_type == 'video':
        info_tag.setMediaType('video')
        info_tag.setTitle(str(node.findtext("name")))


def getNestedTypeText(node, elem_tag ,elem_type):
    try:
        obj_elem = node.find(elem_type)
        if obj_elem is not None or obj_elem != '':
            obj_tag = obj_elem.findtext(elem_tag)
            return obj_tag
    except:
        return None
    return None

def getNestedTypeId(node,elem_type):
    try:
        obj_elem = node.find(elem_type)
        if obj_elem is not None or obj_elem != '':
            obj_id = obj_elem.attrib["id"]
            return obj_id
    except:
        return None
    return None

#this function is used to speed up the loading of the images using differents
#theads, one for request
def precacheArt(elem,elem_type):

    allid=set()
    if elem_type != "album" and elem_type != "song" and\
            elem_type != "artist" and elem_type != "podcast" and elem_type!= "playlist":
        return

    threadList = []
    for node in elem.iter(elem_type):
        if elem_type == "song":
            art_type = "album"
            object_id = getNestedTypeId(node, "album")
        else:
            art_type = elem_type
            object_id = node.attrib["id"]
        #avoid to have duplicate threads with the same object_id
        if object_id not in allid:
            allid.add(object_id)
        else:
            continue
        image_url = node.findtext("art")
        if not object_id or not image_url:
            continue
        x = threading.Thread(target=art.get_art,args=(object_id,art_type,image_url,))
        threadList.append(x)
    #start threads
    for x in threadList:
        x.start()
    #join threads
    for x in threadList:
        x.join()

def addLinks(elem,elem_type,useCacheArt,mode):

    image = "DefaultFolder.png"
    it=[]
    allid = set()

    for node in elem.iter(elem_type):
        cm = []
        object_id = node.attrib["id"]
        if not object_id:
            continue

        name = str(node.findtext("name"))

        if elem_type == "album":
            #remove duplicates in album names ( workaround for a problem in server comunication )
            if object_id not in allid:
                allid.add(object_id)
            else:
                continue
            artist_id = getNestedTypeId(node, "artist")
            if artist_id:
                cm.append( ( ut.tString(30141),"Container.Update(%s?object_id=%s&mode=%s&submode=%s)" %
                    ( sys.argv[0],artist_id, str(AmpMode.ARTISTS), str(AmpSubmode.GET_PARENT_ITEM ) ) ) )
            name = get_album_artist_name(node)
            if useCacheArt:
                image_url = node.findtext("art")
                image = art.get_art(object_id,elem_type,image_url)
        elif elem_type == "artist":
            if useCacheArt:
                image_url = node.findtext("art")
                image = art.get_art(object_id,elem_type,image_url)
        elif elem_type == "podcast":
            if useCacheArt:
                image = art.get_art(object_id,"podcast")
        elif elem_type == "playlist":
            if useCacheArt:
                image = art.get_art(object_id,"playlist")
            try:
                numItems = str(node.findtext("items"))
                name = name + " (" + numItems + ")"
            except:
                pass
        else:
            useCacheArt = False

        liz=xbmcgui.ListItem(name)

        if elem_type == "album" or elem_type=="artist":
            info_tag = liz.getMusicInfoTag()
            fill_tags(elem_type, node, info_tag)


        if useCacheArt:
            #faster loading for libraries
            liz.setArt(  art.get_artLabels(image) )
        liz.setProperty('IsPlayable', 'false')

        if cm:
            liz.addContextMenuItems(cm)

        #AmpSubmode.GET_ALL_SUBITEMS ( 71 )
        u=sys.argv[0]+"?object_id="+object_id+"&mode="+str(mode)+"&submode="+str(AmpSubmode.GET_ALL_SUBITEMS)
        #xbmc.log("AmpachePlugin::addLinks: u - " + u, xbmc.LOGDEBUG )
        isFolder=True
        tu= (u,liz,isFolder)
        it.append(tu)

    xbmcplugin.addDirectoryItems(handle=int(sys.argv[1]),items=it,totalItems=len(elem))

# Used to populate items for songs on XBMC. Calls plugin script with mode ==
# 45 and play_url == (ampache item url)
def addPlayLinks(elem, elem_type):
   
    it=[]

    #we don't use sort method for track cause songs are already sorted
    #by the server and it make a mess in random playlists
    if elem_type == "video":
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
    elif elem_type == "podcast_episode":
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_DATE)

    allid=set()
    albumTrack={}

    for node in elem.iter(elem_type):
        object_id = node.attrib["id"]
        if not object_id:
            continue

        play_url = str(node.findtext("url"))
        object_title = str(node.findtext("title"))
        if elem_type == "live_stream":
            object_title = str(node.findtext("name"))

        liz=xbmcgui.ListItem(object_title)
        liz.setProperty("IsPlayable", "true")
        liz.setPath(play_url)

        if elem_type == "song":
            image_url = node.findtext("art")
            #speed up art management for album songs, avoid duplicate
            #calls
            album_id = getNestedTypeId(node,"album")
            if album_id:
                if album_id not in allid:
                    allid.add(album_id)
                    albumArt = art.get_art(album_id,"album",image_url)
                    albumTrack[album_id]=albumArt
                else:
                    albumArt=albumTrack[album_id]
            else:
                albumArt = art.get_art(None,"album",image_url)
            liz.setArt( art.get_artLabels(albumArt) )
            info_tag = liz.getMusicInfoTag()
            fill_tags("song", node, info_tag)
            liz.setMimeType(node.findtext("mime"))

            cm = []

            artist_id = getNestedTypeId(node, "artist")
            if artist_id:
                cm.append( ( ut.tString(30138),
                "Container.Update(%s?object_id=%s&mode=%s&submode=%s)" % (
                    sys.argv[0],artist_id, str(AmpMode.ARTISTS), str(AmpSubmode.GET_PARENT_ITEM ) ) ) )

            if album_id:
                cm.append( ( ut.tString(30139),
                "Container.Update(%s?object_id=%s&mode=%s&submode=%s)" % (
                    sys.argv[0],album_id, str(AmpMode.ALBUMS), str(AmpSubmode.GET_PARENT_ITEM ) ) ) )

            cm.append( ( ut.tString(30140),
            "Container.Update(%s?title=%s&mode=%s&submode=%s)" % (
                sys.argv[0],urllib.parse.quote_plus(object_title), str(AmpMode.SONGS), str(AmpSubmode.DO_SEARCH_ITEM) ) ) )

            if cm != []:
                liz.addContextMenuItems(cm)
        elif elem_type == "podcast_episode":
            info_tag = liz.getMusicInfoTag()
            fill_tags("podcast_episode", node, info_tag)
        elif elem_type == "video":
            info_tag = liz.getVideoInfoTag()
            fill_tags("video", node, info_tag)
            liz.setMimeType(node.findtext("mime"))

        track_parameters = { "mode": str(AmpMode.END_DIRECTORY), "play_url" : play_url}
        url = sys.argv[0] + '?' + urllib.parse.urlencode(track_parameters)
        tu= (url,liz)
        it.append(tu)

    xbmcplugin.addDirectoryItems(handle=int(sys.argv[1]),items=it,totalItems=len(elem))

#The function that actually plays an Ampache URL by using setResolvedUrl
def play_track(url):
    if url == None:
        xbmc.log("AmpachePlugin::play_track url null", xbmc.LOGINFO )
        return

    #read here the setting, cause delay problems
    autofull = ut.strBool_to_bool(ampache.getSetting("auto-fullscreen"))

    liz = xbmcgui.ListItem()
    liz.setPath(url)

    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True,listitem=liz)

    #enable auto fullscreen playing the track ( closes #17 )
    if autofull is True:
        xbmc.executebuiltin("ActivateWindow(visualisation)")

#Main function to add xbmc plugin elements
def addDir(name,mode,submode,offset=None,object_id=None):
    
    liz=xbmcgui.ListItem(name)
    liz.setProperty('IsPlayable', 'false')

    handle=int(sys.argv[1])

    u=sys.argv[0]+"?mode="+str(mode)+"&submode="+str(submode)
    #offset, in case of very long lists
    if offset:
        u = u + "&offset="+str(offset)
    if object_id:
        u = u + "&object_id="+object_id
    xbmc.log("AmpachePlugin::addDir url " + u, xbmc.LOGDEBUG)
    xbmcplugin.addDirectoryItem(handle=handle,url=u,listitem=liz,isFolder=True)

#this function add items to the directory using the low level addLinks of ddSongLinks functions
def addItems( object_type, elem, object_subtype=None,precache=True):

    ut.setContent(int(sys.argv[1]), object_type)

    xbmc.log("AmpachePlugin::addItems: object_type - " + str(object_type) , xbmc.LOGDEBUG )
    if object_subtype:
        xbmc.log("AmpachePlugin::addItems: object_subtype - " + str(object_subtype) , xbmc.LOGDEBUG )

    elem_type = ut.otype_to_type(object_type,object_subtype)
    xbmc.log("AmpachePlugin::addItems: elem_type - " + str(elem_type) , xbmc.LOGDEBUG )

    useCacheArt = True

    if elem_type != "song":
        limit = len(elem.findall(elem_type))
        if limit > 100:
            #to not overload servers
            if (not ut.strBool_to_bool(ampache.getSetting("images-long-list"))):
                useCacheArt = False

    if useCacheArt and precache:
        precacheArt(elem,elem_type)

    if object_type == 'songs' or object_type == 'videos':
        addPlayLinks(elem,elem_type)
    else:
        #set the mode
        mode = ut.otype_to_mode(object_type, object_subtype)
        addLinks(elem,elem_type,useCacheArt,mode)
    return

def get_all(object_type, mode ,offset=None):
    if offset == None:
        offset=0
    try:
        limit = int(ampache.getSetting(object_type))
        if limit == 0:
            return
    except:
        return

    step = 500
    newLimit = offset+step
    get_items(object_type, limit=step, offset=offset)
    if newLimit < limit:
        pass
    else:
        newLimit = None

    if newLimit:
        addDir(ut.tString(30194),mode, str(AmpSubmode.GET_ALL),offset=newLimit)

#this functions handles the majority of the requests to the server
#so, we have a lot of optional params
def get_items(object_type, object_id=None, add=None,\
        thisFilter=None,limit=5000, object_subtype=None,\
        exact=None, offset=None ):
    
    if object_type:
        xbmc.log("AmpachePlugin::get_items: object_type " + object_type, xbmc.LOGDEBUG)
    else:
        #it should be not possible
        xbmc.log("AmpachePlugin::get_items: object_type set to None" , xbmc.LOGDEBUG)
        return

    if object_subtype:
        xbmc.log("AmpachePlugin::get_items: object_subtype " + object_subtype, xbmc.LOGDEBUG)

    #object_id could be None in some requests, like recently added and get_all
    #items
    if object_id:
        xbmc.log("AmpachePlugin::get_items: object_id " + object_id, xbmc.LOGDEBUG)

    if limit == None:
        limit = int(ampache.getSetting(object_type))

    #default: object_type is the action,otherwise see the if list below
    action = object_type
    
    artist_action_subtypes = [
    'artist_albums','tag_albums','genre_albums','album']

    album_action_subtypes = [ 'tag_artists','genre_artists','artist']

    song_action_subtypes = [ 'tag_songs','genre_songs', 'playlist_songs',
            'album_songs', 'artist_songs','search_songs',
            'podcast_episodes','live_streams']

    #do not use action = object_subtype cause in tags it is used only to
    #discriminate between subtypes
    if object_type == 'albums':
        if object_subtype == 'artist_albums':
            addDir("All Songs",AmpMode.ARTISTS,AmpSubmode.GET_ALL_ARTISTS_SONGS, object_id=object_id)
        #do not use elif, artist_albums is checked two times
        if object_subtype in artist_action_subtypes:
            action = object_subtype
    elif object_type == 'artists':
        if object_subtype in album_action_subtypes:
            action = object_subtype
    elif object_type == 'songs':
        if object_subtype in song_action_subtypes:
            action = object_subtype

    if object_id:
        thisFilter = object_id

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
    #function that rely on xml input, like additems
  
    try:
        ampConn = ampache_connect.AmpacheConnect()
        ampConn.add = add
        ampConn.filter = thisFilter
        ampConn.limit = limit
        ampConn.exact = exact
        ampConn.offset = offset

        elem = ampConn.ampache_http_request(action)
        addItems( object_type, elem, object_subtype)
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
    if not object_id:
        return
    rating = xbmc.getInfoLabel('MusicPlayer.UserRating')
    if rating == "":
        rating = "0"

    xbmc.log("AmpachePlugin::setRating, user Rating " + rating , xbmc.LOGDEBUG)
    #converts from five stats ampache rating to ten stars kodi rating
    amp_rating = math.ceil(int(rating)/2.0)

    try:
        ampConn = ampache_connect.AmpacheConnect()

        action = "rate"
        ampConn.id = object_id
        ampConn.type = "song"
        ampConn.rating = str(amp_rating)

        ampConn.ampache_http_request(action)
    except:
        #do nothing
        return

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

    xbmc.log("AmpachePlugin::get_stats ",  xbmc.LOGDEBUG)

    action = 'stats'
    if(int(ampache.getSetting("api-version"))) < 400001:
        amtype = object_subtype
        thisFilter = None
    else:
        amtype = ut.otype_to_type(object_type)
        thisFilter = object_subtype

    try:
        ampConn = ampache_connect.AmpacheConnect()

        ampConn.filter = thisFilter
        ampConn.limit = limit
        ampConn.type = amtype
                
        elem = ampConn.ampache_http_request(action)
        addItems( object_type, elem)
    except:
        return

def get_recent(object_type,submode,object_subtype=None):

    if submode == AmpSubmode.LAST_UPDATE:
        update = ampache.getSetting("add")
        xbmc.log(update[:10],xbmc.LOGINFO)
        get_items(object_type=object_type,add=update[:10],object_subtype=object_subtype)
    elif submode == AmpSubmode.WEEK_UPDATE:
        get_items(object_type=object_type,add=ut.get_time(-7),object_subtype=object_subtype)
    elif submode == AmpSubmode.MONTH_UPDATE:
        get_items(object_type=object_type,add=ut.get_time(-30),object_subtype=object_subtype)
    elif submode == AmpSubmode.THREE_MONTH_UPDATE:
        get_items(object_type=object_type,add=ut.get_time(-90),object_subtype=object_subtype)

def get_random(object_type, num_items):
    #object type can be : albums, artists, songs, playlists
    
    tot_items = int(ampache.getSetting(object_type))

    xbmc.log("AmpachePlugin::get_random: object_type " + object_type + " num_items " + str(num_items) + " tot_items " +\
            str(tot_items), xbmc.LOGDEBUG)

    if num_items > tot_items:
        #if tot_items are less than num_itmes, return all items
        get_items(object_type, limit=tot_items)
        return

    seq = random.sample(list(range(tot_items)),num_items)
    action = object_type
    xbmc.log("AmpachePlugin::get_random: seq " + str(seq), xbmc.LOGDEBUG )
    ampConn = ampache_connect.AmpacheConnect()
    for item_id in seq:
        try:
            ampConn.offset = item_id
            ampConn.limit = 1
            elem = ampConn.ampache_http_request(action)
            addItems( object_type, elem,precache=False)
        except:
            pass

def switchFromMusicPlaylist(addon_url, mode, submode, object_id=None, title=None):
    """
    this function checks if musicplaylist window is active and switchs to the music window
    necessary when we have to call a function like "get album from this
    artist"
    """
    if xbmc.getCondVisibility("Window.IsActive(musicplaylist)"):
        #close busydialog to activate music window
        #remove the line below once the busydialog bug is correct
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        xbmc.executebuiltin("ActivateWindow(music)")
        if object_id:
            xbmc.executebuiltin("Container.Update(%s?object_id=%s&mode=%s&submode=%s)" %\
                    ( addon_url,object_id, mode, submode ) )
        elif title:
            xbmc.executebuiltin("Container.Update(%s?title=%s&mode=%s&submode=%s)" %\
                    ( addon_url,title, mode, submode ) )


def main_params(plugin_url):
    """
    main_params(plugin_url) -> associative array
    this function extracts the params from plugin url
    and put the in an associative array
    not all params are present in url so we need to handle it with exceptions
    """
    m_params={}
    m_params['mode'] = None
    m_params['submode'] = None
    m_params['object_id'] = None
    m_params['title'] = None
    #used only in play tracks
    m_params['play_url'] = None
    #used to managed very long lists
    m_params['offset'] = None

    params=ut.get_params(plugin_url)

    try:
            m_params['mode']=int(params["mode"])
            xbmc.log("AmpachePlugin::mode " + str(m_params['mode']), xbmc.LOGDEBUG)
    except:
            pass
    try:
            m_params['submode']=int(params["submode"])
            xbmc.log("AmpachePlugin::submode " + str(m_params['submode']), xbmc.LOGDEBUG)
    except:
            pass
    try:
            m_params['object_id']=params["object_id"]
            xbmc.log("AmpachePlugin::object_id " + m_params['object_id'], xbmc.LOGDEBUG)
    except:
            pass
    try:
            m_params['title']=urllib.parse.unquote_plus(params["title"])
            xbmc.log("AmpachePlugin::title " + m_params['title'], xbmc.LOGDEBUG)
    except:
            pass
    try:
            m_params['play_url']=urllib.parse.unquote_plus(params["play_url"])
            xbmc.log("AmpachePlugin::play_url " + m_params['play_url'], xbmc.LOGDEBUG)
    except:
            pass
    try:
            m_params['offset']=int(params["offset"])
            xbmc.log("AmpachePlugin::offset " + str(m_params['offset']), xbmc.LOGDEBUG)
    except:
            pass

    return m_params

#add new line in case of new stat function implemented, checking the version
#in menus
def manage_stats_menu(object_type,submode):

    num_items = (int(ampache.getSetting("random_items"))*3)+3
    apiVersion = int(ampache.getSetting("api-version"))

    if submode == AmpSubmode.RANDOM:
        #playlists are not in the new stats api, so, use the old mode
        if(apiVersion < 400001 or (object_type == 'playlists' and apiVersion < 510000 )):
            get_random(object_type, num_items)
        else:
            get_stats(object_type=object_type,object_subtype="random",limit=num_items)
    elif submode == AmpSubmode.HIGHEST:
        get_stats(object_type=object_type,object_subtype="highest",limit=num_items)
    elif submode == AmpSubmode.FREQUENT:
        get_stats(object_type=object_type,object_subtype="frequent",limit=num_items)
    elif submode == AmpSubmode.FLAGGED:
        get_stats(object_type=object_type,object_subtype="flagged",limit=num_items)
    elif submode == AmpSubmode.FORGOTTEN:
        get_stats(object_type=object_type,object_subtype="forgotten",limit=num_items)
    elif submode == AmpSubmode.NEWEST:
        get_stats(object_type=object_type,object_subtype="newest",limit=num_items)
    elif submode == AmpSubmode.RECENT:
        get_stats(object_type=object_type,object_subtype="recent",limit=num_items)

def Main():

    mode=None
    object_id=None
    #sometimes we need to not endDirectory, but
    #we need to check if the connection is alive
    #until END_DIRECTORY -> endDirectory and checkConnection
    #from END_DIRECTORY to END_CHECK_CONNECTION  -> no endDirectory but checkConnection
    #else no end and no check
    endDir = True

    addon_url = sys.argv[0]
    handle = int(sys.argv[1])
    plugin_url=sys.argv[2]

    xbmc.log("AmpachePlugin::init handle: " + str(handle) + " url: " + plugin_url, xbmc.LOGDEBUG)

    m_params=main_params(plugin_url)
    #faster to change variable
    mode = m_params['mode']
    submode = m_params['submode']
    object_id = m_params['object_id']

    #check if the connection is expired
    #connect to the server
    #do not connect on main screen and when we operate setting; 
    #do not block the main screen in case the connection to a server it is not available and we kwow it
    if mode!=None and mode < AmpMode.END_CHECK_CONNECTION:
        if ut.check_tokenexp():
            try:
                #check server file only when necessary
                servers_manager.initializeServer()
                ampacheConnect = ampache_connect.AmpacheConnect()
                ampacheConnect.AMPACHECONNECT()
            except:
                pass

    apiVersion = int(ampache.getSetting("api-version"))

    #start menu
    if mode==None:
        #search
        addDir(ut.tString(30101),AmpMode.SEARCH_MODE,None)
        #quick access
        addDir(ut.tString(30102),AmpMode.QUICK_ACCESS,None)
        #explore
        addDir(ut.tString(30103),AmpMode.EXPLORE,None)
        #library
        addDir(ut.tString(30104),AmpMode.LIBRARY,None)
        #switch server
        addDir(ut.tString(30023),AmpMode.SWITCH_SERVER,None)
        #settings
        addDir(ut.tString(30105),AmpMode.SETTINGS,None)
        
    #artist mode
    elif mode==AmpMode.ARTISTS:
        #artist, album, songs, playlist follow the same structure
        #get all artists
        if submode == AmpSubmode.GET_ALL:
            get_all("artists", mode ,m_params['offset'])
        #get the artist from this album's artist_id
        elif submode == AmpSubmode.GET_PARENT_ITEM:
            switchFromMusicPlaylist(addon_url, mode, submode, object_id=object_id )
            get_items(object_type="artists",object_id=object_id,object_subtype="artist")
        #search function
        #10-30 search
        elif submode == AmpSubmode.DO_SEARCH:
            endDir = do_search("artists")
        #recent function
        #30-40 recent
        elif submode >= AmpSubmode.LAST_UPDATE and submode <= AmpSubmode.THREE_MONTH_UPDATE:
            get_recent( "artists", submode )
        #submode between 40-46( random.. recent )
        #40-70 stats
        elif submode >= AmpSubmode.RANDOM and submode <= AmpSubmode.RECENT:
            manage_stats_menu("artists",submode)
        #get all albums from an artist_id
        elif submode == AmpSubmode.GET_ALL_SUBITEMS:
            get_items(object_type="albums",object_id=object_id,object_subtype="artist_albums")
        #get all songs from an artist_id
        elif submode == AmpSubmode.GET_ALL_ARTISTS_SONGS:
            get_items(object_type="songs",object_id=object_id,object_subtype="artist_songs" )
    
    
    #albums mode
    elif mode==AmpMode.ALBUMS:
        #get all albums
        if submode == AmpSubmode.GET_ALL:
            get_all("albums", mode ,m_params['offset'])
        #get the album from the song's album_id
        elif submode == AmpSubmode.GET_PARENT_ITEM:
            switchFromMusicPlaylist(addon_url, mode, submode, object_id=object_id )
            get_items(object_type="albums",object_id=object_id,object_subtype="album")
        elif submode == AmpSubmode.DO_SEARCH:
            endDir = do_search("albums")
        elif submode >= AmpSubmode.LAST_UPDATE and submode <= AmpSubmode.THREE_MONTH_UPDATE:
            get_recent( "albums", submode )
        elif submode >= AmpSubmode.RANDOM and submode <= AmpSubmode.RECENT:
            manage_stats_menu("albums",submode)
        #get all songs from an album_id
        elif submode == AmpSubmode.GET_ALL_SUBITEMS:
            get_items(object_type="songs",object_id=object_id,object_subtype="album_songs")

    #song mode
    elif mode == AmpMode.SONGS:
        #10-30 search
        if submode == AmpSubmode.DO_SEARCH:
            endDir = do_search("songs")
        # submode 11 : search all
        elif submode == AmpSubmode.DO_SEARCH_ALL:
            endDir = do_search("songs","search_songs")
        #get all song with this title
        elif submode == AmpSubmode.DO_SEARCH_ITEM:
            switchFromMusicPlaylist(addon_url, mode,submode,title=m_params['title'] )
            endDir = do_search("songs",thisFilter=m_params['title'])
        #30-40 recent
        elif submode >= AmpSubmode.LAST_UPDATE and submode <= AmpSubmode.THREE_MONTH_UPDATE:
            get_recent( "songs", submode )
        #40-70 stats
        elif submode >= AmpSubmode.RANDOM and submode <= AmpSubmode.RECENT:
            manage_stats_menu("songs",submode)

    #playlist mode
    elif mode==AmpMode.PLAYLISTS:
        if submode == AmpSubmode.GET_ALL:
            get_all("playlists", mode ,m_params['offset'])
        elif submode == AmpSubmode.DO_SEARCH:
            endDir = do_search("playlists")
        elif submode >= AmpSubmode.LAST_UPDATE and submode <= AmpSubmode.THREE_MONTH_UPDATE:
            get_recent( "playlists", submode )
        elif submode == AmpSubmode.RANDOM:
            manage_stats_menu("playlists", submode)
        #get all songs from a playlist_id
        elif submode == AmpSubmode.GET_ALL_SUBITEMS:
            get_items(object_type="songs",object_id=object_id,object_subtype="playlist_songs")

    #podcasts
    elif mode==AmpMode.PODCASTS:
        if submode == AmpSubmode.GET_ALL:
            get_all("podcasts", mode ,m_params['offset'])
        elif submode == AmpSubmode.DO_SEARCH:
            endDir = do_search("podcasts")
        #get all episodes
        elif submode == AmpSubmode.GET_ALL_SUBITEMS:
            if apiVersion >= 440000:
                get_items(object_type="songs",object_id=object_id,object_subtype="podcast_episodes")

    #live_streams
    elif mode==AmpMode.LIVE_STREAMS:
        if submode == AmpSubmode.DO_SEARCH:
            endDir = do_search("songs","live_streams")
        #get all streams
        elif submode == AmpSubmode.GET_ALL_SUBITEMS:
            if apiVersion >= 440000:
                get_items(object_type="songs",object_id=object_id,object_subtype="live_streams")

    #video
    elif mode==AmpMode.VIDEOS:
        if submode == AmpSubmode.GET_ALL:
            get_all("videos", mode ,m_params['offset'])
        elif submode == AmpSubmode.DO_SEARCH:
            endDir = do_search("videos")

    #19-21 tags/genres mode
    elif mode>=AmpMode.TAG_ARTISTS  and mode <=AmpMode.TAG_SONGS:
        object_type, object_subtype = ut.mode_to_tags(mode)
        #get_all tags/genres
        if submode == AmpSubmode.GET_ALL:
            get_items(object_type = object_type, object_subtype=object_subtype)
        #search tag/genre
        elif submode == AmpSubmode.DO_SEARCH:
            endDir = do_search(object_type,object_subtype)
        #get all songs from a tag_id/genre_id
        elif submode == AmpSubmode.GET_ALL_SUBITEMS:
            if mode == AmpMode.TAG_ARTISTS:
                get_items(object_type="artists", object_subtype=object_subtype,object_id=object_id)
            elif mode == AmpMode.TAG_ALBUMS:
                get_items(object_type="albums", object_subtype=object_subtype,object_id=object_id)
            elif mode == AmpMode.TAG_SONGS:
                get_items(object_type="songs", object_subtype=object_subtype,object_id=object_id)

    #main menus 50-100
    #explore
    elif mode==AmpMode.EXPLORE:
        #recently added
        addDir(ut.tString(30145),AmpMode.RECENTLY_ADDED_MENU,None)
        #random
        addDir(ut.tString(30146),AmpMode.RANDOM,None)
        if apiVersion >= 400001:
            #highest
            addDir(ut.tString(30148),AmpMode.HIGHEST,None)
            #frequent
            addDir(ut.tString(30164),AmpMode.FREQUENT,None)
            #flagged
            addDir(ut.tString(30165),AmpMode.FLAGGED,None)
            #forgotten
            addDir(ut.tString(30166),AmpMode.FORGOTTEN,None)
            #newest
            addDir(ut.tString(30167),AmpMode.NEWEST,None)
            #recently listened
            addDir(ut.tString(30193),AmpMode.RECENTLY_LISTENED,None)

    #Library
    elif mode==AmpMode.LIBRARY:
        addDir(ut.tString(30115) +" (" + ampache.getSetting("artists")+ ")",AmpMode.ARTISTS, AmpSubmode.GET_ALL)
        addDir(ut.tString(30116) + " (" + ampache.getSetting("albums") + ")",AmpMode.ALBUMS, AmpSubmode.GET_ALL)
        addDir(ut.tString(30118) + " (" + ampache.getSetting("playlists")+ ")",AmpMode.PLAYLISTS, AmpSubmode.GET_ALL)
        if ampache.getSetting("videos"):
            addDir(ut.tString(30221) + " (" + ampache.getSetting("videos")+ ")",AmpMode.VIDEOS, AmpSubmode.GET_ALL)
        if ampache.getSetting("podcasts"):
            addDir(ut.tString(30226) + " (" + ampache.getSetting("podcasts")+ ")",AmpMode.PODCASTS, AmpSubmode.GET_ALL)
        if ampache.getSetting("live_streams"):
            addDir(ut.tString(30229) + " (" +
                    ampache.getSetting("live_streams")+ ")",AmpMode.LIVE_STREAMS,AmpSubmode.GET_ALL_SUBITEMS)
        if apiVersion >= 380001:
            #get all tags ( submode 5 )
            addDir(ut.tString(30119),AmpMode.SEARCH_TAGS, AmpSubmode.GET_ALL)

    #quick access
    elif mode==AmpMode.QUICK_ACCESS:
        #random album
        addDir(ut.tString(30135),AmpMode.ALBUMS,AmpSubmode.RANDOM)
        if apiVersion >= 400001:
            #newest albums
            addDir(ut.tString(30162),AmpMode.ALBUMS,AmpSubmode.NEWEST)
            #frequent albums
            addDir(ut.tString(30153),AmpMode.ALBUMS, AmpSubmode.FREQUENT)
            #recently played albums
            addDir(ut.tString(30191),AmpMode.ALBUMS,AmpSubmode.RECENT)
        else:
            #use recently added albums for old api versions
            addDir(ut.tString(30127),AmpMode.RECENTLY_ADDED,AmpSubmode.ALBUMS)
        #server playlist ( AKA random songs )
        addDir(ut.tString(30147),AmpMode.SONGS,AmpSubmode.RANDOM)

    #search mode
    elif mode==AmpMode.SEARCH_MODE:
        if not (ut.strBool_to_bool(ampache.getSetting("old-search-gui"))):
            endDir = searchGui()
        else:
            #old search gui
            #search artist
            addDir(ut.tString(30120),AmpMode.ARTISTS,AmpSubmode.DO_SEARCH)
            #search album
            addDir(ut.tString(30121),AmpMode.ALBUMS,AmpSubmode.DO_SEARCH)
            #search song
            addDir(ut.tString(30122),AmpMode.SONGS,AmpSubmode.DO_SEARCH)
            #search playlist
            addDir(ut.tString(30123),AmpMode.PLAYLISTS,AmpSubmode.DO_SEARCH)
            #search all
            addDir(ut.tString(30124),AmpMode.SONGS,AmpSubmode.DO_SEARCH_ALL)
            #search tag
            addDir(ut.tString(30125),AmpMode.SEARCH_TAGS,AmpSubmode.DO_SEARCH)
            #search video
            addDir(ut.tString(30222),AmpMode.VIDEOS,AmpSubmode.DO_SEARCH)
            #search podcast
            addDir(ut.tString(30227),AmpMode.PODCASTS,AmpSubmode.DO_SEARCH)
            #search live_streams
            addDir(ut.tString(30230),AmpMode.LIVE_STREAMS,AmpSubmode.DO_SEARCH)

    #search tags
    elif mode==AmpMode.SEARCH_TAGS:
        #search tag_artist
        addDir(ut.tString(30142),AmpMode.TAG_ARTISTS,submode)
        #search tag_album
        addDir(ut.tString(30143),AmpMode.TAG_ALBUMS,submode)
        #search tag_song
        addDir(ut.tString(30144),AmpMode.TAG_SONGS,submode)

    #screen with recent time possibilities ( subscreen of recent artists,
    #recent albums, recent songs )
    elif mode==AmpMode.RECENTLY_ADDED:
        if( submode == AmpSubmode.ARTISTS):
            mode_new = AmpMode.ARTISTS
        elif( submode == AmpSubmode.ALBUMS):
            mode_new = AmpMode.ALBUMS
        elif( submode == AmpSubmode.SONGS):
            mode_new = AmpMode.SONGS
        elif ( submode == AmpSubmode.PLAYLISTS ):
            mode_new = AmpMode.PLAYLISTS

        #last update
        addDir(ut.tString(30130),mode_new,AmpSubmode.LAST_UPDATE)
        #1 week
        addDir(ut.tString(30131),mode_new,AmpSubmode.WEEK_UPDATE)
        addDir(ut.tString(30132),mode_new,AmpSubmode.MONTH_UPDATE)
        addDir(ut.tString(30133),mode_new,AmpSubmode.THREE_MONTH_UPDATE)


    #stats 100-150
    #random
    elif mode==AmpMode.RANDOM:
        #artists
        addDir(ut.tString(30134),AmpMode.ARTISTS,AmpSubmode.RANDOM)
        #albums
        addDir(ut.tString(30135),AmpMode.ALBUMS,AmpSubmode.RANDOM)
        #songs
        addDir(ut.tString(30136),AmpMode.SONGS,AmpSubmode.RANDOM)
        #playlists
        addDir(ut.tString(30137),AmpMode.PLAYLISTS,AmpSubmode.RANDOM)

    #highest
    elif mode==AmpMode.HIGHEST:
        #artists
        addDir(ut.tString(30149),AmpMode.ARTISTS,AmpSubmode.HIGHEST)
        #albums
        addDir(ut.tString(30150),AmpMode.ALBUMS,AmpSubmode.HIGHEST)
        #songs
        addDir(ut.tString(30151),AmpMode.SONGS,AmpSubmode.HIGHEST)

    #frequent
    elif mode==AmpMode.FREQUENT:
        addDir(ut.tString(30152),AmpMode.ARTISTS, AmpSubmode.FREQUENT)
        addDir(ut.tString(30153),AmpMode.ALBUMS, AmpSubmode.FREQUENT)
        addDir(ut.tString(30154),AmpMode.SONGS, AmpSubmode.FREQUENT)
    
    #flagged
    elif mode==AmpMode.FLAGGED:
        addDir(ut.tString(30155),AmpMode.ARTISTS,AmpSubmode.FLAGGED)
        addDir(ut.tString(30156),AmpMode.ALBUMS,AmpSubmode.FLAGGED)
        addDir(ut.tString(30157),AmpMode.SONGS,AmpSubmode.FLAGGED)

    #forgotten
    elif mode==AmpMode.FORGOTTEN:
        addDir(ut.tString(30158),AmpMode.ARTISTS,AmpSubmode.FORGOTTEN)
        addDir(ut.tString(30159),AmpMode.ALBUMS,AmpSubmode.FORGOTTEN)
        addDir(ut.tString(30160),AmpMode.SONGS,AmpSubmode.FORGOTTEN)
    
    #newest
    elif mode==AmpMode.NEWEST:
        addDir(ut.tString(30161),AmpMode.ARTISTS,AmpSubmode.NEWEST)
        addDir(ut.tString(30162),AmpMode.ALBUMS,AmpSubmode.NEWEST)
        addDir(ut.tString(30163),AmpMode.SONGS,AmpSubmode.NEWEST)
    
    #recently listened
    elif mode==AmpMode.RECENTLY_LISTENED:
        addDir(ut.tString(30190),AmpMode.ARTISTS,AmpSubmode.RECENT)
        addDir(ut.tString(30191),AmpMode.ALBUMS,AmpSubmode.RECENT)
        addDir(ut.tString(30192),AmpMode.SONGS,AmpSubmode.RECENT)

    # recent
    elif mode==AmpMode.RECENTLY_ADDED_MENU:
        #recently added artist
        addDir(ut.tString(30126),AmpMode.RECENTLY_ADDED,AmpSubmode.ARTISTS)
        #recently added album
        addDir(ut.tString(30127),AmpMode.RECENTLY_ADDED,AmpSubmode.ALBUMS)
        #recently added song
        addDir(ut.tString(30128),AmpMode.RECENTLY_ADDED,AmpSubmode.SONGS)
        #recently added playlist
        addDir(ut.tString(30129),AmpMode.RECENTLY_ADDED,AmpSubmode.PLAYLISTS)


    #others mode 200-250
    #play track mode  ( mode set in add_links function )
    #mode 200 to avoid endDirectory
    elif mode==AmpMode.END_DIRECTORY:
        #workaround busydialog bug
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        play_track(m_params['play_url'])

    #change rating
    elif mode==AmpMode.SET_RATINGS:
        setRating()

    #settings mode 300-350
    #settings
    elif mode==AmpMode.SETTINGS:
        ampache.openSettings()

    #the four modes below are used to manage servers
    elif mode==AmpMode.ADD_SERVER:
        servers_manager.initializeServer()
        if servers_manager.addServer():
            servers_manager.switchServer()
    
    elif mode==AmpMode.DELETE_SERVER:
        servers_manager.initializeServer()
        if servers_manager.deleteServer():
            servers_manager.switchServer()
    
    elif mode==AmpMode.MODIFY_SERVER:
        servers_manager.initializeServer()
        servers_manager.modifyServer()
    
    elif mode==AmpMode.SWITCH_SERVER:
        servers_manager.initializeServer()
        servers_manager.switchServer()

    elif mode==AmpMode.CLEAN_CACHE_ART:
        art.clean_cache_art(True)


    #no end directory item ( problem with failed searches )
    #endDir is the result of the search function
    if endDir == False:
        mode = AmpMode.MAX

    if mode == None or mode < AmpMode.END_DIRECTORY:
        xbmc.log("AmpachePlugin::endOfDirectory " + str(handle),  xbmc.LOGDEBUG)
        xbmcplugin.endOfDirectory(handle)


