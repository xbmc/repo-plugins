import json
import sys
import requests
from urllib.parse import parse_qs
from enum import Enum

# http://mirrors.kodi.tv/docs/python-docs/
# http://www.crummy.com/software/BeautifulSoup/bs4/doc/
from urllib.parse import urlencode, quote_plus
from ast import literal_eval
import xbmc
import xbmcgui
import xbmcplugin

from utils import *

DEFAULT_MANIFESTATION = 0
RADIOFRANCE_PAGE = "https://www.radiofrance.fr"


def build_lists(data, args, url):
    xbmc.log(str(args), xbmc.LOGINFO)

    def add_search():
        new_args = {k: v[0] for (k, v) in list(args.items())}
        new_args["mode"] = "search"
        li = xbmcgui.ListItem(label=localize(30100))
        li.setIsFolder(True)
        new_url = build_url(new_args)
        highlight_list.append((new_url, li, True))

    def add_podcasts():
        new_args = {k: v[0] for (k, v) in list(args.items())}
        new_args["mode"] = "podcasts"
        li = xbmcgui.ListItem(label=localize(30104))
        li.setIsFolder(True)
        new_url = build_url(new_args)
        highlight_list.append((new_url, li, True))

    def add_pages(item):
        new_args = {k: v[0] for (k, v) in list(args.items())}
        (num, last) = item.pages
        if 1 < num:
            new_args["page"] = num - 1
            li = xbmcgui.ListItem(label=localize(30101))
            li.setIsFolder(True)
            new_url = build_url(new_args)
            highlight_list.append((new_url, li, True))
        if num < last:
            new_args["page"] = num + 1
            li = xbmcgui.ListItem(label=localize(30102))
            li.setIsFolder(True)
            new_url = build_url(new_args)
            highlight_list.append((new_url, li, True))

    def add(item, index):
        new_args = {}
        # Create kodi element
        if item.is_folder():
            if item.path is not None:
                li = xbmcgui.ListItem(label=item.title)
                li.setArt({"thumb": item.image, "icon": item.icon})
                li.setIsFolder(True)
                new_args = {"title": item.title}
                new_args["url"] = item.path
                new_args["mode"] = "url"
                builded_url = build_url(new_args)
                highlight_list.append((builded_url, li, True))

                xbmc.log(
                    str(new_args),
                    xbmc.LOGINFO,
                )
            if 1 == len(item.subs):
                add(create_item(item.subs[0]), index)
            elif 1 < len(item.subs):
                li = xbmcgui.ListItem(label="⭐ " + item.title if item.title is not None else "")
                li.setArt({"thumb": item.image, "icon": item.icon})
                li.setIsFolder(True)
                new_args = {"title": "⭐ " + item.title if item.title is not None else ""}
                new_args["url"] = url
                new_args["index"] = index
                new_args["mode"] = "index"
                builded_url = build_url(new_args)
                highlight_list.append((builded_url, li, True))

                xbmc.log(
                    str(new_args),
                    xbmc.LOGINFO,
                )

        else:
            # Playable element
            li = xbmcgui.ListItem(label=item.title)
            li.setArt({"thumb": item.image, "icon": item.icon})
            new_args = {"title": item.title}
            li.setIsFolder(False)
            tag = li.getMusicInfoTag(offscreen=True)
            tag.setMediaType("audio")
            tag.setTitle(item.title)
            tag.setURL(item.path)
            tag.setGenres([item.genre if item.model == Model['Brand'] else "podcast"])
            tag.setArtist(item.artists)
            tag.setDuration(item.duration if item.duration is not None else 0)
            tag.setReleaseDate(item.release)
            li.setProperty("IsPlayable", "true")
            if item.path is not None:
                new_args["url"] = item.path
                new_args["mode"] = (
                    "brand" if item.model == Model["Brand"] else "stream"
                )

                builded_url = build_url(new_args)
                song_list.append((builded_url, li, False))

            xbmc.log(
                str(new_args),
                xbmc.LOGINFO,
            )

    highlight_list = []
    song_list = []

    mode = args.get("mode", [None])[0]
    if mode is None:
        add_search()
        add_podcasts()

    item = create_item_from_page(data)
    if mode == "index":
        element_index = int(args.get("index", [None])[0])
        items_list = create_item(item.subs[element_index]).elements
    else:
        items_list = item.subs

    add_pages(item)
    index = 0
    for data in items_list:
        sub_item = create_item(data)
        xbmc.log(str(sub_item), xbmc.LOGINFO)
        add(sub_item, index)
        index += 1

    xbmcplugin.setContent(addon_handle, "episodes")
    xbmcplugin.addDirectoryItems(addon_handle, highlight_list, len(highlight_list))
    xbmcplugin.addDirectoryItems(addon_handle, song_list, len(song_list))
    xbmcplugin.endOfDirectory(addon_handle)


def brand(args):
    url = args.get("url", [""])[0]

    xbmc.log("[Play Brand]: " + url, xbmc.LOGINFO)
    play(url)

def play(url):
    play_item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def search(args):
    def GUIEditExportName(name):
        kb = xbmc.Keyboard("Odyssées", localize(30103))
        kb.doModal()
        if not kb.isConfirmed():
            return None
        query = kb.getText()
        return query

    new_args = {k: v[0] for (k, v) in list(args.items())}
    new_args["mode"] = "page"
    value = GUIEditExportName("Odyssées")
    if value is None:
        return

    new_args["url"] = RADIOFRANCE_PAGE + "/recherche"
    new_args = {k: [v] for (k, v) in list(new_args.items())}
    build_url(new_args)
    get_and_build_lists(new_args, url_args="?term=" + value + "&")


def get_and_build_lists(args, url_args="?"):
    xbmc.log(
        "".join(["Get and build: " + str(args) + "(url args: " + url_args + ")"]),
        xbmc.LOGINFO,
    )
    url = args.get("url", [RADIOFRANCE_PAGE])[0]
    page = requests.get(url + "/__data.json" + url_args).text
    content = expand_json(page)

    build_lists(content, args, url)


def main():
    args = parse_qs(sys.argv[2][1:])
    mode = args.get("mode", None)

    xbmc.log(
        "".join(
            ["mode: ", str("" if mode is None else mode[0]), ", args: ", str(args)]
        ),
        xbmc.LOGINFO,
    )

    # initial launch of add-on
    url = ""
    url_args = "?"
    url_args += "recent=false&"
    if "page" in args and 1 < int(args.get("page", ["1"])[0]):
        url_args += "p=" + str(args.get("page", ["1"])[0])
    if mode is not None and mode[0] == "stream":
        play(args("url"))
    elif mode is not None and mode[0] == "search":
        search(args)
    elif mode is not None and mode[0] == "brand":
        brand(args)
    else:
        if mode is not None and mode[0] == "podcasts":
            args["url"][0] += "/podcasts"
        elif mode is None:
            url = RADIOFRANCE_PAGE
            args["url"] = []
            args["url"].append(url)
        # New page
        get_and_build_lists(args, url_args)


if __name__ == "__main__":
    addon_handle = int(sys.argv[1])
    main()
