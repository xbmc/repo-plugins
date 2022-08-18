# -*- coding: utf-8 -*-
# Module: plugin
# Author: crmartinez
# Colaborator: oleksis
# Created on: 18.3.2021
# Modified on: 10.7.2022


import sys
from typing import TYPE_CHECKING, Any, Dict, List
from urllib.parse import parse_qsl, unquote_plus, urlencode

import requests
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

# TODO: Refactor model to class and categories like routess
#       url = "plugin://plugin.video.picta/search/?action=newSearch&query=%s" % query
# TODO: Search history cache
# TODO: Manage requests.exceptions.ConnectionError

# Get the plugin url in plugin:// notation.
_URL = sys.argv[0]
# Get the plugin handle as an integer number.

try:
    _HANDLE = int(sys.argv[1])
except ValueError:
    _HANDLE = -1

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    Video = TypedDict(
        "Video",
        {
            "name": str,
            "thumb": str,
            "video": str,
            "genre": str,
            "plot": str,
            "sub": str,
        },
    )

    Serie = TypedDict(
        "Serie",
        {
            "name": str,
            "id": str,
            "thumb": str,
            "genre": str,
            "cant_temp": str,
        },
    )

    Canal = TypedDict(
        "Canal",
        {
            "name": str,
            "id": str,
            "thumb": str,
            "plot": str,
        },
    )

Categoria = int

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo("id")
addon_base = f"plugin://{addon_id}"
addon_profile_path = xbmcvfs.translatePath(addon.getAddonInfo("profile"))

# For i18n
CANALES = 30901
DOCUMENTALES = 30902
PELICULAS = 30903
MUSICALES = 30904
SERIES = 30905
NEXT = 30913
SEARCH = 30101
NEW_SEARCH = 30201
CATEGORIAS = 30104

COLLECTION: Dict[Any, Any] = {
    CANALES: [],
    DOCUMENTALES: [],
    PELICULAS: [],
    MUSICALES: [],
    SERIES: [],
    SEARCH: [],
    "next_href": 1,
}

ROOT_BASE_URL = "https://www.picta.cu/"
API_BASE_URL = "https://api.picta.cu/v2/"


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    # Get the plugin url in plugin:// notation.
    return f"{_URL}?{urlencode(kwargs)}"


def get_categories() -> List[Categoria]:

    """
    Get the list of video categories.

    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or API.

    .. note:: Consider using `generator functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :return: The list of video categories
    :rtype: list
    """
    return list(COLLECTION.keys())[:-1]


def get_likes(video: "Video") -> str:
    reproducciones = video.get("cantidad_reproducciones", 0)
    me_gusta = video.get("cantidad_me_gusta", 0)
    no_me_gusta = video.get("cantidad_no_me_gusta", 0)
    comentarios = video.get("cantidad_comentarios", 0)
    descargas = video.get("cantidad_descargas", 0)

    return f"► {reproducciones} · ♥ {me_gusta} · ▼ {descargas}"


def get_videos(
    category: int, next_page: int = COLLECTION["next_href"]
) -> List["Video"]:
    """
    Get the list of videofiles/streams.

    Here you can insert some parsing code that retrieves
    the list of video streams in the given category from some site or API.

    .. note:: Consider using `generators functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :param category: Category id
    :type category: int

    :return: the list of videos in the category
    :rtype: list
    """
    result = {}
    COLLECTION[category] = []

    if category == DOCUMENTALES:
        url_docum = f"{API_BASE_URL}publicacion/?page={next_page}&page_size=10&tipologia_nombre_raw=Documental&ordering=-fecha_creacion"
        r = requests.get(url_docum)
        result = r.json()
    elif category == PELICULAS:
        url_pelic = f"{API_BASE_URL}publicacion/?page={next_page}&page_size=10&tipologia_nombre_raw=Pel%C3%ADcula&ordering=-fecha_creacion"
        r = requests.get(url_pelic)
        result = r.json()
    elif category == MUSICALES:
        url_musicales = f"{API_BASE_URL}publicacion/?page={next_page}&page_size=10&tipologia_nombre_raw=Video%20Musical&ordering=-fecha_creacion"
        r = requests.get(url_musicales)
        result = r.json()

    for v in result["results"]:
        generos = ""
        likes = get_likes(v)

        if category == MUSICALES:
            generos = ", ".join(g["nombre"] for g in v["categoria"]["video"]["genero"])
        elif category == PELICULAS:
            generos = ", ".join(
                g["nombre"] for g in v["categoria"]["pelicula"]["genero"]
            )

        COLLECTION[category].append(
            {
                "name": f'{v["nombre"]}\n{likes}',
                "thumb": v["url_imagen"] + "_380x250",
                "video": v["url_manifiesto"],
                "genre": generos,
                "plot": v["descripcion"],
                "sub": v["url_subtitulo"],
            }
        )

    COLLECTION["next_href"] = int(result.get("next") or 0)

    return COLLECTION[category]


