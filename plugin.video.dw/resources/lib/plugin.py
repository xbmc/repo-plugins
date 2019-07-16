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
from resources.lib import search as dws

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # Deutsche Welle


def parse_search_results(soup, url, method, category):
    # type: (BeautifulSoup, str, callable, str) -> None
    """Adds menu items for search result data"""
    items = soup.find_all("div", "hov")
    paginate(soup, url, method, category)
    for item in items:
        action = item.find("a")
        img = action.find("img").get("src")
        date, time = dws.get_date_time(action.find("span", "date").text)
        plot = action.find("p")
        add_menu_item(play_film,
                      action.find("h2").contents[0],
                      {"href": dws.get_url(action.get("href"))},
                      ku.art(dws.get_url(img)),
                      {
                          "plot": plot.text if plot else "",
                          "date": date.strip(),
                          "duration": time
                      },
                      False)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)


def paginate(soup, url, method, category):
    # type: (BeautifulSoup, str, callable, str) -> None
    """Adds pagination to results pages"""
    total = int(soup.find("input", {"name": "allResultsAmount"}).extract()["value"])
    hidden = dws.get_hidden(url)
    if total > dws.SEARCH_MAX_RESULTS:
        offset = hidden + dws.SEARCH_MAX_RESULTS
        page = offset // dws.SEARCH_MAX_RESULTS + 1
        add_menu_item(method,
                      "[{} {}]".format(ku.localize(32011), page),
                      {
                          "href": dws.update_hidden(url, offset),
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
    if method in [play_film, programme]:
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
    if ku.get_setting_as_bool("show_live"):
        add_menu_item(live, 32006, art=ku.icon("livetv.png"))
    if ku.get_setting_as_bool("show_programmes"):
        add_menu_item(programme, 32009, art=ku.icon("programme.png"))
    if ku.get_setting_as_bool("show_topics"):
        add_menu_item(topic, 32008, art=ku.icon("topic.png"))
    if ku.get_setting_as_bool("show_past24h"):
        add_menu_item(past24h, 32004, art=ku.icon("past24h.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32005, art=ku.icon("recent.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, {"menu": True}, ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/live")
def live():
    soup = dws.get_html(dws.DW_MEDIA_LIVE_URI)
    items = soup.find_all("div", "mediaItem")
    for item in items:
        title = item.find("input", {"name": "media_title"}).get("value").encode("utf-8")
        preview_image = dws.get_url(item.find("input", {"name": "preview_image"}).get("value"))
        add_menu_item(play_film,
                      item.find("input", {"name": "channel_name"}).get("value"),
                      {
                          "m3u8": item.find("input", {"name": "file_name"}).get("value"),
                          "title": title
                      },
                      ku.art(preview_image),
                      {"plot": title},
                      False)
    xbmcplugin.setContent(plugin.handle, "tvshows")
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32006))  # Live TV
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/programme")
def programme():
    """Shows the programme menu or a programme's playable items"""
    href = get_arg("href")
    category = get_arg("category", ku.localize(32009))  # Programs
    if not href:
        # TV Shows menu
        soup = dws.get_html(dws.DW_PROGRAMME_URI)
        content = soup.find("div", {"id": "bodyContent"}).extract()
        items = content.find_all("div", "epg")
        for item in items:
            img = item.find("img")
            title = item.find("h2").text.encode("utf-8")
            action = item.find("a", string="All videos")
            pid = dws.get_program_id(action.get("href"))
            plot = item.find("p").text.strip()
            add_menu_item(programme,
                          title,
                          {"href": dws.get_search_url(pid=pid), "category": title},
                          ku.art(dws.get_url(img.get("src"))),
                          {"plot": plot if plot else title})
        xbmcplugin.setContent(plugin.handle, "tvshows")
    else:
        # TV Show's playable episodes
        soup = dws.get_html(href)
        parse_search_results(soup, href, programme, category)
        xbmcplugin.setContent(plugin.handle, "episodes")
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/topic")
def topic():
    """Shows the topics menu or a topic's playable items"""
    href = get_arg("href", False)
    category = get_arg("category", ku.localize(32008))  # Themes
    if not href:
        # Topics menu
        soup = dws.get_html(dws.DW_MEDIA_ALL_URL)
        content = soup.find("div", {"id": "themes"}).extract()
        items = content.find_all("a", "check")
        for item in items:
            add_menu_item(topic,
                          item.text,
                          {"href": dws.get_search_url(tid=item.get("value")), "category": item.text})
    else:
        # Topic's playable items
        soup = dws.get_html(href)
        parse_search_results(soup, href, topic, category)
        xbmcplugin.setContent(plugin.handle, "episodes")
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/past24h")
def past24h():
    """Shows playable items from the last 24 hours"""
    url = dws.get_search_url()
    soup = dws.get_html(url)
    parse_search_results(soup, url, past24h, ku.localize(32004))
    xbmcplugin.setContent(plugin.handle, "episodes")
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32004))  # Past 24 hours
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    items = dws.recents.retrieve()
    for url in items:
        data = dws.get_info(url)
        add_menu_item(play_film,
                      data.get("info").get("title"),
                      {"href": url},
                      ku.art(data.get("image")),
                      data.get("info"),
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
    m3u8 = get_arg("m3u8", False)
    href = get_arg("href", False)
    list_item = ListItem()
    if m3u8:
        # live tv stream
        title = get_arg("title")
        list_item.setPath(path=m3u8)
        list_item.setInfo("video", {"plot": title})
    elif href:
        # other playable item
        data = dws.get_info(href)
        if not data["path"]:
            logger.debug("play_film no path: {}".format(href))
            return
        dws.recents.append(href)
        list_item.setPath(path=data["path"])
        list_item.setInfo("video", data["info"])
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if idx == "cache" and ku.confirm():
        dws.cache_clear()
    elif idx == "recent" and ku.confirm():
        dws.recents.clear()
    elif idx == "search" and ku.confirm():
        dws.searches.clear()


@plugin.route("/search")
def search():
    # type: () -> Optional[bool]
    """Search the archive"""
    query = get_arg("q")
    href = get_arg("href", False)
    category = get_arg("category", ku.localize(32007))
    # Remove saved search item
    if bool(get_arg("delete", False)):
        dws.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    elif bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), {"new": True})  # [New Search]
        for item in dws.searches.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text, {"q": text})
        xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32007))  # Search
        xbmcplugin.endOfDirectory(plugin.handle)
        return True
    # New look-up
    elif bool(get_arg("new", False)):
        query = ku.user_input()
        if not query:
            return False
        category = "{} '{}'".format(ku.localize(32007), query)
        if dws.SEARCH_SAVED:
            dws.searches.append(query)
    # Process search
    url = href if href else dws.get_search_url(query=query)
    soup = dws.get_html(url)
    parse_search_results(soup, url, search, category)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    # type: () -> None
    """Main entry point"""
    plugin.run()
