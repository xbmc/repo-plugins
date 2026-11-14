"""What the lists' rows are made of: labels, art and info tags (see the views)."""

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import kodiutil
from resources.lib.data import guidedata
from resources.lib.util import localtime

_s = kodiutil.string
_log = kodiutil.log


def row_title(prog):
    """Return a channel row's first line: "07:30 Title | S1E10: Episode title", the parts it has."""
    title = prog["description"]
    if prog.get("start_time"):
        title = "%s %s" % (localtime.local_time(prog["start_time"], date=False), title)
    return with_episode(title, prog)


def with_episode(text, prog):
    """Return text with the programme's episode after a bar ("| S1E10: Episode title"), grey, where it has one."""
    numbers, name = guidedata.season_episode(prog), prog.get("episode_name") or ""
    episode = ": ".join(filter(None, ["S%dE%d" % numbers if numbers else "", name if name != prog.get("description") else ""]))
    return "%s%s" % (text, greyed(" | %s" % episode)) if episode else text


def not_available():
    """Return why a channel outside the subscription does not play, in Kodi's words ("Not available")."""
    return kodiutil.kodi_string(10005)


def greyed(text):
    """Return text in the skin's grey: a row that does not play, or what is said beside a label."""
    return kodiutil.coloured("grey", text)


def with_note(label, note):
    """Return a label with a note beside it, grey and italic (a row's state, a menu row's count); as it is without one."""
    return "%s  [I]%s[/I]" % (label, greyed(note)) if note else label


def panel_logo(url):
    """Return the large size of a channel logo, which fits Estuary's side panel (561x421)."""
    return url.replace("/logomedium.png", "/logolarge.png") if url else url


def menu_item(label, icon=None):
    """Return a menu row with this icon (one of Kodi's own, e.g. "DefaultFavourites.png")."""
    li = xbmcgui.ListItem(label)
    if icon:
        li.setArt({"icon": icon, "thumb": icon})
    return li


def set_art(li, art):
    """Give a row the pictures of `art` that it has (empty ones left out: Kodi would show them as missing)."""
    li.setArt({k: v for k, v in art.items() if v})


def set_mpaa(tag, ratings):
    """Give a row the programme's age rating, unless it is "for all ages" ("0-99", which says nothing)."""
    if guidedata.rating_age(ratings):
        tag.setMpaa(ratings)


def film_title(title, year):
    """Return a film's title with its year after it, as Kodi's film lists show it: "Tűnj el! (2017)"."""
    return "%s (%d)" % (title, year) if year else title


def cast_of(pages, kinds):
    """Return the pages of the programmes whose type is among `kinds` (the cast settings')."""
    return {key: page for key, page in pages.items() if page.get("type") in kinds}


def set_credits(tag, info):
    """Put an info page's cast, directors and writers (see infopages) on an item's info tag."""
    info = info or {}
    if info.get("actor"):
        tag.setCast([xbmc.Actor(name, "", order) for order, name in enumerate(info["actor"])])
    if info.get("director"):
        tag.setDirectors(info["director"])
    if info.get("writer"):
        tag.setWriters(info["writer"])


def set_length(tag, seconds):
    """Give a row the programme's length, also as its stream's.

    Otherwise Kodi shows the kept stream length of what played from that address (a live
    channel's 15-minute window) in place of the row's.
    """
    if seconds:
        tag.setDuration(seconds)
        tag.addVideoStream(xbmc.VideoStreamDetail(duration=seconds))


def set_programme_extras(tag, prog):
    """Put a guide programme's length and accessibility flags (as tags) on its row's info tag."""
    set_length(tag, guidedata.duration(prog.get("start_time"), prog.get("end_time")))
    tags = [_s(i) for i in guidedata.access_tags(prog)]
    if tags:
        tag.setTags(tags)


def hide_right_labels(handle):
    """Show the rows' own labels and nothing on their right in this list.

    Without a sort method of its own, Kodi shows a plugin row's length there.
    """
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE, labelMask="%L", label2Mask=" ")


def set_channel_sort_keys(tag, channel, position):
    """Give a channel's row what Kodi's sorts read (see add_channel_sorts): its place, name and number."""
    tag.setProductionCode("%04d" % position)
    tag.setStudios([channel["name"]])
    if channel.get("number"):
        tag.setTrackNumber(int(channel["number"]))


def add_channel_sorts(handle):
    """Offer the channel lists' sorts in Kodi's side menu: the lists' own order, by name, by number.

    Kodi sorts a plugin's rows by none of its channel fields (those are its own TV's), so the own
    order is the row's production code ("Production code", "Gyártási kód"), the name its studio
    ("Studio") and the number its track number ("Track", "Szám"). Kodi's "Default" is left out: it
    sorts nothing, so after another sort it kept that one's order. "%L" keeps the row's own label:
    Kodi shows the info title otherwise.
    """
    for method in (xbmcplugin.SORT_METHOD_PRODUCTIONCODE, xbmcplugin.SORT_METHOD_STUDIO, xbmcplugin.SORT_METHOD_TRACKNUM):
        xbmcplugin.addSortMethod(handle, method, labelMask="%L")


def favourite_channel_item(label_on):
    """Return Kodi's own words for putting a channel onto the favourites (True) or off them.

    The channel rows hide Kodi's own favourites item (see hide_kodi_favourites): the account's take its words.
    """
    return kodiutil.kodi_string(14076 if label_on else 14077)  # "Add to favourites", "Remove from favourites"


def hide_kodi_favourites(li):
    """Leave Kodi's own "Add to favourites" out of a channel row's context menu (the account's has its words)."""
    li.setProperty("hide_add_remove_favourite", "true")
