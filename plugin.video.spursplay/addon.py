import base64
import json
import sys
from datetime import datetime
import time
from urllib.parse import parse_qsl, urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import resources.lib.spursplay as spursplay


plugin_handle = int(sys.argv[1])

api = spursplay.Api()


def router(paramstring):
    params = dict(parse_qsl(paramstring[1:]))
    if params:
        if params["action"] == "play":
            play_video(params["id"], "live" in params)
        elif params["action"] == "listing":
            list_videos(params["id"], params.get("lastSeen"))
        elif params["action"] == "playlists":
            list_playlists(params["id"], params.get("lastSeen"))
        elif params["action"] == "playlist-listing":
            list_playlist_videos(params["id"], params.get("page"))
        elif params["action"] == "section":
            list_section(params["name"])
    else:
        list_categories()


def build_url(**params):
    return f"{sys.argv[0]}?{urlencode(params)}"


def token_expiry(jwt):
    payload_base64 = (jwt.split(".")[1] + "==").encode("ascii")
    return datetime.fromtimestamp(json.loads(base64.urlsafe_b64decode(payload_base64))["exp"])


def log(message, level=xbmc.LOGDEBUG):
    xbmc.log(f"SPURSPLAY: {message}", level=level)


def login():
    addon = xbmcaddon.Addon()

    email, password = addon.getSetting("email"), addon.getSetting("password")
    token = addon.getSetting("token")
    refresh_token = addon.getSetting("refresh_token")

    if not email or not password:
        log("No credentials configured, browsing anonymously")
        return

    if token:
        try:
            expiry = token_expiry(token)
        except (ValueError, KeyError, IndexError) as exc:
            log(f"Stored token is unparseable ({exc!r}), discarding it", level=xbmc.LOGWARNING)
        else:
            if datetime.now() <= expiry:
                log(f"Reusing stored token (expires {expiry})")
                api.token = token
                api.signed_in = True
                return
            log(f"Stored token expired at {expiry}")
    else:
        log("No stored token")

    try:
        if refresh_token:
            log("Refreshing session with stored refresh token")
            try:
                token, refresh_token = api.refresh(refresh_token)
            except spursplay.LoginError as exc:
                log(f"Refresh failed ({exc}), logging in with credentials", level=xbmc.LOGWARNING)
                token, refresh_token = api.login(email, password)
        else:
            log("No stored refresh token, logging in with credentials")
            token, refresh_token = api.login(email, password)
    except spursplay.LoginError as exc:
        log(f"Login failed: {exc}", level=xbmc.LOGWARNING)
        dialog = xbmcgui.Dialog()
        dialog.notification("SPURSPLAY", str(exc), xbmcgui.NOTIFICATION_ERROR)
    else:
        log(f"Login succeeded, saving tokens (token expires {token_expiry(token)})")
        api.signed_in = True
        addon.setSetting("token", token)
        addon.setSetting("refresh_token", refresh_token)
        if not xbmcaddon.Addon().getSetting("token"):
            log("Token did not persist after setSetting", level=xbmc.LOGWARNING)


def list_categories():
    events = api.get_live_events()
    listing = list(video_items(events, live=True))

    # Bucket names to include from the "First Team" section. Anything not listed here
    # is skipped, including ones the club has stopped updating (e.g. "Matchday Uncut").
    allowed_buckets = {
        "Latest",
        "Key Highlights",
        "Full-Match Replays",
        "Golden Goal",
        "Off The Pitch",
        "Our Squad",
    }

    buckets = api.buckets(section="First Team", num_pages=2)
    for name, category_id, bucket_type in buckets:
        # SPURSPLAY has never updated this bucket's name to match the current season
        # (it's been stuck on "Extended Highlights 2021-22" for years), despite the
        # content itself being kept up to date - match by prefix so this keeps working
        # if they ever fix it.
        if name.startswith("Extended Highlights"):
            label = "Extended Highlights"
        elif name in allowed_buckets:
            label = name
        else:
            continue
        list_item = xbmcgui.ListItem(label=label)
        action = "playlists" if bucket_type == "PLAYLISTS" else "listing"
        url = build_url(action=action, id=category_id)
        listing.append((url, list_item, True))

    for name, category_id in [
        ("Originals", "Pb3a"),
        ("Podcasts", "RtHs"),
        ("Classic Matches", "i-p7"),
        ("Press Conferences", "tfvz"),
        ("Goals, Goals, Goals", "PkHA"),
    ]:
        if not api.signed_in and api.is_signed_in_only(category_id):
            continue
        list_item = xbmcgui.ListItem(label=name)
        url = build_url(action="listing", id=category_id)
        listing.append((url, list_item, True))

    for section in ["Academy"]:
        list_item = xbmcgui.ListItem(label=section)
        url = build_url(action="section", name=section)
        listing.append((url, list_item, True))

    xbmcplugin.addDirectoryItems(plugin_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin_handle)


