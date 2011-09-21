# coding: utf-8
'''
Created on 10 jan 2011

@author: Emuller
'''
import os,sys
import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon #@UnresolvedImport
from xml.dom import minidom
from traceback import print_exc
from urllib import unquote_plus
''' sys.setdefaultencoding('utf-8') '''

# plugin modes
MODE_SHOW_SEARCH = 10
MODE_PLAYVIDEO = 30
MODE_SHOW_RECENT = 60
MODE_SHOW_GENRELIST = 70

MODE_SHOW_ARTISTLIST = 100
MODE_SHOW_ARTISTMENU = 110
MODE_SHOW_ALBUMS = 120
MODE_SHOW_TRACKS = 130
MODE_SHOW_GENREMENU = 140

MODE_PLAY_TRACK = 200

MODE_BUILD_ALBUMS_PLAYLIST = 300
MODE_BUILD_TRACKS_PLAYLIST = 310
MODE_BUILD_ARTISTS_PLAYLIST = 320

# parameter keys
PARAMETER_KEY_MODE = "mode"

# control id's
CONTROL_MAIN_LIST_START  = 50
CONTROL_MAIN_LIST_END    = 59

# plugin handle
handle = int(sys.argv[1])
__addonname__ = "plugin.video.musicvideojukebox"
__settings__ = xbmcaddon.Addon(id='plugin.video.musicvideojukebox')
__language__ = __settings__.getLocalizedString
__lastfmapikey__ = "c8a19b7361e56044be8432c023c30888"
__handle__ = int(sys.argv[1])

import iZECore 
izecore = iZECore.iZECore()

import LastFMCore
lastfmcore = LastFMCore.LastFMCore()

import YoutubeCore
youtubecore = YoutubeCore.YoutubeCore()

import GoogleSuggestCore
googlesuggestcore = GoogleSuggestCore.GoogleSuggestCore()

def addDirectoryItem(name, isFolder=True, parameters={},image="", isVideo=True):
    ''' Add a list item to the XBMC UI.'''
    li = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=image)
            
    if isVideo:
        li.setProperty("IsPlayable", "true")
        li.setProperty( "Video", "true" )  
        li.setInfo(type='Video', infoLabels=parameters)    
        
    
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    
    xbmcplugin.setContent( handle=__handle__, content="movies" )    
    return xbmcplugin.addDirectoryItem(handle=__handle__, url=url, listitem=li, isFolder=isFolder)

# UI builder functions
def show_root_menu():
    
    ''' Show the plugin root menu. '''
    addDirectoryItem(name=__language__(30201), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_SEARCH}, isVideo=False)
    addDirectoryItem(name=__language__(30203), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_RECENT}, isVideo=False)
    addDirectoryItem(name=__language__(30204), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_GENRELIST}, isVideo=False)
    addDirectoryItem(name=__language__(30202), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_ARTISTLIST, 'type' : 'chart_topartists'}, isVideo=False)
    addDirectoryItem(name=__language__(30205), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_TRACKS, "type" : "chart_toptracks"}, isVideo=False)
    addDirectoryItem(name=__language__(30206), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_ARTISTLIST, "type" : "chart_hypedartists"}, isVideo=False)
    addDirectoryItem(name=__language__(30207), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_TRACKS, "type" : "chart_hypedtracks"}, isVideo=False)
    addDirectoryItem(name=__language__(30208), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_TRACKS, "type" : "chart_lovedtracks"}, isVideo=False)
    
            
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
    return True


def show_artist_list_menu(params):
    viewmode = izecore.getCurrentViewmode()
    
    if (params.get('type')=="chart_topartists"):
        artists = lastfmcore.Chart_getTopArtists()
    elif (params.get('type')=="tag_topartists"):
        artists = lastfmcore.Tag_getTopArtists(params.get('genre'))
    elif (params.get('type')=="artist_similarartists"):
        artists = lastfmcore.Artist_getSimilar(params.get('artist'))
    elif (params.get('type')=="chart_hypedartists"):
        artists = lastfmcore.Chart_getHypedArtists()
    
    if (artists.length>0):
        params[PARAMETER_KEY_MODE] = MODE_BUILD_ARTISTS_PLAYLIST
        addDirectoryItem(name=__language__(30501), isFolder=False, parameters=params, isVideo=False)    
        
        i = 0
        for artist in artists:
            i=i+1
            name = artist.getElementsByTagName("name")[0].childNodes.item(0).data
            image = ""
            if (artist.getElementsByTagName("image").length>0):
                image = artist.getElementsByTagName("image")[artist.getElementsByTagName("image").length-1].childNodes.item(0).data            
                
            addDirectoryItem(name="%d. %s" % (i, name.encode("utf-8")), isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_ARTISTMENU, "artist":name.encode("utf-8")}, image=image, isVideo=False)
    else:
        addDirectoryItem(name=__language__(30402), isFolder=False, parameters={}, isVideo=False)
        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)     
    xbmc.executebuiltin("Container.SetViewMode(%i)" %  viewmode)  
    
    return True

