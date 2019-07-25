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
from resources.lib import search as ngs

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # National Geographic


def parse_search_results(soup, category, method):
    # type: (BeautifulSoup, str, callable) -> None
    """Adds menu items for search result data"""
    if not soup:  # NB: some show links 404 :(
        return
    paginate(soup.find("a", "load-more"), category, method)
    for item in soup.find_all("div", "media-module"):
        # category/show playable items
        action = item.find("a")
        img = item.find("img")
        title = item.find("div", "title").text.encode("utf-8")
        duration = item.find("div", "timestamp")
        add_menu_item(play_film,
                      title,
                      args={"href": action.get("href")},
                      art=ku.art(img.get("data-lazyload-src", img.get("data-src", img.get("src")))),
                      info={
                          "mediatype": "video",
                          "duration": ngs.time_to_seconds(duration.text) if duration else 0
                      },
                      directory=False)
        xbmcplugin.setContent(plugin.handle, "videos")
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)


def paginate(link, category, method):
    # type: (bs4.element.Tag, str, callable) -> None
    """Adds pagination to results pages"""
    if not link:
        return
    next_page = ngs.get_gp(link.get("href"))
    add_menu_item(method,
                  "[{} {}]".format(ku.localize(32011), next_page + 1),
                  args={"href": link.get("href"), "category": category})


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
    if ku.get_setting_as_bool("show_featured"):
        add_menu_item(featured, 32008, art=ku.icon("featured.png"))
    if ku.get_setting_as_bool("show_collection"):
        add_menu_item(section, 32002, art=ku.icon("collection.png"))
    if ku.get_setting_as_bool("show_shows"):
        add_menu_item(shows, 32003, art=ku.icon("shows.png"))
    if ku.get_setting_as_bool("show_new"):
        add_menu_item(new, 32006, art=ku.icon("new.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32005, art=ku.icon("recent.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, args={"menu": True},
                      art=ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/shows")
def shows():
    page = get_arg("page", 0)
    category = get_arg("category", ku.localize(32003))
    soup = ngs.get_html(ngs.get_show_url(page))
    # Shows paging
    load_more = soup.find("a", "load-more")
    if load_more:
        next_page = ngs.get_gp(load_more.get("href"))
        add_menu_item(shows, "[{} {}]".format(ku.localize(32011), next_page + 1), args={"page": next_page})
    for item in soup.find_all("div", "media-module"):
        # shows menu
        action = item.find("a")
        title = item.find("div", "title").text
        img = action.find("img")
        count = ngs.get_playable_item_count(action.get("href"))
        add_menu_item(section,
                      "{} [{} items]".format(title, count),
                      args={"href": action.get("href"), "category": title},
                      art=ku.art(img.get("src")))
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/new")
def new():
    # type: () -> None
    """Shows new playable items menu"""
    href = get_arg("href", ngs.NG_URI)
    soup = ngs.get_html(ngs.get_url(href))
    parse_search_results(soup.find("div", {"id": "grid-frame"}).extract(), ku.localize(32006), new)
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32006))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/featured")
def featured():
    soup = ngs.get_html(ngs.NG_URI)
    carousel = soup.find("div", {"id", "carousel"})
    parse_search_results(carousel, ku.localize(32008), featured)
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32008))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/section")
def section():
    # type: () -> None
    """Show category menu and category playable items"""
    href = get_arg("href")
    category = get_arg("category", ku.localize(32002))
    if not href:
        # category menu
        soup = ngs.get_html(ngs.NG_URI)
        menu = soup.find("ul", "dropdown-menu").extract()
        for item in menu.find_all("li"):
            action = item.find("a")
            add_menu_item(section, action.text, args={"href": action.get("href"), "category": action.text})
    else:
        # playable items
        soup = ngs.get_html(ngs.get_url(href))
        parse_search_results(soup, category, section)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = ngs.recents.retrieve()
    for url in data:
        soup = ngs.get_html(url)
        info = ngs.get_info(soup)
        add_menu_item(play_film,
                      info.get("title"),
                      args={"href": url},
                      art=ku.art(info.get("image")),
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
    url = ngs.get_url(href)
    soup = ngs.get_html(url)
    data = ngs.get_info(soup)
    if not data.get("video"):
        logger.debug("play_film error: {}".format(href))
        return
    if ngs.RECENT_SAVED:
        ngs.recents.append(url)
    list_item = ListItem(path=data.get("video"))
    list_item.setInfo("video", data.get("info"))
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if idx == "cache" and ku.confirm():
        ngs.cache_clear()
    if idx == "recent" and ku.confirm():
        ngs.recents.clear()
    if idx == "search" and ku.confirm():
        ngs.searches.clear()


@plugin.route("/search")
def search():
    # type: () -> Optional[bool]
    """Search the archive"""
    query = get_arg("q")
    category = get_arg("category", ku.localize(32007))  # Search
    # Remove saved search item
    if bool(get_arg("delete", False)):
        ngs.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), args={"new": True})  # [New Search]
        for item in ngs.searches.retrieve():
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
        if ngs.SEARCH_SAVED:
            ngs.searches.append(query)
    # Process search
    url = get_arg("href", ngs.get_search_url(query=query))
    soup = ngs.get_html(url)
    parse_search_results(soup, category, section)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    # type: () -> None
    """Main entry point"""
    plugin.run()
