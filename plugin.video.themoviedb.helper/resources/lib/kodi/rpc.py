import xbmc
import json
from resources.lib.addon.plugin import kodi_log
from resources.lib.addon.parser import try_int
from resources.lib.addon.setutils import find_dict_in_list
from resources.lib.kodi.mapping import ItemMapper


def get_jsonrpc(method=None, params=None):
    if not method:
        return {}
    query = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1}
    if params:
        query["params"] = params
    try:
        jrpc = xbmc.executeJSONRPC(json.dumps(query))
        response = json.loads(jrpc)
    except Exception as exc:
        kodi_log(u'TMDbHelper - JSONRPC Error:\n{}'.format(exc), 1)
        response = {}
    return response


def get_kodi_library(tmdb_type, tvshowid=None):
    if tmdb_type == 'movie':
        return KodiLibrary(dbtype='movie')
    if tmdb_type == 'tv':
        return KodiLibrary(dbtype='tvshow')
    if tmdb_type in ['season', 'episode'] and tvshowid:
        return KodiLibrary(dbtype=tmdb_type, tvshowid=tvshowid)
    if tmdb_type == 'both':
        return KodiLibrary(dbtype='both')


def get_library(dbtype=None, properties=None, filterr=None):
    if dbtype == "movie":
        method = "VideoLibrary.GetMovies"
    elif dbtype == "tvshow":
        method = "VideoLibrary.GetTVShows"
    elif dbtype == "episode":
        method = "VideoLibrary.GetEpisodes"
    else:
        return

    params = {"properties": properties or ["title"]}
    if filterr:
        params['filter'] = filterr

    response = get_jsonrpc(method, params)
    return response.get('result')


def get_num_credits(dbtype, person):
    if dbtype == 'movie':
        filterr = {
            "or": [
                {"field": "actor", "operator": "contains", "value": person},
                {"field": "director", "operator": "contains", "value": person},
                {"field": "writers", "operator": "contains", "value": person}]}
    elif dbtype == 'tvshow':
        filterr = {
            "or": [
                {"field": "actor", "operator": "contains", "value": person},
                {"field": "director", "operator": "contains", "value": person}]}
    elif dbtype == 'episode':
        filterr = {
            "or": [
                {"field": "actor", "operator": "contains", "value": person},
                {"field": "director", "operator": "contains", "value": person},
                {"field": "writers", "operator": "contains", "value": person}]}
    else:
        return
    response = get_library(dbtype, filterr=filterr)
    return response.get('limits', {}).get('total', 0) if response else 0


def get_person_stats(person):
    infoproperties = {}
    infoproperties['numitems.dbid.movies'] = get_num_credits('movie', person)
    infoproperties['numitems.dbid.tvshows'] = get_num_credits('tvshow', person)
    infoproperties['numitems.dbid.episodes'] = get_num_credits('episode', person)
    infoproperties['numitems.dbid.total'] = (
        try_int(infoproperties.get('numitems.dbid.movies'))
        + try_int(infoproperties.get('numitems.dbid.tvshows'))
        + try_int(infoproperties.get('numitems.dbid.episodes')))
    return infoproperties


def set_watched(dbid=None, dbtype=None, plays=1):
    if not dbid or not dbtype:
        return
    db_key = u"{}id".format(dbtype)
    json_info = get_jsonrpc(
        method=u"VideoLibrary.Get{}Details".format(dbtype.capitalize()),
        params={db_key: dbid, "properties": ["playcount"]})
    playcount = json_info.get('result', {}).get('{}details'.format(dbtype), {}).get('playcount', 0)
    playcount = try_int(playcount) + plays
    return get_jsonrpc(
        method=u"VideoLibrary.Set{}Details".format(dbtype.capitalize()),
        params={db_key: dbid, "playcount": playcount})


def get_directory(url):
    method = "Files.GetDirectory"
    params = {
        "directory": url,
        "media": "files",
        "properties": [
            "title", "year", "originaltitle", "imdbnumber", "premiered", "streamdetails", "size",
            "firstaired", "season", "episode", "showtitle", "file", "tvshowid", "thumbnail"]}
    response = get_jsonrpc(method, params)
    return response.get('result', {}).get('files', [{}]) or [{}]


def _get_item_details(dbid=None, method=None, key=None, properties=None):
    if not dbid or not method or not key or not properties:
        return {}
    params = {
        u"{0}id".format(key): try_int(dbid),
        "properties": properties}
    details = get_jsonrpc(method, params)
    if not details or not isinstance(details, dict):
        return {}
    details = details.get('result', {}).get(u'{0}details'.format(key))
    if details:
        details['dbid'] = dbid
        return ItemMapper(key=key).get_info(details)


def get_movie_details(dbid=None):
    properties = [
        "title", "genre", "year", "rating", "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle",
        "lastplayed", "playcount", "writer", "studio", "mpaa", "cast", "country", "imdbnumber", "runtime", "set",
        "showlink", "streamdetails", "top250", "votes", "fanart", "thumbnail", "file", "sorttitle", "resume", "setid",
        "dateadded", "tag", "art", "userrating", "ratings", "premiered", "uniqueid"]
    return _get_item_details(dbid=dbid, method="VideoLibrary.GetMovieDetails", key="movie", properties=properties)