def get_series(next_page: int = COLLECTION["next_href"]) -> List["Serie"]:
    """
    Get list of Series

    :return: the list of Series
    :rtype: list
    """

    COLLECTION[SERIES] = []
    url_series = f"{API_BASE_URL}serie/?page={next_page}&page_size=10&ordering=-id"
    r = requests.get(url_series)
    result = r.json()

    for v in result["results"]:
        generos = ", ".join(g["nombre"] for g in v["genero"])

        COLLECTION[SERIES].append(
            {
                "name": v["nombre"],
                "id": v["pelser_id"],
                "thumb": v["imagen_secundaria"] + "_380x250",
                "genre": generos,
                "cant_temp": v["cantidad_temporadas"],
            }
        )

    COLLECTION["next_href"] = int(result.get("next") or 0)

    return COLLECTION[SERIES]


def get_episodes(id: str, temp: str) -> List["Video"]:
    """
    Get list of Episodes

    param id: Serie´s ID
    :type id: str

    :param temp: Index of Season
    :type temp: str

    :return: the list of episodes
    :rtype: list
    """
    EPISODIOS: List["Video"] = []
    url_temp = f"{API_BASE_URL}temporada/?serie_pelser_id={id}&ordering=nombre"
    r = requests.get(url_temp)
    result = r.json()

    try:
        t = int(temp)
        temp_id = result["results"][t]["id"]
        size = result["results"][t]["cantidad_capitulos"]

        url_publicacion = f"{API_BASE_URL}publicacion/?temporada_id={temp_id}&page=1&page_size={size}&ordering=nombre"
        r = requests.get(url_publicacion)
        result = r.json()

        for e in result["results"]:
            generos = ", ".join(
                g["nombre"]
                for g in e["categoria"]["capitulo"]["temporada"]["serie"]["genero"]
            )
            likes = get_likes(e)

            EPISODIOS.append(
                {
                    "name": f'{e["nombre"]}\n{likes}',
                    "thumb": e["url_imagen"] + "_380x250",
                    "video": e["url_manifiesto"],
                    "genre": generos,
                    "plot": e["descripcion"],
                    "sub": e["url_subtitulo"],
                }
            )
    except IndexError:
        xbmc.executebuiltin(
            "Notification(Aviso,La temporada todavía no se encuentra disponible,5000)"
        )

    return EPISODIOS


def get_canales(next_page: int = COLLECTION["next_href"]) -> List["Canal"]:
    """
    Get lis of Channels

    :param next_page: Next page
    :type next_page: int

    :return: the list of Channels
    :rtype: list
    """

    COLLECTION[CANALES] = []
    url_canales = f"{API_BASE_URL}canal/?page={next_page}&page_size=10&ordering=-cantidad_suscripciones"
    r = requests.get(url_canales)
    result = r.json()

    for ch in result["results"]:
        COLLECTION[CANALES].append(
            {
                "name": ch["nombre"],
                "id": ch["id"],
                "thumb": ch["url_imagen"] + "_380x250",
                "plot": ch["descripcion"],
            }
        )

    COLLECTION["next_href"] = int(result.get("next") or 0)

    return COLLECTION[CANALES]


def get_canales_videos(
    canal_nombre_raw: str, next_page: int = COLLECTION["next_href"]
) -> List["Video"]:
    """
    Get list of Channels´s videos

    :param canal_nombre_raw: Unquote Channel´s name
    :type canal_nombre_raw: str

    :return: the list of videos in the Channel
    :rtype: list
    """
    VIDEOS: List["Video"] = []

    url_canal_videos = f"{API_BASE_URL}publicacion/?canal_nombre_raw={canal_nombre_raw}&page={next_page}&page_size=10"
    r = requests.get(url_canal_videos)
    result = r.json()

    for v in result["results"]:
        # Videos diferentes tipologias no siempre tienen genero
        likes = get_likes(v)
        VIDEOS.append(
            {
                "name": f'{v["nombre"]}\n{likes}',
                "thumb": v["url_imagen"] + "_380x250",
                "video": v["url_manifiesto"],
                "genre": "",
                "plot": v["descripcion"],
                "sub": v["url_subtitulo"],
            }
        )

    COLLECTION["next_href"] = int(result.get("next") or 0)

    return VIDEOS


