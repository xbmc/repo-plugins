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
    return datetime.fromtimestamp(json.loads(base64.b64decode(payload_base64))["exp"])


def login():
    settings = xbmcaddon.Addon().getSettings()

    email, password = settings.getString(id="email"), settings.getString(id="password")
    token = settings.getString(id="token")

    if email and password and (not token or datetime.now() > token_expiry(token)):
        xbmc.log("Logging in", level=xbmc.LOGDEBUG)
        try:
            token = api.login(email, password)
        except spursplay.LoginError as exc:
            dialog = xbmcgui.Dialog()
            dialog.notification("SPURSPLAY", str(exc), xbmcgui.NOTIFICATION_ERROR)
        else:
            settings.setString("token", token)


def list_categories():
    events = api.get_live_events()
    listing = list(video_items(events, live=True))

    buckets = api.buckets(section="First Team", num_pages=2)
    for name, category_id in buckets:
        list_item = xbmcgui.ListItem(label=name)
        url = build_url(action="listing", id=category_id)
        listing.append((url, list_item, True))

    playlists = api.playlists()
    for name, category_id in playlists:
        list_item = xbmcgui.ListItem(label=name)
        url = build_url(action="playlists", id=category_id)
        listing.append((url, list_item, True))

    for section in ["Originals", "Academy", "Players"]:
        list_item = xbmcgui.ListItem(label=section)
        url = build_url(action="section", name=section)
        listing.append((url, list_item, True))

    xbmcplugin.addDirectoryItems(plugin_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin_handle)


def list_section(section):
    listing = []
    buckets = api.buckets(section)
    for name, category_id in buckets:
        xbmc.log(name, level=xbmc.LOGDEBUG)
        list_item = xbmcgui.ListItem(label=name)
        url = build_url(action="listing", id=category_id)
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
        list_item.setInfo(type="video", infoLabels={"plot": video["description"]})
        video_info = list_item.getVideoInfoTag()
        video_info.setTitle(video["title"])
        if video["duration"] is not None:
            video_info.setDuration(video["duration"])
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

    xbmcplugin.setResolvedUrl(plugin_handle, True, listitem=play_item)


if __name__ == "__main__":
    login()
    router(sys.argv[2])
