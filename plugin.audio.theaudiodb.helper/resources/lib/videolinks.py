#!/usr/bin/python
# -*- coding: utf-8 -*-

#  (c) 2023 black_eagle
#  Unified version for single_artist: first delete videolinks, then add new ones
#  process_all_artists: only add new videolinks (original behavior)

import xbmc
import xbmcaddon
import xbmcgui

import json
import os
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from urllib.error import URLError

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
ADDONNAME = ADDON.getAddonInfo('name')
ADDONVERSION = ADDON.getAddonInfo('version')
ICON = ADDON.getAddonInfo('icon')
FANART = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'art', 'fanart.jpg')
FANART2 = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'art', 'fanart2.jpg')
LANGUAGE = ADDON.getLocalizedString

# Global variable to control which fanart to use
USE_FANART2 = False

AUDIODBKEY = '95424d43204d6564696538'
AUDIODBURL = 'https://www.theaudiodb.com/api/v1/json/%s/%s'
AUDIODBMVIDS = 'mvid-mb.php?i=%s'
AUDIODBSEARCH = 'search.php?s=%s'
AUDIODBDISCOGRAPHY = 'discography.php?s=%s'
AUDIODBALBUM = 'searchalbum.php?s=%s'

# Default Last.fm API key
LASTFM_DEFAULT_KEY = '13609a82a11cd2d54538abf3da577794'


# ---------------------------------------------------------------------
# Background window
# ---------------------------------------------------------------------

class FanartBackground(xbmcgui.Window):
    def __init__(self):
        super(FanartBackground, self).__init__()
        fanart_image = FANART2 if USE_FANART2 else FANART
        self.background = xbmcgui.ControlImage(0, 0, 1280, 720, fanart_image, aspectRatio=2)
        self.addControl(self.background)


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

def log(txt, level=xbmc.LOGDEBUG):
    message = '%s: %s' % (LANGUAGE(30000), txt)
    xbmc.log(msg=message, level=level)


# ---------------------------------------------------------------------
# BLOCK 1: DELETE videolinks
# ---------------------------------------------------------------------

def clear_videolinks_for_artist(artist_id):
    log(f"Clearing videolinks for artistid={artist_id}")

    rpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "AudioLibrary.GetSongs",
        "params": {
            "filter": {"artistid": int(artist_id)},
            "properties": ["songvideourl"]
        }
    }

    response = xbmc.executeJSONRPC(json.dumps(rpc))
    data = json.loads(response)

    songs = data.get("result", {}).get("songs", [])
    if not songs:
        log("No songs found for artist")
        return 0

    cleared = 0

    for song in songs:
        if not song.get("songvideourl"):
            continue

        songid = song["songid"]

        rpc_clear = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "AudioLibrary.SetSongDetails",
            "params": {
                "songid": songid,
                "songvideourl": "",
                "art": {}
            }
        }

        xbmc.executeJSONRPC(json.dumps(rpc_clear))
        cleared += 1
        xbmc.sleep(5)

    log(f"Cleared videolinks for {cleared} songs")
    return cleared


# ---------------------------------------------------------------------
# BLOCK 2: ADD new videolinks
# ---------------------------------------------------------------------

