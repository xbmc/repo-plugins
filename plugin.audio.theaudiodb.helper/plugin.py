# -*- coding: utf-8 -*-
"""
TheAudioDB Helper - Plugin Handler

This module handles plugin:// URLs to provide video content lists.
"""

import sys
import urllib.parse
import json

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

# Import functions from videolinks module
from resources.lib import videolinks

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ICON = ADDON.getAddonInfo('icon')
LANGUAGE = ADDON.getLocalizedString

LOG_PREFIX = "[audio.theaudiodb.helper.Plugin] "


def log(msg, level=xbmc.LOGDEBUG):
    """Simple wrapper for Kodi logging."""
    xbmc.log(LOG_PREFIX + msg, level)


def get_artist_details(artist_id):
    """Get artist details from library"""
    rpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "AudioLibrary.GetArtistDetails",
        "params": {
            "artistid": int(artist_id),
            "properties": ["musicbrainzartistid"]
        }
    }
    
    response = xbmc.executeJSONRPC(json.dumps(rpc))
    data = json.loads(response)
    return data.get("result", {}).get("artistdetails", {})


def extract_video_id(tempurl):
    """Extract YouTube video ID from various URL formats"""
    if not tempurl:
        return ""
    
    # Ignorar URLs que son exactamente https://www.youtube.com/watch?v= (sin ID)
    if tempurl.strip() == "https://www.youtube.com/watch?v=":
        return ""
    
    vid_id = ""
    
    # Format: https://youtu.be/XXXXXXXXXXX
    youtu_be_index = tempurl.find('youtu.be/')
    if youtu_be_index != -1:
        vid_id = tempurl[youtu_be_index + 9:].split('?')[0].split('&')[0].strip()
    
    # Format: https://www.youtube.com/embed/XXXXXXXXXXX
    if not vid_id:
        embed_index = tempurl.find('/embed/')
        if embed_index != -1:
            vid_id = tempurl[embed_index + 7:embed_index + 18].strip()
    
    # Format: https://www.youtube.com/watch?v=XXXXXXXXXXX
    if not vid_id:
        index = tempurl.find('?v=')
        if index != -1:
            vid_id = tempurl[index + 3:].split('&')[0].strip()
        else:
            # Try v= anywhere (e.g. &v=)
            index = tempurl.find('v=')
            if index != -1:
                vid_id = tempurl[index + 2:].split('&')[0].strip()
    
    # Verificación final: asegurar que el ID no esté vacío
    return vid_id.strip() if vid_id and vid_id.strip() else ""


