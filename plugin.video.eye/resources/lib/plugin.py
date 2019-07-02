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
from resources.lib import search as eyes

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # EYE Film

PERIODS = [
    "1896 - 1899",
    "1900 - 1909",
    "1910 - 1919",
    "1920 - 1929",
    "1930 - 1939",
    "1940 - 1949",
    "1950 - 1959",
    "1960 - 1969",
    "1970 - 1979",
    "1980 - 1989",
    "1990 - 1999",
    "2000 - 2009",
    "2010 - 2019"
]


def parse_results(href, category):
    # type: (str, str) -> Union[None, bool]
    html = eyes.get_html(eyes.get_page_url(href))
    paginate(html, category)
    data = html.find_all("li", "packery-item")
    for item in data:
        action = item.find("a")
        details = eyes.get_info(eyes.get_page_url(action["href"]))
        add_menu_item(play_film,
                      details["title"],
                      args={"href": action["href"]},
                      art=details["art"],
                      info=details["info"],
                      directory=False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)


def paginate(html, category):
    pager = html.find("ul", "pager")
    if not pager:
        return
    offset = eyes.text_to_int(pager.find("li", "pager-current").text) + 1
    first_page = pager.find("li", "pager-first")
    next_page = pager.find("li", "pager-next")
    if first_page:
        add_menu_item(collections,
                      "[{} 1]".format(ku.localize(32011)),
                      {"href": first_page.find_next("a")["href"], "category": category})
    if next_page:
        add_menu_item(collections,
                      "[{} {}]".format(ku.localize(32011), offset),
                      {"href": next_page.find_next("a")["href"], "category": category})
    add_menu_item(index, "[{}]".format(ku.localize(32012)))  # [Menu]


def add_menu_item(method, label, args=None, art=None, info=None, directory=True):
    # type: (Callable, Union[str, int], dict, dict, dict, bool) -> None
    """wrapper for xbmcplugin.addDirectoryItem"""
    info = {} if info is None else info
    art = {} if art is None else art
    args = {} if args is None else args
    label = ku.localize(label) if isinstance(label, int) else label
    list_item = ListItem(label)
    list_item.setArt(art)
    list_item.setIsFolder(directory)
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
    default = "" if default is None else ""
    return plugin.args.get(key, [default])[0]


@plugin.route("/")
def index():
    # type: () -> None
    """Main menu"""
    if ku.get_setting_as_bool("show_collections"):
        add_menu_item(collections, 32004, art=ku.icon("collection.png"))  # Collections
    if ku.get_setting_as_bool("show_years"):
        add_menu_item(year, 32006, art=ku.icon("year.png"))  # Years
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32005, art=ku.icon("recent.png"))  # Recent
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, {"menu": True}, ku.icon("search.png"))  # Search
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)  # Settings
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/year")
def year():
    # type: () -> None
    for item in PERIODS:
        href = eyes.EYE_PERIOD_TEMPLATE.format(eyes.date_range(item))
        add_menu_item(collections, str(item), args={"href": href, "category": item})
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32006))  # Years
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/collections")
def collections():
    # type: () -> None
    href = get_arg("href", False)
    category = get_arg("category", ku.localize(32004))
    if not href:
        # Show the list of collections
        html = eyes.get_html(eyes.EYE_COLLECTIONS_URI)
        ul = html.find("ul", {"id": "facetapi-facet-search-apieye-filmgeschiedenis-block-field-coll-sub"})
        data = ul.find_all("li", "leaf")
        for item in data:
            action = item.find("a", "facetapi-inactive")
            title = action.contents[0].encode("utf-8").title()
            add_menu_item(collections, title, args={"href": action["href"], "category": title})
    else:
        parse_results(href, category)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = eyes.recents.retrieve()
    for item in data:
        details = eyes.get_info(item)
        add_menu_item(
            play_film,
            details["title"],
            args={"href": item},
            art=details["art"],
            info=details["info"],
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
    """Play film"""
    uri = eyes.get_page_url(get_arg("href"))
    eyes.recents.append(uri)
    details = eyes.get_info(uri)
    token = eyes.get_stream_token(details["soup"])
    list_item = ListItem(path="plugin://plugin.video.youtube/play/?video_id={}".format(token))
    list_item.setInfo("video", details["info"])
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<token>")
def clear(token):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if token == "cache" and ku.confirm():
        eyes.clear()
    if token == "recent" and ku.confirm():
        eyes.recents.clear()
    if token == "search" and ku.confirm():
        eyes.searches.clear()


@plugin.route("/search")
def search():
    # type: () -> Union[bool, None]
    query = get_arg("q")
    # remove saved search item
    if bool(get_arg("delete", False)):
        eyes.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), {"new": True})  # [New Search]
        for item in eyes.searches.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text, {"q": text})
        xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32007))  # Search
        xbmcplugin.endOfDirectory(plugin.handle)
        return True
    # look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        if not query:
            return False
        if eyes.SEARCH_SAVED:
            eyes.searches.append(query)
    category = "{} '{}'".format(ku.localize(32007), query)  # Search 'query'
    xbmcplugin.setPluginCategory(plugin.handle, category)
    parse_results(eyes.get_search_url(query, 0), category)  # first page is 0
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    # type: () -> None
    plugin.run()