def get_search(query: str, next_page: int = COLLECTION["next_href"]) -> List["Video"]:
    """
    Get list of videos from search

    :param query: Search query
    :type query: str

    :return: the list of videos from search
    :rtype: list
    """
    COLLECTION[SEARCH] = []

    url_search = (
        f"{API_BASE_URL}s/buscar/?criterio={query}&page={next_page}&page_size=10"
    )
    r = requests.get(url_search)
    result = r.json()

    for v in result["results"]:
        # TODO: Search by kind/tipo de contenido: canal, serie, etc
        if v["tipo"] == "publicacion":
            # Videos diferentes tipologias no siempre tienen genero
            likes = get_likes(v)
            COLLECTION[SEARCH].append(
                {
                    "name": f'{v["nombre"]}\n{likes}',
                    "thumb": v["url_imagen"] + "_380x250",
                    "video": v["url_manifiesto"],
                    "genre": "",
                    "plot": v["descripcion"],
                    "sub": v["url_subtitulo"],
                }
            )

    COLLECTION["next_href"] = int(result.get("next") or 0)

    return COLLECTION[SEARCH]


def list_categories() -> None:
    """
    Create the list of video categories in the Kodi interface.
    """
    xbmcplugin.setPluginCategory(_HANDLE, addon.getLocalizedString(CATEGORIAS))
    categories = get_categories()

    for category in categories:
        list_item = xbmcgui.ListItem(label=addon.getLocalizedString(category))
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.picta/?action=listing&category=30905
        url = get_url(action="listing", category=category)
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    # xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


def set_video_list(video: "Video") -> None:
    """
    Set Info and Directory to ListItem

    :param video: Video Dict
    :type video: Dict

    """
    list_item = xbmcgui.ListItem(label=video["name"])
    list_item.setInfo(
        "video",
        {
            "title": video["name"],
            "genre": video["genre"],
            "plot": video["plot"],
            "mediatype": "video",
        },
    )
    list_item.setSubtitles([video["sub"]])
    list_item.setArt(
        {"thumb": video["thumb"], "icon": video["thumb"], "fanart": video["thumb"]}
    )
    list_item.setProperty("IsPlayable", "true")
    url = get_url(action="play", video=video["video"])
    is_folder = False
    xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)


def add_next_page(**kwargs) -> None:
    """
    Add a ListItem to the Kodi interface to show the next page.

    :param category_id: Category ID
    :type category_id: int
    """
    if COLLECTION["next_href"] > 1:
        list_item = xbmcgui.ListItem(label=addon.getLocalizedString(NEXT))
        url = get_url(**kwargs)
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)


def list_videos_channels(
    category, category_label: str, videos: List["Video"], query=""
) -> None:
    """
    Create the list of playable videos in the Kodi interface.

    :param category_id: Category ID
    :type category_id: int
    :param category_label: label name
    :type category_label: str
    :param videos: list of videos
    :type videos: list[Video]
    """
    xbmcplugin.setPluginCategory(_HANDLE, category_label)

    for video in videos:
        set_video_list(video)

    if category == 0:
        add_next_page(
            action="getChannelVideos",
            canal_nombre_raw=category_label,
            next_href=str(COLLECTION["next_href"]),
        )
    elif category == SEARCH:
        add_next_page(
            action="newSearch",
            query=query,
            next_href=str(COLLECTION["next_href"]),
        )
    else:
        add_next_page(
            action="listing", category=category, next_href=str(COLLECTION["next_href"])
        )

    xbmcplugin.endOfDirectory(_HANDLE)


def list_series(category: int, next_page: int = COLLECTION["next_href"]) -> None:
    """Create list of Series"""
    xbmcplugin.setPluginCategory(_HANDLE, addon.getLocalizedString(SERIES))

    xbmcplugin.setContent(_HANDLE, "tvshows")

    series = get_series(next_page)

    for serie in series:
        list_item = xbmcgui.ListItem(label=serie["name"])
        list_item.setInfo(
            "video",
            {"title": serie["name"], "genre": serie["genre"], "mediatype": "tvshow"},
        )
        list_item.setArt(
            {"thumb": serie["thumb"], "icon": serie["thumb"], "fanart": serie["thumb"]}
        )
        url = get_url(
            action="getSeasons",
            id=serie["id"],
            temp=serie["cant_temp"],
            name=serie["name"],
        )
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)

    add_next_page(
        action="listing", category=category, next_href=str(COLLECTION["next_href"])
    )

    # xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.endOfDirectory(_HANDLE)


