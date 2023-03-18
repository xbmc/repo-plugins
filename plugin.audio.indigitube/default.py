import sys, json, re
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlencode

import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
from resources.lib.ListItems import ListItems

try:
    import StorageServer
except:
    from resources.lib.cache import storageserverdummy as StorageServer
cache = StorageServer.StorageServer('plugin.audio.indigitube', 24)  # (Your plugin name, Cache time in hours)

USER_AGENT      = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
CONTENT_QUERY   = 'https://api.appbooks.com/content/_query/{}'
CONTENT_CHANNEL = 'https://api.appbooks.com/content/channel/{}'
CONTENT_ALBUM   = 'https://api.appbooks.com/content/album/{}'
CONTENT_PAGE    = 'https://api.appbooks.com/content/pageConfiguration/{}'

PAGE_HOME = '5b5abc2bf6b4d90e6deeaabb'
QUERY_RADIO = '5d1aeac759dd785afe88ec0b'
CHANNEL_RADIO = '5b5ac73df6b4d90e6deeabd1'

def urlopen_ua(url):
    headers = {
        'User-Agent': USER_AGENT,
        'Authorization': 'Bearer $2a$10$x2Zy/TgIAOC0UUMi3NPKc.KY49e/ZLUJFOpBCNYAs8D72UUnlI526',
    }
    return urlopen(Request(url, headers=headers), timeout=5)

def get_json(url):
    return urlopen_ua(url).read().decode()

def get_json_obj(url):
    return json.loads(get_json(url))

def get_query_content(media_id):
    return get_json_obj(CONTENT_QUERY.format(media_id))

def get_channel_content(media_id):
    return get_json_obj(CONTENT_CHANNEL.format(media_id))

def get_album_content(media_id):
    return get_json_obj(CONTENT_ALBUM.format(media_id))

def get_page_content(page_id):
    return get_json_obj(CONTENT_PAGE.format(page_id))


def build_main_menu():
    home_json = get_page_content(PAGE_HOME)
    root_items = list_items.get_root_items(home_json)
    if len(root_items) > 0:
        xbmcplugin.setPluginCategory(addon_handle, home_json.get('title', ''))
        xbmcplugin.addDirectoryItems(addon_handle, root_items, len(root_items))
        xbmcplugin.endOfDirectory(addon_handle)

def build_query_list(query_id, title=''):
    query_json = get_query_content(query_id)
    query_items = list_items.get_query_items(query_json)
    if len(query_items) > 0:
        xbmcplugin.setPluginCategory(addon_handle, title)
        xbmcplugin.addDirectoryItems(addon_handle, query_items, len(query_items))
        xbmcplugin.endOfDirectory(addon_handle)

def build_channel_list(channel_id):
    channel_json = get_channel_content(channel_id)
    channel_data = channel_json.get('data', {})
    if len(channel_data.get('items', [])) > 1:
        channel_items = list_items.get_channel_items(channel_json)
        if len(channel_items) > 0:
            xbmcplugin.setPluginCategory(addon_handle, channel_json.get('title', ''))
            xbmcplugin.addDirectoryItems(addon_handle, channel_items, len(channel_items))
            xbmcplugin.endOfDirectory(addon_handle)
    else:
        query = channel_data.get('query', {}).get('_id')
        return build_query_list(query, title=channel_json.get('title'))

def build_song_list(album_id):
    album_json = get_album_content(album_id)
    album_items = list_items.get_track_items(album_json)
    if len(album_items) > 0:
        xbmcplugin.setPluginCategory(addon_handle, album_json.get('title', ''))
        xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.setContent(addon_handle, 'songs')
        xbmcplugin.addDirectoryItems(addon_handle, album_items, len(album_items))
        xbmcplugin.endOfDirectory(addon_handle)

def play_song(url):
    play_item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def main():
    if addon.getSettingBool('first_run'):
        xbmcgui.Dialog().textviewer(get_string(30098), get_string(30099))
        if not list_items.matrix:
            explicit = xbmcgui.Dialog().yesno(get_string(30030), get_string(30032), defaultbutton=xbmcgui.DLG_YESNO_YES_BTN)
        else:
            explicit = xbmcgui.Dialog().yesno(get_string(30030), get_string(30032))
        # deceased = xbmcgui.Dialog().yesno(get_string(30040), get_string(30042), defaultbutton=xbmcgui.DLG_YESNO_YES_BTN)
        addon.setSettingBool('allow_explicit', explicit)
        # addon.setSettingBool('allow_deceased', deceased)
        addon.setSettingBool('first_run', False)
    args = parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)
    if mode is None:
        build_main_menu()
    elif mode[0] == 'explicit':
        xbmcgui.Dialog().notification(get_string(30033), get_string(30034))
    elif mode[0] == 'stream':
        play_song(args.get('url', [''])[0])
    elif mode[0] == 'list_radio':
        build_query_list(QUERY_RADIO)
    elif mode[0] == 'list_query':
        query_id = args.get('query_id', [''])[0]
        build_query_list(query_id)
    elif mode[0] == 'list_channel':
        channel_id = args.get('channel_id', [''])[0]
        build_channel_list(channel_id)
    elif mode[0] == 'list_songs':
        album_id = args.get('album_id', [''])[0]
        build_song_list(album_id)

def get_string(string_id):
    return addon.getLocalizedString(string_id)

if __name__ == '__main__':
    xbmc.log("indigiTUBE plugin called: " + str(sys.argv), xbmc.LOGDEBUG)
    addon = xbmcaddon.Addon()
    list_items = ListItems(addon)
    addon_handle = int(sys.argv[1])
    main()
