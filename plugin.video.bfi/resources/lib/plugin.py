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
from resources.lib import search as bfis

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo("name")  # BFI Player

PLAYER_ID_ATTR = "data-video-id"
JIG = {
    "category": {
        "card": ["div", "card--free"],
        "plot": ["div", "card__description"],
        "meta": ["span", "card__info__item"]
    },
    "collection": {
        "card": ["div", "collection-card--free"],
        "plot": ["div", "collection-card__description"]
    },
    "subscription": {
        "card": ["div", "card--subscription"],
        "plot": ["div", "card__description"],
        "meta": ["span", "card__info__item"]
    }
}


def add_menu_item(method, label, **kwargs):
    # type: (callable, Union[str, int], Any) -> None
    """wrapper for xbmcplugin.addDirectoryItem"""
    args = kwargs.get("args", {})
    label = ku.localize(label) if isinstance(label, int) else label
    list_item = ListItem(label)
    list_item.setArt(kwargs.get("art"))
    list_item.setInfo("video", kwargs.get("info"))
    if method == search and "q" in args:
        list_item.addContextMenuItems([(
            ku.localize(32019),
            "XBMC.RunPlugin({})".format(plugin.url_for(search, delete=True, q=label))
        )])
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


def paginate(query, count, total, offset):
    # type: (str, int, int, int) -> None
    """Adds search partition menu items"""
    if count < total and count == bfis.SEARCH_MAX_RESULTS:
        offset += 1
        next_page = "[{} {}]".format(ku.localize(32011), offset + 1)  # [Page n+1]
        first_page = "[{} 1]".format(ku.localize(32011))  # [Page 1]
        main_menu = "[{}]".format(ku.localize(32012))  # [Menu]
        if offset > 1:
            add_menu_item(search, first_page, args={"q": query, "offset": 0})
        add_menu_item(search, next_page, args={"q": query, "offset": offset})
        add_menu_item(index, main_menu)


def parse_search_results(data, query, offset):
    # type: (dict, str, int) -> None
    """Adds menu items for search result data"""
    if not data:
        return
    hits = data.get("hits")
    if not hits:
        return
    results = hits.get("hits", [])
    paginate(query, len(results), int(hits.get("total", 0)), offset)
    for element in results:
        data = element.get("_source", False)
        if not data:
            continue
        title = data.get("title", "")
        duration = data.get("duration")
        info = {
            "originaltitle": data.get("original_title", ""),
            "plot": bfis.html_to_text(data.get("standfirst", "")),
            "genre": data.get("genre", ""),
            "cast": data.get("cast", ""),
            "director": data.get("director", ""),
            "year": int(data.get("release_date", 0)),
            "duration": int(duration) * 60 if duration else 0,
            "mediatype": "video"
        }
        add_menu_item(play_film,
                      title,
                      args={"href": data.get("url")},
                      art=ku.art("", data.get("image", ["Default.png"])[0]),
                      info=info,
                      directory=False)


@plugin.route("/clear/<idx>")
def clear(idx):
    # type: (str) -> None
    """Clear cache, searches or recently played items"""
    if idx == "cache" and ku.confirm():
        bfis.cache_clear()
    if idx == "recent" and ku.confirm():
        bfis.recents.clear()
    if idx == "search" and ku.confirm():
        bfis.searches.clear()


