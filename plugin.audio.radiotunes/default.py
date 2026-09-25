# -*- coding: utf-8 -*-
"""Kodi directory/plugin entry point for the RadioTunes add-on."""
from __future__ import annotations

import sys
from urllib.parse import urlencode, parse_qsl

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.client import AudioAddictClient, AudioAddictError
from resources.lib.helpers import channel_images, image_url, music_listitem
from resources.lib.state import save_state

ADDON_ID = "plugin.audio.radiotunes"
ADDON = xbmcaddon.Addon(ADDON_ID)
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]


def t(string_id):
    """Return a localized add-on string."""
    return ADDON.getLocalizedString(string_id)


def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"[plugin.audio.radiotunes] {msg}", level)


def url_for(action, **kwargs):
    p = {"action": action}
    p.update(kwargs)
    return BASE_URL + "?" + urlencode(p)


def add_folder(label, action, art=None, **kwargs):
    li = xbmcgui.ListItem(label=label)
    if art:
        li.setArt({"thumb": art, "icon": art})
    xbmcplugin.addDirectoryItem(
        HANDLE, url_for(action, **kwargs), li, isFolder=True
    )


def add_action(label, action, **kwargs):
    xbmcplugin.addDirectoryItem(
        HANDLE,
        url_for(action, **kwargs),
        xbmcgui.ListItem(label=label),
        isFolder=False,
    )


def add_channel(channel, favorite_ids=None):
    key = channel.get("key")
    cid = channel.get("id")
    name = channel.get("name") or key
    if not key:
        return

    art, fanart = channel_images(channel)

    li = xbmcgui.ListItem(label=name)
    if art or fanart:
        li.setArt({
            "thumb": art or "",
            "icon": art or "",
            "fanart": fanart or art or "",
        })

    tag = li.getMusicInfoTag()
    tag.setTitle(name)
    tag.setArtist("RadioTunes")
    li.setProperty("IsPlayable", "true")

    if cid is not None and favorite_ids is not None:
        isfav = cid in favorite_ids
        favlabel = t(32042) if isfav else t(32041)
        favaction = "favorite_remove" if isfav else "favorite_add"
        li.addContextMenuItems([
            (
                favlabel,
                f'RunPlugin({url_for(favaction, channel_id=str(cid), channel=key)})'
            )
        ])

    xbmcplugin.addDirectoryItem(
        HANDLE,
        url_for(
            "play",
            channel=key,
            channel_id=str(cid or ""),
            channel_name=name,
            channel_art=art or "",
            channel_fanart=fanart or art or "",
        ),
        li,
        isFolder=False,
    )


def finish(content=None):
    if content:
        xbmcplugin.setContent(HANDLE, content)
    xbmcplugin.endOfDirectory(
        HANDLE, succeeded=True, cacheToDisc=False
    )


def root(client):
    add_folder(t(32010), "all")
    add_folder(t(32011), "styles")
    add_folder(t(32012), "favorites")
    add_folder(t(32014), "filter", filter_key="popular")
    add_folder(t(32015), "filter", filter_key="new")
    add_folder(t(32013), "settings")
    finish()


def favorite_ids(client):
    try:
        return client.favorite_channel_ids()
    except AudioAddictError as exc:
        log(f"Unable to retrieve favorites: {exc}", xbmc.LOGWARNING)
        return None


def list_filter(client, key):
    target = next(
        (f for f in client.channel_filters() if f.get("key") == key),
        None,
    )
    if not target:
        raise AudioAddictError(t(32035))

    favs = favorite_ids(client)
    for c in sorted(
        target.get("channels") or [],
        key=lambda x: (x.get("name") or "").lower(),
    ):
        add_channel(c, favs)
    finish("songs")


def list_styles(client):
    fs = [
        f for f in client.channel_filters()
        if f.get("genre") is True and f.get("display", True)
    ]
    fs.sort(
        key=lambda f: (
            f.get("position", 999),
            (f.get("name") or "").lower(),
        )
    )
    for f in fs:
        add_folder(
            f.get("name") or f.get("key"),
            "style",
            art=image_url((f.get("images") or {}).get("compact")),
            filter_id=str(f.get("id")),
        )
    finish()


def list_style(client, filter_id):
    target = next(
        (
            f for f in client.channel_filters()
            if str(f.get("id")) == str(filter_id)
        ),
        None,
    )
    if not target:
        raise AudioAddictError(t(32034))

    favs = favorite_ids(client)
    for c in sorted(
        target.get("channels") or [],
        key=lambda x: (x.get("name") or "").lower(),
    ):
        add_channel(c, favs)
    finish("songs")


