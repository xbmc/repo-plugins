# -*- coding: utf-8 -*-

"""Main plugin file - Handles the various routes"""

__author__ = "fraser"

import logging

import inputstreamhelper
import routing
import xbmc
import xbmcaddon
import xbmcplugin
from xbmcgui import ListItem

import kodilogging
from resources.lib import kodiutils as ku
from resources.lib import search as jafc

kodilogging.config()
logger = logging.getLogger(__name__)
plugin = routing.Plugin()

ADDON_NAME = xbmcaddon.Addon().getAddonInfo("name")  # Japanese Animated Film Classics
STREAM_ADDON = "inputstream.adaptive"
STREAM_FORMAT = "mpd"
STREAM_MIME_TYPE = "application/dash+xml"


def get_arg(key, default=None):
    # (str, Any) -> Any
    """Get the argument value or default"""
    if default is None:
        default = ""
    return plugin.args.get(key, [default])[0]


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
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(method, **args),
        list_item,
        directory)


def paginate(data, method):
    """Adds pagination links as required"""
    if data is None:
        return
    items = data.find_all("li")
    for item in items:
        if "class" in item.attrs and any(x in item.attrs["class"] for x in ["disabled", "active", "prev", "next"]):
            continue
        action = item.find("a")
        add_menu_item(method, "[{} {}]".format(ku.localize(32011), item.text), {  # [Page n]
            "href": action["href"]
        })
    add_menu_item(index, "[{}]".format(ku.localize(32012)))  # [Menu]


@plugin.route("/")
def index():
    """Main menu"""
    if ku.get_setting_as_bool("show_genres"):
        add_menu_item(themes, 32005, args={
            "href": "en/categories/stories",
            "title": ku.localize(32005)
        }, art=ku.icon("genres.png"))
    if ku.get_setting_as_bool("show_motions"):
        add_menu_item(themes, 32002, args={
            "href": "en/categories/motions",
            "title": ku.localize(32002)
        }, art=ku.icon("techniques.png"))
    if ku.get_setting_as_bool("show_characters"):
        add_menu_item(themes, 32003, args={
            "href": "en/categories/characters",
            "title": ku.localize(32003)
        }, art=ku.icon("characters.png"))
    if ku.get_setting_as_bool("show_authors"):
        add_menu_item(authors, 32004, art=ku.icon("authors.png"))
    if ku.get_setting_as_bool("show_experts"):
        add_menu_item(experts, 32023, art=ku.icon("experts.png"))
    if ku.get_setting_as_bool("show_techniques"):
        add_menu_item(themes, 32006, args={"href": "en/categories/techniques", "title": ku.localize(32006)},
                      art=ku.icon("techniques.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, args={"menu": True}, art=ku.icon("search.png"))
    if ku.get_setting_as_bool("show_recent"):
        add_menu_item(recent, 32026, art=ku.icon("saved.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ADDON_NAME)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/settings")
def settings():
    ku.show_settings()
    xbmc.executebuiltin("Container.Refresh()")


@plugin.route("/play")
def play_film():
    href = get_arg("href", False)
    if not href:
        return
    url = jafc.get_mpd_url(jafc.text_to_int(href))
    is_helper = inputstreamhelper.Helper(STREAM_FORMAT)
    if is_helper.check_inputstream():
        list_item = ListItem(path=url)
        list_item.setProperty("inputstreamaddon", STREAM_ADDON)
        list_item.setProperty("inputstream.adaptive.manifest_type", STREAM_FORMAT)
        list_item.setMimeType(STREAM_MIME_TYPE)
        list_item.setContentLookup(False)
        xbmcplugin.setResolvedUrl(plugin.handle, True, list_item)
    else:
        logger.debug("play_film error: {}".format(url))


@plugin.route("/recent")
def recent():
    """Show recently viewed films"""
    data = jafc.get_recent()
    for item in data:
        token = jafc.pluck(item["uri"], "nfc/", "_en")
        info = jafc.get_info(token)
        if info is None:
            continue
        add_menu_item(
            play_film,
            info["title"],
            args={"href": token},
            info=info,
            art=ku.art(jafc.get_url(jafc.get_image(token))),
            directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32026))  # Recently Viewed
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/clear/<token>")
def clear(token):
    if token == "cache" and ku.confirm():
        jafc.cache_clear()
    if token == "recent" and ku.confirm():
        jafc.recent_clear()


@plugin.route("/search")
def search():
    query = get_arg("q")
    href = get_arg("href", False)

    # remove saved search item
    if bool(get_arg("delete", False)):
        jafc.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True

    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.localize(32016)), {"new": True})  # [New Search]
        for item in jafc.retrieve():
            text = item.encode("utf-8")
            add_menu_item(
                search,
                text,
                args={"q": text})
        xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32007))  # Search
        xbmcplugin.endOfDirectory(plugin.handle)
        return True

    # look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        jafc.append(query)
        if not query:
            return False

    url = jafc.get_url(href) if href else jafc.get_search_url(query)
    data = jafc.get_html(url)
    results = data.find("ul", "work-results")
    if not results:
        return

    paginate(data.find("ul", "pager-menu"), search)
    for item in results.find_all("li", "work-result"):
        action = item.find("a")
        img = item.find("img", "thumbnail")
        add_menu_item(play_film,
                      item.find("h2").text,
                      args={"href": action["href"]},
                      info=jafc.get_info(action["href"]),
                      art=ku.art(jafc.get_url(img["src"])),
                      directory=False)
    xbmcplugin.setPluginCategory(plugin.handle, "{} '{}'".format(ku.localize(32016), query))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/themes")
