# https://docs.python.org/2.7/
import sys

from future.standard_library import install_aliases

install_aliases()
from future.utils import (PY3)

if PY3:
    from urllib.parse import parse_qs
else:
    from urlparse import parse_qs

import xbmcgui
import xbmcplugin
import xbmcaddon
import random
import xbmc
from resources.lib.bandcamp_api import bandcamp
from resources.lib.bandcamp_api.bandcamp import Band, Album
from resources.lib.kodi.ListItems import ListItems

try:
    import StorageServer
except:
    from resources.lib.cache import storageserverdummy as StorageServer
cache = StorageServer.StorageServer("plugin.audio.kxmxpxtx.bandcamp", 24)  # (Your plugin name, Cache time in hours)


def build_main_menu():
    root_items = list_items.get_root_items(username)
    xbmcplugin.addDirectoryItems(addon_handle, root_items, len(root_items))
    xbmcplugin.endOfDirectory(addon_handle)


def build_band_list(bands, from_wishlist=False):
    band_list = list_items.get_band_items(bands, from_wishlist)
    xbmcplugin.addDirectoryItems(addon_handle, band_list, len(band_list))
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(addon_handle)


def build_album_list(albums):
    albums_list = list_items.get_album_items(albums)
    xbmcplugin.addDirectoryItems(addon_handle, albums_list, len(albums_list))
    xbmcplugin.endOfDirectory(addon_handle)


def build_genre_list():
    genre_list = list_items.get_genre_items(cache.cacheFunction(bandcamp.get_genres))
    xbmcplugin.addDirectoryItems(addon_handle, genre_list, len(genre_list))
    xbmcplugin.endOfDirectory(addon_handle)


def build_subgenre_list(genre):
    subgenre_list = list_items.get_subgenre_items(genre, cache.cacheFunction(bandcamp.get_subgenres))
    xbmcplugin.addDirectoryItems(addon_handle, subgenre_list, len(subgenre_list))
    xbmcplugin.endOfDirectory(addon_handle)


def build_song_list(band, album, tracks, autoplay=False):
    track_list = list_items.get_track_items(band=band, album=album, tracks=tracks)
    if autoplay:
        ## Few hacks, check for more info: https://forum.kodi.tv/showthread.php?tid=354733&pid=2952379#pid2952379
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=track_list[0][1])
        xbmc.sleep(2000)
        for url, list_item, folder in track_list[1:]:
            playlist.add(url, list_item)
    else:
        xbmcplugin.addDirectoryItems(addon_handle, track_list, len(track_list))
        xbmcplugin.setContent(addon_handle, 'songs')
        xbmcplugin.endOfDirectory(addon_handle)


def build_search_result_list(items):
    item_list = []
    for item in items:
        if isinstance(item, Band):
            item_list += list_items.get_band_items([item], from_search=True)
        elif isinstance(item, Album):
            item_list += list_items.get_album_items([item])
    xbmcplugin.addDirectoryItems(addon_handle, item_list, len(item_list))
    xbmcplugin.endOfDirectory(addon_handle)


def build_featured_list(bands):
    for band in bands:
        for album in bands[band]:
            track_list = list_items.get_track_items(band=band, album=album, tracks=bands[band][album], to_album=True)
            xbmcplugin.addDirectoryItems(addon_handle, track_list, len(track_list))
    xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)


def play_song(url):
    play_item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def search(query):
    build_search_result_list(bandcamp.search(query))


def main():
    args = parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)
    if mode is None:
        build_main_menu()
    elif mode[0] == 'stream':
        play_song(args['url'][0])
    elif mode[0] == 'list_discover':
        build_genre_list()
    elif mode[0] == 'list_collection':
        build_band_list(bandcamp.get_collection(bandcamp.get_fan_id()))
    elif mode[0] == 'list_wishlist':
        build_band_list(bandcamp.get_wishlist(bandcamp.get_fan_id()), from_wishlist=True)
    elif mode[0] == 'list_wishlist_albums':
        bands = bandcamp.get_wishlist(bandcamp.get_fan_id())
        band = Band(band_id=args.get('band_id', None)[0])
        build_album_list(bands[band])
    elif mode[0] == 'list_search_albums':
        band, albums = bandcamp.get_band(args.get('band_id', None)[0])
        build_album_list(albums)
    elif mode[0] == 'list_albums':
        bands = bandcamp.get_collection(bandcamp.get_fan_id())
        band = Band(band_id=args.get('band_id', None)[0])
        build_album_list(bands[band])
    elif mode[0] == 'list_songs':
        album_id = args.get('album_id', None)[0]
        item_type = args.get('item_type', None)[0]
        build_song_list(*bandcamp.get_album(album_id=album_id, item_type=item_type))
    elif mode[0] == 'list_subgenre':
        genre = args.get('category', None)[0]
        build_subgenre_list(genre)
    elif mode[0] == 'list_subgenre_songs':
        genre = args.get('category', None)[0]
        subgenre = args.get('subcategory', None)[0]
        slices = []
        if addon.getSetting('slice_top') == 'true':
            slices.append("top")
        if addon.getSetting('slice_new') == 'true':
            slices.append("new")
        if addon.getSetting('slice_rec') == 'true':
            slices.append("rec")
        discover_dict = {}
        for slice in slices:
            discover_dict.update(bandcamp.discover(genre, subgenre, slice))
        shuffle_list = list(discover_dict.items())
        random.shuffle(shuffle_list)
        discover_dict = dict(shuffle_list)
        build_featured_list(discover_dict)
    elif mode[0] == 'search':
        action = args.get("action", None)[0]
        query = args.get("query", [""])[0]
        if action == "new":
            query = xbmcgui.Dialog().input(addon.getLocalizedString(30103))
        if query:
            search(query)
    elif mode[0] == 'url':
        url = args.get("url", None)[0]
        build_song_list(*bandcamp.get_album_by_url(url), autoplay=True)
    elif mode[0] == 'settings':
        addon.openSettings()


if __name__ == '__main__':
    xbmc.log("sys.argv:" + str(sys.argv), xbmc.LOGDEBUG)
    addon = xbmcaddon.Addon()
    list_items = ListItems(addon)
    username = addon.getSetting('username')
    bandcamp = bandcamp.Bandcamp(username)
    addon_handle = int(sys.argv[1])
    main()
