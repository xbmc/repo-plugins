# -*- coding: utf-8 -*-
"""Kodi ListItem/artwork helpers for DI.FM channels and Now Playing."""
from __future__ import annotations

import xbmcgui


def image_url(value):
    """Normalise an AudioAddict image URL without forcing a small resize."""
    if not value or not isinstance(value, str):
        return ""

    # Some API image URLs contain a resize template. Using the base URL
    # requests the original resource instead of a deliberately small image.
    if "{" in value:
        value = value.split("{", 1)[0]

    if value.startswith("//"):
        return "https:" + value

    return value


def channel_images(channel):
    """Return the best thumbnail and wide fanart found for a channel."""
    if not isinstance(channel, dict):
        return "", ""

    thumb = image_url(channel.get("asset_url"))
    fanart = image_url(channel.get("banner_url"))
    images = channel.get("images")

    if isinstance(images, dict):
        for key in ("hero", "background", "fanart", "banner", "wide"):
            candidate = image_url(images.get(key))
            if candidate:
                fanart = candidate
                break

        if not thumb:
            for key in ("default", "compact", "square"):
                candidate = image_url(images.get(key))
                if candidate:
                    thumb = candidate
                    break

    return thumb, fanart or thumb


def music_listitem(
    channel_name,
    stream_url,
    channel_art="",
    channel_fanart="",
):
    """Build the initial Kodi ListItem for a linear DI.FM stream."""
    item = xbmcgui.ListItem(path=stream_url)

    tag = item.getMusicInfoTag()
    tag.setTitle(str(channel_name))
    tag.setArtist("DI.FM")
    tag.setAlbum(f"DI.FM — {channel_name}")

    art = {}
    if channel_art:
        art["thumb"] = channel_art
        art["icon"] = channel_art

    if channel_fanart or channel_art:
        art["fanart"] = channel_fanart or channel_art

    if art:
        item.setArt(art)

    return item
