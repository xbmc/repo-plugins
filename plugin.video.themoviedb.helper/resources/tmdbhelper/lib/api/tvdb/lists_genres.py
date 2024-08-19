from tmdbhelper.lib.addon.plugin import get_localized, convert_type
from tmdbhelper.lib.api.tvdb.lists import ListLists, ListListItems


class ListGenres(ListLists):
    def get_items(self, info, tmdb_type, **kwargs):
        self.plugin_category = get_localized(135)
        items = self._get_items('genres', 'tvdb_genre', params={'tmdb_type': tmdb_type})
        return sorted(items, key=lambda x: x.get('label') or 0)


class ListGenre(ListListItems):
    def _get_item(self, i, tmdb_type, mediatype):
        item = self.tvdb_api.mapper.get_info(i, tmdb_type=tmdb_type)
        item['infolabels']['mediatype'] = mediatype
        item = self._get_item_tmdb_id(item, tmdb_type)
        return item

    def get_items(self, info, tvdb_id, tmdb_type, page=1, **kwargs):
        try:
            tvdb_type = {'movie': 'movies', 'tv': 'series'}[tmdb_type]
        except KeyError:
            return
        mediatype = convert_type(tmdb_type, 'dbtype')
        data = self.tvdb_api.get_request_lc(tvdb_type, 'filter', genre=tvdb_id, sort='score', sortType='desc')
        if not data:
            return
        self.library = convert_type(tmdb_type, 'library')
        self.container_content = convert_type(tmdb_type, 'container')
        self.plugin_category = get_localized(135)
        self.tmdb_cache_only = False
        return self._get_threaded_items(data, page, tmdb_type, mediatype)