def list_missing_videos(artist_id):
    """
    List all music videos from theaudiodb.com that are NOT in the user's library.
    Returns items as a Kodi directory listing.
    """
    handle = int(sys.argv[1])
    
    # Get artist details
    artist_details = get_artist_details(artist_id)
    
    if not artist_details:
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    artist_mbid_list = artist_details.get('musicbrainzartistid', [])
    artist_name = artist_details.get('artist', 'Unknown')  # 'artist' is always in artistdetails
    
    # Get MBID - try from library first, then search by name
    artist_mbid = None
    if artist_mbid_list and artist_mbid_list[0]:
        artist_mbid = artist_mbid_list[0]
    else:
        # Try to get MBID from artist name
        artist_mbid = videolinks.get_mbid_from_artist_name(artist_name)
    
    # If still no MBID, can't continue
    if not artist_mbid:
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    # Get videolinks from theaudiodb using existing function
    try:
        mvid_data = videolinks.get_mvid_data(artist_mbid)
        mvidlist = mvid_data.get('mvids', [])
    except Exception as e:
        log(f"Error getting mvid data: {e}", xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    if not mvidlist:
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    # Get user's songs to filter using existing function
    songlist = videolinks.get_songs_for_artist(str(artist_id))
    user_track_ids = {song.get('musicbrainztrackid') for song in songlist if song.get('musicbrainztrackid')}
    user_track_titles = {song.get('title', '').lower() for song in songlist if song.get('title')}
    
    # Create directory items for missing videos
    added_count = 0
    seen_video_ids = set()  # Track video IDs to avoid duplicates
    
    for item in mvidlist:
        track_title = item.get('strTrack', 'Unknown')
        track_mbid = item.get('strMusicBrainzID')
        tempurl = item.get('strMusicVid', '')
        track_thumb = item.get('strTrackThumb', '')
        track_year = item.get('intYear')
        
        # Check if video is in user's library
        in_library = (track_mbid in user_track_ids) or (track_title.lower() in user_track_titles)
        
        # Only add if NOT in library
        if not in_library:
            vid_id = extract_video_id(tempurl)
            
            if not vid_id:
                continue
            
            # Skip if we've already added this video ID
            if vid_id in seen_video_ids:
                continue
            
            seen_video_ids.add(vid_id)
            
            video_url = f'plugin://plugin.video.youtube/play/?video_id={vid_id}'
            
            # Create list item
            list_item = xbmcgui.ListItem(label=track_title)
            
            # Set Label2 with the same value as Label
            list_item.setLabel2(track_title)
            
            # Use InfoTagMusic instead of deprecated setInfo
            info_tag = list_item.getMusicInfoTag()
            info_tag.setTitle(track_title)
            info_tag.setArtist(artist_name)
            info_tag.setMediaType('musicvideo')
            
            # Add year if available
            if track_year:
                try:
                    info_tag.setYear(int(track_year))
                except (ValueError, TypeError):
                    pass
            
            # Set artwork
            art = {}
            if track_thumb:
                art['thumb'] = track_thumb
            
            if art:
                list_item.setArt(art)
            
            # Mark as playable
            list_item.setProperty('IsPlayable', 'true')
            
            # Add to directory
            xbmcplugin.addDirectoryItem(
                handle=handle,
                url=video_url,
                listitem=list_item,
                isFolder=False
            )
            
            added_count += 1
    
    # Set content type
    xbmcplugin.setContent(handle, 'musicvideos')
    
    # Finish directory
    xbmcplugin.endOfDirectory(handle, succeeded=(added_count > 0))


def list_discography(artist_id):
    """
    List combined discography: local library albums + TheAudioDB albums.
    Local albums are listed first (with library properties), then TheAudioDB albums
    that are NOT in the library. All sorted by year ascending.
    """
    handle = int(sys.argv[1])
    
    # Get artist details
    artist_details = get_artist_details(artist_id)
    
    if not artist_details:
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    artist_name = artist_details.get('artist', 'Unknown')
    
    # Step 1: Get all albums from Kodi library for this artist
    library_albums = []
    library_titles_lower = set()
    try:
        rpc_albums = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "AudioLibrary.GetAlbums",
            "params": {
                "filter": {"artistid": int(artist_id)},
                "properties": ["title", "year", "thumbnail", "artist"]
            }
        }
        response = xbmc.executeJSONRPC(json.dumps(rpc_albums))
        data = json.loads(response)
        for lib_album in data.get("result", {}).get("albums", []):
            library_albums.append(lib_album)
            library_titles_lower.add(lib_album.get("title", "").lower())
    except Exception as e:
        log(f"Error getting library albums: {str(e)}", xbmc.LOGERROR)
    tadb_albums = []
    try:
        discography_data = videolinks.get_discography_data(artist_name)
        if discography_data and discography_data.get('album'):
            tadb_albums = discography_data.get('album', []) or []
    except Exception as e:
        log(f"Error getting discography data: {e}", xbmc.LOGERROR)
    
    # If both sources are empty, nothing to show
    if not library_albums and not tadb_albums:
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    # Step 3: Build combined list of albums to display
    # Each entry: (album_name, year_int, thumb_url, is_library, albumid)
    combined = []
    seen_albums = set()
    
    # Add library albums first
    for lib_album in library_albums:
        album_name = lib_album.get("title", "Unknown Album")
        album_key = album_name.lower()
        
        if album_key in seen_albums:
            continue
        seen_albums.add(album_key)
        
        year_int = lib_album.get("year", 0) or 0
        thumb = lib_album.get("thumbnail", "")
        albumid = lib_album.get("albumid", 0)
        
        # Try to get TheAudioDB thumb if library has no thumbnail
        if not thumb:
            for tadb_album in tadb_albums:
                if tadb_album.get('strAlbum', '').lower() == album_key:
                    thumb = tadb_album.get('strAlbumThumb', '')
                    # Also get year from TADB if library has none
                    if not year_int:
                        try:
                            year_int = int(tadb_album.get('intYearReleased', 0))
                        except (ValueError, TypeError):
                            pass
                    break
        
        combined.append({
            'name': album_name,
            'year': year_int,
            'thumb': thumb,
            'in_library': True,
            'albumid': albumid
        })
    
    # Step 3b: Add TheAudioDB albums that are NOT in the library
    for tadb_album in tadb_albums:
        album_name = tadb_album.get('strAlbum', 'Unknown Album')
        album_key = album_name.lower()
        
        # Skip if already added from library
        if album_key in seen_albums:
            continue
        seen_albums.add(album_key)
        
        year_int = 0
        try:
            year_int = int(tadb_album.get('intYearReleased', 0))
        except (ValueError, TypeError):
            year_int = 0
        
        combined.append({
            'name': album_name,
            'year': year_int,
            'thumb': tadb_album.get('strAlbumThumb', ''),
            'in_library': False,
            'albumid': 0
        })
    
    # Sort all albums by year ascending (albums without year go to the end)
    combined.sort(key=lambda x: (x['year'] if x['year'] > 0 else 99999))
    
    # Step 4: Create directory items
    added_count = 0
    
    for album in combined:
        album_name = album['name']
        year_int = album['year']
        album_thumb = album['thumb']
        
        # Create list item
        list_item = xbmcgui.ListItem(label=album_name)
        
        # Use InfoTagMusic instead of deprecated setInfo
        info_tag = list_item.getMusicInfoTag()
        info_tag.setTitle(album_name)
        info_tag.setArtist(artist_name)
        info_tag.setAlbum(album_name)
        info_tag.setMediaType('album')
        
        # Add year if available (only if greater than 0)
        if year_int > 0:
            info_tag.setYear(year_int)
            list_item.setLabel2(str(year_int))
        else:
            list_item.setLabel2('')
        
        # Set library properties if album exists in library
        if album['in_library'] and album['albumid']:
            library_albumid = str(album['albumid'])
            list_item.setProperty('library.albumid', library_albumid)
            list_item.setProperty('library.albumpath', f"musicdb://albums/{library_albumid}")
            list_item.setProperty('inlibrary', 'true')
        
        # Set artwork
        if album_thumb:
            art = {
                'thumb': album_thumb,
                'poster': album_thumb,
                'icon': album_thumb,
                'fanart': album_thumb
            }
            list_item.setArt(art)
        
        # Add to directory
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url='',
            listitem=list_item,
            isFolder=False
        )
        
        added_count += 1
    
    # Set content type
    xbmcplugin.setContent(handle, 'albums')
    
    # Finish directory
    xbmcplugin.endOfDirectory(handle, succeeded=(added_count > 0))