@plugin.route("/")
def index():
    # type: () -> None
    """Main menu"""
    if ku.get_setting_as_bool("show_home"):
        add_menu_item(show_category, 32009,
                      args={"href": "free", "title": ku.localize(32009)},
                      art=ku.icon("home.png"))
    if ku.get_setting_as_bool("show_new"):
        add_menu_item(show_category, 32004,
                      args={"href": "free/new", "title": ku.localize(32004)},
                      art=ku.icon("new.png"))
    if ku.get_setting_as_bool("show_popular"):
        add_menu_item(show_category, 32005,
                      args={"href": "free/popular", "title": ku.localize(32005)},
                      art=ku.icon("popular.png"))
    if ku.get_setting_as_bool("show_collections"):
        add_menu_item(show_category, 32006,
                      args={
                          "key": "collection",
                          "href": "free/collections",
                          "title": ku.localize(32006),
                          "sub_directory": True
                      },
                      art=ku.icon("collection.png"))
    if ku.get_setting_as_bool("show_kermode"):
        add_menu_item(show_category, 32026,
                      args={
                          "href": "subscription/kermode-introduces",
                          "title": ku.localize(32026),
                          "key": "subscription",
                          "target": "play-kermode-introduces"
                      },
                      art=ku.icon("kermode.png"))
    if ku.get_setting_as_bool("show_the_cut"):
        add_menu_item(the_cut, "The Cut", art=ku.icon("the-cut.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, args={"menu": True}, art=ku.icon("search.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32021, art=ku.icon("saved.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/settings")
def settings():
    # type: () -> None
    """Plugin setting config"""
    ku.show_settings()
    xbmc.executebuiltin("Container.Refresh()")


@plugin.route("/recent")
def recent():
    # type: () -> None
    """Show recently viewed films"""
    data = bfis.recents.retrieve()
    for url, video_id in data:
        soup = bfis.get_html(url)
        title = soup.find("h1").text.strip()
        description = soup.find("meta", {"name": "description"}).get("content").encode("utf-8")
        image = soup.find("meta", {"property": "og:image"}).get("content")
        add_menu_item(play_film,
                      title,
                      args={"href": url, "video_id": video_id},
                      info={"plot": description, "mediatype": "video"},
                      art=ku.art("", image),
                      directory=False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32021))  # Recently Viewed
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/the_cut')
def the_cut():
    # type: () -> None
    """Shows the-cut menu and sub-menu items"""
    href = get_arg("href")
    category = get_arg("title", "The Cut")
    if not href:
        # The Cut menu
        soup = bfis.get_html(bfis.THE_CUT_URI)
        for card in soup.find_all("div", "c_card"):
            action = card.find(["a", "card__action"]).extract()
            if action is None:
                continue
            title_tag = card.find("h3", "c_card__title")
            plot_tag = card.find("div", "c_card__footer__summary")
            title = title_tag.text if title_tag else action["aria-label"]
            add_menu_item(the_cut,
                          title,
                          args={"href": action["href"], "title": title},
                          info={"plot": plot_tag.text},
                          art=ku.art(bfis.BFI_URI, card.find("img").attrs))
    else:
        # The Cut playable items
        soup = bfis.get_html(bfis.get_page_url(href))
        items = soup.find_all("div", "player")
        for item in items:
            plot = soup.find("div", "text__visible").find("p") \
                if item is items[0] \
                else item.find_next("div", "m_card__description")
            add_menu_item(play_film,
                          item.get("data-label"),
                          args={"video_id": item.get(PLAYER_ID_ATTR), "href": href},
                          info={"mediatype": "video", "plot": plot.text.encode("utf-8") if plot else ""},
                          art=ku.art(bfis.BFI_URI, item.find_next("img").attrs),
                          directory=False)
        xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/category")
def show_category():
    # type: () -> None
    """Shows the category menu (based on supplied key)"""
    key = get_arg("key", "category")
    href = get_arg("href", "free")
    target = get_arg("target")
    sub_directory = bool(get_arg("sub_directory", False))
    category = get_arg("title", ku.localize(32008))
    soup = bfis.get_html(bfis.get_page_url(href))
    for card in soup.find_all(*JIG[key]["card"]):
        action = card.find(["a", "card__action"])
        if action is None:
            continue
        plot_tag = card.find(*JIG[key]["plot"])
        title = action["aria-label"].encode("utf-8")
        info = {"plot": plot_tag.text if plot_tag else "", "genre": []}
        if "meta" in JIG[key]:
            bfis.parse_meta_info(card.find_all(*JIG[key]["meta"]), info)
        if target == "play-kermode-introduces":
            del info["duration"]
        add_menu_item(show_category if sub_directory else play_film,
                      title,
                      args={"href": action["href"], "title": title, "target": target},
                      art=ku.art(bfis.BFI_URI, card.find("img").attrs),
                      info=info,
                      directory=sub_directory)
    xbmcplugin.setPluginCategory(plugin.handle, category)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/film")
def play_film():
    # type: () -> None
    """Attempts to find the m3u8 file for a give href and play it"""
    url = bfis.get_page_url(get_arg("href"))
    video_id = get_arg("video_id")
    target = get_arg("target")
    soup = bfis.get_html(url)
    if not video_id:
        video_id = soup.find(id=target).get(PLAYER_ID_ATTR) \
            if target \
            else soup.find(True, attrs={PLAYER_ID_ATTR: True})[PLAYER_ID_ATTR]
    if video_id:
        if bfis.RECENT_SAVED:
            bfis.recents.append((url, video_id))
        m3u8 = bfis.get_m3u8_url(video_id)
        xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(path=m3u8))


@plugin.route('/search')
def search():
    # type: () -> Optional[bool]
    """Search the archive"""
    query = get_arg("q")
    offset = int(get_arg("offset", 0))
    # remove saved search item
    if bool(get_arg("delete", False)):
        bfis.searches.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True
    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), args={"new": True})  # [New Search]
        for item in bfis.searches.retrieve():
            add_menu_item(search, item, args={"q": item})
        xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32007))  # Search
        xbmcplugin.endOfDirectory(plugin.handle)
        return True
    # look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        if not query:
            return False
        if bfis.SEARCH_SAVED:
            bfis.searches.append(query)
    # process results
    search_url = bfis.get_search_url(query, offset)
    data = bfis.get_json(search_url)
    parse_search_results(data, query, offset)
    xbmcplugin.setPluginCategory(plugin.handle, "{} '{}'".format(ku.localize(32007), bfis.query_decode(query)))
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    plugin.run()
