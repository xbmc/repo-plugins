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
from resources.lib import search as nfpfs

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # National Film Preservation


def parse_search_results(json, query):
    # type: (dict, str) -> None
    """Parses search results"""
    for video in json.get("videos"):
        for key in video:
            item = video.get(key)
            if not item:
                continue
            elif isinstance(item, list):
                item = " ".join(item)
            elif isinstance(item, int):
                item = str(item)
            if query in item:  # simple text search on each field
                add_menu_item(play_film,
                              video.get("name"),
                              args={"href": video.get("path")},
                              art=ku.art(nfpfs.get_url(video.get("image_path"))),
                              info={
                                  "mediatype": "video",
                                  "plot": nfpfs.text_to_soup(video.get("notes")).find("p").text,
                                  "genre": video.get("archive_names"),
                                  "year": video.get("sort_year")
                              },
                              directory=False)
                break  # only one match per-video


def paginate(category, href, page):
    # type: (str, str, int) -> None
    """Adds pagination to results pages"""
    next_page = page + 1
    add_menu_item(section,
                  "[{} {}]".format(ku.localize(32011), next_page),
                  args={
                      "href": href,
                      "page": next_page,
                      "offset": page * nfpfs.SEARCH_MAX_RESULTS,
                      "category": category
                  })


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
    if method == section or method == play_film:
        list_item.setInfo("video", kwargs.get("info"))
    if method == play_film:
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


def parse_mercury(soup):
    # type: (BeautifulSoup) -> None
    """Parses the mercury theater items (odd mark-up)"""
    for image in soup.select("a > img"):
        action = image.find_previous("a")
        parts = soup.select("a[href={}]".format(action.get("href")))
        add_menu_item(play_film,
                      parts[1].text.strip(),
                      args={"href": action.get("href")},
                      art=ku.art(nfpfs.get_url(image.get("src"))),
                      info={"plot": soup.find("h3").find_next("p").text},
                      directory=False)


@plugin.route("/")
def index():
    # type: () -> None
    """Main menu"""
    add_menu_item(section, "Collections", art=ku.icon("collection.png"))
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
    """Show category menu and category playable items"""
    href = get_arg("href")
    category = get_arg("category", ku.localize(32002))
    page = int(get_arg("page", 1))
    offset = int(get_arg("offset", 0))
    if not href:
        # section menu
        soup = nfpfs.get_html(nfpfs.NFPF_SCREENING_ROOM_URI)
        for item in soup.find_all("table"):
            title = item.find("h5").text
            add_menu_item(section, title,
                          args={"href": item.find("a").get("href"), "category": title},
                          art=ku.art(nfpfs.get_url(item.find("img").get("src"))),
                          info={"plot": item.find("p").text})
    else:
        url = nfpfs.get_url(href)
        soup = nfpfs.get_html(url)
        if url == nfpfs.NFPF_MERCURY_URI:
            # odd playable items
            parse_mercury(soup)
        else:
            results = soup.find_all("figure", "video-thumb")
            items = results[offset:nfpfs.SEARCH_MAX_RESULTS + offset]
            # section paging
            if len(results) > len(items) == nfpfs.SEARCH_MAX_RESULTS:
                paginate(category, href, page)
            for item in items:
                # section playable items
                action = item.find("figcaption").find("a")
                url = nfpfs.get_url(action.get("href"))
                data = nfpfs.get_info(nfpfs.get_html(url))
                data.get("info")["genre"] = item.get("data-archive")
                add_menu_item(play_film,
                              data.get("title"),
                              args={"href": url},
                              art=ku.art(data.get("image")),
                              info=data.get("info"),
                              directory=False)
        xbmcplugin.setContent(plugin.handle, "videos")
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = nfpfs.recents.retrieve()
    for url in data:
        soup = nfpfs.get_html(url)
        info = nfpfs.get_info(soup)
        add_menu_item(play_film,
                      info.get("title"),
                      args={"href": url},
                      art=ku.art(info.get("image")),
                      info=info.get("info"),
                      directory=False)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32005))  # Recent
    xbmcplugin.setContent(plugin.handle, "videos")
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
    url = nfpfs.get_url(href)
    soup = nfpfs.get_html(url)
    data = nfpfs.get_info(soup)
    if not data.get("video"):
        logger.debug("play_film error: {}".format(href))
        return
    if nfpfs.RECENT_SAVED:
        nfpfs.recents.append(url)
    list_item = ListItem(path=data.get("video"))
    list_item.setInfo("video", data.get("info"))
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if idx == "cache" and ku.confirm():
        nfpfs.cache_clear()
    if idx == "recent" and ku.confirm():
        nfpfs.recents.clear()
    if idx == "search" and ku.confirm():
        nfpfs.searches.clear()


@plugin.route("/search")
def search():
    # type: () -> Optional[bool]
    """Search the archive"""
    query = get_arg("q")
    category = get_arg("category", ku.localize(32007))  # Search
    # Remove saved search item
    if bool(get_arg("delete", False)):
        nfpfs.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), args={"new": True})  # [New Search]
        for item in nfpfs.searches.retrieve():
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
        if nfpfs.SEARCH_SAVED:
            nfpfs.searches.append(query)
    # Process search
    parse_search_results(nfpfs.get_json(nfpfs.NFPF_VIDEOS_URI), query)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    # type: () -> None
    """Main entry point"""
    plugin.run()