def list_section(section):
    listing = []
    buckets = api.buckets(section)
    for name, category_id, bucket_type in buckets:
        xbmc.log(name, level=xbmc.LOGDEBUG)
        list_item = xbmcgui.ListItem(label=name)
        action = "playlists" if bucket_type == "PLAYLISTS" else "listing"
        url = build_url(action=action, id=category_id)
        listing.append((url, list_item, True))

    xbmcplugin.addDirectoryItems(plugin_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin_handle)


def list_playlists(category_id, last_seen=None):
    playlists, new_last_seen, more_available = api.get_bucket_playlists(category_id, last_seen)
    listing = []
    for playlist in playlists:
        list_item = xbmcgui.ListItem(label=playlist["title"])
        thumb = playlist["thumbnail"]
        list_item.setArt({"icon": thumb, "thumb": thumb})
        url = build_url(action="playlist-listing", id=playlist["id"])
        listing.append((url, list_item, True))

    if more_available:
        list_item = xbmcgui.ListItem(label="Show More")
        url = build_url(action="playlists", id=category_id, lastSeen=new_last_seen)
        listing.append((url, list_item, True))

    xbmcplugin.addDirectoryItems(plugin_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin_handle, updateListing=last_seen is not None)


def video_items(videos, live=False):
    for video in videos:
        list_item = xbmcgui.ListItem(label=video["title"])
        thumb = video["thumbnail"]
        if live:
            timestamp = round(time.time() / 60) * 60
            thumb += f"?ts={timestamp}"  # Add a timestamp to bust the live thumbnail cache every minute
        list_item.setProperty("IsPlayable", "true")
        list_item.setArt({"icon": thumb, "thumb": thumb, "poster": video["poster"], "fanart": video["cover"]})
        video_info = list_item.getVideoInfoTag()
        video_info.setTitle(video["title"])
        if video["description"]:
            video_info.setPlot(video["description"])
        if video["duration"] is not None:
            video_info.setDuration(video["duration"])
        if video["date"]:
            video_info.setPremiered(video["date"])
        params = {"action": "play", "id": video["id"]}
        if live:
            params["live"] = "true"
        url = build_url(**params)
        yield (url, list_item, False)


def list_playlist_videos(playlist_id, page=None):
    videos, more_available = api.get_playlist_videos(playlist_id, page)

    listing = list(video_items(videos))

    if more_available:
        list_item = xbmcgui.ListItem(label="Show More")
        url = build_url(action="playlist-listing", id=playlist_id, page=int(page or 1) + 1)
        listing.append((url, list_item, True))

    xbmcplugin.addDirectoryItems(plugin_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin_handle, updateListing=page is not None)


def list_videos(category_id="J34p", last_seen=None):
    videos, new_last_seen, more_available = api.get_bucket_videos(category_id, last_seen)

    listing = list(video_items(videos))

    if more_available:
        list_item = xbmcgui.ListItem(label="Show More")
        url = build_url(action="listing", id=category_id, lastSeen=new_last_seen)
        listing.append((url, list_item, True))

    xbmcplugin.addDirectoryItems(plugin_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin_handle, updateListing=last_seen is not None)


def play_video(video_id, live):
    url = api.get_video_url(video_id, live)
    play_item = xbmcgui.ListItem(path=url)

    if url and live and xbmc.getCondVisibility("System.HasAddon(inputstream.adaptive)"):
        # Kodi's built-in demuxer treats live HLS as a non-seekable feed. Route it
        # through inputstream.adaptive so pause and seek within the DVR window work.
        play_item.setProperty("inputstream", "inputstream.adaptive")
        play_item.setProperty("inputstream.adaptive.manifest_type", "hls")
        play_item.setMimeType("application/vnd.apple.mpegurl")
        play_item.setContentLookup(False)

    xbmcplugin.setResolvedUrl(plugin_handle, succeeded=url is not None, listitem=play_item)


if __name__ == "__main__":
    login()
    router(sys.argv[2])