def list_favorites(client):
    channels = client.favorite_channels()
    favs = {
        c.get("id")
        for c in channels
        if c.get("id") is not None
    }

    if not channels:
        add_action(t(32043), "noop")
    else:
        for c in sorted(
            channels,
            key=lambda x: (x.get("name") or "").lower(),
        ):
            add_channel(c, favs)
    finish("songs")


def change_favorite(client, channel_id, add):
    if not channel_id:
        raise AudioAddictError(
            t(32036)
        )

    if add:
        client.add_favorite(int(channel_id))
        msg = t(32044)
    else:
        client.remove_favorite(int(channel_id))
        msg = t(32045)

    xbmcgui.Dialog().notification(
        "RadioTunes",
        msg,
        xbmcgui.NOTIFICATION_INFO,
        1600,
        False,
    )
    xbmc.executebuiltin("Container.Refresh")


def play_linear(
    client,
    channel,
    channel_id,
    channel_name="",
    channel_art="",
    channel_fanart="",
):
    stream_url, count = client.resolve_stream(channel)

    # Start playback immediately once the stream is resolved. Track metadata
    # is optional and is populated asynchronously by the background service,
    # so a slow/unavailable metadata endpoint cannot delay audio startup.
    current = None

    name = channel_name or channel
    li = music_listitem(
        channel_name=name,
        current=current,
        stream_url=stream_url,
        channel_art=channel_art,
        channel_fanart=channel_fanart,
    )
    li.setProperty("IsPlayable", "true")

    state = {
        "mode": "linear",
        "channel_key": channel,
        "channel_name": name,
        "channel_id": int(channel_id) if channel_id else None,
        "stream_url": stream_url,
        "channel_art": channel_art or "",
        "channel_fanart": channel_fanart or channel_art or "",
        "track_id": (
            current.get("id")
            if isinstance(current, dict)
            else None
        ),
        "title": (
            current.get("display_title")
            or current.get("title")
            if isinstance(current, dict)
            else None
        ),
        "artist": (
            current.get("display_artist")
            if isinstance(current, dict)
            else None
        ),
    }
    save_state(state)

    log(f"Resolved channel using one of {count} server(s)")
    xbmcplugin.setResolvedUrl(HANDLE, True, li)


def run():
    params = (
        dict(parse_qsl(sys.argv[2][1:]))
        if len(sys.argv) > 2 and sys.argv[2]
        else {}
    )
    action = params.get("action", "root")

    try:
        if action == "settings":
            ADDON.openSettings()
            xbmcplugin.endOfDirectory(
                HANDLE, succeeded=True, cacheToDisc=False
            )
            return

        if action == "noop":
            finish()
            return

        client = AudioAddictClient()

        if action == "root":
            if not client.has_credentials():
                xbmcgui.Dialog().ok(
                    "RadioTunes",
                    t(32030),
                )
                ADDON.openSettings()
                xbmcplugin.endOfDirectory(
                    HANDLE, succeeded=True, cacheToDisc=False
                )
                return
            root(client)

        elif action == "all":
            list_filter(client, "default")
        elif action == "styles":
            list_styles(client)
        elif action == "style":
            list_style(client, params.get("filter_id", ""))
        elif action == "favorites":
            list_favorites(client)
        elif action == "filter":
            list_filter(client, params.get("filter_key", ""))
        elif action == "favorite_add":
            change_favorite(
                client, params.get("channel_id"), True
            )
        elif action == "favorite_remove":
            change_favorite(
                client, params.get("channel_id"), False
            )
        elif action == "play":
            play_linear(
                client,
                params.get("channel", ""),
                params.get("channel_id", ""),
                params.get("channel_name", ""),
                params.get("channel_art", ""),
                params.get("channel_fanart", ""),
            )
        else:
            raise AudioAddictError(t(32038))

    except AudioAddictError as exc:
        log(str(exc), xbmc.LOGERROR)
        xbmcgui.Dialog().ok("RadioTunes", str(exc))
        try:
            xbmcplugin.endOfDirectory(
                HANDLE, succeeded=False, cacheToDisc=False
            )
        except Exception as end_exc:
            log(f"Unable to close failed directory: {end_exc!r}", xbmc.LOGDEBUG)

    except Exception as exc:
        log(f"Unhandled error: {exc!r}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok("RadioTunes", t(32031))
        try:
            xbmcplugin.endOfDirectory(
                HANDLE, succeeded=False, cacheToDisc=False
            )
        except Exception as end_exc:
            log(f"Unable to close failed directory: {end_exc!r}", xbmc.LOGDEBUG)


if __name__ == "__main__":
    run()
