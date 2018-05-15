# -*- coding: utf-8 -*-
"""Main plugin file - Handles the various routes"""

__author__ = "fraser"

import routing
import xbmc
import xbmcaddon as xa
import xbmcplugin as xp
from xbmcgui import ListItem

from resources.lib import kodiutils as ku
from resources.lib import search as jafc

plugin = routing.Plugin()
ADDON = xa.Addon()
ADDON_ID = ADDON.getAddonInfo("id")  # plugin.video.jafc
ADDON_NAME = ADDON.getAddonInfo("name")  # East Anglian Film Archive
MEDIA_URI = "special://home/addons/{}/resources/media/".format(ADDON_ID)

PLAYBACK_RESOLUTION = "480"


def add_menu_item(method, label, args=None, art=None, info=None, directory=True):
    # type (Callable, str, dict, dict, dict, bool) -> None
    """wrapper for xbmcplugin.addDirectoryItem"""
    info = {} if info is None else info
    art = {} if art is None else art
    args = {} if args is None else args
    label = ku.get_string(label) if isinstance(label, int) else label
    list_item = ListItem(label)
    list_item.setArt(art)
    list_item.setInfo("video", info)
    if method == search and "q" in args:
        # saved search menu items can be removed via context menu
        list_item.addContextMenuItems([(
            ku.get_string(32019),
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


def get_info(href):
    idx = jafc.text_to_int(href)
    data = jafc.get_html("{}{}".format(jafc.JAFC_INFO_URI, idx))
    return {
        "plot": jafc.get_table_data(data, "Plot"),
        "title": jafc.get_table_data(data, "English Title"),
        "originaltitle": jafc.get_table_data(data, "Japanese kana Rendering"),  # Original Title
        "year": jafc.text_to_int(jafc.get_table_data(data, "Production Date")),
        "director": jafc.get_table_data(data, "Credits: Director"),
        "duration": jafc.text_to_int(jafc.get_table_data(data, "Duration (minutes)")) * 60
    }


def paginate(data, method):
    """Adds pagination links as required"""
    if data is None:
        return
    items = data.find_all("li")
    for item in items:
        if "class" in item.attrs and any(x in item.attrs["class"] for x in ["disabled", "active", "prev", "next"]):
            continue
        action = item.find("a")
        add_menu_item(method, "[{} {}]".format(ku.get_string(32011), item.text), {  # [Page n]
            "href": action["href"]
        })
    add_menu_item(index, "[{}]".format(ku.get_string(32012)))  # [Menu]


@plugin.route("/")
def index():
    """Main menu"""
    if ku.get_setting_as_bool("show_genres"):
        add_menu_item(themes, 32005, {
            "href": "en/categories/stories",
            "title": ku.get_string(32005)
        }, ku.icon("genres.png"))
    if ku.get_setting_as_bool("show_motions"):
        add_menu_item(themes, 32002, {
            "href": "en/categories/motions",
            "title": ku.get_string(32002)
        }, ku.icon("techniques.png"))
    if ku.get_setting_as_bool("show_characters"):
        add_menu_item(themes, 32003, {
            "href": "en/categories/characters",
            "title": ku.get_string(32003)
        }, ku.icon("characters.png"))
    if ku.get_setting_as_bool("show_authors"):
        add_menu_item(authors, 32004, art=ku.icon("authors.png"))
    if ku.get_setting_as_bool("show_experts"):
        add_menu_item(experts, 32023, art=ku.icon("experts.png"))
    if ku.get_setting_as_bool("show_techniques"):
        add_menu_item(themes, 32006, {
            "href": "en/categories/techniques",
            "title": ku.get_string(32006)
        }, ku.icon("techniques.png"))
    if ku.get_setting_as_bool("show_search"):
        add_menu_item(search, 32007, {"menu": True}, ku.icon("search.png"))
    if ku.get_setting_as_bool("show_settings"):
        add_menu_item(settings, 32010, art=ku.icon("settings.png"), directory=False)
    xp.setPluginCategory(plugin.handle, ADDON_NAME)
    xp.endOfDirectory(plugin.handle)


@plugin.route("/settings")
def settings():
    ku.show_settings()
    xbmc.executebuiltin("Container.Refresh()")


@plugin.route("/play")
def play_film():
    href = get_arg("href", False)
    if not href:
        return
    url = jafc.get_player_url(jafc.text_to_int(href))
    list_item = ListItem(path=url)
    xp.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<token>")
def clear(token):
    if token == "cache" and ku.confirm():
        jafc.cache_clear()


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
        add_menu_item(search, "[{}]".format(ku.get_string(32016)), {"new": True})  # [New Search]
        for item in jafc.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text, {"q": text})
        xp.setPluginCategory(plugin.handle, ku.get_string(32007))  # Search
        xp.endOfDirectory(plugin.handle)
        return True

    # look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        jafc.append(query)
        if not query:
            return False

    url = jafc.get_page_url(href) if href else jafc.get_search_url(query)
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
                      {"href": action["href"]},
                      info=get_info(action["href"]),
                      art=ku.art(jafc.get_page_url(img["src"])),
                      directory=False)
    xp.setPluginCategory(plugin.handle, "{} '{}'".format(ku.get_string(32016), query))
    xp.endOfDirectory(plugin.handle)


@plugin.route("/themes")
def themes():
    """List of directory menu items for each theme"""
    url = jafc.get_page_url(get_arg("href"))
    data = jafc.get_html(url)
    element = data.find("ul", {
        "class": ["category-condition-keyword", "work-favorites-condition-keyword"]
    })
    for item in element.find_all("li"):
        action = item.find("a")
        span = action.find("span")
        if span:
            span.extract()
        title = action.text
        add_menu_item(films, title, {"href": action["href"], "title": title})
    xp.setPluginCategory(plugin.handle, get_arg("title"))
    xp.endOfDirectory(plugin.handle)


@plugin.route("/films")
def films():
    """Playable movie items"""
    url = jafc.get_page_url(get_arg("href"))
    data = jafc.get_html(url)
    paginate(data.find("ul", "pager-menu"), films)
    container = data.find(True, {"class": ["categories", "characters", "writer-works"]})
    for item in container.find_all("li"):
        title = item.find(True, {"class": ["category-title", "character-serif", "writer-work-heading"]}).text
        action = item.find("a")
        if action is None:
            continue
        img = item.find("img", "thumbnail")
        add_menu_item(
            play_film,
            title,
            {"href": action["href"]},
            info=get_info(action["href"]),
            art=ku.art(jafc.get_page_url(img["src"])),
            directory=False)
    xp.setPluginCategory(plugin.handle, get_arg("title"))
    xp.setContent(plugin.handle, "videos")
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_LABEL_IGNORE_THE)
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_GENRE)
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_VIDEO_YEAR)
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_DURATION)
    xp.endOfDirectory(plugin.handle)


