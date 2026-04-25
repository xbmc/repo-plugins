# -*- coding: utf-8 -*-
"""
TheAudioDB Helper - Router Script

This script provides two main features:
1) Counting local music videos for an artist using XSP (same logic as SkinVariables).
2) Counting online music video links via AudioLibrary.GetSongs.

IMPORTANT LIMITATION:
Kodi does not reliably associate local music videos with artists in VideoLibrary.
For this reason, local music videos are detected exclusively through XSP queries,
not through VideoLibrary artist IDs.
"""

import sys
import re
import html
import urllib.parse
import json

import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import dbid_helper
from resources.lib import videolinks

ADDON = xbmcaddon.Addon()
LOG_PREFIX = "[audio.theaudiodb.helper.Router] "

# -------------------------------------------------------------------------
# TADB language field mappings (defined once, used for artist/album/song)
# -------------------------------------------------------------------------

TADB_BIO_FIELDS = {
    'en': 'strBiographyEN',
    'es': 'strBiographyES',
    'de': 'strBiographyDE',
    'fr': 'strBiographyFR',
    'it': 'strBiographyIT',
    'pt': 'strBiographyPT',
    'ru': 'strBiographyRU',
    'nl': 'strBiographyNL',
    'pl': 'strBiographyPL',
    'se': 'strBiographySE',
    'hu': 'strBiographyHU',
    'no': 'strBiographyNO',
    'cn': 'strBiographyCN',
    'jp': 'strBiographyJP',
    'il': 'strBiographyIL'
}

TADB_DESC_FIELDS = {
    'en': 'strDescriptionEN',
    'es': 'strDescriptionES',
    'de': 'strDescriptionDE',
    'fr': 'strDescriptionFR',
    'it': 'strDescriptionIT',
    'pt': 'strDescriptionPT',
    'ru': 'strDescriptionRU',
    'nl': 'strDescriptionNL',
    'pl': 'strDescriptionPL',
    'se': 'strDescriptionSE',
    'hu': 'strDescriptionHU',
    'no': 'strDescriptionNO',
    'cn': 'strDescriptionCN',
    'jp': 'strDescriptionJP',
    'il': 'strDescriptionIL'
}


def log(msg, level=xbmc.LOGDEBUG):
    """Simple wrapper for Kodi logging."""
    xbmc.log(LOG_PREFIX + msg, level)


# -------------------------------------------------------------------------
# HELPER: Clean Last.fm HTML biography/description text
# -------------------------------------------------------------------------

def clean_lastfm_html(text):
    """
    Clean HTML tags, entities, and footer from Last.fm biography/description text.
    Returns cleaned plain text, or empty string if input is empty.
    """
    if not text:
        return ""
    # Replace <br> and <p> tags with newlines
    cleaned = re.sub(r'<br\s*/?>', '\n', text)
    cleaned = re.sub(r'</p>', '\n\n', cleaned)
    cleaned = re.sub(r'<p>', '', cleaned)
    # Remove all other HTML tags
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    # Decode HTML entities
    cleaned = html.unescape(cleaned)
    # Remove "Read more on Last.fm" footer if present
    cleaned = re.sub(r'\s*Read more on Last\.fm.*$', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    # Clean up extra whitespace
    cleaned = re.sub(r'\n\n+', '\n\n', cleaned)
    return cleaned.strip()


def has_real_content(text):
    """Check if Last.fm text has real content after HTML cleaning."""
    cleaned = clean_lastfm_html(text)
    return bool(cleaned)


# -------------------------------------------------------------------------
# HELPER: Format number with dots as thousand separator (e.g. 5.586.985)
# -------------------------------------------------------------------------

def format_number(value):
    """Format a number string with dots as thousand separators."""
    try:
        return f"{int(value):,}".replace(',', '.')
    except (ValueError, TypeError):
        return str(value) if value else ""


# -------------------------------------------------------------------------
# LOCAL MUSIC VIDEOS (XSP ONLY)
# -------------------------------------------------------------------------

def get_local_musicvideos_by_name(artist_name):
    """
    Returns the number of local music videos for the given artist name.

    This uses an XSP filter identical to what the skin uses.
    It does NOT rely on VideoLibrary artist IDs, because Kodi does not
    consistently assign artist IDs to local music videos.
    """

    if not artist_name:
        return 0

    # Escape '&' for XSP
    safe_name = artist_name.replace("&", "&amp;")

    # XSP identical to the one used by SkinVariables
    xsp = {
        "type": "musicvideos",
        "order": {
            "method": "year",
            "direction": "descending",
            "ignorefolders": 0
        },
        "rules": {
            "and": [
                {
                    "field": "artist",
                    "operator": "is",
                    "value": [safe_name]
                }
            ]
        }
    }

    xsp_encoded = urllib.parse.quote(json.dumps(xsp))
    path = f"videodb://musicvideos/titles/?xsp={xsp_encoded}"

    rpc = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "Files.GetDirectory",
        "params": {
            "directory": path,
            "media": "video"
        }
    }

    response = xbmc.executeJSONRPC(json.dumps(rpc))

    try:
        data = json.loads(response)
        items = data.get("result", {}).get("files", [])
        return len(items)
    except Exception as e:
        log(f"Error getting local musicvideos: {str(e)}", xbmc.LOGERROR)
        return 0


# -------------------------------------------------------------------------
# ONLINE MUSIC VIDEOS (SONG VIDEO URLS)
# -------------------------------------------------------------------------

def get_online_musicvideos_by_artistid(artist_id):
    """
    Returns the number of online music video links for the given artist ID.
    These are stored in AudioLibrary as 'songvideourl'.
    """

    if not artist_id:
        return 0

    rpc = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "AudioLibrary.GetSongs",
        "params": {
            "filter": {"artistid": int(artist_id)},
            "properties": ["songvideourl"]
        }
    }

    response = xbmc.executeJSONRPC(json.dumps(rpc))

    total = 0

    try:
        data = json.loads(response)
        songs = data.get("result", {}).get("songs", [])
        for song in songs:
            if song.get("songvideourl"):
                total += 1
    except Exception as e:
        log(f"Error getting online musicvideos for artistid {artist_id}: {str(e)}", xbmc.LOGERROR)

    return total


