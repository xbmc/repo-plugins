import xbmc
import json
import resources.lib.utils as utils


class KodiLibrary(object):
    def __init__(self, dbtype=None):
        if dbtype:
            if dbtype == "movie":
                method = "VideoLibrary.GetMovies"
            elif dbtype == "tvshow":
                method = "VideoLibrary.GetTVShows"
            query = {"jsonrpc": "2.0",
                     "params": {"properties": ["title", "imdbnumber", "originaltitle", "year"]},
                     "method": method,
                     "id": 1}
            response = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
            dbid_name = '{0}id'.format(dbtype)
            key_to_get = '{0}s'.format(dbtype)
            self.database = []
            for item in response.get('result', {}).get(key_to_get, []):
                self.database.append({'imdb_id': item.get('imdbnumber'),
                                      'dbid': item.get(dbid_name),
                                      'title': item.get('title'),
                                      'originaltitle': item.get('originaltitle'),
                                      'year': item.get('year')})

    def get_dbid(self, imdb_id=None, originaltitle=None, title=None, year=None):
        dbid = None
        if self.database:
            index_list = utils.find_dict_in_list(self.database, 'imdb_id', imdb_id) if imdb_id else []
            if not index_list and originaltitle:
                index_list = utils.find_dict_in_list(self.database, 'originaltitle', originaltitle)
            if not index_list and title:
                index_list = utils.find_dict_in_list(self.database, 'title', title)
            for i in index_list:
                if year:
                    if year in str(self.database[i].get('year')):
                        dbid = self.database[i].get('dbid')
                else:
                    dbid = self.database[i].get('dbid')
                if dbid:
                    return dbid