@plugin.route("/experts")
def experts():
    """Lists experts, and their choices"""
    href = get_arg("href", False)
    if not href:
        url = jafc.get_page_url("en/works-favorites.html")
        data = jafc.get_html(url)
        container = data.find("div", "work-favorites")
        for item in container.find_all("div", "work-favorite"):
            action = item.find("a")
            img = item.find("img", "thumbnail")
            title = img["alt"]
            ku.log(action)
            add_menu_item(experts,
                          title,
                          args={"href": "en/" + action["href"], "title": title},
                          info={"plot": item.find("div", "work-favorite-summary").text},
                          art=ku.art(jafc.get_page_url(img["src"])))
    else:
        url = jafc.get_page_url(href)
        data = jafc.get_html(url)
        for item in data.find_all("div", "favorite-work"):
            img = item.find("img", "thumbnail")
            action = item.find("h2").find("a")
            title = action.text
            add_menu_item(play_film,
                          title,
                          args={"href": action["href"]},
                          info={"plot": item.find("dd").text},
                          art=ku.art(jafc.get_page_url(img["src"])),
                          directory=False)
    xp.setPluginCategory(plugin.handle, get_arg("title"))
    xp.endOfDirectory(plugin.handle)


@plugin.route("/authors")
def authors():
    """List of authors"""
    url = jafc.get_page_url("en/writer.html")
    data = jafc.get_html(url)
    container = data.find("ul", "writer-results")
    for item in container.find_all("li"):
        img = item.find("img", "thumbnail")
        action = item.find("a")
        if action is None:
            continue
        add_menu_item(films, action.text, args={
            "href": "en/{}".format(action["href"]),
            "title": action.text
        }, info={
            "plot": item.find("div", "writer-result-description").text
        }, art=ku.art(jafc.get_page_url(img["src"])))
    xp.addSortMethod(plugin.handle, xp.SORT_METHOD_LABEL)
    xp.endOfDirectory(plugin.handle)


@plugin.route("/highlights")
def highlights():
    """"""


def run():
    plugin.run()