def list_similar_artists(artist_id):
    """
    List similar artists from Last.fm for the given artist.
    Returns items as a Kodi directory listing with artist images.
    Returns up to 9 similar artists.
    """
    handle = int(sys.argv[1])
    
    # Check if Last.fm is enabled
    use_lastfm = ADDON.getSettingBool('biography_use_lastfm')
    if not use_lastfm:
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    # Get artist details
    artist_details = get_artist_details(artist_id)
    
    if not artist_details:
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    artist_name = artist_details.get('artist', 'Unknown')
    
    # Get custom Last.fm API key if provided
    custom_lastfm_key = ADDON.getSettingString('lastfm_api_key').strip()
    
    # Get similar artists from Last.fm (up to 9)
    try:
        similar_artists = videolinks.get_lastfm_similar_artists(artist_name, limit=9, custom_api_key=custom_lastfm_key)
        
        if not similar_artists:
            xbmcplugin.endOfDirectory(handle, succeeded=False)
            return
        
    except Exception as e:
        log(f"Error getting Last.fm similar artists data: {e}", xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    # Get all artists from Kodi library (single call for performance)
    library_artists = {}
    try:
        rpc_artists = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "AudioLibrary.GetArtists",
            "params": {
                "properties": ["thumbnail", "fanart"]
            }
        }
        response = xbmc.executeJSONRPC(json.dumps(rpc_artists))
        data = json.loads(response)
        for artist in data.get("result", {}).get("artists", []):
            library_artists[artist.get("artist", "").lower()] = artist
    except Exception as e:
        log(f"Error getting library artists: {str(e)}", xbmc.LOGERROR)
    
    # Create directory items for similar artists
    added_count = 0
    
    for similar in similar_artists:
        artist_name_similar = similar.get('name', 'Unknown Artist')
        
        thumb_url = ""
        
        # Check if similar artist exists in Kodi library
        library_match = library_artists.get(artist_name_similar.lower())
        library_artistid = ""
        library_path = ""
        
        if library_match:
            library_artistid = str(library_match.get("artistid", ""))
            if library_artistid:
                library_path = f"musicdb://artists/{library_artistid}/"
        
        # Get image: prefer library art, fallback to TheAudioDB
        if library_match:
            # Try library thumbnail/fanart first
            thumb_url = library_match.get('thumbnail', '') or library_match.get('fanart', '')
        
        if not thumb_url:
            # Fallback to TheAudioDB (Last.fm API doesn't provide real images, only placeholders)
            try:
                tadb_info = videolinks.get_artist_info(artist_name_similar)
                if tadb_info:
                    # TheAudioDB provides artist thumb/logo/fanart
                    thumb_url = tadb_info.get('strArtistThumb') or tadb_info.get('strArtistFanart') or tadb_info.get('strArtistLogo')
            except Exception as e:
                log(f"Error getting image for similar artist: {str(e)}", xbmc.LOGERROR)
        
        # Create list item
        list_item = xbmcgui.ListItem(label=artist_name_similar)
        
        # Use InfoTagMusic instead of deprecated setInfo
        info_tag = list_item.getMusicInfoTag()
        info_tag.setTitle(artist_name_similar)
        info_tag.setArtist(artist_name_similar)
        info_tag.setMediaType('artist')
        
        # Set library properties if artist exists in library
        if library_artistid:
            list_item.setProperty('library.artistid', library_artistid)
            list_item.setProperty('library.artistpath', library_path)
            list_item.setProperty('inlibrary', 'true')
        
        # Set artwork if available
        if thumb_url:
            art = {
                'thumb': thumb_url,
                'poster': thumb_url,
                'icon': thumb_url,
                'fanart': thumb_url
            }
            list_item.setArt(art)
        
        # Add to directory (not playable, just informational)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url='',
            listitem=list_item,
            isFolder=False
        )
        
        added_count += 1
    
    # Set content type
    xbmcplugin.setContent(handle, 'artists')
    
    # Finish directory
    xbmcplugin.endOfDirectory(handle, succeeded=(added_count > 0))


