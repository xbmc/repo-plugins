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
from resources.lib import search as bps

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()
ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # British Pathé

BP_PERIODS = [
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
    "2000-2009"
]


def parse_search_results(soup):
    # type: (BeautifulSoup) -> None
    """Adds menu items for search result data"""
    items = soup.find_all("dl", "thumb-item")
    for item in items:
        action = item.find("a")
        if not action:
            continue
        details = bps.get_info(action["href"])
        add_menu_item(play_film,
                      details["title"],
                      args={"href": action["href"]},
                      info=details["info"],
                      art=details["art"],
                      directory=False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)


def paginate(soup, query, period):
    # type: (BeautifulSoup, str, str) -> None
    """Adds pagination to results pages"""
    pager = soup.find("ul", "paging-nav")
    if not pager:
        logger.debug("No pagination for Query:'{}' Period:'{}'".format(query, period))
        return
    selected = pager.findNext("a", "selected")
    if not selected:
        return
    offset = bps.text_to_int(selected.text) + 1
    next_page = pager.find("a", string=">")
    category = period if period and query == "+" else query
    if next_page:
        add_menu_item(
            search,
            "[{} {}]".format(ku.localize(32011), offset),
            args={"q": query, "period": period, "page": offset, "category": category})
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
    if ku.get_setting_as_bool("show_collection"):
        add_menu_item(collection, 32004, art=ku.icon("collection.png"))  # Collections
    if ku.get_setting_as_bool("show_programmes"):
        add_menu_item(programmes, 32021, art=ku.icon("programmes.png"))  # Programmes
    if ku.get_setting_as_bool("show_archive"):
        add_menu_item(archive, 32009, art=ku.icon("new.png"))  # Archive Picks
    if ku.get_setting_as_bool("show_years"):
        add_menu_item(year, 32006, art=ku.icon("year.png"))  # Years
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32005, art=ku.icon("recent.png"))  # Recent
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, {"menu": True}, ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/archive")
def archive():
    # type: () -> None
    """View important anniversaries, contextualising current events or illustrating trending topics"""
    data = bps.get_html(bps.BP_ARCHIVE_URI)
    content = data.find("div", "entry-content")
    if not content:
        logger.debug("Missing menu: {}".format(bps.BP_ARCHIVE_URI))
        return
    images = content.select("a > img")
    # Archive menu
    for img in images:
        action = img.findNext("a")
        if not action:
            continue
        title = action.text.strip()
        date = action.findNextSibling("strong").text.strip()
        add_menu_item(collection,
                      "{} ({})".format(title, date),
                      args={"href": action["href"], "playable": True, "category": title},
                      art=ku.art(img["src"]))
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32009))  # Archive Picks
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/collection")
def collection():
    # type: () -> None
    """Various workspaces by theme, location and the personalities involved."""
    category = get_arg("category", False)
    playable = get_arg("playable", False)
    href = get_arg("href", False)
    data = bps.get_collection_data()
    if not category:
        # Main collections menu
        for item in data:
            add_menu_item(collection, item, args={"category": item.encode("utf-8")})
    if category and not href:
        # Collection category menu
        for item in data[category]:
            add_menu_item(collection,
                          item,
                          args={
                              "href": bps.get_uri(data[category][item][0]),
                              "category": item.encode("utf-8")
                          },
                          art=ku.art(bps.get_uri(data[category][item][1])))
    if href and not playable:
        # Collection category sub-meu
        soup = bps.get_html(href)
        workspaces = soup.find_all("dl", "workspace")
        for item in workspaces:
            action = item.find("a")
            title = action["title"].strip().encode("utf-8")
            add_menu_item(collection,
                          title,
                          args={"href": action["href"], "category": title, "playable": True},
                          art=ku.art(item.find("img")["src"]))
    if href and playable:
        # Collection category sub-menu playable items
        soup = bps.get_html(href)
        parse_search_results(soup)
    xbmcplugin.setPluginCategory(plugin.handle, category if category else ku.localize(32004))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/year")
def year():
    # type: () -> None
    """View archive by periods"""
    period = get_arg("period", False)
    if not period:
        # Years menu
        for item in BP_PERIODS:
            add_menu_item(year, str(item), args={"period": item})
        xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32006))  # Years
    else:
        # Period playable items
        start, end = period.split("-")
        url = bps.get_search_url(start=start, end=end)
        soup = bps.get_html(url)
        paginate(soup, "+", period)
        parse_search_results(soup)
        xbmcplugin.setPluginCategory(plugin.handle, period)  # YYYY-YYYY
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/programmes")
def programmes():
    # type: () -> None
    """View series curated by British Pathé."""
    href = get_arg("href", False)
    category = get_arg("category", ku.localize(32021))  # programming
    if not href:
        # Programmes menu
        soup = bps.get_html(bps.BP_COLLECTIONS_URI)
        for img in soup.select("a > img"):
            if img.parent['href'].startswith('/programmes/'):
                title = img.parent.findNext("a").text
                href = img.parent.findNext("a")["href"]
                add_menu_item(programmes,
                              title,
                              info={"plot": "foobar"},
                              args={"href": href, "category": title},
                              art=ku.art(bps.get_uri(img["src"])))
    else:
        # Programme's playable items
        soup = bps.get_html(bps.get_uri(href))
        table = soup.find("table", {"id": "programmeTable"}).extract()
        for img in table.select("a > img"):
            action = img.parent
            row = action.find_parent("tr")
            add_menu_item(play_film,
                          row.find("span").text,
                          args={"href": action["href"]},
                          info={
                              "plot": "",
                              "year": int(row.find("td", "far-right").text.strip()),
                              "episode": int(row.find("td", "episode-number").text.strip())
                          },
                          art=ku.art(img["src"]),
                          directory=False)
        xbmcplugin.setContent(plugin.handle, "episodes")
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = bps.recents.retrieve()
    for item in data:
        details = bps.get_info(item)
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
    details = bps.get_info(href)
    bps.recents.append(href)
    list_item = ListItem(path=details["m3u8"])
    list_item.setInfo("video", details["info"])
    xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cached or recently played items"""
    if idx == "cache" and ku.confirm():
        bps.cache_clear()
    if idx == "recent" and ku.confirm():
        bps.recents.clear()
    if idx == "search" and ku.confirm():
        bps.searches.clear()


@plugin.route("/search")
def search():
    # type: () -> Optional[bool]
    """Search the archive"""
    query = get_arg("q", "+")
    page = get_arg("page", "1")
    category = get_arg("category", "{} '{}'".format(ku.localize(32007), query))
    period = get_arg("period", "+-+")
    start, end = period.split("-")
    # remove saved search item
    if bool(get_arg("delete", False)):
        bps.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), {"new": True})  # [New Search]
        for item in bps.searches.retrieve():
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
        if bps.SEARCH_SAVED:
            bps.searches.append(query)
        # reset category on new search...
        category = "{} '{}'".format(ku.localize(32007), query)
    url = bps.get_search_url(query, start, end, page)
    soup = bps.get_html(url)
    paginate(soup, query, period)
    parse_search_results(soup)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    # type: () -> None
    """Main entry point"""
    plugin.run()
