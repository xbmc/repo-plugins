# Copyright 2011 Stephen Denham

#    This file is part of xbmc-groove.
#
#    xbmc-groove is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    xbmc-groove is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with xbmc-groove.  If not, see <http://www.gnu.org/licenses/>.


import urllib, sys, os, shutil, re, pickle, time, tempfile, xbmcaddon, xbmcplugin, xbmcgui, xbmc

__addon__     = xbmcaddon.Addon('plugin.audio.groove')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')
__author__    = __addon__.getAddonInfo('author')
__version__   = __addon__.getAddonInfo('version')
__language__  = __addon__.getLocalizedString
__debugging__  = __addon__.getSetting('debug')

MODE_SEARCH_SONGS = 1
MODE_SEARCH_ALBUMS = 2
MODE_SEARCH_ARTISTS = 3
MODE_SEARCH_ARTISTS_ALBUMS = 4
MODE_SEARCH_PLAYLISTS = 5
MODE_ARTIST_POPULAR = 6
MODE_POPULAR_SONGS = 7
MODE_FAVORITES = 8
MODE_PLAYLISTS = 9
MODE_ALBUM = 10
MODE_ARTIST = 11
MODE_PLAYLIST = 12
MODE_SONG_PAGE = 13
MODE_SIMILAR_ARTISTS = 14
MODE_SONG = 15
MODE_FAVORITE = 16
MODE_UNFAVORITE = 17
MODE_MAKE_PLAYLIST = 18
MODE_REMOVE_PLAYLIST = 19
MODE_RENAME_PLAYLIST = 20
MODE_REMOVE_PLAYLIST_SONG = 21
MODE_ADD_PLAYLIST_SONG = 22

ACTION_MOVE_LEFT = 1
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4
ACTION_PAGE_UP = 5
ACTION_PAGE_DOWN = 6
ACTION_SELECT_ITEM = 7
ACTION_PREVIOUS_MENU = 10

# Formats for track labels
ARTIST_ALBUM_NAME_LABEL = 0
NAME_ALBUM_ARTIST_LABEL = 1

# Stream marking time (seconds)
STREAM_MARKING_TIME = 30

# Timeout
STREAM_TIMEOUT = 30

songMarkTime = 0
player = xbmc.Player()
playTimer = None

baseDir = __cwd__
resDir = xbmc.translatePath(os.path.join(baseDir, 'resources'))
libDir = xbmc.translatePath(os.path.join(resDir,  'lib'))
imgDir = xbmc.translatePath(os.path.join(resDir,  'img'))
cacheDir = os.path.join(xbmc.translatePath('special://masterprofile/addon_data/'), os.path.basename(baseDir))
thumbDirName = 'thumb'
thumbDir = os.path.join(xbmc.translatePath('special://masterprofile/addon_data/'), os.path.basename(baseDir), thumbDirName)

baseModeUrl = 'plugin://plugin.audio.groove/'
playlistUrl = baseModeUrl + '?mode=' + str(MODE_PLAYLIST)
playlistsUrl = baseModeUrl + '?mode=' + str(MODE_PLAYLISTS)
favoritesUrl = baseModeUrl + '?mode=' + str(MODE_FAVORITES)

searchArtistsAlbumsName = __language__(30006)

thumbDef = os.path.join(imgDir, 'default.tbn')
listBackground = os.path.join(imgDir, 'listbackground.png')

sys.path.append (libDir)
from GroovesharkAPI import GrooveAPI
from threading import Event, Thread

if __debugging__ == 'true':
    __debugging__ = True
else:
    __debugging__ = False

try:
    groovesharkApi = GrooveAPI(__debugging__)
    if groovesharkApi.pingService() != True:
        raise StandardError(__language__(30007))
except:
    dialog = xbmcgui.Dialog(__language__(30008),__language__(30009),__language__(30010))
    dialog.ok(__language__(30008),__language__(30009))
    sys.exit(-1)
  
# Mark song as playing or played
def markSong(songid, duration, streamKey, streamServerID):
    global songMarkTime
    global playTimer
    global player
    if player.isPlayingAudio():
        tNow = player.getTime()
        if tNow >= STREAM_MARKING_TIME and songMarkTime == 0:
            groovesharkApi.markStreamKeyOver30Secs(streamKey, streamServerID)
            songMarkTime = tNow
        elif duration > tNow and duration - tNow < 2 and songMarkTime >= STREAM_MARKING_TIME:
            playTimer.cancel()
            songMarkTime = 0
            groovesharkApi.markSongComplete(songid, streamKey, streamServerID)
    else:
        playTimer.cancel()
        songMarkTime = 0
            
class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )

# Window dialog to select a grooveshark playlist        
class GroovesharkPlaylistSelect(xbmcgui.WindowDialog):
    
    def __init__(self, items=[]):
        gap = int(self.getHeight()/100)
        w = int(self.getWidth()*0.5)
        h = self.getHeight()-30*gap
        rw = self.getWidth()
        rh = self.getHeight()
        x = rw/2 - w/2
        y = rh/2 -h/2
        
        self.imgBg = xbmcgui.ControlImage(x+gap, 5*gap+y, w-2*gap, h-5*gap, listBackground)
        self.addControl(self.imgBg)

        self.playlistControl = xbmcgui.ControlList(2*gap+x, y+3*gap+30, w-4*gap, h-10*gap, textColor='0xFFFFFFFF', selectedColor='0xFFFF4242', itemTextYOffset=0, itemHeight=50, alignmentY = 0)
        self.addControl(self.playlistControl)

        self.lastPos = 0
        self.isSelecting = False
        self.selected = -1
        listitems = []
        for playlist in items:
            listitems.append(xbmcgui.ListItem(playlist[0]))
        listitems.append(xbmcgui.ListItem(__language__(30011)))
        self.playlistControl.addItems(listitems)
        self.setFocus(self.playlistControl)
        self.playlistControl.selectItem(0)
        item = self.playlistControl.getListItem(self.lastPos)
        item.select(True)

    # Highlight selected item
    def setHighlight(self):
        if self.isSelecting:
            return
        else:
            self.isSelecting = True
        
        pos = self.playlistControl.getSelectedPosition()
        if pos >= 0:
            item = self.playlistControl.getListItem(self.lastPos)
            item.select(False)
            item = self.playlistControl.getListItem(pos)
            item.select(True)
            self.lastPos = pos
        self.isSelecting = False

    # Control - select
    def onControl(self, control):
        if control == self.playlistControl:
            self.selected = self.playlistControl.getSelectedPosition()
            self.close()

    # Action - close or up/down        
    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU:
            self.selected = -1
            self.close()
        elif action == ACTION_MOVE_UP or action == ACTION_MOVE_DOWN or action == ACTION_PAGE_UP or action == ACTION_PAGE_DOWN == 6:
            self.setFocus(self.playlistControl)
            self.setHighlight()

 
class PlayTimer(Thread):
    # interval -- floating point number specifying the number of seconds to wait before executing function
    # function -- the function (or callable object) to be executed

    # iterations -- integer specifying the number of iterations to perform
    # args -- list of positional arguments passed to function
    # kwargs -- dictionary of keyword arguments passed to function
    
    def __init__(self, interval, function, iterations=0, args=[], kwargs={}):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.iterations = iterations
        self.args = args
        self.kwargs = kwargs
        self.finished = Event()
 
    def run(self):
        count = 0
        while not self.finished.isSet() and (self.iterations <= 0 or count < self.iterations):
            self.finished.wait(self.interval)
            if not self.finished.isSet():
                self.function(*self.args, **self.kwargs)
                count += 1
 
    def cancel(self):
        self.finished.set()
    
    def setIterations(self, iterations):
        self.iterations = iterations
        

    def getTime(self):
        return self.iterations * self.interval


