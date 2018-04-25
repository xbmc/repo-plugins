# -*- coding: utf-8 -*-
"""Main plugin file - Handles the various routes"""

__author__ = "fraser"

import routing
import xbmc
import xbmcaddon as xa
import xbmcplugin as xp
from xbmcgui import ListItem

from resources.lib import kodiutils as ku
from resources.lib import search as bcfs

plugin = routing.Plugin()
ADDON = xa.Addon()
ADDON_ID = ADDON.getAddonInfo("id")  # plugin.video.bcf
ADDON_NAME = ADDON.getAddonInfo("name")  # British Council Film
MEDIA_URI = "special://home/addons/{}/resources/media/".format(ADDON_ID)

BCF_THEMES = [
    "Any",
    ku.get_string(32030),  # Architecture
    ku.get_string(32031),  # Arts
    ku.get_string(32032),  # Agriculture
    ku.get_string(32033),  # Biology
    ku.get_string(32034),  # Education
    ku.get_string(32035),  # Industry and Commerce
    ku.get_string(32036),  # London
    ku.get_string(32037),  # Maritime
    ku.get_string(32038),  # Military
    ku.get_string(32039),  # Public Services
    ku.get_string(32040),  # Public Utilities
    ku.get_string(32041),  # Second World War
    ku.get_string(32042),  # Science and Technology
    ku.get_string(32043),  # Scotland
    ku.get_string(32044),  # Sport
    ku.get_string(32045),  # Town and Country
    ku.get_string(32046),  # Leisure
    ku.get_string(32047),  # Landscapes and Scenery
    ]

BCF_SERIES = [
    "Any",
    ku.get_string(32050),  # Scenes from Shakespeare
    ku.get_string(32051),  # Junior Biology
    ku.get_string(32052),  # Senior Biology
    ku.get_string(32053),  # Human Geography
    ku.get_string(32054),  # Technical Geography
    # TODO: "British News" links don't work - contact BCF
    ku.get_string(32055),  # British News 
    ]

# no 1949?
BCF_YEARS = [
    1940,
    1941,
    1942,
    1943,
    1944,
    1945,
    1946,
    1947,
    1948,
    1950]


def parse_results(data):
    # type (BeautifulSoup) -> None
    """Adds menu items for result data"""
    directory = data.find("div", {"id": "directory-list"})
    if directory is None:
        return
    list = directory.find("ul")
    if list is None:
        return
    for child in list.find_all("li"):
        image = child.find("img")
        action = child.find("a")
        if image is None or action is None:
            continue
        info = {
            "genre": child.find("div", "col-4").text.split(","),
            "year": bcfs.text_to_int(child.find("div", "col-3").text),
            "director": child.find("div", "col-2").text
        }
        add_menu_item(
            play_film,
            child.find("div", "col-1").text,
            args={"href": action["href"]},
            info=info,
            art=ku.art(bcfs.get_page_url(image["src"])),
            directory=False)
    xp.setContent(plugin.handle, "videos")
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_LABEL_IGNORE_THE)
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_GENRE)
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_VIDEO_YEAR)
    xp.endOfDirectory(plugin.handle)


def add_menu_item(method, label, args=None, art=None, info=None, directory=True):
    # type (Callable, str, dict, dict, dict, bool) -> None
    """wrapper for xbmcplugin.addDirectoryItem"""
    info = {} if info is None else info
    art = {} if art is None else art
    args = {} if args is None else args
    label = ku.get_string(label) if isinstance(label, int) else label
    list_item = ListItem(label)
    list_item.setArt(art)
    list_item.setInfo("video", info)
    if method == search and "q" in args:
        # saved search menu items can be removed via context menu
        list_item.addContextMenuItems([(
            ku.get_string(32019),
            "XBMC.RunPlugin({})".format(plugin.url_for(search, delete=True, q=label))
        )])
    if not directory and method == play_film:
        list_item.setProperty("IsPlayable", "true")
    xp.addDirectoryItem(
        plugin.handle,
        plugin.url_for(method, **args),
        list_item,
        directory)


