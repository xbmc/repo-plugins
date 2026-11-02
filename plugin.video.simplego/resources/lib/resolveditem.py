"""The ListItem Kodi plays, built from a stream's spec (see stream.playitem.spec).

Imports only Kodi's GUI module and the standard-library guidedata: quickplay builds it on the
fast channel-switch path.
"""

import xbmcgui

from resources.lib.data import guidedata


def list_item(item_spec):
    """Build the ListItem a spec (see stream.playitem.spec) describes."""
    li = xbmcgui.ListItem(path=item_spec["path"])
    li.setMimeType(item_spec["mimetype"])
    li.setContentLookup(False)
    for key, value in item_spec["properties"].items():
        li.setProperty(key, value)
    if item_spec.get("details"):
        _describe(li, item_spec["details"])
    if item_spec.get("logo"):
        # Kodi's playback info shows poster, else tvshow.poster, else icon; a resolved item's art is
        # added to its row's. Live: the logo, not the row's 2:3 poster. Watched back: its 16:9 picture.
        logo = item_spec["logo"]
        li.setArt({"icon": logo} if item_spec.get("details") else {"icon": logo, "poster": logo})
    return li


def _describe(li, details):
    """Put a programme's guide details (see guidedata.details) on the item Kodi plays."""
    tag = li.getVideoInfoTag()
    if details["episode"]:
        tag.setTvShowTitle(details["title"])
        tag.setTitle(details["episode"])
    else:
        tag.setTitle(details["title"])
    tag.setPlot(details["plot"])
    tag.setGenres(details["genres"])
    tag.setMediaType(guidedata.media_type(details["type"], bool(details["episode"] or details.get("season"))))
    if details.get("year"):
        tag.setYear(details["year"])
    if details.get("season"):
        tag.setSeason(details["season"])
        tag.setEpisode(details["number"])
    # The 16:9 picture as poster too: the playback info shows the poster.
    art = {"thumb": details["image"], "fanart": details["image"], "poster": details["image"]}
    li.setArt({k: v for k, v in art.items() if v})