class Grooveshark:
    
    albumImg = xbmc.translatePath(os.path.join(imgDir, 'album.png'))
    artistImg = xbmc.translatePath(os.path.join(imgDir, 'artist.png'))
    artistsAlbumsImg = xbmc.translatePath(os.path.join(imgDir, 'artistsalbums.png'))
    favoritesImg = xbmc.translatePath(os.path.join(imgDir, 'favorites.png'))
    playlistImg = xbmc.translatePath(os.path.join(imgDir, 'playlist.png'))
    usersplaylistsImg = xbmc.translatePath(os.path.join(imgDir, 'usersplaylists.png'))
    popularSongsImg = xbmc.translatePath(os.path.join(imgDir, 'popularSongs.png'))
    popularSongsArtistImg = xbmc.translatePath(os.path.join(imgDir, 'popularSongsArtist.png'))
    songImg = xbmc.translatePath(os.path.join(imgDir, 'song.png'))
    defImg = xbmc.translatePath(os.path.join(imgDir, 'default.tbn'))
    fanImg = xbmc.translatePath(os.path.join(baseDir, 'fanart.jpg'))

    settings = xbmcaddon.Addon(id='plugin.audio.groove')
    songsearchlimit = int(settings.getSetting('songsearchlimit'))
    albumsearchlimit = int(settings.getSetting('albumsearchlimit'))
    artistsearchlimit = int(settings.getSetting('artistsearchlimit'))
    songspagelimit = int(settings.getSetting('songspagelimit'))
    username = settings.getSetting('username')
    password = settings.getSetting('password')

    userid = 0
    
    def __init__( self ):
        self._handle = int(sys.argv[1])
        if os.path.isdir(cacheDir) == False:
            os.makedirs(cacheDir)
            if __debugging__ :
                xbmc.log(__language__(30012) + " " + cacheDir)
        artDir = xbmc.translatePath(thumbDir)
        if os.path.isdir(artDir) == False:
            os.makedirs(artDir)
            if __debugging__ :
                xbmc.log(__language__(30012) + " " + artDir)
            
    # Top-level menu
    def categories(self):

        self.userid = self._get_login()
        
        # Setup
        xbmcplugin.setPluginFanart(int(sys.argv[1]), self.fanImg)
        
        self._add_dir(__language__(30013), '', MODE_SEARCH_SONGS, self.songImg, 0)
        self._add_dir(__language__(30014), '', MODE_SEARCH_ALBUMS, self.albumImg, 0)
        self._add_dir(__language__(30015), '', MODE_SEARCH_ARTISTS, self.artistImg, 0)
        self._add_dir(searchArtistsAlbumsName, '', MODE_SEARCH_ARTISTS_ALBUMS, self.artistsAlbumsImg, 0)
        # Not supported by key
        #self._add_dir("Search for user's playlists...", '', MODE_SEARCH_PLAYLISTS, self.usersplaylistsImg, 0)
        self._add_dir(__language__(30016), '', MODE_ARTIST_POPULAR, self.popularSongsArtistImg, 0)
        self._add_dir(__language__(30017), '', MODE_POPULAR_SONGS, self.popularSongsImg, 0)
        if (self.userid != 0):
            self._add_dir(__language__(30018), '', MODE_FAVORITES, self.favoritesImg, 0)
            self._add_dir(__language__(30019), '', MODE_PLAYLISTS, self.playlistImg, 0)

    # Search for songs            
    def searchSongs(self):
        query = self._get_keyboard(default="", heading=__language__(30020))
        if (query != ''):
            songs = groovesharkApi.getSongSearchResults(query, limit = self.songsearchlimit)
            if (len(songs) > 0):
                self._add_songs_directory(songs)
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30021))
                self.categories()
        else:
            self.categories()
    
    # Search for albums
    def searchAlbums(self):
        query = self._get_keyboard(default="", heading=__language__(30022))
        if (query != ''): 
            albums = groovesharkApi.getAlbumSearchResults(query, limit = self.albumsearchlimit)
            if (len(albums) > 0):
                self._add_albums_directory(albums)
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30023))
                self.categories()
        else:
            self.categories()
    
    # Search for artists
    def searchArtists(self):
        query = self._get_keyboard(default="", heading=__language__(30024))
        if (query != ''): 
            artists = groovesharkApi.getArtistSearchResults(query, limit = self.artistsearchlimit)
            if (len(artists) > 0):
                self._add_artists_directory(artists)
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30025))
                self.categories()
        else:
            self.categories()

    # Search for playlists
    def searchPlaylists(self):
        query = self._get_keyboard(default="", heading=__language__(30026))
        if (query != ''): 
            playlists = groovesharkApi.getUserPlaylistsByUsername(query)
            if (len(playlists) > 0):
                self._add_playlists_directory(playlists)
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30027))
                self.categories()
        else:
            self.categories()

    # Search for artists albums
    def searchArtistsAlbums(self, artistName = None):
        if artistName == None or artistName == searchArtistsAlbumsName:
            query = self._get_keyboard(default="", heading=__language__(30028))
        else:
            query = artistName
        if (query != ''): 
            artists = groovesharkApi.getArtistSearchResults(query, limit = self.artistsearchlimit)
            if (len(artists) > 0):
                artist = artists[0]
                artistID = artist[1]
                if __debugging__ :
                    xbmc.log("Found " + artist[0] + "...")
                albums = groovesharkApi.getArtistAlbums(artistID, self.albumsearchlimit)
                if (len(albums) > 0):
                    self._add_albums_directory(albums, artistID)
                else:
                    dialog = xbmcgui.Dialog()
                    dialog.ok(__language__(30008), __language__(30029))
                    self.categories()
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30030))
                self.categories()
        else:
            self.categories()
                  
    # Get my favorites
    def favorites(self):
        userid = self._get_login()
        if (userid != 0):
            favorites = groovesharkApi.getUserFavoriteSongs()
            if (len(favorites) > 0):
                self._add_songs_directory(favorites, isFavorites=True)
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30031))
                self.categories()
    
    # Get popular songs
    def popularSongs(self):
        popular = groovesharkApi.getPopularSongsToday(limit = self.songsearchlimit)
        if (len(popular) > 0):
            self._add_songs_directory(popular)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30032))
            self.categories()

    # Get my playlists             
    def playlists(self):
        userid = self._get_login()
        if (userid != 0):
            playlists = groovesharkApi.getUserPlaylists()
            if (len(playlists) > 0):
                self._add_playlists_directory(playlists)
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30033))
                self.categories()
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30034), __language__(30035))
                
    # Make songs a favorite 
    def favorite(self, songid):
        userid = self._get_login()
        if (userid != 0):
            if __debugging__ :
                xbmc.log("Favorite song: " + str(songid))
            groovesharkApi.addUserFavoriteSong(songID = songid)
            xbmc.executebuiltin('XBMC.Notification(' + __language__(30008) + ', ' + __language__(30036) + ', 1000, ' + thumbDef + ')')
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30034), __language__(30037))
            
    # Remove song from favorites
    def unfavorite(self, songid, prevMode=0):
        userid = self._get_login()
        if (userid != 0):
            if __debugging__ :
                xbmc.log("Unfavorite song: " + str(songid) + ', previous mode was ' + str(prevMode))
            groovesharkApi.removeUserFavoriteSongs(songIDs = songid)
            xbmc.executebuiltin('XBMC.Notification(' + __language__(30008) + ', ' + __language__(30038) + ', 1000, ' + thumbDef + ')')
            # Refresh to remove item from directory
            if (int(prevMode) == MODE_FAVORITES):
                xbmc.executebuiltin("Container.Refresh(" + favoritesUrl + ")")
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30034), __language__(30039))
            

    # Show selected album
    def album(self, albumid):
        album = groovesharkApi.getAlbumSongs(albumid, limit = self.songsearchlimit)
        self._add_songs_directory(album, trackLabelFormat=NAME_ALBUM_ARTIST_LABEL)

    # Show selected artist
    def artist(self, artistid):
        albums = groovesharkApi.getArtistAlbums(artistid, limit = self.albumsearchlimit)
        self._add_albums_directory(albums, artistid, True)
    
    # Show selected playlist
    def playlist(self, playlistid, playlistname):
        userid = self._get_login()
        if (userid != 0):
            songs = groovesharkApi.getPlaylistSongs(playlistid)
            self._add_songs_directory(songs, trackLabelFormat=NAME_ALBUM_ARTIST_LABEL, playlistid=playlistid, playlistname=playlistname)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30034), __language__(30040))
            
    # Show popular songs of the artist
    def artistPopularSongs(self):
        query = self._get_keyboard(default="", heading=__language__(30041))
        if (query != ''): 
            artists = groovesharkApi.getArtistSearchResults(query, limit = self.artistsearchlimit)
            if (len(artists) > 0):
                artist = artists[0]
                artistID = artist[1]
                if __debugging__ :
                    xbmc.log("Found " + artist[0] + "...")
                songs = groovesharkApi.getArtistPopularSongs(artistID, limit = self.songsearchlimit)
                if (len(songs) > 0):
                    self._add_songs_directory(songs, trackLabelFormat=NAME_ALBUM_ARTIST_LABEL)
                else:
                    dialog = xbmcgui.Dialog()
                    dialog.ok(__language__(30008), __language__(30042))
                    self.categories()
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30043))
                self.categories()
        else:
            self.categories()
            
    # Play a song
    def playSong(self, item):
        global playTimer
        global player
        if item != None:
            # Get stream as it could have expired
            item.select(True)
            url = ''
            songid = item.getProperty('songid')
            stream = groovesharkApi.getSubscriberStreamKey(songid)
            if stream != False:
                url = stream['url']
                key = stream['StreamKey']
                server = stream['StreamServerID']
                duration = int(self._setDuration(stream['uSecs']))
                stream = [songid, duration, url, key, server]
                self._setSongStream(stream)
                if url != '':
                    item.setPath(url)
                    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=item)
                    if __debugging__ :
                        xbmc.log("Grooveshark playing: " + url)
                    # Wait for play then start timer
                    seconds = 0
                    while seconds < STREAM_TIMEOUT:
                        try:
                            if player.isPlayingAudio() == True:
                                if playTimer != None:
                                    playTimer.cancel()
                                    songMarkTime = 0
                                playTimer = PlayTimer(1, markSong, self._setDuration(duration), [songid, duration, key, server])
                                playTimer.start()
                                break
                        except: pass
                        time.sleep(1)
                        seconds = seconds + 1
                else:
                    xbmc.log("No song URL")
            else:
                xbmc.log("No song stream")
        else:
            xbmc.executebuiltin('XBMC.Notification(' + __language__(30008) + ', ' + __language__(30044) + ', 1000, ' + thumbDef + ')')
        
    # Make a song directory item
    def songItem(self, songid, name, album, artist, coverart, trackLabelFormat=ARTIST_ALBUM_NAME_LABEL, tracknumber=1):
        
        stream = self._getSongStream(songid)
        if stream != False:
            duration = stream[1]
            url = stream[2]
            key = stream[3]
            server = stream[4]
            songImg = self._get_icon(coverart, 'song-' + str(songid) + "-image")
            if int(trackLabelFormat) == NAME_ALBUM_ARTIST_LABEL:
                trackLabel = name + " - " + album + " - " + artist
            else:
                trackLabel = artist + " - " + album + " - " + name
            item = xbmcgui.ListItem(label = trackLabel, thumbnailImage=songImg, iconImage=songImg)
            item.setPath(url)
            item.setInfo( type="music", infoLabels={ "title": name, "album": album, "artist": artist, "duration": duration, "tracknumber" : tracknumber} )
            item.setProperty('mimetype', 'audio/mpeg')
            item.setProperty("IsPlayable", "true")
            item.setProperty('songid', str(songid))
            item.setProperty('coverart', songImg)
            item.setProperty('title', name)
            item.setProperty('album', album)
            item.setProperty('artist', artist)
            item.setProperty('duration', str(duration))
            item.setProperty('key', str(key))
            item.setProperty('server', str(server))
            return item
        else:
            xbmc.log("No song URL")
            return None
    
    # Next page of songs
    def songPage(self, offset, trackLabelFormat, playlistid = 0, playlistname = ''):
        self._add_songs_directory([], trackLabelFormat, offset, playlistid = playlistid, playlistname = playlistname)
        
    # Make a playlist from an album      
    def makePlaylist(self, albumid, name):
        userid = self._get_login()
        if (userid != 0):
            re.split(' - ',name,1)
            nameTokens = re.split(' - ',name,1) # suggested name
            name = self._get_keyboard(default=nameTokens[0], heading=__language__(30045))
            if name != '':
                album = groovesharkApi.getAlbumSongs(albumid, limit = self.songsearchlimit)
                songids = []
                for song in album:
                    songids.append(song[1])
                if groovesharkApi.createPlaylist(name, songids) == 0:
                    dialog = xbmcgui.Dialog()
                    dialog.ok(__language__(30008), __language__(30046), name)
                else:
                    xbmc.executebuiltin('XBMC.Notification(' + __language__(30008) + ',' + __language__(30047)+ ', 1000, ' + thumbDef + ')')
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30034), __language__(30048))
    
    # Rename a playlist
    def renamePlaylist(self, playlistid, name):
        userid = self._get_login()
        if (userid != 0):
            newname = self._get_keyboard(default=name, heading=__language__(30049))
            if newname == '':
                return
            elif groovesharkApi.playlistRename(playlistid, newname) == 0:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30050), name)
            else:
                # Refresh to show new item name
                xbmc.executebuiltin("Container.Refresh")
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30034), __language__(30051))
        
    # Remove a playlist
    def removePlaylist(self, playlistid, name):
        dialog = xbmcgui.Dialog()
        if dialog.yesno(__language__(30008), name, __language__(30052)) == True:
            userid = self._get_login()
            if (userid != 0):
                if groovesharkApi.playlistDelete(playlistid) == 0:
                    dialog = xbmcgui.Dialog()
                    dialog.ok(__language__(30008), __language__(30053), name)
                else:
                    # Refresh to remove item from directory
                    xbmc.executebuiltin("Container.Refresh(" + playlistsUrl + ")")
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30034), __language__(30054))

    # Add song to playlist
    def addPlaylistSong(self, songid):
        userid = self._get_login()
        if (userid != 0):
            playlists = groovesharkApi.getUserPlaylists()
            if (len(playlists) > 0):
                ret = 0
                # Select the playlist
                playlistSelect = GroovesharkPlaylistSelect(items=playlists)
                playlistSelect.setFocus(playlistSelect.playlistControl)
                playlistSelect.doModal()
                i = playlistSelect.selected
                del playlistSelect
                if i > -1:
                    # Add a new playlist
                    if i >= len(playlists):
                        name = self._get_keyboard(default='', heading=__language__(30055))
                        if name != '':
                            songIds = []
                            songIds.append(songid)
                            if groovesharkApi.createPlaylist(name, songIds) == 0:
                                dialog = xbmcgui.Dialog()
                                dialog.ok(__language__(30008), __language__(30056), name)
                            else:
                                xbmc.executebuiltin('XBMC.Notification(' + __language__(30008) + ',' + __language__(30057) + ', 1000, ' + thumbDef + ')')
                    # Existing playlist
                    else:
                        playlist = playlists[i]
                        playlistid = playlist[1]
                        if __debugging__ :
                            xbmc.log("Add song " + str(songid) + " to playlist " + str(playlistid))
                        songIDs=[]
                        songs = groovesharkApi.getPlaylistSongs(playlistid)
                        for song in songs:
                            songIDs.append(song[1])
                        songIDs.append(songid)
                        ret = groovesharkApi.setPlaylistSongs(playlistid, songIDs)
                        if ret == False:
                            dialog = xbmcgui.Dialog()
                            dialog.ok(__language__(30008), __language__(30058))
                        else:    
                            xbmc.executebuiltin('XBMC.Notification(' + __language__(30008) + ',' + __language__(30059) + ', 1000, ' + thumbDef + ')')
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30060))
                self.categories()
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30034), __language__(30061))

    # Remove song from playlist
    def removePlaylistSong(self, playlistid, playlistname, songid):
        dialog = xbmcgui.Dialog()
        if dialog.yesno(__language__(30008), __language__(30062), __language__(30063)) == True:
            userid = self._get_login()
            if (userid != 0):
                songs = groovesharkApi.getPlaylistSongs(playlistID)
                songIDs=[]
                for song in songs:
                    if (song[1] != songid):
                        songIDs.append(song[1])
                ret = groovesharkApi.setPlaylistSongs(playlistID, songIDs)
                if ret == False:
                    dialog = xbmcgui.Dialog()
                    dialog.ok(__language__(30008), __language__(30064), __language__(30065))
                else:
                    # Refresh to remove item from directory
                    xbmc.executebuiltin('XBMC.Notification(' + __language__(30008) + ',' + __language__(30066)+ ', 1000, ' + thumbDef + ')')
                    xbmc.executebuiltin("Container.Update(" + playlistUrl + "&id="+str(playlistid) + "&name=" + playlistname + ")")
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30034), __language__(30067))
      
    # Find similar artists to searched artist
    def similarArtists(self, artistId):
        similar = groovesharkApi.getSimilarArtists(artistId, limit = self.artistsearchlimit)
        if (len(similar) > 0):
            self._add_artists_directory(similar)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30068))
            self.categories()
    
    # Get keyboard input
    def _get_keyboard(self, default="", heading="", hidden=False):
        kb = xbmc.Keyboard(default, heading, hidden)
        kb.doModal()
        if (kb.isConfirmed()):
            return unicode(kb.getText(), "utf-8")
        return ''
    
    # Login to grooveshark
    def _get_login(self):
        if (self.username == "" or self.password == ""):
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30069), __language__(30070), __language__(30082))
            return 0
        else:
            if self.userid == 0:
                uid = groovesharkApi.login(self.username, self.password)
            if (uid != 0):
                return uid
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok(__language__(30008), __language__(30069), __language__(30070), __language__(30082))
                return 0
    
    # File download            
    def _get_icon(self, url, songid):
        if url != 'None':
            localThumb = os.path.join(xbmc.translatePath(os.path.join(thumbDir, str(songid)))) + '.tbn'
            try:
                if os.path.isfile(localThumb) == False:
                    loc = urllib.URLopener()
                    loc.retrieve(url, localThumb)
            except:
                shutil.copy2(thumbDef, localThumb)
            return os.path.join(os.path.join(thumbDir, str(songid))) + '.tbn'
        else:
            return thumbDef
    
    # Add songs to directory
    def _add_songs_directory(self, songs, trackLabelFormat=ARTIST_ALBUM_NAME_LABEL, offset=0, playlistid=0, playlistname='', isFavorites=False):

        totalSongs = len(songs)
        offset = int(offset)
        start = 0
        end = totalSongs

        # No pages needed
        if offset == 0 and totalSongs <= self.songspagelimit:
            if __debugging__ :
                xbmc.log("Found " + str(totalSongs) + " songs...")
        # Pages
        else:
            # Cache all next pages songs
            if offset == 0:
                self._setSavedSongs(songs)
            else:
                songs = self._getSavedSongs()
                totalSongs = len(songs)
                
            if totalSongs > 0:
                start = offset
                end = min(start + self.songspagelimit,totalSongs)
        
        id = 0
        n = start
        items = end - start
        while n < end:
            song = songs[n]
            name = song[0]
            songid = song[1]
            album = song[2]
            artist = song[4]
            coverart = song[6]
            item = self.songItem(songid, name, album, artist, coverart, trackLabelFormat, (n+1))
            if item != None:   
                coverart = item.getProperty('coverart')
                songname = song[0]
                songalbum = song[2]
                songartist = song[4]
                u=sys.argv[0]+"?mode="+str(MODE_SONG)+"&name="+urllib.quote_plus(songname)+"&id="+str(songid) \
                +"&album="+urllib.quote_plus(songalbum) \
                +"&artist="+urllib.quote_plus(songartist) \
                +"&coverart="+urllib.quote_plus(coverart)
                fav=sys.argv[0]+"?mode="+str(MODE_FAVORITE)+"&name="+urllib.quote_plus(songname)+"&id="+str(songid)
                unfav=sys.argv[0]+"?mode="+str(MODE_UNFAVORITE)+"&name="+urllib.quote_plus(songname)+"&id="+str(songid)+"&prevmode="
                menuItems = []
                if isFavorites == True:
                    unfav = unfav +str(MODE_FAVORITES)
                else:
                    menuItems.append((__language__(30071), "XBMC.RunPlugin("+fav+")"))
                menuItems.append((__language__(30072), "XBMC.RunPlugin("+unfav+")"))
                if playlistid > 0:
                    rmplaylstsong=sys.argv[0]+"?playlistid="+str(playlistid)+"&id="+str(songid)+"&mode="+str(MODE_REMOVE_PLAYLIST_SONG)+"&name="+playlistname
                    menuItems.append((__language__(30073), "XBMC.RunPlugin("+rmplaylstsong+")"))
                else:
                    addplaylstsong=sys.argv[0]+"?id="+str(songid)+"&mode="+str(MODE_ADD_PLAYLIST_SONG)
                    menuItems.append((__language__(30074), "XBMC.RunPlugin("+addplaylstsong+")"))
                item.addContextMenuItems(menuItems, replaceItems=False)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=item,isFolder=False, totalItems=items)
                id = id + 1
            else:
                end = min(end + 1,totalSongs)
                if __debugging__ :
                    xbmc.log(song[0] + " does not exist.")
            n = n + 1

        if totalSongs > end:
            u=sys.argv[0]+"?mode="+str(MODE_SONG_PAGE)+"&id=playlistid"+"&offset="+str(end)+"&label="+str(trackLabelFormat)+"&name="+playlistname
            self._add_dir(__language__(30075) + '...', u, MODE_SONG_PAGE, self.songImg, 0, totalSongs - end)

        xbmcplugin.setContent(self._handle, 'songs')
        xbmcplugin.setPluginFanart(int(sys.argv[1]), self.fanImg)
    
    # Add albums to directory
    def _add_albums_directory(self, albums, artistid=0, isverified=False):
        n = len(albums)
        itemsExisting = n
        if __debugging__ :
            xbmc.log("Found " + str(n) + " albums...")
        i = 0
        while i < n:
            album = albums[i]
            albumID = album[3]
            if isverified or groovesharkApi.getDoesAlbumExist(albumID):                    
                albumArtistName = album[0]
                albumName = album[2]
                albumImage = self._get_icon(album[4], 'album-' + str(albumID))
                self._add_dir(albumName + " - " + albumArtistName, '', MODE_ALBUM, albumImage, albumID, itemsExisting)
            else:
                itemsExisting = itemsExisting - 1
            i = i + 1
        # Not supported by key
        #if artistid > 0:
        #    self._add_dir('Similar artists...', '', MODE_SIMILAR_ARTISTS, self.artistImg, artistid)
        xbmcplugin.setContent(self._handle, 'albums')
        xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE)
        xbmcplugin.setPluginFanart(int(sys.argv[1]), self.fanImg)
    
    # Add artists to directory
    def _add_artists_directory(self, artists):
        n = len(artists)
        itemsExisting = n
        if __debugging__ :
            xbmc.log("Found " + str(n) + " artists...")
        i = 0
        while i < n:
            artist = artists[i]
            artistID = artist[1]
            if groovesharkApi.getDoesArtistExist(artistID):                    
                artistName = artist[0]
                self._add_dir(artistName, '', MODE_ARTIST, self.artistImg, artistID, itemsExisting)
            else:
                itemsExisting = itemsExisting - 1
            i = i + 1
        xbmcplugin.setContent(self._handle, 'artists')
        xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_ARTIST_IGNORE_THE)
        xbmcplugin.setPluginFanart(int(sys.argv[1]), self.fanImg)

    # Add playlists to directory          
    def _add_playlists_directory(self, playlists):
        n = len(playlists)
        if __debugging__ :
            xbmc.log("Found " + str(n) + " playlists...")
        i = 0
        while i < n:
            playlist = playlists[i]
            playlistName = playlist[0]
            playlistID = playlist[1]
            dir = self._add_dir(playlistName, '', MODE_PLAYLIST, self.playlistImg, playlistID, n)
            i = i + 1  
        xbmcplugin.setContent(self._handle, 'files')
        xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.setPluginFanart(int(sys.argv[1]), self.fanImg)
      
    # Add whatever directory
    def _add_dir(self, name, url, mode, iconimage, id, items=1):

        if url == '':
            u=sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&id="+str(id)
        else:
            u = url
        dir=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        dir.setInfo( type="Music", infoLabels={ "title": name } )
        
        # Custom menu items
        menuItems = []
        if mode == MODE_ALBUM:
            mkplaylst=sys.argv[0]+"?mode="+str(MODE_MAKE_PLAYLIST)+"&name="+name+"&id="+str(id)
            menuItems.append((__language__(30076), "XBMC.RunPlugin("+mkplaylst+")"))
        if mode == MODE_PLAYLIST:
            rmplaylst=sys.argv[0]+"?mode="+str(MODE_REMOVE_PLAYLIST)+"&name="+urllib.quote_plus(name)+"&id="+str(id)
            menuItems.append((__language__(30077), "XBMC.RunPlugin("+rmplaylst+")"))
            mvplaylst=sys.argv[0]+"?mode="+str(MODE_RENAME_PLAYLIST)+"&name="+urllib.quote_plus(name)+"&id="+str(id)
            menuItems.append((__language__(30078), "XBMC.RunPlugin("+mvplaylst+")"))

        dir.addContextMenuItems(menuItems, replaceItems=False)
        
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=dir,isFolder=True, totalItems=items)
    
    def _getSavedSongs(self):
        path = os.path.join(cacheDir, 'songs.dmp')
        try:
            f = open(path, 'rb')
            songs = pickle.load(f)
            f.close()
        except:
            songs = []
            pass
        return songs

    def _setSavedSongs(self, songs):            
        try:
            # Create the 'data' directory if it doesn't exist.
            if not os.path.exists(cacheDir):
                os.makedirs(cacheDir)
            path = os.path.join(cacheDir, 'songs.dmp')
            f = open(path, 'wb')
            pickle.dump(songs, f, protocol=pickle.HIGHEST_PROTOCOL)
            f.close()
        except:
            xbmc.log("An error occurred saving songs")
            pass

    # Duration to seconds
    def _setDuration(self, usecs):
        if usecs < 60000000:
            usecs = usecs * 10 # Some durations are 10x to small
        return int(usecs / 1000000)
    
    def _getSongStream(self, songid):
        id = int(songid)
        stream = None
        streams = []
        path = os.path.join(cacheDir, 'streams.dmp')
        try:
            f = open(path, 'rb')
            streams = pickle.load(f)
            for song in streams:
                if song[0] == id:
                    duration = song[1]
                    url = song[2]
                    key = song[3]
                    server = song[4]
                    stream = [id, duration, url, key, server]
                    if __debugging__ :
                        xbmc.log("Found " + str(id) + " in stream cache")
                    break;
            f.close()
        except:
            pass

        # Not in cache
        if stream == None:
            stream = groovesharkApi.getSubscriberStreamKey(songid)
            if stream != False and stream['url'] != '':
                duration = self._setDuration(stream['uSecs'])
                url = stream['url']
                key = stream['StreamKey']
                server = stream['StreamServerID']
                stream = [id, duration, url, key, server]
                self._addSongStream(stream)

        return stream
        
    def _addSongStream(self, stream):
        streams = self._getStreams()           
        streams.append(stream)                
        path = os.path.join(cacheDir, 'streams.dmp')
        try:
            f = open(path, 'wb')
            pickle.dump(streams, f, protocol=pickle.HIGHEST_PROTOCOL)
            f.close()
            if __debugging__ :
                xbmc.log("Added " + str(stream[0]) + " to stream cache")
        except:
            xbmc.log("An error occurred adding to stream")
    
    def _setSongStream(self, stream):
        id = int(stream[0])
        stream[1] = self._setDuration(stream[1])
        streams = self._getStreams()
        path = os.path.join(cacheDir, 'streams.dmp')
        i = 0

        for song in streams:
            if song[0] == id:
                streams[i] = stream
                try:
                    f = open(path, 'wb')
                    pickle.dump(streams, f, protocol=pickle.HIGHEST_PROTOCOL)
                    f.close()
                    if __debugging__ :
                        xbmc.log("Updated " + str(id) + " in stream cache")
                    break;
                except:
                    xbmc.log("An error occurred setting stream")                    
            i = i + 1
    
    def _getStreams(self):
        path = os.path.join(cacheDir, 'streams.dmp')
        try:
            f = open(path, 'rb')
            streams = pickle.load(f)
            f.close()
        except:
            streams = []
            pass
        return streams

    