def get_mbid_from_artist_name(artist_name):
    """
    Search for artist MBID using artist name in TheAudioDB.
    Returns the MBID of the first result found, or None if not found.
    """
    if not artist_name:
        return None
    
    # URL encode the artist name
    encoded_name = urllib.parse.quote(artist_name)
    searchurl = AUDIODBURL % (AUDIODBKEY, AUDIODBSEARCH % encoded_name)
    
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    
    try:
        req = urllib.request.Request(searchurl, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        search_data = json.loads(respdata)
        
        # Check if we got results
        artists = search_data.get('artists')
        if artists and len(artists) > 0:
            # Get the first result's MBID
            first_artist = artists[0]
            mbid = first_artist.get('strMusicBrainzID')
            
            if mbid:
                log(f"Found MBID via name search for '{artist_name}': {mbid}")
                return mbid
            else:
                log(f"No MBID found in search results for '{artist_name}'")
                return None
        else:
            log(f"No artist found in TheAudioDB for name: '{artist_name}'")
            return None
            
    except HTTPError as e:
        log(f"HTTP Error searching for artist '{artist_name}': {e.code} {e.reason}", xbmc.LOGWARNING)
        return None
    except URLError as e:
        log(f"URL Error searching for artist '{artist_name}': {e.reason}", xbmc.LOGWARNING)
        return None
    except Exception as e:
        log(f"Error searching for artist '{artist_name}': {str(e)}", xbmc.LOGWARNING)
        return None


def get_artist_info(artist_name):
    """
    Get complete artist information from TheAudioDB.
    Returns the full artist data dictionary or None if not found.
    """
    if not artist_name:
        return None
    
    # URL encode the artist name
    encoded_name = urllib.parse.quote(artist_name)
    searchurl = AUDIODBURL % (AUDIODBKEY, AUDIODBSEARCH % encoded_name)
    
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    
    try:
        req = urllib.request.Request(searchurl, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        search_data = json.loads(respdata)
        
        # Check if we got results
        artists = search_data.get('artists')
        if artists and len(artists) > 0:
            # Return the first result with all its data
            return artists[0]
        else:
            return None
            
    except Exception as e:
        log(f"Error getting artist info for '{artist_name}': {str(e)}", xbmc.LOGERROR)
        return None


def get_lastfm_artist_info(artist_name, lang='en', custom_api_key=''):
    """
    Get artist information from Last.fm API.
    Returns artist data dictionary or None if not found.
    
    Args:
        artist_name: Name of the artist
        lang: Language code (en, es, de, fr, etc.)
        custom_api_key: Optional custom Last.fm API key (if empty, uses default)
    """
    if not artist_name:
        return None
    
    # Use custom API key if provided, otherwise use default
    if custom_api_key:
        LASTFM_API_KEY = custom_api_key
        log(f"Using custom Last.fm API key for '{artist_name}'")
    else:
        # Default Last.fm API key for TheAudioDB Helper
        LASTFM_API_KEY = LASTFM_DEFAULT_KEY
    
    # URL encode the artist name
    encoded_name = urllib.parse.quote(artist_name)
    
    # Build Last.fm API URL
    lastfm_url = f"https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={encoded_name}&api_key={LASTFM_API_KEY}&format=json&lang={lang}"
    
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    
    try:
        req = urllib.request.Request(lastfm_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        data = json.loads(respdata)
        
        # Check if we got a valid response
        if 'artist' in data:
            return data['artist']
        else:
            return None
            
    except Exception as e:
        log(f"Error getting Last.fm info for '{artist_name}': {str(e)}", xbmc.LOGERROR)
        return None


def get_lastfm_similar_artists(artist_name, limit=9, custom_api_key=''):
    """
    Get similar artists from Last.fm API using artist.getSimilar method.
    Returns list of similar artists or empty list if not found.
    
    Args:
        artist_name: Name of the artist
        limit: Maximum number of similar artists to return (default: 9, max: 30)
        custom_api_key: Optional custom Last.fm API key (if empty, uses default)
    """
    if not artist_name:
        return []
    
    # Use custom API key if provided, otherwise use default
    if custom_api_key:
        LASTFM_API_KEY = custom_api_key
    else:
        # Default Last.fm API key for TheAudioDB Helper
        LASTFM_API_KEY = LASTFM_DEFAULT_KEY
    
    # URL encode the artist name
    encoded_name = urllib.parse.quote(artist_name)
    
    # Build Last.fm API URL for artist.getSimilar
    lastfm_url = f"https://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist={encoded_name}&api_key={LASTFM_API_KEY}&format=json&limit={limit}"
    
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    
    try:
        req = urllib.request.Request(lastfm_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        data = json.loads(respdata)
        
        # Check if we got a valid response
        similar_artists = data.get('similarartists', {}).get('artist', [])
        
        if isinstance(similar_artists, list):
            return similar_artists
        else:
            return []
            
    except Exception as e:
        log(f"Error getting Last.fm similar artists for '{artist_name}': {str(e)}", xbmc.LOGERROR)
        return []


def get_lastfm_top_tracks(artist_name, limit=9, custom_api_key=''):
    """
    Get top tracks from Last.fm API using artist.getTopTracks method.
    Returns list of top tracks or empty list if not found.
    
    Args:
        artist_name: Name of the artist
        limit: Maximum number of tracks to return (default: 9)
        custom_api_key: Optional custom Last.fm API key (if empty, uses default)
    """
    if not artist_name:
        return []
    
    # Use custom API key if provided, otherwise use default
    if custom_api_key:
        LASTFM_API_KEY = custom_api_key
    else:
        # Default Last.fm API key for TheAudioDB Helper
        LASTFM_API_KEY = LASTFM_DEFAULT_KEY
    
    # URL encode the artist name
    encoded_name = urllib.parse.quote(artist_name)
    
    # Build Last.fm API URL for artist.getTopTracks
    lastfm_url = f"https://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={encoded_name}&api_key={LASTFM_API_KEY}&format=json&limit={limit}"
    
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    
    try:
        req = urllib.request.Request(lastfm_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        data = json.loads(respdata)
        
        # Check if we got a valid response
        top_tracks = data.get('toptracks', {}).get('track', [])
        
        if isinstance(top_tracks, list):
            return top_tracks
        else:
            return []
            
    except Exception as e:
        log(f"Error getting Last.fm top tracks for '{artist_name}': {str(e)}", xbmc.LOGERROR)
        return []


def get_wikipedia_biography(artist_name, lang='en'):
    """
    Get artist biography from Wikipedia API.
    Returns biography text or None if not found.
    
    Args:
        artist_name: Name of the artist
        lang: Language code (en, es, de, fr, etc.)
    """
    if not artist_name:
        return None
    
    # URL encode the artist name
    encoded_name = urllib.parse.quote(artist_name)
    
    # Build Wikipedia API URL
    # Using action=query&prop=extracts to get article content
    wikipedia_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=1&explaintext=1&titles={encoded_name}"
    
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    
    try:
        req = urllib.request.Request(wikipedia_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        data = json.loads(respdata)
        
        # Wikipedia API returns pages as a dictionary with page IDs as keys
        pages = data.get('query', {}).get('pages', {})
        
        if not pages:
            return None
        
        # Get the first (and should be only) page
        page_id = list(pages.keys())[0]
        
        # If page_id is -1, the page doesn't exist
        if page_id == '-1':
            return None
        
        page_data = pages[page_id]
        extract = page_data.get('extract', '')
        
        # Check if we have actual content
        if extract and len(extract.strip()) > 0:
            return extract.strip()
        else:
            return None
            
    except Exception as e:
        log(f"Error getting Wikipedia info for '{artist_name}' in language '{lang}': {str(e)}", xbmc.LOGERROR)
        return None


def get_discography_data(artist_name):
    """
    Get discography data from TheAudioDB using artist name.
    Returns a dictionary with album information including covers.
    """
    if not artist_name:
        return None
    
    # URL encode the artist name
    encoded_name = urllib.parse.quote(artist_name)
    
    # First get the album list with covers using searchalbum endpoint
    album_url = AUDIODBURL % (AUDIODBKEY, AUDIODBALBUM % encoded_name)
    
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    
    try:
        req = urllib.request.Request(album_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        album_data = json.loads(respdata)
        
        # The searchalbum endpoint returns albums with strAlbumThumb included
        return album_data
        
    except HTTPError as e:
        log(f"HTTP Error getting discography for '{artist_name}': {e.code} {e.reason}", xbmc.LOGWARNING)
        return None
    except URLError as e:
        log(f"URL Error getting discography for '{artist_name}': {e.reason}", xbmc.LOGWARNING)
        return None
    except Exception as e:
        log(f"Error getting discography for '{artist_name}': {str(e)}", xbmc.LOGWARNING)
        return None



def get_album_info(artist_name, album_name):
    """
    Get specific album information from TheAudioDB using artist name and album name.
    Uses searchalbum.php?s=artist&a=album endpoint to find the album,
    then enriches with album.php?m=idAlbum lookup for complete artwork fields.
    Returns the album data dictionary or None if not found.
    """
    if not artist_name or not album_name:
        return None
    
    encoded_artist = urllib.parse.quote(artist_name)
    encoded_album = urllib.parse.quote(album_name)
    
    album_url = f"https://www.theaudiodb.com/api/v1/json/{AUDIODBKEY}/searchalbum.php?s={encoded_artist}&a={encoded_album}"
    
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    
    try:
        req = urllib.request.Request(album_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        data = json.loads(respdata)
        
        albums = data.get('album')
        if albums and len(albums) > 0:
            album = albums[0]
            
            # The searchalbum endpoint may use different field names than album.php lookup.
            # Enrich with album.php?m=idAlbum to get complete/updated artwork fields.
            album_id = album.get('idAlbum')
            if album_id:
                lookup_data = _get_album_lookup(album_id, headers)
                if lookup_data:
                    # Merge lookup data into search data (lookup takes priority for artwork)
                    for key, value in lookup_data.items():
                        if value is not None and (album.get(key) is None or album.get(key) == ""):
                            album[key] = value
                        # Also map renamed fields: strAlbumBack (lookup) -> strAlbumThumbBack (legacy)
                        if key == 'strAlbumBack' and value:
                            album['strAlbumThumbBack'] = value
            
            return album
        else:
            return None
            
    except Exception as e:
        log(f"Error getting album info for '{artist_name}' - '{album_name}': {str(e)}", xbmc.LOGERROR)
        return None


def _get_album_lookup(album_id, headers):
    """
    Lookup album details by TheAudioDB album ID using album.php?m= endpoint.
    Returns the album data dictionary or None if not found.
    """
    if not album_id:
        return None
    
    lookup_url = f"https://www.theaudiodb.com/api/v1/json/{AUDIODBKEY}/album.php?m={album_id}"
    
    try:
        req = urllib.request.Request(lookup_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        data = json.loads(respdata)
        
        albums = data.get('album')
        if albums and len(albums) > 0:
            return albums[0]
        else:
            return None
            
    except Exception as e:
        log(f"Error looking up album ID '{album_id}': {str(e)}", xbmc.LOGERROR)
        return None


def get_lastfm_album_info(artist_name, album_name, lang='en', custom_api_key=''):
    """
    Get album information from Last.fm API using album.getinfo method.
    Returns album data dictionary or None if not found.
    
    Args:
        artist_name: Name of the artist
        album_name: Name of the album
        lang: Language code (en, es, de, fr, etc.)
        custom_api_key: Optional custom Last.fm API key (if empty, uses default)
    """
    if not artist_name or not album_name:
        return None
    
    if custom_api_key:
        LASTFM_API_KEY = custom_api_key
    else:
        LASTFM_API_KEY = LASTFM_DEFAULT_KEY
    
    encoded_artist = urllib.parse.quote(artist_name)
    encoded_album = urllib.parse.quote(album_name)
    
    lastfm_url = f"https://ws.audioscrobbler.com/2.0/?method=album.getinfo&artist={encoded_artist}&album={encoded_album}&api_key={LASTFM_API_KEY}&format=json&lang={lang}"
    
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    
    try:
        req = urllib.request.Request(lastfm_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        data = json.loads(respdata)
        
        if 'album' in data:
            return data['album']
        else:
            return None
            
    except Exception as e:
        log(f"Error getting Last.fm album info for '{artist_name}' - '{album_name}': {str(e)}", xbmc.LOGERROR)
        return None


def get_track_info(artist_name, album_name, track_name):
    """
    Get track information from TheAudioDB.
    Strategy: 
    1) searchtrack.php?s={artist}&t={track} for direct search
    2) Fallback: search album, get all tracks, find matching track
    3) Enrich with track.php?h={idTrack} for complete multilingual data
    Returns the track data dictionary or None if not found.
    """
    if not artist_name or not track_name:
        return None

    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))

    track_data = None

    # Step 1: Direct search by artist + track name
    try:
        encoded_artist = urllib.parse.quote(artist_name)
        encoded_track = urllib.parse.quote(track_name)
        search_url = f"https://www.theaudiodb.com/api/v1/json/{AUDIODBKEY}/searchtrack.php?s={encoded_artist}&t={encoded_track}"

        req = urllib.request.Request(search_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        data = json.loads(respdata)

        tracks = data.get('track')
        if tracks and len(tracks) > 0:
            track_name_lower = track_name.lower().strip()
            for track in tracks:
                tadb_track_name = (track.get('strTrack', '') or '').lower().strip()
                if tadb_track_name == track_name_lower:
                    track_data = track
                    break
            # Fallback: partial match
            if not track_data:
                for track in tracks:
                    tadb_track_name = (track.get('strTrack', '') or '').lower().strip()
                    if track_name_lower in tadb_track_name or tadb_track_name in track_name_lower:
                        track_data = track
                        break
    except Exception as e:
        log(f"Error searching track '{track_name}' by '{artist_name}': {str(e)}", xbmc.LOGERROR)

    # Step 2: Fallback - search via album tracks if direct search failed
    if not track_data and album_name:
        try:
            album_data = get_album_info(artist_name, album_name)
            if album_data:
                album_id = album_data.get('idAlbum')
                if album_id:
                    track_url = f"https://www.theaudiodb.com/api/v1/json/{AUDIODBKEY}/track.php?m={album_id}"
                    req = urllib.request.Request(track_url, headers=headers)
                    resp = urllib.request.urlopen(req, timeout=5)
                    respdata = resp.read()
                    data = json.loads(respdata)

                    tracks = data.get('track')
                    if tracks and len(tracks) > 0:
                        track_name_lower = track_name.lower().strip()
                        for track in tracks:
                            tadb_track_name = (track.get('strTrack', '') or '').lower().strip()
                            if tadb_track_name == track_name_lower:
                                track_data = track
                                break
                        if not track_data:
                            for track in tracks:
                                tadb_track_name = (track.get('strTrack', '') or '').lower().strip()
                                if track_name_lower in tadb_track_name or tadb_track_name in track_name_lower:
                                    track_data = track
                                    break
        except Exception as e:
            log(f"Error getting track via album for '{track_name}' by '{artist_name}': {str(e)}", xbmc.LOGERROR)

    # Step 3: Enrich with individual track lookup for complete data (all description languages)
    if track_data:
        track_id = track_data.get('idTrack')
        if track_id:
            try:
                lookup_url = f"https://www.theaudiodb.com/api/v1/json/{AUDIODBKEY}/track.php?h={track_id}"
                req = urllib.request.Request(lookup_url, headers=headers)
                resp = urllib.request.urlopen(req, timeout=5)
                respdata = resp.read()
                lookup_data = json.loads(respdata)

                lookup_tracks = lookup_data.get('track')
                if lookup_tracks and len(lookup_tracks) > 0:
                    full_track = lookup_tracks[0]
                    # Merge: lookup data takes priority for non-empty values
                    for key, value in full_track.items():
                        if value is not None and (track_data.get(key) is None or track_data.get(key) == ""):
                            track_data[key] = value
            except Exception as e:
                log(f"Error looking up track ID '{track_id}': {str(e)}", xbmc.LOGERROR)

    return track_data


def get_lrclib_lyrics(artist_name, track_name):
    """
    Get plain lyrics from lrclib.net API.
    Returns the plain lyrics string or None if not found.
    No API key required.
    """
    if not artist_name or not track_name:
        return None

    import difflib

    encoded_query = urllib.parse.quote(f"{artist_name} {track_name}")
    search_url = f"https://lrclib.net/api/search?q={encoded_query}"

    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))

    try:
        req = urllib.request.Request(search_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        respdata = resp.read()
        result = json.loads(respdata)

        if not result or not isinstance(result, list):
            return None

        # Find best match using fuzzy matching
        for item in result:
            artistname = item.get('artistName', '')
            songtitle = item.get('trackName', '') or item.get('name', '')
            if (difflib.SequenceMatcher(None, artist_name.lower(), artistname.lower()).ratio() > 0.8) and \
               (difflib.SequenceMatcher(None, track_name.lower(), songtitle.lower()).ratio() > 0.8):
                # Prefer plainLyrics (no timestamps)
                plain = item.get('plainLyrics')
                if plain:
                    return plain
                # Fallback: strip timestamps from syncedLyrics
                synced = item.get('syncedLyrics')
                if synced:
                    import re
                    stripped = re.sub(r'\[\d{2}:\d{2}\.\d{2,3}\]\s?', '', synced)
                    return stripped.strip()

        return None

    except Exception as e:
        log(f"Error getting lyrics from lrclib for '{track_name}' by '{artist_name}': {str(e)}", xbmc.LOGERROR)
        return None


def _strip_lrc_timestamps(synced_text):
    """Strip LRC timestamps from synced lyrics, returning plain text."""
    import re
    stripped = re.sub(r'\[\d{2}:\d{2}[.:]\d{2,3}\]\s?', '', synced_text)
    # Also remove metadata tags like [ar:Artist], [ti:Title], etc.
    stripped = re.sub(r'\[[a-z]{2}:.*?\]\s*\n?', '', stripped)
    return stripped.strip()


def get_netease_lyrics(artist_name, track_name):
    """
    Get lyrics from NetEase Cloud Music API.
    Returns plain lyrics string (timestamps stripped) or None if not found.
    No API key required.
    """
    if not artist_name or not track_name:
        return None

    try:
        # Step 1: Search for the track
        search_url = 'https://music.163.com/api/search/get/web'
        search_data = urllib.parse.urlencode({
            's': f"{artist_name} {track_name}",
            'type': 1,
            'limit': 5
        }).encode('utf-8')

        headers = {
            'User-Agent': '%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION),
            'Referer': 'https://music.163.com/',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        req = urllib.request.Request(search_url, data=search_data, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())

        songs = result.get('result', {}).get('songs', [])
        if not songs:
            return None

        # Find best match using fuzzy matching
        import difflib
        song_id = None
        for song in songs:
            netease_title = song.get('name', '')
            netease_artists = [a.get('name', '') for a in song.get('artists', [])]
            netease_artist = netease_artists[0] if netease_artists else ''

            title_ratio = difflib.SequenceMatcher(None, track_name.lower(), netease_title.lower()).ratio()
            artist_ratio = difflib.SequenceMatcher(None, artist_name.lower(), netease_artist.lower()).ratio()

            if title_ratio > 0.7 and artist_ratio > 0.7:
                song_id = song.get('id')
                break

        if not song_id:
            return None

        # Step 2: Get lyrics for the song
        lyrics_url = f'https://music.163.com/api/song/lyric?id={song_id}&lv=1&tv=-1'
        req = urllib.request.Request(lyrics_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        lyrics_data = json.loads(resp.read())

        # Try synced lyrics first (lrc field), then plain
        lrc = lyrics_data.get('lrc', {}).get('lyric', '')
        if lrc:
            return _strip_lrc_timestamps(lrc)

        return None

    except Exception as e:
        log(f"Error getting lyrics from NetEase for '{track_name}' by '{artist_name}': {str(e)}", xbmc.LOGERROR)
        return None


def get_megalobiz_lyrics(artist_name, track_name):
    """
    Get lyrics from Megalobiz.com by scraping search results.
    Returns plain lyrics string (timestamps stripped) or None if not found.
    No API key required.
    """
    if not artist_name or not track_name:
        return None

    try:
        encoded_query = urllib.parse.quote(f"{artist_name} {track_name}")
        search_url = f"https://www.megalobiz.com/search/all?qry={encoded_query}&searchButton.x=0&searchButton.y=0"

        headers = {
            'User-Agent': '%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION)
        }

        req = urllib.request.Request(search_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode('utf-8', errors='replace')

        # Find the first LRC link in search results
        import re
        lrc_match = re.search(r'href="(/lrc/maker/[^"]+)"', html)
        if not lrc_match:
            return None

        # Fetch the LRC page
        lrc_url = f"https://www.megalobiz.com{lrc_match.group(1)}"
        req = urllib.request.Request(lrc_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        lrc_html = resp.read().decode('utf-8', errors='replace')

        # Extract LRC content from the span with class "lyrics_details"
        lrc_content_match = re.search(
            r'<span[^>]*class="[^"]*lyrics_details[^"]*"[^>]*>(.*?)</span>',
            lrc_html, re.DOTALL
        )
        if not lrc_content_match:
            return None

        lrc_raw = lrc_content_match.group(1)
        # Clean HTML tags
        lrc_text = re.sub(r'<br\s*/?>', '\n', lrc_raw)
        lrc_text = re.sub(r'<[^>]+>', '', lrc_text)
        # Unescape HTML entities
        import html as html_module
        lrc_text = html_module.unescape(lrc_text)

        if lrc_text.strip():
            return _strip_lrc_timestamps(lrc_text)

        return None

    except Exception as e:
        log(f"Error getting lyrics from Megalobiz for '{track_name}' by '{artist_name}': {str(e)}", xbmc.LOGERROR)
        return None


def get_lyricsovh_lyrics(artist_name, track_name):
    """
    Get plain lyrics from lyrics.ovh API.
    Returns the plain lyrics string or None if not found.
    No API key required.
    """
    if not artist_name or not track_name:
        return None

    try:
        encoded_artist = urllib.parse.quote(artist_name)
        encoded_title = urllib.parse.quote(track_name)
        url = f"https://api.lyrics.ovh/v1/{encoded_artist}/{encoded_title}"

        headers = {
            'User-Agent': '%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION)
        }

        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())

        lyrics = result.get('lyrics', '')
        if lyrics and lyrics.strip():
            return lyrics.strip()

        return None

    except Exception as e:
        log(f"Error getting lyrics from lyrics.ovh for '{track_name}' by '{artist_name}': {str(e)}", xbmc.LOGERROR)
        return None


def get_lyrics_cascaded(artist_name, track_name):
    """
    Get lyrics using a cascade of providers.
    Tries each provider in order until lyrics are found.
    Returns a tuple (lyrics_text, source_name) or (None, None) if not found.

    Provider order:
    1. LRCLIB (synced + plain, largest open-source DB)
    2. NetEase (synced, large catalog especially Asian music)
    3. Megalobiz (synced, good for older tracks)
    4. lyrics.ovh (plain text, last resort)
    """
    if not artist_name or not track_name:
        return None, None

    # 1. LRCLIB (existing function)
    lyrics = get_lrclib_lyrics(artist_name, track_name)
    if lyrics:
        return lyrics, "LRCLIB"

    # 2. NetEase
    lyrics = get_netease_lyrics(artist_name, track_name)
    if lyrics:
        return lyrics, "NetEase"

    # 3. Megalobiz
    lyrics = get_megalobiz_lyrics(artist_name, track_name)
    if lyrics:
        return lyrics, "Megalobiz"

    # 4. lyrics.ovh (plain text only, last resort)
    lyrics = get_lyricsovh_lyrics(artist_name, track_name)
    if lyrics:
        return lyrics, "lyrics.ovh"

    return None, None


def get_lastfm_track_info(artist_name, track_name, lang='en', custom_api_key=''):
    """
    Get track information from Last.fm API using track.getInfo method.
    Returns track data dictionary or None if not found.

    Args:
        artist_name: Name of the artist
        track_name: Name of the track
        lang: Language code (en, es, de, fr, etc.)
        custom_api_key: Optional custom Last.fm API key (if empty, uses default)
    """
    if not artist_name or not track_name:
        return None

    if custom_api_key:
        LASTFM_API_KEY = custom_api_key
    else:
        LASTFM_API_KEY = LASTFM_DEFAULT_KEY

    encoded_artist = urllib.parse.quote(artist_name)
    encoded_track = urllib.parse.quote(track_name)

    lastfm_url = f"https://ws.audioscrobbler.com/2.0/?method=track.getinfo&artist={encoded_artist}&track={encoded_track}&api_key={LASTFM_API_KEY}&format=json&lang={lang}"

    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))

    try:
        req = urllib.request.Request(lastfm_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        data = json.loads(respdata)

        if 'track' in data:
            return data['track']
        else:
            return None

    except Exception as e:
        log(f"Error getting Last.fm track info for '{track_name}' by '{artist_name}': {str(e)}", xbmc.LOGERROR)
        return None


def get_mvid_data(artist_mbid):
    mvidurl = AUDIODBURL % (AUDIODBKEY, AUDIODBMVIDS % artist_mbid)
    headers = {}
    headers['User-Agent'] = ('%s/%s ( http://kodi.tv )' % (ADDONNAME, ADDONVERSION))
    try:
        req = urllib.request.Request(mvidurl, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        respdata = resp.read()
        mvid_data = json.loads(respdata)
        return mvid_data
    except HTTPError as e:
        message = LANGUAGE(30001) + " {} {} ".format(e.code, e.reason)
        message = message + LANGUAGE(30017) + " {}".format(mvidurl)
        log(message, xbmc.LOGERROR)
        xbmcgui.Dialog().notification(LANGUAGE(30000), LANGUAGE(30014), ICON)
        return {}
    except URLError as e:
        message = LANGUAGE(30002) + " {} ".format(e.reason)
        message = message + LANGUAGE(30017) + " {}".format(mvidurl)
        log(message, xbmc.LOGERROR)
        xbmcgui.Dialog().notification(LANGUAGE(30000), LANGUAGE(30014), ICON)
        return {}
    except Exception as e:
        log(f"Error getting mvid data: {str(e)}", xbmc.LOGERROR)
        return {}


def update_songs(songstoupdate):
    updated_count = 0
    for songs in songstoupdate:
        have_art = True
        songid = songs['songid']
        vidurl = songs['strVideoURL']
        vidthumb = songs['strVideoThumb']
        log(LANGUAGE(30003) + " " + str(songid) + " " + LANGUAGE(30004))
        if vidthumb is None:
            vidthumb = ""
            have_art = False

        # Build JSON-RPC call safely with json.dumps to avoid injection
        # issues when URLs contain quotes or special characters
        params = {
            "songid": songid,
            "songvideourl": vidurl
        }
        if have_art:
            params["art"] = {"videothumb": vidthumb}

        rpc = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "AudioLibrary.SetSongDetails",
            "params": params
        }

        xbmc.executeJSONRPC(json.dumps(rpc))
        updated_count += 1
        xbmc.sleep(5)
    
    return updated_count


def get_songs_for_artist(artist_id):
    try:
        # Validate artist_id is numeric to avoid malformed JSON
        artist_id_int = int(artist_id)
    except (ValueError, TypeError):
        log("get_songs_for_artist: invalid artist_id: " + str(artist_id),
            xbmc.LOGERROR)
        return []

    query = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "AudioLibrary.GetSongs",
        "params": {
            "filter": {"artistid": artist_id_int},
            "properties": ["musicbrainztrackid", "title"]
        }
    }
    try:
        getsongs = xbmc.executeJSONRPC(json.dumps(query))
        thesongs = json.loads(getsongs)
    except (ValueError, TypeError) as e:
        log("get_songs_for_artist: failed to parse RPC response for "
            "artist " + str(artist_id) + ": " + str(e), xbmc.LOGERROR)
        return []
    songlist = thesongs.get('result', {}).get('songs', [])
    return songlist


def match_mvids_to_songs(mvidlist, songlist):
    total_added = 0
    for item in mvidlist:
        songstoupdate = []
        mviddata = {}
        mviddata['title'] = item['strTrack']
        mviddata['mbtrackid'] = item.get('strMusicBrainzID')
        tempurl = item.get('strMusicVid', '')
        
        # Ignorar URLs vacías o que solo contienen https://www.youtube.com/watch?v=
        if not tempurl or tempurl.strip() == "https://www.youtube.com/watch?v=":
            continue
        
        vid_id = None
        
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
        
        if not vid_id or vid_id.strip() == "":
            continue

        mviddata['url'] = \
            'plugin://plugin.video.youtube/play/?video_id=%s' % vid_id
        mviddata['thumb'] = item.get('strTrackThumb', '')
        for songinfo in songlist:
            songdata = {}
            matched = False
            # Match by MusicBrainz Track ID
            if songinfo['musicbrainztrackid'] and mviddata['mbtrackid'] \
                    and songinfo['musicbrainztrackid'] == mviddata['mbtrackid']:
                matched = True
            # Match by exact title
            elif songinfo.get('title', '').lower().strip() == mviddata['title'].lower().strip():
                matched = True
            # Match by normalized title (remove parenthetical suffixes and extra whitespace)
            elif not matched:
                import re
                norm_song = re.sub(r'\s*[\(\[].+?[\)\]]', '', songinfo.get('title', '')).lower().strip()
                norm_mvid = re.sub(r'\s*[\(\[].+?[\)\]]', '', mviddata['title']).lower().strip()
                if norm_song and norm_mvid and (norm_song == norm_mvid
                        or norm_song in mviddata['title'].lower() or mviddata['title'].lower() in songinfo.get('title', '').lower()):
                    matched = True
            if matched:
                songdata['songid'] = songinfo['songid']
                songdata['strVideoURL'] = mviddata['url']
                songdata['strVideoThumb'] = mviddata['thumb']
                xbmc.sleep(5)
                if songdata:
                    songstoupdate.append(songdata)
        if songstoupdate:
            total_added += update_songs(songstoupdate)
    
    return total_added


# ---------------------------------------------------------------------
# PROCESS ALL ARTISTS: only add new videolinks (original behavior)
# ---------------------------------------------------------------------

def process_all_artists():
    global USE_FANART2
    USE_FANART2 = True
    
    # Set Window Property so skin can show custom background during scan
    xbmcgui.Window(10000).setProperty('theaudiodb.scanning.videolinks', 'true')
    
    bg = FanartBackground()
    bg.show()
    
    monitor = xbmc.Monitor()
    dialog = None
    try:
        while not monitor.abortRequested():
            artist_list = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, \
            "method": "AudioLibrary.GetArtists", \
            "params": {"sort": { "order": "ascending", \
            "ignorearticle": true, "method": "label", \
            "albumartistsonly": true}, "properties":["musicbrainzartistid"]}}')
            try:
                artistlist = json.loads(artist_list)
            except (ValueError, TypeError) as e:
                log("process_all_artists: failed to parse artist list: "
                    + str(e), xbmc.LOGERROR)
                break
            total_artists = artistlist['result']['limits']['total']
            log(LANGUAGE(30008))
            dialog = xbmcgui.DialogProgress()
            dialog.create(LANGUAGE(30015), LANGUAGE(30016))
            start_value = 0
            xbmc.sleep(100)
            
            # Contadores para el resumen final
            processed_count = 0
            skipped_count = 0
            total_videos_added = 0

            for artist in artistlist['result']['artists']:
                if monitor.abortRequested() or dialog.iscanceled():
                    break
                start_value += 1
                artist_mbid_list = artist.get('musicbrainzartistid', [])
                artist_mbid = artist_mbid_list[0] if artist_mbid_list else ""
                artist_name = artist['artist']
                artist_id = artist['artistid']
                log(LANGUAGE(30009) + artist_name)
                
                # If no MBID, try to get it from artist name
                if artist_mbid is None or artist_mbid == "":
                    log(LANGUAGE(30010) + artist_name + " - Trying name search...")
                    artist_mbid = get_mbid_from_artist_name(artist_name)
                    
                    # If still no MBID, skip this artist
                    if not artist_mbid:
                        skipped_count += 1
                        dialog.update(
                            int(start_value * 100 / total_artists),
                            LANGUAGE(30011) + artist_name)
                        xbmc.sleep(100)
                        continue
                
                xbmc.sleep(100)
                dialog.update(
                    int(start_value * 100 / total_artists),
                    LANGUAGE(30012) + artist_name)
                songlist = get_songs_for_artist(str(artist_id))
                mvid_data = get_mvid_data(artist_mbid)
                mvidlist = mvid_data.get('mvids') or []
                if not mvidlist:
                    log(LANGUAGE(30013) + artist_name)
                    xbmc.sleep(100)
                    continue
                videos_added = match_mvids_to_songs(mvidlist, songlist)
                if videos_added > 0:
                    total_videos_added += videos_added
                    processed_count += 1
            
            # Notificación final simplificada
            xbmcgui.Dialog().notification(LANGUAGE(30000), LANGUAGE(30029), ICON, 3000)  # "Finished"
            break
    finally:
        # Always cleanup resources, even if an exception occurred
        if dialog is not None:
            try:
                dialog.close()
            except Exception:
                pass
        try:
            bg.close()
        except Exception:
            pass
        # Clear Window Property - scan finished
        xbmcgui.Window(10000).clearProperty('theaudiodb.scanning.videolinks')


# ---------------------------------------------------------------------
# PROCESS SINGLE ARTIST: first delete, then add (unified behavior)
# ---------------------------------------------------------------------

def single_artist(artist_id):
    bg = FanartBackground()
    bg.show()

    # STEP 1: Delete all videolinks
    cleared = clear_videolinks_for_artist(artist_id)

    # STEP 2: Add new videolinks
    response = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1,\
    "method": "AudioLibrary.GetArtistDetails","params":{"artistid":'
                                   + artist_id +
                                   ',"properties":["musicbrainzartistid"]}}')
    artists = json.loads(response)
    
    # Check for errors in JSON-RPC response
    if 'error' in artists:
        log(f"JSON-RPC error getting artist details: {artists['error']}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(
            LANGUAGE(30000),
            LANGUAGE(30014),
            ICON,
            3000
        )
        bg.close()
        return
    
    if 'result' not in artists or 'artistdetails' not in artists['result']:
        log(f"Invalid JSON-RPC response: {artists}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(
            LANGUAGE(30000),
            LANGUAGE(30014),
            ICON,
            3000
        )
        bg.close()
        return
    
    artist_details = artists['result']['artistdetails']
    artist_mbid_list = artist_details.get('musicbrainzartistid', [])
    artist_mbid = artist_mbid_list[0] if artist_mbid_list else ""
    artist_name = artist_details.get('artist', '')  # 'artist' is always in artistdetails

    # If no MBID, try to get it from artist name
    if artist_mbid is None or artist_mbid == "":
        log(f"No MBID for artist '{artist_name}' - Trying name search...")
        artist_mbid = get_mbid_from_artist_name(artist_name)
        
        # If still no MBID, show notification and exit
        if not artist_mbid:
            xbmcgui.Dialog().notification(
                LANGUAGE(30000),
                LANGUAGE(30024),  # "No MusicBrainz ID found"
                ICON,
                3000
            )
            bg.close()
            return

    songlist = get_songs_for_artist(artist_id)
    mvid_data = get_mvid_data(artist_mbid)
    mvidlist = mvid_data.get('mvids') or []

    added_count = 0
    if mvidlist:
        added_count = match_mvids_to_songs(mvidlist, songlist)

    xbmcgui.Dialog().notification(
        LANGUAGE(30000),
        LANGUAGE(30029),  # "Finished"
        ICON,
        3000
    )

    bg.close()
    
    # Clear Updatevideos property
    window = xbmcgui.Window(10000)
    window.clearProperty("Updatevideos")


# ---------------------------------------------------------------------
# VIEW ALL ARTIST VIDEOLINKS: show all videos from theaudiodb.com
# ---------------------------------------------------------------------

def view_all_artist_videolinks(artist_id):
    """
    Shows all available music videos for an artist from theaudiodb.com,
    including those not matched to songs in the user's library.
    """
    bg = FanartBackground()
    bg.show()

    # Get artist details
    response = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1,\
    "method": "AudioLibrary.GetArtistDetails","params":{"artistid":'
                                   + artist_id +
                                   ',"properties":["musicbrainzartistid"]}}')
    artists = json.loads(response)
    
    # Check for errors
    if 'error' in artists or 'result' not in artists:
        bg.close()
        return
    
    artist_details = artists['result']['artistdetails']
    artist_mbid_list = artist_details.get('musicbrainzartistid', [])
    artist_mbid = artist_mbid_list[0] if artist_mbid_list else ""
    artist_name = artist_details.get('artist', '')  # 'artist' is always in artistdetails

    # If no MBID, try to get it from artist name
    if artist_mbid is None or artist_mbid == "":
        log(f"No MBID for artist '{artist_name}' - Trying name search...")
        artist_mbid = get_mbid_from_artist_name(artist_name)
        
        # If still no MBID, show notification and exit
        if not artist_mbid:
            xbmcgui.Dialog().notification(
                LANGUAGE(30000),
                LANGUAGE(30024),  # "No MusicBrainz ID found"
                ICON,
                3000
            )
            bg.close()
            return

    # Get videolinks from theaudiodb
    mvid_data = get_mvid_data(artist_mbid)
    mvidlist = mvid_data.get('mvids', [])

    if not mvidlist:
        xbmcgui.Dialog().notification(
            LANGUAGE(30000),
            LANGUAGE(30025),  # "No videos found for this artist"
            ICON,
            3000
        )
        bg.close()
        return

    # Get user's songs to mark which videos are in library
    songlist = get_songs_for_artist(artist_id)
    user_track_ids = {song['musicbrainztrackid'] for song in songlist if song.get('musicbrainztrackid')}
    user_track_titles = {song.get('title', '').lower() for song in songlist}

    # Prepare video list for selection dialog
    video_items = []
    video_urls = []
    
    for item in mvidlist:
        track_title = item['strTrack']
        track_mbid = item.get('strMusicBrainzID')
        tempurl = item.get('strMusicVid', '')
        
        # Ignorar URLs vacías o que solo contienen https://www.youtube.com/watch?v=
        if not tempurl or tempurl.strip() == "https://www.youtube.com/watch?v=":
            continue
        
        # Extract video ID
        index = tempurl.find('=')
        if index == -1:
            continue
            
        vid_id = tempurl[index+1:]
        
        # Verificar que el vid_id no esté vacío
        if not vid_id or vid_id.strip() == "":
            continue
        
        http_index = vid_id.find('//youtu.be/')
        if http_index != -1:
            vid_id = vid_id[http_index+11:]
        check1 = vid_id.find('/www.youtube.com/embed/')
        if check1 != -1:
            vid_id = vid_id[check1 + 23:check1 + 34]
        
        video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % vid_id
        
        # Check if video is in user's library
        in_library = (track_mbid in user_track_ids) or (track_title.lower() in user_track_titles)
        
        # Mark videos that are in library
        if in_library:
            display_name = f"✓ {track_title}"
        else:
            display_name = f"   {track_title}"
        
        video_items.append(display_name)
        video_urls.append(video_url)

    bg.close()

    if not video_items:
        xbmcgui.Dialog().notification(
            LANGUAGE(30000),
            LANGUAGE(30025),  # "No videos found for this artist"
            ICON,
            3000
        )
        return

    # Show selection dialog
    dialog = xbmcgui.Dialog()
    selected = dialog.select(
        f"{LANGUAGE(30026)} - {artist_name}",  # "Music Videos"
        video_items
    )

    if selected >= 0:
        # Play selected video
        xbmc.Player().play(video_urls[selected])


# ---------------------------------------------------------------------
# VIEW MISSING VIDEOLINKS: show only videos NOT in library
# ---------------------------------------------------------------------

def view_missing_artist_videolinks(artist_id):
    """
    Shows only music videos from theaudiodb.com that are NOT 
    matched to songs in the user's library.
    """
    bg = FanartBackground()
    bg.show()

    # Get artist details
    response = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1,\
    "method": "AudioLibrary.GetArtistDetails","params":{"artistid":'
                                   + artist_id +
                                   ',"properties":["musicbrainzartistid"]}}')
    artists = json.loads(response)
    
    # Check for errors
    if 'error' in artists or 'result' not in artists:
        bg.close()
        return
    
    artist_details = artists['result']['artistdetails']
    artist_mbid_list = artist_details.get('musicbrainzartistid', [])
    artist_mbid = artist_mbid_list[0] if artist_mbid_list else ""
    artist_name = artist_details.get('artist', '')  # 'artist' is always in artistdetails

    # If no MBID, try to get it from artist name
    if artist_mbid is None or artist_mbid == "":
        log(f"No MBID for artist '{artist_name}' - Trying name search...")
        artist_mbid = get_mbid_from_artist_name(artist_name)
        
        # If still no MBID, show notification and exit
        if not artist_mbid:
            xbmcgui.Dialog().notification(
                LANGUAGE(30000),
                LANGUAGE(30024),  # "No MusicBrainz ID found"
                ICON,
                3000
            )
            bg.close()
            return

    # Get videolinks from theaudiodb
    mvid_data = get_mvid_data(artist_mbid)
    mvidlist = mvid_data.get('mvids', [])

    if not mvidlist:
        xbmcgui.Dialog().notification(
            LANGUAGE(30000),
            LANGUAGE(30025),  # "No videos found for this artist"
            ICON,
            3000
        )
        bg.close()
        return

    # Get user's songs to filter out videos in library
    songlist = get_songs_for_artist(artist_id)
    user_track_ids = {song['musicbrainztrackid'] for song in songlist if song.get('musicbrainztrackid')}
    user_track_titles = {song.get('title', '').lower() for song in songlist}

    # Prepare video list - ONLY videos NOT in library
    video_items = []
    video_urls = []
    
    for item in mvidlist:
        track_title = item['strTrack']
        track_mbid = item.get('strMusicBrainzID')
        tempurl = item.get('strMusicVid', '')
        
        # Check if video is in user's library
        in_library = (track_mbid in user_track_ids) or (track_title.lower() in user_track_titles)
        
        # Only add if NOT in library
        if not in_library:
            # Ignorar URLs vacías o que solo contienen https://www.youtube.com/watch?v=
            if not tempurl or tempurl.strip() == "https://www.youtube.com/watch?v=":
                continue
            
            # Extract video ID
            index = tempurl.find('=')
            if index == -1:
                continue
                
            vid_id = tempurl[index+1:]
            
            # Verificar que el vid_id no esté vacío
            if not vid_id or vid_id.strip() == "":
                continue
            
            http_index = vid_id.find('//youtu.be/')
            if http_index != -1:
                vid_id = vid_id[http_index+11:]
            check1 = vid_id.find('/www.youtube.com/embed/')
            if check1 != -1:
                vid_id = vid_id[check1 + 23:check1 + 34]
            
            video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % vid_id
            
            video_items.append(track_title)
            video_urls.append(video_url)

    bg.close()

    if not video_items:
        xbmcgui.Dialog().notification(
            LANGUAGE(30000),
            LANGUAGE(30027),  # "All videos are already in your library"
            ICON,
            3000
        )
        return

    # Show selection dialog
    dialog = xbmcgui.Dialog()
    selected = dialog.select(
        f"{LANGUAGE(30028)} - {artist_name}",  # "Missing Music Videos"
        video_items
    )

    if selected >= 0:
        # Play selected video
        xbmc.Player().play(video_urls[selected])



