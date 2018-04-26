# -*- coding: utf-8 -*-
"""Main plugin file - Handles the various routes"""

__author__ = "fraser"

import routing
import xbmc
import xbmcaddon as xa
import xbmcplugin as xp
from xbmcgui import ListItem

from resources.lib import kodiutils as ku
from resources.lib import search as eafa

plugin = routing.Plugin()
ADDON = xa.Addon()
ADDON_ID = ADDON.getAddonInfo("id")  # plugin.video.eafa
ADDON_NAME = ADDON.getAddonInfo("name")  # East Anglian Film Archive
MEDIA_URI = "special://home/addons/{}/resources/media/".format(ADDON_ID)


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


def parse_time(text):
    # type (str) -> int
    """
    Attempts to calculate the total number of seconds in a time string
    e.g. "10"=10 "1:14"=74 "1:03:28"=3808
    """
    sep = text.count(":")
    if not sep:
        return eafa.text_to_int(text)
    if sep == 1:
        m, s = text.split(":")
        return (eafa.text_to_int(m) * 60) + eafa.text_to_int(s)
    if sep == 2:
        h, m, s = text.split(":")
        return ((eafa.text_to_int(h) * 3600) +
                (eafa.text_to_int(m) * 60) +
                eafa.text_to_int(s))
    return 0


def parse_results(data, offset=1, query=None):
    # type (BeautifulSoup, int, str) -> None
    """Parse videos from results and add pagination"""
    items = data.find_all("div", "result_item")
    if not items:
        return
    if query is not None and data.find("div", "pagination"):
        paginate(query, offset, len(items))
    for item in items:
        action = item.find("a")
        title = item.find("h2").text.strip()
        img = item.find("img")
        add_menu_item(
            play_film,
            title,
            args={"href": action["href"].lstrip("../")},
            art=ku.art(eafa.get_page_url(img["src"])),
            info={
                "title": title,
                "plot": item.find("p").text.strip(),
                "duration": parse_time(item.find("span", "dur").text)
            },
            directory=False
        )
    xp.setContent(plugin.handle, "videos")
    xp.endOfDirectory(plugin.handle)


def parse_links(data, form):
    # type (BeautifulSoup, dict) -> None
    """Parse links from results and add prepare query"""
    links = data.select("a[href*=javascript:__doPostBack]")
    if not links:
        return
    for link in links:
        title = link.text.strip().title()
        add_menu_item(themes, title, {
            "target": eafa.pluck(link["href"], "'", "'"),
            "state": form["state"],
            "validation": form["validation"],
            "action": form["action"],
            "title": title
        })
    xp.setContent(plugin.handle, "videos")
    xp.endOfDirectory(plugin.handle)


def get_form_data(data):
    # type (BeautifulSoup) -> Union[bool, dict]
    """Attempts to extract the form state and validation data"""
    validation = data.find("input", {"id": "__EVENTVALIDATION"})
    if not validation:
        return False
    return {
        "state": data.find("input", {"id": "__VIEWSTATE"})["value"],
        "action": data.find("form", {"id": "aspnetForm"})["action"],
        "validation": validation["value"]
    }


def paginate(query, offset, count):
    # type (str, int, int) -> None
    """Adds pagination links as required"""
    offset += 1
    next_page = "[{} {}]".format(ku.get_string(32011), offset)  # [Page n+1]
    first_page = "[{} 1]".format(ku.get_string(32011))  # [Page 1]
    main_menu = "[{}]".format(ku.get_string(32012))  # [Menu]
    if offset > 2:
        add_menu_item(search, first_page, {"q": query, "page": 1})
    if count == eafa.SEARCH_MAX_RESULTS:
        add_menu_item(search, next_page, {"q": query, "page": offset})
    add_menu_item(index, main_menu)


