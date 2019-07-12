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
from resources.lib import search as locs

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # Library of Congress

LOC_PERIODS = [
    "1700-1799",
    "1890-1899",
    "1900-1909",
    "1910-1919",
    "1920-1929",
    "1930-1939",
    "1940-1949",
    "1950-1959",
    "1950-1959",
    "1960-1969",
    "1970-1979",
    "1980-1989",
    "1990-1999",
    "2000-2009",
    "2010-2019",
    "2019-2029"  # future proof
]


def parse_search_results(data, category):
    """Adds menu items for search result data"""
    paginate(data["pagination"], category)
    for data in data["results"]:
        add_menu_item(play_film,
                      data.get("title").title(),
                      {"href": "{}?fo=json".format(data.get("url"))},
                      locs.get_art(data),
                      locs.get_info(data),
                      False)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)


def paginate(json, category, idx=None):
    """Adds pagination to results pages"""
    if not json:
        return
    next_page = json.get("next", False)
    current = int(json.get("current", 0))
    if current > 0:
        add_menu_item(index, "[{}]".format(ku.localize(32012)))  # [Menu]
    if next_page:
        offset = current + 1
        add_menu_item(section,
                      "[{} {}]".format(ku.localize(32011), offset),  # [Page n+1]
                      {
                          "idx": idx,
                          "offset": offset,
                          "category": category
                      } if idx else {
                          "href": next_page,
                          "category": category
                      })


def add_menu_item(method, label, args=None, art=None, info=None, directory=True):
    # type: (Callable, Union[str, int], dict, dict, dict, bool) -> None
    """wrapper for xbmcplugin.addDirectoryItem"""
    info = {} if info is None else info
    art = {} if art is None else art
    args = {} if args is None else args
    label = ku.localize(label) if isinstance(label, int) else label
    list_item = ListItem(label)
    list_item.setArt(art)
    if method == search and "q" in args:
        # saved search menu items can be removed via context menu
        list_item.addContextMenuItems([(
            ku.localize(32019),
            "XBMC.RunPlugin({})".format(plugin.url_for(search, delete=True, q=label))
        )])
    if method == play_film:
        list_item.setInfo("video", info)
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
    if ku.get_setting_as_bool("show_contributor"):
        add_menu_item(section,
                      32002,
                      {"idx": "index/contributor/", "category": ku.localize(32002)},
                      ku.icon("contributor.png"))
    if ku.get_setting_as_bool("show_location"):
        add_menu_item(section,
                      32009,
                      {"idx": "index/location/", "category": ku.localize(32009)},
                      ku.icon("location.png"))
    if ku.get_setting_as_bool("show_partof"):
        add_menu_item(section,
                      32021,
                      {"idx": "index/partof/", "category": ku.localize(32021)},
                      ku.icon("series.png"))
    if ku.get_setting_as_bool("show_subject"):
        add_menu_item(section,
                      32004,
                      {"idx": "index/subject/", "category": ku.localize(32004)},
                      ku.icon("genre.png"))
    if ku.get_setting_as_bool("show_years"):
        add_menu_item(year, 32006, art=ku.icon("year.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32005, art=ku.icon("recent.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, {"menu": True}, ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/year")
def year():
    # type: () -> None
    """Show year menu"""
    for item in LOC_PERIODS:
        url = locs.get_search_url(dates=item.replace("-", "/"))
        add_menu_item(section, item, {"href": url, "category": item})
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32006))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/section")
def section():
    # type: () -> None
    """Show section menus and playable items"""
    idx = get_arg("idx", False)
    href = get_arg("href", False)
    category = get_arg("category")
    offset = get_arg("offset", 0)
    if idx:
        # Section menu
        url = locs.get_search_url(idx, page=offset)
        data = locs.get_json(url)
        paginate(data.get("pagination"), category, idx)
        for data in data.get("facets", [{}])[0].get("filters"):
            title = data.get("title").title()
            count = data.get("count")
            add_menu_item(section,
                          "{} [{} items]".format(title, count),
                          {"href": data.get("on"), "category": title})
    if href:
        # Playable items
        data = locs.get_json(href)
        parse_search_results(data, category)
        xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = locs.recents.retrieve()
    for href in data:
        data = locs.get_json(href)
        add_menu_item(
            play_film,
            data.get("item", {}).get("title").title(),
            {"href": href},
            locs.get_art(data),
            locs.get_info(data),
            False)
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
    href = get_arg("href")
    data = locs.get_json(href)
    url = locs.get_video_url(data)
    if not url:
        logger.debug("play_film error: {}".format(href))
        return
    locs.recents.append(href)
    list_item = ListItem(path=url)
    list_item.setInfo("video", locs.get_info(data))
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if idx == "cache" and ku.confirm():
        locs.cache_clear()
    if idx == "recent" and ku.confirm():
        locs.recents.clear()
    if idx == "search" and ku.confirm():
        locs.searches.clear()


@plugin.route("/search")
def search():
    # type: () -> Optional[bool]
    """Search the archive"""
    query = get_arg("q")
    category = get_arg("category", ku.localize(32007))  # Search
    # Remove saved search item
    if bool(get_arg("delete", False)):
        locs.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), {"new": True})  # [New Search]
        for item in locs.searches.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text, {"q": text, "category": "{} '{}'".format(ku.localize(32007), text)})
        xbmcplugin.setPluginCategory(plugin.handle, category)
        xbmcplugin.endOfDirectory(plugin.handle)
        return True
    # New look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        if not query:
            return False
        category = "{} '{}'".format(ku.localize(32007), query)
        if locs.SEARCH_SAVED:
            locs.searches.append(query)
    # Process search
    url = locs.get_search_url(query=query)
    data = locs.get_json(url)
    parse_search_results(data, category)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    # type: () -> None
    """Main entry point"""
    plugin.run()
