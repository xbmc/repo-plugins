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
from resources.lib import search as eafa

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo("name")  # East Anglian Film Archive

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()


def paginate(soup, **kwargs):
    # type: (BeautifulSoup, Any) -> None
    """Adds pagination links as required"""
    pagination = soup.find("div", "pagination")
    if not pagination:
        return
    if kwargs.get("query", False):
        # search results
        if kwargs.get("count", 0) == eafa.SEARCH_MAX_RESULTS:
            offset = int(kwargs.get("offset", 0)) + 1
            add_menu_item(search,
                          "[{} {}]".format(ku.localize(32011), offset),
                          args={"q": kwargs.get("query"), "page": offset})
        return
    current = int(pagination.find("span", "current").text)
    next_page = pagination.find("img", {"src": "images/page-next.gif"})
    if next_page:
        # theme results
        form = eafa.get_form_data(soup)
        callback_id = eafa.get_callback_id(next_page.parent.get("href"))
        add_menu_item(themes, "[{} {}]".format(ku.localize(32011), current + 1),
                      args={
                          "target": callback_id,
                          "state": form.get("state"),
                          "validation": form.get("validation"),
                          "action": form.get("action"),
                          "category": kwargs.get("category")
                      })


def parse_search_results(soup, **kwargs):
    # type: (BeautifulSoup, Any) -> None
    """Parse playable items from results and add pagination"""
    items = soup.find_all("div", "result_item")
    if not items:
        logger.debug("parse_search_results no items")
        return
    paginate(soup, count=len(items), **kwargs)
    for item in items:
        catalogue_number = eafa.text_to_int(item.find("div", "title_right").text)
        if not catalogue_number:
            logger.debug("parse_search_results error no catalogue_number: {}".format(item))
            continue
        url = eafa.get_catalogue_url(catalogue_number)
        meta = eafa.get_info(eafa.get_html(url))
        if not meta:
            logger.debug("parse_search_results error no meta: {}".format(url))
            continue
        add_menu_item(play_film, meta.get("title"),
                      args={"href": url},
                      art=ku.art(meta.get("image")),
                      info=meta.get("info"),
                      directory=False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)


def parse_links(soup, form):
    # type: (BeautifulSoup, dict) -> None
    """Parse links from results and add prepare query"""
    links = soup.select("a[href*=javascript:__doPostBack]")
    if not links:
        logger.debug("parse_links no links")
        return
    for link in links:
        title = link.text.strip().title()
        add_menu_item(themes, title,
                      args={
                          "target": eafa.get_callback_id(link.get("href")),
                          "state": form.get("state"),
                          "validation": form.get("validation"),
                          "action": form.get("action"),
                          "category": title
                      })


def add_remove_context_menu(list_item, label, method, **kwargs):
    # type: (ListItem, str, callable, Any) -> None
    list_item.addContextMenuItems([(
        "{} {}".format(ku.localize(32019), label),
        "XBMC.RunPlugin({})".format(plugin.url_for(method, delete=True, **kwargs))
    )])