def build_artists_playlist(params):
    if (params.get('type')=="chart_topartists"):
        artists = lastfmcore.Chart_getTopArtists()
    elif (params.get('type')=="tag_topartists"):
        artists = lastfmcore.Tag_getTopArtists(params.get('genre'))
    elif (params.get('type')=="artist_similarartists"):
        artists = lastfmcore.Artist_getSimilar(params.get('artist'))
    elif (params.get('type')=="chart_hypedartists"):
        artists = lastfmcore.Chart_getHypedArtists()
        
    playlistStarted = False 
    
    player = xbmc.Player()
    if player.isPlaying():
        player.stop()
    
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    
    if (artists.length>0):
        for artist in artists:
            name = artist.getElementsByTagName("name")[0].childNodes.item(0).data
        
            tracks = lastfmcore.Artist_getTopTracks(name.encode("utf-8"), 3)
            for track in tracks:
                trackartist = track.getElementsByTagName("artist")[0].getElementsByTagName("name")[0].childNodes.item(0).data
                trackname = track.getElementsByTagName("name")[0].childNodes.item(0).data
                
                image = ""
                if (track.getElementsByTagName("image").length>0):
                    image = track.getElementsByTagName("image")[track.getElementsByTagName("image").length-1].childNodes.item(0).data
                    
                parameters={PARAMETER_KEY_MODE:MODE_PLAY_TRACK, "artist" : trackartist.encode("utf-8"), "track" : trackname.encode("utf-8"), "thumbnail" : image.encode("utf-8"), "title" : "%s - %s" % (trackartist.encode("utf-8"), trackname.encode("utf-8")), "plot": ""}
                listitem=xbmcgui.ListItem(label="%s - %s" % (trackartist, trackname), iconImage=image, thumbnailImage=image)
                listitem.setProperty('IsPlayable', 'true')
                listitem.setProperty( "Video", "true" )  
                listitem.setInfo(type='Video', infoLabels=parameters)
                
                url = sys.argv[0] + '?' + urllib.urlencode(parameters)        
                playlist.add(url=url, listitem=listitem)
                
                if not playlistStarted:
                    xbmc.executebuiltin('XBMC.Action(Playlist)')                 
                    ''' play playlist'''                
                    playlistStarted = True
                    xbmc.executebuiltin('playlist.playoffset(video,0)' )
        
    else:
        izecore.showMessage(__language__(30401), __language__(30402))
    
    
    
def show_artist_menu(params):
    viewmode = izecore.getCurrentViewmode()
    
    artist = params.get('artist')
    addDirectoryItem(name="%s - %s" % (__language__(30502), artist), isFolder=False, parameters={PARAMETER_KEY_MODE: MODE_BUILD_ALBUMS_PLAYLIST, "type" : "artist_topalbums", "artist":artist}, isVideo=False)
    addDirectoryItem(name="%s - %s" % (__language__(30503), artist), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_ALBUMS, "artist":artist, "type" : "artist_topalbums"}, isVideo=False)
    addDirectoryItem(name="%s - %s" % (__language__(30504), artist), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_TRACKS, "artist":artist, "type" : "artist_toptracks"}, isVideo=False)
    addDirectoryItem(name="%s - %s" % (__language__(30505), artist), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_ARTISTLIST, "artist":artist, "type" : "artist_similarartists"}, isVideo=False)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)     
    xbmc.executebuiltin("Container.SetViewMode(%i)" %  viewmode)  
    
    return True
    