def themes():
    """List of directory menu items for each theme"""
    url = jafc.get_url(get_arg("href"))
    data = jafc.get_html(url)
    element = data.find("ul", {
        "class": ["category-condition-keyword", "work-favorites-condition-keyword"]
    })
    for item in element.find_all("li"):
        action = item.find("a")
        span = action.find("span")
        if span:
            span.extract()
        add_menu_item(
            films,
            action.text,
            args={"href": action["href"], "title": action.text})
    xbmcplugin.setPluginCategory(plugin.handle, get_arg("title"))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/films")
def films():
    """Playable movie items"""
    url = jafc.get_url(get_arg("href"))
    data = jafc.get_html(url)
    paginate(data.find("ul", "pager-menu"), films)
    container = data.find(True, {"class": ["categories", "characters", "writer-works"]})
    if container is None:
        ku.notification(ku.localize(32008), ku.localize(32009))  # Error - No playable items found
        return
    for item in container.find_all("li"):
        action = item.find("a")
        if action is None:
            continue
        add_menu_item(
            play_film,
            item.find(True, {"class": ["category-title", "character-serif", "writer-work-heading"]}).text,
            args={"href": action["href"]},
            info=jafc.get_info(action["href"]),
            art=ku.art(jafc.get_url(item.find("img", "thumbnail")["src"])),
            directory=False)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.setPluginCategory(plugin.handle, get_arg("title"))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/experts")
def experts():
    """Lists experts, and their choices"""
    href = get_arg("href", False)
    if not href:
        url = jafc.get_url("en/works-favorites.html")
        data = jafc.get_html(url)
        container = data.find("div", "work-favorites")
        for item in container.find_all("div", "work-favorite"):
            author = item.find("strong").text
            add_menu_item(experts,
                          author,
                          args={"href": "en/" + item.find("a")["href"], "title": item.find("strong").text},
                          info={"plot": item.find("div", "work-favorite-summary").text},
                          art=ku.art(jafc.get_url(item.find("img", "thumbnail")["src"])))
            xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32023))  # Experts Choice
    else:
        url = jafc.get_url(href)
        data = jafc.get_html(url)
        for item in data.find_all("div", "favorite-work"):
            action = item.find("h2").find("a")
            add_menu_item(play_film,
                          action.text,
                          args={"href": action["href"]},
                          info={"plot": item.find("dd").text},
                          art=ku.art(jafc.get_url(item.find("img", "thumbnail")["src"])),
                          directory=False)
            xbmcplugin.setPluginCategory(plugin.handle, get_arg("title"))  # Experts name
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/authors")
def authors():
    """List of authors"""
    url = jafc.get_url("en/writer.html")
    data = jafc.get_html(url)
    container = data.find("ul", "writer-results")
    for item in container.find_all("li"):
        action = item.find("a")
        if action is None:
            continue
        add_menu_item(films,
                      action.text,
                      args={"href": "en/{}".format(action["href"]), "title": action.text},
                      info={"plot": item.find("div", "writer-result-description").text},
                      art=ku.art(jafc.get_url(item.find("img", "thumbnail")["src"])))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.setPluginCategory(plugin.handle, ku.localize(32004))  # Authors
    xbmcplugin.endOfDirectory(plugin.handle)


def run():
    plugin.run()
