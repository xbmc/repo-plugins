from resources.lib.globals import *

params = get_params()
media_id = None
name = None
mode = None
stream_type = None
genre_id = None

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

if mode is None:
    main_menu()

elif mode == 99:
    list_genre(media_id)

elif mode == 100:
    if genre_id is not None:
        if media_id == 'shows':
            list_shows(genre_id)
        elif media_id == 'movies':
            list_movies(genre_id)

# elif mode == 101:
#     list_movies()

elif mode == 102:
    get_episodes(media_id)

elif mode == 103:
    if stream_type == "movies": media_id = get_movie_id(media_id)
    get_stream(media_id)


xbmcplugin.endOfDirectory(addon_handle)