# -------------------------------------------------------------------------
# TOTAL COUNT
# -------------------------------------------------------------------------

def get_total_musicvideos(artist_id, artist_name):
    """
    Returns the sum of:
    - Local music videos (via XSP)
    - Online music video links (via AudioLibrary)
    """

    local = get_local_musicvideos_by_name(artist_name)
    online = get_online_musicvideos_by_artistid(artist_id)

    return local + online


# -------------------------------------------------------------------------
# HELPER: Get Last.fm text from bio/wiki with HTML validation
# -------------------------------------------------------------------------

def _extract_lastfm_bio(lastfm_info):
    """Extract and validate biography text from Last.fm artist info response."""
    if not lastfm_info or 'bio' not in lastfm_info:
        return ""
    temp_bio = lastfm_info['bio'].get('content', "") or lastfm_info['bio'].get('summary', "")
    if temp_bio and has_real_content(temp_bio):
        return temp_bio
    return ""


def _extract_lastfm_wiki(lastfm_data, min_length=70):
    """Extract and validate wiki/description text from Last.fm album/track info response."""
    if not lastfm_data:
        return ""
    wiki = lastfm_data.get('wiki', {})
    if not isinstance(wiki, dict):
        return ""
    temp_desc = wiki.get('content', '') or wiki.get('summary', '')
    if temp_desc:
        cleaned = clean_lastfm_html(temp_desc)
        if cleaned and len(cleaned) >= min_length:
            return temp_desc
    return ""


# -------------------------------------------------------------------------
# ROUTER
# -------------------------------------------------------------------------

def parse_params(raw):
    """Parses query-string style parameters from sys.argv."""
    if not raw:
        return {}
    if raw.startswith('?'):
        raw = raw[1:]
    return dict(urllib.parse.parse_qsl(raw, keep_blank_values=True))


