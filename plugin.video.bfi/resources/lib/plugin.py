# -*- coding: utf-8 -*-
"""Main plugin file - Handles the various routes"""

__author__ = "fraser.chapman@gmail.com"

import routing
import xbmc
import xbmcaddon as xa
import xbmcplugin as xp
from xbmcgui import ListItem

from resources.lib import kodiutils as ku
from resources.lib import search as bfis

plugin = routing.Plugin()
ADDON = xa.Addon()
ADDON_ID = ADDON.getAddonInfo("id")  # plugin.video.bfi
ADDON_NAME = ADDON.getAddonInfo("name")  # BFI Player

PLAYER_ID_ATTR = "data-video-id"
JIG = {
    "category": {
        "card": ["div", "card--free"],
        "title": ["h3", "card__title"],
        "plot": ["div", "card__description"],
        "meta": ["span", "card__info__item"]
    },
    "collection": {
        "card": ["div", "collection-card--free"],
        "title": ["h3", "collection-card__title"],
        "plot": ["div", "collection-card__description"]
    },
    "the-cut": {
        "card": ["div", "c_card"],
        "title": ["h3", "c_card__title"],
        "plot": ["div", "c_card__footer__summary"]
    }
}


def add_menu_item(method, label, args=None, art=None, info=None, directory=True):
    # type (Callable, str, dict, dict, dict, bool) -> None
    """wrapper for xbmcplugin.addDirectoryItem"""
    info = {} if info is None else info
    art = {} if art is None else art
    args = {} if args is None else args
    label = ku.localize(label) if isinstance(label, int) else label
    list_item = ListItem(label)
    list_item.setArt(art)
    list_item.setInfo("video", info)
    if method == search and "q" in args:
        # saved search menu items can be removed via context menu
        list_item.addContextMenuItems([(
            ku.localize(32019),
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


def paginate(query, count, total, offset):
    # type (str, int, int, int) -> None
    """Adds search partition menu items"""
    if count < total and count == bfis.SEARCH_MAX_RESULTS:
        offset += 1
        next_page = "[{} {}]".format(ku.localize(32011), offset + 1)  # [Page n+1]
        first_page = "[{} 1]".format(ku.localize(32011))  # [Page 1]
        main_menu = "[{}]".format(ku.localize(32012))  # [Menu]
        if offset > 1:
            add_menu_item(search, first_page, {"q": query, "offset": 0})
        add_menu_item(search, next_page, {"q": query, "offset": offset})
        add_menu_item(index, main_menu)


@plugin.route("/clear/<target>")
def clear(target):
    if target == "cache" and ku.confirm():
        bfis.cache_clear()
    if target == "recent" and ku.confirm():
        bfis.recent_clear()


@plugin.route("/")
def index():
    """Main menu"""
    if ku.get_setting_as_bool("show_home"):
        add_menu_item(show_category, 32009, {
            "href": "free",
            "title": ku.localize(32009)}, ku.icon("home.png"))
    if ku.get_setting_as_bool("show_new"):
        add_menu_item(show_category, 32004, {
            "href": "free/new",
            "title": ku.localize(32004)}, ku.icon("new.png"))
    if ku.get_setting_as_bool("show_popular"):
        add_menu_item(show_category, 32005, {
            "href": "free/popular",
            "title": ku.localize(32005)}, ku.icon("popular.png"))
    if ku.get_setting_as_bool("show_collections"):
        add_menu_item(show_category, 32006, {
            "key": "collection",
            "href": "free/collections",
            "title": ku.localize(32006),
            "isdir": True
        }, ku.icon("collection.png"))
    if ku.get_setting_as_bool("show_the_cut"):
        add_menu_item(show_category, "The Cut", {
            "key": "the-cut",
            "href": "the-cut",
            "title": "The Cut",
        }, ku.icon("the-cut.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, {"menu": True}, ku.icon("search.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32021, art=ku.icon("saved.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xp.setPluginCategory(plugin.handle, ADDON_NAME)
    xp.endOfDirectory(plugin.handle)


@plugin.route("/settings")
def settings():
    """Plugin setting config"""
    ku.show_settings()
    xbmc.executebuiltin("Container.Refresh()")


@plugin.route("/recent")
def recent():
    """Show recently viewed films"""
    data = bfis.get_recent()
    for item in data:
        parts = item["uri"].split("/")[3:]
        href = "/".join(parts)
        title = parts[2].split("-")
        name = " ".join(title[1:-2]).title()
        add_menu_item(play_film, name, {"href": href}, info={"year": title[-2]}, directory=False)
    xp.endOfDirectory(plugin.handle)


@plugin.route("/film")
def play_film():
    """Attempts to find and load an m3u8 file for a give href"""
    url = bfis.get_page_url(get_arg("href"))
    html = bfis.get_html(url)
    try:
        video_id = html.find(True, attrs={PLAYER_ID_ATTR: True})[PLAYER_ID_ATTR]
    except (AttributeError, TypeError):
        return False
    if video_id is not None:
        video_url = bfis.get_video_url(video_id)
        m3u8_url = bfis.get_m3u8(video_url)
        xp.setResolvedUrl(plugin.handle, True, ListItem(path=m3u8_url))


@plugin.route('/search')
def search():
    query = get_arg("q")
    offset = int(get_arg("offset", 0))
    # remove saved search item
    if bool(get_arg("delete", False)):
        bfis.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True

    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), {"new": True})  # [New Search]
        for item in bfis.retrieve():
            add_menu_item(search, item, {"q": item})
        xp.setPluginCategory(plugin.handle, ku.localize(32007))  # Search
        xp.endOfDirectory(plugin.handle)
        return True

    # look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        bfis.append(query)
        if not query:
            return False

    search_url = bfis.get_search_url(query, offset)
    data = bfis.get_json(search_url)
    if data is None:
        return False

    hits = data.get("hits")
    if not hits:
        return False

    # Results
    results = hits.get("hits", [])
    paginate(query,
             len(results),
             int(hits.get("total", 0)),
             offset)
    for element in results:
        data = element.get("_source", False)
        if not data:
            continue

        title = data.get("title", "")
        duration = data.get("duration", 0)  # can still be NoneType *
        info = {
            "originaltitle": data.get("original_title", ""),
            "plot": bfis.html_to_text(data.get("standfirst", "")),
            "genre": data.get("genre", ""),
            "cast": data.get("cast", ""),
            "director": data.get("director", ""),
            "year": int(data.get("release_date", 0)),
            "duration": 0 if duration is None else int(duration) * 60,  # *
            "mediatype": "video"
        }
        add_menu_item(
            play_film,
            title,
            {"href": data.get("url")},
            ku.art("", data.get("image", ["Default.png"])[0]),
            info,
            False)
    xp.setContent(plugin.handle, "videos")
    xp.setPluginCategory(plugin.handle, "{} '{}'".format(ku.localize(32007), bfis.query_decode(query)))
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_LABEL_IGNORE_THE)
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_GENRE)
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_VIDEO_YEAR)
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_DURATION)
    xp.endOfDirectory(plugin.handle)


