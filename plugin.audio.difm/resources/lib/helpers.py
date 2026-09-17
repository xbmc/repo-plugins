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
    current,
    stream_url,
    channel_art="",
    channel_fanart="",
):
    """Build the initial Kodi ListItem for a linear DI.FM stream."""
    item = xbmcgui.ListItem(path=stream_url)
    title = channel_name
    artist = "DI.FM"
    thumb = ""

    if isinstance(current, dict):
        title = (
            current.get("display_title")
            or current.get("title")
            or title
        )
        artist = current.get("display_artist") or artist
        images = current.get("images")
        thumb = image_url(
            current.get("asset_url")
            or (
                images.get("default")
                if isinstance(images, dict)
                else ""
            )
        )

    tag = item.getMusicInfoTag()
    tag.setTitle(str(title))
    tag.setArtist(str(artist))
    tag.setAlbum(f"DI.FM — {channel_name}")

    art = {}
    if thumb or channel_art:
        art["thumb"] = thumb or channel_art
        art["icon"] = thumb or channel_art

    if channel_fanart or channel_art:
        art["fanart"] = channel_fanart or channel_art

    if art:
        item.setArt(art)

    return item