def get_arg(key, default=None):
    # (str, Any) -> Any
    """Get the argument value or default"""
    if default is None:
        default = ""
    return plugin.args.get(key, [default])[0]


@plugin.route("/")
def index():
    """Main menu"""
    if ku.get_setting_as_bool("show_themes"):
        add_menu_item(theme, 32004, {"token": 0}, ku.icon("themes.png"))
    if ku.get_setting_as_bool("show_years"):
        add_menu_item(year, 32005, {"token": 0}, ku.icon("year.png"))
    if ku.get_setting_as_bool("show_series"):
        add_menu_item(series, 32006, {"token": 0}, ku.icon("collection.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, {"menu": True}, ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xp.setPluginCategory(plugin.handle, ADDON_NAME)
    xp.endOfDirectory(plugin.handle)


@plugin.route("/settings")
def settings():
    ku.show_settings()
    xbmc.executebuiltin("Container.Refresh()")


@plugin.route("/play")
def play_film():
    uri = bcfs.get_page_url(get_arg("href"))
    data = bcfs.get_html(uri)
    if data is None:
        return False
    link = data.select_one("a[href*={}]".format(bcfs.PLAYER_URI))
    if link is None:
        return False
    list_item = ListItem(path=link["href"])
    dl_data = data.find("dl", "details")
    plot = data.find("p", "standfirst").text
    year = dl_data.find("dt", string="Release year").find_next_sibling("dd").text.strip()
    list_item.setInfo("video", {
        "plot": plot,
        "year": year
    })
    xp.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<token>")
def clear(token):
    if token == "cache" and ku.confirm():
        bcfs.cache_clear()


@plugin.route("/search")
def search():
    query = get_arg("q")
    offset = int(get_arg("offset", 0))
    # remove saved search item
    if bool(get_arg("delete", False)):
        bcfs.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True

    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.get_string(32016)), {"new": True})  # [New Search]
        for item in bcfs.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text, {"q": text})
        xp.setPluginCategory(plugin.handle, ku.get_string(32007))  # Search
        xp.endOfDirectory(plugin.handle)
        return True

    # look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        bcfs.append(query)
        if not query:
            return False

    search_url = bcfs.get_search_url(query=query)
    data = bcfs.get_html(search_url)
    xp.setPluginCategory(plugin.handle, "{} '{}'".format(ku.get_string(32007), bcfs.query_decode(query)))
    parse_results(data)


@plugin.route("/theme/<token>")
def theme(token):
    if token == "0":
        for idx, name in enumerate(BCF_THEMES):
            if idx == 0:
                continue
            add_menu_item(theme, name, {"token": idx})
        xp.setPluginCategory(plugin.handle, ku.get_string(32004))
        xp.endOfDirectory(plugin.handle)
        return
    uri = bcfs.get_search_url(genre=token)
    data = bcfs.get_html(uri)
    xp.setPluginCategory(plugin.handle, BCF_THEMES[int(token)])
    parse_results(data)


@plugin.route("/series/<token>")
def series(token):
    if token == "0":
        for idx, name in enumerate(BCF_SERIES):
            if idx == 0:
                continue
            add_menu_item(series, name, {"token": idx})
        xp.setPluginCategory(plugin.handle, ku.get_string(32006))
        xp.endOfDirectory(plugin.handle)
        return
    uri = bcfs.get_search_url(series=token)
    data = bcfs.get_html(uri)
    xp.setPluginCategory(plugin.handle, BCF_SERIES[int(token)])
    parse_results(data)


@plugin.route("/year/<token>")
def year(token):
    if token == "0":
        for item in BCF_YEARS:
            add_menu_item(year, str(item), {"token": item})
        xp.setPluginCategory(plugin.handle, ku.get_string(32005))
        xp.endOfDirectory(plugin.handle)
        return
    uri = bcfs.get_search_url(year=token)
    data = bcfs.get_html(uri)
    xp.setPluginCategory(plugin.handle, token)
    parse_results(data)


def run():
    plugin.run()
