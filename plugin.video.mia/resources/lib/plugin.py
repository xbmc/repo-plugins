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
from resources.lib import search as mias

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # Moving Image Archive


def parse_search_results(soup, url, category):
    # type: (BeautifulSoup, str) -> None
    """Adds menu items for search result data"""
    paginate(soup, url, category)
    table = soup.find("table", "search_results")
    if not table:
        logger.debug("No result data: '{}' '{}'".format(category, url))
        return
    data = table.extract()
    rows = data.find_all("tr")
    for row in rows:
        td = row.find("td", "search_results_image")
        if not td:
            continue
        img = td.find("img")["src"]
        action = row.select("h4 > a")[0]
        info = {"plot": row.find_all("p")[1].text}
        add_menu_item(play_film, action.text.title(), {"href": action["href"]}, ku.art(img), info, False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)


def paginate(soup, url, category):
    """Adds pagination to results pages"""
    current = soup.find("a", "page_number_current")
    if not current:
        return
    links = soup.find("p", "page_navigator_links").extract()
    page = int(soup.find("a", "page_number_current").text)
    offset = page + 1
    next_page = links.find("a", {"title": "Display next page of search results"})
    add_menu_item(index, "[{}]".format(ku.localize(32012)))  # [Menu]
    if next_page:
        add_menu_item(search,
                      "[{} {}]".format(ku.localize(32011), offset),
                      args={"offset": offset, "href": url, "category": category})


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
    if ku.get_setting_as_bool("show_featured"):
        add_menu_item(section,
                      32002,
                      {"token": "featuredFilmCollection_facet", "category": ku.localize(32002)},
                      ku.icon("featured.png"))
    if ku.get_setting_as_bool("show_place"):
        add_menu_item(section,
                      32009,
                      {"token": "place_facet", "category": ku.localize(32009)},
                      ku.icon("place.png"))
    if ku.get_setting_as_bool("show_series"):
        add_menu_item(section,
                      32021,
                      {"token": "series_facet", "category": ku.localize(32021)},
                      ku.icon("series.png"))
    if ku.get_setting_as_bool("show_genre"):
        add_menu_item(section,
                      32004,
                      {"token": "genre_facet", "category": ku.localize(32004)},
                      ku.icon("genre.png"))
    if ku.get_setting_as_bool("show_years"):
        add_menu_item(section,
                      32006,
                      {"token": "decade_facet", "category": ku.localize(32006)},
                      ku.icon("year.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32005, art=ku.icon("recent.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, {"menu": True}, ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/section")
def section():
    # type: () -> None
    """Handles the various sections such as years, genre, series, etc"""
    href = get_arg("href", False)
    token = get_arg("token", False)
    category = get_arg("category")
    if not href and token:
        # Section menu
        soup = mias.get_html(mias.get_search_url())
        element = soup.find("ul", {"id": token})
        if not element:
            logger.debug("No menu data: {}".format(token))
            return
        items = element.extract().findAll("li")
        for item in items:
            action = item.find("a")
            if not action:
                continue
            title = action.text.title()
            add_menu_item(section, title, args={"href": action["href"], "category": title})
    else:
        # Section playable items
        url = mias.get_url(href)
        soup = mias.get_html(url)
        parse_search_results(soup, url, category)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = mias.recents.retrieve()
    for item in data:
        details = mias.get_info(item)
        add_menu_item(
            play_film,
            details["title"],
            args={"href": item},
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
    href = get_arg("href")
    url = mias.get_url(href)
    details = mias.get_info(url)
    mias.recents.append(url)
    list_item = ListItem(path=details["m3u8"])
    list_item.setInfo("video", details["info"])
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if idx == "cache" and ku.confirm():
        mias.cache_clear()
    if idx == "recent" and ku.confirm():
        mias.recents.clear()
    if idx == "search" and ku.confirm():
        mias.searches.clear()


@plugin.route("/search")
def search():
    # type: () -> Optional[bool]
    """Search the archive"""
    query = get_arg("q")
    href = get_arg("href", False)
    offset = int(get_arg("offset", 1))
    category = get_arg("category", ku.localize(32007))
    # Remove saved search item
    if bool(get_arg("delete", False)):
        mias.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), {"new": True})  # [New Search]
        for item in mias.searches.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text, {"q": text})
        xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32007))  # Search
        xbmcplugin.endOfDirectory(plugin.handle)
        return True
    # New look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        if not query:
            return False
        category = "{} '{}'".format(ku.localize(32007), query)
        if mias.SEARCH_SAVED:
            mias.searches.append(query)
    # Process search
    url = mias.get_search_url(query) if query else mias.update_offset(href, offset)
    logger.warning(url)
    soup = mias.get_html(url)
    parse_search_results(soup, url, category)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    # type: () -> None
    """Main entry point"""
    plugin.run()