# Parse URL parameters
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if __debugging__ :
        xbmc.log(paramstring)
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param
        
# Main
grooveshark = Grooveshark();

params=get_params()
mode=None
try: mode=int(params["mode"])
except: pass
id=0
try: id=int(params["id"])
except: pass
name = None
try: name=urllib.unquote_plus(params["name"])
except: pass

# Call function for URL
if mode==None:
    grooveshark.categories()
       
elif mode==MODE_SEARCH_SONGS:
    grooveshark.searchSongs()
    
elif mode==MODE_SEARCH_ALBUMS:
    grooveshark.searchAlbums()

elif mode==MODE_SEARCH_ARTISTS:
    grooveshark.searchArtists()
    
elif mode==MODE_SEARCH_ARTISTS_ALBUMS:
    grooveshark.searchArtistsAlbums(name)
    
elif mode==MODE_SEARCH_PLAYLISTS:
    grooveshark.searchPlaylists() 

elif mode==MODE_POPULAR_SONGS:
    grooveshark.popularSongs()
    
elif mode==MODE_ARTIST_POPULAR:
    grooveshark.artistPopularSongs()

elif mode==MODE_FAVORITES:
    grooveshark.favorites()

elif mode==MODE_PLAYLISTS:
    grooveshark.playlists()
    