@plugin.route("/")
def index():
    """Main menu"""
    if ku.get_setting_as_bool("show_highlights"):
        add_menu_item(highlights,
                      ku.get_string(32006),
                      art=ku.icon("highlights.png"))
    if ku.get_setting_as_bool("show_genres"):
        add_menu_item(browse,
                      ku.get_string(32005),
                      {"id": "genre_items", "title": ku.get_string(32005)},
                      ku.icon("genres.png"))
    if ku.get_setting_as_bool("show_subjects"):
        add_menu_item(browse,
                      ku.get_string(32003),
                      {"id": "subject_items", "title": ku.get_string(32003)},
                      ku.icon("subjects.png"))
    if ku.get_setting_as_bool("show_people"):
        add_menu_item(browse,
                      ku.get_string(32004),
                      {"id": "people_items", "title": ku.get_string(32004)},
                      ku.icon("people.png"))
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
    url = eafa.get_page_url(get_arg("href"))
    data = eafa.get_html(url)
    container = data.find("div", {"id": "video-container"})
    if not container:
        return False
    script = container.find_next_sibling("script")
    if not script:
        return False
    mp4_url = eafa.pluck(
        eafa.remove_whitespace(script.text),
        "'hd-2':{'file':'", "'}}});")  # TODO: maybe re
    list_item = ListItem(path=mp4_url)
    xp.setResolvedUrl(plugin.handle, True, list_item)


@plugin.route("/clear/<token>")
def clear(token):
    if token == "cache" and ku.confirm():
        eafa.cache_clear()


@plugin.route("/search")
def search():
    query = get_arg("q")
    page = int(get_arg("page", 1))

    # remove saved search item
    if bool(get_arg("delete", False)):
        eafa.remove(query)
        xbmc.executebuiltin("Container.Refresh()")
        return True

    # View saved search menu
    if bool(get_arg("menu", False)):
        add_menu_item(search, "[{}]".format(ku.get_string(32016)), {"new": True})  # [New Search]
        for item in eafa.retrieve():
            text = item.encode("utf-8")
            add_menu_item(search, text, {"q": text})
        xp.setPluginCategory(plugin.handle, ku.get_string(32007))  # Search
        xp.endOfDirectory(plugin.handle)
        return True

    # look-up
    if bool(get_arg("new", False)):
        query = ku.user_input()
        eafa.append(query)
        if not query:
            return False

    form = get_form_data(eafa.get_html(eafa.EAFA_SEARCH_URI))
    if not form:
        return False
    data = eafa.post_html(eafa.EAFA_SEARCH_URI, {
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ucSearch$ToolkitScriptManager1",
        "__EVENTARGUMENT": eafa.get_search_params(query, page),
        "__VIEWSTATE": form["state"]
    })
    xp.setPluginCategory(
        plugin.handle,
        "{} '{}'".format(ku.get_string(32007),  # Search 'query'
                         eafa.query_decode(query))
    )
    parse_results(data, page, query)


@plugin.route("/browse")
def browse():
    data = eafa.get_html(eafa.EAFA_BROWSE_URI)
    form = get_form_data(data)
    if not form:
        return False
    container = data.find("div", {"id": get_arg("id")})
    form["action"] = "browse.aspx"
    parse_links(container, form)


@plugin.route("/themes")
def themes():
    url = eafa.get_page_url(get_arg("action"))
    xp.setPluginCategory(plugin.handle, get_arg("title"))
    parse_results(eafa.post_html(url, {
        "ctl00$ContentPlaceHolder1$ucBrowse$cbVideo": "on",
        "__EVENTTARGET": get_arg("target"),
        "__EVENTVALIDATION": get_arg("validation"),
        "__VIEWSTATE": get_arg("state")
    }))


@plugin.route("/highlights")
def highlights():
    href = get_arg("href", False)
    xp.setPluginCategory(plugin.handle, get_arg("title", ku.get_string(32006)))  # Highlights
    if not href:
        url = eafa.get_page_url("highlights.aspx")
        data = eafa.get_html(url)
        for item in data.find_all("div", "hl_box"):
            action = item.find("a")
            img = action.find("img")
            title = img["alt"]
            add_menu_item(
                highlights,
                title,
                {"href": action["href"], "title": title},
                art=ku.art(eafa.get_page_url(img["src"]))
            )
        xp.setContent(plugin.handle, "videos")
        xp.endOfDirectory(plugin.handle)
        return
    url = eafa.get_page_url(href)
    data = eafa.get_html(url)
    form = get_form_data(data)
    if form:
        parse_links(data, form)
    else:
        parse_results(data)


def run():
    plugin.run()
