import sys
import requests
from urllib.parse import parse_qs
from concurrent.futures import ThreadPoolExecutor
import itertools

import xbmc
import xbmcgui
import xbmcplugin

from utils import *
from interface import *

DEFAULT_MANIFESTATION = 0
RADIOFRANCE_PAGE = "https://www.radiofrance.fr"

def build_lists(data, args, url):

    gui_elements_list = []

    mode = args.get("mode", [None])[0]
    if mode is None:
        Search(args).add(gui_elements_list)
        Podcasts(args).add(gui_elements_list)

    item = create_item_from_page(data)
    if mode == "index":
        element_index = int(args.get("index", [None])[0])
        items_list = create_item(0, item.subs[element_index]).subs
    else:
        items_list = item.subs

    Pages(item, args).add(gui_elements_list)

    with ThreadPoolExecutor() as p:
        elements_lists = p.map(add_with_index, itertools.count(), iter(items_list), itertools.repeat(args))
        gui_elements_list += list(itertools.chain.from_iterable(elements_lists))

    xbmcplugin.setContent(addon_handle, "episodes")
    xbmcplugin.addDirectoryItems(addon_handle, gui_elements_list, len(gui_elements_list))
    xbmcplugin.endOfDirectory(addon_handle)


def add_with_index(index, data, args):
    item = create_item(index, data)
    if not isinstance(item, Item):
        (_, data, exception) = item
        xbmc.log("Error :" + str( exception) + " on " + str( data),
                 xbmc.LOGERROR)
        return []

    xbmc.log(str(item), xbmc.LOGINFO)
    elements_list = []
    url = args.get("url", [""])[0]

    if 1 == len(item.subs):
        sub_item = create_item(0, item.subs[0])
        if sub_item.is_folder() :
            elements_list.append(Folder(sub_item, args).construct())
        else:
            elements_list.append(Playable(sub_item, args).construct())
    elif 1 < len(item.subs):
        elements_list.append(Indexed(item, url, index, args).construct())

    if item.is_folder():
        if item.path is not None:
            elements_list.append(Folder(item, args).construct())
    else:
        elements_list.append(Playable(item, args).construct())
    return elements_list

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
