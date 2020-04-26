import xbmc
import json
import resources.lib.utils as utils


class KodiLibrary(object):
    def __init__(self, dbtype=None, tvshowid=None, attempt_reconnect=False):
        self.dbtype = None
        self.database = None
        self.get_database(dbtype, tvshowid)

        if self.database or not dbtype or not attempt_reconnect:
            return

        # If we didn't get database retry in case Kodi was starting up
        retries = 0
        monitor = xbmc.Monitor()
        while not monitor.abortRequested() and not self.database and retries < 5:
            monitor.waitForAbort(1)
            self.get_database(dbtype, tvshowid)
            retries += 1
            utils.kodi_log(u'Unable to retrive {} KodiDB!\nAttempting to Reconnect - Attempt {}'.format(dbtype, retries), 1)
        if not self.database:
            utils.kodi_log(u'Getting KodiDB {} FAILED!'.format(dbtype), 1)

    def get_jsonrpc(self, method=None, params=None):
        if not method or not params:
            return {}
        query = {
            "jsonrpc": "2.0",
            "params": params,
            "method": method,
            "id": 1}
        try:
            response = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
        except Exception as exc:
            utils.kodi_log(u'TMDbHelper - JSONRPC Error:\n{}'.format(exc), 1)
            response = {}
        return response

    def get_database(self, dbtype=None, tvshowid=None):
        if not dbtype:
            return
        if dbtype == "movie":
            method = "VideoLibrary.GetMovies"
            params = {"properties": ["title", "imdbnumber", "originaltitle", "uniqueid", "year", "file"]}
        if dbtype == "tvshow":
            method = "VideoLibrary.GetTVShows"
            params = {"properties": ["title", "imdbnumber", "originaltitle", "uniqueid", "year"]}
        if dbtype == "episode":
            method = "VideoLibrary.GetEpisodes"
            params = {
                "tvshowid": tvshowid,
                "properties": ["title", "showtitle", "season", "episode", "file"]}
        dbid_name = '{0}id'.format(dbtype)
        key_to_get = '{0}s'.format(dbtype)
        response = self.get_jsonrpc(method, params)
        self.dbtype = dbtype
        self.database = [{
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

    def get_library(self, dbtype=None, properties=None, filterr=None):
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

        response = self.get_jsonrpc(method, params)
        return response.get('result')

    def get_num_credits(self, dbtype, person):
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
        response = self.get_library(dbtype, filterr=filterr)
        return response.get('limits', {}).get('total', 0) if response else 0

    def get_person_stats(self, person):
        infoproperties = {}
        infoproperties['numitems.dbid.movies'] = self.get_num_credits('movie', person)
        infoproperties['numitems.dbid.tvshows'] = self.get_num_credits('tvshow', person)
        infoproperties['numitems.dbid.episodes'] = self.get_num_credits('episode', person)
        infoproperties['numitems.dbid.total'] = (
            utils.try_parse_int(infoproperties.get('numitems.dbid.movies')) +
            utils.try_parse_int(infoproperties.get('numitems.dbid.tvshows')) +
            utils.try_parse_int(infoproperties.get('numitems.dbid.episodes')))
        infoproperties = utils.del_empty_keys(infoproperties, ['N/A', '0.0', '0'])
        return infoproperties

    def get_info(self, info, dbid=None, imdb_id=None, originaltitle=None, title=None, year=None, season=None, episode=None, fuzzy_match=False, tmdb_id=None, tvdb_id=None):
        if not self.database or not info:
            return
        index_list = utils.find_dict_in_list(self.database, 'dbid', dbid) if dbid else []
        if not index_list and season:
            index_list = utils.find_dict_in_list(self.database, 'season', utils.try_parse_int(season))
        if not index_list and imdb_id:
            index_list = utils.find_dict_in_list(self.database, 'imdb_id', imdb_id)
        if not index_list and tmdb_id:
            index_list = utils.find_dict_in_list(self.database, 'tmdb_id', str(tmdb_id))
        if not index_list and tvdb_id:
            index_list = utils.find_dict_in_list(self.database, 'tvdb_id', str(tvdb_id))
        if not index_list and originaltitle:
            index_list = utils.find_dict_in_list(self.database, 'originaltitle', originaltitle)
        if not index_list and title:
            index_list = utils.find_dict_in_list(self.database, 'title', title)
        for i in index_list:
            if season and episode:
                if utils.try_parse_int(episode) == self.database[i].get('episode'):
                    return self.database[i].get(info)
            elif not year or year in str(self.database[i].get('year')):
                return self.database[i].get(info)
        if index_list and fuzzy_match and year and not season and not episode:
            """ Fuzzy Match """
            i = index_list[0]
            return self.database[i].get(info)

    def get_infolabels(self, item, key):
        infolabels = {}
        infolabels['genre'] = item.get('genre', [])
        infolabels['country'] = item.get('country', [])
        infolabels['episode'] = item.get('episode')
        infolabels['season'] = item.get('season')
        infolabels['sortepisode'] = item.get('sortepisode')
        infolabels['sortseason'] = item.get('sortseason')
        infolabels['episodeguide'] = item.get('episodeguide')
        infolabels['showlink'] = item.get('showlink', [])
        infolabels['top250'] = item.get('top250')
        infolabels['setid'] = item.get('setid')
        infolabels['tracknumber'] = item.get('tracknumber')
        infolabels['rating'] = item.get('rating')
        infolabels['userrating'] = item.get('userrating')
        infolabels['watched'] = item.get('watched')
        infolabels['playcount'] = utils.try_parse_int(item.get('playcount'))
        infolabels['overlay'] = item.get('overlay')
        infolabels['director'] = item.get('director', [])
        infolabels['mpaa'] = item.get('mpaa')
        infolabels['plot'] = item.get('plot')
        infolabels['plotoutline'] = item.get('plotoutline')
        infolabels['title'] = item.get('title')
        infolabels['originaltitle'] = item.get('originaltitle')
        infolabels['sorttitle'] = item.get('sorttitle')
        infolabels['duration'] = item.get('duration')
        infolabels['studio'] = item.get('studio', [])
        infolabels['tagline'] = item.get('tagline')
        infolabels['writer'] = item.get('writer', [])
        infolabels['tvshowtitle'] = item.get('tvshowtitle')
        infolabels['premiered'] = item.get('premiered')
        infolabels['status'] = item.get('status')
        infolabels['set'] = item.get('set')
        infolabels['setoverview'] = item.get('setoverview')
        infolabels['tag'] = item.get('tag', [])
        infolabels['imdbnumber'] = item.get('imdbnumber')
        infolabels['code'] = item.get('code')
        infolabels['aired'] = item.get('aired')
        infolabels['credits'] = item.get('credits')
        infolabels['lastplayed'] = item.get('lastplayed')
        infolabels['album'] = item.get('album')
        infolabels['artist'] = item.get('artist', [])
        infolabels['votes'] = item.get('votes')
        infolabels['path'] = item.get('path')
        infolabels['trailer'] = item.get('trailer')
        infolabels['dateadded'] = item.get('dateadded')
        infolabels['overlay'] = 5 if utils.try_parse_int(item.get('playcount')) > 0 and key in ['movie', 'episode'] else 4
        infolabels = utils.del_empty_keys(infolabels, ['N/A', '0.0', '0'])
        return infolabels

    def get_infoproperties(self, item):
        infoproperties = {}
        infoproperties['watchedepisodes'] = item.get('watchedepisodes')
        infoproperties['metacritic_rating'] = '{0:.1f}'.format(utils.try_parse_float(item.get('ratings', {}).get('metacritic', {}).get('rating')))
        infoproperties['imdb_rating'] = '{0:.1f}'.format(utils.try_parse_float(item.get('ratings', {}).get('imdb', {}).get('rating')))
        infoproperties['imdb_votes'] = '{:0,.0f}'.format(utils.try_parse_float(item.get('ratings', {}).get('imdb', {}).get('votes')))
        infoproperties['tmdb_rating'] = '{0:.1f}'.format(utils.try_parse_float(item.get('ratings', {}).get('themoviedb', {}).get('rating')))
        infoproperties['tmdb_votes'] = '{:0,.0f}'.format(utils.try_parse_float(item.get('ratings', {}).get('themoviedb', {}).get('votes')))
        infoproperties = utils.del_empty_keys(infoproperties, ['N/A', '0.0', '0'])
        return infoproperties

    def get_niceitem(self, item, key):
        label = item.get('label') or ''
        icon = thumb = item.get('thumbnail') or ''
        poster = item.get('art', {}).get('poster') or ''
        fanart = item.get('fanart') or item.get('art', {}).get('fanart') or ''
        landscape = item.get('art', {}).get('landscape') or ''
        clearlogo = item.get('art', {}).get('clearlogo') or ''
        clearart = item.get('art', {}).get('clearart') or ''
        discart = item.get('art', {}).get('discart') or ''
        cast = item.get('cast', [])
        streamdetails = item.get('streamdetails', {})
        infolabels = self.get_infolabels(item, key)
        infoproperties = self.get_infoproperties(item)
        return {
            'label': label, 'icon': icon, 'poster': poster, 'thumb': thumb, 'fanart': fanart, 'landscape': landscape,
            'clearlogo': clearlogo, 'clearart': clearart, 'discart': discart, 'cast': cast, 'infolabels': infolabels,
            'infoproperties': infoproperties, 'streamdetails': streamdetails}

    def get_item_details(self, dbid=None, method=None, key=None, properties=None):
        if not dbid or not method or not key or not properties:
            return {}
        param_name = "{0}id".format(key)
        params = {
            param_name: utils.try_parse_int(dbid),
            "properties": properties}
        details = self.get_jsonrpc(method, params)
        if not details or not isinstance(details, dict):
            return {}
        details = details.get('result', {}).get('{0}details'.format(key))
        return self.get_niceitem(details, key)

    def get_movie_details(self, dbid=None):
        properties = [
            "title", "genre", "year", "rating", "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle",
            "lastplayed", "playcount", "writer", "studio", "mpaa", "cast", "country", "imdbnumber", "runtime", "set",
            "showlink", "streamdetails", "top250", "votes", "fanart", "thumbnail", "file", "sorttitle", "resume", "setid",
            "dateadded", "tag", "art", "userrating", "ratings", "premiered", "uniqueid"]
        return self.get_item_details(dbid=dbid, method="VideoLibrary.GetMovieDetails", key="movie", properties=properties)

    def get_tvshow_details(self, dbid=None):
        properties = [
            "title", "genre", "year", "rating", "plot", "studio", "mpaa", "cast", "playcount", "episode", "imdbnumber",
            "premiered", "votes", "lastplayed", "fanart", "thumbnail", "file", "originaltitle", "sorttitle", "episodeguide",
            "season", "watchedepisodes", "dateadded", "tag", "art", "userrating", "ratings", "runtime", "uniqueid"]
        return self.get_item_details(dbid=dbid, method="VideoLibrary.GetTVShowDetails", key="tvshow", properties=properties)

    def get_episode_details(self, dbid=None):
        properties = [
            "title", "plot", "votes", "rating", "writer", "firstaired", "playcount", "runtime", "director", "productioncode",
            "season", "episode", "originaltitle", "showtitle", "cast", "streamdetails", "lastplayed", "fanart", "thumbnail",
            "file", "resume", "tvshowid", "dateadded", "uniqueid", "art", "specialsortseason", "specialsortepisode", "userrating",
            "seasonid", "ratings"]
        return self.get_item_details(dbid=dbid, method="VideoLibrary.GetEpisodeDetails", key="episode", properties=properties)

    def get_directory(self, url):
        method = "Files.GetDirectory"
        params = {
            "directory": url,
            "media": "files",
            "properties": [
                "title", "year", "originaltitle", "imdbnumber", "premiered", "streamdetails", "size",
                "firstaired", "season", "episode", "showtitle", "file", "tvshowid", "thumbnail"]}
        response = self.get_jsonrpc(method, params)
        return response.get('result', {}).get('files', [{}]) or [{}]