def show_album_menu(params):
    viewmode = izecore.getCurrentViewmode()
    
    if (params.get('type')=="artist_topalbums"):
        albums = lastfmcore.Artist_getTopAlbums(params.get('artist'))
    if (params.get('type')=="tag_topalbums"):
        albums = lastfmcore.Tag_getTopAlbums(params.get('genre'))
    
    if (albums.length>0):
        params[PARAMETER_KEY_MODE] = MODE_BUILD_ALBUMS_PLAYLIST
        addDirectoryItem(name=__language__(30506), isFolder=False, parameters=params, isVideo=False)
        
        i = 0
        for album in albums:
            i = i + 1
            name = album.getElementsByTagName("name")[0].childNodes.item(0).data
            artist = album.getElementsByTagName("artist")[0].getElementsByTagName("name")[0].childNodes.item(0).data
            image = ""
            if (album.getElementsByTagName("image").length>0):
                image = album.getElementsByTagName("image")[album.getElementsByTagName("image").length-1].childNodes.item(0).data
            addDirectoryItem(name="%d. %s - %s" % (i, artist.encode("utf-8"), name.encode("utf-8")), isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_TRACKS, "type" : "album_getinfo", "artist":artist.encode("utf-8"), "album": name.encode("utf-8")}, image=image, isVideo=False)
    else:
        addDirectoryItem(name=__language__(30403), isFolder=False, parameters={}, isVideo=False)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)     
    xbmc.executebuiltin("Container.SetViewMode(%i)" %  viewmode)  
    
    return True

def build_albums_playlist(params):
    if (params.get('type')=="artist_topalbums"):
        albums = lastfmcore.Artist_getTopAlbums(params.get('artist'))
    if (params.get('type')=="tag_topalbums"):
        albums = lastfmcore.Tag_getTopAlbums(params.get('genre'))
    
    
    playlistStarted = False 
    
    player = xbmc.Player()
    if player.isPlaying():
        player.stop()
    
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()   
    
    ''' get 3 tracks from every album '''
    if (albums.length>0):
        
        for album in albums:
            if (album.getElementsByTagName("mbid")[0].childNodes.length>0):
                mbid = album.getElementsByTagName("mbid")[0].childNodes.item(0).data                            
                tracks = lastfmcore.Album_getInfoByMBID(mbid)
            else:
                name = album.getElementsByTagName("name")[0].childNodes.item(0).data
                artist = album.getElementsByTagName("artist")[0].getElementsByTagName("name")[0].childNodes.item(0).data
                tracks = lastfmcore.Album_getInfo(artist.encode("utf-8"),name.encode("utf-8"))
            
            i = 0
            for track in tracks:
                i = i + 1
                trackartist = track.getElementsByTagName("artist")[0].getElementsByTagName("name")[0].childNodes.item(0).data
                trackname = track.getElementsByTagName("name")[0].childNodes.item(0).data
                
                image = ""
                if (track.getElementsByTagName("image").length>0):
                    image = track.getElementsByTagName("image")[track.getElementsByTagName("image").length-1].childNodes.item(0).data
                    
                parameters={PARAMETER_KEY_MODE:MODE_PLAY_TRACK, "artist" : trackartist.encode("utf-8"), "track" : trackname.encode("utf-8"), "thumbnail" : image.encode("utf-8"), "title" : "%s - %s" % (trackartist.encode("utf-8"), trackname.encode("utf-8")), "plot": ""}
                listitem=xbmcgui.ListItem(label="%s - %s" % (trackartist, trackname), iconImage=image, thumbnailImage=image)
                listitem.setProperty('IsPlayable', 'true')
                listitem.setProperty( "Video", "true" )  
                listitem.setInfo(type='Video', infoLabels=parameters)
                
                url = sys.argv[0] + '?' + urllib.urlencode(parameters)        
                playlist.add(url=url, listitem=listitem)
                
                if not playlistStarted:
                    xbmc.executebuiltin('XBMC.Action(Playlist)')                 
                    ''' play playlist'''                
                    playlistStarted = True
                    xbmc.executebuiltin('playlist.playoffset(video,0)' )

                 
        
        
        
    else:
        izecore.showMessage(__language__(30401), __language__(30403))
    
    
    

