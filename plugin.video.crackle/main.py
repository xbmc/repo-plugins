from resources.lib.globals import *

params = get_params()
media_id = None
name = None
mode = None
stream_type = None
genre_id = None
page_num = 1
icon_url = ''

if 'id' in params:
    media_id = urllib.unquote_plus(params["id"])
if 'name' in params:
    name = urllib.unquote_plus(params["name"])
if 'mode' in params:
    mode = int(params["mode"])
if 'type' in params:
    stream_type = urllib.unquote_plus(params["type"])
if 'genre_id' in params:
    genre_id = urllib.unquote_plus(params["genre_id"])
if 'page_num' in params:
    page_num = int(params["page_num"])
if 'icon_url' in params:
    icon_url = urllib.unquote_plus(params["icon_url"])

if mode is None or mode == 1:
    main_menu()

elif mode == 99:
    list_genre(media_id)

elif mode == 100:
    if genre_id is not None:
        list_movies_shows(media_id, genre_id, page_num)

elif mode == 102:
    get_children(media_id, icon_url)

elif mode == 103:    
    if stream_type == 'movies':
        media_id = get_movie_id(media_id)
    get_stream(media_id)

elif mode == 104:
    dialog = xbmcgui.Dialog()
    search_phrase = dialog.input('Search Text', type=xbmcgui.INPUT_ALPHANUM)
    if search_phrase != "":
        search(search_phrase)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

if mode != 104:
    xbmcplugin.endOfDirectory(addon_handle)