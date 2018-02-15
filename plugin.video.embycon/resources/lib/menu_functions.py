# Gnu General Public License - see LICENSE.TXT

import sys
import json
import urllib
import encodings

import xbmcplugin
import xbmcaddon

from downloadutils import DownloadUtils
from kodi_utils import addMenuDirectoryItem
from simple_logging import SimpleLogging
from translation import i18n
from datamanager import DataManager

log = SimpleLogging(__name__)
downloadUtils = DownloadUtils()

__addon__ = xbmcaddon.Addon(id='plugin.video.embycon')


def showGenreList(item_type=None):
    log.debug("== ENTER: showGenreList() ==")

    server = downloadUtils.getServer()
    if server is None:
        return

    kodi_type = "Movies"
    emby_type = "Movie"
    if item_type is not None and item_type == "series":
        emby_type = "Series"
        kodi_type = "tvshows"

    url = ("{server}/emby/Genres?" +
             "SortBy=SortName" +
             "&SortOrder=Ascending" +
             "&IncludeItemTypes=" + emby_type +
             "&Recursive=true" +
             "&UserId={userid}" +
             "&format=json")

    data_manager = DataManager()
    result = data_manager.GetContent(url)

    if result is not None:
        result = result.get("Items")
    else:
        result = []

    collections = []

    for genre in result:
        item_data = {}
        item_data['title'] = genre.get("Name")
        item_data['media_type'] = kodi_type
        item_data['thumbnail'] = downloadUtils.getArtwork(genre, "Thumb", server=server)
        item_data['path'] = ('{server}/emby/Users/{userid}/Items?Fields={field_filters}' +
                             '&Recursive=true&GenreIds=' + genre.get("Id") +
                             '&IncludeItemTypes=' + emby_type +
                             '&ImageTypeLimit=1&format=json')
        collections.append(item_data)

    for collection in collections:
        url = sys.argv[0] + ("?url=" + urllib.quote(collection['path']) +
                             "&mode=GET_CONTENT" +
                             "&media_type=" + collection["media_type"])
        log.debug("addMenuDirectoryItem: {0} ({1})", collection.get('title'), url)
        addMenuDirectoryItem(collection.get('title', i18n('unknown')), url, thumbnail=collection.get("thumbnail"))

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def showMovieAlphaList():
    log.debug("== ENTER: showMovieAlphaList() ==")

    settings = xbmcaddon.Addon(id='plugin.video.embycon')
    server = downloadUtils.getServer()
    if server is None:
        return

    collections = []

    item_data = {}
    item_data['title'] = "#"
    item_data['media_type'] = "Movies"
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Fields={field_filters}' +
                         '&Recursive=true' +
                         '&NameLessThan=A' +
                         '&IncludeItemTypes=Movie' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    alphaList = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "Y", "Z"]

    for alphaName in alphaList:
        item_data = {}
        item_data['title'] = alphaName
        item_data['media_type'] = "Movies"
        item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                             '?Fields={field_filters}' +
                             '&Recursive=true' +
                             '&NameStartsWith=' + alphaName +
                             '&IncludeItemTypes=Movie' +
                             '&ImageTypeLimit=1&format=json')
        collections.append(item_data)

    for collection in collections:
        url = (sys.argv[0] + "?url=" + urllib.quote(collection['path']) +
               "&mode=GET_CONTENT&media_type=" + collection["media_type"])
        log.debug("addMenuDirectoryItem: {0} ({1})", collection.get('title'), url)
        addMenuDirectoryItem(collection.get('title', i18n('unknown')), url)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def showYearsList():

    server = downloadUtils.getServer()
    if server is None:
        return

    jsonData = downloadUtils.downloadUrl("{server}/emby/Years" +
                                         "?SortBy=SortName" +
                                         "&SortOrder=Descending" +
                                         "&IncludeItemTypes=Movie" +
                                         "&Recursive=true" +
                                         "&UserId={userid}" +
                                         "&format=json")
    log.debug("YEAR_LIST_DATA: {0}", jsonData)

    result = json.loads(jsonData)
    if result is not None:
        result = result.get("Items")
    else:
        result = []

    collections = []

    for year in result:
        item_data = {}
        item_data['title'] = year.get("Name")
        item_data['media_type'] = "Movies"
        #item_data['thumbnail'] = server + "/Years/" +  year.get("Name") + "/Images/Thumb"
        item_data['path'] = ('{server}/emby/Users/{userid}/Items'
                             '?Fields={field_filters}' +
                             '&Recursive=true' +
                             '&Years=' + year.get("Name") +
                             '&IncludeItemTypes=Movie' +
                             '&ImageTypeLimit=1' +
                             '&format=json')
        collections.append(item_data)

    for collection in collections:
        url = sys.argv[0] + ("?url=" + urllib.quote(collection['path']) +
                             "&mode=GET_CONTENT" +
                             "&media_type=" + collection["media_type"])
        log.debug("addMenuDirectoryItem: {0} ({1})", collection.get('title'), url)
        addMenuDirectoryItem(collection.get('title', i18n('unknown')), url)#, thumbnail=collection.get("thumbnail"))

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def displaySections():
    log.debug("== ENTER: displaySections() ==")
    xbmcplugin.setContent(int(sys.argv[1]), 'files')

    server = downloadUtils.getServer()
    if server is None:
        return

    # Add collections
    collections = getCollections()

    if collections:
        for collection in collections:
            url = (sys.argv[0] + "?url=" + urllib.quote(collection['path']) +
                   "&mode=GET_CONTENT&media_type=" + collection["media_type"])
            if collection.get("name_format") is not None:
                url += "&name_format=" + urllib.quote(collection.get("name_format"))
            log.debug("addMenuDirectoryItem: {0} ({1})", collection.get('title'), url)
            addMenuDirectoryItem(collection.get('title', i18n('unknown')), url, thumbnail=collection.get("thumbnail"))

        addMenuDirectoryItem(i18n('movies_year'), "plugin://plugin.video.embycon/?mode=MOVIE_YEARS")
        addMenuDirectoryItem(i18n('movies_genre'), "plugin://plugin.video.embycon/?mode=MOVIE_GENRE")
        addMenuDirectoryItem(i18n('movies_az'), "plugin://plugin.video.embycon/?mode=MOVIE_ALPHA")
        addMenuDirectoryItem(i18n('tvshow_genre'), "plugin://plugin.video.embycon/?mode=SERIES_GENRE")
        addMenuDirectoryItem(i18n('search'), "plugin://plugin.video.embycon/?mode=SEARCH")

        addMenuDirectoryItem(i18n('show_clients'), "plugin://plugin.video.embycon/?mode=SHOW_SERVER_SESSIONS")
        addMenuDirectoryItem(i18n('change_user'), "plugin://plugin.video.embycon/?mode=CHANGE_USER")

    addMenuDirectoryItem(i18n('detect_server'), "plugin://plugin.video.embycon/?mode=DETECT_SERVER_USER")
    addMenuDirectoryItem(i18n('show_settings'), "plugin://plugin.video.embycon/?mode=SHOW_SETTINGS")

    # only add these if we have other collection which means we have a valid server conn
    if collections:
        addMenuDirectoryItem(i18n('cache_textures'), "plugin://plugin.video.embycon/?mode=CACHE_ARTWORK")
        addMenuDirectoryItem(i18n('widgets'), "plugin://plugin.video.embycon/?mode=WIDGETS")

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def getCollections():
    log.debug("== ENTER: getCollections ==")

    server = downloadUtils.getServer()
    if server is None:
        return []

    userid = downloadUtils.getUserId()

    if userid == None or len(userid) == 0:
        log.debug("No userid so returning []")
        return []

    data_manager = DataManager()
    result = data_manager.GetContent("{server}/emby/Users/{userid}/Items/Root?format=json")
    if result is None:
        return []

    parentid = result.get("Id")
    log.debug("parentid: {0}", parentid)

    htmlpath = "{server}/emby/Users/{userid}/items?ParentId=" + parentid + "&Sortby=SortName&format=json"
    result = data_manager.GetContent(htmlpath)

    if result is not None:
        result = result.get("Items")
    else:
        result = []

    collections = []

    for item in result:
        item_name = item.get("Name")

        collection_type = item.get('CollectionType', None)
        log.debug("CollectionType: {0}", collection_type)
        log.debug("Title: {0}", item_name)

        if collection_type == "music":
            item_data = {}
            item_data['title'] = item_name + i18n('_all_albums')
            item_data['thumbnail'] = downloadUtils.getArtwork(item, "Primary", server=server)
            item_data['media_type'] = 'MusicAlbums'
            item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                                 '?Recursive=true' +
                                 '&ParentId=' + item.get("Id") +
                                 '&IncludeItemTypes=MusicAlbum' +
                                 '&ImageTypeLimit=1' +
                                 '&EnableImageTypes=Primary,Backdrop,Banner,Thumb' +
                                 '&format=json')
            collections.append(item_data)

            item_data = {}
            item_data['title'] = item_name + i18n('_all_artists')
            item_data['thumbnail'] = downloadUtils.getArtwork(item, "Primary", server=server)
            item_data['media_type'] = 'MusicArtists'
            item_data['path'] = ('{server}/emby/Artists/AlbumArtists' +
                                 '?Recursive=true' +
                                 '&ParentId=' + item.get("Id") +
                                 '&ImageTypeLimit=1' +
                                 '&EnableImageTypes=Primary,Backdrop,Banner,Thumb' +
                                 '&format=json')
            collections.append(item_data)

        if collection_type in ["tvshows", "movies", "boxsets"]:
            collections.append({
                'title': item_name,
                'thumbnail': downloadUtils.getArtwork(item, "Primary", server=server),
                'path': ('{server}/emby/Users/{userid}/Items' +
                         '?ParentId=' + item.get("Id") +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&Fields={field_filters}' +
                         '&ImageTypeLimit=1' +
                         '&format=json'),
                'media_type': collection_type})

        if collection_type == "tvshows":
            collections.append({
                'title': item_name + i18n('_unwatched'),
                'thumbnail': downloadUtils.getArtwork(item, "Primary", server=server),
                'path': ('{server}/emby/Users/{userid}/Items' +
                         '?ParentId=' + item.get("Id") +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&Fields={field_filters}' +
                         '&Filters=IsUnplayed' +
                         '&Recursive=true' +
                         '&IncludeItemTypes=Series' +
                         '&ImageTypeLimit=1' +
                         '&format=json'),
                'media_type': 'tvshows'})
            collections.append({
                'title': item_name + i18n('_in_progress'),
                'thumbnail': downloadUtils.getArtwork(item, "Primary", server=server),
                'path': ('{server}/emby/Users/{userid}/Items' +
                         '?ParentId=' + item.get("Id") +
                         '&Limit={ItemLimit}' +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&Fields={field_filters}' +
                         '&Filters=IsResumable' +
                         '&Recursive=true' +
                         '&IncludeItemTypes=Episode' +
                         '&ImageTypeLimit=1' +
                         '&format=json'),
                'media_type': 'Episodes',
                'name_format': 'Episode|episode_name_format'})
            collections.append({
                'title': item_name + i18n('_latest'),
                'thumbnail': downloadUtils.getArtwork(item, "Primary", server=server),
                'path': ('{server}/emby/Users/{userid}/Items/Latest' +
                         '?ParentId=' + item.get("Id") +
                         '&Limit={ItemLimit}' +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&Fields={field_filters}' +
                         '&SortBy=DateCreated' +
                         '&SortOrder=Descending' +
                         '&Filters=IsUnplayed' +
                         '&Recursive=true' +
                         '&IncludeItemTypes=Episode' +
                         '&ImageTypeLimit=1' +
                         '&format=json'),
                'media_type': 'Episodes',
                'name_format': 'Episode|episode_name_format'})            
            collections.append({
                'title': item_name + i18n('_recently_added'),
                'thumbnail': downloadUtils.getArtwork(item, "Primary", server=server),
                'path': ('{server}/emby/Users/{userid}/Items' +
                         '?ParentId=' + item.get("Id") +
                         '&Limit={ItemLimit}' +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&Fields={field_filters}' +
                         '&SortBy=DateCreated' +
                         '&SortOrder=Descending' +
                         '&Filters={IsUnplayed,}IsNotFolder' +
                         '&Recursive=true' +
                         '&IncludeItemTypes=Episode' +
                         '&ImageTypeLimit=1' +
                         '&format=json'),
                'media_type': 'Episodes',
                'name_format': 'Episode|episode_name_format'})
            collections.append({
                'title': item_name + i18n('_next_up'),
                'thumbnail': downloadUtils.getArtwork(item, "Primary", server=server),
                'path': ('{server}/emby/Shows/NextUp/?Userid={userid}' +
                         '&ParentId=' + item.get("Id") +
                         '&Limit={ItemLimit}' +
                         '&Recursive=true' +
                         '&Fields={field_filters}' +
                         '&Filters=IsUnplayed,IsNotFolder' +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&IncludeItemTypes=Episode' +
                         '&ImageTypeLimit=1' +
                         '&format=json'),
                'media_type': 'Episodes',
                'name_format': 'Episode|episode_name_format'})

        if collection_type == "movies":
            collections.append({
                'title': item_name + i18n('_unwatched'),
                'thumbnail': downloadUtils.getArtwork(item, "Primary", server=server),
                'path': ('{server}/emby/Users/{userid}/Items' +
                         '?ParentId=' + item.get("Id") +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&Fields={field_filters}' +
                         '&Filters=IsUnplayed' +
                         '&ImageTypeLimit=1' +
                         '&format=json'),
                'media_type': collection_type})
            collections.append({
                'title': item_name + i18n('_in_progress'),
                'thumbnail': downloadUtils.getArtwork(item, "Primary", server=server),
                'path': ('{server}/emby/Users/{userid}/Items' +
                         '?ParentId=' + item.get("Id") +
                         '&Limit={ItemLimit}' +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&Fields={field_filters}' +
                         '&Filters=IsResumable' +
                         '&ImageTypeLimit=1' +
                         '&format=json'),
                'media_type': collection_type})
            collections.append({
                'title': item_name + i18n('_recently_added'),
                'thumbnail': downloadUtils.getArtwork(item, "Primary", server=server),
                'path': ('{server}/emby/Users/{userid}/Items' +
                         '?ParentId=' + item.get("Id") +
                         '&Limit={ItemLimit}' +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&Fields={field_filters}' +
                         '&SortBy=DateCreated' +
                         '&SortOrder=Descending' +
                         '&Filters={IsUnplayed,}IsNotFolder' +
                         '&ImageTypeLimit=1' +
                         '&format=json'),
                'media_type': collection_type})

    # Add standard nodes
    item_data = {}
    item_data['title'] = i18n('movies_all')
    item_data['media_type'] = 'Movies'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Fields={field_filters}' +
                         '&Recursive=true' +
                         '&IncludeItemTypes=Movie' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('movies_unwatched')
    item_data['media_type'] = 'Movies'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Recursive=true' +
                         '&Fields={field_filters}' +
                         '&Filters=IsUnplayed' +
                         '&IncludeItemTypes=Movie' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('movies_in_progress')
    item_data['media_type'] = 'Movies'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Limit={ItemLimit}' +
                         '&Recursive=true' +
                         '&Fields={field_filters}' +
                         '&Filters=IsResumable' +
                         '&IncludeItemTypes=Movie' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('movies_recently_added')
    item_data['media_type'] = 'Movies'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Limit={ItemLimit}' +
                         '&Recursive=true' +
                         '&SortBy=DateCreated' +
                         '&Fields={field_filters}' +
                         '&SortOrder=Descending' +
                         '&Filters={IsUnplayed,}IsNotFolder' +
                         '&IncludeItemTypes=Movie' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('movies_favorites')
    item_data['media_type'] = 'Movies'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Fields={field_filters}' +
                         '&Recursive=true' +
                         '&Filters=IsFavorite' +
                         '&IncludeItemTypes=Movie' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('movies_boxsets')
    item_data['media_type'] = 'BoxSets'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Recursive=true' +
                         '&Fields={field_filters}' +
                         '&IncludeItemTypes=BoxSet' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('tvshows_all')
    item_data['media_type'] = 'tvshows'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Fields={field_filters}' +
                         '&Recursive=true' +
                         '&IncludeItemTypes=Series' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('tvshows_unwatched')
    item_data['media_type'] = 'tvshows'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Fields={field_filters}' +
                         '&Recursive=true' +
                         '&Filters=IsUnplayed' +
                         '&IncludeItemTypes=Series' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('tvshows_favorites')
    item_data['media_type'] = 'tvshows'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Fields={field_filters}' +
                         '&Recursive=true' +
                         '&Filters=IsFavorite' +
                         '&IncludeItemTypes=Series' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('tvshows_latest')
    item_data['media_type'] = 'Episodes'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items/Latest' +
                         '?Limit={ItemLimit}' +
                         '&Recursive=true' +
                         '&GroupItems=true' +
                         '&SortBy=DateCreated' +
                         '&Fields={field_filters}' +
                         '&SortOrder=Descending' +
                         '&Filters={IsUnplayed}' +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&IncludeItemTypes=Episode' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    item_data['name_format'] = 'Episode|episode_name_format'
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('episodes_in_progress')
    item_data['media_type'] = 'Episodes'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Limit={ItemLimit}' +
                         '&Recursive=true' +
                         '&Fields={field_filters}' +
                         '&Filters=IsResumable' +
                         '&IncludeItemTypes=Episode' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    item_data['name_format'] = 'Episode|episode_name_format'
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('episodes_recently_added')
    item_data['media_type'] = 'Episodes'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Limit={ItemLimit}' +
                         '&Recursive=true' +
                         '&SortBy=DateCreated' +
                         '&Fields={field_filters}' +
                         '&SortOrder=Descending' +
                         '&Filters={IsUnplayed,}IsNotFolder' +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&IncludeItemTypes=Episode' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    item_data['name_format'] = 'Episode|episode_name_format'
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('episodes_up_next')
    item_data['media_type'] = 'Episodes'
    item_data['path'] = ('{server}/emby/Shows/NextUp/?Userid={userid}' +
                         '&Limit={ItemLimit}' +
                         '&Recursive=true' +
                         '&Fields={field_filters}' +
                         '&Filters=IsUnplayed,IsNotFolder' +
                         '&IsVirtualUnaired=false' +
                         '&IsMissing=False' +
                         '&IncludeItemTypes=Episode' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    item_data['name_format'] = 'Episode|episode_name_format'
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('upcoming_tv')
    item_data['media_type'] = 'Episodes'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Recursive=true' +
                         '&SortBy=PremiereDate' +
                         '&Fields={field_filters}' +
                         '&SortOrder=Ascending' +
                         '&IsVirtualUnaired=true' +
                         '&IsNotFolder' +
                         '&IncludeItemTypes=Episode' +
                         '&ImageTypeLimit=1' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('music_all_albums')
    item_data['media_type'] = 'MusicAlbums'
    item_data['path'] = ('{server}/emby/Users/{userid}/Items' +
                         '?Recursive=true' +
                         '&IncludeItemTypes=MusicAlbum' +
                         '&ImageTypeLimit=1' +
                         '&EnableImageTypes=Primary,Backdrop,Banner,Thumb' +
                         '&format=json')
    collections.append(item_data)

    item_data = {}
    item_data['title'] = i18n('music_all_artists')
    item_data['media_type'] = 'MusicArtists'
    item_data['path'] = ('{server}/emby/Artists/AlbumArtists' +
                         '?Recursive=true' +
                         '&ImageTypeLimit=1' +
                         '&EnableImageTypes=Primary,Backdrop,Banner,Thumb' +
                         '&format=json')
    collections.append(item_data)


    return collections


def showWidgets():
    addMenuDirectoryItem(i18n('emby_movies'), 'plugin://plugin.video.embycon/?mode=SHOW_CONTENT&item_type=Movie&media_type=Movies')
    addMenuDirectoryItem(i18n('emby_tvshows'), 'plugin://plugin.video.embycon/?mode=SHOW_CONTENT&item_type=Series&media_type=TVShows')

    addMenuDirectoryItem(i18n('movies_recently_added'), 'plugin://plugin.video.embycon/?mode=WIDGET_CONTENT&type=recent_movies')
    addMenuDirectoryItem(i18n('movies_in_progress'), 'plugin://plugin.video.embycon/?mode=WIDGET_CONTENT&type=inprogress_movies')
    addMenuDirectoryItem(i18n('movies_random'), 'plugin://plugin.video.embycon/?mode=WIDGET_CONTENT&type=random_movies')
    addMenuDirectoryItem(i18n('episodes_recently_added'), 'plugin://plugin.video.embycon/?mode=WIDGET_CONTENT&type=recent_episodes')
    addMenuDirectoryItem(i18n('episodes_in_progress'), 'plugin://plugin.video.embycon/?mode=WIDGET_CONTENT&type=inprogress_episodes')
    addMenuDirectoryItem(i18n('episodes_up_next'), 'plugin://plugin.video.embycon/?mode=WIDGET_CONTENT&type=nextup_episodes')

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def showSearch():
    addMenuDirectoryItem(i18n('movies'), 'plugin://plugin.video.embycon/?mode=NEW_SEARCH&item_type=Movie')
    addMenuDirectoryItem(i18n('tvshows'), 'plugin://plugin.video.embycon/?mode=NEW_SEARCH&item_type=Series')
    addMenuDirectoryItem(i18n('episodes'), 'plugin://plugin.video.embycon/?mode=NEW_SEARCH&item_type=Episode')

    xbmcplugin.endOfDirectory(int(sys.argv[1]))