def show_tracks_menu(params):
    viewmode = izecore.getCurrentViewmode()
            
    if (params.get("type")=="album_getinfo"):
        tracks = lastfmcore.Album_getInfo(params.get('artist'), params.get('album'))
    elif (params.get("type")=="artist_toptracks"):
        tracks = lastfmcore.Artist_getTopTracks(params.get('artist'))
    elif (params.get("type")=="chart_toptracks"):
        tracks = lastfmcore.Chart_getTopTracks()            
    elif (params.get("type")=="tag_toptracks"):
        tracks = lastfmcore.Tag_getTopTracks(params.get('genre'))
    elif (params.get("type")=="chart_hypedtracks"):
        tracks = lastfmcore.Chart_getHypedTracks()
    elif (params.get("type")=="chart_lovedtracks"):
        tracks = lastfmcore.Chart_getLovedTracks()
        
    if (tracks.length>0):        
        params[PARAMETER_KEY_MODE] = MODE_BUILD_TRACKS_PLAYLIST
        addDirectoryItem(name=__language__(30507), isFolder=False, parameters=params, isVideo=False)
        
        i = 0
        for track in tracks:
            i = i + 1
            name = track.getElementsByTagName("name")[0].childNodes.item(0).data
            artist = track.getElementsByTagName("artist")[0].getElementsByTagName("name")[0].childNodes.item(0).data
            image = ""
            if (track.getElementsByTagName("image").length>0):
                image = track.getElementsByTagName("image")[track.getElementsByTagName("image").length-1].childNodes.item(0).data
            

            addDirectoryItem(name="%d. %s - %s" % (i, artist.encode("utf-8"), name.encode("utf-8")), isFolder=False, parameters={PARAMETER_KEY_MODE:MODE_PLAY_TRACK, "artist" : artist.encode("utf-8"), "track" : name.encode("utf-8"), "thumbnail" : image.encode("utf-8")},image=image, isVideo=True)

            
    else:
        addDirectoryItem(name=__language__(30404), isFolder=False, parameters={}, isVideo=False)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)     
    xbmc.executebuiltin("Container.SetViewMode(%i)" %  viewmode)  
    
    return True

def build_tracks_playlist(params):
    if (params.get("type")=="album_getinfo"):
        tracks = lastfmcore.Album_getInfo(params.get('artist'), params.get('album'))
    elif (params.get("type")=="artist_toptracks"):
        tracks = lastfmcore.Artist_getTopTracks(params.get('artist'))
    elif (params.get("type")=="chart_toptracks"):
        tracks = lastfmcore.Chart_getTopTracks()            
    elif (params.get("type")=="tag_toptracks"):
        tracks = lastfmcore.Tag_getTopTracks(params.get('genre'))
    elif (params.get("type")=="chart_hypedtracks"):
        tracks = lastfmcore.Chart_getHypedTracks()
    elif (params.get("type")=="chart_lovedtracks"):
        tracks = lastfmcore.Chart_getLovedTracks()
    
    
    playlistStarted = False 
    
    player = xbmc.Player()
    if player.isPlaying():
        player.stop()
    
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    
    if (tracks.length>0):
        i = 0
        for track in tracks:
            i = i + 1
            name = track.getElementsByTagName("name")[0].childNodes.item(0).data
            artist = track.getElementsByTagName("artist")[0].getElementsByTagName("name")[0].childNodes.item(0).data
            image = ""
            if (track.getElementsByTagName("image").length>0):
                image = track.getElementsByTagName("image")[track.getElementsByTagName("image").length-1].childNodes.item(0).data
                 
            parameters={PARAMETER_KEY_MODE:MODE_PLAY_TRACK, "artist" : artist.encode("utf-8"), "track" : name.encode("utf-8"), "thumbnail" : image.encode("utf-8"), "title" : "%s - %s" % (artist.encode("utf-8"), name.encode("utf-8")), "plot": "" }
            listitem=xbmcgui.ListItem(label="%s - %s" % (artist, name), iconImage=image, thumbnailImage=image)
            listitem.setProperty('IsPlayable', 'true')
            listitem.setProperty( "Video", "true" )  
            listitem.setInfo(type='Video', infoLabels=parameters)
            
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)        
            playlist.add(url=url, listitem=listitem)
            
            if not playlistStarted:
                xbmc.executebuiltin('XBMC.Action(Playlist)')                 
                ''' play playlist'''                
                playlistStarted = True
                xbmc.executebuiltin('playlist.playoffset(video,0)' )
                
    else:
        izecore.showMessage(__language__(30401), __language__(30404))
        