def main():
    if len(sys.argv) == 1:
        videolinks.process_all_artists()
        return

    arg = sys.argv[1]

    # Legacy DBID helper
    if arg.startswith("artist="):
        dbid_helper.main()
        return

    # Legacy videolinks call
    if "action=" not in arg and arg.isdigit():
        videolinks.single_artist(arg)
        return

    params = parse_params(arg)
    action = params.get("action")

    if action == "videolinks":
        artist_id = params.get("artistid")
        delete_only = params.get("delete_only")
        
        # Set Updatevideos property at the start (for skin updates)
        if delete_only:
            win = xbmcgui.Window(10000)
            win.setProperty("Updatevideos", "True")
        
        if artist_id:
            # Show notification when processing single artist
            xbmcgui.Dialog().notification(
                videolinks.LANGUAGE(30000),  # "Music Video Links Helper"
                videolinks.LANGUAGE(30016),  # "Please wait..."
                videolinks.ICON,
                3000
            )
            videolinks.single_artist(artist_id)
        else:
            videolinks.process_all_artists()
        return

    # --- Actions restricted to DialogMusicInfo ---
    if not xbmc.getCondVisibility('Window.IsActive(musicinformation) | Window.IsActive(songinformation)'):
        if action in ("load_artist_details", "load_album_details", "load_song_details",
                       "view_all_videolinks", "view_missing_videolinks"):
            log(f"Action '{action}' blocked - only allowed from DialogMusicInfo", xbmc.LOGINFO)
            return

    if action == "view_all_videolinks":
        artist_id = params.get("artistid")
        if artist_id:
            videolinks.view_all_artist_videolinks(artist_id)
        return

    if action == "view_missing_videolinks":
        artist_id = params.get("artistid")
        if artist_id:
            videolinks.view_missing_artist_videolinks(artist_id)
        return

    if action == "artist_musicvideo_count":
        artist_id = params.get("artistid")

        # Artist name is passed via Window property (safe for special characters)
        win = xbmcgui.Window(10000)
        artist_name = win.getProperty("audio.theaudiodb.helper.ArtistName")

        total = get_total_musicvideos(artist_id, artist_name)

        win.setProperty("audio.theaudiodb.helper.ArtistMusicVideoCount", str(total))

        return

    if action == "open_album_from_dialog":
        # Get album path from Window property
        win = xbmcgui.Window(10000)
        album_path = win.getProperty("audio.theaudiodb.helper.AlbumPath")
        artist_dbid = win.getProperty("audio.theaudiodb.Artist.DBID")
        
        if album_path:
            # Store the album path in home window property
            xbmc.executebuiltin(f'SetProperty(WhatAlbum,{album_path},home)')
            
            # Close the music information dialog
            xbmc.executebuiltin('Dialog.Close(musicinformation)')
            
            # First, navigate to artist's albums view (if artist DBID is available)
            if artist_dbid:
                xbmc.executebuiltin(f'ActivateWindow(music,musicdb://artists/{artist_dbid}/,return)')
                xbmc.sleep(100)  # Small delay to ensure the window is ready
            
            # Then open music window with the album path
            xbmc.executebuiltin(f'ActivateWindow(music,{album_path}/,return)')
            
            # Wait for window to open (max 3 seconds)
            for i in range(30):
                if xbmc.getCondVisibility('Window.IsActive(music)'):
                    # Wait 150ms before setting focus
                    xbmc.sleep(150)
                    xbmc.executebuiltin('SetFocus(50)')
                    break
                xbmc.sleep(100)
        else:
            log("No album path provided", xbmc.LOGERROR)
        return

    if action == "open_album_info":
        # Open album info from within the artist's musicinformation dialog
        # by finding the album in container 50 and clicking on it
        win = xbmcgui.Window(10000)
        album_id = win.getProperty("audio.theaudiodb.helper.AlbumID")
        
        if not album_id:
            log("No album ID provided for album info", xbmc.LOGERROR)
            return
        
        # We should already be in musicinformation (artist info screen)
        if not xbmc.getCondVisibility('Window.IsActive(musicinformation)'):
            log("musicinformation is not active", xbmc.LOGWARNING)
            return
        
        # Get the number of items in container 50 (album list)
        num_items_str = xbmc.getInfoLabel('Container(50).NumItems')
        try:
            num_items = int(num_items_str)
        except (ValueError, TypeError):
            num_items = 0
        
        if num_items == 0:
            log("No items in container 50", xbmc.LOGWARNING)
            return
        
        # Find the album by DBID in container 50
        for i in range(num_items):
            item_dbid = xbmc.getInfoLabel(f'Container(50).ListItemAbsolute({i}).DBID')
            if item_dbid == album_id:
                # Set focus on the album and click it
                xbmc.executebuiltin(f'SetFocus(50,{i})')
                xbmc.sleep(200)
                xbmc.executebuiltin('Action(Select)')
                log(f"Opening album info for DBID {album_id} (position {i})")
                return
        
        log(f"Album ID {album_id} not found in container 50", xbmc.LOGWARNING)
        return

    if action == "load_artist_details":
        # Artist name is passed via Window property (safe for special characters)
        win = xbmcgui.Window(10000)
        artist_name = win.getProperty("audio.theaudiodb.helper.ArtistName")
        
        if not artist_name:
            log("No artist name provided for biography", xbmc.LOGERROR)
            return
        
        # Get user settings
        use_wikipedia = ADDON.getSettingBool('biography_use_wikipedia')
        use_lastfm = ADDON.getSettingBool('biography_use_lastfm')
        custom_lastfm_key = ADDON.getSettingString('lastfm_api_key').strip()
        auto_save_biography = ADDON.getSettingBool('biography_auto_save')
        auto_save_artwork = ADDON.getSettingBool('artwork_auto_save')
        
        # Get Kodi's current language
        kodi_language = xbmc.getLanguage(xbmc.ISO_639_1)  # Returns 2-letter code like 'es', 'en', 'de'
        
        biography = ""
        source = ""
        
        # Get TheAudioDB info once (used in priorities 1 and 4)
        tadb_info = videolinks.get_artist_info(artist_name)
        
        # Cache Last.fm results to avoid redundant HTTP calls
        lastfm_cache = {}
        
        # Priority 1: TheAudioDB in Kodi's language (always enabled)
        if tadb_info:
            bio_field = TADB_BIO_FIELDS.get(kodi_language, 'strBiographyEN')
            biography = tadb_info.get(bio_field, "")
            if biography:
                source = "TheAudioDB"
        
        # Priority 2: Last.fm in Kodi's language (if enabled and no bio yet)
        if not biography and use_lastfm:
            lastfm_info = videolinks.get_lastfm_artist_info(artist_name, kodi_language, custom_lastfm_key)
            lastfm_cache[kodi_language] = lastfm_info
            temp_bio = _extract_lastfm_bio(lastfm_info)
            if temp_bio:
                biography = temp_bio
                source = "Last.fm"
        
        # Priority 3: TheAudioDB in English (always enabled if still no bio)
        if not biography and tadb_info:
            biography = tadb_info.get('strBiographyEN', "")
            if biography:
                source = "TheAudioDB"
        
        # Priority 4: Last.fm in English (if enabled, fallback)
        if not biography and use_lastfm:
            lastfm_info_en = videolinks.get_lastfm_artist_info(artist_name, 'en', custom_lastfm_key)
            lastfm_cache['en'] = lastfm_info_en
            temp_bio = _extract_lastfm_bio(lastfm_info_en)
            if temp_bio:
                biography = temp_bio
                source = "Last.fm"
        
        # Priority 5: Wikipedia in Kodi's language (if enabled, final fallbacks)
        if not biography and use_wikipedia:
            wiki_bio = videolinks.get_wikipedia_biography(artist_name, kodi_language)
            if wiki_bio:
                biography = wiki_bio
                source = "Wikipedia"
        
        # Priority 6: Wikipedia in English (if enabled, last resort)
        if not biography and use_wikipedia:
            wiki_bio = videolinks.get_wikipedia_biography(artist_name, 'en')
            if wiki_bio:
                biography = wiki_bio
                source = "Wikipedia"
        
        # Clean up Last.fm HTML tags if present
        if biography and source == "Last.fm":
            biography = clean_lastfm_html(biography)
        
        # Discard biographies that are too short (placeholder texts like "None found, add one?")
        if biography and len(biography) < 70:
            biography = ""
            source = ""
        
        # Set the biography property
        win.setProperty("Artist.TADB.Biography", biography)
        win.setProperty("Artist.Biography.Source", source)  # For attribution if needed
        
        # Set all additional TADB artist properties (images + metadata)
        if tadb_info:
            # Images
            win.setProperty("Artist.TADB.Thumb",      tadb_info.get("strArtistThumb", "") or "")
            win.setProperty("Artist.TADB.Logo",       tadb_info.get("strArtistLogo", "") or "")
            win.setProperty("Artist.TADB.Fanart",     tadb_info.get("strArtistFanart", "") or "")
            win.setProperty("Artist.TADB.Fanart2",    tadb_info.get("strArtistFanart2", "") or "")
            win.setProperty("Artist.TADB.Fanart3",    tadb_info.get("strArtistFanart3", "") or "")
            win.setProperty("Artist.TADB.Fanart4",    tadb_info.get("strArtistFanart4", "") or "")
            win.setProperty("Artist.TADB.Banner",     tadb_info.get("strArtistBanner", "") or "")
            win.setProperty("Artist.TADB.WideThumb",  tadb_info.get("strArtistWideThumb", "") or "")
            win.setProperty("Artist.TADB.Clearart",   tadb_info.get("strArtistClearart", "") or "")
            win.setProperty("Artist.TADB.Cutout",     tadb_info.get("strArtistCutout", "") or "")
            # Metadata
            win.setProperty("Artist.TADB.Country",    tadb_info.get("strCountry", "") or "")
            win.setProperty("Artist.TADB.Genre",      tadb_info.get("strGenre", "") or "")
            win.setProperty("Artist.TADB.Style",      tadb_info.get("strStyle", "") or "")
            win.setProperty("Artist.TADB.Mood",       tadb_info.get("strMood", "") or "")
            win.setProperty("Artist.TADB.FormedYear", tadb_info.get("intFormedYear", "") or "")
            win.setProperty("Artist.TADB.BornYear",   tadb_info.get("intBornYear", "") or "")
            win.setProperty("Artist.TADB.DiedYear",   tadb_info.get("intDiedYear", "") or "")
            win.setProperty("Artist.TADB.Disbanded",  tadb_info.get("strDisbanded", "") or "")
            win.setProperty("Artist.TADB.Gender",     tadb_info.get("strGender", "") or "")
            win.setProperty("Artist.TADB.Website",    tadb_info.get("strWebsite", "") or "")
            win.setProperty("Artist.TADB.RecordLabel",tadb_info.get("strLabel", "") or "")
        else:
            # Clear all TADB properties if no data found
            for prop in [
                "Artist.TADB.Thumb", "Artist.TADB.Logo",
                "Artist.TADB.Fanart", "Artist.TADB.Fanart2", "Artist.TADB.Fanart3", "Artist.TADB.Fanart4",
                "Artist.TADB.Banner", "Artist.TADB.WideThumb", "Artist.TADB.Clearart", "Artist.TADB.Cutout",
                "Artist.TADB.Country", "Artist.TADB.Genre", "Artist.TADB.Style", "Artist.TADB.Mood",
                "Artist.TADB.FormedYear", "Artist.TADB.BornYear", "Artist.TADB.DiedYear",
                "Artist.TADB.Disbanded", "Artist.TADB.Gender", "Artist.TADB.Website", "Artist.TADB.RecordLabel"
            ]:
                win.clearProperty(prop)
        
        # Process additional Last.fm data if Last.fm is enabled
        if use_lastfm:
            # Reuse cached Last.fm data if available, otherwise fetch
            lastfm_data = lastfm_cache.get(kodi_language)
            if lastfm_data is None:
                lastfm_data = videolinks.get_lastfm_artist_info(artist_name, kodi_language, custom_lastfm_key)
            if not lastfm_data:
                lastfm_data = lastfm_cache.get('en')
                if lastfm_data is None:
                    lastfm_data = videolinks.get_lastfm_artist_info(artist_name, 'en', custom_lastfm_key)
            
            if lastfm_data:
                # Extract listeners count and format with thousand separators
                stats = lastfm_data.get('stats', {})
                listeners = stats.get('listeners', '0')
                win.setProperty("Artist.LastFM.Listeners", format_number(listeners))
                
                # Extract and format tags/genres
                tags_data = lastfm_data.get('tags', {})
                tags_list = tags_data.get('tag', [])
                if isinstance(tags_list, list) and tags_list:
                    # Get first 5 tags, join with " / "
                    tag_names = [tag.get('name', '') for tag in tags_list[:5] if tag.get('name')]
                    tags_string = ' / '.join(tag_names)
                    win.setProperty("Artist.LastFM.Tags", tags_string)
                else:
                    win.setProperty("Artist.LastFM.Tags", "")
            else:
                # Clear properties if no Last.fm data
                win.setProperty("Artist.LastFM.Listeners", "")
                win.setProperty("Artist.LastFM.Tags", "")
        else:
            # Clear properties if Last.fm is disabled
            win.setProperty("Artist.LastFM.Listeners", "")
            win.setProperty("Artist.LastFM.Tags", "")
        
        # Auto-save biography, genre and styles to Kodi database if enabled
        if auto_save_biography and artist_name and (biography or tadb_info):
            try:
                # First, get the artist ID and current data from the artist name
                rpc_get_artist = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "AudioLibrary.GetArtists",
                    "params": {
                        "filter": {
                            "field": "artist",
                            "operator": "is",
                            "value": artist_name
                        },
                        "properties": ["description", "genre", "style"]
                    }
                }
                
                response = xbmc.executeJSONRPC(json.dumps(rpc_get_artist))
                data = json.loads(response)
                
                artists = data.get("result", {}).get("artists", [])
                
                if artists:
                    artist_info = artists[0]
                    artistid = artist_info.get("artistid")
                    current_description = artist_info.get("description", "")
                    current_genre = artist_info.get("genre", []) or []
                    current_styles = artist_info.get("style", []) or []
                    
                    if artistid:
                        # Build params with only what needs saving
                        params_to_save = {"artistid": artistid}
                        saved_fields = []
                        
                        # Biography: save if empty (requires user confirmation)
                        if biography and not current_description:
                            win.setProperty('theaudiodb.dialog.type', 'biography')
                            if xbmcgui.Dialog().yesno(
                                ADDON.getLocalizedString(32013),
                                ''
                            ):
                                params_to_save["description"] = biography
                                saved_fields.append(f"biography ({source})")
                            else:
                                log(f"User declined saving biography for artist '{artist_name}'")
                            win.clearProperty('theaudiodb.dialog.type')
                        
                        # Genre: save if empty in Kodi and available in TADB (no confirmation needed)
                        if not current_genre and tadb_info:
                            tadb_genre = tadb_info.get("strGenre", "") or ""
                            if tadb_genre:
                                genre_list = [g.strip() for g in tadb_genre.replace('/', ',').split(',') if g.strip()]
                                if genre_list:
                                    params_to_save["genre"] = genre_list
                                    saved_fields.append("genre")
                        
                        # Styles: save if empty in Kodi and available in TADB (no confirmation needed)
                        if not current_styles and tadb_info:
                            tadb_style = tadb_info.get("strStyle", "") or ""
                            if tadb_style:
                                style_list = [s.strip() for s in tadb_style.replace('/', ',').split(',') if s.strip()]
                                if style_list:
                                    params_to_save["style"] = style_list
                                    saved_fields.append("styles")
                        
                        # Save all collected data in one RPC call
                        if len(params_to_save) > 1:  # More than just artistid
                            rpc_set_artist = {
                                "jsonrpc": "2.0",
                                "id": 2,
                                "method": "AudioLibrary.SetArtistDetails",
                                "params": params_to_save
                            }
                            
                            xbmc.executeJSONRPC(json.dumps(rpc_set_artist))
                            log(f"Auto-saved to database for artist '{artist_name}': {', '.join(saved_fields)}")
                        else:
                            log(f"Nothing to save for '{artist_name}' - database already has description, genre and style")
                else:
                    log(f"Could not find artist '{artist_name}' in database for auto-save", xbmc.LOGWARNING)
                    
            except Exception as e:
                log(f"Error auto-saving data for '{artist_name}': {str(e)}", xbmc.LOGERROR)
        
        # Auto-save artwork to Kodi database if enabled and TADB data was found
        if auto_save_artwork and tadb_info and artist_name:
            try:
                # Get the artist ID and current art from Kodi database
                rpc_get_artist_art = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "AudioLibrary.GetArtists",
                    "params": {
                        "filter": {
                            "field": "artist",
                            "operator": "is",
                            "value": artist_name
                        },
                        "properties": ["art"]
                    }
                }
                
                response = xbmc.executeJSONRPC(json.dumps(rpc_get_artist_art))
                data = json.loads(response)
                
                artists = data.get("result", {}).get("artists", [])
                
                if artists:
                    artist_info = artists[0]
                    artistid = artist_info.get("artistid")
                    current_art = artist_info.get("art", {}) or {}
                    
                    if artistid:
                        # Mapping: Kodi art type -> TheAudioDB field
                        art_mapping = {
                            'thumb':     'strArtistThumb',
                            'clearlogo': 'strArtistLogo',
                            'clearart':  'strArtistClearart',
                            'fanart':    'strArtistFanart',
                            'fanart1':   'strArtistFanart2',
                            'fanart2':   'strArtistFanart3',
                            'fanart3':   'strArtistFanart4',
                            'landscape': 'strArtistWideThumb',
                            'banner':    'strArtistBanner',
                            'cutout':    'strArtistCutout',
                        }
                        
                        # Build art dict with only missing images
                        art_to_save = {}
                        for kodi_type, tadb_field in art_mapping.items():
                            # Check if Kodi database is missing this art type
                            if not current_art.get(kodi_type):
                                tadb_url = tadb_info.get(tadb_field, "") or ""
                                if tadb_url:
                                    art_to_save[kodi_type] = tadb_url
                        
                        if art_to_save:
                            rpc_set_art = {
                                "jsonrpc": "2.0",
                                "id": 3,
                                "method": "AudioLibrary.SetArtistDetails",
                                "params": {
                                    "artistid": artistid,
                                    "art": art_to_save
                                }
                            }
                            
                            xbmc.executeJSONRPC(json.dumps(rpc_set_art))
                            saved_types = ', '.join(art_to_save.keys())
                            log(f"Artwork auto-saved to database for artist '{artist_name}': {saved_types}")
                        else:
                            log(f"Artwork not saved for '{artist_name}' - database already has all available artwork")
                else:
                    log(f"Could not find artist '{artist_name}' in database for artwork auto-save", xbmc.LOGWARNING)
                    
            except Exception as e:
                log(f"Error auto-saving artwork for '{artist_name}': {str(e)}", xbmc.LOGERROR)
        
        return

    if action == "load_song_details":
        # Song details are passed via Window properties (safe for special characters)
        win = xbmcgui.Window(10000)
        artist_name = win.getProperty("audio.theaudiodb.helper.SongArtist")
        album_name = win.getProperty("audio.theaudiodb.helper.SongAlbum")
        song_name = win.getProperty("audio.theaudiodb.helper.SongTitle")
        
        if not artist_name or not song_name:
            log("No artist or song name provided for song details", xbmc.LOGERROR)
            return
        
        # Get user settings
        use_lastfm = ADDON.getSettingBool('biography_use_lastfm')
        custom_lastfm_key = ADDON.getSettingString('lastfm_api_key').strip()
        
        # Get Kodi's current language
        kodi_language = xbmc.getLanguage(xbmc.ISO_639_1)
        
        # Get TheAudioDB track info
        tadb_track = videolinks.get_track_info(artist_name, album_name, song_name)
        
        # Build description with priority cascade (same as artist/album)
        description = ""
        source = ""
        
        # Priority 1: TheAudioDB in Kodi's language
        if tadb_track:
            desc_field = TADB_DESC_FIELDS.get(kodi_language, 'strDescriptionEN')
            description = tadb_track.get(desc_field, "") or ""
            if description:
                source = "TheAudioDB"
        
        # Priority 2: Last.fm in Kodi's language
        if not description and use_lastfm:
            lastfm_track = videolinks.get_lastfm_track_info(artist_name, song_name, kodi_language, custom_lastfm_key)
            temp_desc = _extract_lastfm_wiki(lastfm_track)
            if temp_desc:
                description = temp_desc
                source = "Last.fm"
        
        # Priority 3: TheAudioDB in English
        if not description and tadb_track:
            description = tadb_track.get('strDescriptionEN', "") or ""
            if description:
                source = "TheAudioDB"
        
        # Priority 4: Last.fm in English
        if not description and use_lastfm:
            lastfm_track_en = videolinks.get_lastfm_track_info(artist_name, song_name, 'en', custom_lastfm_key)
            temp_desc = _extract_lastfm_wiki(lastfm_track_en)
            if temp_desc:
                description = temp_desc
                source = "Last.fm"
        
        # Clean up Last.fm HTML tags if present
        if description and source == "Last.fm":
            description = clean_lastfm_html(description)
        
        # Discard descriptions that are too short (placeholder texts)
        if description and len(description) < 70:
            description = ""
            source = ""
        
        # Set description properties
        win.setProperty("Song.TADB.Description",    description)
        win.setProperty("Song.Description.Source",  source)
        
        # Set TADB metadata and artwork properties
        if tadb_track:
            win.setProperty("Song.TADB.Mood",           tadb_track.get("strMood", "") or "")
            win.setProperty("Song.TADB.Style",          tadb_track.get("strStyle", "") or "")
            
            # Get album label (from album data, not available at track level)
            song_label = ""
            album_id_for_label = tadb_track.get("idAlbum")
            if album_id_for_label:
                try:
                    album_for_label = videolinks._get_album_lookup(album_id_for_label, 
                        {'User-Agent': '%s/%s ( http://kodi.tv )' % (ADDON.getAddonInfo('name'), ADDON.getAddonInfo('version'))})
                    if album_for_label:
                        song_label = album_for_label.get("strLabel", "") or ""
                except Exception as e:
                    log(f"Error getting album label for song: {str(e)}", xbmc.LOGERROR)
            win.setProperty("Song.TADB.Label", song_label)
            
            # Music video info
            win.setProperty("Song.TADB.MusicVidDirector",   tadb_track.get("strMusicVidDirector", "") or "")
            win.setProperty("Song.TADB.MusicVidScreen1",    tadb_track.get("strMusicVidScreen1", "") or "")
            win.setProperty("Song.TADB.MusicVidScreen2",    tadb_track.get("strMusicVidScreen2", "") or "")
            win.setProperty("Song.TADB.MusicVidScreen3",    tadb_track.get("strMusicVidScreen3", "") or "")
            
            # Music video YouTube stats
            mvid_views = tadb_track.get("intMusicVidViews") or ""
            win.setProperty("Song.TADB.MusicVidViews", format_number(mvid_views) if mvid_views else "")
            mvid_likes = tadb_track.get("intMusicVidLikes") or ""
            win.setProperty("Song.TADB.MusicVidLikes", format_number(mvid_likes) if mvid_likes else "")
            mvid_comments = tadb_track.get("intMusicVidComments") or ""
            win.setProperty("Song.TADB.MusicVidComments", format_number(mvid_comments) if mvid_comments else "")
        else:
            # Clear TADB-only song properties if no TADB data found
            for prop in [
                "Song.TADB.Mood", "Song.TADB.Style", "Song.TADB.Label",
                "Song.TADB.MusicVidDirector",
                "Song.TADB.MusicVidScreen1", "Song.TADB.MusicVidScreen2", "Song.TADB.MusicVidScreen3",
                "Song.TADB.MusicVidViews", "Song.TADB.MusicVidLikes", "Song.TADB.MusicVidComments"
            ]:
                win.clearProperty(prop)
        
        # Get lyrics from multiple providers (cascaded fallback)
        lyrics_text, lyrics_source = videolinks.get_lyrics_cascaded(artist_name, song_name)
        win.setProperty("Song.Lyrics", lyrics_text or "")
        win.setProperty("Song.Lyrics.Source", lyrics_source or "")
        
        # Get Last.fm track info (listeners and tags only, description already handled above)
        if use_lastfm:
            lastfm_track = videolinks.get_lastfm_track_info(artist_name, song_name, kodi_language, custom_lastfm_key)
            if not lastfm_track:
                lastfm_track = videolinks.get_lastfm_track_info(artist_name, song_name, 'en', custom_lastfm_key)
            
            if lastfm_track:
                # Listeners
                win.setProperty("Song.LastFM.Listeners", format_number(lastfm_track.get('listeners', '0')))
                
                # Playcount
                win.setProperty("Song.LastFM.Playcount", format_number(lastfm_track.get('playcount', '0')))
                
                # Tags
                tags_data = lastfm_track.get('toptags', {})
                if isinstance(tags_data, dict):
                    tags_list = tags_data.get('tag', [])
                    if isinstance(tags_list, list) and tags_list:
                        tag_names = [tag.get('name', '') for tag in tags_list[:5] if isinstance(tag, dict) and tag.get('name')]
                        tags_string = ' / '.join(tag_names)
                        win.setProperty("Song.LastFM.Tags", tags_string)
                    else:
                        win.setProperty("Song.LastFM.Tags", "")
                else:
                    win.setProperty("Song.LastFM.Tags", "")
            else:
                win.setProperty("Song.LastFM.Listeners", "")
                win.setProperty("Song.LastFM.Playcount", "")
                win.setProperty("Song.LastFM.Tags", "")
        else:
            win.setProperty("Song.LastFM.Listeners", "")
            win.setProperty("Song.LastFM.Playcount", "")
            win.setProperty("Song.LastFM.Tags", "")
        
        return

    if action == "load_album_details":
        # Artist and album names are passed via Window properties (safe for special characters)
        win = xbmcgui.Window(10000)
        artist_name = win.getProperty("audio.theaudiodb.helper.AlbumArtist")
        album_name = win.getProperty("audio.theaudiodb.helper.AlbumName")
        
        if not artist_name or not album_name:
            log("No artist or album name provided for album details", xbmc.LOGERROR)
            return
        
        # Get user settings
        use_lastfm = ADDON.getSettingBool('biography_use_lastfm')
        custom_lastfm_key = ADDON.getSettingString('lastfm_api_key').strip()
        auto_save_description = ADDON.getSettingBool('biography_auto_save')
        auto_save_artwork = ADDON.getSettingBool('artwork_auto_save')
        
        # Get Kodi's current language
        kodi_language = xbmc.getLanguage(xbmc.ISO_639_1)
        
        description = ""
        source = ""
        
        # Get TheAudioDB album info once
        tadb_album = videolinks.get_album_info(artist_name, album_name)
        
        # Priority 1: TheAudioDB in Kodi's language
        if tadb_album:
            desc_field = TADB_DESC_FIELDS.get(kodi_language, 'strDescriptionEN')
            description = tadb_album.get(desc_field, "") or ""
            if description:
                source = "TheAudioDB"
        
        # Priority 2: Last.fm in Kodi's language
        if not description and use_lastfm:
            lastfm_album = videolinks.get_lastfm_album_info(artist_name, album_name, kodi_language, custom_lastfm_key)
            temp_desc = _extract_lastfm_wiki(lastfm_album, min_length=0)
            if temp_desc:
                description = temp_desc
                source = "Last.fm"
        
        # Priority 3: TheAudioDB in English
        if not description and tadb_album:
            description = tadb_album.get('strDescriptionEN', "") or ""
            if description:
                source = "TheAudioDB"
        
        # Priority 4: Last.fm in English
        if not description and use_lastfm:
            lastfm_album = videolinks.get_lastfm_album_info(artist_name, album_name, 'en', custom_lastfm_key)
            temp_desc = _extract_lastfm_wiki(lastfm_album, min_length=0)
            if temp_desc:
                description = temp_desc
                source = "Last.fm"
        
        # Clean up Last.fm HTML tags if present
        if description and source == "Last.fm":
            description = clean_lastfm_html(description)
        
        # Discard descriptions that are too short (placeholder texts)
        if description and len(description) < 70:
            description = ""
            source = ""
        
        # Set album description properties
        win.setProperty("Album.TADB.Description", description)
        win.setProperty("Album.Description.Source", source)
        
        # Set all TheAudioDB album properties
        if tadb_album:
            # Images (strAlbumThumbBack for legacy, strAlbumBack for new API responses)
            win.setProperty("Album.TADB.Thumb",      tadb_album.get("strAlbumThumb", "") or "")
            win.setProperty("Album.TADB.ThumbBack",   tadb_album.get("strAlbumThumbBack", "") or tadb_album.get("strAlbumBack", "") or "")
            win.setProperty("Album.TADB.CDart",       tadb_album.get("strAlbumCDart", "") or "")
            win.setProperty("Album.TADB.Spine",       tadb_album.get("strAlbumSpine", "") or "")
            win.setProperty("Album.TADB.3DCase",      tadb_album.get("strAlbum3DCase", "") or "")
            win.setProperty("Album.TADB.3DFlat",      tadb_album.get("strAlbum3DFlat", "") or "")
            win.setProperty("Album.TADB.3DFace",      tadb_album.get("strAlbum3DFace", "") or "")
            win.setProperty("Album.TADB.3DThumb",     tadb_album.get("strAlbum3DThumb", "") or "")
            # Metadata
            win.setProperty("Album.TADB.Genre",       tadb_album.get("strGenre", "") or "")
            win.setProperty("Album.TADB.Style",       tadb_album.get("strStyle", "") or "")
            win.setProperty("Album.TADB.Mood",        tadb_album.get("strMood", "") or "")
            win.setProperty("Album.TADB.Year",        str(tadb_album.get("intYearReleased", "") or ""))
            win.setProperty("Album.TADB.Label",       tadb_album.get("strLabel", "") or "")
        else:
            # Clear all TADB album properties if no data found
            for prop in [
                "Album.TADB.Thumb", "Album.TADB.ThumbBack",
                "Album.TADB.CDart", "Album.TADB.Spine",
                "Album.TADB.3DCase", "Album.TADB.3DFlat", "Album.TADB.3DFace", "Album.TADB.3DThumb",
                "Album.TADB.Genre", "Album.TADB.Style", "Album.TADB.Mood",
                "Album.TADB.Year", "Album.TADB.Label"
            ]:
                win.clearProperty(prop)
        
        # Process Last.fm album data
        if use_lastfm:
            # Get Last.fm album info (prefer current language, fallback to English)
            lastfm_data = videolinks.get_lastfm_album_info(artist_name, album_name, kodi_language, custom_lastfm_key)
            if not lastfm_data:
                lastfm_data = videolinks.get_lastfm_album_info(artist_name, album_name, 'en', custom_lastfm_key)
            
            if lastfm_data:
                # Extract and format playcount
                win.setProperty("Album.LastFM.Playcount", format_number(lastfm_data.get('playcount', '0')))
                
                # Extract and format tags
                tags_data = lastfm_data.get('tags', {})
                if isinstance(tags_data, dict):
                    tags_list = tags_data.get('tag', [])
                    if isinstance(tags_list, list) and tags_list:
                        tag_names = [tag.get('name', '') for tag in tags_list[:5] if isinstance(tag, dict) and tag.get('name')]
                        tags_string = ' / '.join(tag_names)
                        win.setProperty("Album.LastFM.Tags", tags_string)
                    else:
                        win.setProperty("Album.LastFM.Tags", "")
                else:
                    win.setProperty("Album.LastFM.Tags", "")
            else:
                win.setProperty("Album.LastFM.Playcount", "")
                win.setProperty("Album.LastFM.Tags", "")
        else:
            win.setProperty("Album.LastFM.Playcount", "")
            win.setProperty("Album.LastFM.Tags", "")
        
        # Get artist description from Kodi database (not available via ListItem in album view)
        try:
            rpc_get_artist = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "AudioLibrary.GetArtists",
                "params": {
                    "filter": {
                        "field": "artist",
                        "operator": "is",
                        "value": artist_name
                    },
                    "properties": ["description"]
                }
            }
            response = xbmc.executeJSONRPC(json.dumps(rpc_get_artist))
            data = json.loads(response)
            artists = data.get("result", {}).get("artists", [])
            if artists:
                artist_bio = artists[0].get("description", "") or ""
                win.setProperty("Album.Artist.Description", artist_bio)
            else:
                win.setProperty("Album.Artist.Description", "")
        except Exception as e:
            log(f"Error getting artist description for '{artist_name}': {str(e)}", xbmc.LOGERROR)
            win.setProperty("Album.Artist.Description", "")
        
        # Auto-save album description and metadata to Kodi database if enabled
        if auto_save_description and album_name and artist_name:
            # Gather metadata from addon sources (TheAudioDB and Last.fm)
            addon_genre = ""
            addon_style = ""
            addon_mood = ""
            addon_label = ""
            if tadb_album:
                addon_genre = tadb_album.get("strGenre", "") or ""
                addon_style = tadb_album.get("strStyle", "") or ""
                addon_mood = tadb_album.get("strMood", "") or ""
                addon_label = tadb_album.get("strLabel", "") or ""
            
            # Only proceed if we have description or any metadata to save
            if description or addon_genre or addon_style or addon_mood or addon_label:
                try:
                    # Find the album in Kodi's database
                    rpc_get_album = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "AudioLibrary.GetAlbums",
                        "params": {
                            "filter": {
                                "and": [
                                    {"field": "album", "operator": "is", "value": album_name},
                                    {"field": "artist", "operator": "is", "value": artist_name}
                                ]
                            },
                            "properties": ["description", "genre", "style", "mood", "albumlabel"]
                        }
                    }
                    
                    response = xbmc.executeJSONRPC(json.dumps(rpc_get_album))
                    data = json.loads(response)
                    
                    albums = data.get("result", {}).get("albums", [])
                    
                    if albums:
                        album_info = albums[0]
                        albumid = album_info.get("albumid")
                        
                        if albumid:
                            save_params = {"albumid": albumid}
                            saved_fields = []
                            
                            # Description: save if empty (requires user confirmation)
                            current_description = album_info.get("description", "")
                            if description and not current_description:
                                win.setProperty('theaudiodb.dialog.type', 'description')
                                if xbmcgui.Dialog().yesno(
                                    ADDON.getLocalizedString(32014),
                                    ''
                                ):
                                    save_params["description"] = description
                                    saved_fields.append("description")
                                else:
                                    log(f"User declined saving description for album '{album_name}' by '{artist_name}'")
                                win.clearProperty('theaudiodb.dialog.type')
                            
                            # Genre (no confirmation needed)
                            current_genre = album_info.get("genre", [])
                            if addon_genre and not current_genre:
                                save_params["genre"] = [addon_genre]
                                saved_fields.append("genre")
                            
                            # Style (no confirmation needed)
                            current_style = album_info.get("style", [])
                            if addon_style and not current_style:
                                save_params["style"] = [addon_style]
                                saved_fields.append("style")
                            
                            # Mood (no confirmation needed)
                            current_mood = album_info.get("mood", [])
                            if addon_mood and not current_mood:
                                save_params["mood"] = [addon_mood]
                                saved_fields.append("mood")
                            
                            # Album label (no confirmation needed)
                            current_label = album_info.get("albumlabel", "")
                            if addon_label and not current_label:
                                save_params["albumlabel"] = addon_label
                                saved_fields.append("albumlabel")
                            
                            if len(save_params) > 1:  # More than just albumid
                                rpc_set_album = {
                                    "jsonrpc": "2.0",
                                    "id": 2,
                                    "method": "AudioLibrary.SetAlbumDetails",
                                    "params": save_params
                                }
                                
                                xbmc.executeJSONRPC(json.dumps(rpc_set_album))
                                log(f"Auto-saved to database for album '{album_name}' by '{artist_name}': {', '.join(saved_fields)}")
                            else:
                                log(f"Nothing to save for album '{album_name}' - database already has description and metadata")
                    else:
                        log(f"Could not find album '{album_name}' by '{artist_name}' in database for auto-save", xbmc.LOGWARNING)
                        
                except Exception as e:
                    log(f"Error auto-saving description/metadata for album '{album_name}': {str(e)}", xbmc.LOGERROR)
        
        # Auto-save album artwork to Kodi database if enabled and TADB data was found
        if auto_save_artwork and tadb_album and album_name and artist_name:
            try:
                # Find the album in Kodi's database
                rpc_get_album = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "AudioLibrary.GetAlbums",
                    "params": {
                        "filter": {
                            "and": [
                                {"field": "album", "operator": "is", "value": album_name},
                                {"field": "artist", "operator": "is", "value": artist_name}
                            ]
                        },
                        "properties": ["art"]
                    }
                }
                
                response = xbmc.executeJSONRPC(json.dumps(rpc_get_album))
                data = json.loads(response)
                
                albums = data.get("result", {}).get("albums", [])
                
                if albums:
                    album_info = albums[0]
                    albumid = album_info.get("albumid")
                    current_art = album_info.get("art", {}) or {}
                    
                    if albumid:
                        # Mapping: Kodi art type -> TheAudioDB field
                        art_mapping = {
                            'thumb':    'strAlbumThumb',
                            'back':     'strAlbumThumbBack',
                            'discart':  'strAlbumCDart',
                            'spine':    'strAlbumSpine',
                            '3dcase':   'strAlbum3DCase',
                            '3dflat':   'strAlbum3DFlat',
                            '3dface':   'strAlbum3DFace',
                            '3dthumb':  'strAlbum3DThumb',
                        }
                        
                        # Build art dict with only missing images
                        art_to_save = {}
                        for kodi_type, tadb_field in art_mapping.items():
                            if not current_art.get(kodi_type):
                                tadb_url = tadb_album.get(tadb_field, "") or ""
                                # Fallback: strAlbumBack (new API field name for back cover)
                                if not tadb_url and tadb_field == 'strAlbumThumbBack':
                                    tadb_url = tadb_album.get("strAlbumBack", "") or ""
                                if tadb_url:
                                    art_to_save[kodi_type] = tadb_url
                        
                        if art_to_save:
                            rpc_set_art = {
                                "jsonrpc": "2.0",
                                "id": 3,
                                "method": "AudioLibrary.SetAlbumDetails",
                                "params": {
                                    "albumid": albumid,
                                    "art": art_to_save
                                }
                            }
                            
                            xbmc.executeJSONRPC(json.dumps(rpc_set_art))
                            saved_types = ', '.join(art_to_save.keys())
                            log(f"Artwork auto-saved to database for album '{album_name}' by '{artist_name}': {saved_types}")
                        else:
                            log(f"Artwork not saved for album '{album_name}' - database already has all available artwork")
                else:
                    log(f"Could not find album '{album_name}' by '{artist_name}' in database for artwork auto-save", xbmc.LOGWARNING)
                    
            except Exception as e:
                log(f"Error auto-saving artwork for album '{album_name}': {str(e)}", xbmc.LOGERROR)
        
        return


if __name__ == "__main__":
    main()