def list_top_tracks(artist_id):
    """
    List top tracks from Last.fm for the given artist.
    Returns items as a Kodi directory listing with listener counts.
    Returns up to 9 top tracks, sorted by listener count (descending).
    """
    handle = int(sys.argv[1])
    
    # Check if Last.fm is enabled
    use_lastfm = ADDON.getSettingBool('biography_use_lastfm')
    if not use_lastfm:
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    # Get artist details
    artist_details = get_artist_details(artist_id)
    
    if not artist_details:
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    artist_name = artist_details.get('artist', 'Unknown')
    
    # Get custom Last.fm API key if provided
    custom_lastfm_key = ADDON.getSettingString('lastfm_api_key').strip()
    
    # Get top tracks from Last.fm
    try:
        top_tracks = videolinks.get_lastfm_top_tracks(artist_name, limit=9, custom_api_key=custom_lastfm_key)
        
        if not top_tracks:
            xbmcplugin.endOfDirectory(handle, succeeded=False)
            return
        
    except Exception as e:
        log(f"Error getting Last.fm top tracks data: {e}", xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    
    # Get all songs from this artist in Kodi library (single call for performance)
    artist_songs_library = {}
    album_cache = {}
    try:
        query = {
            "jsonrpc": "2.0",
            "method": "AudioLibrary.GetSongs",
            "params": {
                "filter": {"field": "artist", "operator": "is", "value": artist_name},
                "properties": ["title", "thumbnail", "albumid", "art", "file"]
            },
            "id": 1
        }
        
        response = xbmc.executeJSONRPC(json.dumps(query))
        response_json = json.loads(response)
        
        if 'result' in response_json and 'songs' in response_json['result']:
            # Create a dictionary for fast lookup by song title
            for song in response_json['result']['songs']:
                song_title = song.get('title', '').lower()
                artist_songs_library[song_title] = song
    except Exception as e:
        log(f"Error getting library songs: {str(e)}", xbmc.LOGERROR)
    
    # Create directory items for top tracks
    added_count = 0
    
    # Sort tracks by listeners (descending order)
    sorted_tracks = sorted(top_tracks, key=lambda x: int(x.get('listeners', 0)), reverse=True)
    
    # Calculate max listeners for normalization (for progress bar visualization)
    max_listeners = max(int(track.get('listeners', 0)) for track in sorted_tracks) if sorted_tracks else 1
    
    for track in sorted_tracks:
        track_name = track.get('name', 'Unknown Track')
        listeners = track.get('listeners', '')
        
        # Create list item
        list_item = xbmcgui.ListItem(label=track_name)
        
        # Set Label2 with listener count formatted with thousands separator
        # and calculate percentage for progress bar
        if listeners:
            try:
                # Format number with dots as thousands separator (e.g., 1.405.896)
                listeners_int = int(listeners)
                listeners_formatted = f"{listeners_int:,}".replace(',', '.')
                list_item.setLabel2(listeners_formatted)
                
                # Calculate percentage relative to most listened track (0-100)
                percent = int((listeners_int / max_listeners) * 100) if max_listeners > 0 else 0
                list_item.setProperty('percent.listened', str(percent))
            except (ValueError, TypeError):
                list_item.setLabel2('')
                list_item.setProperty('percent.listened', '0')
        else:
            list_item.setLabel2('')
            list_item.setProperty('percent.listened', '0')
        
        # Use InfoTagMusic instead of deprecated setInfo
        info_tag = list_item.getMusicInfoTag()
        info_tag.setTitle(track_name)
        info_tag.setArtist(artist_name)
        info_tag.setMediaType('song')
        
        # Try to get album art from Kodi library if the song exists
        track_name_lower = track_name.lower()
        if track_name_lower in artist_songs_library:
            song = artist_songs_library[track_name_lower]
            
            # Store file path for skin to use with PlayMedia("path")
            file_path = song.get('file', '')
            if file_path:
                list_item.setProperty('library.filepath', file_path)
            
            # Priority order: videothumb > thumbnail > album art
            # First check if song has videothumb in art
            art_dict = song.get('art', {})
            videothumb = art_dict.get('videothumb', '') if isinstance(art_dict, dict) else ''
            
            if videothumb:
                # Use videothumb if available (highest priority)
                list_item.setArt({'thumb': videothumb, 'icon': videothumb})
            else:
                # Fall back to regular thumbnail
                thumbnail = song.get('thumbnail', '')
                
                if thumbnail:
                    list_item.setArt({'thumb': thumbnail, 'icon': thumbnail})
                elif 'albumid' in song and song['albumid'] > 0:
                    album_id = song['albumid']
                    
                    # Check if we already have this album in cache
                    if album_id in album_cache:
                        album_thumb = album_cache[album_id]
                        if album_thumb:
                            list_item.setArt({'thumb': album_thumb, 'icon': album_thumb})
                    else:
                        # Get album details to retrieve album art
                        try:
                            album_query = {
                                "jsonrpc": "2.0",
                                "method": "AudioLibrary.GetAlbumDetails",
                                "params": {
                                    "albumid": album_id,
                                    "properties": ["thumbnail"]
                                },
                                "id": 2
                            }
                            album_response = xbmc.executeJSONRPC(json.dumps(album_query))
                            album_json = json.loads(album_response)
                            
                            if 'result' in album_json and 'albumdetails' in album_json['result']:
                                album_thumb = album_json['result']['albumdetails'].get('thumbnail', '')
                                album_cache[album_id] = album_thumb  # Cache for other songs from same album
                                if album_thumb:
                                    list_item.setArt({'thumb': album_thumb, 'icon': album_thumb})
                        except Exception as e:
                            log(f"Error getting album thumbnail: {str(e)}", xbmc.LOGERROR)
        
        # Add to directory (not playable, just informational)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url='',
            listitem=list_item,
            isFolder=False
        )
        
        added_count += 1
    
    # Set content type
    xbmcplugin.setContent(handle, 'songs')
    
    # Finish directory
    xbmcplugin.endOfDirectory(handle, succeeded=(added_count > 0))