def show_genre_menu(params):
    viewmode = izecore.getCurrentViewmode()
    
    genre = params.get('genre')
    
    addDirectoryItem(name=__language__(30508), isFolder=False, parameters={PARAMETER_KEY_MODE: MODE_BUILD_ARTISTS_PLAYLIST, "type" : "tag_topartists", "genre" : genre}, isVideo=False)
    addDirectoryItem(name="%s - %s" % (__language__(30202), genre), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_ARTISTLIST, "type": "tag_topartists", "genre" : genre}, isVideo=False)
    addDirectoryItem(name="%s - %s" % (__language__(30503), genre), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_ALBUMS, "type": "tag_topalbums", "genre" : genre}, isVideo=False)
    addDirectoryItem(name="%s - %s" % (__language__(30504), genre), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_TRACKS, "type": "tag_toptracks", "genre" : genre}, isVideo=False)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)     
    xbmc.executebuiltin("Container.SetViewMode(%i)" %  viewmode)  

def show_recentlyplayed(params):
    ''' show stored searchqueries '''
    searchqueries = getSearchQueries()
    
    for index, query in enumerate(searchqueries):
        addDirectoryItem(name=query, isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_SEARCH, "artist":query}, isVideo=False)
        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
    
def show_search(params):
    viewmode = izecore.getCurrentViewmode()
    q = params.get("artist")
    if (q==None):
        q = izecore.getKeyboardInput(title=__language__(30201), default="")
    
    artistname = googlesuggestcore.search(q)
    
    storeSearchQuery(artistname.encode("utf-8"))
    
    artistxml = lastfmcore.Artist_search(artistname)
    
    if artistxml.length>0:
        ''' build menu '''
        for artist in artistxml:
            name = artist.getElementsByTagName("name")[0].childNodes.item(0).data
            addDirectoryItem(name=name.encode("utf-8"), isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_ARTISTMENU, "artist":name.encode("utf-8")}, isVideo=False)
        
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)     
        xbmc.executebuiltin("Container.SetViewMode(%i)" %  viewmode)   
    else:
        ''' do exact search '''
        '''xbmc.executebuiltin('XBMC.RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode( { "mode" : MODE_SHOW_ARTISTMENU, "artist" : q} ) ) )'''
        
        ''' try again '''
        artistxml = lastfmcore.Artist_search(q)
        
        if artistxml.length>0:
            ''' build menu '''
            for artist in artistxml:
                name = artist.getElementsByTagName("name")[0].childNodes.item(0).data
                addDirectoryItem(name=name.encode("utf-8"), isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_ARTISTMENU, "artist":name.encode("utf-8")}, isVideo=False)
        else:
            addDirectoryItem(name=__language__(30402), isFolder=False, parameters={}, isVideo=False)
            
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)     
        xbmc.executebuiltin("Container.SetViewMode(%i)" %  viewmode)
        
            
    
def show_genre(params):
    viewmode = izecore.getCurrentViewmode()
    
    ''' build a list of genres '''
    addDirectoryItem(name="60s", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"60s"}, isVideo=False)
    addDirectoryItem(name="70s", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"70s"}, isVideo=False)
    addDirectoryItem(name="80s", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"80s"}, isVideo=False)
    addDirectoryItem(name="90s", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"90s"}, isVideo=False)
    addDirectoryItem(name="Acoustic", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"acoustic"}, isVideo=False)
    addDirectoryItem(name="Ambient", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"ambient"}, isVideo=False)
    addDirectoryItem(name="Blues", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"blues"}, isVideo=False)
    addDirectoryItem(name="Classic Rock", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"classic rock"}, isVideo=False)
    addDirectoryItem(name="Classical", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"classical"}, isVideo=False)
    addDirectoryItem(name="Country", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"country"}, isVideo=False)
    addDirectoryItem(name="Dance", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"dance"}, isVideo=False)
    addDirectoryItem(name="Disco", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"disco"}, isVideo=False)
    addDirectoryItem(name="Electronic", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"electronic"}, isVideo=False)
    addDirectoryItem(name="Folk", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"folk"}, isVideo=False)
    addDirectoryItem(name="Hardcore", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"hardcore"}, isVideo=False)
    addDirectoryItem(name="Hardstyle", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"hardstyle"}, isVideo=False)
    addDirectoryItem(name="Hip hop", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"hip hop"}, isVideo=False)
    addDirectoryItem(name="Indie", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"indie"}, isVideo=False)
    addDirectoryItem(name="Jazz", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"jazz"}, isVideo=False)
    addDirectoryItem(name="Latin", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"latin"}, isVideo=False)
    addDirectoryItem(name="Metal", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"metal"}, isVideo=False)
    addDirectoryItem(name="Pop", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"pop"}, isVideo=False)
    addDirectoryItem(name="Pop punk", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"pop punk"}, isVideo=False)
    addDirectoryItem(name="Punk", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"punk"}, isVideo=False)
    addDirectoryItem(name="Reggae", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"reggae"}, isVideo=False)
    addDirectoryItem(name="R&B", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"rnb"}, isVideo=False)
    addDirectoryItem(name="Rock", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"rock"}, isVideo=False)
    addDirectoryItem(name="Soul", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"soul"}, isVideo=False)
    addDirectoryItem(name="Trance", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"trance"}, isVideo=False)
    addDirectoryItem(name="World", isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_SHOW_GENREMENU, "genre":"world"}, isVideo=False)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)     
    xbmc.executebuiltin("Container.SetViewMode(%i)" %  viewmode)   

