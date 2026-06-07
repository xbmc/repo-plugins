#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
from urllib.parse import urlencode, parse_qsl

# Addon info
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')

# Base URL for c3lounge
BASE_URL = "https://c3lounge.de"
STREAM_BASE_URL = "https://live.c3lounge.de:8000"
API_URL = f"{STREAM_BASE_URL}/status-json.xsl"


def log(msg, level=xbmc.LOGINFO):
    """Log message to Kodi log"""
    xbmc.log(f"[{ADDON_ID}] {msg}", level)


def get_url(**kwargs):
    """Create a URL for calling the plugin"""
    return f"{sys.argv[0]}?{urlencode(kwargs)}"


def get_now_playing():
    """Get now playing information from Icecast API"""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Icecast returns data in icestats.source array
        if 'icestats' in data and 'source' in data['icestats']:
            sources = data['icestats']['source']
            if isinstance(sources, list) and len(sources) > 0:
                # Return the first mp3 stream source with metadata
                for source in sources:
                    if 'artist' in source and 'title' in source:
                        return source
                return sources[0]
            return sources
        return None
    except Exception as e:
        log(f"Error fetching now playing data: {e}", xbmc.LOGERROR)
        return None


def get_stream_url():
    """Get the stream URL from the station info"""
    try:
        # Get quality setting
        quality = ADDON.getSetting('stream_quality')

        # Map quality to stream format
        quality_map = {
            'High': '192.mp3',    # 192kbps MP3
            'Medium': '64.opus',  # 64kbps OPUS
            'Low': '32.opus'      # 32kbps OPUS
        }

        stream_file = quality_map.get(quality, '192.mp3')
        return f"{STREAM_BASE_URL}/{stream_file}"

    except Exception as e:
        log(f"Error getting stream URL: {e}", xbmc.LOGERROR)
        return f"{STREAM_BASE_URL}/192.mp3"


def play_stream():
    """Play the radio stream"""
    stream_url = get_stream_url()
    log(f"Playing stream: {stream_url}")

    # Get now playing info for metadata
    now_playing = get_now_playing()

    # Create list item
    list_item = xbmcgui.ListItem(path=stream_url)
    list_item.setProperty('IsPlayable', 'true')

    # Set metadata if available
    if now_playing:
        try:
            # Icecast provides artist and title directly
            title = now_playing.get('title', 'c3lounge Radio')
            artist = now_playing.get('artist', '')

            list_item.setInfo('music', {
                'title': title,
                'artist': artist,
                'mediatype': 'song'
            })

            log(f"Now playing: {artist} - {title}")
        except Exception as e:
            log(f"Error setting metadata: {e}", xbmc.LOGERROR)

    list_item.setContentLookup(False)

    # Play the stream
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=list_item)


def show_now_playing():
    """Show now playing information"""
    now_playing = get_now_playing()

    if now_playing:
        try:
            # Icecast provides artist and title directly
            title = now_playing.get('title', 'Unknown')
            artist = now_playing.get('artist', 'Unknown')
            listeners = now_playing.get('listeners', 0)

            message = f"Artist: {artist}\nTitle: {title}"
            message += f"\n\nListeners: {listeners}"

            xbmcgui.Dialog().ok('Now Playing', message)
        except Exception as e:
            log(f"Error showing now playing: {e}", xbmc.LOGERROR)
            xbmcgui.Dialog().ok('Error', 'Could not fetch now playing information')
    else:
        xbmcgui.Dialog().ok('Error', 'Could not fetch now playing information')


def list_categories():
    """List available categories/actions"""
    # Add "Play c3lounge Radio" item
    list_item = xbmcgui.ListItem(label="Play c3lounge Radio")
    list_item.setProperty('IsPlayable', 'true')
    list_item.setInfo('music', {
        'title': 'c3lounge Radio Stream',
        'mediatype': 'song'
    })
    url = get_url(action='play')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def router(paramstring):
    """Route to the appropriate function based on the provided paramstring"""
    params = dict(parse_qsl(paramstring))

    if not params:
        # No parameters - show main menu
        list_categories()
    else:
        action = params.get('action')

        if action == 'play':
            play_stream()
        elif action == 'nowplaying':
            show_now_playing()
            # Refresh the directory to go back to menu
            xbmc.executebuiltin('Container.Refresh')
        else:
            list_categories()


if __name__ == '__main__':
    log(f"Starting {ADDON_NAME} v{ADDON_VERSION}")
    router(sys.argv[2][1:])
