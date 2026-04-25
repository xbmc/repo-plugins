#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcaddon
import sys
import json
import unicodedata

ADDON = xbmcaddon.Addon()
WINDOW = xbmcgui.Window(10000)  # Home window

LOG_PREFIX = "[audio.theaudiodb.helper.DBID] "

def log(msg):
    xbmc.log(LOG_PREFIX + msg, xbmc.LOGINFO)

def get_param(name):
    raw = sys.argv[1] if len(sys.argv) > 1 else ""

    if not raw:
        return None

    if raw.startswith('?'):
        raw = raw[1:]

    prefix = name + "="
    if not raw.startswith(prefix):
        return None

    value = raw[len(prefix):]
    return value

def normalize_artist_name(name):
    if not name:
        return ""
    n = unicodedata.normalize("NFC", name.strip())
    return n

def get_artist_dbid(artist_name):
    query = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "AudioLibrary.GetArtists",
        "params": {
            "filter": {
                "field": "artist",
                "operator": "is",
                "value": artist_name
            }
        }
    }

    rpc_string = json.dumps(query)
    response = xbmc.executeJSONRPC(rpc_string)

    try:
        data = json.loads(response)
    except Exception as e:
        log(f"JSON decode error: {e}")
        return None

    artists = data.get("result", {}).get("artists", [])

    if not artists:
        return None

    dbid = artists[0].get("artistid")
    return dbid

def main():
    artist = get_param("artist")

    if not artist:
        WINDOW.clearProperty("audio.theaudiodb.Artist.DBID")
        return

    artist = normalize_artist_name(artist)

    dbid = get_artist_dbid(artist)

    if dbid is None:
        WINDOW.clearProperty("audio.theaudiodb.Artist.DBID")
    else:
        WINDOW.setProperty("audio.theaudiodb.Artist.DBID", str(dbid))

if __name__ == "__main__":
    main()
