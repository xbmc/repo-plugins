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
from resources.lib import search as pas

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # Prelinger Archives


def parse_search_results(soup, url, total, category):
    # type: (BeautifulSoup, str, int, str) -> None
    """Adds menu items for search result data"""
    items = soup.find_all("div", {"data-mediatype": "movies"})
    count = len(items)
    if count == 0 or total == 0:
        logger.debug("parse_search_results no results: {}".format(url))
        return
    paginate(url, count, total, category)
    for item in items:
        container = item.find("div", "C234").extract()
        action = container.find("a").extract()
        plot = item.find_next("div", "details-ia").find("div", "C234").find("span")
        add_menu_item(play_film,
                      action.find("div", "ttl").text.strip(),
                      args={"href": action.get("href")},
                      art=ku.art(pas.get_url(action.find("img", "item-img")["source"])),
                      info={"plot": plot.text if plot else "", "year": item.get("data-year", 0)},
                      directory=False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)


def paginate(url, count, total, category):
    """Adds pagination to results pages"""
    pages = total // count + (total % count > 0)
    page = pas.get_page_number(url)
    if page < pages and count == pas.SEARCH_MAX_RESULTS:
        offset = page + 1
        add_menu_item(search,
                      "[{} {}]".format(ku.localize(32011), offset),
                      args={"href": pas.update_page_number(url, offset), "category": category, "total": total})


def add_menu_item(method, label, **kwargs):
    # type: (callable, Union[str, int], Any) -> None
    """wrapper for xbmcplugin.addDirectoryItem"""
    args = kwargs.get("args", {})
    label = ku.localize(label) if isinstance(label, int) else label
    list_item = ListItem(label)
    list_item.setArt(kwargs.get("art"))
    if method == search and "q" in args:
        list_item.addContextMenuItems([(
            ku.localize(32019),
            "XBMC.RunPlugin({})".format(plugin.url_for(search, delete=True, q=label))
        )])
    if method == play_film:
        list_item.setInfo("video", kwargs.get("info"))
        list_item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(method, **args),
        list_item,
        kwargs.get("directory", True))


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
    if ku.get_setting_as_bool("show_creator"):
        add_menu_item(section, 32002, args={"idx": "creator", "category": ku.localize(32002)},
                      art=ku.icon("creator.png"))
    if ku.get_setting_as_bool("show_subject"):
        add_menu_item(section, 32004, args={"idx": "subject", "category": ku.localize(32004)},
                      art=ku.icon("subject.png"))
    if ku.get_setting_as_bool("show_collection"):
        add_menu_item(section, 32008, args={"idx": "collection", "category": ku.localize(32008)},
                      art=ku.icon("collection.png"))
    if ku.get_setting_as_bool("show_years"):
        add_menu_item(section, 32006, args={"idx": "year", "category": ku.localize(32006)},
                      art=ku.icon("year.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32005, art=ku.icon("recent.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, args={"menu": True},
                      art=ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/section")
def section():
    # type: () -> None
    """Show section menus and playable items"""
    idx = get_arg("idx")
    category = get_arg("category")
    page = int(get_arg("page", 1))
    offset = int(get_arg("offset", 0))
    url = pas.get_list_url(idx)
    data = pas.get_json(url)
    results = data.get("options")
    # Section paging
    if len(results) > pas.SEARCH_MAX_RESULTS:
        np = page + 1
        logger.warning("FOOOO start:{} end:{}".format(offset, pas.SEARCH_MAX_RESULTS + offset))
        add_menu_item(section, "[{} {}]".format(ku.localize(32011), np),
                      args={"idx": idx, "page": np, "offset": page * pas.SEARCH_MAX_RESULTS, "category": category})
        results = results[offset:pas.SEARCH_MAX_RESULTS + offset]
    # Section menu
    for data in results:
        val = data.get("val")
        title = data.get("txt", str(val)) \
            if isinstance(val, int) \
            else val.title().encode("utf-8")
        total = data.get("n")
        add_menu_item(search,
                      "{} [{} items]".format(title, total),
                      args={"href": pas.get_section_url(idx, val), "category": title, "total": total})
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = pas.recents.retrieve()
    for url in data:
        soup = pas.get_html(url)
        info = pas.get_info(soup)
        add_menu_item(play_film,
                      info.get("title"),
                      args={"href": url},
                      art=ku.art(pas.get_url(info.get("image"))),
                      info=info.get("info"),
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
    url = pas.get_url(href)
    soup = pas.get_html(url)
    data = pas.get_info(soup)
    if not data.get("video"):
        logger.debug("play_film error: {}".format(href))
        return
    if pas.RECENT_SAVED:
        pas.recents.append(url)
    list_item = ListItem(path=data.get("video"))
    list_item.setInfo("video", data.get("info"))
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if idx == "cache" and ku.confirm():
        pas.cache_clear()
    if idx == "recent" and ku.confirm():
        pas.recents.clear()
    if idx == "search" and ku.confirm():
        pas.searches.clear()


@plugin.route("/search")
def search():
    # type: () -> Optional[bool]
    """Search the archive"""
    query = get_arg("q")
    category = get_arg("category", ku.localize(32007))  # Search
    total = get_arg("total")
    # Remove saved search item
    if bool(get_arg("delete", False)):
        pas.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), args={"new": True})  # [New Search]
        for item in pas.searches.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text, args={"q": text, "category": "{} '{}'".format(ku.localize(32007), text)})
        xbmcplugin.setPluginCategory(plugin.handle, category)
        xbmcplugin.endOfDirectory(plugin.handle)
        return True
    # New look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        if not query:
            return False
        category = "{} '{}'".format(ku.localize(32007), query)
        if pas.SEARCH_SAVED:
            pas.searches.append(query)
    # Process search
    url = get_arg("href", pas.get_search_url(query=query))
    soup = pas.get_html(url)
    count = int(total) if total else pas.text_to_int(soup.find("div", "results_count").text)
    parse_search_results(soup, url, count, category)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    # type: () -> None
    """Main entry point"""
    plugin.run()