def play_track(params): 
    ''' find the track on youtube'''
    videos = youtubecore.getVideosByTrackName(params.get('artist'), params.get('track'))
    
    if (videos.length>0):
        video = videos[0];
        
        ''' get the videoid '''
        videoId = video.getElementsByTagNameNS("http://gdata.youtube.com/schemas/2007", "videoid")[0].childNodes.item(0).data        
        
        '''play the video'''
        params['videoId'] = videoId
        
        playVideo(params)
    
def playVideo(params):
    ''' get video url based on guid '''    
    
    ''' call the youtube player '''
    url = "plugin://plugin.video.youtube?path=/root&action=play_video&videoid=%s" % params.get( "videoId")
    
    listitem=xbmcgui.ListItem(label=params.get("videoId"), iconImage=params.get('thumbnail'), thumbnailImage=params.get('thumbnail'), path=url)
    xbmcplugin.setResolvedUrl(handle=__handle__, succeeded=True, listitem=listitem)
    
    
    

    
def getSearchQueries():
    try:
        searchqueries = eval(__settings__.getSetting("searchqueries"))
    except:
        searchqueries = []
        
    return searchqueries

def storeSearchQuery(query):
    searchqueries = getSearchQueries()
    
    ''' if query already in list abort this function '''
    for index, storedquery in enumerate(searchqueries):
        if query.lower() == storedquery.lower():
            return False
        
    maxsearches = (10, 20, 40, 60, 80, 100)[ int(__settings__.getSetting("maxsearches")) ]
    
    searchqueries = [query] + searchqueries[:maxsearches-1]
    '''searchqueries.sort(myComp)'''
    __settings__.setSetting("searchqueries", repr(searchqueries))
    return True

def myComp (a,b):    
    if (a.lower() > b.lower()):
        return 1
    else:
        return -1
    




# parameter values
params = izecore.getParameters(sys.argv[2])
mode = int(params.get(PARAMETER_KEY_MODE, "0"))

# Depending on the mode, call the appropriate function to build the UI.
if not sys.argv[2]:
    # new start
    ok = show_root_menu()
elif mode == MODE_SHOW_SEARCH:
    ok = show_search(params)
elif mode == MODE_PLAYVIDEO:
    ok = playVideo(params)
elif mode == MODE_SHOW_RECENT:
    ok = show_recentlyplayed(params)
elif mode == MODE_SHOW_GENRELIST:
    ok = show_genre(params)
elif mode == MODE_SHOW_ARTISTLIST:
    ok = show_artist_list_menu(params)
elif mode == MODE_SHOW_ARTISTMENU:
    ok = show_artist_menu(params)
elif mode == MODE_SHOW_ALBUMS:
    ok = show_album_menu(params)
elif mode == MODE_SHOW_TRACKS:
    ok = show_tracks_menu(params)
elif mode == MODE_SHOW_GENREMENU:
    ok = show_genre_menu(params)
elif mode == MODE_PLAY_TRACK:
    ok = play_track(params)
elif mode == MODE_BUILD_ALBUMS_PLAYLIST:
    ok = build_albums_playlist(params)
elif mode == MODE_BUILD_TRACKS_PLAYLIST:
    ok = build_tracks_playlist(params)
elif mode == MODE_BUILD_ARTISTS_PLAYLIST:
    ok = build_artists_playlist(params)
    