elif mode==MODE_SONG_PAGE:
    try: offset=urllib.unquote_plus(params["offset"])
    except: pass
    try: label=urllib.unquote_plus(params["label"])
    except: pass
    grooveshark.songPage(offset, label, id, name)

elif mode==MODE_SONG:
    try: album=urllib.unquote_plus(params["album"])
    except: pass
    try: artist=urllib.unquote_plus(params["artist"])
    except: pass
    try: coverart=urllib.unquote_plus(params["coverart"])
    except: pass
    song = grooveshark.songItem(id, name, album, artist, coverart)
    grooveshark.playSong(song)

elif mode==MODE_ARTIST:
    grooveshark.artist(id)
    
elif mode==MODE_ALBUM:
    grooveshark.album(id)
    
elif mode==MODE_PLAYLIST:
    grooveshark.playlist(id, name)
    
elif mode==MODE_FAVORITE:
    grooveshark.favorite(id)
    
elif mode==MODE_UNFAVORITE:
    try: prevMode=int(urllib.unquote_plus(params["prevmode"]))
    except:
        prevMode = 0
    grooveshark.unfavorite(id, prevMode)

elif mode==MODE_SIMILAR_ARTISTS:
    grooveshark.similarArtists(id)

elif mode==MODE_MAKE_PLAYLIST:
    grooveshark.makePlaylist(id, name)
    
elif mode==MODE_REMOVE_PLAYLIST:
    grooveshark.removePlaylist(id, name)    

elif mode==MODE_RENAME_PLAYLIST:
    grooveshark.renamePlaylist(id, name)    

elif mode==MODE_REMOVE_PLAYLIST_SONG:
    try: playlistID=urllib.unquote_plus(params["playlistid"])
    except: pass
    grooveshark.removePlaylistSong(playlistID, name, id)

elif mode==MODE_ADD_PLAYLIST_SONG:
    grooveshark.addPlaylistSong(id)        
    
if mode < MODE_SONG:
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