def play_song(filepath):
    """
    Play a song from the given filepath.
    """
    if filepath:
        player = xbmc.Player()
        player.play(filepath)
        log(f"Playing: {filepath}")


def router(paramstring):
    """
    Router function that parses the plugin URL and directs to the appropriate function.
    """
    params = dict(urllib.parse.parse_qsl(paramstring))
    
    action = params.get('action')
    artist_id = params.get('artistid')
    filepath = params.get('filepath')
    
    if action == 'play' and filepath:
        play_song(filepath)
    elif action in ('missing_videos', 'discography', 'similars', 'toptracks'):
        # These actions are restricted to DialogMusicInfo
        if not xbmc.getCondVisibility('Window.IsActive(musicinformation) | Window.IsActive(songinformation)'):
            log(f"Plugin action '{action}' blocked - only allowed from DialogMusicInfo", xbmc.LOGINFO)
            handle = int(sys.argv[1])
            xbmcplugin.endOfDirectory(handle, succeeded=False)
        elif action == 'missing_videos' and artist_id:
            list_missing_videos(artist_id)
        elif action == 'discography' and artist_id:
            list_discography(artist_id)
        elif action == 'similars' and artist_id:
            list_similar_artists(artist_id)
        elif action == 'toptracks' and artist_id:
            list_top_tracks(artist_id)
        else:
            handle = int(sys.argv[1])
            xbmcplugin.endOfDirectory(handle, succeeded=False)
    else:
        # No valid action - return empty directory
        handle = int(sys.argv[1])
        xbmcplugin.endOfDirectory(handle, succeeded=False)


if __name__ == '__main__':
    try:
        # Get the plugin parameters
        paramstring = sys.argv[2][1:] if len(sys.argv) > 2 else ""
        router(paramstring)
    except Exception as e:
        log(f"Plugin error: {e}", xbmc.LOGERROR)
        import traceback
        log(traceback.format_exc(), xbmc.LOGERROR)
        handle = int(sys.argv[1])
        xbmcplugin.endOfDirectory(handle, succeeded=False)