@plugin.route("/category")
def show_category():
    key = get_arg("key", "category")
    href = get_arg("href", "free")
    is_dir = bool(get_arg("isdir", False))
    category = get_arg("title", ku.localize(32008))
    url = bfis.get_page_url(href)
    html = bfis.get_html(url)
    for card in html.findAll(*JIG[key]["card"]):
        action = card.find(["a", "card__action"])
        if action is None:
            continue
        title_tag = card.find(*JIG[key]["title"])
        plot_tag = card.find(*JIG[key]["plot"])
        title = title_tag.text.encode("utf-8") if title_tag else action["aria-label"]
        info = {
            "mediatype": "video",
            "plot": bfis.html_to_text(plot_tag.text) if plot_tag else ""
        }
        if "meta" in JIG[key]:
            try:
                genre, year, duration = card.find_all(*JIG[key]["meta"], limit=3)
                info["genre"] = genre.text
                info["year"] = year.text
                info["duration"] = duration.text * 60  # duration is min
            except (ValueError, TypeError):
                pass
        add_menu_item(
            show_category if is_dir else play_film,
            title,
            {"href": action["href"], "title": title},
            ku.art(bfis.BFI_URI, card.find("img").attrs),
            info,
            is_dir
        )
    xp.setPluginCategory(plugin.handle, category)
    xp.setContent(plugin.handle, "videos")
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_LABEL_IGNORE_THE)
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_GENRE)
    xp.endOfDirectory(plugin.handle)


def run():
    plugin.run()