def add_menu_item(method, label, **kwargs):
    # type: (callable, Union[str, int], Any) -> None
    """wrapper for xbmcplugin.addDirectoryItem"""
    args = kwargs.get("args", {})
    label = ku.localize(label) if isinstance(label, int) else label
    list_item = ListItem(label)
    list_item.setArt(kwargs.get("art"))
    if method == search and args.get("saved"):
        add_remove_context_menu(list_item, label, search, q=label)
    if method == play_film:
        list_item.setInfo("video", kwargs.get("info"))
        list_item.setProperty("IsPlayable", "true")
        if args.get("recent"):
            add_remove_context_menu(list_item, label, recent, url=args.get("url"))
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
    if ku.get_setting_as_bool("show_highlights"):
        add_menu_item(highlights, 32006,
                      art=ku.icon("highlights.png"))
    if ku.get_setting_as_bool("show_genres"):
        add_menu_item(browse, 32005,
                      args={"id": "genre_items", "title": ku.localize(32005)},
                      art=ku.icon("genres.png"))
    if ku.get_setting_as_bool("show_subjects"):
        add_menu_item(browse, 32003,
                      args={"id": "subject_items", "title": ku.localize(32003)},
                      art=ku.icon("subjects.png"))
    if ku.get_setting_as_bool("show_people"):
        add_menu_item(browse, 32004,
                      args={"id": "people_items", "title": ku.localize(32004)},
                      art=ku.icon("people.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32023,
                      art=ku.icon("recent.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007,
                      args={"menu": True},
                      art=ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010,
                      art=ku.icon("settings.png"),
                      directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: ()-> None
    """Recently viewed items menu"""
    # remove recently viewed item
    if bool(get_arg("delete", False)):
        eafa.recents.remove(get_arg("url"))
        xbmc.executebuiltin("Container.Refresh()")
        return
    for url in eafa.recents.retrieve():
        soup = eafa.get_html(url)
        meta = eafa.get_info(soup)
        add_menu_item(play_film, meta.get("title"),
                      args={"recent": True, "url": url},
                      info=meta.get("info"),
                      art=ku.art(meta.get("image")),
                      directory=False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32023))  # Recently Viewed
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/play")
def play_film():
    # type: () -> None
    href = get_arg("href")
    if not href:
        logger.debug("play_film error no href")
        return
    url = eafa.get_url(href)
    soup = eafa.get_html(url)
    meta = eafa.get_info(soup)
    if not meta.get("video"):
        logger.debug("play_film error no video: {}".format(url))
        return
    if ku.get_setting_as_bool("recent_saved"):
        eafa.recents.append(url)
    list_item = ListItem(path=meta.get("video"))
    list_item.setInfo("video", meta.get("info"))
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/browse")
def browse():
    # type: () -> None
    """Shows browse menu items for genre, subject, people, etc"""
    data = eafa.get_html(eafa.EAFA_BROWSE_URI)
    form = eafa.get_form_data(data)
    if not form:
        logger.debug("browse error no form: {}".format(eafa.EAFA_BROWSE_URI))
        return
    parse_links(data.find("div", {"id": get_arg("id")}), form)
    xbmcplugin.setPluginCategory(plugin.handle, get_arg("title"))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/themes")
def themes():
    # type: () -> None
    """Shows themes playable items"""
    url = eafa.get_url(get_arg("action"))
    soup = eafa.post_html(url, {
        "ctl00$ContentPlaceHolder1$ucBrowse$cbVideo": "on",
        "__EVENTTARGET": get_arg("target"),
        "__EVENTVALIDATION": get_arg("validation"),
        "__VIEWSTATE": get_arg("state")
    })
    parse_search_results(soup, category=get_arg("category"))
    xbmcplugin.setPluginCategory(plugin.handle, get_arg("category"))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/highlights")
def highlights():
    # type: () -> None
    """Shows the highlights menu, sub-menus and playable items"""
    href = get_arg("href", False)
    category = get_arg("category", ku.localize(32006))  # Highlights
    if not href:
        # Highlights menu
        url = eafa.get_url("highlights.aspx")
        soup = eafa.get_html(url)
        for item in soup.find_all("div", "hl_box"):
            action = item.find("a")
            img = action.find("img")
            title = img["alt"]
            add_menu_item(highlights, title,
                          args={"href": action.get("href"), "category": title},
                          art=ku.art(eafa.get_url(img["src"])))
    else:
        url = eafa.get_url(href)
        soup = eafa.get_html(url)
        form = eafa.get_form_data(soup)
        if form:
            # sub-menu
            parse_links(soup, form)
        else:
            # playable items
            parse_search_results(soup, category=category)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/search")
def search():
    # type: () -> None
    """Shows saved searches menu and handles new searches"""
    query = get_arg("q")
    page = int(get_arg("page", 1))
    category = get_arg("category")
    # remove saved search item
    if get_arg("delete"):
        eafa.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return
    # View saved search menu
    if get_arg("menu"):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), args={"new": True})  # [New Search]
        for item in eafa.searches.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text,
                          args={
                              "q": text,
                              "category": "{} '{}'".format(ku.localize(32007), text),
                              "saved": True
                          })
        xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32007))  # Search
        xbmcplugin.endOfDirectory(plugin.handle)
        return
    # look-up
    if get_arg("new"):
        query = ku.user_input()
        if not query:
            return
        if ku.get_setting_as_bool("search_saved"):
            eafa.searches.append(query)
        category = "{} '{}'".format(ku.localize(32007), query)
    form = eafa.get_form_data(eafa.get_html(eafa.EAFA_SEARCH_URI))
    soup = eafa.do_search(form, page, query)
    parse_search_results(soup, offset=page, query=query, category=category)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cache, search or recently played"""
    if idx == "cache" and ku.confirm():
        eafa.cache_clear()
    elif idx == "recent" and ku.confirm():
        eafa.recents.clear()
    elif idx == "search" and ku.confirm():
        eafa.searches.clear()


@plugin.route("/settings")
def settings():
    # type: () -> None
    """Shows the plugin settings"""
    ku.show_settings()
    xbmc.executebuiltin("Container.Refresh()")


def run():
    # type: () -> None
    """Main entry point"""
    plugin.run()
