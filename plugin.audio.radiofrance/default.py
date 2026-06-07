import os
import datetime
import json

import sys
import requests
from pathlib import Path
from urllib.parse import parse_qs
from concurrent.futures import ThreadPoolExecutor
import itertools

import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import xbmcplugin

from utils import *
from interface import *

DEFAULT_MANIFESTATION = 0
RADIOFRANCE_PAGE = "https://www.radiofrance.fr"

CACHE_DIR = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
CACHE_FILE = os.path.join(CACHE_DIR, 'radiofrance_cache.json')
CACHE_TIMEOUT = datetime.timedelta(seconds=300)

# Function to save cache to a file
def save_cache(data):
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        xbmc.log("Caching to :" + CACHE_FILE, xbmc.LOGINFO)
        json.dump(data, f)

# Function to load cache from a file
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            xbmc.log("Loading cach from :" + CACHE_FILE, xbmc.LOGINFO)
            try:
                data = json.load(f)
            except:
                return {}
            return data
    return {}

def build_lists(data, args, url):
    gui_elements_list = []

    mode = args.get("mode", [None])[0]
    if mode is None:
        Search(args).add(gui_elements_list)
        Podcasts(args).add(gui_elements_list)

    item = create_item_from_page(data)
    context = data.get('context', {})

    if mode == "index":
        element_index = int(args.get("index", [None])[0])
        items_list = create_item(0, item.subs[element_index], context).subs
    else:
        items_list = item.subs

    Pages(item, args).add(gui_elements_list)

    context = data.get('context', {})
    with ThreadPoolExecutor() as executor:
        elements_lists = list(executor.map(lambda idx, data: add_with_index(idx, data, args, context), range(len(items_list)), items_list))

    gui_elements_list.extend(itertools.chain.from_iterable(elements_lists))

    xbmcplugin.setContent(addon_handle, "episodes")
    xbmcplugin.addDirectoryItems(addon_handle, gui_elements_list, len(gui_elements_list))
    xbmcplugin.endOfDirectory(addon_handle)

def add_with_index(index, data, args, context):
    item = create_item(index, data, context)
    if not isinstance(item, Item):
        _, data, exception = item
        xbmc.log(f"Error: {exception} on {data}", xbmc.LOGERROR)
        return []

    xbmc.log(str(item), xbmc.LOGINFO)
    elements_list = []
    url = args.get("url", [""])[0]

    if len(item.subs) <= 2:
        sub_list = list(map(lambda idx, data: create_item(idx, data, context), range(len(item.subs)), item.subs))

        for sub_item in sub_list:
            if sub_item.is_folder():
                elements_list.append(Folder(sub_item, args).construct())
            else:
                elements_list.append(Playable(sub_item, args).construct())
    elif len(item.subs) > 1:
        elements_list.append(Indexed(item, url, index, args).construct())

    if item.is_folder() and item.path is not None:
        elements_list.append(Folder(item, args).construct())
    elif not item.is_folder():
        elements_list.append(Playable(item, args).construct())

    return elements_list

def brand(args):
    url = args.get("url", [""])[0]
    xbmc.log(f"[Play Brand]: {url}", xbmc.LOGINFO)
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

    new_args = {k: v[0] for k, v in args.items()}
    new_args["mode"] = "page"
    value = GUIEditExportName("Odyssées")
    if value is None:
        return

    new_args["url"] = f"{RADIOFRANCE_PAGE}/recherche"
    new_args = {k: [v] for k, v in new_args.items()}
    build_url(new_args)
    get_and_build_lists(new_args, url_args=f"?term={value}&")

def get_and_build_lists(args, url_args="?"):

    cache = load_cache()

    xbmc.log(f"Get and build: {args} (url args: {url_args})", xbmc.LOGINFO)
    url = args.get("url", [RADIOFRANCE_PAGE])[0]

    now = datetime.datetime.now()
    if url + url_args in cache and now - datetime.datetime.fromisoformat(cache[url + url_args]['datetime']) < CACHE_TIMEOUT:
        xbmc.log(f"Using cached data for url: {url + url_args}", xbmc.LOGINFO)
        data = cache[url + url_args]['data']
    else:
        page = requests.get(f"{url}/__data.json{url_args}").text
        data = expand_json(page)
        cache[url + url_args] = {'datetime': datetime.datetime.now().isoformat(), 'data': data}
        save_cache(cache)

    build_lists(data, args, url)

def main():
    args = parse_qs(sys.argv[2][1:])
    mode = args.get("mode", [None])[0]

    xbmc.log(f"Mode: {mode}, Args: {args}", xbmc.LOGINFO)

    # Initial launch of add-on
    url = ""
    url_args = "?"
    # url_args += "recent=false&"
    if "page" in args and int(args.get("page", ["1"])[0]) > 1:
        url_args += f"&p={args.get('page', ['1'])[0]}"
    if mode == "stream":
        play(args["url"][0])
    elif mode == "search":
        search(args)
    elif mode == "brand":
        brand(args)
    else:
        if mode == "podcasts":
            args["url"][0] += "/podcasts"
        elif not mode:
            url = RADIOFRANCE_PAGE
            args["url"] = [url]
        # New page
        get_and_build_lists(args, url_args)

if __name__ == "__main__":
    addon_handle = int(sys.argv[1])
    main()