def list_canales(category: int, next_page: int = COLLECTION["next_href"]) -> None:
    """Create list of Channels"""
    xbmcplugin.setPluginCategory(_HANDLE, addon.getLocalizedString(CANALES))

    canales = get_canales(next_page)

    for canal in canales:
        list_item = xbmcgui.ListItem(label=canal["name"])
        list_item.setInfo(
            "video",
            {"title": canal["name"], "plot": canal["plot"], "mediatype": "video"},
        )
        list_item.setArt(
            {"thumb": canal["thumb"], "icon": canal["thumb"], "fanart": canal["thumb"]}
        )
        url = get_url(action="getChannelVideos", canal_nombre_raw=canal["name"])
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)

    add_next_page(
        action="listing", category=category, next_href=str(COLLECTION["next_href"])
    )

    # xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.endOfDirectory(_HANDLE)


def list_seasons(pelser_id: str, temporada: str, name: str) -> None:
    """
    Create list of Seasons

    :param pelser_id: ID of the Serie
    :type pelser_id: str

    :param temporada: Count of Seasons
    :type temporada: str

    :param name: Serie´s name
    :type name: str
    """
    xbmcplugin.setPluginCategory(_HANDLE, name)
    xbmcplugin.setContent(_HANDLE, "season")
    # Note:
    # La cantidad_temporadas para una serie no está actualizada mediante la API
    # Ejemplo:
    #   Serie = {"pelser_id": 107, "nombre": "Rick and Morty", "cantidad_temporadas": 4}
    # Si consultas {{temporadaBySerieEndpoint}} "count": 5,
    cant_temp = int(temporada) + 1

    for i in range(cant_temp):
        temp_name = f"Temporada {i + 1}"
        list_item = xbmcgui.ListItem(label=temp_name)
        url = get_url(action="getEpisodes", serie_id=pelser_id, temp=i, name=temp_name)
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(_HANDLE)


def list_episodes(serie_id: str, temp: str, name: str) -> None:
    """
    Create list of Episodes

    :param serie_id: Serie´s ID
    :type serie_id: str

    :param temp: Index of Season
    :type temp: str

    :param name: Season´s name
    :type name: str
    """
    xbmcplugin.setPluginCategory(_HANDLE, name)
    xbmcplugin.setContent(_HANDLE, "episodes")

    episodes = get_episodes(serie_id, temp)

    for video in episodes:
        set_video_list(video)

    xbmcplugin.endOfDirectory(_HANDLE)


def list_search_root(category: int) -> None:
    """
    Show search root menu

    :param category: Category of search
    :type category: int
    """
    xbmcplugin.setPluginCategory(_HANDLE, addon.getLocalizedString(category))
    list_item = xbmcgui.ListItem(label=addon.getLocalizedString(NEW_SEARCH))
    url = get_url(action="newSearch")
    is_folder = True
    xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_HANDLE)


def play_video(path: str) -> None:
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # TODO: Add support for HLS(m3u8) like IPTV
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    play_item.setContentLookup(False)
    play_item.setMimeType("application/xml+dash")
    play_item.setProperty("inputstream", "inputstream.adaptive")
    play_item.setProperty("inputstream.adaptive.manifest_type", "mpd")
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=play_item)


def router(paramstring: str) -> None:
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str

    :Raises
    ValueError if invalid paramstring
    """
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_HANDLE, "videos")

    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        next_page = int(params.get("next_href") or 1)

        if params["action"] == "listing":
            # Display the list of videos in a provided category.
            category_id = int(params["category"])

            if category_id == SEARCH:
                list_search_root(category_id)
            elif category_id == SERIES:
                list_series(category_id, next_page)
            elif category_id == CANALES:
                list_canales(category_id, next_page)
            else:
                category_label = addon.getLocalizedString(category_id)
                videos = get_videos(category_id, next_page)
                list_videos_channels(category_id, category_label, videos)
        elif params["action"] == "getSeasons":
            list_seasons(params["id"], params["temp"], params["name"])
        elif params["action"] == "getEpisodes":
            list_episodes(params["serie_id"], params["temp"], params["name"])
        elif params["action"] == "getChannelVideos":
            category_id = 0
            canal_nombre_raw: str = unquote_plus(params["canal_nombre_raw"])
            videos = get_canales_videos(canal_nombre_raw, next_page)
            list_videos_channels(category_id, canal_nombre_raw, videos)
        elif params["action"] == "newSearch":
            query = params.get("query")
            if not query:
                query = xbmcgui.Dialog().input(addon.getLocalizedString(SEARCH))
            if query:
                videos = get_search(query, next_page)
                list_videos_channels(
                    SEARCH, addon.getLocalizedString(SEARCH), videos, query
                )
        elif params["action"] == "play":
            # Play a video from a provided URL.
            play_video(params["video"])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError(
                "Invalid paramstring: {0} debug: {1}".format(paramstring, params)
            )
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


def run() -> None:
    """Main entrypoint"""
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
