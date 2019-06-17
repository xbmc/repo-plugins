# -*- coding: utf-8 -*-

"""Main plugin file - Handles the various routes"""

__author__ = "fraser"

import logging

import routing
import xbmc
import xbmcaddon
import xbmcplugin
from xbmcgui import ListItem

from resources.lib import kodilogging
from resources.lib import kodiutils as ku
from resources.lib import search as iwm

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # IWM Film

IWM_YEARS = [
    "Pre-1914",
    "1914-1918",
    "1919-1939",
    "1939-1945",
    "1945-1975",
    "1976-2000",
    "2001-2025"
]


def parse_search_results(query, offset, data):
    # type: (str, int, dict) -> Union[None, bool]
    """Adds menu items for search result data"""
    if data is None or not data["results"]:
        return False
    paginate(query, len(data["results"]), int(data["ttlResults"]), offset)
    for child in data["results"]:
        add_menu_item(
            play_film,
            iwm.clean_title(child["Title"]),
            args={"href": child["url"]},
            info={
                "year": child["fieldClasses"]["date"],
                "plot": child["Summary"],
                "duration": iwm.time_to_seconds(child["mediaObjectDuration"])
            },
            art=ku.art(child["refImageUrl"]),
            directory=False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(plugin.handle)


def paginate(query, count, total, offset):
    # type: (str, int, int, int) -> None
    """Adds search partition menu items"""
    if count < total and count == iwm.SEARCH_MAX_RESULTS:
        offset += 1
        if offset > 1:
            add_menu_item(search, "[{} 1]".format(ku.localize(32011)), {"q": query, "offset": 1})
        add_menu_item(search, "[{} {}]".format(ku.localize(32011), offset), {"q": query, "offset": offset})
        add_menu_item(index, "[{}]".format(ku.localize(32012)))


def add_menu_item(method, label, args=None, art=None, info=None, directory=True):
    # type: (Callable, Union[str, int], dict, dict, dict, bool) -> None
    """wrapper for xbmcplugin.addDirectoryItem"""
    info = {} if info is None else info
    art = {} if art is None else art
    args = {} if args is None else args
    label = ku.localize(label) if isinstance(label, int) else label
    list_item = ListItem(label)
    list_item.setArt(art)
    list_item.setInfo("video", info)
    if method == search and "q" in args:
        # saved search menu items can be removed via context menu
        list_item.addContextMenuItems([(
            ku.localize(32019),
            "XBMC.RunPlugin({})".format(plugin.url_for(search, delete=True, q=label))
        )])
    if not directory and method == play_film:
        list_item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(method, **args),
        list_item,
        directory)


def get_arg(key, default=None):
    # type: (str, Any) -> Any
    """Get the argument value or default"""
    if default is None:
        default = ""
    return plugin.args.get(key, [default])[0]


@plugin.route("/")
def index():
    # type: () -> None
    """Main menu"""
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, {"menu": True}, ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    if ku.get_setting_as_bool("show_new"):
        add_menu_item(new, 32004, art=ku.icon("new.png"))  # New Content
    if ku.get_setting_as_bool("show_years"):
        add_menu_item(year, 32006, art=ku.icon("year.png"))  # Years
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32005, art=ku.icon("recent.png"))  # Recent
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/year")
def year():
    # type: () -> None
    for item in IWM_YEARS:
        add_menu_item(search, str(item), args={"period": item})
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32006))  # Years
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/new")
def new():
    # type: () -> Union[None, bool]
    data = iwm.post_form({"zoneID": 6})
    if data is None:
        return False
    for item in data["cellTokens"]:
        title, plot = item["overlay"].split("\n<BR>", 1)
        add_menu_item(
            play_film,
            iwm.clean_title(title),
            args={"href": "/record/{}".format(item["recordID"])},
            info={"plot": plot.replace("<BR>", "")},
            art=ku.art(iwm.get_image_url(item["imageStyle"])),
            directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32004))  # New Content
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = iwm.get_recent()
    for item in data:
        details = iwm.get_info(item["uri"])
        add_menu_item(
            play_film,
            details["title"],
            args={"href": "/record/{}".format(item["uri"].split("/")[-1:][0])},
            info=details["info"],
            art=details["art"],
            directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32005))  # Recent
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/settings")
def settings():
    # type: () -> None
    """Addon Settings"""
    ku.show_settings()
    xbmc.executebuiltin("Container.Refresh()")


@plugin.route("/play")
def play_film():
    # type: () -> None
    """Show playable item"""
    details = iwm.get_info(iwm.get_page_url(get_arg("href")))
    list_item = ListItem(path=iwm.get_m3u8_url(details["soup"].text))
    list_item.setInfo("video", details["info"])
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<token>")
def clear(token):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if token == "cache" and ku.confirm():
        iwm.cache_clear()
    if token == "recent" and ku.confirm():
        iwm.cache_clear()


@plugin.route("/search")
def search():
    # type: () -> Union[bool, None]
    query = get_arg("q")
    offset = int(get_arg("offset", 1))
    period = get_arg("period", "")
    sound = "Sound" if ku.get_setting_as_bool("search_sound") else ""
    colour = "Colour" if ku.get_setting_as_bool("search_colour") else ""
    # remove saved search item
    if bool(get_arg("delete", False)):
        iwm.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True

    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), {"new": True})  # [New Search]
        for item in iwm.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text, {"q": text})
        xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32007))  # Search
        xbmcplugin.endOfDirectory(plugin.handle)
        return True

    # look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        iwm.append(query)
        if not query:
            return False

    payload = iwm.IWM_SEARCH_PAYLOAD.copy()
    payload["keyword"] = query
    payload["page"] = offset
    payload["filter"] = 'Content_Date_Period,"{}",colourSorter,"{}",soundSorter,"{}",mediaType,"Video"'.format(period, colour, sound)

    title = period if period else query
    data = iwm.post_json(payload)
    xbmcplugin.setPluginCategory(plugin.handle, "{} '{}'".format(ku.localize(32007), title))  # Search 'query'
    parse_search_results(query, offset, data)


def run():
    # type: () -> None
    plugin.run()
