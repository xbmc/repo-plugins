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
from resources.lib import search as ntsvs

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # Ngā Taonga Sound & Vision


def parse_search_results(soup, category, method):
    # type: (BeautifulSoup, str, callable) -> None
    """Adds menu items for search result data"""
    paginate(soup.find("div", "pagination"), category, method)
    key = "search-result" if method is not new else "recently-added"
    for item in soup.find_all("div", "gallery-record"):
        action = item.find("a")
        title = item.find(True, "{}-title".format(key))
        add_menu_item(play_film,
                      title.text.strip().title(),
                      args={"href": action.get("href"), "category": category},
                      art=ku.art(ntsvs.get_image_url(item.find_next("div").get("style"))),
                      info={
                          "year": ntsvs.text_to_int(item.find("p", "{}-year".format(key)).text),
                          "plot": item.find("p", "{}-text".format(key)).text
                      },
                      directory=False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)


def paginate(pagination, category, method):
    # type: (bs4.element.Tag, str, callable) -> None
    """Adds pagination to results pages"""
    if pagination is None:
        return
    next_page = pagination.find("a", "next_page")
    if next_page is None:
        return
    current = int(pagination.find("em", "current").text)
    add_menu_item(method,
                  "[{} {}]".format(ku.localize(32011), current + 1),
                  args={"href": ntsvs.get_url(next_page.get("href")), "category": category})


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
    if ku.get_setting_as_bool("show_new"):
        add_menu_item(new, 32006, art=ku.icon("new.png"))
    if ku.get_setting_as_bool("show_genre"):
        add_menu_item(section, 32002, art=ku.icon("genre.png"),
                      args={"category": ku.localize(32002), "key": "genre", "param": "genre"})
    if ku.get_setting_as_bool("show_place"):
        add_menu_item(section, 32003, art=ku.icon("place.png"),
                      args={"category": ku.localize(32003), "key": "place_of_production", "param": "place"})
    if ku.get_setting_as_bool("show_year"):
        add_menu_item(year, 32004, art=ku.icon("year.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32005, art=ku.icon("recent.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, args={"menu": True}, art=ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/new")
def new():
    soup = ntsvs.get_html(ntsvs.NTSV_LANDING_URI)
    boxes = soup.find("div", "film-boxes").extract()
    parse_search_results(boxes, "Recently Added", new)
    xbmcplugin.setPluginCategory(plugin.handle, "Recently Added")
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/year")
def year():
    href = get_arg("href")
    category = get_arg("category", ku.localize(32004))  # Years
    if not href:
        for item in ntsvs.NTSV_PERIODS:
            add_menu_item(year, item,
                          args={"href": ntsvs.get_search_url(year=item.replace("-", "TO")), "category": item})
    else:
        soup = ntsvs.get_html(href)
        parse_search_results(soup, category, year)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/section")
def section():
    # type: () -> None
    """Shows section menus and section playable items"""
    href = get_arg("href")
    category = get_arg("category")
    if not href:
        soup = ntsvs.get_html(ntsvs.get_search_url())
        sidebar = soup.find("div", "sidebar-column").extract()
        for item in sidebar.find_all("input", {"name": get_arg("key")}):
            value = item.get("value")
            title = value.title()
            count = ntsvs.text_to_int(item.find_next("span", "facet-count").text)
            label = "{} [{} {}]".format(title, count, ku.localize(32009))  # title [n items]
            add_menu_item(section, label,
                          args={"href": ntsvs.get_search_url(**{get_arg("param"): value}), "category": title})
    else:
        soup = ntsvs.get_html(ntsvs.get_url(href))
        logger.warning(ntsvs.get_url(href))
        parse_search_results(soup, category, section)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = ntsvs.recents.retrieve()
    for url in data:
        soup = ntsvs.get_html(url)
        info = ntsvs.get_info(soup)
        add_menu_item(play_film,
                      info.get("title"),
                      args={"href": url},
                      art=ku.art(info.get("image")),
                      info=info.get("info"),
                      directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32005))  # Recently Viewed
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
    url = ntsvs.get_url(href)
    soup = ntsvs.get_html(url)
    data = ntsvs.get_info(soup)
    if not data.get("video"):
        logger.debug("play_film error: {}".format(href))
        return
    if ntsvs.RECENT_SAVED:
        ntsvs.recents.append(url)
    list_item = ListItem(path=data.get("video"))
    list_item.setInfo("video", data.get("info"))
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if idx == "cache" and ku.confirm():
        ntsvs.cache_clear()
    if idx == "recent" and ku.confirm():
        ntsvs.recents.clear()
    if idx == "search" and ku.confirm():
        ntsvs.searches.clear()


@plugin.route("/search")
def search():
    # type: () -> Optional[bool]
    """Search the archive"""
    query = get_arg("q")
    category = get_arg("category", ku.localize(32007))  # Search
    # Remove saved search item
    if bool(get_arg("delete", False)):
        ntsvs.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), args={"new": True})  # [New Search]
        for item in ntsvs.searches.retrieve():
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
        category = "{} '{}'".format(ku.localize(32007), query)  # Search 'query'
        if ntsvs.SEARCH_SAVED:
            ntsvs.searches.append(query)
    # Process search
    url = get_arg("href", ntsvs.get_search_url(query=query))
    soup = ntsvs.get_html(url)
    parse_search_results(soup, category, search)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    # type: () -> None
    """Main entry point"""
    plugin.run()