def get_tvshow_details(dbid=None):
    properties = [
        "title", "genre", "year", "rating", "plot", "studio", "mpaa", "cast", "playcount", "episode", "imdbnumber",
        "premiered", "votes", "lastplayed", "fanart", "thumbnail", "file", "originaltitle", "sorttitle", "episodeguide",
        "season", "watchedepisodes", "dateadded", "tag", "art", "userrating", "ratings", "runtime", "uniqueid"]
    return _get_item_details(dbid=dbid, method="VideoLibrary.GetTVShowDetails", key="tvshow", properties=properties)


def get_season_details(dbid=None):
    properties = [
        "season", "showtitle", "playcount", "episode", "fanart", "thumbnail", "tvshowid", "watchedepisodes",
        "art", "userrating", "title"]
    return _get_item_details(dbid=dbid, method="VideoLibrary.GetSeasonDetails", key="season", properties=properties)


def get_episode_details(dbid=None):
    properties = [
        "title", "plot", "votes", "rating", "writer", "firstaired", "playcount", "runtime", "director", "productioncode",
        "season", "episode", "originaltitle", "showtitle", "cast", "streamdetails", "lastplayed", "fanart", "thumbnail",
        "file", "resume", "tvshowid", "dateadded", "uniqueid", "art", "specialsortseason", "specialsortepisode", "userrating",
        "seasonid", "ratings"]
    return _get_item_details(dbid=dbid, method="VideoLibrary.GetEpisodeDetails", key="episode", properties=properties)


class KodiLibrary(object):
    def __init__(self, dbtype=None, tvshowid=None, attempt_reconnect=False, logging=True):
        self.dbtype = dbtype
        self.database = self._get_database(dbtype, tvshowid, attempt_reconnect)

    def _get_database(self, dbtype, tvshowid=None, attempt_reconnect=False, logging=True):
        if dbtype == 'both':
            movies = self.get_database('movie', None, attempt_reconnect) or []
            tvshows = self.get_database('tvshow', None, attempt_reconnect) or []
            return movies + tvshows
        return self.get_database(dbtype, tvshowid, attempt_reconnect)

    def get_database(self, dbtype, tvshowid=None, attempt_reconnect=False, logging=True):
        retries = 5 if attempt_reconnect else 1
        while not xbmc.Monitor().abortRequested() and retries > 0:
            database = self._get_kodi_db(dbtype, tvshowid)
            if database:
                return database
            xbmc.Monitor().waitForAbort(1)
            retries -= 1
        if logging:
            kodi_log(u'Getting KodiDB {} FAILED!'.format(dbtype), 1)

    def _get_kodi_db(self, dbtype=None, tvshowid=None):
        if not dbtype:
            return
        if dbtype == "movie":
            method = "VideoLibrary.GetMovies"
            params = {"properties": ["title", "imdbnumber", "originaltitle", "uniqueid", "year", "file"]}
        if dbtype == "tvshow":
            method = "VideoLibrary.GetTVShows"
            params = {"properties": ["title", "imdbnumber", "originaltitle", "uniqueid", "year"]}
        if dbtype == "season":
            method = "VideoLibrary.GetSeasons"
            params = {"tvshowid": tvshowid, "properties": ["title", "showtitle", "season"]}
        if dbtype == "episode":
            method = "VideoLibrary.GetEpisodes"
            params = {"tvshowid": tvshowid, "properties": ["title", "showtitle", "season", "episode", "file"]}
        dbid_name = u'{0}id'.format(dbtype)
        key_to_get = u'{0}s'.format(dbtype)
        response = get_jsonrpc(method, params)
        return [{
            'imdb_id': item.get('uniqueid', {}).get('imdb'),
            'tmdb_id': item.get('uniqueid', {}).get('tmdb'),
            'tvdb_id': item.get('uniqueid', {}).get('tvdb'),
            'dbid': item.get(dbid_name),
            'title': item.get('title'),
            'originaltitle': item.get('originaltitle'),
            'showtitle': item.get('showtitle'),
            'season': item.get('season'),
            'episode': item.get('episode'),
            'year': item.get('year'),
            'file': item.get('file')}
            for item in response.get('result', {}).get(key_to_get, [])]

    def get_info(
            self, info, dbid=None, imdb_id=None, originaltitle=None, title=None, year=None, season=None,
            episode=None, fuzzy_match=False, tmdb_id=None, tvdb_id=None):
        if not self.database or not info:
            return
        yearcheck = False
        index_list = find_dict_in_list(self.database, 'dbid', dbid) if dbid else []
        if not index_list and season:
            index_list = find_dict_in_list(self.database, 'season', try_int(season))
        if not index_list and imdb_id:
            index_list = find_dict_in_list(self.database, 'imdb_id', imdb_id)
        if not index_list and tmdb_id:
            index_list = find_dict_in_list(self.database, 'tmdb_id', str(tmdb_id))
        if not index_list and tvdb_id:
            index_list = find_dict_in_list(self.database, 'tvdb_id', str(tvdb_id))
        if not index_list:
            yearcheck = str(year) or 'dummynull'  # Also use year if matching by title to be certain we have correct item. Dummy value for True value that will always fail comparison check.
        if not index_list and originaltitle:
            index_list = find_dict_in_list(self.database, 'originaltitle', originaltitle)
        if not index_list and title:
            index_list = find_dict_in_list(self.database, 'title', title)
        for i in index_list:
            if season and episode:
                if try_int(episode) == self.database[i].get('episode'):
                    return self.database[i].get(info)
            elif not yearcheck or yearcheck in str(self.database[i].get('year')):
                return self.database[i].get(info)
        if index_list and fuzzy_match and not season and not episode:
            """ Fuzzy Match """
            i = index_list[0]
            return self.database[i].get(info)
